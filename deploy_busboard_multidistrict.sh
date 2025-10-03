#!/bin/bash
# Full multi-district deployment script for Bus Status Board on Ubuntu

# -----------------------------
# Configuration - EDIT THESE
# -----------------------------
APP_NAME="busboard"
APP_DIR="/home/ubuntu/$APP_NAME"   # directory where the app will live
GITHUB_REPO="https://github.com/AJOAISD/bus-status-board.git"  # replace with your repo
PYTHON_VERSION="python3"
DOMAIN="your_domain_or_ip"        # change this if you have a domain
GUNICORN_PORT=8000
USER="ubuntu"
GROUP="www-data"
# -----------------------------

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-venv python3-pip nginx git sqlite3

# Clone the repo (or pull if it exists)
if [ -d "$APP_DIR" ]; then
    cd $APP_DIR || exit
    git pull
else
    git clone $GITHUB_REPO $APP_DIR
    cd $APP_DIR || exit
fi

# Create virtual environment
$PYTHON_VERSION -m venv venv
source venv/bin/activate

# Install Python packages from requirements.txt if exists, else install Flask & Gunicorn
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
else
    pip install --upgrade pip
    pip install flask gunicorn
fi

# Deactivate virtualenv
deactivate

# Create data directory for district databases
mkdir -p $APP_DIR/data

# Optional: Create initial example district
DB_FILE="$APP_DIR/data/district1.db"
if [ ! -f "$DB_FILE" ]; then
    sqlite3 $DB_FILE <<EOF
CREATE TABLE IF NOT EXISTS buses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bus_number TEXT NOT NULL,
    driver TEXT NOT NULL,
    status TEXT NOT NULL,
    notes TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT NOT NULL,
    run_time TEXT NOT NULL,
    group_name TEXT NOT NULL,
    destination TEXT NOT NULL,
    driver TEXT NOT NULL,
    bus_number TEXT NOT NULL
);
EOF
    echo "Initial district database created at $DB_FILE"
fi

# -----------------------------
# Create systemd service
# -----------------------------
SERVICE_FILE="/etc/systemd/system/$APP_NAME.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Bus Board Flask App
After=network.target

[Service]
User=$USER
Group=$GROUP
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:$GUNICORN_PORT app:app

[Install]
WantedBy=multi-user.target
EOL

sudo systemctl daemon-reload
sudo systemctl start $APP_NAME
sudo systemctl enable $APP_NAME

# -----------------------------
# Configure NGINX
# -----------------------------
NGINX_FILE="/etc/nginx/sites-available/$APP_NAME"

sudo bash -c "cat > $NGINX_FILE" <<EOL
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:$GUNICORN_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL

# Enable site and restart nginx
sudo ln -s /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# -----------------------------
# Optional: HTTPS with Certbot
# -----------------------------
echo "If you have a domain, install certbot for HTTPS:"
echo "sudo apt install certbot python3-certbot-nginx"
echo "sudo certbot --nginx -d $DOMAIN"

# -----------------------------
# Done
# -----------------------------
echo "Deployment complete! Your app should be available at http://$DOMAIN"
echo "Systemd service: sudo systemctl status $APP_NAME"
echo "Gunicorn logs: sudo journalctl -u $APP_NAME -f"
echo "Initial example district database: $APP_DIR/data/district1.db"
