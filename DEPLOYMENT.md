# SmartComplaint — Production Deployment Guide

This guide explains how to deploy SmartComplaint to Linux (Ubuntu/Debian VPS) or Windows Server in production.

---

## 1. Production Architecture Overview

```
                      HTTPS (443)
                          │
                   [Nginx / Caddy]  (Reverse Proxy, SSL, Static Files)
                          │
                     HTTP (5000)
                          │
             [Gunicorn / Waitress WSGI] (Python Workers)
                          │
                  [SmartComplaint App]
                          │
              [MySQL 8.0+ / PostgreSQL]
```

---

## 2. Production Environment Checklist (`.env`)

Never use default or debug values in production. Set these in your server `.env`:

```ini
# Flask Security
SECRET_KEY=generate-a-strong-random-key-64-chars
FLASK_ENV=production
FLASK_DEBUG=0

# Production Database (MySQL)
DATABASE_URL=mysql+pymysql://complaint_user:SecurePassword123@127.0.0.1:3306/smartcomplaint_db

# File Upload Limits
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=/var/www/smartcomplaint/uploads

# Real SMTP Email Delivery (Gmail, SendGrid, Amazon SES)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-org-alert@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=SmartComplaint <your-org-alert@gmail.com>
```

---

## 3. Linux Deployment (Ubuntu 22.04 / 24.04 VPS)

### Step 1: Install System Dependencies
```bash
sudo apt update && sudo apt install -y python3-venv python3-pip mysql-server nginx git
```

### Step 2: Set Up MySQL Database
```sql
sudo mysql -u root
CREATE DATABASE smartcomplaint_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'complaint_user'@'localhost' IDENTIFIED BY 'SecurePassword123';
GRANT ALL PRIVILEGES ON smartcomplaint_db.* TO 'complaint_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Step 3: Clone Code & Setup Virtual Environment
```bash
cd /var/www
sudo git clone <repo_url> smartcomplaint
cd /var/www/smartcomplaint
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### Step 4: Systemd Service (`/etc/systemd/system/smartcomplaint.service`)
```ini
[Unit]
Description=Gunicorn instance to serve SmartComplaint
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/smartcomplaint
Environment="PATH=/var/www/smartcomplaint/.venv/bin"
ExecStart=/var/www/smartcomplaint/.venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 wsgi:app

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start smartcomplaint
sudo systemctl enable smartcomplaint
```

### Step 5: Configure Nginx as Reverse Proxy (`/etc/nginx/sites-available/smartcomplaint`)
```nginx
server {
    listen 80;
    server_name complaints.yourdomain.com;

    client_max_body_size 16M;

    location /static/ {
        alias /var/www/smartcomplaint/app/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Enable the site & obtain free SSL via Certbot:
```bash
sudo ln -s /etc/nginx/sites-available/smartcomplaint /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo certbot --nginx -d complaints.yourdomain.com
```

---

## 4. Windows Server Deployment (Waitress)

Install Waitress in the virtual environment:
```powershell
.\.venv\Scripts\pip install waitress
```

Run as a Windows service using NSSM (Non-Sucking Service Manager) or task scheduler:
```powershell
.\.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:5000 wsgi:app
```

Use IIS as a reverse proxy with URL Rewrite and ARR (Application Request Routing).

