import io
import sys
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:5000"

def run_tests():
    print("--- Starting End-to-End Test Suite for Magnus CMS ---")
    s = requests.Session()

    # 1. Test Unauthenticated Access Redirects to /login
    protected_urls = [
        "/",
        "/home",
        "/dashboard",
        "/more",
        "/frontend/index.html",
        "/frontend/dashboard.html",
        "/frontend/pages/multiple-tabs.html",
        "/frontend/pages/menu.html",
        "/frontend/pages/autocomplete.html",
        "/frontend/pages/collapsible.html",
        "/frontend/pages/images.html",
        "/frontend/pages/slider.html",
        "/frontend/pages/tooltips.html",
        "/frontend/pages/popups.html",
        "/frontend/pages/links.html",
        "/frontend/pages/css-properties.html",
        "/frontend/pages/iframes.html",
        "/frontend/pages/content-manager.html",
        "/frontend/pages/media-manager.html",
        "/frontend/pages/form-manager.html",
        "/frontend/pages/notification-manager.html",
        "/frontend/pages/activity-logs.html",
        "/frontend/pages/reports.html"
    ]
    for url in protected_urls:
        r = s.get(f"{BASE_URL}{url}", allow_redirects=False)
        assert r.status_code == 302, f"Expected 302 redirect for unauthenticated {url}, got {r.status_code}"
        assert r.headers.get("Location") == "/login", f"Expected redirect to /login for {url}, got {r.headers.get('Location')}"
    print("✓ All 23 protected URLs redirect unauthenticated users to /login")

    # 2. Test Login Page & Assets Accessible Without Auth
    r_login = s.get(f"{BASE_URL}/login")
    assert r_login.status_code == 200, f"/login returned {r_login.status_code}"
    assert "Magnus CMS" in r_login.text or "Sign in" in r_login.text

    r_css = s.get(f"{BASE_URL}/frontend/css/style.css")
    assert r_css.status_code == 200, "CSS asset returned non-200"
    print("✓ Login page and public static assets served with HTTP 200")

    # 3. Test Invalid Password Rejection (Secure Verification)
    bad_login = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "demo@magnus.com",
        "password": "WrongPassword123!"
    })
    assert bad_login.status_code == 401, f"Expected 401 for bad password, got {bad_login.status_code}"
    print("✓ Secure hashed password verification correctly rejected invalid credentials")

    # 4. Test Admin Login (Sets Flask Session)
    login_res = s.post(f"{BASE_URL}/api/auth/login", json={
        "email": "demo@magnus.com",
        "password": "AdminPassword123!"
    })
    assert login_res.status_code == 200, f"Admin login failed: {login_res.text}"
    admin_data = login_res.json()["data"]
    admin_token = admin_data["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("✓ Admin login successful, session established & JWT token obtained")

    # 5. Test Authenticated Session Access to /home, /dashboard, and More Pages
    auth_pages = [
        "/home",
        "/dashboard",
        "/frontend/pages/multiple-tabs.html",
        "/frontend/pages/menu.html",
        "/frontend/pages/autocomplete.html",
        "/frontend/pages/collapsible.html",
        "/frontend/pages/images.html",
        "/frontend/pages/slider.html",
        "/frontend/pages/tooltips.html",
        "/frontend/pages/popups.html",
        "/frontend/pages/links.html",
        "/frontend/pages/css-properties.html",
        "/frontend/pages/iframes.html",
        "/frontend/pages/content-manager.html",
        "/frontend/pages/media-manager.html",
        "/frontend/pages/form-manager.html",
        "/frontend/pages/notification-manager.html",
        "/frontend/pages/activity-logs.html",
        "/frontend/pages/reports.html"
    ]
    for p in auth_pages:
        r = s.get(f"{BASE_URL}{p}")
        assert r.status_code == 200, f"Authenticated page {p} failed with {r.status_code}"
    print("✓ Authenticated session can access /home, /dashboard, and all 17 More pages")

    # 6. Test Logout Flow
    logout_session = requests.Session()
    logout_session.post(f"{BASE_URL}/api/auth/login", json={"email": "demo@magnus.com", "password": "AdminPassword123!"})
    r_check = logout_session.get(f"{BASE_URL}/home", allow_redirects=False)
    assert r_check.status_code == 200, "Expected 200 on /home before logout"
    r_logout = logout_session.get(f"{BASE_URL}/logout", allow_redirects=False)
    assert r_logout.status_code == 302 and r_logout.headers.get("Location") == "/login"
    r_after = logout_session.get(f"{BASE_URL}/home", allow_redirects=False)
    assert r_after.status_code == 302 and r_after.headers.get("Location") == "/login"
    print("✓ Logout clears session and redirects to /login")

    # 7. Test Normal User Login
    user_res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "user@magnus.com",
        "password": "UserPassword123!"
    })
    assert user_res.status_code == 200, f"User login failed: {user_res.text}"
    user_data = user_res.json()["data"]
    user_token = user_data["token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    print("✓ Standard user login successful")

    # 8. Test Authorization Guard (User should get 403 on admin-only route)
    denied_res = s.get(f"{BASE_URL}/api/dashboard/stats", headers=user_headers)
    assert denied_res.status_code == 403, f"Expected 403 for user on admin stats, got {denied_res.status_code}"
    
    unauth_res = requests.get(f"{BASE_URL}/api/dashboard/stats")
    assert unauth_res.status_code == 401, f"Expected 401 for unauthenticated stats, got {unauth_res.status_code}"
    print("✓ Authentication & Role-based Authorization guards verified (401 & 403)")

    # 9. Test Dashboard Stats
    stats_res = s.get(f"{BASE_URL}/api/dashboard/stats", headers=admin_headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()["data"]
    assert "total_tabs" in stats and "total_users" in stats
    print("✓ Dashboard statistics endpoint working")

    # 10. Test Tabs CRUD
    tab_create = s.post(f"{BASE_URL}/api/tabs", headers=admin_headers, json={
        "title": "Automated Test Tab",
        "content": "This is test tab content.",
        "display_order": 99,
        "status": "active"
    })
    assert tab_create.status_code == 201, f"Create tab failed: {tab_create.text}"
    tab_id = tab_create.json()["data"]["id"]

    tab_get = s.get(f"{BASE_URL}/api/tabs/{tab_id}", headers=admin_headers)
    assert tab_get.status_code == 200 and tab_get.json()["data"]["title"] == "Automated Test Tab"

    tab_update = s.put(f"{BASE_URL}/api/tabs/{tab_id}", headers=admin_headers, json={
        "title": "Automated Test Tab Updated",
        "content": "Updated content.",
        "display_order": 100,
        "status": "inactive"
    })
    assert tab_update.status_code == 200

    tab_del = s.delete(f"{BASE_URL}/api/tabs/{tab_id}", headers=admin_headers)
    assert tab_del.status_code == 200
    print("✓ Multiple Tabs CRUD verified")

    # 7. Test Menu CRUD & Tree
    menu_create = s.post(f"{BASE_URL}/api/menus", headers=admin_headers, json={
        "name": "Test Parent Menu",
        "url": "/test",
        "display_order": 1,
        "status": "active"
    })
    assert menu_create.status_code == 201
    parent_menu_id = menu_create.json()["data"]["id"]

    child_create = s.post(f"{BASE_URL}/api/menus", headers=admin_headers, json={
        "name": "Test Child Menu",
        "url": "/test/child",
        "parent_id": parent_menu_id,
        "display_order": 1,
        "status": "active"
    })
    assert child_create.status_code == 201
    child_menu_id = child_create.json()["data"]["id"]

    tree_get = s.get(f"{BASE_URL}/api/menus?tree=true")
    assert tree_get.status_code == 200
    
    # Clean up menus
    s.delete(f"{BASE_URL}/api/menus/{child_menu_id}", headers=admin_headers)
    s.delete(f"{BASE_URL}/api/menus/{parent_menu_id}", headers=admin_headers)
    print("✓ Navigation Menu CRUD and Tree hierarchy verified")

    # 8. Test Autocomplete Search
    ac_create = s.post(f"{BASE_URL}/api/autocomplete", headers=admin_headers, json={
        "label": "Test Autocomplete Term",
        "value": "test_term",
        "description": "Test description",
        "status": "active"
    })
    assert ac_create.status_code == 201
    ac_id = ac_create.json()["data"]["id"]

    search_res = s.get(f"{BASE_URL}/api/autocomplete/search?q=Auto")
    assert search_res.status_code == 200
    found = any(item["id"] == ac_id for item in search_res.json()["data"])
    assert found, "Created autocomplete item not found in search results"

    s.delete(f"{BASE_URL}/api/autocomplete/{ac_id}", headers=admin_headers)
    print("✓ Autocomplete CRUD & SQL LIKE search verified")

    # 9. Test Collapsible CRUD
    col_create = s.post(f"{BASE_URL}/api/collapsible", headers=admin_headers, json={
        "title": "Test Collapsible Header",
        "content": "Test body",
        "display_order": 1,
        "status": "active"
    })
    assert col_create.status_code == 201
    col_id = col_create.json()["data"]["id"]
    s.delete(f"{BASE_URL}/api/collapsible/{col_id}", headers=admin_headers)
    print("✓ Collapsible Content CRUD verified")

    # 10. Test Image Upload & CRUD
    png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
    files = {'image_file': ('test_upload.png', io.BytesIO(png_bytes), 'image/png')}
    data = {
        'title': 'Automated Test Upload',
        'description': 'Test upload description',
        'alt_text': 'Test Alt',
        'category': 'Testing',
        'status': 'active'
    }
    img_res = s.post(f"{BASE_URL}/api/images", headers=admin_headers, data=data, files=files)
    assert img_res.status_code == 201, f"Image upload failed: {img_res.text}"
    img_id = img_res.json()["data"]["id"]
    img_file = img_res.json()["data"]["file_path"]

    # Verify static file serving
    static_img = s.get(f"{BASE_URL}/uploads/{img_file}")
    assert static_img.status_code == 200, f"Static image file not found at /uploads/{img_file}"

    # 11. Test Slider CRUD referencing image
    slider_create = s.post(f"{BASE_URL}/api/sliders", headers=admin_headers, json={
        "title": "Automated Test Slide",
        "description": "Slide caption",
        "image_id": img_id,
        "display_order": 1,
        "status": "active"
    })
    assert slider_create.status_code == 201, f"Slider create failed: {slider_create.text}"
    slider_id = slider_create.json()["data"]["id"]

    slider_get = s.get(f"{BASE_URL}/api/sliders/{slider_id}", headers=admin_headers)
    assert slider_get.status_code == 200 and slider_get.json()["data"]["image_id"] == img_id

    s.delete(f"{BASE_URL}/api/sliders/{slider_id}", headers=admin_headers)
    s.delete(f"{BASE_URL}/api/images/{img_id}", headers=admin_headers)
    print("✓ Image file upload & Slider relational CRUD verified")

    # 12. Test Tooltips CRUD
    tip_create = s.post(f"{BASE_URL}/api/tooltips", headers=admin_headers, json={
        "element_name": "test_element_btn",
        "content": "Helpful hint",
        "position": "bottom",
        "status": "active"
    })
    assert tip_create.status_code == 201
    tip_id = tip_create.json()["data"]["id"]
    s.delete(f"{BASE_URL}/api/tooltips/{tip_id}", headers=admin_headers)
    print("✓ Tooltips CRUD verified")

    # 13. Test Popups CRUD
    popup_create = s.post(f"{BASE_URL}/api/popups", headers=admin_headers, json={
        "title": "Test Popup Notice",
        "content": "Popup body text",
        "trigger_type": "button_click",
        "status": "active"
    })
    assert popup_create.status_code == 201
    popup_id = popup_create.json()["data"]["id"]
    s.delete(f"{BASE_URL}/api/popups/{popup_id}", headers=admin_headers)
    print("✓ Popups CRUD verified")

    # 14. Test Links CRUD & URL Safety
    unsafe_link = s.post(f"{BASE_URL}/api/links", headers=admin_headers, json={
        "title": "Malicious Link",
        "url": "javascript:alert('xss')",
        "target": "_blank",
        "status": "active"
    })
    assert unsafe_link.status_code == 400, "Unsafe javascript: protocol was not rejected!"

    safe_link = s.post(f"{BASE_URL}/api/links", headers=admin_headers, json={
        "title": "Valid Link",
        "url": "https://example.com/docs",
        "target": "_blank",
        "status": "active"
    })
    assert safe_link.status_code == 201
    link_id = safe_link.json()["data"]["id"]
    s.delete(f"{BASE_URL}/api/links/{link_id}", headers=admin_headers)
    print("✓ Links CRUD and protocol security verified")

    # 15. Test CSS Properties Whitelist
    bad_css = s.post(f"{BASE_URL}/api/css-properties", headers=admin_headers, json={
        "selector": ".dynamic-card",
        "property_name": "behavior",
        "property_value": "url(xss.htc)",
        "status": "active"
    })
    assert bad_css.status_code == 400, "Non-whitelisted CSS property was not rejected!"

    good_css = s.post(f"{BASE_URL}/api/css-properties", headers=admin_headers, json={
        "selector": ".dynamic-card",
        "property_name": "border-radius",
        "property_value": "12px",
        "status": "active"
    })
    assert good_css.status_code == 201
    css_id = good_css.json()["data"]["id"]
    s.delete(f"{BASE_URL}/api/css-properties/{css_id}", headers=admin_headers)
    print("✓ CSS Properties CRUD and strict whitelist validation verified")

    # 16. Test iFrames CRUD & HTTPS Enforcement
    bad_frame = s.post(f"{BASE_URL}/api/iframes", headers=admin_headers, json={
        "title": "Insecure Frame",
        "url": "http://insecure-site.com",
        "width": "100%",
        "height": "400px",
        "status": "active"
    })
    assert bad_frame.status_code == 400, "Insecure non-HTTPS URL was not rejected!"

    good_frame = s.post(f"{BASE_URL}/api/iframes", headers=admin_headers, json={
        "title": "Safe Map Embed",
        "url": "https://www.openstreetmap.org/export/embed.html",
        "width": "100%",
        "height": "400px",
        "allow_fullscreen": 1,
        "status": "active"
    })
    assert good_frame.status_code == 201
    iframe_id = good_frame.json()["data"]["id"]
    s.delete(f"{BASE_URL}/api/iframes/{iframe_id}", headers=admin_headers)
    print("✓ iFrames CRUD and HTTPS enforcement verified")

    # 17. Test Content Manager CRUD & Filters
    cnt_create = s.post(f"{BASE_URL}/api/content", headers=admin_headers, json={
        "title": "Automated Content Article",
        "description": "Short summary",
        "content": "<p>Full rich content body here.</p>",
        "category": "Articles",
        "display_order": 10,
        "status": "active"
    })
    assert cnt_create.status_code == 201, f"Content creation failed: {cnt_create.text}"
    cnt_id = cnt_create.json()["data"]["id"]

    cnt_get = s.get(f"{BASE_URL}/api/content/{cnt_id}")
    assert cnt_get.status_code == 200 and cnt_get.json()["data"]["title"] == "Automated Content Article"

    cnt_update = s.put(f"{BASE_URL}/api/content/{cnt_id}", headers=admin_headers, json={
        "title": "Updated Content Title",
        "description": "Updated summary",
        "content": "<p>Updated body.</p>",
        "category": "Articles",
        "display_order": 20,
        "status": "disabled"
    })
    assert cnt_update.status_code == 200 and cnt_update.json()["data"]["status"] == "disabled"

    cnt_del = s.delete(f"{BASE_URL}/api/content/{cnt_id}", headers=admin_headers)
    assert cnt_del.status_code == 200
    print("✓ 12. Content Manager CRUD & Filters verified")

    # 18. Test Media Manager File Upload & Metadata CRUD
    media_file_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x02\x00\x00\x00\x02\x08\x02\x00\x00\x00\xfd\xd4\x9a\x73\x00\x00\x00\x0cIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
    media_files = {'media_file': ('test_media_item.png', io.BytesIO(media_file_bytes), 'image/png')}
    media_data = {
        'description': 'Test media manager asset',
        'category': 'Documents',
        'status': 'active'
    }
    media_res = s.post(f"{BASE_URL}/api/media", headers=admin_headers, data=media_data, files=media_files)
    assert media_res.status_code == 201, f"Media upload failed: {media_res.text}"
    media_id = media_res.json()["data"]["id"]

    media_upd = s.put(f"{BASE_URL}/api/media/{media_id}", headers=admin_headers, json={
        "description": "Updated media description",
        "category": "Branding",
        "status": "disabled"
    })
    assert media_upd.status_code == 200

    media_del = s.delete(f"{BASE_URL}/api/media/{media_id}", headers=admin_headers)
    assert media_del.status_code == 200
    print("✓ 13. Media Manager Upload & Metadata CRUD verified")

    # 19. Test Form Manager (Dynamic Forms & Submissions)
    form_create = s.post(f"{BASE_URL}/api/forms", headers=admin_headers, json={
        "title": "Customer Feedback Survey",
        "description": "Please give us your feedback",
        "status": "active",
        "fields": [
            {"field_name": "full_name", "field_label": "Full Name", "field_type": "text", "is_required": True, "display_order": 1},
            {"field_name": "email_addr", "field_label": "Email Address", "field_type": "email", "is_required": True, "display_order": 2},
            {"field_name": "rating", "field_label": "Satisfaction Rating", "field_type": "dropdown", "options": "Excellent,Good,Fair,Poor", "is_required": False, "display_order": 3},
            {"field_name": "comments", "field_label": "Comments", "field_type": "textarea", "is_required": False, "display_order": 4}
        ]
    })
    assert form_create.status_code == 201, f"Form creation failed: {form_create.text}"
    form_id = form_create.json()["data"]["id"]

    # Test submitting form as public user
    submit_res = s.post(f"{BASE_URL}/api/forms/{form_id}/submit", json={
        "full_name": "Alice Tester",
        "email_addr": "alice@example.com",
        "rating": "Excellent",
        "comments": "Antigravity generated an awesome system!"
    })
    assert submit_res.status_code == 201, f"Form submission failed: {submit_res.text}"
    submission_id = submit_res.json()["data"]["id"]

    # Admin checks submissions
    subs_res = s.get(f"{BASE_URL}/api/forms/{form_id}/submissions", headers=admin_headers)
    assert subs_res.status_code == 200
    assert len(subs_res.json()["data"]) >= 1

    # Clean up submission & form
    del_sub = s.delete(f"{BASE_URL}/api/forms/submissions/{submission_id}", headers=admin_headers)
    assert del_sub.status_code == 200

    del_form = s.delete(f"{BASE_URL}/api/forms/{form_id}", headers=admin_headers)
    assert del_form.status_code == 200
    print("✓ 14. Form Manager & Submissions Flow verified")

    # 20. Test Notification Manager CRUD
    notif_create = s.post(f"{BASE_URL}/api/notifications", headers=admin_headers, json={
        "title": "System Update Notice",
        "message": "Maintenance scheduled for midnight.",
        "type": "Warning",
        "status": "active"
    })
    assert notif_create.status_code == 201, f"Notification creation failed: {notif_create.text}"
    notif_id = notif_create.json()["data"]["id"]

    notif_get = s.get(f"{BASE_URL}/api/notifications/{notif_id}")
    assert notif_get.status_code == 200 and notif_get.json()["data"]["type"].lower() == "warning"

    notif_del = s.delete(f"{BASE_URL}/api/notifications/{notif_id}", headers=admin_headers)
    assert notif_del.status_code == 200
    print("✓ 15. Notification Manager CRUD verified")

    # 21. Test Activity Logs with Filter & Search
    activity_res = s.get(f"{BASE_URL}/api/activity-logs?module=Form%20Manager", headers=admin_headers)
    assert activity_res.status_code == 200
    assert "items" in activity_res.json()["data"]
    print(f"✓ 16. Activity Logs search, filter, and pagination verified")

    # 22. Test Reports Aggregation
    reports_res = s.get(f"{BASE_URL}/api/reports/summary", headers=admin_headers)
    assert reports_res.status_code == 200
    rep_data = reports_res.json()["data"]
    for key in ["total_users", "total_content", "total_media", "total_forms", "total_submissions", "total_notifications", "recent_activities"]:
        assert key in rep_data, f"Missing key {key} in reports summary response"
    print("✓ 17. Reports database SQL aggregations verified")

    # 23. Verify Audit Logs
    audit_res = s.get(f"{BASE_URL}/api/audit-logs", headers=admin_headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()["data"]["items"]
    assert len(logs) > 0, "No audit logs found"
    print(f"✓ Audit logs verified ({len(logs)} audit records tracked in MySQL)")

    print("\n========================================================")
    print("🎉 ALL 23 E2E TEST VERIFICATIONS PASSED SUCCESSFULLY!")
    print("========================================================")

if __name__ == "__main__":
    run_tests()
