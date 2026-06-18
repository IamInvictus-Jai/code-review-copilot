import unittest
import os
from unittest.mock import patch

# Set dummy environment variables before importing app.main to pass module validation
os.environ["WEBHOOK_SECRET"] = "test_secret"
os.environ["GEMINI_API_KEY"] = "test_gemini_key"

from fastapi.testclient import TestClient
from app.main import app

class TestHealthEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch.dict(os.environ, {
        "ENVIRONMENT": "development",
        "GITHUB_TOKEN": "token_val",
        "GEMINI_API_KEY": "gemini_val",
        "WEBHOOK_SECRET": "secret_val"
    }, clear=True)
    def test_health_check_healthy_development(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["environment"], "development")
        self.assertEqual(data["configuration"], {
            "GITHUB_TOKEN": True,
            "GEMINI_API_KEY": True,
            "WEBHOOK_SECRET": True
        })

    @patch.dict(os.environ, {
        "ENVIRONMENT": "development",
        "GITHUB_TOKEN": "",
        "GEMINI_API_KEY": "gemini_val",
        "WEBHOOK_SECRET": "secret_val"
    }, clear=True)
    def test_health_check_unhealthy_development(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "unhealthy")
        self.assertEqual(data["environment"], "development")
        self.assertEqual(data["configuration"], {
            "GITHUB_TOKEN": False,
            "GEMINI_API_KEY": True,
            "WEBHOOK_SECRET": True
        })

    @patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "GITHUB_TOKEN": "token_val",
        "GEMINI_API_KEY": "gemini_val",
        "WEBHOOK_SECRET": "secret_val",
        "PINECONE_API_KEY": "pinecone_val"
    }, clear=True)
    def test_health_check_healthy_production(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["environment"], "production")
        self.assertEqual(data["configuration"], {
            "GITHUB_TOKEN": True,
            "GEMINI_API_KEY": True,
            "WEBHOOK_SECRET": True,
            "PINECONE_API_KEY": True
        })

    @patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "GITHUB_TOKEN": "token_val",
        "GEMINI_API_KEY": "gemini_val",
        "WEBHOOK_SECRET": "secret_val",
        "PINECONE_API_KEY": ""
    }, clear=True)
    def test_health_check_unhealthy_production_missing_pinecone(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "unhealthy")
        self.assertEqual(data["environment"], "production")
        self.assertEqual(data["configuration"], {
            "GITHUB_TOKEN": True,
            "GEMINI_API_KEY": True,
            "WEBHOOK_SECRET": True,
            "PINECONE_API_KEY": False
        })

if __name__ == "__main__":
    unittest.main()
