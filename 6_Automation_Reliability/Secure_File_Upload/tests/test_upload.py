"""All network tests bind literal loopback; no external service is contacted."""
from contextlib import contextmanager, redirect_stdout
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import ipaddress

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import upload_client as client

TOKEN = "synthetic-local-test-token"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # No request headers or credentials in test logs.

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        self.server.records.append({"path": self.path, "body": body,
                                    "auth": self.headers.get("Authorization"),
                                    "content_type": self.headers.get("Content-Type")})
        if self.server.delay:
            time.sleep(self.server.delay)
        status = self.server.status
        if self.headers.get("Authorization") != "Bearer " + TOKEN:
            status = 401
        self.send_response(status)
        self.send_header("Content-Type", self.server.content_type)
        if self.server.redirect:
            self.send_header("Location", self.server.redirect)
        self.end_headers()
        try:
            self.wfile.write(self.server.response)
        except (ConnectionError, ssl.SSLError):
            pass


@contextmanager
def server(context=None, status=201, response=b'{"id":1}', content_type="application/json", delay=0, redirect=None):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    httpd.daemon_threads = True
    httpd.records = [];httpd.status = status;httpd.response = response
    httpd.content_type = content_type;httpd.delay = delay;httpd.redirect = redirect
    if context is not None:
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True);thread.start()
    try:
        yield httpd, ("https" if context else "http") + "://127.0.0.1:" + str(httpd.server_port) + "/fruits/"
    finally:
        httpd.shutdown();httpd.server_close();thread.join(timeout=3)


def certificates(folder):
    # Fresh disposable keys are generated only inside the OS temporary directory.
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Disposable upload test CA")])
    now = datetime.now(timezone.utc)
    ca = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
          .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
          .not_valid_before(now-timedelta(minutes=5)).not_valid_after(now+timedelta(days=1))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .sign(ca_key, hashes.SHA256()))
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    leaf = (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Loopback fixture")]))
            .issuer_name(ca.subject).public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now-timedelta(minutes=5)).not_valid_after(now+timedelta(days=1))
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), critical=False)
            .sign(ca_key, hashes.SHA256()))
    ca_path=folder/"ca.pem";ca_path.write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    leaf_path=folder/"server.pem";leaf_path.write_bytes(leaf.public_bytes(serialization.Encoding.PEM))
    key_path=folder/"server.key";key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(leaf_path,key_path)
    return context,str(ca_path)


class UploadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tls_temp=tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.tls_context,cls.ca_file=certificates(Path(cls.tls_temp.name))

    @classmethod
    def tearDownClass(cls):cls.tls_temp.cleanup()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(ignore_cleanup_errors=True);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.meta=self.root/"descriptions";self.meta.mkdir()
        (self.meta/"001.txt").write_text("Demo\n500 lbs\nFirst description\nSecond line\n",encoding="utf8")
        self.images=self.root/"images";self.images.mkdir()
        Image.new("RGB",(32,24),(20,100,150)).save(self.images/"001.jpeg")

    def execute(self,url=None,kind="metadata",extra=(),token=TOKEN):
        args=["--endpoint",url or "https://example.invalid/fruits/","--input-dir",str(self.meta if kind=="metadata" else self.images)]+list(extra)
        output=io.StringIO()
        with patch.dict(os.environ,{"UPLOAD_API_TOKEN":token}),redirect_stdout(output):code=client.cli(kind,args)
        return code,json.loads(output.getvalue())

    def test_reject_remote_http_even_with_test_flag(self):
        for url in ["http://example.org/x","http://localhost/x","http://127.0.0.1.example.org/x","http://169.254.169.254/x"]:
            with self.subTest(url=url),self.assertRaises(client.UploadError):client.endpoint(url,True)

    def test_loopback_http_needs_explicit_flag(self):
        with self.assertRaises(client.UploadError):client.endpoint("http://127.0.0.1/x")
        self.assertEqual(client.endpoint("http://127.0.0.1/x",True).hostname,"127.0.0.1")
        self.assertEqual(client.endpoint("http://[::1]/x",True).hostname,"::1")

    def test_reject_url_credentials_query_fragment_and_control(self):
        for url in ["https://user:secret@example.org/","https://example.org/?token=abc","https://example.org/#x","https://example.org/\r\nX:bad","file:///tmp/x","https://example.org:0/x"]:
            with self.subTest(url=url),self.assertRaises(client.UploadError):client.endpoint(url)

    def test_token_required_and_header_injection_rejected(self):
        for token in ["","a\r\nInjected: yes"," token","x"*4097]:
            code,r=self.execute(token=token);self.assertEqual(code,1);self.assertIn("UPLOAD_API_TOKEN",r["error"])

    def test_metadata_preserves_multiline_description(self):
        body,ct=client.metadata(self.meta/"001.txt");record=json.loads(body)
        self.assertEqual(record["description"],"First description\nSecond line")
        self.assertEqual(record["weight"],500);self.assertEqual(record["image_name"],"001.jpeg")

    def test_invalid_metadata_fields_fail(self):
        for text in ["Demo\n500", "Demo\n-1 lbs\nDescription", "Demo\n1.5 lbs\nDescription", "Demo\n0\nDescription", "Demo\n500 kg\nDescription", "\n500\nDescription", "Demo\n500\n"]:
            with self.subTest(text=text):
                (self.meta/"001.txt").write_text(text)
                with self.assertRaises(client.UploadError):client.metadata(self.meta/"001.txt")

    def test_invalid_encoding_and_oversized_metadata(self):
        for data in [b'\xff',b'x'*(client.MAX_METADATA+1)]:
            (self.meta/"001.txt").write_bytes(data)
            with self.assertRaises(client.UploadError):client.metadata(self.meta/"001.txt")

    def test_empty_and_oversized_batch_fail(self):
        empty=self.root/"empty";empty.mkdir()
        with self.assertRaises(client.UploadError):client.prepare(empty,"metadata")
        for i in range(101):(empty/f"{i:03}.txt").write_text("A\n1\nB")
        with self.assertRaises(client.UploadError):client.prepare(empty,"metadata")

    def test_batch_byte_budget_enforced(self):
        with patch.object(client,"MAX_BATCH_BYTES",1),self.assertRaises(client.UploadError):client.prepare(self.meta,"metadata")

    def test_filename_header_injection_rejected(self):
        p=self.meta/"bad name.txt";p.write_text("Demo\n1\nDescription")
        with self.assertRaises(client.UploadError):client.metadata(p)

    def test_valid_jpeg_and_corrupt_jpeg(self):
        body,ct=client.image(self.images/"001.jpeg");self.assertIn(b'filename="001.jpeg"',body);self.assertTrue(ct.startswith("multipart/form-data; boundary="))
        jpg=self.images/"002.jpg";jpg.write_bytes((self.images/"001.jpeg").read_bytes())
        jpg_body,_=client.image(jpg);self.assertIn(b'filename="002.jpeg"',jpg_body)
        (self.images/"001.jpeg").write_bytes(b"not an image")
        with self.assertRaises(client.UploadError):client.image(self.images/"001.jpeg")

    def test_renamed_png_and_large_dimensions_rejected(self):
        Image.new("RGB",(10,10)).save(self.images/"001.jpeg",format="PNG")
        with self.assertRaises(client.UploadError):client.image(self.images/"001.jpeg")
        Image.new("RGB",(5000,4100)).save(self.images/"001.jpeg")
        with self.assertRaises(client.UploadError):client.image(self.images/"001.jpeg")

    def test_dry_run_works_without_token_and_connects_nowhere(self):
        with patch.object(client,"send",side_effect=AssertionError("must not connect")):
            code,r=self.execute(extra=["--dry-run"],token="")
        self.assertEqual(code,0);self.assertEqual(r["status"],"validated_only");self.assertEqual(r["acknowledged"],0)

    def test_bad_batch_connects_nowhere(self):
        (self.meta/"002.txt").write_text("malformed")
        with server() as (httpd,url):code,r=self.execute(url,extra=["--allow-local-http"])
        self.assertEqual(code,1);self.assertEqual(httpd.records,[])

    def test_real_loopback_metadata_upload_and_bearer(self):
        with server() as (httpd,url):code,r=self.execute(url,extra=["--allow-local-http"])
        self.assertEqual(code,0);self.assertEqual(r["acknowledged"],1)
        self.assertEqual(httpd.records[0]["auth"],"Bearer "+TOKEN)
        self.assertEqual(json.loads(httpd.records[0]["body"])["weight"],500)

    def test_real_loopback_image_upload(self):
        with server() as (httpd,url):code,r=self.execute(url,kind="images",extra=["--allow-local-http"])
        self.assertEqual(code,0);self.assertIn(b'Content-Type: image/jpeg',httpd.records[0]["body"])

    def test_real_tls_with_explicit_trusted_test_ca(self):
        with server(self.tls_context) as (httpd,url):code,r=self.execute(url,extra=["--ca-file",self.ca_file])
        self.assertEqual(code,0);self.assertEqual(r["files"][0]["http_status"],201)

    def test_real_tls_subprocess_entrypoints(self):
        with server(self.tls_context) as (httpd,url):
            for script,directory in [("run.py",self.meta),("supplier_image_upload.py",self.images)]:
                with self.subTest(script=script):
                    result=subprocess.run([sys.executable,str(ROOT/script),"--endpoint",url,"--input-dir",str(directory),"--ca-file",self.ca_file],env={**os.environ,"UPLOAD_API_TOKEN":TOKEN},capture_output=True,text=True,timeout=10)
                    self.assertEqual(result.returncode,0,result.stderr)
                    report=json.loads(result.stdout);self.assertEqual(report["acknowledged"],1)
                    self.assertNotIn(TOKEN,result.stdout)
            self.assertEqual(len(httpd.records),2)

    def test_real_tls_rejects_untrusted_ca(self):
        with server(self.tls_context) as (httpd,url):code,r=self.execute(url)
        self.assertEqual(code,1);self.assertEqual(r["error"],"tls_verification_or_handshake_failed");self.assertEqual(httpd.records,[])

    def test_real_tls_rejects_hostname_mismatch(self):
        with server(self.tls_context) as (httpd,url):code,r=self.execute(url.replace("127.0.0.1","localhost"),extra=["--ca-file",self.ca_file])
        self.assertEqual(code,1);self.assertEqual(r["error"],"tls_verification_or_handshake_failed");self.assertEqual(httpd.records,[])

    def test_real_unauthorized_server_rejects_wrong_token(self):
        with server() as (httpd,url):code,r=self.execute(url,extra=["--allow-local-http"],token="wrong-synthetic-token")
        self.assertEqual(code,1);self.assertEqual(r["error"],"http_status_401")

    def test_http_failure_is_not_success(self):
        for status in [400,403,429,500]:
            with self.subTest(status=status),server(status=status) as (httpd,url):
                code,r=self.execute(url,extra=["--allow-local-http"])
                self.assertEqual(code,1);self.assertEqual(r["error"],f"http_status_{status}");self.assertEqual(r["acknowledged"],0)

    def test_redirect_is_not_followed_or_forwarded(self):
        with server() as (sink,destination),server(status=307,redirect=destination) as (httpd,url):
            code,r=self.execute(url,extra=["--allow-local-http"])
            self.assertEqual(code,1);self.assertEqual(r["error"],"http_status_307");self.assertEqual(sink.records,[])

    def test_bounded_acknowledgement_contract(self):
        for body,ct in [(b'not-json','application/json'),(b'[]','application/json'),(b'{}','application/json'),(b'{"id":1}','text/html'),(b'x'*(client.MAX_RESPONSE+1),'application/json')]:
            with self.subTest(body=body[:10],ct=ct),server(response=body,content_type=ct) as (httpd,url):
                code,r=self.execute(url,extra=["--allow-local-http"]);self.assertEqual(code,1);self.assertEqual(r["acknowledged"],0)

    def test_socket_timeout_fails_without_retry(self):
        with server(delay=.3) as (httpd,url):code,r=self.execute(url,extra=["--allow-local-http","--timeout","0.05"])
        self.assertEqual(code,1);self.assertIn("outcome_may_be_unknown",r["error"]);self.assertEqual(len(httpd.records),1)

    def test_invalid_timeout_prevents_upload(self):
        for timeout in ["0","-1","nan","inf","121"]:
            with self.subTest(timeout=timeout):
                code,r=self.execute(extra=["--timeout",timeout]);self.assertEqual(code,1)

    def test_fail_fast_reports_partial_acknowledgement(self):
        (self.meta/"002.txt").write_text("Demo two\n5\nDescription")
        with patch.object(client,"send",side_effect=[201,client.UploadError("http_status_500")]):code,r=self.execute()
        self.assertEqual(code,1);self.assertEqual(r["planned"],2);self.assertEqual(r["acknowledged"],1)

    def test_error_report_does_not_echo_server_body_or_token(self):
        with server(status=500,response=TOKEN.encode()) as (httpd,url):code,r=self.execute(url,extra=["--allow-local-http"])
        self.assertEqual(code,1);self.assertNotIn(TOKEN,json.dumps(r));self.assertNotIn("Authorization",json.dumps(r))

    def test_entry_points_run_in_subprocess(self):
        for script,directory in [("run.py",self.meta),("supplier_image_upload.py",self.images)]:
            with self.subTest(script=script):
                result=subprocess.run([sys.executable,str(ROOT/script),"--endpoint","https://example.invalid/","--input-dir",str(directory),"--dry-run"],capture_output=True,text=True,timeout=10)
                self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout)["status"],"validated_only")


if __name__ == "__main__":unittest.main()
