# Systemd Service Setup Guide

This guide explains how to set up the Menstrual Health Chatbot as a systemd service on Linux.

## Prerequisites

- Linux system with systemd (Ubuntu, Debian, CentOS, etc.)
- Python 3.7+ installed
- Root or sudo access

## Step 1: Deploy the Application

1. Copy your application to the server:
```bash
# Create application directory
sudo mkdir -p /opt/menstrual_health_bot

# Copy files to server (adjust the source path as needed)
sudo cp -r /path/to/ai_chat_bot /opt/menstrual_health_bot/

# Set ownership (replace 'www-data' with your preferred user)
sudo chown -R www-data:www-data /opt/menstrual_health_bot
```

## Step 2: Set Up Python Virtual Environment

```bash
# Navigate to application directory
cd /opt/menstrual_health_bot/ai_chat_bot

# Create virtual environment
sudo -u www-data python3 -m venv venv

# Activate virtual environment
sudo -u www-data venv/bin/pip install --upgrade pip

# Install dependencies
sudo -u www-data venv/bin/pip install -r requirements.txt
```

## Step 3: Configure Environment Variables

```bash
# Create or edit the .env file
sudo nano /opt/menstrual_health_bot/ai_chat_bot/.env
```

Ensure your `.env` file contains necessary variables like:
```
PORT=80
LOGGING_LEVEL=INFO
LOGGING_FILE=/var/log/menstrual_health_bot/chatbot.log
# Add other environment variables as needed
```

## Step 4: Create Log Directory

```bash
# Create log directory
sudo mkdir -p /var/log/menstrual_health_bot

# Set ownership
sudo chown www-data:www-data /var/log/menstrual_health_bot
```

## Step 5: Install the Systemd Service

```bash
# Copy the service file to systemd directory
sudo cp /opt/menstrual_health_bot/ai_chat_bot/menstrual-health-bot.service /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable menstrual-health-bot.service
```

## Step 6: Start the Service

```bash
# Start the service
sudo systemctl start menstrual-health-bot.service

# Check status
sudo systemctl status menstrual-health-bot.service
```

## Managing the Service

### Check Service Status
```bash
sudo systemctl status menstrual-health-bot.service
```

### Start Service
```bash
sudo systemctl start menstrual-health-bot.service
```

### Stop Service
```bash
sudo systemctl stop menstrual-health-bot.service
```

### Restart Service
```bash
sudo systemctl restart menstrual-health-bot.service
```

### View Logs
```bash
# View recent logs
sudo journalctl -u menstrual-health-bot.service -n 100

# Follow logs in real-time
sudo journalctl -u menstrual-health-bot.service -f

# View logs from today
sudo journalctl -u menstrual-health-bot.service --since today
```

### Disable Service (prevent auto-start on boot)
```bash
sudo systemctl disable menstrual-health-bot.service
```

## Troubleshooting

### Service Won't Start

1. Check the service status:
```bash
sudo systemctl status menstrual-health-bot.service
```

2. View detailed logs:
```bash
sudo journalctl -u menstrual-health-bot.service -n 50 --no-pager
```

3. Verify file permissions:
```bash
ls -la /opt/menstrual_health_bot/ai_chat_bot
```

4. Test running manually:
```bash
sudo -u www-data /opt/menstrual_health_bot/ai_chat_bot/venv/bin/waitress-serve --host=0.0.0.0 --port=8000 index:app
```

### Port Permission Issues

If using port 80 (requires root privileges):

**Option 1: Use a reverse proxy (Recommended)**
- Set PORT=8000 in .env
- Use Nginx or Apache as a reverse proxy to forward port 80 to 8000

**Option 2: Grant port binding capability**
```bash
sudo setcap CAP_NET_BIND_SERVICE=+eip /opt/menstrual_health_bot/ai_chat_bot/venv/bin/python3
```

### Update the Application

When you update the code:
```bash
# Copy new files
sudo cp -r /path/to/updated/files/* /opt/menstrual_health_bot/ai_chat_bot/

# Set ownership
sudo chown -R www-data:www-data /opt/menstrual_health_bot/ai_chat_bot

# Restart service
sudo systemctl restart menstrual-health-bot.service
```

## Configuration Customization

### Change User/Group

Edit the service file if you want to run as a different user:
```bash
sudo nano /etc/systemd/system/menstrual-health-bot.service
```

Change these lines:
```
User=your_username
Group=your_groupname
```

Then reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart menstrual-health-bot.service
```

### Change Port

Edit the `.env` file:
```bash
sudo nano /opt/menstrual_health_bot/ai_chat_bot/.env
```

Change:
```
PORT=8000
```

Then restart:
```bash
sudo systemctl restart menstrual-health-bot.service
```

## Nginx Reverse Proxy (Recommended for Production)

Install Nginx:
```bash
sudo apt update
sudo apt install nginx
```

Create Nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/menstrual-health-bot
```

Add:
```nginx
server {
    listen 80;
    server_name your_domain.com;  # Replace with your domain

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/menstrual-health-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Security Considerations

1. **Use a non-root user**: The service file uses `www-data`, which is recommended
2. **Set proper file permissions**: Ensure only the service user can read sensitive files
3. **Use environment variables**: Keep sensitive data in `.env` file with restricted permissions:
   ```bash
   sudo chmod 600 /opt/menstrual_health_bot/ai_chat_bot/.env
   ```
4. **Enable firewall**: Only allow necessary ports
5. **Use HTTPS**: Set up SSL/TLS certificates (Let's Encrypt) with Nginx

## Additional Notes

- The service automatically restarts if it crashes (`Restart=always`)
- Logs are stored in systemd journal and can be viewed with `journalctl`
- Database migrations run automatically before each start
- The service starts automatically on system boot
