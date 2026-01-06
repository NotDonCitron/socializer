#!/usr/bin/env python3
"""
FastAPI web UI for radar social media automation platform.

Provides REST API endpoints and WebSocket support for:
- Account management (CRUD operations)
- Proxy pool management
- Session monitoring
- Real-time status updates
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import websockets

from .account_pool import AccountPool, Account, AccountStatus, AccountPriority
from .proxy_manager import ProxyManager, ProxyConfig, ProxyHealth
from .session_orchestrator import SessionOrchestrator
from .engagement import EngagementManager


# Global state management
class AppState:
    """Global application state."""

    def __init__(self):
        self.account_pool = AccountPool()
        self.proxy_manager = ProxyManager()
        self.session_orchestrator = SessionOrchestrator(self.account_pool)
        self.engagement_manager = EngagementManager()
        self.websocket_clients: List[WebSocket] = []
        self.is_monitoring_active = False

    async def broadcast_update(self, event_type: str, data: Dict[str, Any]):
        """Broadcast update to all connected WebSocket clients."""
        message = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        disconnected_clients = []
        for client in self.websocket_clients:
            try:
                await client.send_json(message)
            except Exception:
                disconnected_clients.append(client)

        # Clean up disconnected clients
        for client in disconnected_clients:
            self.websocket_clients.remove(client)

app_state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting radar web UI...")

    # Start background monitoring
    asyncio.create_task(monitoring_task())

    yield

    # Shutdown
    print("🛑 Shutting down radar web UI...")

app = FastAPI(
    title="Radar Social Media Automation",
    description="Web UI for managing accounts, proxies, and sessions",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (if we add a frontend)
# app.mount("/static", StaticFiles(directory="static"), name="static")


# Background monitoring task
async def monitoring_task():
    """Background task for system monitoring."""
    while True:
        try:
            # Update account stats
            account_stats = app_state.account_pool.get_pool_stats()

            # Update proxy stats
            proxy_stats = app_state.proxy_manager.get_combined_stats()

            # Get session stats
            session_stats = {
                "active_sessions": len(app_state.session_orchestrator.get_active_sessions()),
                "platform_stats": {}  # Would need to implement
            }

            # Broadcast combined stats
            await app_state.broadcast_update("stats_update", {
                "accounts": account_stats,
                "proxies": proxy_stats,
                "sessions": session_stats
            })

            await asyncio.sleep(30)  # Update every 30 seconds

        except Exception as e:
            print(f"Monitoring error: {e}")
            await asyncio.sleep(60)


# API Routes

@app.get("/")
async def root():
    """Serve the main dashboard."""
    return FileResponse("static/index.html", media_type="text/html")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0"
    }


# Account Management API

@app.get("/api/accounts")
async def get_accounts(platform: Optional[str] = None, status: Optional[str] = None):
    """Get all accounts with optional filtering."""
    try:
        accounts = app_state.account_pool.list_accounts()

        if platform:
            accounts = [a for a in accounts if a.platform == platform]
        if status:
            accounts = [a for a in accounts if a.status.value == status]

        # Convert to dict format
        account_dicts = []
        for account in accounts:
            account_dicts.append({
                "id": account.id,
                "platform": account.platform,
                "username": account.username,
                "status": account.status.value,
                "priority": account.priority.value,
                "risk_score": account.risk_score,
                "last_used": account.last_used.isoformat() if account.last_used else None,
                "success_rate": account.calculate_success_rate(),
                "session_success_rate": account.calculate_session_success_rate(),
                "daily_usage": account.todays_usage,
                "daily_limit": account.daily_limit,
                "tags": list(account.tags)
            })

        return {"accounts": account_dicts, "count": len(account_dicts)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/accounts")
async def create_account(account_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """Create a new account."""
    try:
        required_fields = ["platform", "username"]
        for field in required_fields:
            if field not in account_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Create account object
        account_id = account_data.get("id", f"{account_data['platform']}_{account_data['username']}")
        account = Account(
            id=account_id,
            platform=account_data["platform"],
            username=account_data["username"],
            priority=AccountPriority(account_data.get("priority", "secondary")),
            status=AccountStatus(account_data.get("status", "active")),
            tags=set(account_data.get("tags", []))
        )

        # Store password if provided
        if "password" in account_data:
            account.custom_data["password"] = account_data["password"]

        app_state.account_pool.add_account(account)

        # Broadcast update
        background_tasks.add_task(
            app_state.broadcast_update,
            "account_created",
            {"account_id": account.id, "platform": account.platform}
        )

        return {"account_id": account.id, "message": "Account created successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/accounts/{account_id}")
async def get_account(account_id: str):
    """Get a specific account."""
    try:
        account = app_state.account_pool.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        return {
            "id": account.id,
            "platform": account.platform,
            "username": account.username,
            "status": account.status.value,
            "priority": account.priority.value,
            "risk_score": account.risk_score,
            "last_used": account.last_used.isoformat() if account.last_used else None,
            "created_at": account.created_at.isoformat(),
            "total_sessions": account.total_sessions,
            "successful_sessions": account.successful_sessions,
            "total_engagements": account.total_engagements,
            "successful_engagements": account.successful_engagements,
            "daily_limit": account.daily_limit,
            "hourly_limit": account.hourly_limit,
            "todays_usage": account.todays_usage,
            "last_hour_usage": account.last_hour_usage,
            "tags": list(account.tags),
            "notes": account.notes,
            "custom_data": account.custom_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/accounts/{account_id}")
async def update_account(account_id: str, updates: Dict[str, Any], background_tasks: BackgroundTasks):
    """Update an account."""
    try:
        # Convert string values to enums
        if "status" in updates:
            updates["status"] = AccountStatus(updates["status"])
        if "priority" in updates:
            updates["priority"] = AccountPriority(updates["priority"])
        if "tags" in updates:
            updates["tags"] = updates["tags"]

        success = app_state.account_pool.update_account(account_id, **updates)
        if not success:
            raise HTTPException(status_code=404, detail="Account not found")

        # Broadcast update
        background_tasks.add_task(
            app_state.broadcast_update,
            "account_updated",
            {"account_id": account_id, "updates": updates}
        )

        return {"message": "Account updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/accounts/{account_id}")
async def delete_account(account_id: str, background_tasks: BackgroundTasks):
    """Delete an account."""
    try:
        success = app_state.account_pool.remove_account(account_id)
        if not success:
            raise HTTPException(status_code=404, detail="Account not found")

        # Broadcast update
        background_tasks.add_task(
            app_state.broadcast_update,
            "account_deleted",
            {"account_id": account_id}
        )

        return {"message": "Account deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Proxy Management API

@app.get("/api/proxies")
async def get_proxies(provider: Optional[str] = None, status: Optional[str] = None):
    """Get all proxies with optional filtering."""
    try:
        proxies = app_state.proxy_manager.load_all()

        if provider:
            proxies = [p for p in proxies if p.provider == provider]
        if status:
            proxies = [p for p in proxies if p.health.value == status]

        proxy_dicts = []
        for proxy in proxies:
            proxy_dicts.append({
                "id": proxy.id,
                "host": proxy.host,
                "port": proxy.port,
                "protocol": proxy.protocol.value,
                "provider": proxy.provider,
                "country": proxy.country,
                "health": proxy.health.value,
                "success_rate": proxy.success_rate,
                "response_time_ms": proxy.response_time_ms,
                "last_used": proxy.last_used.isoformat() if proxy.last_used else None,
                "is_active": proxy.is_active
            })

        return {"proxies": proxy_dicts, "count": len(proxy_dicts)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/proxies")
async def add_proxy(proxy_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """Add a new proxy."""
    try:
        if "url" not in proxy_data:
            raise HTTPException(status_code=400, detail="Missing required field: url")

        proxy = ProxyConfig.from_url(
            proxy_data["url"],
            provider=proxy_data.get("provider")
        )

        proxy_id = app_state.proxy_manager.add_proxy(proxy)

        # Broadcast update
        background_tasks.add_task(
            app_state.broadcast_update,
            "proxy_added",
            {"proxy_id": proxy_id}
        )

        return {"proxy_id": proxy_id, "message": "Proxy added successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/proxies/{proxy_id}")
async def delete_proxy(proxy_id: str, background_tasks: BackgroundTasks):
    """Delete a proxy."""
    try:
        app_state.proxy_manager.remove_proxy(proxy_id)

        # Broadcast update
        background_tasks.add_task(
            app_state.broadcast_update,
            "proxy_deleted",
            {"proxy_id": proxy_id}
        )

        return {"message": "Proxy deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/proxies/providers")
async def get_proxy_providers():
    """Get configured proxy providers."""
    try:
        providers = app_state.proxy_manager.list_providers()
        provider_info = []

        for provider_name in providers:
            provider = app_state.proxy_manager.get_provider(provider_name)
            if provider:
                info = {
                    "name": provider_name,
                    "type": type(provider).__name__,
                    "config": {
                        "zone": getattr(provider.config, 'zone', None),
                        "country": getattr(provider.config, 'country', None)
                    }
                }
                provider_info.append(info)

        return {"providers": provider_info}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Session Management API

@app.get("/api/sessions")
async def get_sessions(platform: Optional[str] = None):
    """Get active sessions."""
    try:
        sessions = app_state.session_orchestrator.get_active_sessions()

        if platform:
            sessions = [s for s in sessions if s.get("platform") == platform]

        session_dicts = []
        for session in sessions:
            session_dicts.append({
                "session_id": session.get("session_id"),
                "account_id": session.get("account_id"),
                "platform": session.get("platform"),
                "status": session.get("status"),
                "started_at": session.get("started_at"),
                "current_url": session.get("current_url"),
                "last_activity": session.get("last_activity")
            })

        return {"sessions": session_dicts, "count": len(session_dicts)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions")
async def start_session(session_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """Start a new session."""
    try:
        required_fields = ["account_id", "platform"]
        for field in required_fields:
            if field not in session_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        session_id = app_state.session_orchestrator.start_session(
            account_id=session_data["account_id"],
            platform=session_data["platform"],
            headless=session_data.get("headless", True)
        )

        # Broadcast update
        background_tasks.add_task(
            app_state.broadcast_update,
            "session_started",
            {"session_id": session_id, "account_id": session_data["account_id"]}
        )

        return {"session_id": session_id, "message": "Session started successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sessions/{session_id}")
async def stop_session(session_id: str, background_tasks: BackgroundTasks):
    """Stop a session."""
    try:
        success = app_state.session_orchestrator.stop_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        # Broadcast update
        background_tasks.add_task(
            app_state.broadcast_update,
            "session_stopped",
            {"session_id": session_id}
        )

        return {"message": "Session stopped successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Statistics API

@app.get("/api/stats")
async def get_system_stats():
    """Get comprehensive system statistics."""
    try:
        account_stats = app_state.account_pool.get_pool_stats()
        proxy_stats = app_state.proxy_manager.get_combined_stats()
        sessions = app_state.session_orchestrator.get_active_sessions()

        return {
            "accounts": account_stats,
            "proxies": proxy_stats,
            "sessions": {
                "active_count": len(sessions),
                "sessions": sessions
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time updates

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    app_state.websocket_clients.append(websocket)

    try:
        # Send initial stats
        stats = await get_system_stats()
        await websocket.send_json({
            "event": "initial_stats",
            "timestamp": datetime.now().isoformat(),
            "data": stats
        })

        # Keep connection alive
        while True:
            # Wait for any message (ping/pong)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        if websocket in app_state.websocket_clients:
            app_state.websocket_clients.remove(websocket)


# Simple HTML dashboard (for development/testing)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Simple HTML dashboard."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Radar Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .stats { display: flex; gap: 20px; margin-bottom: 30px; }
            .stat-card { border: 1px solid #ccc; padding: 15px; border-radius: 5px; min-width: 200px; }
            .stat-card h3 { margin-top: 0; color: #333; }
            .stat-card .number { font-size: 2em; font-weight: bold; color: #007bff; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Radar Social Media Automation</h1>

        <div class="stats" id="stats">
            <div class="stat-card">
                <h3>Accounts</h3>
                <div class="number" id="account-count">-</div>
            </div>
            <div class="stat-card">
                <h3>Active Sessions</h3>
                <div class="number" id="session-count">-</div>
            </div>
            <div class="stat-card">
                <h3>Proxies</h3>
                <div class="number" id="proxy-count">-</div>
            </div>
        </div>

        <h2>Recent Activity</h2>
        <div id="activity">Loading...</div>

        <script>
            // WebSocket connection for real-time updates
            const ws = new WebSocket('ws://localhost:8000/ws');

            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                console.log('Received:', message);

                if (message.event === 'initial_stats' || message.event === 'stats_update') {
                    updateStats(message.data);
                } else if (message.event === 'account_created') {
                    addActivity(`Account ${message.data.account_id} created`);
                } else if (message.event === 'session_started') {
                    addActivity(`Session ${message.data.session_id} started`);
                }
            };

            ws.onopen = function() {
                console.log('WebSocket connected');
            };

            function updateStats(data) {
                document.getElementById('account-count').textContent = data.accounts.total_accounts || 0;
                document.getElementById('session-count').textContent = data.sessions.active_count || 0;
                document.getElementById('proxy-count').textContent = data.proxies.total_proxies || 0;
            }

            function addActivity(text) {
                const activityDiv = document.getElementById('activity');
                const timestamp = new Date().toLocaleTimeString();
                activityDiv.innerHTML = `<div>${timestamp}: ${text}</div>` + activityDiv.innerHTML;
            }

            // Refresh stats every 30 seconds
            setInterval(() => {
                fetch('/api/stats')
                    .then(response => response.json())
                    .then(data => updateStats(data))
                    .catch(error => console.error('Error fetching stats:', error));
            }, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


def main():
    """Run the web UI server."""
    import argparse

    parser = argparse.ArgumentParser(description='Radar Web UI')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')

    args = parser.parse_args()

    print(f"🌐 Starting web UI on http://{args.host}:{args.port}")
    print(f"📊 Dashboard: http://{args.host}:{args.port}/dashboard")
    print(f"📚 API docs: http://{args.host}:{args.port}/docs")

    uvicorn.run(
        "radar.web_ui:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()