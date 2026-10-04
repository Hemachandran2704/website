import os
import sys
import sqlite3
import datetime
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "magnus_cms")
SQLITE_DB_PATH = os.path.join(BASE_DIR, "database", "magnus_cms.db")
MORE_RECORD_TABLES = (
    "tabs", "menus", "autocomplete_items", "collapsible_contents", "images",
    "sliders", "tooltips", "popups", "links", "css_properties", "iframes"
)
SQLITE_OWNERSHIP_MIGRATED = False

# Try to determine if MySQL driver is available
HAS_MYSQL_CONNECTOR = False
HAS_PYMYSQL = False
db_pool = None


def _migrate_mysql_more_ownership(conn):
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users' AND COLUMN_NAME = 'role'",
            (DB_NAME,),
        )
        if cursor.fetchone()[0]:
            cursor.execute("UPDATE users SET role = 'user' WHERE role <> 'user'")
            cursor.execute("ALTER TABLE users MODIFY COLUMN role ENUM('user') NOT NULL DEFAULT 'user'")
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'demo@magnus.com'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "UPDATE users SET name = 'Sample User', email = 'demo@magnus.com' "
                "WHERE email = 'admin@magnus.com'"
            )

        cursor.execute(
            "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'announcements' AND COLUMN_NAME = 'target_role'",
            (DB_NAME,),
        )
        if cursor.fetchone()[0]:
            cursor.execute("UPDATE announcements SET target_role = 'user' WHERE target_role = 'admin'")
            cursor.execute("ALTER TABLE announcements MODIFY COLUMN target_role ENUM('all', 'user') DEFAULT 'all'")

        for table in MORE_RECORD_TABLES:
            cursor.execute(
                "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s",
                (DB_NAME, table),
            )
            if cursor.fetchone()[0] == 0:
                continue

            cursor.execute(
                "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = 'user_id'",
                (DB_NAME, table),
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    f"ALTER TABLE `{table}` "
                    f"ADD COLUMN user_id INT NULL, "
                    f"ADD INDEX idx_{table}_user_id (user_id), "
                    f"ADD CONSTRAINT fk_{table}_user FOREIGN KEY (user_id) "
                    "REFERENCES users(id) ON DELETE CASCADE"
                )
        conn.commit()
    finally:
        cursor.close()

try:
    import mysql.connector
    from mysql.connector import pooling
    HAS_MYSQL_CONNECTOR = True
except ImportError:
    try:
        import pymysql
        import pymysql.cursors
        HAS_PYMYSQL = True
    except ImportError:
        pass

# Check MySQL availability
USE_SQLITE = False

def _test_mysql():
    global db_pool, USE_SQLITE
    if HAS_MYSQL_CONNECTOR:
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                connect_timeout=2
            )
            _migrate_mysql_more_ownership(conn)
            conn.close()
            try:
                db_pool = pooling.MySQLConnectionPool(
                    pool_name="magnus_pool",
                    pool_size=10,
                    pool_reset_session=True,
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME,
                    autocommit=False
                )
            except Exception:
                db_pool = None
            return True
        except Exception as e:
            print(f"[Database] MySQL connection unavailable ({e}). Using embedded SQLite database.")
            USE_SQLITE = True
            return False
    elif HAS_PYMYSQL:
        try:
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                connect_timeout=2
            )
            _migrate_mysql_more_ownership(conn)
            conn.close()
            return True
        except Exception as e:
            print(f"[Database] MySQL connection unavailable ({e}). Using embedded SQLite database.")
            USE_SQLITE = True
            return False
    else:
        USE_SQLITE = True
        return False

_test_mysql()


def _init_sqlite_db():
    """Initializes SQLite tables and seed data if database is empty."""
    global SQLITE_OWNERSHIP_MIGRATED
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='content_manager';")
    if not cursor.fetchone():
        print("[Database] Initializing SQLite schema and seed data...")
        schema_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tabs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            display_order INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS menus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            parent_id INTEGER NULL DEFAULT NULL,
            display_order INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES menus(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS autocomplete_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            value TEXT NOT NULL,
            description TEXT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS collapsible_contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            display_order INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NULL,
            file_path TEXT NOT NULL,
            alt_text TEXT NULL,
            category TEXT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sliders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NULL,
            image_id INTEGER NOT NULL,
            display_order INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS tooltips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            element_name TEXT NOT NULL,
            content TEXT NOT NULL,
            position TEXT NOT NULL DEFAULT 'top',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS popups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            trigger_type TEXT NOT NULL DEFAULT 'button_click',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            target TEXT NOT NULL DEFAULT '_self',
            description TEXT NULL,
            display_order INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS css_properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_name TEXT NOT NULL,
            property_value TEXT NOT NULL,
            selector TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS iframes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            width TEXT NOT NULL DEFAULT '100%',
            height TEXT NOT NULL DEFAULT '400px',
            allow_fullscreen INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NULL,
            action TEXT NOT NULL,
            module TEXT NOT NULL,
            record_id INTEGER NULL,
            description TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS content_manager (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NULL,
            content TEXT NOT NULL,
            category TEXT NULL,
            display_order INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS media_manager (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            description TEXT NULL,
            category TEXT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS forms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS form_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            form_id INTEGER NOT NULL,
            field_label TEXT NOT NULL,
            field_name TEXT NOT NULL,
            field_type TEXT NOT NULL DEFAULT 'text',
            options TEXT NULL,
            is_required INTEGER NOT NULL DEFAULT 0,
            display_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS form_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            form_id INTEGER NOT NULL,
            submitted_data TEXT NOT NULL,
            ip_address TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'info',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NULL,
            action TEXT NOT NULL,
            module TEXT NOT NULL,
            record_id INTEGER NULL,
            description TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ticket_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES support_tickets(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size TEXT DEFAULT '0 KB',
            category TEXT DEFAULT 'General',
            status TEXT DEFAULT 'pending',
            review_notes TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            email_notifications INTEGER DEFAULT 1,
            security_alerts INTEGER DEFAULT 1,
            activity_digest INTEGER DEFAULT 1,
            language TEXT DEFAULT 'en',
            appearance TEXT DEFAULT 'light',
            phone TEXT NULL,
            department TEXT DEFAULT 'General',
            bio TEXT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT NOT NULL UNIQUE,
            setting_value TEXT NOT NULL,
            description TEXT NULL,
            category TEXT DEFAULT 'system',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            priority TEXT DEFAULT 'normal',
            target_role TEXT DEFAULT 'all',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NULL,
            event_date TEXT NOT NULL,
            event_time TEXT DEFAULT '09:00',
            status TEXT DEFAULT 'upcoming',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS user_favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            category TEXT DEFAULT 'Module',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        cursor.executescript(schema_sql)

        # Migration check: Ensure user_id exists in notifications
        cur_cols = [c[1] for c in cursor.execute("PRAGMA table_info(notifications)").fetchall()]
        if "user_id" not in cur_cols:
            try:
                cursor.execute("ALTER TABLE notifications ADD COLUMN user_id INTEGER NULL")
            except Exception as e:
                print(f"Migration error for notifications.user_id: {e}")

        # Insert Seed data
        seed_users = [
            (1, 'Sample User', 'demo@magnus.com', 'scrypt:32768:8:1$kLxLB4OtHDj9t0ya$8b9649b560245d681bd402c4334e796df99f1fa9915f5a56b3ffaafc8dcaa20f361d6af72eeaa4b8dcfa7cdfd5e0d1f2c9aa131250b7ff60ca064f35e4c5bc24', 'user', 'active'),
            (2, 'Standard User', 'user@magnus.com', 'scrypt:32768:8:1$BbWkBnTNXiidmGqB$eb1fba56cb7e3cac890bf1e21eeb60c0932cd9483da32de1f91f88797ee27e249999eaf0cc5438bc18a82e60c8474941e0a4a4d783daf0d740bab11b871faebb', 'user', 'active')
        ]
        cursor.executemany("INSERT OR IGNORE INTO users (id, name, email, password_hash, role, status) VALUES (?, ?, ?, ?, ?, ?)", seed_users)

        seed_tabs = [
            (1, 'Overview', 'Welcome to Magnus Dynamic CMS. This enterprise content platform empowers teams to configure real-time UI components effortlessly.', 1, 'active'),
            (2, 'Architecture', 'The backend is built with Python Flask RESTful APIs, MySQL/SQLite database persistence, and robust RBAC security. The frontend leverages clean Vanilla JS.', 2, 'active'),
            (3, 'Security', 'All inputs are sanitized, passwords use modern cryptographic scrypt hashing, SQL statements are fully parameterized, and CSS properties follow strict whitelisting.', 3, 'active'),
            (4, 'Draft Release Notes', 'Upcoming features in version 2.0 include multi-tenant organizations and automated asset backups.', 4, 'inactive')
        ]
        cursor.executemany("INSERT OR IGNORE INTO tabs (id, title, content, display_order, status) VALUES (?, ?, ?, ?, ?)", seed_tabs)

        seed_menus = [
            (1, 'Home', '/frontend/index.html', None, 1, 'active'),
            (2, 'Employee', '#', None, 2, 'active'),
            (3, 'Settings', '#', None, 3, 'active'),
            (4, 'More', '#', None, 4, 'active'),
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
            (15, 'iFrames', '/frontend/pages/iframes.html', 4, 11, 'active'),
            (16, 'Content Manager', '/frontend/pages/content-manager.html', 4, 12, 'active'),
            (17, 'Media Manager', '/frontend/pages/media-manager.html', 4, 13, 'active'),
            (18, 'Form Manager', '/frontend/pages/form-manager.html', 4, 14, 'active'),
            (19, 'Notification Manager', '/frontend/pages/notification-manager.html', 4, 15, 'active'),
            (20, 'Activity Logs', '/frontend/pages/activity-logs.html', 4, 16, 'active'),
            (21, 'Reports', '/frontend/pages/reports.html', 4, 17, 'active')
        ]
        cursor.executemany("INSERT OR IGNORE INTO menus (id, name, url, parent_id, display_order, status) VALUES (?, ?, ?, ?, ?, ?)", seed_menus)

        seed_autocomplete = [
            (1, 'Python Flask', 'flask_framework', 'Lightweight WSGI web application framework for Python', 'active'),
            (2, 'MySQL Database', 'mysql_db', 'World leading open-source relational database management system', 'active'),
            (3, 'Vanilla JavaScript', 'vanilla_js', 'Native ECMAScript programming without external heavy frameworks', 'active'),
            (4, 'RESTful API Architecture', 'rest_api', 'Stateless client-server architecture using standard HTTP verbs', 'active'),
            (5, 'JSON Web Tokens', 'jwt_auth', 'Compact, URL-safe means of representing claims to be transferred between two parties', 'active'),
            (6, 'CSS Glassmorphism', 'glassmorphism', 'Translucent frosted glass visual styling using backdrop filters', 'active'),
            (7, 'Responsive Web Design', 'responsive_design', 'Dynamic fluid grid and media query layout optimization', 'active'),
            (8, 'Legacy SOAP Services', 'soap_service', 'Deprecated XML protocol service integration', 'inactive')
        ]
        cursor.executemany("INSERT OR IGNORE INTO autocomplete_items (id, label, value, description, status) VALUES (?, ?, ?, ?, ?)", seed_autocomplete)

        seed_collapsible = [
            (1, 'What is Magnus Dynamic CMS?', 'Magnus Dynamic CMS is a full-featured content management system designed to dynamically configure UI components from tables.', 1, 'active'),
            (2, 'How does role-based access control work?', 'Administrators have full CRUD access across all modules, file uploads, and audit records. Regular users have read access to published active items.', 2, 'active'),
            (3, 'How are file uploads secured?', 'Uploaded files are validated against allowed image MIME types and extensions (jpg, jpeg, png, webp), sanitized using secure random filenames, and capped at 5MB.', 3, 'active'),
            (4, 'Internal Engineering Memo', 'Secret staging server credentials and maintenance windows.', 4, 'inactive')
        ]
        cursor.executemany("INSERT OR IGNORE INTO collapsible_contents (id, title, content, display_order, status) VALUES (?, ?, ?, ?, ?)", seed_collapsible)

        seed_images = [
            (1, 'Cloud Platform Infrastructure', 'High availability cloud server network illustration', 'sample_cloud.webp', 'Cloud Server Network', 'Technology', 'active'),
            (2, 'Data Analytics Dashboard', 'Modern business analytics and metrics telemetry view', 'sample_analytics.webp', 'Analytics Charts & Metrics', 'Business', 'active'),
            (3, 'Security Shield Defense', 'Cybersecurity lock and cryptography visualization', 'sample_security.webp', 'Cybersecurity Shield', 'Security', 'active'),
            (4, 'Deprecated Marketing Banner', 'Archived Q1 marketing graphic', 'sample_archive.webp', 'Archived Banner', 'Archive', 'inactive')
        ]
        cursor.executemany("INSERT OR IGNORE INTO images (id, title, description, file_path, alt_text, category, status) VALUES (?, ?, ?, ?, ?, ?, ?)", seed_images)

        seed_sliders = [
            (1, 'Next-Gen Cloud Infrastructure', 'Reliable, scalable, and resilient backend systems tailored for enterprise performance.', 1, 1, 'active'),
            (2, 'Real-Time Telemetry & Insights', 'Monitor system events, audit trails, and user sessions instantly with live telemetry.', 2, 2, 'active'),
            (3, 'Enterprise Grade Security', 'Scrypt password hashing, parameterized queries, and strict input validation built-in.', 3, 3, 'active'),
            (4, 'Winter Special Promo', 'Expired promotional slide from previous seasonal campaign.', 1, 4, 'inactive')
        ]
        cursor.executemany("INSERT OR IGNORE INTO sliders (id, title, description, image_id, display_order, status) VALUES (?, ?, ?, ?, ?, ?)", seed_sliders)

        seed_tooltips = [
            (1, 'btn_save_changes', 'Click to persist your form changes directly to the database.', 'top', 'active'),
            (2, 'input_search_query', 'Enter at least 2 characters to trigger live backend search.', 'bottom', 'active'),
            (3, 'badge_role_admin', 'Administrator privilege grant: Full CRUD and audit log access.', 'right', 'active'),
            (4, 'btn_delete_record', 'Destructive operation: Requires explicit modal confirmation before deletion.', 'left', 'active'),
            (5, 'deprecated_badge', 'This feature will be sunset in v3.', 'top', 'inactive')
        ]
        cursor.executemany("INSERT OR IGNORE INTO tooltips (id, element_name, content, position, status) VALUES (?, ?, ?, ?, ?)", seed_tooltips)

        seed_popups = [
            (1, 'Welcome to Magnus CMS', 'Explore all 11 dynamic More Menu modules. Every single module is backed by Flask REST APIs.', 'page_load', 'active'),
            (2, 'Keyboard Shortcuts Guide', 'Press Esc to dismiss modals, Tab to navigate form fields, and Enter to submit active forms.', 'button_click', 'active'),
            (3, 'Session Maintenance Notice', 'Scheduled system backup will occur tonight at 02:00 AM UTC.', 'manual', 'active'),
            (4, 'Old Holiday Notice', 'Past holiday greetings popup.', 'page_load', 'inactive')
        ]
        cursor.executemany("INSERT OR IGNORE INTO popups (id, title, content, trigger_type, status) VALUES (?, ?, ?, ?, ?)", seed_popups)

        seed_links = [
            (1, 'Flask Official Documentation', 'https://flask.palletsprojects.com/', '_blank', 'Comprehensive guide to building REST APIs and microservices with Flask.', 1, 'active'),
            (2, 'Python Reference Manual', 'https://docs.python.org/3/', '_blank', 'Official Python reference and language guides.', 2, 'active'),
            (3, 'MDN Web Docs - Vanilla JS', 'https://developer.mozilla.org/en-US/docs/Web/JavaScript', '_blank', 'Definitive browser documentation for Fetch API, DOM manipulation, and ES6+ standards.', 3, 'active'),
            (4, 'Local Documentation Portal', '/frontend/dashboard.html', '_self', 'Navigate directly to your internal management portal.', 4, 'active'),
            (5, 'Old Staging Site', 'https://staging.old.magnus.local', '_blank', 'Decommissioned staging server link.', 5, 'inactive')
        ]
        cursor.executemany("INSERT OR IGNORE INTO links (id, title, url, target, description, display_order, status) VALUES (?, ?, ?, ?, ?, ?, ?)", seed_links)

        seed_css = [
            (1, 'border-radius', '8px', '.dynamic-card', 'active'),
            (2, 'background-color', '#f8fafc', '.dynamic-panel', 'active'),
            (3, 'font-weight', '600', '.dynamic-heading', 'active'),
            (4, 'color', '#0f172a', '.dynamic-text', 'active'),
            (5, 'padding', '16px', '.dynamic-box', 'active'),
            (6, 'opacity', '0.9', '.dynamic-badge', 'inactive')
        ]
        cursor.executemany("INSERT OR IGNORE INTO css_properties (id, property_name, property_value, selector, status) VALUES (?, ?, ?, ?, ?)", seed_css)

        seed_iframes = [
            (1, 'OpenStreetMap Embed', 'https://www.openstreetmap.org/export/embed.html?bbox=-0.13,51.50,-0.11,51.52&layer=mapnik', '100%', '420px', 1, 'active'),
            (2, 'Wikipedia Portal Embed', 'https://en.wikipedia.org/wiki/Special:Random', '100%', '450px', 1, 'active'),
            (3, 'Internal Metric View', 'https://example.com', '100%', '350px', 0, 'inactive')
        ]
        cursor.executemany("INSERT OR IGNORE INTO iframes (id, title, url, width, height, allow_fullscreen, status) VALUES (?, ?, ?, ?, ?, ?, ?)", seed_iframes)

        seed_content = [
            (1, 'Company Mission & Vision', 'Core organization values and strategy roadmap', 'At Magnus Technologies, we deliver world-class digital management platforms designed with high reliability, security, and developer productivity in mind.', 'Corporate', 1, 'active'),
            (2, 'Platform Privacy Policy', 'Compliance statement regarding user privacy and GDPR', 'We adhere to rigorous data privacy principles. User information is protected with state-of-the-art encryption standards.', 'Legal', 2, 'active'),
            (3, 'Technical Support Guidelines', 'Tier-1 to Tier-3 escalation matrix and SLAs', 'Standard response SLAs are 24/7 for critical incidents and 1 business day for general feature requests.', 'Support', 3, 'active'),
            (4, 'Draft Marketing Roadmap 2027', 'Internal marketing deliverables and trade shows', 'Confidential preliminary release schedule for upcoming product tiers.', 'Marketing', 4, 'inactive')
        ]
        cursor.executemany("INSERT OR IGNORE INTO content_manager (id, title, description, content, category, display_order, status) VALUES (?, ?, ?, ?, ?, ?, ?)", seed_content)

        seed_media = [
            (1, 'system_architecture_diagram.png', 'image/png', 'sample_cloud.webp', 'Enterprise microservices and API topology diagram', 'Architecture', 'active'),
            (2, 'product_catalog_2026.png', 'image/png', 'sample_analytics.webp', 'Annual corporate asset brochure and capabilities deck', 'Marketing', 'active'),
            (3, 'compliance_certificate.png', 'image/png', 'sample_security.webp', 'ISO 27001 cybersecurity compliance certificate', 'Compliance', 'active'),
            (4, 'archived_draft_logo.png', 'image/png', 'sample_archive.webp', 'Legacy brand asset watermark', 'Archive', 'inactive')
        ]
        cursor.executemany("INSERT OR IGNORE INTO media_manager (id, file_name, file_type, file_path, description, category, status) VALUES (?, ?, ?, ?, ?, ?, ?)", seed_media)

        seed_forms = [
            (1, 'Contact Us & Inquiry Form', 'Standard customer and developer contact form', 'active'),
            (2, 'Customer Feedback Survey', 'Post-onboarding client satisfaction survey', 'active'),
            (3, 'Employee Request Portal', 'Internal equipment and leave request form', 'active'),
            (4, 'Deprecated Partner Onboarding', 'Old partner application form', 'inactive')
        ]
        cursor.executemany("INSERT OR IGNORE INTO forms (id, title, description, status) VALUES (?, ?, ?, ?)", seed_forms)

        seed_form_fields = [
            (1, 1, 'Full Name', 'full_name', 'text', '', 1, 1),
            (2, 1, 'Email Address', 'email', 'email', '', 1, 2),
            (3, 1, 'Phone Number', 'phone', 'phone', '', 0, 3),
            (4, 1, 'Department', 'department', 'dropdown', 'Sales,Technical Support,Billing,General Inquiry', 1, 4),
            (5, 1, 'Message', 'message', 'textarea', '', 1, 5),
            (6, 2, 'Client Name', 'client_name', 'text', '', 1, 1),
            (7, 2, 'Overall Rating', 'rating', 'radio', 'Excellent,Good,Average,Poor', 1, 2),
            (8, 2, 'Feedback Details', 'comments', 'textarea', '', 1, 3),
            (9, 2, 'Subscribe to Updates', 'subscribe', 'checkbox', 'Yes', 0, 4)
        ]
        cursor.executemany("INSERT OR IGNORE INTO form_fields (id, form_id, field_label, field_name, field_type, options, is_required, display_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", seed_form_fields)

        seed_form_subs = [
            (1, 1, '{"full_name": "John Doe", "email": "john.doe@enterprise.com", "phone": "+1-555-0199", "department": "Technical Support", "message": "Inquiring about REST API throughput and webhooks capability."}', '192.168.1.100'),
            (2, 1, '{"full_name": "Jane Smith", "email": "j.smith@cloudtech.io", "phone": "+1-555-0288", "department": "Sales", "message": "Requesting enterprise licensing quote."}', '192.168.1.101'),
            (3, 2, '{"client_name": "Acme Corp", "rating": "Excellent", "comments": "The Magnus dynamic CMS modules have streamlined our operations significantly.", "subscribe": "Yes"}', '192.168.1.102')
        ]
        cursor.executemany("INSERT OR IGNORE INTO form_submissions (id, form_id, submitted_data, ip_address) VALUES (?, ?, ?, ?)", seed_form_subs)

        seed_notifs = [
            (1, None, 'System Security Patch Applied', 'Core database connections and auth middleware updated to the latest security guidelines.', 'success', 'active'),
            (2, None, 'Scheduled Database Maintenance', 'Nightly snapshot backup scheduled for Sunday at 02:00 UTC.', 'info', 'active'),
            (3, None, 'Storage Utilization Notice', 'Uploaded media folder reached 65% capacity.', 'warning', 'active'),
            (4, None, 'Urgent TLS Certificate Expiry', 'Legacy SSL certificates decommissioned.', 'alert', 'active'),
            (5, None, 'Archived Holiday Message', 'Season greetings notice from last year.', 'info', 'inactive'),
            (6, 2, 'Welcome to Your User Portal', 'Your account is active. Explore your personalized dashboard and support services.', 'info', 'active')
        ]
        cursor.executemany("INSERT OR IGNORE INTO notifications (id, user_id, title, message, type, status) VALUES (?, ?, ?, ?, ?, ?)", seed_notifs)

        seed_tickets = [
            (1, 2, 'Need assistance with API access', 'Hello, I would like to request developer API tokens for testing webhook integrations.', 'Technical Support', 'medium', 'open'),
            (2, 2, 'Invoice question for Q3 licensing', 'Can you please confirm if our payment for the Q3 tier has been processed?', 'Billing', 'low', 'resolved')
        ]
        cursor.executemany("INSERT OR IGNORE INTO support_tickets (id, user_id, subject, message, category, priority, status) VALUES (?, ?, ?, ?, ?, ?, ?)", seed_tickets)

        seed_ticket_replies = [
            (1, 1, 2, 'I have reviewed the API documentation and need endpoint guidance.', 0),
            (2, 1, 1, 'Hi! Our team is provisioning your API credentials. You should receive an update shortly.', 1),
            (3, 2, 1, 'Payment has been confirmed and receipt generated.', 1)
        ]
        cursor.executemany("INSERT OR IGNORE INTO ticket_replies (id, ticket_id, user_id, message, is_admin) VALUES (?, ?, ?, ?, ?)", seed_ticket_replies)

        seed_documents = [
            (1, 2, 'Corporate Onboarding Agreement', 'onboarding_agreement.pdf', 'sample_cloud.webp', '245 KB', 'Agreements', 'approved', 'Approved by administrator on onboarding review'),
            (2, 2, 'Q3 Quarterly Compliance Verification', 'compliance_verification.pdf', 'sample_security.webp', '1.2 MB', 'Compliance', 'pending', None)
        ]
        cursor.executemany("INSERT OR IGNORE INTO documents (id, user_id, title, file_name, file_path, file_size, category, status, review_notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", seed_documents)

        seed_settings = [
            (1, 'site_name', 'Magnus Dynamic CMS', 'Main application platform brand name', 'general'),
            (2, 'allow_registration', 'true', 'Permit new public user self-registration', 'security'),
            (3, 'session_timeout_hours', '24', 'Default JWT and session expiration duration in hours', 'security'),
            (4, 'maintenance_mode', 'false', 'Enable temporary maintenance downtime banner', 'system'),
            (5, 'max_upload_size_mb', '5', 'Maximum allowed asset upload file size in MB', 'system'),
            (6, 'email_notifications_enabled', 'true', 'System-wide transactional email notifications toggle', 'notifications')
        ]
        cursor.executemany("INSERT OR IGNORE INTO system_settings (id, setting_key, setting_value, description, category) VALUES (?, ?, ?, ?, ?)", seed_settings)

        seed_user_settings = [
            (1, 1, 1, 1, 1, 'en', 'dark', '+1-555-0100', 'IT Administration', 'Lead System Administrator for Magnus CMS platform infrastructure.'),
            (2, 2, 1, 1, 0, 'en', 'light', '+1-555-0245', 'Operations', 'Standard team member accessing content management and support portal.')
        ]
        cursor.executemany("INSERT OR IGNORE INTO user_settings (id, user_id, email_notifications, security_alerts, activity_digest, language, appearance, phone, department, bio) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", seed_user_settings)

        seed_announcements = [
            (1, 'Platform Maintenance Window Notice', 'Scheduled backend database optimization this Saturday from 02:00 to 03:00 UTC.', 'normal', 'all', 'active'),
            (2, 'New Document Upload Feature Live', 'Users can now upload and track compliance documents directly in their user dashboard.', 'normal', 'all', 'active'),
            (3, 'Security Policy Reminder: Use Strong Passwords', 'Please ensure your account credentials comply with organization password requirements.', 'high', 'all', 'active')
        ]
        cursor.executemany("INSERT OR IGNORE INTO announcements (id, title, message, priority, target_role, status) VALUES (?, ?, ?, ?, ?, ?)", seed_announcements)

        seed_schedules = [
            (1, 2, 'Team Sync & Product Demo', 'Quarterly roadmap demonstration and feature walkthrough', '2026-10-15', '10:00', 'upcoming'),
            (2, 2, 'Security Training Webinar', 'Annual mandatory security awareness training', '2026-10-22', '14:00', 'upcoming')
        ]
        cursor.executemany("INSERT OR IGNORE INTO user_schedules (id, user_id, title, description, event_date, event_time, status) VALUES (?, ?, ?, ?, ?, ?, ?)", seed_schedules)

        seed_favorites = [
            (1, 2, 'Dynamic Multiple Tabs', '/frontend/pages/multiple-tabs.html', 'Module'),
            (2, 2, 'Form Manager', '/frontend/pages/form-manager.html', 'Module')
        ]
        cursor.executemany("INSERT OR IGNORE INTO user_favorites (id, user_id, title, url, category) VALUES (?, ?, ?, ?, ?)", seed_favorites)

        seed_activity = [
            (1, 1, 'SEED', 'SYSTEM', 1, 'System initialized with core and extended More modules'),
            (2, 1, 'CREATE', 'USERS', 1, 'Created system administrator account'),
            (3, 1, 'CREATE', 'CONTENT', 1, 'Published Company Mission & Vision'),
            (4, 1, 'CREATE', 'FORMS', 1, 'Created Contact Us & Inquiry Form'),
            (5, 1, 'SUBMIT', 'FORMS', 1, 'Received new form submission from John Doe'),
            (6, 2, 'CREATE', 'TICKETS', 1, 'Opened support ticket for API access inquiry')
        ]
        cursor.executemany("INSERT OR IGNORE INTO audit_logs (id, user_id, action, module, record_id, description) VALUES (?, ?, ?, ?, ?, ?)", seed_activity)
        cursor.executemany("INSERT OR IGNORE INTO activity_logs (id, user_id, action, module, record_id, description) VALUES (?, ?, ?, ?, ?, ?)", seed_activity)

        conn.commit()
        print("[Database] SQLite database seeded successfully.")
    else:
        # If DB existed, ensure new tables exist too
        schema_ext = """
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ticket_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES support_tickets(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size TEXT DEFAULT '0 KB',
            category TEXT DEFAULT 'General',
            status TEXT DEFAULT 'pending',
            review_notes TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            email_notifications INTEGER DEFAULT 1,
            security_alerts INTEGER DEFAULT 1,
            activity_digest INTEGER DEFAULT 1,
            language TEXT DEFAULT 'en',
            appearance TEXT DEFAULT 'light',
            phone TEXT NULL,
            department TEXT DEFAULT 'General',
            bio TEXT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT NOT NULL UNIQUE,
            setting_value TEXT NOT NULL,
            description TEXT NULL,
            category TEXT DEFAULT 'system',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            priority TEXT DEFAULT 'normal',
            target_role TEXT DEFAULT 'all',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NULL,
            event_date TEXT NOT NULL,
            event_time TEXT DEFAULT '09:00',
            status TEXT DEFAULT 'upcoming',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS user_favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            category TEXT DEFAULT 'Module',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        cursor.executescript(schema_ext)

        # Migration check: Ensure user_id exists in notifications
        cur_cols = [c[1] for c in cursor.execute("PRAGMA table_info(notifications)").fetchall()]
        if "user_id" not in cur_cols:
            try:
                cursor.execute("ALTER TABLE notifications ADD COLUMN user_id INTEGER NULL")
            except Exception as e:
                print(f"Migration error for notifications.user_id: {e}")

        conn.commit()

    if not SQLITE_OWNERSHIP_MIGRATED:
        cursor.execute("UPDATE users SET role = 'user' WHERE role <> 'user'")
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'demo@magnus.com'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "UPDATE users SET name = 'Sample User', email = 'demo@magnus.com' "
                "WHERE email = 'admin@magnus.com'"
            )
        cursor.execute("UPDATE announcements SET target_role = 'user' WHERE target_role = 'admin'")
        for table in MORE_RECORD_TABLES:
            columns = {column[1] for column in cursor.execute(f"PRAGMA table_info({table})").fetchall()}
            if "user_id" not in columns:
                cursor.execute(
                    f"ALTER TABLE {table} ADD COLUMN user_id INTEGER "
                    "REFERENCES users(id) ON DELETE CASCADE"
                )
        conn.commit()
        SQLITE_OWNERSHIP_MIGRATED = True

    conn.close()

if USE_SQLITE:
    _init_sqlite_db()


def _format_row(row):
    if not row or not isinstance(row, dict):
        return row
    formatted = {}
    for k, v in row.items():
        if isinstance(v, (datetime.datetime, datetime.date)):
            formatted[k] = v.strftime("%Y-%m-%d %H:%M:%S")
        else:
            formatted[k] = v
    return formatted


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        val = row[idx]
        if isinstance(val, (datetime.datetime, datetime.date)):
            val = val.strftime("%Y-%m-%d %H:%M:%S")
        d[col[0]] = val
    return d


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Safely executes parameterized SQL queries across MySQL or SQLite.
    Prevents SQL injection by enforcing parameter binding.
    """
    global USE_SQLITE
    
    if USE_SQLITE:
        _init_sqlite_db()
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        try:
            # Convert %s placeholders to ? for SQLite
            sqlite_query = query.replace("%s", "?")
            cursor.execute(sqlite_query, params or ())
            
            last_id = cursor.lastrowid
            row_count = cursor.rowcount
            
            result = None
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall() or []
                
            if commit:
                conn.commit()
                
            return {
                "result": result,
                "last_id": last_id,
                "row_count": row_count
            }
        except Exception as err:
            if commit:
                conn.rollback()
            raise err
        finally:
            cursor.close()
            conn.close()

    # MySQL execution
    conn = None
    cursor = None
    try:
        if HAS_MYSQL_CONNECTOR:
            if db_pool:
                conn = db_pool.get_connection()
            else:
                conn = mysql.connector.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME,
                    autocommit=False
                )
            cursor = conn.cursor(dictionary=True)
        else:
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            cursor = conn.cursor()

        cursor.execute(query, params or ())
        last_id = cursor.lastrowid
        row_count = cursor.rowcount

        result = None
        if fetch_one:
            raw = cursor.fetchone()
            result = _format_row(raw) if raw else None
        elif fetch_all:
            raw = cursor.fetchall()
            result = [_format_row(r) for r in raw] if raw else []
            
        if commit:
            conn.commit()
            
        return {
            "result": result,
            "last_id": last_id,
            "row_count": row_count
        }
    except Exception as err:
        if conn and commit:
            conn.rollback()
        # If MySQL connection dropped, try falling back to SQLite
        if "Can't connect to MySQL" in str(err) or "10061" in str(err) or "Connection refused" in str(err):
            USE_SQLITE = True
            return execute_query(query, params, fetch_one=fetch_one, fetch_all=fetch_all, commit=commit)
        raise err
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def log_audit(user_id, action, module, record_id=None, description=""):
    """
    Inserts a record into both audit_logs and activity_logs tables for traceability.
    """
    try:
        query1 = """
            INSERT INTO audit_logs (user_id, action, module, record_id, description)
            VALUES (%s, %s, %s, %s, %s)
        """
        execute_query(query1, (user_id, action.upper(), module.upper(), record_id, description), commit=True)
        query2 = """
            INSERT INTO activity_logs (user_id, action, module, record_id, description)
            VALUES (%s, %s, %s, %s, %s)
        """
        execute_query(query2, (user_id, action.upper(), module.upper(), record_id, description), commit=True)
    except Exception as e:
        print(f"Audit log failed: {e}")

