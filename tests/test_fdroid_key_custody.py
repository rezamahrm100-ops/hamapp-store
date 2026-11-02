import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fdroid_key_custody as custody


@unittest.skipUnless(os.name == "posix", "POSIX-only offline custody")
class CustodyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.source = root / "secure-key.jks"
        self.source.write_bytes(b"test-only-not-a-keystore:" + b"x" * 2048)
        self.source.chmod(0o600)
        self.backup_dir = root / "offline-disk"
        self.backup_dir.mkdir(mode=0o700)
        self.backup_dir.chmod(0o700)
        self.dest = self.backup_dir / "backup.jks"

    def test_actual_streaming_backup_and_byte_verification(self):
        receipt = custody.create_backup(self.source, self.backup_dir, "backup.jks",
                                       volume_check=lambda *_: True)
        self.assertTrue(receipt["byte_for_byte_backup_verified"])
        self.assertFalse(receipt["offline_disconnection_physically_verified"])
        self.assertFalse(receipt["production_publishing_authorized"])
        self.assertEqual(self.source.read_bytes(), self.dest.read_bytes())
        self.assertEqual(stat.S_IMODE(self.dest.stat().st_mode), 0o600)
        self.assertNotIn("sha256", str(receipt))
        with self.assertRaises(custody.CustodyError):
            custody.create_backup(self.source, self.backup_dir, "backup.jks",
                                  volume_check=lambda *_: True)

    def test_same_volume_rejected_fail_closed(self):
        with self.assertRaises(custody.CustodyError):
            custody.create_backup(self.source, self.backup_dir, "backup.jks",
                                  volume_check=lambda *_: False)
        self.assertFalse(self.dest.exists())

    def test_damaged_backup_rejected(self):
        custody.create_backup(self.source, self.backup_dir, "backup.jks",
                              volume_check=lambda *_: True)
        self.dest.write_bytes(b"x" * 2048)
        with self.assertRaises(custody.CustodyError):
            custody.validate_backup(self.source, self.dest, volume_check=lambda *_: True)

    def test_world_readable_key_rejected(self):
        self.source.chmod(0o644)
        with self.assertRaises(custody.CustodyError):
            custody.create_backup(self.source, self.backup_dir, "backup.jks",
                                  volume_check=lambda *_: True)

    def test_symlink_input_rejected(self):
        link = self.source.parent / "untrusted.jks"
        link.symlink_to(self.source)
        with self.assertRaises(custody.CustodyError):
            custody.create_backup(link, self.backup_dir, "backup.jks",
                                  volume_check=lambda *_: True)

    def test_invalid_name_rejected(self):
        for name in ("../file.jks", ".secret", "nested/file", "bad\\name"):
            with self.subTest(name=name), self.assertRaises(custody.CustodyError):
                custody.create_backup(self.source, self.backup_dir, name,
                                      volume_check=lambda *_: True)


if __name__ == "__main__":
    unittest.main()
