"""
StegoShield Web API and Security Header Tests
"""

import unittest
import json
import os
import io
from PIL import Image

from app import app
from steganography.utils import generate_unique_filename


class TestWebAPI(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_health_check_endpoint(self):
        """Verifies that /health returns 200 OK and healthy status for cloud monitors."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("service"), "stegoshield")

    def test_security_headers_present(self):
        """Verifies that all OWASP-recommended security headers are set."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'SAMEORIGIN')
        self.assertEqual(response.headers.get('X-XSS-Protection'), '1; mode=block')
        self.assertIn('Content-Security-Policy', response.headers)

    def test_hsts_header_on_https(self):
        """Verifies that Strict-Transport-Security is set when requested via HTTPS."""
        response = self.client.get('/', headers={'X-Forwarded-Proto': 'https'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Strict-Transport-Security', response.headers)

    def test_manifest_and_sw_routes(self):
        """Verifies that PWA manifest.json and sw.js are served with appropriate headers."""
        resp_manifest = self.client.get('/manifest.json')
        self.assertEqual(resp_manifest.status_code, 200)
        self.assertIn('manifest+json', resp_manifest.headers.get('Content-Type', ''))
        resp_manifest.close()

        resp_sw = self.client.get('/sw.js')
        self.assertEqual(resp_sw.status_code, 200)
        self.assertEqual(resp_sw.headers.get('Service-Worker-Allowed'), '/')
        resp_sw.close()


    def test_api_wipe_existing_file(self):
        """Verifies that /api/wipe securely deletes ephemeral output files."""
        # Create a mock output file
        test_filename = generate_unique_filename("png")
        test_path = os.path.join(self.app.config['OUTPUT_FOLDER'], test_filename)
        with open(test_path, 'wb') as f:
            f.write(b"mock stego png data")

        self.assertTrue(os.path.exists(test_path))

        response = self.client.post(f'/api/wipe/{test_filename}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data.get("success"))
        self.assertFalse(os.path.exists(test_path))

    def test_api_wipe_nonexistent_file(self):
        """Verifies that wiping a non-existent file returns 404 gracefully."""
        response = self.client.post('/api/wipe/stego_nonexistent.png')
        self.assertEqual(response.status_code, 404)

    def test_api_inspect_without_file(self):
        """Verifies that calling /api/inspect without file returns 400 Bad Request."""
        response = self.client.post('/api/inspect')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data.get("success"))


if __name__ == '__main__':
    unittest.main()
