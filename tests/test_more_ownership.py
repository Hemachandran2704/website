import io
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app import app


class TestMoreRecordOwnership(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.owner_headers = self._login("user@magnus.com", "UserPassword123!")
        self.other_headers = self._login("demo@magnus.com", "AdminPassword123!")

    def _login(self, email, password):
        response = self.client.post("/api/auth/login", json={"email": email, "password": password})
        self.assertEqual(response.status_code, 200, response.get_json())
        return {"Authorization": f"Bearer {response.get_json()['data']['token']}"}

    def _assert_owned_crud(self, endpoint, payload, changed_field, changed_value):
        created = self.client.post(f"/api/{endpoint}", headers=self.owner_headers, json=payload)
        self.assertEqual(created.status_code, 201, created.get_json())
        record_id = created.get_json()["data"]["id"]

        owner_rows = self.client.get(f"/api/{endpoint}", headers=self.owner_headers).get_json()["data"]
        owner_row = next(row for row in owner_rows if row["id"] == record_id)
        self.assertTrue(owner_row["can_manage"])
        self.assertNotIn("user_id", owner_row)

        other_rows = self.client.get(f"/api/{endpoint}", headers=self.other_headers).get_json()["data"]
        self.assertFalse(any(row["id"] == record_id for row in other_rows))
        self.assertEqual(self.client.get(f"/api/{endpoint}/{record_id}", headers=self.other_headers).status_code, 404)

        updated_payload = dict(payload)
        updated_payload[changed_field] = changed_value
        self.assertEqual(
            self.client.put(f"/api/{endpoint}/{record_id}", headers=self.other_headers, json=updated_payload).status_code,
            404,
        )
        self.assertEqual(self.client.delete(f"/api/{endpoint}/{record_id}", headers=self.other_headers).status_code, 404)
        self.assertEqual(
            self.client.put(f"/api/{endpoint}/{record_id}", headers=self.owner_headers, json=updated_payload).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(f"/api/{endpoint}/{record_id}", headers=self.owner_headers).get_json()["data"][changed_field],
            changed_value,
        )
        self.assertEqual(self.client.delete(f"/api/{endpoint}/{record_id}", headers=self.owner_headers).status_code, 200)

    def test_json_more_modules_are_owner_scoped(self):
        cases = [
            ("tabs", {"title": "ownership test tab", "content": "initial", "status": "active"}, "title", "updated tab"),
            ("menus", {"name": "ownership test menu", "url": "/ownership-test", "status": "active"}, "name", "updated menu"),
            ("autocomplete", {"label": "ownership test autocomplete", "value": "ownership_test", "description": "initial", "status": "active"}, "label", "updated autocomplete"),
            ("collapsible", {"title": "ownership test collapsible", "content": "initial", "status": "active"}, "title", "updated collapsible"),
            ("tooltips", {"element_name": "ownership-test-tooltip", "content": "initial", "position": "top", "status": "active"}, "content", "updated tooltip"),
            ("popups", {"title": "ownership test popup", "content": "initial", "trigger_type": "manual", "status": "active"}, "content", "updated popup"),
            ("links", {"title": "ownership test link", "url": "/ownership-test", "target": "_self", "description": "initial", "status": "active"}, "url", "/ownership-test-updated"),
            ("css-properties", {"property_name": "font-size", "property_value": "13px", "selector": ".ownership-test", "status": "active"}, "property_value", "15px"),
            ("iframes", {"title": "ownership test iframe", "url": "https://example.com/ownership-test", "status": "active"}, "title", "updated iframe"),
        ]
        for case in cases:
            with self.subTest(endpoint=case[0]):
                self._assert_owned_crud(*case)

    def test_image_and_slider_ownership(self):
        image_response = self.client.post(
            "/api/images",
            headers=self.owner_headers,
            data={
                "title": "ownership test image",
                "status": "active",
                "image_file": (io.BytesIO(b"image-data"), "ownership-test.png", "image/png"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(image_response.status_code, 201, image_response.get_json())
        image_id = image_response.get_json()["data"]["id"]
        file_path = image_response.get_json()["data"]["file_path"]

        owner_file_client = app.test_client()
        owner_file_client.post("/api/auth/login", json={"email": "user@magnus.com", "password": "UserPassword123!"})
        other_file_client = app.test_client()
        other_file_client.post("/api/auth/login", json={"email": "demo@magnus.com", "password": "AdminPassword123!"})
        owned_file = owner_file_client.get(f"/uploads/{file_path}")
        self.assertEqual(owned_file.status_code, 200)
        owned_file.close()
        self.assertEqual(other_file_client.get(f"/uploads/{file_path}").status_code, 404)
        self.assertEqual(app.test_client().get(f"/uploads/{file_path}").status_code, 404)

        slider_payload = {
            "title": "ownership test slide",
            "description": "initial",
            "image_id": image_id,
            "display_order": 994,
            "status": "active",
        }
        self.assertEqual(self.client.post("/api/sliders", headers=self.other_headers, json=slider_payload).status_code, 400)
        self._assert_owned_crud("sliders", slider_payload, "title", "updated slide")

        self.assertEqual(self.client.get(f"/api/images/{image_id}", headers=self.other_headers).status_code, 404)
        self.assertEqual(
            self.client.put(f"/api/images/{image_id}", headers=self.other_headers, json={"title": "stolen"}).status_code,
            404,
        )
        self.assertEqual(self.client.delete(f"/api/images/{image_id}", headers=self.other_headers).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/images/{image_id}", headers=self.owner_headers).status_code, 200)

    def test_document_delete_is_owner_only_even_for_admin(self):
        created = self.client.post(
            "/api/documents",
            headers=self.owner_headers,
            data={"title": "ownership test document", "category": "General"},
            content_type="multipart/form-data",
        )
        self.assertEqual(created.status_code, 201, created.get_json())
        document_id = created.get_json()["data"]["id"]

        self.assertEqual(
            self.client.delete(f"/api/documents/{document_id}", headers=self.other_headers).status_code,
            404,
        )
        with patch(
            "backend.middleware.auth_middleware.AuthService.get_user_by_id",
            return_value={"id": 1, "role": "admin", "status": "active"},
        ):
            self.assertEqual(
                self.client.delete(f"/api/documents/{document_id}", headers=self.owner_headers).status_code,
                404,
            )

        self.assertEqual(
            self.client.delete(f"/api/documents/{document_id}", headers=self.owner_headers).status_code,
            200,
        )


if __name__ == "__main__":
    unittest.main()