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

    def test_manifest_installable_assets(self):
        data=json.loads((ROOT/'web'/'manifest.webmanifest').read_text(encoding='utf-8'))
        self.assertEqual(data['display'],'standalone')
        self.assertEqual({x['sizes'] for x in data['icons']}, {'192x192','512x512'})

    def test_no_download_links_before_first_verified_release(self):
        data=json.loads((ROOT/'catalog'/'apps.json').read_text(encoding='utf-8'))
        self.assertTrue(all(a['status']=='planned' and a['download_url'] is None for a in data['apps']))


if __name__ == '__main__':
    unittest.main()
