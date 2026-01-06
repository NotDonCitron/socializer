"""
Base classes and interfaces for proxy provider integrations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio
import aiohttp
from urllib.parse import urlparse

from radar.proxy_manager import ProxyConfig, ProxyHealth


@dataclass
class ProxyProviderConfig:
    """Configuration for proxy providers."""
    name: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    base_url: Optional[str] = None
    zone: Optional[str] = None
    country: Optional[str] = None
    max_concurrent_requests: int = 10
    request_timeout: int = 30
    retry_attempts: int = 3
    custom_headers: Optional[Dict[str, str]] = None
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize config to dictionary."""
        return {
            "name": self.name,
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "username": self.username,
            "password": self.password,
            "base_url": self.base_url,
            "zone": self.zone,
            "country": self.country,
            "max_concurrent_requests": self.max_concurrent_requests,
            "request_timeout": self.request_timeout,
            "retry_attempts": self.retry_attempts,
            "custom_headers": self.custom_headers,
            "enabled": self.enabled
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxyProviderConfig":
        """Deserialize config from dictionary."""
        return cls(**data)


class ProxyProvider(ABC):
    """
    Abstract base class for proxy providers.

    All proxy providers must implement this interface to ensure
    consistent behavior across different proxy services.
    """

    def __init__(self, config: ProxyProviderConfig):
        """
        Initialize proxy provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        self._last_health_check = datetime.min
        self._health_cache_duration = 300  # 5 minutes

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    async def initialize(self):
        """Initialize the provider (create HTTP session, etc.)."""
        if not self._session:
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
            headers = self.config.custom_headers or {}

            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )

    async def cleanup(self):
        """Clean up provider resources."""
        if self._session:
            await self._session.close()
            self._session = None

    @abstractmethod
    async def get_proxy(self, country: Optional[str] = None,
                       session_id: Optional[str] = None,
                       sticky: bool = False) -> ProxyConfig:
        """
        Get a proxy from the provider.

        Args:
            country: Optional country code (e.g., 'US', 'GB')
            session_id: Optional session identifier for sticky sessions
            sticky: Whether to return a sticky session proxy

        Returns:
            ProxyConfig object

        Raises:
            ProxyProviderError: If proxy cannot be obtained
        """
        pass

    @abstractmethod
    async def get_proxies_bulk(self, count: int,
                              country: Optional[str] = None) -> List[ProxyConfig]:
        """
        Get multiple proxies at once.

        Args:
            count: Number of proxies to retrieve
            country: Optional country filter

        Returns:
            List of ProxyConfig objects
        """
        pass

    @abstractmethod
    async def validate_proxy(self, proxy: ProxyConfig) -> bool:
        """
        Validate that a proxy is working.

        Args:
            proxy: Proxy to validate

        Returns:
            True if proxy is working
        """
        pass

    @abstractmethod
    async def rotate_session(self, session_id: str) -> ProxyConfig:
        """
        Rotate to a new proxy for an existing session.

        Args:
            session_id: Session identifier

        Returns:
            New ProxyConfig for the session
        """
        pass

    @abstractmethod
    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics from the provider.

        Returns:
            Dictionary with usage metrics
        """
        pass

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the provider.

        Returns:
            Health status dictionary
        """
        # Cache health checks to avoid excessive API calls
        now = datetime.now()
        if (now - self._last_health_check).seconds < self._health_cache_duration:
            return {"status": "cached", "cached_at": self._last_health_check.isoformat()}

        try:
            # Try to get a test proxy
            test_proxy = await self.get_proxy()
            is_healthy = await self.validate_proxy(test_proxy)

            self._last_health_check = now

            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "checked_at": now.isoformat(),
                "test_proxy": test_proxy.to_dict() if test_proxy else None
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "checked_at": now.isoformat()
            }

    async def _make_request(self, method: str, url: str,
                          params: Optional[Dict[str, Any]] = None,
                          data: Optional[Dict[str, Any]] = None,
                          headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Make an authenticated request to the provider API.

        Args:
            method: HTTP method
            url: Request URL
            params: Query parameters
            data: Request body data
            headers: Additional headers

        Returns:
            JSON response data

        Raises:
            ProxyProviderError: On request failure
        """
        async with self._semaphore:
            if not self._session:
                raise ProxyProviderError("Provider not initialized")

            request_headers = headers or {}

            try:
                async with self._session.request(
                    method, url, params=params, json=data, headers=request_headers
                ) as response:
                    response.raise_for_status()
                    return await response.json()

            except aiohttp.ClientError as e:
                raise ProxyProviderError(f"Request failed: {e}") from e

    def _build_proxy_url(self, host: str, port: int, username: Optional[str] = None,
                        password: Optional[str] = None, protocol: str = "http") -> str:
        """
        Build a proxy URL from components.

        Args:
            host: Proxy hostname/IP
            port: Proxy port
            username: Optional username
            password: Optional password
            protocol: Protocol (http, https, socks5)

        Returns:
            Formatted proxy URL
        """
        if username and password:
            return f"{protocol}://{username}:{password}@{host}:{port}"
        else:
            return f"{protocol}://{host}:{port}"

    async def _test_proxy_connectivity(self, proxy: ProxyConfig,
                                     test_url: str = "http://httpbin.org/ip") -> Tuple[bool, float]:
        """
        Test proxy connectivity and measure response time.

        Args:
            proxy: Proxy to test
            test_url: URL to test against

        Returns:
            Tuple of (success, response_time_ms)
        """
        if not self._session:
            return False, 0.0

        proxy_url = proxy.to_playwright_format()

        try:
            start_time = asyncio.get_event_loop().time()

            # Use the provider's session for testing to include auth
            proxy_dict = {}
            if "server" in proxy_url:
                proxy_dict["server"] = proxy_url["server"]
            if "username" in proxy_url and "password" in proxy_url:
                proxy_dict["username"] = proxy_url["username"]
                proxy_dict["password"] = proxy_url["password"]

            async with self._session.get(test_url, proxy=proxy_dict.get("server"),
                                       proxy_auth=aiohttp.BasicAuth(
                                           proxy_dict.get("username", ""),
                                           proxy_dict.get("password", "")
                                       ) if "username" in proxy_dict else None) as response:
                success = response.status == 200
                end_time = asyncio.get_event_loop().time()
                response_time = (end_time - start_time) * 1000  # Convert to ms

                return success, response_time

        except Exception:
            return False, 0.0


class ProxyProviderError(Exception):
    """Exception raised by proxy providers."""
    pass


# Utility functions

def create_provider(provider_name: str, config: ProxyProviderConfig) -> ProxyProvider:
    """
    Factory function to create proxy providers.

    Args:
        provider_name: Name of the provider ('brightdata', 'smartproxy', 'oxylabs')
        config: Provider configuration

    Returns:
        Configured ProxyProvider instance

    Raises:
        ValueError: If provider name is not recognized
    """
    provider_name = provider_name.lower()

    if provider_name == "brightdata":
        from .brightdata import BrightDataProvider
        return BrightDataProvider(config)
    elif provider_name == "smartproxy":
        from .smartproxy import SmartProxyProvider
        return SmartProxyProvider(config)
    elif provider_name == "oxylabs":
        from .oxylabs import OxylabsProvider
        return OxylabsProvider(config)
    else:
        raise ValueError(f"Unknown proxy provider: {provider_name}")