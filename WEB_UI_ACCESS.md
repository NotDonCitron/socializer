# 🌐 Radar Web UI - Access Guide

## ✅ Server Status
Your radar web UI server is **RUNNING** on port 8000!

## 🔗 How to Access

### Option 1: Clear Browser Cache (Recommended)
If you see your old website, clear your browser cache:

**In Chrome/Chromium/Edge:**
1. Press `Ctrl + Shift + Delete`
2. Select "Cached images and files"
3. Click "Clear data"
4. Visit: http://localhost:8000/dashboard

**Or use Hard Refresh:**
- Press `Ctrl + Shift + R` (Linux/Windows)
- Or `Ctrl + F5`

### Option 2: Direct URL Access
Visit these URLs directly (they bypass cached homepage):

- **Dashboard**: http://localhost:8000/dashboard
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

### Option 3: Use Incognito/Private Mode
Open an incognito window:
- `Ctrl + Shift + N` (Chrome)
- Then visit: http://localhost:8000/dashboard

### Option 4: Use Different Port
If you want to keep your old site AND run the new web UI:

```bash
# Stop current server (if running)
pkill -f "radar.web_ui"

# Start on a different port (e.g., 8080)
python -m radar.web_ui --host 0.0.0.0 --port 8080
```

Then access at: http://localhost:8080/dashboard

---

## 📋 Available Endpoints

### Web Pages
- `/` or `/dashboard` - Main dashboard
- `/docs` - Interactive API documentation (Swagger UI)

### API Endpoints

**Health & Stats:**
- `GET /api/health` - Health check
- `GET /api/stats` - System statistics

**Accounts:**
- `GET /api/accounts` - List all accounts
- `POST /api/accounts` - Create new account
- `GET /api/accounts/{id}` - Get account details
- `PUT /api/accounts/{id}` - Update account
- `DELETE /api/accounts/{id}` - Delete account

**Proxies:**
- `GET /api/proxies` - List all proxies
- `POST /api/proxies` - Add new proxy
- `DELETE /api/proxies/{id}` - Delete proxy
- `GET /api/proxies/providers` - List providers

**Sessions:**
- `GET /api/sessions` - List active sessions
- `POST /api/sessions` - Start new session
- `DELETE /api/sessions/{id}` - Stop session

**WebSocket:**
- `WS /ws` - Real-time updates

---

## 🧪 Quick Test

Test if the server is responding:

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-06T04:24:00",
  "version": "0.1.0"
}
```

---

## 🔧 Troubleshooting

### Still seeing old website?
1. Check you're using the correct URL: `/dashboard` not just `/`
2. Clear ALL browser data for localhost
3. Try a different browser
4. Use incognito mode

### Server not responding?
Check if it's running:
```bash
ps aux | grep radar.web_ui
```

Restart server:
```bash
python -m radar.web_ui --host 0.0.0.0 --port 8000
```

### Want to use a different port?
```bash
python -m radar.web_ui --host 0.0.0.0 --port 8080
```

---

## 📊 What You Should See

The dashboard includes:
- **4 stat cards**: Accounts, Active Sessions, Proxies, Success Rate
- **Recent Activity feed**: Live updates of all actions
- **System Status panel**: Health indicators
- **5 navigation tabs**: Dashboard, Accounts, Proxies, Sessions, Settings

---

## 🆘 Need Help?

1. Check the terminal where you started the server for errors
2. Visit `/docs` for interactive API testing
3. Check the API_ENDPOINTS.md file for detailed API documentation