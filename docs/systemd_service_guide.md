# Systemd Service Installation Guide

This guide explains how to set up the AI Chatbot as a systemd service on Linux systems.

## Prerequisites

1. Linux system with systemd (Ubuntu 16.04+, Debian 8+, CentOS 7+, etc.)
2. Python 3.8 or higher installed
3. The chatbot application deployed to the server
4. Root or sudo access

## Installation Steps

### 1. Deploy Application

Deploy your application to a suitable directory (e.g., `/var/www/ai_chat_bot`):

```bash
# Create application directory
sudo mkdir -p /var/www/ai_chat_bot

# Copy application files
sudo cp -r /path/to/your/app/* /var/www/ai_chat_bot/

# Set ownership (adjust user as needed)
sudo chown -R www-data:www-data /var/www/ai_chat_bot
```

### 2. Set Up Virtual Environment

```bash
cd /var/www/ai_chat_bot

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Deactivate
deactivate
```

### 3. Create Log Directory

```bash
sudo mkdir -p /var/log/ai-chatbot
sudo chown www-data:www-data /var/log/ai-chatbot
```

### 4. Configure Service File

Edit `ai-chatbot.service` and adjust these settings for your environment:

- **User/Group**: Change `www-data` to your preferred user (default is fine for web servers)
- **WorkingDirectory**: Update `/var/www/ai_chat_bot` to your actual installation path
- **Port**: Change `--bind 0.0.0.0:80` if you want a different port (80 requires root privileges)
- **Workers**: Adjust `--workers 4` based on your server's CPU cores (recommended: 2-4 × CPU cores)

### 5. Install Service File

```bash
# Copy service file to systemd directory
sudo cp ai-chatbot.service /etc/systemd/system/

# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable ai-chatbot.service
```

### 6. Start the Service

```bash
# Start the service
sudo systemctl start ai-chatbot.service

# Check status
sudo systemctl status ai-chatbot.service
```

## Service Management Commands

### Check Service Status
```bash
sudo systemctl status ai-chatbot.service
```

### View Logs
```bash
# View recent logs
sudo journalctl -u ai-chatbot.service -n 50

# Follow logs in real-time
sudo journalctl -u ai-chatbot.service -f

# View application logs
sudo tail -f /var/log/ai-chatbot/access.log
sudo tail -f /var/log/ai-chatbot/error.log
```

### Start/Stop/Restart Service
```bash
# Start
sudo systemctl start ai-chatbot.service

# Stop
sudo systemctl stop ai-chatbot.service

# Restart
sudo systemctl restart ai-chatbot.service

# Reload (graceful restart)
sudo systemctl reload ai-chatbot.service
```

### Enable/Disable Auto-start
```bash
# Enable (start on boot)
sudo systemctl enable ai-chatbot.service

# Disable (don't start on boot)
sudo systemctl disable ai-chatbot.service
```

## Using Non-Privileged Port

If you don't want to run on port 80 (which requires root), use a port like 8000:

1. Edit the service file:
   ```bash
   sudo nano /etc/systemd/system/ai-chatbot.service
   ```

2. Change the ExecStart line:
   ```
   ExecStart=/var/www/ai_chat_bot/.venv/bin/gunicorn index:app --bind 0.0.0.0:8000 --workers 4 ...
   ```

3. Reload and restart:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart ai-chatbot.service
   ```

4. Set up nginx or Apache as a reverse proxy to handle port 80/443 and forward to port 8000.

## Nginx Reverse Proxy Configuration (Optional)

If using a non-privileged port, set up nginx as a reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### Service Won't Start

1. Check service status for errors:
   ```bash
   sudo systemctl status ai-chatbot.service -l
   ```

2. Check system logs:
   ```bash
   sudo journalctl -xe -u ai-chatbot.service
   ```

3. Verify file paths in service file are correct
4. Check file permissions
5. Ensure virtual environment is set up correctly

### Permission Errors

```bash
# Fix ownership
sudo chown -R www-data:www-data /var/www/ai_chat_bot

# Fix permissions
sudo chmod -R 755 /var/www/ai_chat_bot
```

### Port Already in Use

If port 80 is already in use:
- Use a different port (edit service file)
- Or stop the conflicting service:
  ```bash
  sudo netstat -tulpn | grep :80  # Find what's using port 80
  ```

### Database Locked Errors

If you get database locked errors with SQLite:
- Consider using PostgreSQL or MySQL for production
- Or ensure only one worker process: `--workers 1`
- Enable WAL mode in SQLite (already done in the code)

## Environment Variables

If you need to set environment variables (API keys, etc.), add them to the service file:

```ini
[Service]
Environment="TOGETHER_API_KEY=your_api_key_here"
Environment="WHATSAPP_API_TOKEN=your_token_here"
Environment="PORT=80"
```

Or use an environment file:

```ini
[Service]
EnvironmentFile=/var/www/ai_chat_bot/.env
```

## Security Best Practices

1. **Don't run as root**: Use a dedicated user like `www-data`
2. **Keep secrets secure**: Use environment variables or secret management
3. **Enable firewall**: Only allow necessary ports
4. **Use HTTPS**: Set up SSL/TLS with Let's Encrypt
5. **Regular updates**: Keep dependencies and system packages updated
6. **Monitor logs**: Set up log rotation and monitoring

## Log Rotation

Create `/etc/logrotate.d/ai-chatbot`:

```
/var/log/ai-chatbot/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload ai-chatbot.service > /dev/null 2>&1 || true
    endscript
}
```

## Production Checklist

- [ ] Deploy application to `/var/www/ai_chat_bot` or similar
- [ ] Set up virtual environment and install dependencies
- [ ] Create log directories with proper permissions
- [ ] Configure service file with correct paths and settings
- [ ] Install and enable systemd service
- [ ] Set up nginx/Apache reverse proxy (if using non-privileged port)
- [ ] Configure firewall rules
- [ ] Set up SSL/TLS certificates
- [ ] Configure environment variables securely
- [ ] Set up log rotation
- [ ] Test service start/stop/restart
- [ ] Verify application is accessible
- [ ] Set up monitoring and alerting

## Support

For issues specific to the chatbot application, refer to the main README.md or create an issue on GitHub.
