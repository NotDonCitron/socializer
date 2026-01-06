"""
Oxylabs proxy provider integration.

Oxylabs provides enterprise proxy services with:
- Web Unblocker for high-success residential proxies
- Dedicated datacenter proxies
- Rotating residential proxies
- Username/password authentication
- Country and city targeting
"""

import random
from typing import Dict, List, Any, Optional

from .base import ProxyProvider, ProxyProviderConfig, ProxyProviderError
from radar.proxy_manager import ProxyConfig, ProxyProtocol


class OxylabsProvider(ProxyProvider):
    """
    Oxylabs provider implementation.

    Supports Web Unblocker and other Oxylabs proxy services.
    """

    def __init__(self, config: ProxyProviderConfig):
        """
        Initialize Oxylabs provider.

        Args:
            config: Provider configuration with:
                - username: Oxylabs username (required)
                - password: Oxylabs password (required)
                - zone: Proxy type ('unblocker', 'residential', 'datacenter') (optional, defaults to 'unblocker')
                - country: Default country code (optional)
        """
        super().__init__(config)

        if not config.username:
            raise ValueError("Oxylabs username is required")
        if not config.password:
            raise ValueError("Oxylabs password is required")

        # Oxylabs endpoints for different proxy types
        self.endpoints = {
            "unblocker": {
                "host": "unblock.oxylabs.io",
                "port": 60000
            },
            "residential": {
                "host": "pr.oxylabs.io",
                "port": 7777
            },
            "datacenter": {
                "host": "dc.pr.oxylabs.io",
                "port": 8000
            }
        }

        # Default to unblocker if not specified
        self.proxy_type = config.zone or "unblocker"
        self.default_country = config.country

        if self.proxy_type not in self.endpoints:
            raise ValueError(f"Invalid proxy type: {self.proxy_type}. Must be 'unblocker', 'residential', or 'datacenter'")

    async def get_proxy(self, country: Optional[str] = None,
                       session_id: Optional[str] = None,
                       sticky: bool = False) -> ProxyConfig:
        """
        Get a proxy from Oxylabs.

        Args:
            country: Country code (e.g., 'us', 'gb', 'de')
            session_id: Session ID for sticky sessions
            sticky: Whether to create a sticky session

        Returns:
            ProxyConfig object
        """
        endpoint = self.endpoints[self.proxy_type]

        # Build username with options
        username_parts = [self.config.username]

        # Add country for geo-targeting
        target_country = country or self.default_country
        if target_country:
            username_parts.append(f"cc-{target_country.upper()}")

        # Add session ID for sticky sessions
        if sticky:
            if session_id:
                username_parts.append(f"ses-{session_id}")
            else:
                # Generate random session ID
                session_id = f"ses_{random.randint(100000, 999999)}"
                username_parts.append(session_id)

        username = "-".join(username_parts)

        return ProxyConfig(
            host=endpoint["host"],
            port=endpoint["port"],
            username=username,
            password=self.config.password,
            protocol=ProxyProtocol.HTTP,
            provider="oxylabs",
            country=target_country,
            id=f"oxylabs_{self.proxy_type}_{target_country or 'any'}_{session_id or 'rotating'}"
        )

    async def get_proxies_bulk(self, count: int,
                              country: Optional[str] = None) -> List[ProxyConfig]:
        """
        Get multiple proxies from Oxylabs.

        Args:
            count: Number of proxies to retrieve
            country: Optional country filter

        Returns:
            List of ProxyConfig objects
        """
        proxies = []

        for i in range(count):
            # Oxylabs supports sticky sessions for consistency
            session_id = f"bulk_{random.randint(100000, 999999)}_{i}"
            proxy = await self.get_proxy(country=country, session_id=session_id, sticky=True)
            proxies.append(proxy)

        return proxies

    async def validate_proxy(self, proxy: ProxyConfig) -> bool:
        """
        Validate Oxylabs proxy by testing connectivity.

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

        For Oxylabs, this maintains the session but gets a new IP.

        Args:
            session_id: Session identifier

        Returns:
            New ProxyConfig for the session
        """
        # Keep the same session ID but it will rotate to a new IP
        return await self.get_proxy(session_id=session_id, sticky=True)

    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics from Oxylabs.

        Oxylabs provides usage stats via their dashboard API.

        Returns:
            Dictionary with usage metrics
        """
        try:
            # Oxylabs usage API (mock implementation)
            # In reality, this would require API authentication
            return {
                "provider": "oxylabs",
                "proxy_type": self.proxy_type,
                "estimated_daily_usage_gb": 75,  # Mock data
                "requests_today": 35000,  # Mock data
                "success_rate": 0.96,  # Mock data
                "active_sessions": 150 if self.proxy_type == "unblocker" else 50  # Mock data
            }

        except Exception as e:
            return {
                "provider": "oxylabs",
                "proxy_type": self.proxy_type,
                "error": f"Failed to get usage stats: {e}"
            }

    async def get_available_countries(self) -> List[str]:
        """
        Get list of available countries for Oxylabs proxies.

        Returns:
            List of country codes
        """
        # Oxylabs supports extensive country coverage
        # This is a subset - in reality would fetch from API
        return [
            "US", "GB", "DE", "FR", "IT", "ES", "CA", "AU", "JP", "KR",
            "BR", "MX", "AR", "CL", "CO", "PE", "VE", "EC", "BO", "UY",
            "PL", "CZ", "HU", "RO", "BG", "GR", "TR", "RU", "UA", "BY",
            "KZ", "UZ", "IN", "TH", "MY", "SG", "PH", "ID", "VN", "TW",
            "HK", "CN", "ZA", "EG", "NG", "KE", "MA", "TN", "GH", "CI",
            "NL", "BE", "AT", "CH", "SE", "NO", "DK", "FI", "PT", "IE"
        ]

    def get_endpoint_info(self) -> Dict[str, Any]:
        """
        Get information about the current endpoint.

        Returns:
            Endpoint configuration
        """
        endpoint = self.endpoints[self.proxy_type]

        features = []
        if self.proxy_type == "unblocker":
            features = ["web_unblocker", "high_success_rate", "rotating_ips", "sticky_sessions", "country_targeting"]
        elif self.proxy_type == "residential":
            features = ["residential_ips", "rotating_ips", "country_targeting", "city_targeting"]
        else:  # datacenter
            features = ["datacenter_ips", "high_speed", "low_latency", "static_ips"]

        return {
            "proxy_type": self.proxy_type,
            "host": endpoint["host"],
            "port": endpoint["port"],
            "features": features,
            "default_country": self.default_country,
            "protocol": "http"
        }

    async def get_city_list(self, country: str) -> List[str]:
        """
        Get list of available cities for a country.

        Args:
            country: Country code

        Returns:
            List of city names
        """
        # Mock implementation - in reality would fetch from Oxylabs API
        city_mapping = {
            "US": ["newyork", "losangeles", "chicago", "houston", "miami"],
            "GB": ["london", "manchester", "birmingham", "leeds"],
            "DE": ["berlin", "munich", "hamburg", "cologne"],
            "FR": ["paris", "lyon", "marseille", "toulouse"],
            "IT": ["rome", "milan", "naples", "turin"],
            "ES": ["madrid", "barcelona", "valencia", "seville"],
            "CA": ["toronto", "vancouver", "montreal", "calgary"]
        }

        return city_mapping.get(country.upper(), [])


# Convenience functions

def create_oxylabs_config(username: str, password: str,
                         proxy_type: str = "unblocker",
                         country: Optional[str] = None) -> ProxyProviderConfig:
    """
    Create Oxylabs provider configuration.

    Args:
        username: Oxylabs username
        password: Oxylabs password
        proxy_type: 'unblocker', 'residential', or 'datacenter'
        country: Default country code

    Returns:
        ProxyProviderConfig for Oxylabs
    """
    return ProxyProviderConfig(
        name="oxylabs",
        username=username,
        password=password,
        zone=proxy_type,
        country=country,
        base_url="https://oxylabs.io/api"
    )