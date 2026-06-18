import unittest
import os
from unittest.mock import patch, MagicMock

# Set dummy env vars
os.environ["WEBHOOK_SECRET"] = "test_secret"
os.environ["GEMINI_API_KEY"] = "test_gemini_key"

from fastapi.testclient import TestClient
from app.main import app

class TestConventionsEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("app.services.chroma.get_vector_store")
    def test_learn_convention_endpoint(self, mock_get_vector_store):
        # Mock vector store and its add_texts method
        mock_vs = MagicMock()
        mock_get_vector_store.return_value = mock_vs
        
        response = self.client.post(
            "/conventions/learn",
            json={
                "rule": "Always use logging instead of print",
                "repo_name": "owner/repo"
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "status": "success",
            "message": "Learned new rule: Always use logging instead of print"
        })
        
        mock_get_vector_store.assert_called_once_with("owner/repo")
        mock_vs.add_texts.assert_called_once_with(texts=["Always use logging instead of print"])
