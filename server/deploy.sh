#!/bin/bash

# =============================================================================
# GI Claim Assistance API - Deployment Script
# Domain: gibe.pkcode.in
# =============================================================================

set -e  # Exit on any error

# Configuration
APP_NAME="giclaim-api"
APP_DIR="/var/www/giclaim-api"
SERVICE_NAME="giclaim-api"
DOMAIN="gibe.pkcode.in"
PORT=8001  # Using 8001 to avoid conflict with existing FastAPI on 8000

echo "🚀 Setting up GI Claim Assistance API"
echo "   Domain: $DOMAIN"
echo "   Port: $PORT"
echo ""

# =============================================================================
# Step 1: Update system and install dependencies
# =============================================================================
echo "📦 Updating system..."
sudo apt update && sudo apt upgrade -y

echo "🐍 Installing Python and dependencies..."
sudo apt install python3-pip python3-venv python3-dev -y

echo "🔧 Installing build dependencies..."
sudo apt install build-essential libffi-dev -y

# =============================================================================
# Step 2: Create application directory and copy files
# =============================================================================
echo "📁 Setting up application directory..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy files (assuming you're running this from the server folder)
echo "📋 Copying application files..."
cp -r ./* $APP_DIR/
cd $APP_DIR

# Remove local virtual environment if copied
rm -rf myenv __pycache__ .git

# =============================================================================
# Step 3: Create virtual environment and install packages
# =============================================================================
echo "🔧 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn uvicorn[standard]

# =============================================================================
# Step 4: Create .env file if it doesn't exist
# =============================================================================
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        cat > .env << 'ENVFILE'
# Environment: production for server
ENVIRONMENT=production

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Server Configuration
PORT=8001
HOST=0.0.0.0

# CORS Configuration (add your frontend domain)
CORS_ORIGINS=https://gibe.pkcode.in,http://localhost:5173,http://localhost:3000

# Local Database (if using local DB)
LOCAL_DB_HOST=localhost
LOCAL_DB_PORT=3306
LOCAL_DB_USER=root
LOCAL_DB_PASSWORD=your_password
LOCAL_DB_NAME=mydb

# AWS Configuration (for production with AWS RDS)
AWS_REGION=ap-south-1
AWS_SECRET_NAME=DB_SECRET
ENVFILE
    fi
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and configure your settings!"
    echo "   Run: sudo nano $APP_DIR/.env"
fi

# =============================================================================
# Step 5: Create systemd service
# =============================================================================
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=GI Claim Assistance API
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:$PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# =============================================================================
# Step 6: Enable and start the service
# =============================================================================
echo "🎬 Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# =============================================================================
# Step 7: Configure Apache2 Virtual Host
# =============================================================================
echo "🌐 Configuring Apache2 for $DOMAIN..."

# Enable required Apache modules
sudo a2enmod proxy proxy_http proxy_balancer lbmethod_byrequests headers rewrite ssl

# Create Apache virtual host
sudo tee /etc/apache2/sites-available/${DOMAIN}.conf > /dev/null <<EOF
<VirtualHost *:80>
    ServerName $DOMAIN
    ServerAdmin webmaster@$DOMAIN

    # Redirect all HTTP to HTTPS (enable after SSL setup)
    # RewriteEngine On
    # RewriteCond %{HTTPS} off
    # RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

    # Proxy settings
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:$PORT/
    ProxyPassReverse / http://127.0.0.1:$PORT/

    # Headers
    RequestHeader set X-Forwarded-Proto "http"
    RequestHeader set X-Forwarded-For "%{REMOTE_ADDR}s"

    # Logging
    ErrorLog \${APACHE_LOG_DIR}/${DOMAIN}_error.log
    CustomLog \${APACHE_LOG_DIR}/${DOMAIN}_access.log combined
</VirtualHost>
EOF

# Enable the site
sudo a2ensite ${DOMAIN}.conf

# Test Apache configuration
echo "🔍 Testing Apache configuration..."
sudo apache2ctl configtest

# Reload Apache
echo "🔄 Reloading Apache..."
sudo systemctl reload apache2

# =============================================================================
# Step 8: Setup SSL with Certbot (Let's Encrypt)
# =============================================================================
echo ""
echo "🔒 SSL Certificate Setup"
echo "   Run the following command to get SSL certificate:"
echo ""
echo "   sudo certbot --apache -d $DOMAIN"
echo ""

# =============================================================================
# Completion
# =============================================================================
echo ""
echo "✅ Deployment complete!"
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "📋 NEXT STEPS:"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo "1. Configure your .env file:"
echo "   sudo nano $APP_DIR/.env"
echo ""
echo "2. Add your Gemini API key and database credentials"
echo ""
echo "3. Restart the service:"
echo "   sudo systemctl restart $SERVICE_NAME"
echo ""
echo "4. Get SSL certificate:"
echo "   sudo certbot --apache -d $DOMAIN"
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "📊 USEFUL COMMANDS:"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo "Check service status:  sudo systemctl status $SERVICE_NAME"
echo "View service logs:     sudo journalctl -u $SERVICE_NAME -f"
echo "Restart service:       sudo systemctl restart $SERVICE_NAME"
echo "Stop service:          sudo systemctl stop $SERVICE_NAME"
echo "Apache logs:           sudo tail -f /var/log/apache2/${DOMAIN}_error.log"
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "🌐 YOUR API ENDPOINTS:"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo "API URL:     http://$DOMAIN"
echo "Health:      http://$DOMAIN/api/health"
echo "Docs:        http://$DOMAIN/docs"
echo "OpenAPI:     http://$DOMAIN/openapi.json"
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
