import contextlib
import io
import json
import socket
import unittest
from unittest.mock import patch
import health_check as h

def sample(cpu=10, disk=50, memory=1000, host="127.0.0.1"):
    return {k: {"value": v} for k, v in zip(["cpu_percent", "disk_free_percent", "available_memory_mb", "localhost_ipv4"], [cpu, disk, memory, host])}

class HealthTests(unittest.TestCase):
    def test_healthy(self):
        self.assertEqual(h.evaluate(sample())["status"], "healthy")
    def test_exact_thresholds(self):
        self.assertEqual(len(h.evaluate(sample(80, 20, 100))["issues"]), 3)
    def test_local_resolution_mismatch(self):
        self.assertEqual(h.evaluate(sample(host="127.0.0.2"))["issues"], ["localhost_ipv4"])
    def test_probe_error_does_not_hide_other_checks(self):
        with patch.object(h.socket, "gethostbyname", side_effect=socket.gaierror), patch.object(h.psutil, "cpu_percent", return_value=99) as cpu:
            result = h.evaluate(h.collect(".", 0.1))
        cpu.assert_called_once_with(interval=0.1)
        self.assertEqual(result["status"], "error")
        self.assertIn("cpu_percent", result["issues"])
        self.assertIn("localhost_ipv4", result["errors"])
    def test_missing_sample_is_error(self):
        self.assertEqual(len(h.evaluate({})["errors"]), 4)
    def run_cli(self, values, args=()):
        with patch.object(h, "collect", return_value=values), contextlib.redirect_stdout(io.StringIO()) as out:
            code = h.main(list(args))
        return code, json.loads(out.getvalue())
    def test_no_email_by_default(self):
        with patch.object(h, "notify") as send:
            code, report = self.run_cli(sample(cpu=90))
        self.assertEqual(code, 1)
        self.assertEqual(report["notification"], "disabled")
        send.assert_not_called()
    def test_notification_failure_exit(self):
        with patch.object(h, "notify", side_effect=RuntimeError("secret must not be printed")):
            code, report = self.run_cli(sample(cpu=90), ["--send-email"])
        self.assertEqual(code, 3)
        self.assertNotIn("secret", json.dumps(report))
    def test_smtp_requires_configuration(self):
        with self.assertRaises(ValueError): h.notify({}, {})
    def test_smtp_starttls_before_login(self):
        env = {k: "example" for k in ["MONITOR_SMTP_HOST", "MONITOR_SMTP_USER", "MONITOR_SMTP_PASSWORD", "MONITOR_FROM", "MONITOR_TO"]}
        with patch.object(h.smtplib, "SMTP") as factory: h.notify({"status": "alert"}, env)
        names = [c[0] for c in factory.return_value.__enter__.return_value.method_calls]
        self.assertLess(names.index("starttls"), names.index("login"))
        self.assertIn("send_message", names)
    def test_exit_states(self):
        self.assertEqual(self.run_cli(sample())[0], 0)
        self.assertEqual(self.run_cli({})[0], 2)
    def test_invalid_interval(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit): h.main(["--interval", "0"])

if __name__ == "__main__": unittest.main()
