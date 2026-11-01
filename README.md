# SmartComplaint — Online Public Grievance & Civic Issue Management System

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Leaflet-OpenStreetMap-199900?style=for-the-badge&logo=leaflet&logoColor=white" alt="Leaflet Maps" />
  <img src="https://img.shields.io/badge/Gunicorn-Production-499848?style=for-the-badge&logo=gunicorn&logoColor=white" alt="Gunicorn" />
  <img src="https://img.shields.io/badge/Render-Deployed-46E3B7?style=for-the-badge&logo=render&logoColor=black" alt="Render" />
</div>

---

> **SmartComplaint** is an enterprise-grade full-stack civic grievance management platform empowering citizens to report, geo-tag, track, and resolve municipal infrastructure breakdowns—such as dangerous potholes, non-functional streetlights, water pipeline bursts, sewage overflows, and garbage dumping.

---

## 🏛️ Live Demonstration & Demo Accounts

| Role | Email | Password | Access Privileges |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@smartcomplaint.com` | `Admin@123` | Department dispatch, status triage, reporting, analytics |
| **Field Officer / Staff** | `staff@smartcomplaint.com` | `Staff@123` | Work orders, progress notes, field resolution |
| **Citizen (Aarav)** | `user@smartcomplaint.com` | `User@123` | Register grievances, pin map, track lifecycle, rate service |
| **Citizen (Pooja)** | `sarah@smartcomplaint.com` | `User@123` | Multi-city complaint tracking & feedback reviews |

---

## 🌟 Core System Capabilities

### 1. Civic Grievance Categories & Dynamic Subcategories
- **Roads & Transportation**: Potholes, Damaged roads, Broken footpaths, Traffic signal issues, Road signs missing
- **Electricity & Streetlights**: Power outages, Streetlights not working, Damaged electric poles, Exposed wiring, Transformer issues
- **Water Supply**: No water supply, Water leakage, Dirty drinking water, Low water pressure, Broken water pipelines
- **Drainage & Sewage**: Blocked drains, Sewage overflow, Open manholes, Waterlogging, Damaged drainage pipes
- **Garbage & Sanitation**: Garbage not collected, Overflowing dustbins, Illegal dumping, Dirty public areas, Public toilet maintenance
- **Public Facilities**: Damaged parks, Broken benches, Playground problems, Community facility maintenance
- **Environment & Public Health**: Air pollution, Noise pollution, Water pollution, Fallen trees, Mosquito breeding areas
- **Other Civic Issues**: Stray animal concerns, Public property damage, Public space encroachment

### 2. Location & Interactive OpenStreetMap (Leaflet.js)
- Pin exact geographic coordinates on an interactive OpenStreetMap.
- Optional **"Use My GPS Location"** using HTML5 Geolocation (permission is strictly optional; manual text entry is fully supported).
- Reverse geocoding via OpenStreetMap Nominatim automatically populates City, State, and Ward when pinning.

### 3. Evidence Upload & Duplicate Detection
- Drag-and-drop photo attachment (PNG, JPG, PDF up to 16 MB) with instant thumbnail preview and removal.
- Optional video upload (MP4, MOV, WEBM up to 50 MB) for dynamic issues like pipeline bursts or flooding.
- Real-time duplicate grievance detection using `SequenceMatcher` algorithm to prevent duplicate municipal tickets.

### 4. End-to-End Civic Lifecycle Workflow
$$\text{Submitted} \longrightarrow \text{Under Review} \longrightarrow \text{Assigned} \longrightarrow \text{In Progress} \longrightarrow \text{Resolved} \longrightarrow \text{Closed}$$
- Support for **Reopened** complaints if problems resurface.
- Rejection workflow with formal rationale logged for auditing.
- Complete chronological timeline tracking with timestamps and officer accountability.
- 5-Star citizen satisfaction rating & review post-resolution.

### 5. Administration & Department Operations
- Multi-dimensional filtering: Civic Category, City/Town, Area, Status, Priority, and Department.
- Executive analytics dashboard: Resolution rates, SLA status breakdown, priority distribution, monthly trends via Chart.js.
- One-click CSV and PDF report generation (via ReportLab).
- Dynamic department management and role assignment.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SmartComplaint Web UI                      │
│     (Jinja2 + Midnight Navy / Teal / Emerald SaaS Design)       │
│      ├── Citizen Portal (/submit, /track, /history, /profile)   │
│      ├── Department Workspace (/staff/dashboard)                │
│      └── Management Console (/admin/dashboard, /admin/analytics)│
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTP (RESTful Routes)
┌────────────────────────────────▼────────────────────────────────┐
│                     Flask Application Layer                     │
│  ├── auth_bp   : Bcrypt Hashing, Role Guards, Session Auth     │
│  ├── user_bp   : Civic Grievance Triage, Subcategory API, Maps  │
│  ├── admin_bp  : Department Management, Status Overrides, Export│
│  └── staff_bp  : Work Orders, Field Notes, Resolution Closures  │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                         Services Layer                          │
│  ├── complaint_service.py   : SC-2026-XXXXX Generation & Triage │
│  ├── notification_service.py: In-App Alerts & Mail Dispatch     │
│  └── report_service.py      : CSV Engine & ReportLab PDF Studio │
└────────────────────────────────┬────────────────────────────────┘
                                 │ SQLAlchemy ORM
┌────────────────────────────────▼────────────────────────────────┐
│                        Database Layer                           │
│     PostgreSQL 15 (Production)  /  SQLite (Local Development)   │
│     Tables: users, departments, complaints, status_timeline,    │
│             notifications, feedback                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Local Development Setup

### 1. Clone & Setup Virtual Environment
```powershell
git clone https://github.com/harshvardhan178-dev/online-complaint-management-system.git
cd online-complaint-management-system

# Create virtual environment
python -m venv .venv

# Activate on Windows
.\.venv\Scripts\activate

# Activate on macOS/Linux
# source .venv/bin/activate
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
```powershell
# Automatically provisions tables and initial admin
python -c "from app import create_app; from app.models import db; app = create_app(); ctx = app.app_context(); ctx.push(); db.create_all()"

# Populate realistic civic grievances across all departments
python seed_demo_data.py
```

### 4. Run Test Suite
```powershell
python -m unittest tests/test_app.py
```

### 5. Launch Development Server
```powershell
python run.py
```
Open **http://127.0.0.1:5000** in your browser.

---

## 🌐 How to Deploy to Production (Step-by-Step)

The project includes pre-configured **`render.yaml`**, **`Procfile`**, and **`wsgi.py`** for automated continuous deployment.

### Option A: Render.com (Recommended Free Deployment)

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Upgrade to civic grievance system with production configs"
   git push origin main
   ```
2. **Open Render Dashboard**:
   - Go to [dashboard.render.com](https://dashboard.render.com/) and click **New +** $\rightarrow$ **Blueprint**.
   - Connect your GitHub repository.
   - Render reads `render.yaml` and provisions:
     - 1 **Web Service** (Python 3.11 running Gunicorn)
     - 1 **PostgreSQL Database** (`smartcomplaint-db`)
3. **Environment Variables**:
   Render automatically links the internal database URL. Fill any optional keys:
   - `SECRET_KEY`: Auto-generated by Render.
   - `DEFAULT_ADMIN_EMAIL`: `admin@smartcomplaint.com`
   - `DEFAULT_ADMIN_PASSWORD`: `<your-secure-password>`
4. **Post-Deployment Verification**:
   - Check the health check endpoint: `https://your-app.onrender.com/health`
   - Log into the admin console with your admin credentials.
   - In Render Shell, you can run `python seed_demo_data.py` to populate initial municipal data.

### Option B: Docker / VPS / Ubuntu Server

Run with Gunicorn behind Nginx:
```bash
gunicorn wsgi:app --workers 3 --bind 0.0.0.0:5000 --timeout 120
```

---

## 🛡️ Security Implementation
- **Password Protection**: Passwords salted and hashed with `Flask-Bcrypt` (Blowfish-based key derivation).
- **Security Response Headers**: Production middleware injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, and `X-XSS-Protection: 1; mode=block`.
- **Role-Based Access Control**: Role decorators (`@admin_required`, `@staff_required`, `@login_required`) enforce privilege boundaries on all endpoints.
- **Upload Sanitization**: Uploaded files processed through `werkzeug.utils.secure_filename`, strictly whitelisted extensions, and 50 MB payload caps.

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
Built as an advanced software engineering portfolio demonstration.
