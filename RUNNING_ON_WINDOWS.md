# Running the Server on Windows

## Why Not Gunicorn?

Gunicorn **does not work on Windows** because it uses Unix-specific modules like `fcntl`. 

**Error you'll see with Gunicorn on Windows:**
```
ModuleNotFoundError: No module named 'fcntl'
```

## ✅ Solution: Use Waitress

Waitress is a production-ready WSGI server that works perfectly on Windows.

---

## Installation

Waitress is already in `requirements.txt`. If not installed:

```powershell
pip install waitress
```

---

## Running the Server

### **Option 1: Manual Command** ⭐ Recommended

```powershell
# Activate virtual environment first
.\venv\Scripts\Activate

# Run the server
waitress-serve --host=0.0.0.0 --port=80 index:app
```

### **Option 2: Using Batch Script** (CMD)

```cmd
start_server.bat
```

### **Option 3: Using PowerShell Script**

```powershell
.\start_server.ps1
```

---

## Configuration Options

### Basic (Development)
```powershell
waitress-serve --host=0.0.0.0 --port=5000 index:app
```

### Production with Options
```powershell
waitress-serve --host=0.0.0.0 --port=80 --threads=4 --channel-timeout=60 index:app
```

**Parameters:**
- `--host=0.0.0.0` - Listen on all network interfaces
- `--port=80` - Port to listen on (change if needed)
- `--threads=4` - Number of worker threads (default: 4)
- `--channel-timeout=60` - Connection timeout in seconds
- `index:app` - Module:app_instance (index.py contains `app = Flask(__name__)`)

---

## Port 80 Considerations

### ⚠️ Administrator Required

Port 80 typically requires **administrator privileges** on Windows.

**If you get a permission error:**

1. **Option A:** Run PowerShell/CMD as Administrator
   - Right-click PowerShell/CMD
   - Select "Run as Administrator"
   - Run the command again

2. **Option B:** Use a different port
   ```powershell
   waitress-serve --host=0.0.0.0 --port=5000 index:app
   ```
   
   Then update `.env`:
   ```properties
   PORT=5000
   ```

---

## Checking if Server is Running

### Test Locally
```powershell
# In browser or PowerShell
Invoke-WebRequest -Uri http://localhost:80
```

Expected response: `Bot is running`

### Test from Network
```powershell
# Replace <your-ip> with your machine's IP address
Invoke-WebRequest -Uri http://<your-ip>:80
```

---

## Server Logs

Waitress will output logs to the console:

```
Serving on http://0.0.0.0:80
127.0.0.1 - - [24/Oct/2025:10:30:45 +0000] "POST /hook/messages HTTP/1.1" 200 2 "-" "PostmanRuntime/7.32.2"
```

---

## Stopping the Server

Press `Ctrl+C` in the terminal where Waitress is running.

---

## Comparison: Waitress vs Gunicorn

| Feature | Waitress | Gunicorn |
|---------|----------|----------|
| Windows Support | ✅ Yes | ❌ No |
| Linux Support | ✅ Yes | ✅ Yes |
| Production Ready | ✅ Yes | ✅ Yes |
| Performance | Good | Excellent |
| Configuration | Simple | More options |
| Worker Model | Thread-based | Process-based |

**For Windows:** Use Waitress  
**For Linux/Production:** Use Gunicorn or Waitress

---

## Production Deployment on Windows

### Recommended Setup

1. **Use Waitress** (already configured)
2. **Run as Windows Service** (optional, for auto-start)
3. **Use Reverse Proxy** (IIS or nginx)
4. **Enable HTTPS** (SSL/TLS certificates)

### Windows Service Setup (Optional)

You can use **NSSM** (Non-Sucking Service Manager) to run your app as a Windows service:

```powershell
# Install NSSM (https://nssm.cc/download)
# Then:
nssm install ChatbotService "C:\path\to\venv\Scripts\waitress-serve.exe" "--host=0.0.0.0 --port=80 index:app"
nssm start ChatbotService
```

---

## Troubleshooting

### Issue: `waitress-serve: command not found`

**Solution:**
```powershell
# Check if Waitress is installed
pip show waitress

# If not, install it
pip install waitress

# If installed but not in PATH, use full path
python -m waitress --host=0.0.0.0 --port=80 index:app
```

### Issue: Port already in use

**Error:**
```
OSError: [WinError 10048] Only one usage of each socket address is normally permitted
```

**Solution:**
```powershell
# Find what's using the port
netstat -ano | findstr :80

# Kill the process (replace <PID> with actual process ID)
taskkill /PID <PID> /F

# Or use a different port
waitress-serve --host=0.0.0.0 --port=5000 index:app
```

### Issue: Permission denied on port 80

**Solution:** Run PowerShell/CMD as Administrator or use port 5000

---

## Environment Variables

Your `.env` file is loaded by `index.py`:

```properties
MODE=no_counsellor
API_TOKEN=WMyMhrLCKZddmPpS8eVcnlixG3jCRqSo
API_URL=https://gate.whapi.cloud
PORT=80
LOGGING_LEVEL=DEBUG
```

These are automatically loaded by `load_dotenv()` in `index.py`.

---

## Quick Reference

```powershell
# Start server (basic)
waitress-serve --host=0.0.0.0 --port=80 index:app

# Start server (production)
waitress-serve --host=0.0.0.0 --port=80 --threads=4 --channel-timeout=60 index:app

# Start server (development, port 5000)
waitress-serve --host=127.0.0.1 --port=5000 index:app

# Test server
curl http://localhost:80

# Stop server
Ctrl+C
```

---

## Next Steps

1. ✅ Waitress installed
2. ✅ Startup scripts created
3. 🔄 Test the server: `waitress-serve --host=0.0.0.0 --port=80 index:app`
4. 🔄 Configure webhook in WhatsApp API dashboard
5. 🔄 Test webhook endpoint: `POST http://your-server/hook/messages`

---

**Your chatbot is now ready to run on Windows! 🚀**
