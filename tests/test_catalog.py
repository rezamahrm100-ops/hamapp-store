import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validate_catalog', ROOT / 'scripts' / 'validate_catalog.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.sample = {"schema_version": 1, "apps": [{"id": "demo", "name_fa": "نمونه", "name_en": "Demo", "description": "Test", "platforms": ["android"], "status": "planned", "version": None, "download_url": None}]}

    def test_real_catalog(self):
        payload = json.loads((ROOT / "catalog/apps.json").read_text(encoding='utf-8'))
        self.assertFalse(validator.validate(payload))

    def test_planned_cannot_advertise_download(self):
        self.sample['apps'][0]['download_url'] = 'https://example.com/not-built.apk'
        self.assertTrue(validator.validate(self.sample))

    def test_released_requires_https(self):
        app = self.sample['apps'][0]
        app.update(status='released', version='1.0.0', download_url='http://example.org/test.apk')
        self.assertTrue(validator.validate(self.sample))
        app['download_url'] = 'https://example.org/test.apk'
        self.assertFalse(validator.validate(self.sample))

    def test_duplicate_id_rejected(self):
        self.sample['apps'].append(self.sample['apps'][0].copy())
        self.assertTrue(validator.validate(self.sample))


if __name__ == '__main__':
    unittest.main()
