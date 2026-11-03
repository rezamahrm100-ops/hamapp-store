"""Actual temporary SQLite/tar source tests for official F-Droid app DB probe.

Only the hosted Android emulator job can prove a REAL official app persisted a
repo. These unit tests cannot create a false in-app repository registration.
"""
import io
import os
from pathlib import Path
import sqlite3
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import fdroid_official_repo_db_probe as probe


class OfficialFdroidRepositoryPersistenceProofTests(unittest.TestCase):
    def setUp(self):
        work=tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.path=Path(work.name)

    def _sqlite(self, host="10.0.2.2:8975", *, table="Repository"):
        p=self.path/"source.sqlite"
        db=sqlite3.connect(p)
        try:
            db.execute('CREATE TABLE "'+table+'" (id INTEGER PRIMARY KEY, url TEXT NOT NULL)')
            db.execute('INSERT INTO "'+table+'" (id,url) VALUES (?,?)',
                       (3,"https://"+host+"/fdroid/repo/"))
            db.commit()
        finally:
            db.close()
        return p

    def _tar(self, paths):
        output=io.BytesIO()
        with tarfile.open(fileobj=output,mode="w") as z:
            for name,data in paths:
                record=tarfile.TarInfo(name)
                record.size=len(data)
                z.addfile(record,io.BytesIO(data))
        return output.getvalue()

    def test_real_sqlite_persistence_read_only_and_wrong_host_rejected(self):
        p=self._sqlite()
        self.assertEqual(probe.inspect_sqlite(p),["Repository"])
        self.assertEqual(probe.inspect_sqlite(p,"10.0.2.2:9001"),[])
        db=sqlite3.connect(p)
        try:
            rows=db.execute("SELECT COUNT(*) FROM Repository").fetchone()
        finally:
            db.close()
        self.assertEqual(rows,(1,))

    def test_mismatched_non_repo_table_does_not_count(self):
        p=self._sqlite(table="ExternalLink")
        self.assertEqual(probe.inspect_sqlite(p),[])

    def test_real_tar_unpack_exact_path_and_db_magic(self):
        db=self._sqlite().read_bytes()
        raw=self._tar([("databases/fdroid.sqlite",db)])
        result=probe.validate_tar_snapshot(raw,self.path)
        self.assertEqual(len(result),1)
        self.assertEqual(probe.inspect_sqlite(result[0]),["Repository"])
        # Windows mode bits are synthetic; actual hosted POSIX private 0600
        # enforcement is separately checked by the real Android CI job.
        if os.name == "posix":
            self.assertEqual(result[0].stat().st_mode & 0o077,0)

    def test_tar_traversal_symlinks_and_duplicate_files_fail_closed(self):
        for path in ("databases/../tokens", "../private.db","databases/evil/key",
                     "/databases/secret", "databases/.hidden", "unrelated.txt"):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as tmp:
                raw=self._tar([(path,b"anything")])
                with self.assertRaises(probe.RepositoryPersistenceError):
                    probe.validate_tar_snapshot(raw,Path(tmp))
        with tempfile.TemporaryDirectory() as tmp:
            raw=self._tar([("databases/a.db",b"first"),("databases/a.db",b"second")])
            with self.assertRaises(probe.RepositoryPersistenceError):
                probe.validate_tar_snapshot(raw,Path(tmp))
        with tempfile.TemporaryDirectory() as tmp:
            out=io.BytesIO()
            with tarfile.open(fileobj=out,mode="w") as archive:
                record=tarfile.TarInfo("databases/linked.db")
                record.type=tarfile.SYMTYPE
                record.linkname="../../private"
                archive.addfile(record)
            with self.assertRaises(probe.RepositoryPersistenceError):
                probe.validate_tar_snapshot(out.getvalue(),Path(tmp))

    def test_actual_emulator_gate_denies_untrusted_host(self):
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"false","RUNNER_OS":"Linux"}):
            with self.assertRaises(probe.RepositoryPersistenceError):
                probe.verify("a"*40,"B"*64,self.path/"receipt.json")

    def test_hosted_workflow_must_not_upload_private_sqlite_bytes(self):
        source=(ROOT/"scripts/fdroid_real_client_subscription_emulator.sh").read_text("utf-8")
        workflow=(ROOT/".github/workflows/fdroid-real-client-signed-repo.yml").read_text("utf-8")
        probe_source=(ROOT/"scripts/fdroid_official_repo_db_probe.py").read_text("utf-8")
        self.assertIn("scripts/fdroid_official_repo_db_probe.py",source)
        self.assertIn("private-repository-db-proof.json",source)
        self.assertIn("scripts/fdroid_official_repo_db_probe.py",workflow)
        self.assertIn("private-repository-db-proof.json",workflow)
        self.assertIn("max",probe_source.lower())
        self.assertIn('"client_installed_apk_from_repo_verified": False',probe_source)
        self.assertIn('"client_updated_apk_from_repo_verified": False',probe_source)
        self.assertNotIn("dist/fdroid-real-client-probe/fdroid.sqlite",workflow)
        self.assertNotIn("runs-on: self-hosted",workflow)


if __name__=="__main__":
    unittest.main()
