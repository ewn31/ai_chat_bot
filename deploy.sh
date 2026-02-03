#!/bin/bash

# Deployment script for Menstrual Health Chatbot
# This script sets up the application as a systemd service

set -e  # Exit on error

echo "================================================"
echo "Menstrual Health Chatbot - Deployment Script"
echo "================================================"
echo

# Configuration
APP_NAME="menstrual-health-bot"
APP_DIR="/opt/menstrual_health_bot/ai_chat_bot"
SERVICE_USER="www-data"
SERVICE_GROUP="www-data"
LOG_DIR="/var/log/menstrual_health_bot"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

# Get the current script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Step 1: Creating application directory..."
mkdir -p /opt/menstrual_health_bot
echo "✓ Directory created"

echo
echo "Step 2: Copying application files..."
# Copy all files except venv and __pycache__
rsync -av --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' "$SCRIPT_DIR/" "$APP_DIR/"
echo "✓ Files copied"

echo
echo "Step 3: Creating/verifying service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    echo "Creating user $SERVICE_USER..."
    useradd -r -s /bin/false $SERVICE_USER
else
    echo "User $SERVICE_USER already exists"
fi
echo "✓ User verified"

echo
echo "Step 4: Setting file permissions..."
chown -R $SERVICE_USER:$SERVICE_GROUP /opt/menstrual_health_bot
echo "✓ Permissions set"

echo
echo "Step 5: Setting up Python virtual environment..."
if [ -d "$APP_DIR/venv" ]; then
    echo "Virtual environment already exists, removing old one..."
    rm -rf "$APP_DIR/venv"
fi

sudo -u $SERVICE_USER python3 -m venv "$APP_DIR/venv"
sudo -u $SERVICE_USER "$APP_DIR/venv/bin/pip" install --upgrade pip
echo "✓ Virtual environment created"

echo
echo "Step 6: Installing Python dependencies..."
if [ -f "$APP_DIR/requirements.txt" ]; then
    sudo -u $SERVICE_USER "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
    echo "✓ Dependencies installed"
else
    echo "Warning: requirements.txt not found, skipping dependency installation"
fi

echo
echo "Step 7: Downloading NLTK data..."
if [ -f "$APP_DIR/download_nltk_data.py" ]; then
    sudo -u $SERVICE_USER "$APP_DIR/venv/bin/python" "$APP_DIR/download_nltk_data.py"
    echo "✓ NLTK data downloaded"
else
    echo "Warning: download_nltk_data.py not found, skipping NLTK data download"
fi

echo
echo "Step 8: Creating log directory..."
mkdir -p "$LOG_DIR"
chown $SERVICE_USER:$SERVICE_GROUP "$LOG_DIR"
echo "✓ Log directory created"

echo
echo "Step 9: Checking .env file..."
if [ ! -f "$APP_DIR/.env" ]; then
    echo "Warning: .env file not found"
    echo "Creating template .env file..."
    cat > "$APP_DIR/.env" << 'EOF'
# Application Configuration
PORT=8000
LOGGING_LEVEL=INFO
LOGGING_FILE=/var/log/menstrual_health_bot/chatbot.log

# Add your API keys and other environment variables here
# WHATSAPP_API_KEY=your_key_here
# DATABASE_URL=your_database_url
EOF
    chown $SERVICE_USER:$SERVICE_GROUP "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    echo "✓ Template .env file created"
    echo "  ⚠️  Please edit $APP_DIR/.env and add your configuration!"
else
    echo "✓ .env file exists"
    chmod 600 "$APP_DIR/.env"
    chown $SERVICE_USER:$SERVICE_GROUP "$APP_DIR/.env"
fi

echo
echo "Step 10: Installing systemd service..."
cp "$APP_DIR/$APP_NAME.service" /etc/systemd/system/
systemctl daemon-reload
echo "✓ Service installed"

echo
echo "Step 11: Enabling service to start on boot..."
systemctl enable $APP_NAME.service
echo "✓ Service enabled"

echo
echo "================================================"
echo "Deployment Complete!"
echo "================================================"
echo
echo "Next steps:"
echo "1. Edit configuration: sudo nano $APP_DIR/.env"
echo "2. Start the service: sudo systemctl start $APP_NAME.service"
echo "3. Check status: sudo systemctl status $APP_NAME.service"
echo "4. View logs: sudo journalctl -u $APP_NAME.service -f"
echo
echo "Quick commands:"
echo "  Start:   sudo systemctl start $APP_NAME"
echo "  Stop:    sudo systemctl stop $APP_NAME"
echo "  Restart: sudo systemctl restart $APP_NAME"
echo "  Status:  sudo systemctl status $APP_NAME"
echo "  Logs:    sudo journalctl -u $APP_NAME -f"
echo
echo "For production, consider:"
echo "  - Setting up Nginx as a reverse proxy"
echo "  - Configuring SSL/TLS certificates"
echo "  - Setting up a firewall"
echo
echo "See SYSTEMD_SETUP.md for detailed documentation"
echo
