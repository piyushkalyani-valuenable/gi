# GI Claim Assistance API - Deployment Guide

## Domain: gibe.pkcode.in

---

## Quick Deployment Steps

### 1. Upload files to server

```bash
# From your local machine, upload the server folder
scp -r ./server/* user@your-server:/tmp/giclaim-api/

# Or use git
ssh user@your-server
cd /tmp
git clone your-repo-url
cd your-repo/server
```

### 2. Run the deployment script

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### 3. Configure environment

```bash
# Edit the .env file
sudo nano /var/www/giclaim-api/.env
```

**Required settings:**
```env
ENVIRONMENT=production
GEMINI_API_KEY=your_actual_key_here
PORT=8001
HOST=0.0.0.0
CORS_ORIGINS=https://your-frontend-domain.com,http://localhost:5173

# Database settings
LOCAL_DB_HOST=localhost
LOCAL_DB_PORT=3306
LOCAL_DB_USER=your_db_user
LOCAL_DB_PASSWORD=your_db_password
LOCAL_DB_NAME=your_db_name

# Or for AWS RDS
AWS_REGION=ap-south-1
AWS_SECRET_NAME=DB_SECRET
```

### 4. Restart service

```bash
sudo systemctl restart giclaim-api
```

### 5. Get SSL certificate

```bash
sudo certbot --apache -d gibe.pkcode.in
```

---

## Manual Deployment (Step by Step)

If the script doesn't work, follow these manual steps:

### Step 1: Install dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv python3-dev build-essential -y
```

### Step 2: Create app directory

```bash
sudo mkdir -p /var/www/giclaim-api
sudo chown $USER:$USER /var/www/giclaim-api
cp -r ./* /var/www/giclaim-api/
cd /var/www/giclaim-api
```

### Step 3: Setup Python environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn uvicorn[standard]
```

### Step 4: Create systemd service

```bash
sudo nano /etc/systemd/system/giclaim-api.service
```

Paste this content:
```ini
[Unit]
Description=GI Claim Assistance API
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/giclaim-api
Environment="PATH=/var/www/giclaim-api/venv/bin"
EnvironmentFile=/var/www/giclaim-api/.env
ExecStart=/var/www/giclaim-api/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Step 5: Start service

```bash
sudo systemctl daemon-reload
sudo systemctl enable giclaim-api
sudo systemctl start giclaim-api
sudo systemctl status giclaim-api
```

### Step 6: Configure Apache

```bash
# Enable modules
sudo a2enmod proxy proxy_http headers rewrite ssl

# Create virtual host
sudo nano /etc/apache2/sites-available/gibe.pkcode.in.conf
```

Paste this content:
```apache
<VirtualHost *:80>
    ServerName gibe.pkcode.in

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8001/
    ProxyPassReverse / http://127.0.0.1:8001/

    RequestHeader set X-Forwarded-Proto "http"

    ErrorLog ${APACHE_LOG_DIR}/gibe.pkcode.in_error.log
    CustomLog ${APACHE_LOG_DIR}/gibe.pkcode.in_access.log combined
</VirtualHost>
```

```bash
# Enable site
sudo a2ensite gibe.pkcode.in.conf
sudo apache2ctl configtest
sudo systemctl reload apache2
```

### Step 7: SSL Certificate

```bash
sudo certbot --apache -d gibe.pkcode.in
```

---

## Troubleshooting

### Check if service is running
```bash
sudo systemctl status giclaim-api
```

### View logs
```bash
# Application logs
sudo journalctl -u giclaim-api -f

# Apache logs
sudo tail -f /var/log/apache2/gibe.pkcode.in_error.log
```

### Test API directly
```bash
curl http://127.0.0.1:8001/api/health
```

### Restart everything
```bash
sudo systemctl restart giclaim-api
sudo systemctl reload apache2
```

### Check port usage
```bash
sudo netstat -tlnp | grep 8001
```

### Permission issues
```bash
sudo chown -R $USER:www-data /var/www/giclaim-api
sudo chmod -R 755 /var/www/giclaim-api
```

---

## Update Deployment

To update the API after code changes:

```bash
cd /var/www/giclaim-api

# Pull latest code (if using git)
git pull

# Or copy new files
# scp -r ./server/* user@server:/var/www/giclaim-api/

# Activate venv and update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart giclaim-api
```

---

## Architecture

```
Internet → Apache2 (port 80/443) → Gunicorn (port 8001) → FastAPI App
              ↓
         gibe.pkcode.in
              ↓
         SSL/TLS (Certbot)
              ↓
         Reverse Proxy
              ↓
         http://127.0.0.1:8001
```
