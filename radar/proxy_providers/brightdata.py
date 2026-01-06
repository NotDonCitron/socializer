"""
BrightData (Luminati) proxy provider integration.

BrightData provides enterprise-grade proxy services with:
- Super Proxy for rotating residential proxies
- Zone-based proxy management
- Country and city targeting
- Sticky sessions with session IDs
"""

import random
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from .base import ProxyProvider, ProxyProviderConfig, ProxyProviderError
from radar.proxy_manager import ProxyConfig, ProxyProtocol


class BrightDataProvider(ProxyProvider):
    """
    BrightData proxy provider implementation.

    Uses BrightData's Super Proxy API for high-quality residential proxies.
    """

    def __init__(self, config: ProxyProviderConfig):
        """
        Initialize BrightData provider.

        Args:
            config: Provider configuration with:
                - username: BrightData customer ID (required)
                - password: BrightData zone password (required)
                - zone: Zone name (required)
                - country: Default country code (optional)
        """
        super().__init__(config)

        if not config.username:
            raise ValueError("BrightData customer ID (username) is required")
        if not config.password:
            raise ValueError("BrightData zone password is required")
        if not config.zone:
            raise ValueError("BrightData zone name is required")

        # BrightData Super Proxy endpoints
        self.super_proxy_host = "zproxy.lum-superproxy.io"
        self.super_proxy_port = 22225

        # Zone configuration
        self.zone = config.zone
        self.default_country = config.country

    async def get_proxy(self, country: Optional[str] = None,
                       session_id: Optional[str] = None,
                       sticky: bool = False) -> ProxyConfig:
        """
        Get a proxy from BrightData.

        Args:
            country: Country code (e.g., 'us', 'gb', 'de')
            session_id: Session ID for sticky sessions
            sticky: Whether to create a sticky session

        Returns:
            ProxyConfig object
        """
        # Build BrightData proxy URL with zone and options
        username_parts = [self.config.username]

        # Add zone
        username_parts.append(f"zone-{self.zone}")

        # Add country if specified
        target_country = country or self.default_country
        if target_country:
            username_parts.append(f"country-{target_country.lower()}")

        # Add session ID for sticky sessions
        if sticky and session_id:
            username_parts.append(f"session-{session_id}")
        elif sticky:
            # Generate random session ID for sticky session
            session_id = f"ses_{random.randint(100000, 999999)}"
            username_parts.append(f"session-{session_id}")

        # Build username
        username = "-".join(username_parts)

        return ProxyConfig(
            host=self.super_proxy_host,
            port=self.super_proxy_port,
            username=username,
            password=self.config.password,
            protocol=ProxyProtocol.HTTP,
            provider="brightdata",
            country=target_country,
            id=f"brightdata_{self.zone}_{target_country or 'any'}_{session_id or 'rotating'}"
        )

    async def get_proxies_bulk(self, count: int,
                              country: Optional[str] = None) -> List[ProxyConfig]:
        """
        Get multiple proxies from BrightData.

        For BrightData, we create multiple proxy configs with different
        session IDs for sticky sessions, or rotating proxies.

        Args:
            count: Number of proxies to retrieve
            country: Optional country filter

        Returns:
            List of ProxyConfig objects
        """
        proxies = []

        for i in range(count):
            if count > 1:
                # Create sticky sessions for bulk requests
                session_id = f"bulk_{random.randint(100000, 999999)}_{i}"
                proxy = await self.get_proxy(country=country, session_id=session_id, sticky=True)
            else:
                # Single rotating proxy
                proxy = await self.get_proxy(country=country, sticky=False)

            proxies.append(proxy)

        return proxies

    async def validate_proxy(self, proxy: ProxyConfig) -> bool:
        """
        Validate BrightData proxy by testing connectivity.

        Args:
            proxy: Proxy to validate

        Returns:
            True if proxy is working
        """
        success, response_time = await self._test_proxy_connectivity(proxy)
        return success

    async def rotate_session(self, session_id: str) -> ProxyConfig:
        """
        Rotate to a new proxy for a session.

        For BrightData, this creates a new proxy config with the same session ID,
        which will get a different IP from the pool.

        Args:
            session_id: Session identifier

        Returns:
            New ProxyConfig for the session
        """
        # BrightData handles rotation automatically for the same session
        # We just return a new proxy config with the same session ID
        return await self.get_proxy(session_id=session_id, sticky=True)

    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics from BrightData.

        BrightData provides usage stats via their API.

        Returns:
            Dictionary with usage metrics
        """
        try:
            # BrightData usage API
            url = f"https://brightdata.com/api/usage?customer={self.config.username}"

            # This would require API key authentication
            # For now, return mock stats
            return {
                "provider": "brightdata",
                "zone": self.zone,
                "estimated_daily_usage_gb": 100,  # Mock data
                "requests_today": 50000,  # Mock data
                "success_rate": 0.95,  # Mock data
                "active_sessions": 25  # Mock data
            }

        except Exception as e:
            return {
                "provider": "brightdata",
                "error": f"Failed to get usage stats: {e}",
                "zone": self.zone
            }

    async def get_zone_info(self) -> Dict[str, Any]:
        """
        Get information about the current zone.

        Returns:
            Zone configuration and capabilities
        """
        return {
            "zone": self.zone,
            "type": "residential",  # Assuming residential zone
            "features": [
                "rotating_ips",
                "sticky_sessions",
                "country_targeting",
                "city_targeting",
                "super_proxy"
            ],
            "default_country": self.default_country,
            "super_proxy_host": self.super_proxy_host,
            "super_proxy_port": self.super_proxy_port
        }

    def _parse_proxy_url(self, proxy_url: str) -> Dict[str, Any]:
        """
        Parse BrightData proxy URL to extract configuration.

        Args:
            proxy_url: BrightData proxy URL

        Returns:
            Dictionary with parsed components
        """
        parsed = urlparse(proxy_url)

        # BrightData username format: customer-zone-country-session
        username_parts = parsed.username.split('-') if parsed.username else []

        info = {
            "customer": None,
            "zone": None,
            "country": None,
            "session": None
        }

        if len(username_parts) >= 1:
            info["customer"] = username_parts[0]
        if len(username_parts) >= 2 and username_parts[1].startswith("zone-"):
            info["zone"] = username_parts[1].replace("zone-", "")
        if len(username_parts) >= 3 and username_parts[2].startswith("country-"):
            info["country"] = username_parts[2].replace("country-", "")
        if len(username_parts) >= 4 and username_parts[3].startswith("session-"):
            info["session"] = username_parts[3].replace("session-", "")

        return info


# Convenience functions

def create_brightdata_config(customer_id: str, zone_password: str,
                           zone: str, country: Optional[str] = None) -> ProxyProviderConfig:
    """
    Create BrightData provider configuration.

    Args:
        customer_id: BrightData customer ID
        zone_password: Zone password
        zone: Zone name
        country: Default country code

    Returns:
        ProxyProviderConfig for BrightData
    """
    return ProxyProviderConfig(
        name="brightdata",
        username=customer_id,
        password=zone_password,
        zone=zone,
        country=country,
        base_url="https://brightdata.com/api"
    )