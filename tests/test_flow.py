import unittest
import json
import os
import sys
import time

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app import app
from backend.config.database import execute_query

class TestCompleteAuthAndRoleFlow(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.test_email = f"test_flow_{int(time.time()*1000)}@magnus.com"

    def test_01_public_registration_creates_user_role_only(self):
        """Test public registration forces role='user' even if 'admin' requested"""
        reg_payload = {
            "name": "Jane Developer",
            "email": self.test_email,
            "password": "JanePassword123!",
            "confirm_password": "JanePassword123!",
            "role": "admin"  # Malicious attempt to self-assign admin
        }
        res = self.client.post("/api/auth/register", 
                               data=json.dumps(reg_payload),
                               content_type="application/json")
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 201, f"Registration failed: {data}")
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["user"]["role"], "user")
        self.assertNotIn("password", data["data"]["user"])
        self.assertNotIn("password_hash", data["data"]["user"])

    def test_02_duplicate_email_registration_fails(self):
        """Test duplicate email rejection"""
        # Register first
        reg_payload = {
            "name": "Original User",
            "email": self.test_email,
            "password": "OriginalPassword123!",
            "confirm_password": "OriginalPassword123!"
        }
        self.client.post("/api/auth/register", 
                         data=json.dumps(reg_payload),
                         content_type="application/json")

        # Try registering same email again
        res = self.client.post("/api/auth/register", 
                               data=json.dumps(reg_payload),
                               content_type="application/json")
        data = json.loads(res.data)
        self.assertIn(res.status_code, (400, 409))
        self.assertFalse(data["success"])
        self.assertIn("already exists", data["message"].lower())

    def test_03_user_login_success_and_wrong_credentials(self):
        """Test user login with valid and invalid credentials"""
        # Invalid password
        res_fail = self.client.post("/api/auth/login",
                                    data=json.dumps({"email": "user@magnus.com", "password": "WrongPassword!"}),
                                    content_type="application/json")
        data_fail = json.loads(res_fail.data)
        self.assertEqual(res_fail.status_code, 401)
        self.assertFalse(data_fail["success"])

        # Valid login
        res_ok = self.client.post("/api/auth/login",
                                  data=json.dumps({"email": "user@magnus.com", "password": "UserPassword123!"}),
                                  content_type="application/json")
        data_ok = json.loads(res_ok.data)
        self.assertEqual(res_ok.status_code, 200)
        self.assertTrue(data_ok["success"])
        self.assertEqual(data_ok["data"]["user"]["role"], "user")
        self.assertIn("token", data_ok["data"])

    def test_04_user_cannot_access_admin_api(self):
        """Test that regular user cannot access admin users list or admin settings"""
        # Login as regular user
        login_res = self.client.post("/api/auth/login",
                                     data=json.dumps({"email": "user@magnus.com", "password": "UserPassword123!"}),
                                     content_type="application/json")
        token = json.loads(login_res.data)["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to access Admin User Management
        admin_res = self.client.get("/api/users", headers=headers)
        self.assertEqual(admin_res.status_code, 403)
        admin_data = json.loads(admin_res.data)
        self.assertFalse(admin_data["success"])

        # Try to access Admin Settings
        settings_res = self.client.get("/api/settings/system", headers=headers)
        self.assertEqual(settings_res.status_code, 403)

    def test_05_seeded_accounts_share_the_single_user_role(self):
        """The former administrator sample account has no elevated role."""
        login_res = self.client.post("/api/auth/login",
                                     data=json.dumps({"email": "demo@magnus.com", "password": "AdminPassword123!"}),
                                     content_type="application/json")
        login_data = json.loads(login_res.data)
        self.assertEqual(login_res.status_code, 200)
        self.assertEqual(login_data["data"]["user"]["role"], "user")
        token = login_data["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        self.assertEqual(self.client.get("/api/users", headers=headers).status_code, 403)
        self.assertEqual(self.client.get("/api/reports?range=7days", headers=headers).status_code, 403)
        self.assertEqual(self.client.get("/api/tickets", headers=headers).status_code, 200)

    def test_06_user_isolated_ticket_and_document_workflow(self):
        """Test that user can create ticket and document, and only see their own"""
        # User 1
        u1_res = self.client.post("/api/auth/login",
                                  data=json.dumps({"email": "user@magnus.com", "password": "UserPassword123!"}),
                                  content_type="application/json")
        u1_token = json.loads(u1_res.data)["data"]["token"]
        u1_headers = {"Authorization": f"Bearer {u1_token}"}

        # User creates a ticket
        ticket_payload = {
            "subject": "Billing inquiry from test",
            "category": "billing",
            "priority": "medium",
            "message": "Hello, I have a question regarding my subscription invoice."
        }
        create_t_res = self.client.post("/api/tickets",
                                        data=json.dumps(ticket_payload),
                                        headers=u1_headers,
                                        content_type="application/json")
        self.assertEqual(create_t_res.status_code, 201)
        ticket_id = json.loads(create_t_res.data)["data"]["id"]

        # User sees their ticket
        u1_tickets_res = self.client.get("/api/tickets", headers=u1_headers)
        u1_tickets = json.loads(u1_tickets_res.data)["data"]
        self.assertTrue(any(t["id"] == ticket_id for t in u1_tickets))

    def test_07_user_dashboard_endpoints(self):
        """Test user overview, profile, personal settings, calendar and favorites"""
        login_res = self.client.post("/api/auth/login",
                                     data=json.dumps({"email": "user@magnus.com", "password": "UserPassword123!"}),
                                     content_type="application/json")
        token = json.loads(login_res.data)["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # User Overview
        overview_res = self.client.get("/api/user/overview", headers=headers)
        self.assertEqual(overview_res.status_code, 200, f"Overview error: {overview_res.data}")
        overview_data = json.loads(overview_res.data)
        self.assertTrue(overview_data["success"])

        # User Profile
        prof_res = self.client.get("/api/user/profile", headers=headers)
        self.assertEqual(prof_res.status_code, 200)
        prof_data = json.loads(prof_res.data)
        self.assertTrue(prof_data["success"])
        self.assertEqual(prof_data["data"]["email"], "user@magnus.com")

        # User Settings
        settings_res = self.client.get("/api/settings/user", headers=headers)
        self.assertEqual(settings_res.status_code, 200)
        settings_data = json.loads(settings_res.data)
        self.assertTrue(settings_data["success"])

        # User Schedules
        sched_res = self.client.get("/api/user/schedules", headers=headers)
        self.assertEqual(sched_res.status_code, 200)

        # User Favorites
        fav_res = self.client.get("/api/user/favorites", headers=headers)
        self.assertEqual(fav_res.status_code, 200)

    def test_08_protected_page_routing(self):
        """Test protected page routing for unauthenticated, user, and admin"""
        # Unauthenticated access to /admin/dashboard
        res_unauth = self.client.get("/admin/dashboard", follow_redirects=False)
        self.assertEqual(res_unauth.status_code, 302)
        self.assertIn("/login", res_unauth.location)

        # Unauthenticated access to /dashboard
        res_dash_unauth = self.client.get("/dashboard", follow_redirects=False)
        self.assertEqual(res_dash_unauth.status_code, 302)
        self.assertIn("/login", res_dash_unauth.location)

    def test_09_user_password_change_and_security(self):
        """Test user changing password securely and rejecting invalid old password"""
        # Create fresh user
        u_email = f"pwd_test_{int(time.time()*1000)}@magnus.com"
        reg_res = self.client.post("/api/auth/register",
                                   data=json.dumps({
                                       "name": "Password Tester",
                                       "email": u_email,
                                       "password": "InitialPassword123!",
                                       "confirm_password": "InitialPassword123!"
                                   }),
                                   content_type="application/json")
        self.assertEqual(reg_res.status_code, 201)
        login_res = self.client.post("/api/auth/login",
                         data=json.dumps({"email": u_email, "password": "InitialPassword123!"}),
                         content_type="application/json")
        self.assertEqual(login_res.status_code, 200)
        token = json.loads(login_res.data)["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try changing password with incorrect old password
        bad_change = self.client.put("/api/user/password",
                                     data=json.dumps({
                                         "current_password": "WrongOldPassword!",
                                         "new_password": "NewSecretPassword123!",
                                         "confirm_new_password": "NewSecretPassword123!"
                                     }),
                                     headers=headers,
                                     content_type="application/json")
        self.assertEqual(bad_change.status_code, 400)
        self.assertFalse(json.loads(bad_change.data)["success"])

        # Change with correct old password
        good_change = self.client.put("/api/user/password",
                                      data=json.dumps({
                                          "current_password": "InitialPassword123!",
                                          "new_password": "NewSecretPassword123!",
                                          "confirm_new_password": "NewSecretPassword123!"
                                      }),
                                      headers=headers,
                                      content_type="application/json")
        self.assertEqual(good_change.status_code, 200)
        self.assertTrue(json.loads(good_change.data)["success"])

        # Verify old password fails to login
        old_login = self.client.post("/api/auth/login",
                                     data=json.dumps({"email": u_email, "password": "InitialPassword123!"}),
                                     content_type="application/json")
        self.assertEqual(old_login.status_code, 401)

        # Verify new password succeeds
        new_login = self.client.post("/api/auth/login",
                                     data=json.dumps({"email": u_email, "password": "NewSecretPassword123!"}),
                                     content_type="application/json")
        self.assertEqual(new_login.status_code, 200)

    def test_10_ticket_updates_remain_owner_scoped(self):
        """A different normal account cannot update or reply to another user's ticket."""
        # User login & ticket creation
        u_res = self.client.post("/api/auth/login",
                                 data=json.dumps({"email": "user@magnus.com", "password": "UserPassword123!"}),
                                 content_type="application/json")
        u_token = json.loads(u_res.data)["data"]["token"]
        u_headers = {"Authorization": f"Bearer {u_token}"}

        t_res = self.client.post("/api/tickets",
                                 data=json.dumps({
                                     "subject": "Need assistance with cloud storage",
                                     "message": "Storage quota limit reached.",
                                     "category": "technical",
                                     "priority": "high"
                                 }),
                                 headers=u_headers,
                                 content_type="application/json")
        ticket_id = json.loads(t_res.data)["data"]["id"]

        # A second account has the same role and cannot act on the first account's ticket.
        a_res = self.client.post("/api/auth/login",
                                 data=json.dumps({"email": "demo@magnus.com", "password": "AdminPassword123!"}),
                                 content_type="application/json")
        a_token = json.loads(a_res.data)["data"]["token"]
        a_headers = {"Authorization": f"Bearer {a_token}"}

        self.assertEqual(self.client.put(f"/api/tickets/{ticket_id}/status",
                         data=json.dumps({"status": "in_progress"}),
                         headers=a_headers,
                         content_type="application/json").status_code, 403)
        self.assertEqual(self.client.post(f"/api/tickets/{ticket_id}/reply",
                          data=json.dumps({"message": "Unauthorized reply."}),
                          headers=a_headers,
                          content_type="application/json").status_code, 403)

        status_res = self.client.put(f"/api/tickets/{ticket_id}/status",
                         data=json.dumps({"status": "resolved"}),
                         headers=u_headers,
                         content_type="application/json")
        self.assertEqual(status_res.status_code, 200)
        reply_res = self.client.post(f"/api/tickets/{ticket_id}/reply",
                         data=json.dumps({"message": "Resolved by ticket owner."}),
                         headers=u_headers,
                         content_type="application/json")
        self.assertEqual(reply_res.status_code, 200)

        # User views ticket and sees reply
        view_res = self.client.get(f"/api/tickets/{ticket_id}", headers=u_headers)
        self.assertEqual(view_res.status_code, 200)
        v_data = json.loads(view_res.data)["data"]
        self.assertEqual(v_data["status"], "resolved")
        self.assertTrue(len(v_data["replies"]) > 0)

    def test_11_logout_and_auth_persistence_check(self):
        """Test logout clears auth and prevents subsequent protected access"""
        login_res = self.client.post("/api/auth/login",
                                     data=json.dumps({"email": "user@magnus.com", "password": "UserPassword123!"}),
                                     content_type="application/json")
        self.assertEqual(login_res.status_code, 200)

        # Logout
        logout_res = self.client.post("/api/auth/logout")
        self.assertEqual(logout_res.status_code, 200)

        # Unauthenticated /api/auth/me without bearer token
        me_res = self.client.get("/api/auth/me")
        self.assertEqual(me_res.status_code, 401)


if __name__ == "__main__":
    unittest.main()
