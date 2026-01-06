"""
Proxy management module for multi-account social media automation.

Provides proxy configuration, rotation, health monitoring, and account-proxy binding.
Inspired by Dolphin Anty's approach to maintaining consistent proxy identities per account.

Enhanced with provider integrations for BrightData, SmartProxy, and Oxylabs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any
import json
import os
import random
import sqlite3
import asyncio
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor


class ProxyProtocol(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS5 = "socks5"


class ProxyHealth(Enum):
    HEALTHY = "healthy"
    SLOW = "slow"
    BLOCKED = "blocked"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class ProxyConfig:
    """Configuration for a single proxy server."""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: ProxyProtocol = ProxyProtocol.HTTP
    country: Optional[str] = None
    provider: Optional[str] = None
    last_used: datetime = field(default_factory=datetime.now)
    success_rate: float = 1.0
    is_active: bool = True
    id: Optional[str] = None
    response_time_ms: Optional[float] = None
    health: ProxyHealth = ProxyHealth.UNKNOWN

    def to_playwright_format(self) -> Dict[str, str]:
        """Convert to Playwright proxy configuration format."""
        proxy_dict = {
            "server": f"{self.protocol.value}://{self.host}:{self.port}"
        }
        if self.username and self.password:
            proxy_dict["username"] = self.username
            proxy_dict["password"] = self.password
        return proxy_dict

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage."""
        return {
            "id": self.id,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "protocol": self.protocol.value,
            "country": self.country,
            "provider": self.provider,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "success_rate": self.success_rate,
            "is_active": self.is_active,
            "response_time_ms": self.response_time_ms,
            "health": self.health.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxyConfig":
        """Deserialize from dictionary."""
        return cls(
            id=data.get("id"),
            host=data["host"],
            port=data["port"],
            username=data.get("username"),
            password=data.get("password"),
            protocol=ProxyProtocol(data.get("protocol", "http")),
            country=data.get("country"),
            provider=data.get("provider"),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else datetime.now(),
            success_rate=data.get("success_rate", 1.0),
            is_active=data.get("is_active", True),
            response_time_ms=data.get("response_time_ms"),
            health=ProxyHealth(data.get("health", "unknown"))
        )

    @classmethod
    def from_url(cls, url: str, provider: Optional[str] = None) -> "ProxyConfig":
        """
        Parse proxy from URL format.
        
        Supports formats:
        - protocol://host:port
        - protocol://user:pass@host:port
        - host:port (assumes http)
        - user:pass@host:port (assumes http)
        """
        import re

        # Remove protocol prefix if present
        protocol = ProxyProtocol.HTTP
        if url.startswith("socks5://"):
            protocol = ProxyProtocol.SOCKS5
            url = url[9:]
        elif url.startswith("https://"):
            protocol = ProxyProtocol.HTTPS
            url = url[8:]
        elif url.startswith("http://"):
            protocol = ProxyProtocol.HTTP
            url = url[7:]

        # Parse credentials if present
        username = None
        password = None
        if "@" in url:
            creds, hostport = url.rsplit("@", 1)
            if ":" in creds:
                username, password = creds.split(":", 1)
            url = hostport

        # Parse host and port
        if ":" in url:
            host, port_str = url.rsplit(":", 1)
            port = int(port_str)
        else:
            host = url
            port = 8080  # Default port

        return cls(
            host=host,
            port=port,
            username=username,
            password=password,
            protocol=protocol,
            provider=provider
        )


class ProxyManager:
    """
    Manages proxy pool with rotation, health tracking, and account binding.
    
    Features:
    - Load proxies from file, database, or API providers
    - Bind proxies to specific accounts for consistent identity
    - Health monitoring and automatic failover
    - Smart rotation based on success rate and usage
    """

    def __init__(self, db_path: str = "data/radar.sqlite"):
        """
        Initialize proxy manager.

        Args:
            db_path: Path to SQLite database for proxy storage
        """
        self.db_path = db_path
        self._proxies: Dict[str, ProxyConfig] = {}  # id -> ProxyConfig
        self._account_bindings: Dict[str, str] = {}  # account_id -> proxy_id

        # Provider management
        self._providers: Dict[str, Any] = {}  # provider_name -> provider_instance
        self._provider_configs: Dict[str, Any] = {}  # provider_name -> config
        self._provider_lock = threading.Lock()  # Thread safety for provider operations
        self._health_monitor_thread: Optional[threading.Thread] = None
        self._health_monitor_running = False
        self._health_check_interval = 300  # 5 minutes

        self._init_database()

    def _init_database(self):
        """Initialize SQLite tables for proxy storage."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS proxies (
                    id TEXT PRIMARY KEY,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    username TEXT,
                    password TEXT,
                    protocol TEXT DEFAULT 'http',
                    country TEXT,
                    provider TEXT,
                    last_used TEXT,
                    success_rate REAL DEFAULT 1.0,
                    is_active INTEGER DEFAULT 1,
                    response_time_ms REAL,
                    health TEXT DEFAULT 'unknown',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS proxy_account_bindings (
                    account_id TEXT PRIMARY KEY,
                    proxy_id TEXT NOT NULL,
                    bound_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (proxy_id) REFERENCES proxies(id)
                )
            """)
            
            conn.commit()

    def _generate_id(self) -> str:
        """Generate a unique proxy ID."""
        import uuid
        return str(uuid.uuid4())[:8]

    def add_proxy(self, proxy: ProxyConfig) -> str:
        """
        Add a proxy to the pool.
        
        Args:
            proxy: ProxyConfig to add
            
        Returns:
            Proxy ID
        """
        if not proxy.id:
            proxy.id = self._generate_id()
        
        self._proxies[proxy.id] = proxy
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO proxies 
                (id, host, port, username, password, protocol, country, provider, 
                 last_used, success_rate, is_active, response_time_ms, health)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proxy.id, proxy.host, proxy.port, proxy.username, proxy.password,
                proxy.protocol.value, proxy.country, proxy.provider,
                proxy.last_used.isoformat() if proxy.last_used else None,
                proxy.success_rate, 1 if proxy.is_active else 0,
                proxy.response_time_ms, proxy.health.value
            ))
            conn.commit()
        
        return proxy.id

    def remove_proxy(self, proxy_id: str):
        """Remove a proxy from the pool."""
        self._proxies.pop(proxy_id, None)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
            conn.execute("DELETE FROM proxy_account_bindings WHERE proxy_id = ?", (proxy_id,))
            conn.commit()

    def get_proxy(self, proxy_id: str) -> Optional[ProxyConfig]:
        """Get a specific proxy by ID."""
        if proxy_id in self._proxies:
            return self._proxies[proxy_id]
        
        # Try to load from database
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM proxies WHERE id = ?", (proxy_id,)).fetchone()
            if row:
                proxy = self._row_to_proxy(row)
                self._proxies[proxy_id] = proxy
                return proxy
        
        return None

    def _row_to_proxy(self, row: sqlite3.Row) -> ProxyConfig:
        """Convert database row to ProxyConfig."""
        return ProxyConfig(
            id=row["id"],
            host=row["host"],
            port=row["port"],
            username=row["username"],
            password=row["password"],
            protocol=ProxyProtocol(row["protocol"]) if row["protocol"] else ProxyProtocol.HTTP,
            country=row["country"],
            provider=row["provider"],
            last_used=datetime.fromisoformat(row["last_used"]) if row["last_used"] else datetime.now(),
            success_rate=row["success_rate"] or 1.0,
            is_active=bool(row["is_active"]),
            response_time_ms=row["response_time_ms"],
            health=ProxyHealth(row["health"]) if row["health"] else ProxyHealth.UNKNOWN
        )

    def load_all(self) -> List[ProxyConfig]:
        """Load all proxies from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM proxies WHERE is_active = 1").fetchall()
            
            for row in rows:
                proxy = self._row_to_proxy(row)
                self._proxies[proxy.id] = proxy
        
        return list(self._proxies.values())

    def load_from_file(self, file_path: str, provider: Optional[str] = None) -> int:
        """
        Load proxies from a text file (one per line).
        
        Args:
            file_path: Path to proxy list file
            provider: Optional provider name to tag proxies
            
        Returns:
            Number of proxies loaded
        """
        count = 0
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        proxy = ProxyConfig.from_url(line, provider=provider)
                        self.add_proxy(proxy)
                        count += 1
                    except Exception as e:
                        print(f"Failed to parse proxy line: {line} - {e}")
        
        return count

    def bind_to_account(self, account_id: str, proxy_id: str):
        """
        Bind a proxy to an account for consistent identity.
        
        This ensures the account always uses the same proxy IP,
        maintaining a consistent browser fingerprint.
        """
        self._account_bindings[account_id] = proxy_id
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO proxy_account_bindings (account_id, proxy_id)
                VALUES (?, ?)
            """, (account_id, proxy_id))
            conn.commit()

    def unbind_account(self, account_id: str):
        """Remove proxy binding for an account."""
        self._account_bindings.pop(account_id, None)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM proxy_account_bindings WHERE account_id = ?", (account_id,))
            conn.commit()

    def get_proxy_for_account(self, account_id: str) -> Optional[ProxyConfig]:
        """
        Get the proxy bound to an account.
        
        Returns the consistently assigned proxy for this account,
        or None if no proxy is bound.
        """
        # Check memory cache first
        if account_id in self._account_bindings:
            proxy_id = self._account_bindings[account_id]
            return self.get_proxy(proxy_id)
        
        # Check database
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT proxy_id FROM proxy_account_bindings WHERE account_id = ?",
                (account_id,)
            ).fetchone()
            
            if row:
                self._account_bindings[account_id] = row[0]
                return self.get_proxy(row[0])
        
        return None

    def get_available_proxy(self, exclude_ids: List[str] = None) -> Optional[ProxyConfig]:
        """
        Get an available proxy from the pool.
        
        Prioritizes by:
        1. Health status
        2. Success rate
        3. Last used time (least recently used)
        """
        exclude_ids = exclude_ids or []
        
        available = [
            p for p in self._proxies.values()
            if p.is_active and p.id not in exclude_ids and p.health != ProxyHealth.DOWN
        ]
        
        if not available:
            self.load_all()  # Reload from database
            available = [
                p for p in self._proxies.values()
                if p.is_active and p.id not in exclude_ids and p.health != ProxyHealth.DOWN
            ]
        
        if not available:
            return None
        
        # Sort by health, then success rate, then last used
        def sort_key(p: ProxyConfig):
            health_score = {
                ProxyHealth.HEALTHY: 0,
                ProxyHealth.UNKNOWN: 1,
                ProxyHealth.SLOW: 2,
                ProxyHealth.BLOCKED: 3,
                ProxyHealth.DOWN: 4
            }.get(p.health, 5)
            return (health_score, -p.success_rate, p.last_used)
        
        available.sort(key=sort_key)
        return available[0]

    def rotate_proxy(self, account_id: str) -> Optional[ProxyConfig]:
        """
        Rotate to a new proxy for an account.
        
        Used when the current proxy is blocked or underperforming.
        """
        current_proxy_id = self._account_bindings.get(account_id)
        exclude = [current_proxy_id] if current_proxy_id else []
        
        new_proxy = self.get_available_proxy(exclude_ids=exclude)
        if new_proxy:
            self.bind_to_account(account_id, new_proxy.id)
        
        return new_proxy

    def update_proxy_health(self, proxy_id: str, health: ProxyHealth, response_time_ms: float = None):
        """Update proxy health status after a request."""
        proxy = self.get_proxy(proxy_id)
        if not proxy:
            return
        
        proxy.health = health
        proxy.last_used = datetime.now()
        
        if response_time_ms is not None:
            proxy.response_time_ms = response_time_ms
        
        # Adjust success rate based on health
        if health == ProxyHealth.HEALTHY:
            proxy.success_rate = min(1.0, proxy.success_rate + 0.01)
        elif health in (ProxyHealth.BLOCKED, ProxyHealth.DOWN):
            proxy.success_rate = max(0.0, proxy.success_rate - 0.1)
        elif health == ProxyHealth.SLOW:
            proxy.success_rate = max(0.0, proxy.success_rate - 0.02)
        
        # Update database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE proxies 
                SET health = ?, last_used = ?, response_time_ms = ?, success_rate = ?
                WHERE id = ?
            """, (health.value, proxy.last_used.isoformat(), proxy.response_time_ms,
                  proxy.success_rate, proxy_id))
            conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """Get proxy pool statistics."""
        self.load_all()
        
        total = len(self._proxies)
        healthy = sum(1 for p in self._proxies.values() if p.health == ProxyHealth.HEALTHY)
        active = sum(1 for p in self._proxies.values() if p.is_active)
        bound = len(self._account_bindings)
        
        return {
            "total_proxies": total,
            "healthy": healthy,
            "active": active,
            "bound_to_accounts": bound,
            "avg_success_rate": sum(p.success_rate for p in self._proxies.values()) / max(total, 1)
        }

    def export_to_json(self, file_path: str):
        """Export all proxies to JSON file."""
        self.load_all()
        
        data = {
            "proxies": [p.to_dict() for p in self._proxies.values()],
            "bindings": self._account_bindings
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def import_from_json(self, file_path: str) -> int:
        """Import proxies from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)

        count = 0
        for proxy_data in data.get("proxies", []):
            proxy = ProxyConfig.from_dict(proxy_data)
            self.add_proxy(proxy)
            count += 1

        for account_id, proxy_id in data.get("bindings", {}).items():
            self.bind_to_account(account_id, proxy_id)

        return count

    # Provider Management Methods

    def add_provider(self, provider_name: str, provider_config: Any) -> None:
        """
        Add a proxy provider to the manager.

        Args:
            provider_name: Unique name for the provider
            provider_config: Provider configuration object
        """
        with self._provider_lock:
            try:
                from .proxy_providers import create_provider
                provider = create_provider(provider_name, provider_config)
                # Initialize the provider session once (handle async context)
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        with ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, provider.initialize())
                            future.result()  # Wait for completion
                    else:
                        asyncio.run(provider.initialize())
                except RuntimeError:
                    # No event loop, create one
                    asyncio.run(provider.initialize())
                self._providers[provider_name] = provider
                self._provider_configs[provider_name] = provider_config
            except Exception as e:
                raise ValueError(f"Failed to create provider {provider_name}: {e}")

    def remove_provider(self, provider_name: str) -> bool:
        """
        Remove a proxy provider.

        Args:
            provider_name: Name of the provider to remove

        Returns:
            True if provider was removed
        """
        with self._provider_lock:
            if provider_name in self._providers:
                # Close provider if it has cleanup
                provider = self._providers[provider_name]
                if hasattr(provider, 'cleanup'):
                    # Use ThreadPoolExecutor to handle async context
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            with ThreadPoolExecutor() as executor:
                                future = executor.submit(asyncio.run, provider.cleanup())
                                future.result()  # Wait for completion
                        else:
                            asyncio.run(provider.cleanup())
                    except Exception as e:
                        print(f"Warning: Failed to cleanup provider {provider_name}: {e}")

                del self._providers[provider_name]
                del self._provider_configs[provider_name]
                return True
        return False

    def get_provider(self, provider_name: str) -> Optional[Any]:
        """
        Get a provider instance.

        Args:
            provider_name: Name of the provider

        Returns:
            Provider instance or None
        """
        return self._providers.get(provider_name)

    def list_providers(self) -> List[str]:
        """Get list of configured provider names."""
        return list(self._providers.keys())

    async def get_proxy_from_provider(self, provider_name: str,
                                    country: Optional[str] = None,
                                    session_id: Optional[str] = None,
                                    sticky: bool = False) -> Optional[ProxyConfig]:
        """
        Get a proxy from a specific provider.

        Args:
            provider_name: Name of the provider
            country: Optional country code
            session_id: Optional session ID for sticky sessions
            sticky: Whether to create sticky session

        Returns:
            ProxyConfig or None if provider not found or failed
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return None

        try:
            async with provider:
                proxy = await provider.get_proxy(country=country, session_id=session_id, sticky=sticky)
                if proxy:
                    # Add to pool and return
                    self.add_proxy(proxy)
                return proxy
        except Exception as e:
            print(f"Failed to get proxy from {provider_name}: {e}")
            return None

    async def get_proxies_from_provider(self, provider_name: str, count: int,
                                       country: Optional[str] = None) -> List[ProxyConfig]:
        """
        Get multiple proxies from a provider.

        Args:
            provider_name: Name of the provider
            count: Number of proxies to get
            country: Optional country filter

        Returns:
            List of ProxyConfig objects
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return []

        try:
            async with provider:
                proxies = await provider.get_proxies_bulk(count=count, country=country)
                # Add all to pool
                for proxy in proxies:
                    self.add_proxy(proxy)
                return proxies
        except Exception as e:
            print(f"Failed to get proxies from {provider_name}: {e}")
            return []

    async def get_proxy_from_any_provider_async(self, country: Optional[str] = None,
                                               preferred_provider: Optional[str] = None,
                                               sticky: bool = False) -> Optional[ProxyConfig]:
        """
        Get a proxy from any available provider with failover (async version).

        Args:
            country: Optional country code
            preferred_provider: Preferred provider name
            sticky: Whether to create sticky session

        Returns:
            ProxyConfig or None
        """
        providers_to_try = []

        # Try preferred provider first
        if preferred_provider and preferred_provider in self._providers:
            providers_to_try.append(preferred_provider)

        # Add remaining providers
        for name in self._providers:
            if name != preferred_provider:
                providers_to_try.append(name)

        # Try each provider
        for provider_name in providers_to_try:
            proxy = await self.get_proxy_from_provider(
                provider_name, country=country, sticky=sticky
            )
            if proxy:
                return proxy

        return None

    def get_proxy_from_any_provider(self, country: Optional[str] = None,
                                   preferred_provider: Optional[str] = None,
                                   sticky: bool = False) -> Optional[ProxyConfig]:
        """
        Get a proxy from any available provider with failover.

        Args:
            country: Optional country code
            preferred_provider: Preferred provider name
            sticky: Whether to create sticky session

        Returns:
            ProxyConfig or None
        """
        # Create a new event loop if needed
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, delegate to async version
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.get_proxy_from_any_provider_async(country, preferred_provider, sticky)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.get_proxy_from_any_provider_async(country, preferred_provider, sticky)
                )
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(
                self.get_proxy_from_any_provider_async(country, preferred_provider, sticky)
            )

    def start_health_monitoring(self):
        """Start background health monitoring for providers."""
        if self._health_monitor_thread and self._health_monitor_thread.is_alive():
            return

        self._health_monitor_running = True
        self._health_monitor_thread = threading.Thread(
            target=self._health_monitor_loop,
            daemon=True
        )
        self._health_monitor_thread.start()

    def stop_health_monitoring(self):
        """Stop background health monitoring."""
        self._health_monitor_running = False
        if self._health_monitor_thread:
            self._health_monitor_thread.join(timeout=5)

    def _health_monitor_loop(self):
        """Background health monitoring loop."""
        while self._health_monitor_running:
            try:
                asyncio.run(self._perform_provider_health_checks())
                # Also check local proxy health
                self._perform_proxy_health_checks()
            except Exception as e:
                print(f"Health monitor error: {e}")

            time.sleep(self._health_check_interval)

    async def _perform_provider_health_checks(self):
        """Check health of all providers."""
        for provider_name, provider in self._providers.items():
            try:
                async with provider:
                    health_status = await provider.health_check()
                    print(f"Provider {provider_name} health: {health_status.get('status', 'unknown')}")
            except Exception as e:
                print(f"Provider {provider_name} health check failed: {e}")

    def _perform_proxy_health_checks(self):
        """Check health of proxies in the pool."""
        # Simple health check - mark old proxies as unknown
        now = datetime.now()
        for proxy in self._proxies.values():
            if proxy.last_used and (now - proxy.last_used).days > 1:
                if proxy.health == ProxyHealth.HEALTHY:
                    proxy.health = ProxyHealth.UNKNOWN
                    # Update in database
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute(
                            "UPDATE proxies SET health = ? WHERE id = ?",
                            (ProxyHealth.UNKNOWN.value, proxy.id)
                        )
                        conn.commit()

    async def get_provider_stats(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """
        Get usage statistics from a provider.

        Args:
            provider_name: Name of the provider

        Returns:
            Statistics dictionary or None
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return None

        try:
            async with provider:
                return await provider.get_usage_stats()
        except Exception as e:
            return {"error": f"Failed to get stats: {e}"}

    def get_combined_stats(self) -> Dict[str, Any]:
        """Get combined statistics for local pool and providers."""
        stats = self.get_stats()
        stats["providers"] = {}

        # Add provider stats (handle async context safely)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, use ThreadPoolExecutor
                with ThreadPoolExecutor() as executor:
                    for provider_name in self._providers:
                        future = executor.submit(
                            asyncio.run,
                            self.get_provider_stats(provider_name)
                        )
                        provider_stats = future.result()
                        if provider_stats:
                            stats["providers"][provider_name] = provider_stats
            else:
                # Safe to use asyncio.run
                for provider_name in self._providers:
                    provider_stats = asyncio.run(self.get_provider_stats(provider_name))
                    if provider_stats:
                        stats["providers"][provider_name] = provider_stats
        except Exception as e:
            # Fallback - just return local stats
            stats["providers_error"] = f"Failed to get provider stats: {e}"

        return stats

    def __enter__(self):
        """Context manager entry."""
        self.start_health_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_health_monitoring()