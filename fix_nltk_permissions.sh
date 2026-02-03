#!/bin/bash

# Quick fix script for NLTK permission errors
# Run this on your server to fix the NLTK data directory issue

set -e

echo "================================================"
echo "NLTK Permission Fix Script"
echo "================================================"
echo

APP_DIR="/opt/menstrual_health_bot/ai_chat_bot"
SERVICE_USER="www-data"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

echo "Step 1: Stopping service..."
systemctl stop menstrual-health-bot.service 2>/dev/null || echo "Service not running"
echo "✓ Service stopped"

echo
echo "Step 2: Creating NLTK data directory..."
mkdir -p "$APP_DIR/nltk_data"
chown -R $SERVICE_USER:$SERVICE_USER "$APP_DIR/nltk_data"
echo "✓ Directory created"

echo
echo "Step 3: Downloading NLTK data..."
if [ -f "$APP_DIR/download_nltk_data.py" ]; then
    cd "$APP_DIR"
    sudo -u $SERVICE_USER NLTK_DATA="$APP_DIR/nltk_data" "$APP_DIR/venv/bin/python" "$APP_DIR/download_nltk_data.py"
    echo "✓ NLTK data downloaded"
else
    echo "Warning: download_nltk_data.py not found"
    echo "Downloading it now..."

    # Create the download script
    cat > "$APP_DIR/download_nltk_data.py" << 'EOFPYTHON'
#!/usr/bin/env python3
"""Download required NLTK data packages for the chatbot."""

import os
import nltk
import sys

def download_nltk_data():
    """Download all required NLTK packages."""

    # Set NLTK data path to application directory
    nltk_data_dir = os.path.join(os.path.dirname(__file__), 'nltk_data')
    os.makedirs(nltk_data_dir, exist_ok=True)

    # Add to NLTK's data path
    if nltk_data_dir not in nltk.data.path:
        nltk.data.path.insert(0, nltk_data_dir)

    print(f"Downloading NLTK data to: {nltk_data_dir}")

    # List of required packages
    packages = [
        'punkt',
        'punkt_tab',
        'averaged_perceptron_tagger',
        'averaged_perceptron_tagger_eng',
    ]

    success = True
    for package in packages:
        try:
            print(f"Downloading {package}...", end=' ')
            nltk.download(package, download_dir=nltk_data_dir, quiet=True)
            print("✓")
        except Exception as e:
            print(f"✗ Failed: {e}")
            success = False

    if success:
        print("\n✓ All NLTK packages downloaded successfully")
        return 0
    else:
        print("\n✗ Some packages failed to download")
        return 1

if __name__ == "__main__":
    sys.exit(download_nltk_data())
EOFPYTHON

    chown $SERVICE_USER:$SERVICE_USER "$APP_DIR/download_nltk_data.py"
    chmod +x "$APP_DIR/download_nltk_data.py"

    cd "$APP_DIR"
    sudo -u $SERVICE_USER NLTK_DATA="$APP_DIR/nltk_data" "$APP_DIR/venv/bin/python" "$APP_DIR/download_nltk_data.py"
    echo "✓ NLTK data downloaded"
fi

echo
echo "Step 4: Updating systemd service file..."
SERVICE_FILE="/etc/systemd/system/menstrual-health-bot.service"

# Check if NLTK_DATA is already in service file
if grep -q "NLTK_DATA" "$SERVICE_FILE"; then
    echo "✓ Service file already has NLTK_DATA environment variable"
else
    echo "Adding NLTK_DATA to service file..."
    # Insert NLTK_DATA after the PATH environment variable
    sed -i '/Environment="PATH=/a Environment="NLTK_DATA=/opt/menstrual_health_bot/ai_chat_bot/nltk_data"\nEnvironment="HOME=/opt/menstrual_health_bot/ai_chat_bot"' "$SERVICE_FILE"
    echo "✓ Service file updated"
fi

systemctl daemon-reload
echo "✓ Systemd reloaded"

echo
echo "Step 5: Starting service..."
systemctl start menstrual-health-bot.service
sleep 2

if systemctl is-active --quiet menstrual-health-bot.service; then
    echo "✓ Service started successfully"
else
    echo "✗ Service failed to start"
    echo
    echo "Checking logs:"
    journalctl -u menstrual-health-bot.service -n 30 --no-pager
    exit 1
fi

echo
echo "================================================"
echo "Fix Complete!"
echo "================================================"
echo
echo "Service status:"
systemctl status menstrual-health-bot.service --no-pager -l
echo
echo "To view logs: sudo journalctl -u menstrual-health-bot -f"
