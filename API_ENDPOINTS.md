# Radar Web UI - API Endpoints Reference

Base URL: `http://localhost:8000`

## 📊 Health & Status

### GET /api/health
Health check endpoint
```bash
curl http://localhost:8000/api/health
```

### GET /api/stats
Get comprehensive system statistics (accounts, proxies, sessions)
```bash
curl http://localhost:8000/api/stats
```

---

## 👥 Account Management

### GET /api/accounts
List all accounts with optional filtering
```bash
# Get all accounts
curl http://localhost:8000/api/accounts

# Filter by platform
curl http://localhost:8000/api/accounts?platform=tiktok

# Filter by status
curl http://localhost:8000/api/accounts?status=active
```

### POST /api/accounts
Create a new account
```bash
curl -X POST http://localhost:8000/api/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "tiktok",
    "username": "myuser123",
    "password": "mypassword",
    "priority": "primary",
    "tags": ["production", "main"]
  }'
```

### GET /api/accounts/{account_id}
Get specific account details
```bash
curl http://localhost:8000/api/accounts/tiktok_myuser123
```

### PUT /api/accounts/{account_id}
Update an account
```bash
curl -X PUT http://localhost:8000/api/accounts/tiktok_myuser123 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "active",
    "priority": "primary",
    "notes": "Main production account"
  }'
```

### DELETE /api/accounts/{account_id}
Delete an account
```bash
curl -X DELETE http://localhost:8000/api/accounts/tiktok_myuser123
```

---

## 🌐 Proxy Management

### GET /api/proxies
List all proxies with optional filtering
```bash
# Get all proxies
curl http://localhost:8000/api/proxies

# Filter by provider
curl http://localhost:8000/api/proxies?provider=brightdata

# Filter by health status
curl http://localhost:8000/api/proxies?status=healthy
```

### POST /api/proxies
Add a new proxy
```bash
curl -X POST http://localhost:8000/api/proxies \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://user:pass@proxy.example.com:8080",
    "provider": "brightdata"
  }'
```

### DELETE /api/proxies/{proxy_id}
Delete a proxy
```bash
curl -X DELETE http://localhost:8000/api/proxies/proxy_abc123
```

### GET /api/proxies/providers
List configured proxy providers
```bash
curl http://localhost:8000/api/proxies/providers
```

---

## 💻 Session Management

### GET /api/sessions
List active sessions with optional filtering
```bash
# Get all sessions
curl http://localhost:8000/api/sessions

# Filter by platform
curl http://localhost:8000/api/sessions?platform=instagram
```

### POST /api/sessions
Start a new browser session
```bash
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "tiktok_myuser123",
    "platform": "tiktok",
    "headless": true
  }'
```

### DELETE /api/sessions/{session_id}
Stop a session
```bash
curl -X DELETE http://localhost:8000/api/sessions/session_xyz789
```

---

## 🔌 WebSocket Endpoint

### WS /ws
WebSocket connection for real-time updates
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
  const message = JSON.parse(event.data);
  console.log('Event:', message.event);
  console.log('Data:', message.data);
};

// Events you'll receive:
// - stats_update: Regular stats updates
// - account_created: New account added
// - account_updated: Account modified
// - account_deleted: Account removed
// - proxy_added: New proxy added
// - proxy_deleted: Proxy removed
// - session_started: Session started
// - session_stopped: Session stopped
```

---

## 📄 Web Pages

### GET /
Main dashboard (redirects to static/index.html)

### GET /dashboard
Simple HTML dashboard for development/testing

### GET /docs
Auto-generated OpenAPI/Swagger documentation (interactive API explorer)

---

## Summary of HTTP Methods Used

- **GET**: Retrieve data (accounts, proxies, sessions, stats)
- **POST**: Create new resources (accounts, proxies, sessions)
- **PUT**: Update existing resources (accounts)
- **DELETE**: Remove resources (accounts, proxies, sessions)
- **WebSocket**: Real-time bidirectional communication

---

## Quick Start

1. Start the server:
```bash
python -m radar.cli webui --port 8000
```

2. Access the dashboard:
```
http://localhost:8000/dashboard
```

3. View API docs:
```
http://localhost:8000/docs
```

4. Test an endpoint:
```bash
curl http://localhost:8000/api/health
```