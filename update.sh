#!/bin/bash

# Update script for Menstrual Health Chatbot
# This script updates the application code and restarts the service

set -e  # Exit on error

echo "================================================"
echo "Menstrual Health Chatbot - Update Script"
echo "================================================"
echo

# Configuration
APP_NAME="menstrual-health-bot"
APP_DIR="/opt/menstrual_health_bot/ai_chat_bot"
SERVICE_USER="www-data"
SERVICE_GROUP="www-data"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

# Check if service is installed
if ! systemctl list-unit-files | grep -q "$APP_NAME.service"; then
    echo "Error: Service not installed. Please run deploy.sh first"
    exit 1
fi

# Get the current script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Step 1: Stopping service..."
systemctl stop $APP_NAME.service
echo "✓ Service stopped"

echo
echo "Step 2: Backing up current deployment..."
BACKUP_DIR="/opt/menstrual_health_bot/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r "$APP_DIR" "$BACKUP_DIR/"
echo "✓ Backup created at $BACKUP_DIR"

echo
echo "Step 3: Updating application files..."
rsync -av --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' "$SCRIPT_DIR/" "$APP_DIR/"
echo "✓ Files updated"

echo
echo "Step 4: Updating Python dependencies..."
if [ -f "$APP_DIR/requirements.txt" ]; then
    sudo -u $SERVICE_USER "$APP_DIR/venv/bin/pip" install --upgrade -r "$APP_DIR/requirements.txt"
    echo "✓ Dependencies updated"
else
    echo "Warning: requirements.txt not found"
fi

echo
echo "Step 5: Setting file permissions..."
chown -R $SERVICE_USER:$SERVICE_GROUP "$APP_DIR"
# Preserve .env permissions
chmod 600 "$APP_DIR/.env"
echo "✓ Permissions set"

echo
echo "Step 6: Running database migrations..."
sudo -u $SERVICE_USER "$APP_DIR/venv/bin/python" "$APP_DIR/migrate.py" apply || echo "Warning: Migration failed or not needed"
echo "✓ Migrations attempted"

echo
echo "Step 7: Starting service..."
systemctl start $APP_NAME.service
echo "✓ Service started"

echo
echo "Step 8: Checking service status..."
sleep 2
if systemctl is-active --quiet $APP_NAME.service; then
    echo "✓ Service is running"
else
    echo "✗ Service failed to start"
    echo
    echo "Checking logs:"
    journalctl -u $APP_NAME.service -n 20 --no-pager
    echo
    echo "To restore backup:"
    echo "  sudo systemctl stop $APP_NAME"
    echo "  sudo rm -rf $APP_DIR"
    echo "  sudo cp -r $BACKUP_DIR/ai_chat_bot $APP_DIR"
    echo "  sudo systemctl start $APP_NAME"
    exit 1
fi

echo
echo "================================================"
echo "Update Complete!"
echo "================================================"
echo
echo "Service status:"
systemctl status $APP_NAME.service --no-pager -l
echo
echo "View logs: sudo journalctl -u $APP_NAME -f"
echo "Backup location: $BACKUP_DIR"
echo
