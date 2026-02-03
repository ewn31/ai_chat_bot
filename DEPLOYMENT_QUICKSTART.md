# Quick Start: Deploy with Systemd

This is a quick reference guide for deploying the Menstrual Health Chatbot as a systemd service on Linux.

## Prerequisites

- Ubuntu/Debian Linux server (or similar)
- Python 3.7+
- Root/sudo access
- Your server's IP address or domain name

## Quick Deployment (3 Steps)

### 1. Transfer Files to Linux Server

From your local machine:
```bash
# Using scp
scp -r ai_chat_bot/ user@your-server:/tmp/

# Or using rsync
rsync -avz ai_chat_bot/ user@your-server:/tmp/ai_chat_bot/
```

### 2. Run Deployment Script

On your Linux server:
```bash
# Navigate to the uploaded directory
cd /tmp/ai_chat_bot

# Make deployment script executable
chmod +x deploy.sh

# Run deployment
sudo ./deploy.sh
```

### 3. Configure and Start

```bash
# Edit configuration
sudo nano /opt/menstrual_health_bot/ai_chat_bot/.env

# Start the service
sudo systemctl start menstrual-health-bot

# Verify it's running
sudo systemctl status menstrual-health-bot
```

Done! Your bot is now running and will auto-start on system reboot.

## Common Commands

```bash
# View live logs
sudo journalctl -u menstrual-health-bot -f

# Restart service
sudo systemctl restart menstrual-health-bot

# Stop service
sudo systemctl stop menstrual-health-bot

# Check service status
sudo systemctl status menstrual-health-bot
```

## Updating the Application

When you make code changes:

```bash
# 1. Transfer updated files to server
rsync -avz ai_chat_bot/ user@your-server:/tmp/ai_chat_bot/

# 2. Run update script on server
cd /tmp/ai_chat_bot
sudo ./update.sh
```

The update script automatically:
- Creates a backup
- Updates files
- Installs new dependencies
- Runs migrations
- Restarts the service

## Production Setup (Recommended)

For production environments, add these steps:

### 1. Set Up Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt update && sudo apt install nginx -y

# Create Nginx config
sudo nano /etc/nginx/sites-available/menstrual-health-bot
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable and start:
```bash
sudo ln -s /etc/nginx/sites-available/menstrual-health-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 2. Add SSL Certificate (HTTPS)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com
```

### 3. Configure Firewall

```bash
# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Troubleshooting

### Service won't start
```bash
# Check detailed logs
sudo journalctl -u menstrual-health-bot -n 50

# Test manually
sudo -u www-data /opt/menstrual_health_bot/ai_chat_bot/venv/bin/python /opt/menstrual_health_bot/ai_chat_bot/index.py
```

### Port already in use
```bash
# Check what's using the port
sudo lsof -i :8000

# Change port in .env
sudo nano /opt/menstrual_health_bot/ai_chat_bot/.env
# Set: PORT=8001

# Restart service
sudo systemctl restart menstrual-health-bot
```

### Permission errors
```bash
# Fix ownership
sudo chown -R www-data:www-data /opt/menstrual_health_bot

# Fix .env permissions
sudo chmod 600 /opt/menstrual_health_bot/ai_chat_bot/.env
```

## File Locations

- **Application**: `/opt/menstrual_health_bot/ai_chat_bot/`
- **Service file**: `/etc/systemd/system/menstrual-health-bot.service`
- **Logs**: `sudo journalctl -u menstrual-health-bot`
- **App logs**: `/var/log/menstrual_health_bot/chatbot.log`
- **Config**: `/opt/menstrual_health_bot/ai_chat_bot/.env`

## Architecture

```
Internet
    ↓
Nginx (Port 80/443)
    ↓
Waitress WSGI Server (Port 8000)
    ↓
Flask Application
    ↓
SQLite Database
```

## Need More Help?

- Detailed setup: See `SYSTEMD_SETUP.md`
- Service management: `sudo systemctl status menstrual-health-bot`
- Logs: `sudo journalctl -u menstrual-health-bot -f`

## Security Checklist

- [ ] Changed default .env values
- [ ] Set up firewall (ufw)
- [ ] Configured HTTPS/SSL
- [ ] Restricted .env file permissions (600)
- [ ] Running as non-root user (www-data)
- [ ] Set up log rotation
- [ ] Regular backups enabled

For questions or issues, check the logs first!
