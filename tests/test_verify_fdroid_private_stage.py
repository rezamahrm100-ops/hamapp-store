"""Synthetic F-Droid index fixtures test policy, NOT a production signing key."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import verify_fdroid_private_stage as verifier

FP="A"*64
DATA=b"test binary owner-only synthetic fixture"

class IndexV2Tests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.repo=self.root/"repo"
        self.repo.mkdir()
        self.jar=self.repo/"entry.jar"
        self.jar.write_bytes(b"TEST-ONLY-NOT-A-REAL-SIGNED-JAR")
        self.candidate={
            "release":{"app_id":"example","platform":"android","version":"1.2.3",
                "asset_url":"https://github.com/rezamahrm100-ops/source-demo/releases/download/v1.2.3/demo.apk",
                "sha256":hashlib.sha256(DATA).hexdigest(),"size_bytes":len(DATA)},
            "source_repo":"source-demo","source_sha":"a"*40,
            "package_id":"ir.hamapp.example","version_code":7
        }
        self.index={"repo":{"name":{"en-US":"test"}},"packages":{
            "ir.hamapp.example":{"metadata":{},"versions":{
                "version-key":{"file":{"name":"/demo.apk",
                                       "sha256":hashlib.sha256(DATA).hexdigest(),
                                       "size":len(DATA)},
                               "manifest":{"versionCode":7,"versionName":"1.2.3"}}
            }}
        }}
        self.write_index()

    def write_index(self):
        self.raw=json.dumps(self.index,sort_keys=True,separators=(",",":")).encode()
        (self.repo/"index-v2.json").write_bytes(self.raw)
        self.entry={"index":{"name":"/index-v2.json",
                             "sha256":hashlib.sha256(self.raw).hexdigest(),
                             "size":len(self.raw)}}
    def loader(self, filename, fingerprint):
        self.assertEqual(filename,str(self.jar))
        self.assertEqual(fingerprint,FP)
        return self.entry,b"fake-public-key",FP

    def test_verified_signed_entry_links_exact_version_sha_and_size(self):
        receipt=verifier.verify(self.root,FP,self.candidate,loader=self.loader)
        self.assertTrue(receipt["local_index_signed_with_pinned_repository_key"])
        self.assertFalse(receipt["public_https_repository_verified"])
        self.assertFalse(receipt["official_fdroid_client_install_tested"])
        self.assertFalse(receipt["production_store_ready"])
        self.assertEqual(receipt["indexed_apk_sha256"],self.candidate["release"]["sha256"])

    def test_missing_index_or_untrusted_symlink_rejected(self):
        (self.repo/"index-v2.json").unlink()
        with self.assertRaises(verifier.PrivateIndexError):
            verifier.verify(self.root,FP,self.candidate,loader=self.loader)
        (self.repo/"index-v2.json").symlink_to(self.jar)
        with self.assertRaises(verifier.PrivateIndexError):
            verifier.verify(self.root,FP,self.candidate,loader=self.loader)

    def test_mismatched_signed_entry_digest_rejected(self):
        self.entry["index"]["sha256"]="b"*64
        with self.assertRaises(verifier.PrivateIndexError):
            verifier.verify(self.root,FP,self.candidate,loader=self.loader)

    def test_wrong_certificate_rejected(self):
        def fake(*args, **kwargs):
            return self.entry,b"key","B"*64
        with self.assertRaises(verifier.PrivateIndexError):
            verifier.verify(self.root,FP,self.candidate,loader=fake)
        with self.assertRaises(verifier.PrivateIndexError):
            verifier.verify(self.root,"not-a-fingerprint",self.candidate,loader=self.loader)

    def test_signed_index_has_to_list_exact_candidate_sha_version_and_size(self):
        for key,value in [("sha256","b"*64),("size",99)]:
            with self.subTest(key=key):
                self.index["packages"]["ir.hamapp.example"]["versions"]["version-key"]["file"][key]=value
                self.write_index()
                with self.assertRaises(verifier.PrivateIndexError):
                    verifier.verify(self.root,FP,self.candidate,loader=self.loader)
                self.index["packages"]["ir.hamapp.example"]["versions"]["version-key"]["file"][key]=(
                    len(DATA) if key=="size" else hashlib.sha256(DATA).hexdigest())
        self.index["packages"]["ir.hamapp.example"]["versions"]["version-key"]["manifest"]["versionCode"]=8
        self.write_index()
        with self.assertRaises(verifier.PrivateIndexError):
            verifier.verify(self.root,FP,self.candidate,loader=self.loader)

    def test_duplicated_same_candidate_in_versions_rejected(self):
        versions=self.index["packages"]["ir.hamapp.example"]["versions"]
        versions["duplicate"]=dict(versions["version-key"])
        self.write_index()
        with self.assertRaises(verifier.PrivateIndexError):
            verifier.verify(self.root,FP,self.candidate,loader=self.loader)

    def test_invalid_or_unverified_upstream_jar_is_not_accepted(self):
        def fail(*args, **kwargs):
            raise RuntimeError("JAR signature verification failed")
        with self.assertRaises(verifier.PrivateIndexError):
            verifier.verify(self.root,FP,self.candidate,loader=fail)

if __name__=="__main__":
    unittest.main()
