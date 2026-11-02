"""Revocation is a proposed atomic Git change, NOT publication or approval."""
import copy
import pathlib
import sys
import unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import release_governance as g

CERT="b"*64
DIGEST="a"*64
def fixture():
    catalog={"schema_version":1,"apps":[{
        "id":"example","name_fa":"مثال","name_en":"Example",
        "description":"Test release","platforms":["android"],
        "status":"released","version":"1.2.3",
        "download_url":"https://github.com/rezamahrm100-ops/example-repo/releases/download/v1.2.3/example.apk",
        "release_proof":{"sha256":DIGEST,"size_bytes":100,
            "certificate_sha256":CERT,"source_repo":"example-repo",
            "package_id":"ir.hamapp.example","version_code":7}
    }]}
    registry={"schema_version":1,"publishers":[{
        "app_id":"example","source_repo":"example-repo","platform":"android",
        "certificate_sha256":CERT,"package_id":"ir.hamapp.example"
    }]}
    history={"schema_version":1,"revoked_signers":[],"releases":[{
        "app_id":"example","platform":"android","version":"1.2.3",
        "version_code":7,"source_repo":"example-repo",
        "package_id":"ir.hamapp.example","certificate_sha256":CERT,
        "artifact_sha256":DIGEST,"status":"approved"
    }]}
    return catalog,registry,history

class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.catalog,self.registry,self.history=fixture()

    def test_revocation_clears_live_link_and_rejects_replay(self):
        original=copy.deepcopy((self.catalog,self.history))
        result=g.revoke(self.catalog,self.registry,self.history,app_id="example",
                platform="android",version="1.2.3",artifact_sha256=DIGEST)
        app=result["catalog"]["apps"][0]
        self.assertEqual(app["status"],"planned")
        self.assertIsNone(app["download_url"])
        self.assertIsNone(app["version"])
        self.assertNotIn("release_proof",app)
        self.assertEqual(result["history"]["releases"][0]["status"],"revoked")
        self.assertFalse(result["audit"]["files_committed"])
        self.assertFalse(result["audit"]["site_deployed"])
        self.assertTrue(result["audit"]["github_owner_review_required"])
        self.assertEqual(original,(self.catalog,self.history))
        with self.assertRaises(g.GovernanceError):
            g.revoke(result["catalog"],self.registry,result["history"],app_id="example",
                     platform="android",version="1.2.3",artifact_sha256=DIGEST)

    def test_wrong_digest_or_version_never_revokes(self):
        for version,digest in (("1.2.4",DIGEST),("1.2.3","d"*64)):
            with self.subTest(version=version):
                with self.assertRaises(g.GovernanceError):
                    g.revoke(self.catalog,self.registry,self.history,app_id="example",
                             platform="android",version=version,artifact_sha256=digest)

    def test_signer_emergency_revocation_disables_app(self):
        result=g.revoke_signer(self.catalog,self.registry,self.history,CERT)
        self.assertIn(CERT,result["history"]["revoked_signers"])
        self.assertEqual(result["catalog"]["apps"][0]["status"],"planned")
        self.assertEqual(result["audit"]["affected_release_count"],1)
        with self.assertRaises(g.GovernanceError):
            g.revoke_signer(result["catalog"],self.registry,result["history"],CERT)

    def test_unrelated_release_untouched(self):
        self.catalog["apps"].append(dict(self.catalog["apps"][0],id="another",
               status="planned",version=None,download_url=None,release_proof=None))
        result=g.revoke_signer(self.catalog,self.registry,self.history,CERT)
        self.assertEqual(result["catalog"]["apps"][1]["status"],"planned")

    def test_promotion_requires_real_integrated_assessment_and_never_approves(self):
        receipt={"hash_signature_and_github_source_integrated":True,
                 "owner_promotion_approved":False,"public_distribution_authorized":False,
                 "release":{"artifact_sha256":DIGEST},
                 "verified_provenance":{"artifact_sha256":DIGEST}}
        with patch.object(g.integrated_release_review,"assess",return_value=receipt) as verified:
            result=g.plan_promotion({"release":{}},self.registry,self.history,"unused.apk",
                        "approved-workflow","refs/tags/v1.2.3")
        verified.assert_called_once()
        self.assertFalse(result["public_distribution_authorized"])
        self.assertTrue(result["github_owner_review_required"])
        self.assertFalse(result["malware_permission_review_complete"])

    def test_promotion_rejects_signature_failure(self):
        with patch.object(g.integrated_release_review,"assess",side_effect=ValueError("bad signer")):
            with self.assertRaises(ValueError):
                g.plan_promotion({"release":{}},self.registry,self.history,"unused.apk",
                                 "approved-workflow","refs/tags/v1.2.3")
