# Magnus Dynamic Content Management System (CMS)

A full-stack Magnus application with a single user account type, session/JWT authentication, scrypt password hashing, and MySQL-backed More module records.

---

## 1. Project Overview

Signed-in users can configure and manage their own records in the 11 existing More modules:

1. **Multiple Tabs** – Dynamic tabbed panels with ordering and active state control.
2. **Navigation Menu** – Hierarchical parent-child and nested dropdown menu trees.
3. **Autocomplete** – Real-time backend search powered by MySQL `LIKE` queries with a 2-character threshold.
4. **Collapsible Content** – Expandable/collapsible FAQ and documentation accordions.
5. **Image Library** – Multi-format image asset uploads (JPG, PNG, WebP) with size validation and filesystem storage.
6. **Hero Slider** – Interactive image carousel with automated slide transitions, prev/next navigation, and dot indicators.
7. **Tooltips** – Contextual micro-guides with dynamic top/bottom/left/right boundary positioning.
8. **Modal Popups** – Configurable dialog alerts supporting button clicks, page load, and manual triggers.
9. **Managed Links** – Protocol-safe URL directory with target controls (`_self`, `_blank`).
10. **CSS Properties** – Whitelisted runtime stylesheet rule injection preventing unsafe script execution.
11. **iFrame Embeds** – Secure HTTPS sandboxed external portals and map embeds.
12. **Audit Logging** – Automatic audit logging for every `CREATE`, `UPDATE`, `DELETE`, `LOGIN`, and `LOGOUT` event.

---

## 2. Technology Stack

- **Frontend**:
  - HTML5 & CSS3 (Vanilla CSS, custom design system, no Tailwind)
  - Vanilla JavaScript (ES6+, Fetch API, async/await, no React/Next.js)
  - Fully responsive layout for desktop, tablet, and mobile
- **Backend**:
  - Python 3.10+
  - Flask 3.x
  - Flask-CORS
  - PyJWT & Werkzeug security (scrypt cryptographic password hashing)
- **Database & Storage**:
  - MySQL 8.0 / MariaDB
  - Normalized schema (`magnus_cms`) with foreign keys, cascading rules, and indexes
  - Disk-backed secure image file storage

---

## 3. Architecture & Project Structure

```
e:\task
│   .env.example
│   .gitignore
│   app.py                     # Root runner (python app.py)
│   README.md
│   requirements.txt
│
├───backend
│   │   app.py                 # Core Flask WSGI application
│   │
│   ├───config
│   │       database.py        # MySQL connection pooling & parameterized query layer
│   │
│   ├───controllers
│   │       auth_controller.py
│   │       autocomplete_controller.py
│   │       collapsible_controller.py
│   │       css_controller.py
│   │       dashboard_controller.py
│   │       iframe_controller.py
│   │       images_controller.py
│   │       links_controller.py
│   │       menu_controller.py
│   │       popup_controller.py
│   │       slider_controller.py
│   │       tabs_controller.py
│   │       tooltip_controller.py
│   │
│   ├───middleware
│   │       auth_middleware.py # JWT verification & role authorization decorators
│   │
│   ├───routes
│   │       auth_routes.py
│   │       autocomplete_routes.py
│   │       collapsible_routes.py
│   │       css_routes.py
│   │       dashboard_routes.py
│   │       iframe_routes.py
│   │       images_routes.py
│   │       links_routes.py
│   │       menu_routes.py
│   │       popup_routes.py
│   │       slider_routes.py
│   │       tabs_routes.py
│   │       tooltip_routes.py
│   │
│   ├───services
│   │       auth_service.py        # Scrypt password hashing & JWT encoding/decoding
│   │       upload_service.py      # Secure filename generation & MIME/size validation
│   │       validation_service.py  # Business logic & field validation
│   │
│   ├───uploads/               # Uploaded image file storage
│   │
│   └───utils
│           responses.py       # Standardized JSON response envelope
│           validators.py      # CSS whitelist, URL protocol sanitizers, email regex
│
├───database
│       schema.sql             # Complete normalized MySQL DDL
│       seed.sql               # Initial administrator, standard user & sample module data
│
└───frontend
    │   dashboard.html         # Admin executive dashboard & audit log activity feed
    │   index.html             # Public user portal showcasing all 11 active features
    │   login.html             # Authentication login screen with demo credentials filler
    │
    ├───css
    │       dashboard.css      # Sidebar, topbar, stats cards, and audit feed styling
    │       forms.css          # Input states, validation alerts, and file dropzone
    │       style.css          # Design system tokens, buttons, badges, modals, toasts
    │       tables.css         # Data tables, filters, search boxes, and action buttons
    │
    ├───js
    │       api.js             # Central fetch client, JWT bearer headers & toast dispatcher
    │       auth.js            # Auth guards, role checks & sidebar user profile
    │       autocomplete.js    # Autocomplete CRUD & live MySQL search test
    │       collapsible.js     # Collapsible CRUD & accordion interactions
    │       css-properties.js  # Safe CSS rules CRUD & live stylesheet injection
    │       dashboard.js       # Metrics calculation & audit log rendering
    │       iframes.js         # iFrame CRUD & sandboxed previews
    │       images.js          # File upload handler & asset gallery
    │       links.js           # Verified links CRUD & protocol security
    │       menu.js            # Menu hierarchy builder & parent-child trees
    │       multiple-tabs.js   # Dynamic tabs CRUD & tab switching
    │       popups.js          # Modal popups CRUD & trigger simulator
    │       slider.js          # Slider CRUD & automated carousel
    │       tooltips.js        # Tooltips CRUD & dynamic viewport boundary positioning
    │
    └───pages                  # Admin CRUD Management Pages for all 11 modules
            autocomplete.html
            collapsible.html
            css-properties.html
            iframes.html
            images.html
            links.html
            menu.html
            multiple-tabs.html
            popups.html
            slider.html
            tooltips.html
```

---

## 4. Database Setup & Schema

The application uses a normalized MySQL database named `magnus_cms`.

### Tables Summary

| Table | Primary Key | Description |
|---|---|---|
| `users` | `id` | User accounts with scrypt-hashed passwords and a single `user` role. |
| `tabs` | `id` | Tab navigation panels with display order and active status. |
| `menus` | `id` | Hierarchical menus with `parent_id` foreign key referencing `menus(id)`. |
| `autocomplete_items` | `id` | Keyword records indexed for SQL `LIKE` queries. |
| `collapsible_contents` | `id` | Expandable accordion content entries. |
| `images` | `id` | Metadata and filesystem storage paths for uploaded assets. |
| `sliders` | `id` | Image slides with foreign key reference `image_id -> images(id)`. |
| `tooltips` | `id` | Element identifiers, message contents, and positioning (`top`, `bottom`, `left`, `right`). |
| `popups` | `id` | Modal dialogs with trigger types (`button_click`, `page_load`, `manual`). |
| `links` | `id` | Protocol-validated URLs with target window settings (`_self`, `_blank`). |
| `css_properties` | `id` | Whitelisted CSS attribute rules and target selectors. |
| `iframes` | `id` | HTTPS embed frame configurations with dimensions and fullscreen flags. |
| `audit_logs` | `id` | Chronological activity log tracking user IDs, actions, modules, and descriptions. |

### MySQL Setup Commands

1. Make sure MySQL Server is running (e.g. via MySQL Service or XAMPP on port 3306).
2. Execute the schema and seed scripts:

```bash
# In MySQL Shell or terminal:
mysql -u root -p < database/schema.sql
mysql -u root -p magnus_cms < database/seed.sql
```

*(On Windows PowerShell, run: `Get-Content database/schema.sql | mysql -u root; Get-Content database/seed.sql | mysql -u root magnus_cms`)*

---

## 5. Python Environment & Installation

### Prerequisites
- Python 3.10 or higher
- pip package manager
- Running MySQL instance

### Installation Steps

1. Clone or extract the repository into your workspace.
2. Create and activate a Python virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 6. Environment Variables (`.env`)

Create a `.env` file in the root directory (based on `.env.example`):

```ini
# Database Configuration
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=magnus_cms

# Flask Server Configuration
FLASK_ENV=development
FLASK_DEBUG=1
PORT=5000
SECRET_KEY=super-secret-magnus-cms-key-change-in-production-2026
JWT_EXPIRATION_HOURS=24

# File Uploads Configuration
UPLOAD_FOLDER=backend/uploads
MAX_CONTENT_LENGTH=5242880
ALLOWED_EXTENSIONS=jpg,jpeg,png,webp
```

---

## 7. Running the Application

### Start the Flask Server
From the root directory:
```bash
python app.py
```
*(Or alternatively: `python backend/app.py`)*

The server starts on `http://127.0.0.1:5000`.

### Access URLs
- **Public Portal (User View)**: [http://127.0.0.1:5000/frontend/index.html](http://127.0.0.1:5000/frontend/index.html)
- **Login**: [http://127.0.0.1:5000/login](http://127.0.0.1:5000/login)
- **Dashboard**: [http://127.0.0.1:5000/dashboard](http://127.0.0.1:5000/dashboard)

---

## 8. Demo Credentials

| Account | Email | Password |
|---|---|---|
| **Demo user** | `user@magnus.com` | `UserPassword123!` |

*(The login screen provides a Fill button for the demo account.)*

---

## 9. REST API Documentation

### Authentication
- `POST /api/auth/login` – Authenticate with email & password. Returns JWT token and user profile.
- `POST /api/auth/logout` – Invalidate session and record audit log.
- `GET  /api/auth/me` – Retrieve current authenticated user profile.

### Dashboard & Auditing
- `GET /api/dashboard/stats` – Get total record counts for all 11 modules and users.
- `GET /api/audit-logs` – Retrieve paginated audit trail logs (`?page=1&limit=25&module=...`).

All More write operations require authentication and are limited to the signed-in user's records. Legacy shared rows are read-only; cross-user record access returns 404.

### Multiple Tabs
- `GET    /api/tabs` – List tabs (`?status=active|inactive|all&search=...`).
- `GET    /api/tabs/<id>` – Retrieve single tab by ID.
- `POST   /api/tabs` – Create an owned tab (`title`, `content`, `display_order`, `status`).
- `PUT    /api/tabs/<id>` – Update an owned tab.
- `DELETE /api/tabs/<id>` – Delete an owned tab.

### Navigation Menu
- `GET    /api/menus` – List menus (`?status=active|inactive|all&tree=true|false&search=...`).
- `GET    /api/menus/<id>` – Retrieve single menu item.
- `POST   /api/menus` – Create an owned menu (`name`, `url`, `parent_id`, `display_order`, `status`).
- `PUT    /api/menus/<id>` – Update an owned menu item. Prevents cyclic parenting.
- `DELETE /api/menus/<id>` – Delete an owned menu item. Reparents owned child items safely.

### Autocomplete
- `GET    /api/autocomplete` – List all autocomplete items with filters.
- `GET    /api/autocomplete/search?q=<query>` – Backend SQL `LIKE` search for queries &ge; 2 chars.
- `GET    /api/autocomplete/<id>` – Retrieve single autocomplete record.
- `POST   /api/autocomplete` – Create an owned item (`label`, `value`, `description`, `status`).
- `PUT    /api/autocomplete/<id>` – Update an owned item.
- `DELETE /api/autocomplete/<id>` – Delete an owned item.

### Collapsible Content
- `GET    /api/collapsible` – List collapsible sections (`?status=active|inactive|all&search=...`).
- `GET    /api/collapsible/<id>` – Retrieve single section.
- `POST   /api/collapsible` – Create an owned collapsible (`title`, `content`, `display_order`, `status`).
- `PUT    /api/collapsible/<id>` – Update an owned collapsible.
- `DELETE /api/collapsible/<id>` – Delete an owned collapsible.

### Image Library
- `GET    /api/images` – List images (`?status=active|inactive|all&category=...&search=...`).
- `GET    /api/images/<id>` – Retrieve single image details.
- `POST   /api/images` – Create an owned image with safe filename generation and MIME validation.
- `PUT    /api/images/<id>` – Update owned metadata or replace the image file.
- `DELETE /api/images/<id>` – Delete an owned record and remove its file.

### Hero Slider
- `GET    /api/sliders` – List sliders with joined image data (`?status=active|inactive|all`).
- `GET    /api/sliders/<id>` – Retrieve single slide.
- `POST   /api/sliders` – Create an owned slide linked to a shared or owned `image_id`.
- `PUT    /api/sliders/<id>` – Update an owned slide.
- `DELETE /api/sliders/<id>` – Delete an owned slide.

### Tooltips
- `GET    /api/tooltips` – List tooltips (`?status=active|inactive|all`).
- `GET    /api/tooltips/<id>` – Retrieve single tooltip.
- `POST   /api/tooltips` – Create an owned tooltip (`element_name`, `content`, `position`, `status`).
- `PUT    /api/tooltips/<id>` – Update an owned tooltip.
- `DELETE /api/tooltips/<id>` – Delete an owned tooltip.

### Modal Popups
- `GET    /api/popups` – List popups (`?trigger_type=...&status=...`).
- `GET    /api/popups/<id>` – Retrieve single popup.
- `POST   /api/popups` – Create an owned popup (`title`, `content`, `trigger_type`, `status`).
- `PUT    /api/popups/<id>` – Update an owned popup.
- `DELETE /api/popups/<id>` – Delete an owned popup.

### Managed Links
- `GET    /api/links` – List links (`?status=active|inactive|all`).
- `GET    /api/links/<id>` – Retrieve single link.
- `POST   /api/links` – Create an owned link (`title`, `url`, `target`, `description`, `display_order`, `status`).
- `PUT    /api/links/<id>` – Update an owned link. Validates against dangerous protocols.
- `DELETE /api/links/<id>` – Delete an owned link.

### CSS Properties
- `GET    /api/css-properties` – List CSS rules (`?status=active|inactive|all`).
- `GET    /api/css-properties/<id>` – Retrieve single CSS property.
- `POST   /api/css-properties` – Create an owned CSS property. Strictly checks the allowed whitelist.
- `PUT    /api/css-properties/<id>` – Update an owned CSS property.
- `DELETE /api/css-properties/<id>` – Delete an owned CSS property.

### iFrame Embeds
- `GET    /api/iframes` – List iframe embeds (`?status=active|inactive|all`).
- `GET    /api/iframes/<id>` – Retrieve single iframe embed.
- `POST   /api/iframes` – Create an owned iframe (`title`, `url`, `width`, `height`, `allow_fullscreen`, `status`).
- `PUT    /api/iframes/<id>` – Update an owned iframe. Enforces secure HTTPS URL validation.
- `DELETE /api/iframes/<id>` – Delete an owned iframe.

---

## 10. Security & Quality Assurance

- **SQL Injection Prevention**: Every single query uses parameterized `execute_query(query, params)` with tuple binding. No raw string interpolation.
- **Password Protection**: Passwords are never stored in plaintext. They are encrypted using Werkzeug's cryptographic `scrypt` hashing algorithm.
- **CSS Execution Whitelist**: Only safe properties (`font-size`, `font-weight`, `color`, `background-color`, `border-radius`, `padding`, `margin`, `width`, `height`, `opacity`, `display`, `text-align`) can be saved. Executable expressions (`expression()`, `javascript:`, `<script>`) are rejected.
- **URL Sanitization**: Dangerous protocols (`javascript:`, `data:`, `vbscript:`) are blocked for links and iframes.
- **Upload Safety**: Files are checked for permitted extensions (JPG, JPEG, PNG, WebP) and 5MB size limits, saved with UUIDs to eliminate path traversal vulnerabilities.
- **Audit Traceability**: All critical administrative and authentication operations are logged to the `audit_logs` table.

---

## 11. Screenshots Section Placeholder

- **Public Portal**: Showcase of dynamic sliders, tabs, search, and accordions.
- **Admin Dashboard**: Real-time metrics and audit log activity stream.
- **Module Management**: Data table with live preview playground and modal editor.

---

## 12. Future Enhancements

- Multi-tenant organization support and role permission granularity.
- Drag-and-drop visual reordering for menus and hero sliders.
- Advanced image cropping and responsive thumbnail generation via Pillow.
- Export audit logs to CSV and JSON formats.
