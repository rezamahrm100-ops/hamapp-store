import pathlib
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import antivirus_binary_review as av

NOW=datetime(2026,11,3,12,0,0,tzinfo=timezone.utc)
DB="ClamAV 1.4.3/27999/Tue Nov 3 09:00:00 2026\n"

class FakeRunner:
    def __init__(self, status=0, version=DB, mutate=None):
        self.status=status;self.version=version;self.commands=[];self.calls=[];self.mutate=mutate
    def __call__(self, cmd, **kwargs):
        self.commands.append(cmd)
        self.calls.append(kwargs)
        if cmd[1]=="--version":
            return subprocess.CompletedProcess(cmd,0,self.version,"")
        if self.mutate: self.mutate()
        return subprocess.CompletedProcess(cmd,self.status,"" if self.status==0 else "FOUND","")

class AntivirusReviewTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.file=pathlib.Path(t.name)/"package.apk"
        self.file.write_bytes(b"synthetic non-executable bytes for test only")

    def test_run_real_clamscan_command_and_hash(self):
        runner=FakeRunner()
        receipt=av.scan(self.file,runner=runner,now=NOW)
        self.assertTrue(receipt["actual_signature_scan_completed_without_detection"])
        self.assertFalse(receipt["malware_absence_verified"])
        self.assertEqual(runner.commands[1][0:4],
                         ["clamscan","--infected","--no-summary","--stdout"])
        self.assertTrue(all(call["shell"] is False and call["check"] is False
                            for call in runner.calls))

    def test_stale_or_missing_db_rejected(self):
        for version in ("ClamAV 1.4.3\n",
                        "ClamAV 1.4.3/27777/Mon Jan 1 00:00:00 2024\n"):
            with self.subTest(version=version),self.assertRaises(av.MalwareReviewError):
                av.scan(self.file,runner=FakeRunner(version=version),now=NOW)

    def test_detection_and_failed_scan_block(self):
        for result in (1,2,124):
            with self.subTest(result=result),self.assertRaises(av.MalwareReviewError):
                av.scan(self.file,runner=FakeRunner(status=result),now=NOW)

    def test_changed_file_during_scan_rejected(self):
        def change(): self.file.write_bytes(b"swapped malicious bytes")
        with self.assertRaises(av.MalwareReviewError):
            av.scan(self.file,runner=FakeRunner(mutate=change),now=NOW)

    def test_rejects_symlink_and_bad_extension(self):
        x=self.file.with_suffix(".txt")
        x.write_bytes(b"unknown")
        with self.assertRaises(av.MalwareReviewError):
            av.scan(x,runner=FakeRunner(),now=NOW)
        link=self.file.parent/"link.apk"
        try: link.symlink_to(self.file)
        except OSError: self.skipTest("symlink unavailable")
        with self.assertRaises(av.MalwareReviewError):
            av.scan(link,runner=FakeRunner(),now=NOW)

    def test_version_date_parser(self):
        engine,ver,date=av.check_database_version(DB,now=NOW)
        self.assertEqual(engine,"1.4.3")
        self.assertEqual(ver,27999)
        self.assertEqual(date,"2026-11-03")
        with self.assertRaises(av.MalwareReviewError):
            av.check_database_version(DB,now=NOW+timedelta(days=30))

if __name__=="__main__":
    unittest.main()
