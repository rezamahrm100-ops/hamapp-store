import io
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_live_pages as pages

class Response:
    def __init__(self, url, data, *, status=200, final=None):
        self.data = io.BytesIO(data)
        self.url = url if final is None else final
        self.status = status
    def __enter__(self): return self
    def __exit__(self, *args): self.data.close()
    def read(self, size): return self.data.read(size)
    def getcode(self): return self.status
    def geturl(self): return self.url

class FakeOpener:
    def __init__(self, resources):
        self.resources = resources
        self.calls = []
    def open(self, request, timeout):
        url = request.full_url
        self.calls.append((url, timeout))
        return self.resources[url]

class PagesCheckTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = pathlib.Path(t.name)
        self.responses = {}
        for path in pages.FILES:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            data = ("evidence " + path).encode("utf-8")
            target.write_bytes(data)
            self.responses[pages.ORIGIN + path] = Response(pages.ORIGIN + path, data)
    def test_all_public_bytes_and_redirect_controls(self):
        opener = FakeOpener(self.responses)
        result = pages.check_site(self.root, opener=opener)
        self.assertEqual(result["expected_public_files_checked"], len(pages.FILES))
        self.assertTrue(result["actual_https_bytes_match_local_build"])
        self.assertFalse(result["public_release_authorized"])
        self.assertEqual(len(opener.calls), len(pages.FILES))
    def test_exact_origin_required(self):
        with self.assertRaises(pages.LivePagesError):
            pages.check_site(self.root, origin="http://localhost/", opener=FakeOpener(self.responses))
    def test_stale_page_mismatch_refused(self):
        url = pages.ORIGIN + "app.js"
        self.responses[url] = Response(url, b"stale-content")
        with self.assertRaisesRegex(pages.LivePagesError, "do not match"):
            pages.check_site(self.root, opener=FakeOpener(self.responses))
    def test_redirect_refused(self):
        url = pages.ORIGIN + "index.html"
        self.responses[url] = Response(url, self.responses[url].data.getvalue(),
                                      final="https://attacker.example.invalid/")
        with self.assertRaisesRegex(pages.LivePagesError, "redirect"):
            pages.check_site(self.root, opener=FakeOpener(self.responses))
    def test_missing_local_file_refused(self):
        (self.root / "sw.js").unlink()
        with self.assertRaises(pages.LivePagesError):
            pages.check_site(self.root, opener=FakeOpener(self.responses))
    def test_missing_local_symlink_refused(self):
        (self.root / "sw.js").unlink()
        try:
            (self.root / "sw.js").symlink_to(self.root / "app.js")
        except OSError:
            self.skipTest("symlink creation not permitted")
        with self.assertRaises(pages.LivePagesError):
            pages.check_site(self.root, opener=FakeOpener(self.responses))

if __name__ == "__main__":
    unittest.main()
