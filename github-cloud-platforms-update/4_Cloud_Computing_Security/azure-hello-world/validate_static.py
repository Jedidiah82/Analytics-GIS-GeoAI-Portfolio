"""Local artifact checks, not an Azure deployment test."""
from html.parser import HTMLParser
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).parent / "static"
class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.tags=[]; self.links=[]; self.feed(text)
    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.links += [value for key,value in attrs if key in {"href", "src"}]
class StaticTests(unittest.TestCase):
    def test_documents(self):
        for filename in ["index.html", "404.html"]:
            page = Page((ROOT/filename).read_text())
            for tag in ["html", "title", "meta", "main", "h1"]: self.assertIn(tag, page.tags)
    def test_local_assets(self):
        for filename in ROOT.glob("*.html"):
            for link in Page(filename.read_text()).links:
                if not link.startswith(("https://", "#")):
                    self.assertTrue((ROOT/(link.lstrip("/") or "index.html")).is_file(), link)
    def test_security_headers(self):
        headers = json.loads((ROOT/"staticwebapp.config.json").read_text())["globalHeaders"]
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertNotIn("unsafe-inline", headers["Content-Security-Policy"])
    def test_404(self):
        override = json.loads((ROOT/"staticwebapp.config.json").read_text())["responseOverrides"]["404"]
        self.assertEqual(override["statusCode"], 404)
        self.assertTrue((ROOT/override["rewrite"].lstrip("/")).exists())
    def test_no_client_secrets(self):
        text = " ".join(p.read_text() for p in ROOT.iterdir() if p.is_file())
        for needle in ["BEGIN PRIVATE KEY", "AccountKey=", "AZURE_STATIC_WEB_APPS_API_TOKEN="]: self.assertNotIn(needle, text)
if __name__ == "__main__": unittest.main(verbosity=2)
