-- ========================================================
-- Seed Data for Magnus Dynamic CMS (magnus_cms)
-- ========================================================

USE magnus_cms;

-- Clear existing data safely
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE audit_logs;
TRUNCATE TABLE sliders;
TRUNCATE TABLE images;
TRUNCATE TABLE tooltips;
TRUNCATE TABLE popups;
TRUNCATE TABLE links;
TRUNCATE TABLE css_properties;
TRUNCATE TABLE iframes;
TRUNCATE TABLE collapsible_contents;
TRUNCATE TABLE autocomplete_items;
TRUNCATE TABLE menus;
TRUNCATE TABLE tabs;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. Users (sample accounts with hashed passwords)
-- Passwords:
-- demo@magnus.com -> AdminPassword123!
-- user@magnus.com  -> UserPassword123!
INSERT INTO users (id, name, email, password_hash, role, status) VALUES
(1, 'Sample User', 'demo@magnus.com', 'scrypt:32768:8:1$kLxLB4OtHDj9t0ya$8b9649b560245d681bd402c4334e796df99f1fa9915f5a56b3ffaafc8dcaa20f361d6af72eeaa4b8dcfa7cdfd5e0d1f2c9aa131250b7ff60ca064f35e4c5bc24', 'user', 'active'),
(2, 'Standard User', 'user@magnus.com', 'scrypt:32768:8:1$BbWkBnTNXiidmGqB$eb1fba56cb7e3cac890bf1e21eeb60c0932cd9483da32de1f91f88797ee27e249999eaf0cc5438bc18a82e60c8474941e0a4a4d783daf0d740bab11b871faebb', 'user', 'active');

-- 2. Tabs
INSERT INTO tabs (id, title, content, display_order, status) VALUES
(1, 'Overview', 'Welcome to Magnus Dynamic CMS. This enterprise content platform empowers teams to configure real-time UI components effortlessly.', 1, 'active'),
(2, 'Architecture', 'The backend is built with Python Flask RESTful APIs, MySQL database persistence, and robust RBAC security. The frontend leverages clean Vanilla JS.', 2, 'active'),
(3, 'Security', 'All inputs are sanitized, passwords use modern cryptographic scrypt hashing, SQL statements are fully parameterized, and CSS properties follow strict whitelisting.', 3, 'active'),
(4, 'Draft Release Notes', 'Upcoming features in version 2.0 include multi-tenant organizations and automated asset backups.', 4, 'inactive');

-- 3. Menus (Hierarchy with parent and nested children)
INSERT INTO menus (id, name, url, parent_id, display_order, status) VALUES
(1, 'Home', '/frontend/index.html', NULL, 1, 'active'),
(2, 'Employee', '#', NULL, 2, 'active'),
(3, 'Settings', '#', NULL, 3, 'active'),
(4, 'More', '#', NULL, 4, 'active'),
(5, 'Multiple Tabs', '/frontend/pages/multiple-tabs.html', 4, 1, 'active'),
(6, 'Menu', '/frontend/pages/menu.html', 4, 2, 'active'),
(7, 'Autocomplete', '/frontend/pages/autocomplete.html', 4, 3, 'active'),
(8, 'Collapsible Content', '/frontend/pages/collapsible.html', 4, 4, 'active'),
(9, 'Images', '/frontend/pages/images.html', 4, 5, 'active'),
(10, 'Slider', '/frontend/pages/slider.html', 4, 6, 'active'),
(11, 'Tooltips', '/frontend/pages/tooltips.html', 4, 7, 'active'),
(12, 'Popups', '/frontend/pages/popups.html', 4, 8, 'active'),
(13, 'Links', '/frontend/pages/links.html', 4, 9, 'active'),
(14, 'CSS Properties', '/frontend/pages/css-properties.html', 4, 10, 'active'),
(15, 'iFrames', '/frontend/pages/iframes.html', 4, 11, 'active');

-- 4. Autocomplete Items
INSERT INTO autocomplete_items (id, label, value, description, status) VALUES
(1, 'Python Flask', 'flask_framework', 'Lightweight WSGI web application framework for Python', 'active'),
(2, 'MySQL Database', 'mysql_db', 'World leading open-source relational database management system', 'active'),
(3, 'Vanilla JavaScript', 'vanilla_js', 'Native ECMAScript programming without external heavy frameworks', 'active'),
(4, 'RESTful API Architecture', 'rest_api', 'Stateless client-server architecture using standard HTTP verbs', 'active'),
(5, 'JSON Web Tokens', 'jwt_auth', 'Compact, URL-safe means of representing claims to be transferred between two parties', 'active'),
(6, 'CSS Glassmorphism', 'glassmorphism', 'Translucent frosted glass visual styling using backdrop filters', 'active'),
(7, 'Responsive Web Design', 'responsive_design', 'Dynamic fluid grid and media query layout optimization', 'active'),
(8, 'Legacy SOAP Services', 'soap_service', 'Deprecated XML protocol service integration', 'inactive');

-- 5. Collapsible Contents
INSERT INTO collapsible_contents (id, title, content, display_order, status) VALUES
(1, 'What is Magnus Dynamic CMS?', 'Magnus Dynamic CMS is a full-featured content management system designed to dynamically configure UI components from MySQL tables.', 1, 'active'),
(2, 'How does role-based access control work?', 'Administrators have full CRUD access across all modules, file uploads, and audit records. Regular users have read access to published active items.', 2, 'active'),
(3, 'How are file uploads secured?', 'Uploaded files are validated against allowed image MIME types and extensions (jpg, jpeg, png, webp), sanitized using secure random filenames, and capped at 5MB.', 3, 'active'),
(4, 'Internal Engineering Memo', 'Secret staging server credentials and maintenance windows.', 4, 'inactive');

-- 6. Images
INSERT INTO images (id, title, description, file_path, alt_text, category, status) VALUES
(1, 'Cloud Platform Infrastructure', 'High availability cloud server network illustration', 'sample_cloud.webp', 'Cloud Server Network', 'Technology', 'active'),
(2, 'Data Analytics Dashboard', 'Modern business analytics and metrics telemetry view', 'sample_analytics.webp', 'Analytics Charts & Metrics', 'Business', 'active'),
(3, 'Security Shield Defense', 'Cybersecurity lock and cryptography visualization', 'sample_security.webp', 'Cybersecurity Shield', 'Security', 'active'),
(4, 'Deprecated Marketing Banner', 'Archived Q1 marketing graphic', 'sample_archive.webp', 'Archived Banner', 'Archive', 'inactive');

-- 7. Sliders (Relational FK to images)
INSERT INTO sliders (id, title, description, image_id, display_order, status) VALUES
(1, 'Next-Gen Cloud Infrastructure', 'Reliable, scalable, and resilient backend systems tailored for enterprise performance.', 1, 1, 'active'),
(2, 'Real-Time Telemetry & Insights', 'Monitor system events, audit trails, and user sessions instantly with live telemetry.', 2, 2, 'active'),
(3, 'Enterprise Grade Security', 'Scrypt password hashing, parameterized queries, and strict input validation built-in.', 3, 3, 'active'),
(4, 'Winter Special Promo', 'Expired promotional slide from previous seasonal campaign.', 1, 4, 'inactive');

-- 8. Tooltips
INSERT INTO tooltips (id, element_name, content, position, status) VALUES
(1, 'btn_save_changes', 'Click to persist your form changes directly to the MySQL database.', 'top', 'active'),
(2, 'input_search_query', 'Enter at least 2 characters to trigger live backend SQL LIKE search.', 'bottom', 'active'),
(3, 'badge_role_admin', 'Administrator privilege grant: Full CRUD and audit log access.', 'right', 'active'),
(4, 'btn_delete_record', 'Destructive operation: Requires explicit modal confirmation before deletion.', 'left', 'active'),
(5, 'deprecated_badge', 'This feature will be sunset in v3.', 'top', 'inactive');

-- 9. Popups
INSERT INTO popups (id, title, content, trigger_type, status) VALUES
(1, 'Welcome to Magnus CMS', 'Explore all 11 dynamic More Menu modules. Every single module is backed by Flask REST APIs and MySQL persistence.', 'page_load', 'active'),
(2, 'Keyboard Shortcuts Guide', 'Press Esc to dismiss modals, Tab to navigate form fields, and Enter to submit active forms.', 'button_click', 'active'),
(3, 'Session Maintenance Notice', 'Scheduled system backup will occur tonight at 02:00 AM UTC.', 'manual', 'active'),
(4, 'Old Holiday Notice', 'Past holiday greetings popup.', 'page_load', 'inactive');

-- 10. Links
INSERT INTO links (id, title, url, target, description, display_order, status) VALUES
(1, 'Flask Official Documentation', 'https://flask.palletsprojects.com/', '_blank', 'Comprehensive guide to building REST APIs and microservices with Flask.', 1, 'active'),
(2, 'MySQL 8.0 Reference Manual', 'https://dev.mysql.com/doc/refman/8.0/en/', '_blank', 'Official SQL reference, indexing guides, and relational schema best practices.', 2, 'active'),
(3, 'MDN Web Docs - Vanilla JS', 'https://developer.mozilla.org/en-US/docs/Web/JavaScript', '_blank', 'Definitive browser documentation for Fetch API, DOM manipulation, and ES6+ standards.', 3, 'active'),
(4, 'Local Documentation Portal', '/frontend/dashboard.html', '_self', 'Navigate directly to your internal management portal.', 4, 'active'),
(5, 'Old Staging Site', 'https://staging.old.magnus.local', '_blank', 'Decommissioned staging server link.', 5, 'inactive');

-- 11. CSS Properties (Whitelisted CSS attributes)
INSERT INTO css_properties (id, property_name, property_value, selector, status) VALUES
(1, 'border-radius', '8px', '.dynamic-card', 'active'),
(2, 'background-color', '#f8fafc', '.dynamic-panel', 'active'),
(3, 'font-weight', '600', '.dynamic-heading', 'active'),
(4, 'color', '#0f172a', '.dynamic-text', 'active'),
(5, 'padding', '16px', '.dynamic-box', 'active'),
(6, 'opacity', '0.9', '.dynamic-badge', 'inactive');

-- 12. iFrames (Whitelisted safe embed URLs)
INSERT INTO iframes (id, title, url, width, height, allow_fullscreen, status) VALUES
(1, 'OpenStreetMap Embed', 'https://www.openstreetmap.org/export/embed.html?bbox=-0.13,51.50,-0.11,51.52&layer=mapnik', '100%', '420px', 1, 'active'),
(2, 'Wikipedia Portal Embed', 'https://en.wikipedia.org/wiki/Special:Random', '100%', '450px', 1, 'active'),
(3, 'Internal Metric View', 'https://example.com', '100%', '350px', 0, 'inactive');

-- 13. Audit Logs (Initial system records)
INSERT INTO audit_logs (id, user_id, action, module, record_id, description) VALUES
(1, 1, 'SEED', 'SYSTEM', 1, 'Initial database schema and seed data loaded successfully'),
(2, 1, 'CREATE', 'USERS', 1, 'Created system administrator account'),
(3, 1, 'CREATE', 'USERS', 2, 'Created standard demo user account'),
(4, 1, 'CREATE', 'TABS', 1, 'Published Overview tab'),
(5, 1, 'CREATE', 'MENUS', 1, 'Configured hierarchical navigation tree');

-- 14. Content Manager
INSERT INTO content_manager (id, title, description, content, category, display_order, status) VALUES
(1, 'Company Mission & Vision', 'Core organization values and strategy roadmap', 'At Magnus Technologies, we deliver world-class digital management platforms designed with high reliability, security, and developer productivity in mind.', 'Corporate', 1, 'active'),
(2, 'Platform Privacy Policy', 'Compliance statement regarding user privacy and GDPR', 'We adhere to rigorous data privacy principles. User information is protected with state-of-the-art encryption standards.', 'Legal', 2, 'active'),
(3, 'Technical Support Guidelines', 'Tier-1 to Tier-3 escalation matrix and SLAs', 'Standard response SLAs are 24/7 for critical incidents and 1 business day for general feature requests.', 'Support', 3, 'active'),
(4, 'Draft Marketing Roadmap 2027', 'Internal marketing deliverables and trade shows', 'Confidential preliminary release schedule for upcoming product tiers.', 'Marketing', 4, 'inactive');

-- 15. Media Manager
INSERT INTO media_manager (id, file_name, file_type, file_path, description, category, status) VALUES
(1, 'system_architecture_diagram.png', 'image/png', 'sample_cloud.webp', 'Enterprise microservices and API topology diagram', 'Architecture', 'active'),
(2, 'product_catalog_2026.png', 'image/png', 'sample_analytics.webp', 'Annual corporate asset brochure and capabilities deck', 'Marketing', 'active'),
(3, 'compliance_certificate.png', 'image/png', 'sample_security.webp', 'ISO 27001 cybersecurity compliance certificate', 'Compliance', 'active'),
(4, 'archived_draft_logo.png', 'image/png', 'sample_archive.webp', 'Legacy brand asset watermark', 'Archive', 'inactive');

-- 16. Forms
INSERT INTO forms (id, title, description, status) VALUES
(1, 'Contact Us & Inquiry Form', 'Standard customer and developer contact form', 'active'),
(2, 'Customer Feedback Survey', 'Post-onboarding client satisfaction survey', 'active'),
(3, 'Employee Request Portal', 'Internal equipment and leave request form', 'active'),
(4, 'Deprecated Partner Onboarding', 'Old partner application form', 'inactive');

-- 17. Form Fields
INSERT INTO form_fields (id, form_id, field_label, field_name, field_type, options, is_required, display_order) VALUES
(1, 1, 'Full Name', 'full_name', 'text', '', 1, 1),
(2, 1, 'Email Address', 'email', 'email', '', 1, 2),
(3, 1, 'Phone Number', 'phone', 'phone', '', 0, 3),
(4, 1, 'Department', 'department', 'dropdown', 'Sales,Technical Support,Billing,General Inquiry', 1, 4),
(5, 1, 'Message', 'message', 'textarea', '', 1, 5),
(6, 2, 'Client Name', 'client_name', 'text', '', 1, 1),
(7, 2, 'Overall Rating', 'rating', 'radio', 'Excellent,Good,Average,Poor', 1, 2),
(8, 2, 'Feedback Details', 'comments', 'textarea', '', 1, 3),
(9, 2, 'Subscribe to Updates', 'subscribe', 'checkbox', 'Yes', 0, 4);

-- 18. Form Submissions
INSERT INTO form_submissions (id, form_id, submitted_data, ip_address) VALUES
(1, 1, '{"full_name": "John Doe", "email": "john.doe@enterprise.com", "phone": "+1-555-0199", "department": "Technical Support", "message": "Inquiring about REST API throughput and webhooks capability."}', '192.168.1.100'),
(2, 1, '{"full_name": "Jane Smith", "email": "j.smith@cloudtech.io", "phone": "+1-555-0288", "department": "Sales", "message": "Requesting enterprise licensing quote."}', '192.168.1.101'),
(3, 2, '{"client_name": "Acme Corp", "rating": "Excellent", "comments": "The Magnus dynamic CMS modules have streamlined our operations significantly.", "subscribe": "Yes"}', '192.168.1.102');

-- 19. Notifications
INSERT INTO notifications (id, title, message, type, status) VALUES
(1, 'System Security Patch Applied', 'Core database connections and auth middleware updated to the latest security guidelines.', 'success', 'active'),
(2, 'Scheduled Database Maintenance', 'Nightly snapshot backup scheduled for Sunday at 02:00 UTC.', 'info', 'active'),
(3, 'Storage Utilization Notice', 'Uploaded media folder reached 65% capacity.', 'warning', 'active'),
(4, 'Urgent TLS Certificate Expiry', 'Legacy SSL certificates decommissioned.', 'alert', 'active'),
(5, 'Archived Holiday Message', 'Season greetings notice from last year.', 'info', 'inactive');

-- 20. Activity Logs
INSERT INTO activity_logs (id, user_id, action, module, record_id, description) VALUES
(1, 1, 'SEED', 'SYSTEM', 1, 'System initialized with core and extended More modules'),
(2, 1, 'CREATE', 'USERS', 1, 'Created system administrator account'),
(3, 1, 'CREATE', 'CONTENT', 1, 'Published Company Mission & Vision'),
(4, 1, 'CREATE', 'FORMS', 1, 'Created Contact Us & Inquiry Form'),
(5, 1, 'SUBMIT', 'FORMS', 1, 'Received new form submission from John Doe');

