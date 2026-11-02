import pathlib
import stat
import sys
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import binary_archive_review as scanner

class RealArchiveSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.file = pathlib.Path(self.temp.name) / "demo.apk"

    def write(self, items):
        with zipfile.ZipFile(self.file, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, value in items:
                archive.writestr(name, value)

    def test_valid_actual_zip_crc_and_digest(self):
        self.write([("AndroidManifest.xml", b"binary XML fixture"),
                    ("classes.dex", b"dex\x0a")])
        result = scanner.review(self.file)
        self.assertEqual(result["archive_entry_count"], 2)
        self.assertTrue(result["actual_archive_crc_and_paths_checked"])
        self.assertFalse(result["malware_free_verified"])
        self.assertFalse(result["public_release_authorized"])

    def test_dot_traversal_rejected(self):
        for path in ("../escape", "/absolute", "dir/../escape", "C:/evil.exe",
                     "sub//double", "./prefix"):
            with self.subTest(path=path):
                self.write([(path, b"payload")])
                with self.assertRaises(scanner.ArchiveReviewError):
                    scanner.review(self.file)

    def test_raw_windows_separator_is_rejected_without_zipfile_normalization(self):
        from types import SimpleNamespace
        # zipfile normalizes backslashes to slash during archive *creation*
        # on Windows. Test the raw untrusted entry parser independently.
        record = SimpleNamespace(filename="directory\\evil.exe", flag_bits=0,
                                 compress_type=zipfile.ZIP_STORED,
                                 create_system=0, external_attr=0,
                                 file_size=2, compress_size=2)
        with self.assertRaisesRegex(scanner.ArchiveReviewError, "unsafe"):
            scanner.checked_entry(record, set())

    def test_duplicate_and_case_collisions_rejected(self):
        with zipfile.ZipFile(self.file, "w") as f:
            f.writestr("classes.dex", b"1")
            f.writestr("Classes.dex", b"2")
        with self.assertRaisesRegex(scanner.ArchiveReviewError, "duplicate"):
            scanner.review(self.file)

    def test_symlink_entry_rejected(self):
        link = zipfile.ZipInfo("assets/link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(self.file, "w") as f:
            f.writestr(link, "../shadow")
        with self.assertRaisesRegex(scanner.ArchiveReviewError, "symbolic"):
            scanner.review(self.file)

    def test_crc_tamper_rejected(self):
        with zipfile.ZipFile(self.file, "w", compression=zipfile.ZIP_STORED) as archive:
            archive.writestr("data.bin", b"secret-archive-pattern")
        payload = self.file.read_bytes()
        self.file.write_bytes(payload.replace(b"secret-archive-pattern", b"tamper-archive-pattern"))
        with self.assertRaises(scanner.ArchiveReviewError):
            scanner.review(self.file)

    def test_excessive_compression_rejected(self):
        self.write([("huge-zeros", b"\x00" * 1024 * 1024)])
        with self.assertRaisesRegex(scanner.ArchiveReviewError, "compression ratio"):
            scanner.review(self.file)

    def test_wrong_extension_and_corrupt_file(self):
        self.file.write_bytes(b"not a valid ZIP")
        with self.assertRaises(scanner.ArchiveReviewError):
            scanner.review(self.file)
        self.file.rename(self.file.with_suffix(".exe"))
        with self.assertRaises(scanner.ArchiveReviewError):
            scanner.review(self.file.with_suffix(".exe"))

if __name__ == "__main__":
    unittest.main()
