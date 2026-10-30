# SmartComplaint – Online Complaint Management System

A secure, full-featured web application for submitting, tracking, assigning, and resolving complaints with a modern responsive UI, real-time status timelines, automated duplicate detection, and analytics reporting.

---

## 🌟 Key Features

### 👤 User Portal
- **Complaint Submission**: File complaints with category, priority, description, and supporting file attachments.
- **Duplicate Detection**: Real-time duplicate checking compares title and description against existing tickets to prevent duplicate submissions.
- **Live Status Tracking**: Search and view detailed timelines of your complaints with step-by-step progress notes.
- **History & Search**: Filter and search complaints by status, category, priority, or keywords.
- **Resolution Feedback**: Star rating (1–5) and comment review upon resolution.
- **In-App Notifications**: Alerts when a complaint is reviewed, assigned, updated, or resolved.

### 🛡️ Administrator Portal
- **Executive Dashboard**: KPI metrics, resolution rate %, status doughnut chart, and 6-month submission trends.
- **Complaint Lifecycle Management**: Filter, view, assign to departments/staff, or update status (with rejection reasons).
- **User & Department Management**: View users, toggle active/deactivated status, modify roles, and create new departments.
- **Reporting & Data Export**: One-click download of complaint records in **CSV** spreadsheet or **PDF** document format (powered by ReportLab).
- **Analytics & Trends**: Visual charts for category breakdowns, priority distributions, and satisfaction scores.

### 👷 Staff Portal
- **Assigned Tasks**: View tasks assigned specifically to you or your department.
- **Progress Updates**: Add timestamped progress notes to the public timeline.
- **Resolution Logging**: Provide resolution details and mark complaints as Resolved.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Windows / Linux / macOS

### 2. Environment Setup
The project virtual environment is already prepared in `.venv`. To activate:

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

Install requirements (if setting up on a new environment):
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```powershell
python run.py
```
Open your web browser and navigate to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Pre-Seeded Demo Accounts

On initial run, the system automatically initializes the database and creates default accounts so you can test all roles immediately:

| Role | Email | Password | Access / Features |
|---|---|---|---|
| **Administrator** | `admin@smartcomplaint.com` | `Admin@123` | Full admin panel, assignment, reports, user control |
| **Department Staff** | `staff@smartcomplaint.com` | `Staff@123` | Assigned tasks dashboard, progress updates, resolution |
| **Regular User** | `user@smartcomplaint.com` | `User@123` | Submit complaints, live tracking, feedback, history |

> **Tip:** You can also click the quick-fill pills on the login page to sign in with one click.

---

## 🗄️ Database Configuration

### SQLite (Default)
By default, the application runs on SQLite (`smartcomplaint.db`), requiring **zero database installation or configuration**.

### MySQL (Optional)
To switch to a MySQL server, edit `.env`:
```ini
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/smartcomplaint_db
```
Make sure the database exists in MySQL:
```sql
CREATE DATABASE smartcomplaint_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 🧪 Running Automated Tests

Run the full automated test suite (covering auth, duplicate detection, lifecycle, notifications, CSV/PDF reports):
```powershell
python -m unittest tests/test_app.py
```

---

## 📂 Project Architecture

```
Online Complaint Management System/
│
├── app/
│   ├── __init__.py            # Flask app factory, extension init, database seeder
│   ├── config.py              # App configuration, DB URI, file limits
│   ├── models.py              # SQLAlchemy models (User, Complaint, Department, etc.)
│   │
│   ├── routes/
│   │   ├── auth.py            # Login, register, logout, role guards
│   │   ├── user.py            # User dashboard, submit, track, history, feedback
│   │   ├── admin.py           # Admin overview, user management, reports, analytics
│   │   └── staff.py           # Staff dashboard, progress update, resolution
│   │
│   ├── services/
│   │   ├── complaint_service.py   # Complaint lifecycle, auto-ID generation, duplicate detection
│   │   ├── notification_service.py # In-app notifications & optional SMTP email
│   │   └── report_service.py      # CSV export, PDF report generation, metrics
│   │
│   ├── static/
│   │   ├── css/style.css      # Modern responsive styling & design tokens
│   │   └── js/
│   │       ├── main.js        # Mobile toggle, modals, quick-login pills
│   │       ├── dashboard.js   # Live duplicate detection debounce & star rating
│   │       └── charts.js      # Chart.js visualizations
│   │
│   └── templates/
│       ├── base.html          # Core responsive sidebar layout
│       ├── auth/              # Login & Register views
│       ├── user/              # User views (dashboard, submit, track, history, alerts)
│       ├── admin/             # Admin views (dashboard, complaints, users, reports, analytics)
│       └── staff/             # Staff views (dashboard, detail)
│
├── tests/
│   └── test_app.py            # Comprehensive unit & integration tests
├── uploads/                   # Uploaded complaint attachments
├── requirements.txt           # Python package dependencies
├── run.py                     # Application entry point
├── .env                       # Environment configuration
└── README.md                  # Documentation
```

