import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SiteContractTests(unittest.TestCase):
    def test_essential_web_assets(self):
        for name in ['index.html','styles.css','app.js','sw.js','manifest.webmanifest','icon-192.png','icon-512.png']:
            with self.subTest(name=name):
                self.assertTrue((ROOT/'web'/name).is_file())

    def test_farsi_right_to_left_and_accessibility(self):
        page=(ROOT/'web'/'index.html').read_text(encoding='utf-8')
        self.assertIn('lang="fa" dir="rtl"',page)
        self.assertIn('role="status"',page)
        self.assertIn('aria-pressed',page)

    def test_service_worker_registration_uses_browser_secure_context(self):
        app = (ROOT / "web/app.js").read_text(encoding="utf-8")
        self.assertIn("window.isSecureContext", app)
        self.assertNotIn("location.hostname === 'localhost'", app)

    def test_native_dialog_and_text_only_details(self):
        page = (ROOT / "web/index.html").read_text(encoding="utf-8")
        app = (ROOT / "web/app.js").read_text(encoding="utf-8")
        self.assertIn('id="detailsDialog"', page)
        self.assertIn('aria-labelledby="detailsTitle"', page)
        self.assertIn("detailsDialog.showModal()", app)
        self.assertIn("detailsContent.replaceChildren()", app)
        self.assertIn("detailsTitle.textContent", app)
        self.assertNotIn("innerHTML", app)
        self.assertIn("app.release_proof", app)

    def test_manifest_installable_assets(self):
        data=json.loads((ROOT/'web'/'manifest.webmanifest').read_text(encoding='utf-8'))
        self.assertEqual(data['display'],'standalone')
        self.assertEqual({x['sizes'] for x in data['icons']}, {'192x192','512x512'})

    def test_generated_offline_fallback_contains_no_download_or_released_app(self):
        import subprocess
        import sys
        p = subprocess.run([sys.executable, str(ROOT / "scripts/build_site.py")],
                           cwd=ROOT, capture_output=True, text=True, timeout=45)
        self.assertEqual(p.returncode, 0, p.stderr)
        offline = json.loads((ROOT / "dist/site/catalog/planned-offline.json").read_text(encoding="utf-8"))
        self.assertTrue(all(x["status"] == "planned" and x["download_url"] is None
                            and x["version"] is None and "release_proof" not in x
                            for x in offline["apps"]))
        sw = (ROOT / "web/sw.js").read_text(encoding="utf-8")
        self.assertIn("./catalog/planned-offline.json", sw)
        self.assertIn("cache:'no-store'", sw)
        app = (ROOT / "web/app.js").read_text(encoding="utf-8")
        self.assertIn("offlineMode = true", app)
        self.assertIn("app.status === 'planned'", app)

    def test_no_download_links_before_first_verified_release(self):
        data=json.loads((ROOT/'catalog'/'apps.json').read_text(encoding='utf-8'))
        self.assertTrue(all(a['status']=='planned' and a['download_url'] is None for a in data['apps']))


if __name__ == '__main__':
    unittest.main()
