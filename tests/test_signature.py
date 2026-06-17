import unittest
import os
import hmac
import hashlib

# Set dummy environment variables before importing app.main
os.environ["WEBHOOK_SECRET"] = "test_secret"
os.environ["GEMINI_API_KEY"] = "test_gemini_key"

from app.main import verify_github_signature

class TestSignatureVerification(unittest.TestCase):
    def test_verify_github_signature_valid(self):
        payload = b'{"action": "opened"}'
        hash_object = hmac.new(b'test_secret', msg=payload, digestmod=hashlib.sha256)
        signature = "sha256=" + hash_object.hexdigest()
        
        self.assertTrue(verify_github_signature(payload, signature))

    def test_verify_github_signature_invalid(self):
        payload = b'{"action": "opened"}'
        signature = "sha256=invalidhash"
        self.assertFalse(verify_github_signature(payload, signature))

    def test_verify_github_signature_missing_header(self):
        payload = b'{"action": "opened"}'
        self.assertFalse(verify_github_signature(payload, ""))

if __name__ == "__main__":
    unittest.main()
