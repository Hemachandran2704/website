import unittest
import json
import time
import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app import app

class TestRegisterFlow(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.test_email = f"test_user_{int(time.time() * 1000)}@magnus.com"

    def test_01_register_page_html(self):
        """Fetch Register page and verify all required elements are present"""
        r = self.client.get("/register")
        self.assertEqual(r.status_code, 200)
        html = r.data.decode("utf-8")
        self.assertIn('id="name"', html)
        self.assertIn('id="email"', html)
        self.assertIn('id="password"', html)
        self.assertIn('id="confirm_password"', html)
        self.assertIn('id="register-form"', html)

    def test_02_validation_empty_inputs(self):
        """Validation: Empty inputs"""
        r = self.client.post("/api/auth/register",
                             data=json.dumps({
                                 "name": "",
                                 "email": "",
                                 "password": "",
                                 "confirm_password": ""
                             }),
                             content_type="application/json")
        res = json.loads(r.data)
        self.assertIn(r.status_code, (400, 422))
        self.assertFalse(res.get("success"))

    def test_03_validation_password_mismatch(self):
        """Validation: Password mismatch"""
        r = self.client.post("/api/auth/register",
                             data=json.dumps({
                                 "name": "Jane Doe",
                                 "email": "janedoe@example.com",
                                 "password": "Password123!",
                                 "confirm_password": "MismatchPassword!"
                             }),
                             content_type="application/json")
        res = json.loads(r.data)
        self.assertEqual(r.status_code, 400)
        self.assertFalse(res.get("success"))

    def test_04_successful_registration_requires_separate_login(self):
        """Successful registration creates an account; login then opens the dashboard."""
        r = self.client.post("/api/auth/register",
                             data=json.dumps({
                                 "name": "Jane Doe",
                                 "email": self.test_email,
                                 "password": "Password123!",
                                 "confirm_password": "Password123!"
                             }),
                             content_type="application/json")
        res = json.loads(r.data)
        self.assertEqual(r.status_code, 201)
        self.assertTrue(res.get("success"))
        self.assertNotIn("token", res["data"])
        self.assertIn("user", res["data"])
        self.assertEqual(res["data"]["user"]["role"], "user")

        # Registration does not start an authenticated session.
        r_home = self.client.get("/home", follow_redirects=False)
        self.assertEqual(r_home.status_code, 302)
        self.assertEqual(r_home.headers.get("Location"), "/login")

        login = self.client.post("/api/auth/login", data=json.dumps({
            "email": self.test_email,
            "password": "Password123!"
        }), content_type="application/json")
        self.assertEqual(login.status_code, 200)
        self.assertEqual(self.client.get("/home").status_code, 200)

        # Duplicate registration returns error
        r_dup = self.client.post("/api/auth/register",
                                 data=json.dumps({
                                     "name": "Duplicate User",
                                     "email": self.test_email,
                                     "password": "Password123!",
                                     "confirm_password": "Password123!"
                                 }),
                                 content_type="application/json")
        res_dup = json.loads(r_dup.data)
        self.assertIn(r_dup.status_code, (400, 409))
        self.assertFalse(res_dup.get("success"))

if __name__ == "__main__":
    unittest.main()
