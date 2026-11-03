"""Actual private-on-disk intake tests. Never store production apps in CI."""
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import private_publisher_inbox as inbox

@unittest.skipUnless(os.name=="posix", "POSIX-only owner file permissions")
class PrivateSubmissionTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.workspace=Path(tmp.name)
        self.root=inbox.init_root(self.workspace/"sealed-inbox")
        self.artifact=self.workspace/"owner-review.apk"
        with zipfile.ZipFile(self.artifact,"w",compression=zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr("AndroidManifest.xml",b"synthetic only, no executable content")
        digest=hashlib.sha256(self.artifact.read_bytes()).hexdigest()
        self.candidate={
            "source_repo":"example-repo", "source_sha":"a"*40,
            "package_id":"ir.hamapp.example", "version_code":7,
            "release":{
                "app_id":"example","platform":"android","version":"1.2.3",
                "asset_url":"https://github.com/rezamahrm100-ops/example-repo/releases/download/v1.2.3/owner-review.apk",
                "sha256":digest,"size_bytes":self.artifact.stat().st_size
            }
        }
        self.uid="f"*32

    def stage(self):
        return inbox.stage(self.root,self.candidate,self.artifact,"example-repo",
                           make_id=lambda n:self.uid)

    def test_really_copies_bytes_off_repository_with_private_modes(self):
        original=copy.deepcopy(self.candidate)
        result=self.stage()
        folder=self.root/self.uid
        self.assertEqual(result["status"],"quarantined")
        self.assertFalse(result["publisher_identity_authenticated"])
        self.assertFalse(result["owner_release_approved"])
        self.assertFalse(result["production_distribution_authorized"])
        self.assertTrue(result["archive_structure_checked"])
        self.assertEqual((folder/"candidate.apk").read_bytes(),self.artifact.read_bytes())
        self.assertEqual(stat.S_IMODE((folder/"candidate.apk").stat().st_mode),0o600)
        self.assertEqual(stat.S_IMODE(folder.stat().st_mode),0o700)
        self.assertEqual(inbox.verify_events(folder)[0],"quarantined")
        self.assertEqual(self.candidate,original)
        self.assertFalse((ROOT/"catalog"/"apps.json").read_text(encoding="utf8").count(self.uid))
        self.assertEqual(json.loads((folder/"submission.json").read_text())["artifact_sha256"],
                         self.candidate["release"]["sha256"])

    def test_source_mismatch_never_creates_private_package(self):
        self.candidate["release"]["sha256"]="b"*64
        with self.assertRaises(ValueError):
            self.stage()
        self.assertFalse((self.root/self.uid).exists())

    def test_untrusted_cross_repo_and_claimed_tenant_rejected(self):
        self.candidate["source_repo"]="different"
        with self.assertRaises(ValueError):
            self.stage()
        self.candidate["source_repo"]="example-repo"
        with self.assertRaises(ValueError):
            inbox.stage(self.root,self.candidate,self.artifact,"attacker",
                        make_id=lambda n:self.uid)

    def test_rejects_symlinks_hardlinks_and_non_private_root(self):
        alias=self.workspace/"link.apk"
        alias.symlink_to(self.artifact)
        with self.assertRaises(inbox.QuarantineError):
            inbox.stage(self.root,self.candidate,alias,"example-repo")
        link=self.workspace/"hardlink.apk"
        os.link(self.artifact,link)
        with self.assertRaises(inbox.QuarantineError):
            self.stage()
        link.unlink()
        self.root.chmod(0o755)
        with self.assertRaises(inbox.QuarantineError):
            self.stage()

    def test_replays_and_unsafe_submission_ids_rejected(self):
        self.stage()
        with self.assertRaises(inbox.QuarantineError):
            self.stage()
        with self.assertRaises(inbox.QuarantineError):
            inbox.load(self.root,"../data")
        with self.assertRaises(inbox.QuarantineError):
            inbox.stage(self.root,self.candidate,self.artifact,"example-repo",
                        make_id=lambda n:"../etc")

    def test_review_events_append_only_and_cannot_grant_approval(self):
        self.stage()
        folder=self.root/self.uid
        r=inbox.transition(self.root,self.uid,"request_review")
        self.assertEqual(r["status"],"review_requested")
        self.assertFalse(r["public_distribution_authorized"])
        self.assertEqual(inbox.verify_events(folder)[0],"review_requested")
        self.assertEqual(inbox.transition(self.root,self.uid,"hold")["status"],"held")
        self.assertEqual(inbox.transition(self.root,self.uid,"reject")["status"],"rejected")
        with self.assertRaises(inbox.QuarantineError):
            inbox.transition(self.root,self.uid,"request_review")
        with self.assertRaises(inbox.QuarantineError):
            inbox.transition(self.root,self.uid,"approve")
        self.assertEqual(len(list((folder/"events").iterdir())),4)

    def test_only_review_requested_exact_bytes_can_enter_real_intake(self):
        self.stage()
        with self.assertRaises(inbox.QuarantineError):
            inbox.load_for_preflight(self.root, self.uid)
        inbox.transition(self.root, self.uid, "request_review")
        candidate, path, proof = inbox.load_for_preflight(self.root, self.uid)
        self.assertEqual(candidate, self.candidate)
        self.assertEqual(path.read_bytes(), self.artifact.read_bytes())
        self.assertFalse(proof["publisher_identity_authenticated"])
        path.write_bytes(b"tampered after quarantining")
        with self.assertRaises(ValueError):
            inbox.load_for_preflight(self.root, self.uid)

    def test_rejected_item_never_passes_owner_intake(self):
        self.stage()
        inbox.transition(self.root, self.uid, "reject")
        with self.assertRaises(inbox.QuarantineError):
            inbox.load_for_preflight(self.root, self.uid)

    def test_post_stage_source_metadata_mutation_is_rejected(self):
        self.stage()
        inbox.transition(self.root, self.uid, "request_review")
        path=self.root/self.uid/"candidate.json"
        altered=copy.deepcopy(self.candidate)
        altered["source_sha"]="b"*40
        path.write_text(json.dumps(altered),encoding="utf8")
        with self.assertRaises(inbox.QuarantineError):
            inbox.load_for_preflight(self.root, self.uid)

    def test_corrupted_event_chain_or_reordering_is_rejected(self):
        self.stage()
        folder=self.root/self.uid
        event=folder/"events"/"000001.json"
        data=json.loads(event.read_text())
        data["owner_review_approved"]=True
        event.write_text(json.dumps(data))
        with self.assertRaises(inbox.QuarantineError):
            inbox.verify_events(folder)
        with self.assertRaises(inbox.QuarantineError):
            inbox.transition(self.root,self.uid,"hold")

    def test_collision_between_separate_publishers_does_not_overwrite(self):
        self.stage()
        original=(self.root/self.uid/"candidate.apk").read_bytes()
        with self.assertRaises(inbox.QuarantineError):
            self.stage()
        self.assertEqual((self.root/self.uid/"candidate.apk").read_bytes(),original)

    def test_public_project_checkout_destination_blocked(self):
        with self.assertRaises(inbox.QuarantineError):
            inbox.init_root(ROOT/"catalog")

    def test_quarantine_windows_binary_without_dangerous_zip_unpacking(self):
        exe=self.workspace/"safe.exe"
        exe.write_bytes(b"synthetic Windows test bytes")
        candidate=copy.deepcopy(self.candidate)
        candidate["release"].update(platform="windows",asset_url=(
            "https://github.com/rezamahrm100-ops/example-repo/releases/download/v1.2.3/safe.exe"),
            sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),size_bytes=exe.stat().st_size)
        candidate["package_id"]=None
        candidate["version_code"]=None
        result=inbox.stage(self.root,candidate,exe,"example-repo",
                           make_id=lambda n:"e"*32)
        self.assertFalse(result["archive_structure_checked"])
        self.assertFalse(result["developer_certificate_verified"])
        self.assertFalse(result["production_distribution_authorized"])

if __name__=="__main__":
    unittest.main()
