"""
SmartProxy provider integration.

SmartProxy provides residential and datacenter proxies with:
- Residential proxies with country/city targeting
- Datacenter proxies for high speed
- Username/password authentication
- Rotating and sticky sessions
"""

import random
from typing import Dict, List, Any, Optional

from .base import ProxyProvider, ProxyProviderConfig, ProxyProviderError
from radar.proxy_manager import ProxyConfig, ProxyProtocol


class SmartProxyProvider(ProxyProvider):
    """
    SmartProxy provider implementation.

    Supports both residential and datacenter proxies.
    """

    def __init__(self, config: ProxyProviderConfig):
        """
        Initialize SmartProxy provider.

        Args:
            config: Provider configuration with:
                - username: SmartProxy username (required)
                - password: SmartProxy password (required)
                - zone: Proxy type ('residential', 'datacenter') (optional, defaults to 'residential')
                - country: Default country code (optional)
        """
        super().__init__(config)

        if not config.username:
            raise ValueError("SmartProxy username is required")
        if not config.password:
            raise ValueError("SmartProxy password is required")

        # SmartProxy endpoints
        self.endpoints = {
            "residential": {
                "host": "gate.smartproxy.com",
                "port": 7000
            },
            "datacenter": {
                "host": "dc.smartproxy.com",
                "port": 20000
            }
        }

        # Default to residential if not specified
        self.proxy_type = config.zone or "residential"
        self.default_country = config.country

        if self.proxy_type not in self.endpoints:
            raise ValueError(f"Invalid proxy type: {self.proxy_type}. Must be 'residential' or 'datacenter'")

    async def get_proxy(self, country: Optional[str] = None,
                       session_id: Optional[str] = None,
                       sticky: bool = False) -> ProxyConfig:
        """
        Get a proxy from SmartProxy.

        Args:
            country: Country code for residential proxies (e.g., 'us', 'gb')
            session_id: Session ID for sticky sessions
            sticky: Whether to create a sticky session

        Returns:
            ProxyConfig object
        """
        endpoint = self.endpoints[self.proxy_type]

        # Build username with options
        username_parts = [self.config.username]

        # Add country for residential proxies
        if self.proxy_type == "residential":
            target_country = country or self.default_country
            if target_country:
                username_parts.append(f"country-{target_country.lower()}")

        # Add session ID for sticky sessions (residential only)
        if sticky and self.proxy_type == "residential":
            if session_id:
                username_parts.append(f"session-{session_id}")
            else:
                # Generate random session ID
                session_id = f"ses_{random.randint(100000, 999999)}"
                username_parts.append(f"session-{session_id}")

        username = "-".join(username_parts)

        return ProxyConfig(
            host=endpoint["host"],
            port=endpoint["port"],
            username=username,
            password=self.config.password,
            protocol=ProxyProtocol.HTTP,
            provider="smartproxy",
            country=country or self.default_country,
            id=f"smartproxy_{self.proxy_type}_{country or 'any'}_{session_id or 'rotating'}"
        )

    async def get_proxies_bulk(self, count: int,
                              country: Optional[str] = None) -> List[ProxyConfig]:
        """
        Get multiple proxies from SmartProxy.

        Args:
            count: Number of proxies to retrieve
            country: Optional country filter

        Returns:
            List of ProxyConfig objects
        """
        proxies = []

        for i in range(count):
            if self.proxy_type == "residential" and count > 1:
                # Create sticky sessions for bulk residential requests
                session_id = f"bulk_{random.randint(100000, 999999)}_{i}"
                proxy = await self.get_proxy(country=country, session_id=session_id, sticky=True)
            else:
                # Rotating proxies for datacenter or single residential
                proxy = await self.get_proxy(country=country, sticky=False)

            proxies.append(proxy)

        return proxies

    async def validate_proxy(self, proxy: ProxyConfig) -> bool:
        """
        Validate SmartProxy proxy by testing connectivity.

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

        Args:
            session_id: Session identifier

        Returns:
            New ProxyConfig for the session
        """
        if self.proxy_type == "residential":
            # For residential, keep the same session ID to maintain stickiness
            return await self.get_proxy(session_id=session_id, sticky=True)
        else:
            # For datacenter, just return a new rotating proxy
            return await self.get_proxy(sticky=False)

    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics from SmartProxy.

        SmartProxy provides usage stats via their dashboard API.

        Returns:
            Dictionary with usage metrics
        """
        try:
            # SmartProxy usage API (mock implementation)
            # In reality, this would require API authentication
            return {
                "provider": "smartproxy",
                "proxy_type": self.proxy_type,
                "estimated_daily_usage_gb": 50,  # Mock data
                "requests_today": 25000,  # Mock data
                "success_rate": 0.98,  # Mock data
                "active_proxies": 100 if self.proxy_type == "residential" else 50  # Mock data
            }

        except Exception as e:
            return {
                "provider": "smartproxy",
                "proxy_type": self.proxy_type,
                "error": f"Failed to get usage stats: {e}"
            }

    async def get_available_countries(self) -> List[str]:
        """
        Get list of available countries for residential proxies.

        Returns:
            List of country codes
        """
        if self.proxy_type != "residential":
            return []

        # SmartProxy supports many countries
        # This is a subset - in reality would fetch from API
        return [
            "us", "gb", "de", "fr", "it", "es", "ca", "au", "jp", "kr",
            "br", "mx", "ar", "cl", "co", "pe", "ve", "ec", "bo", "uy",
            "pl", "cz", "hu", "ro", "bg", "gr", "tr", "ru", "ua", "by",
            "kz", "uz", "in", "th", "my", "sg", "ph", "id", "vn", "tw",
            "hk", "cn", "za", "eg", "ng", "ke", "ma", "tn", "gh", "ci"
        ]

    def get_endpoint_info(self) -> Dict[str, Any]:
        """
        Get information about the current endpoint.

        Returns:
            Endpoint configuration
        """
        endpoint = self.endpoints[self.proxy_type]

        return {
            "proxy_type": self.proxy_type,
            "host": endpoint["host"],
            "port": endpoint["port"],
            "features": [
                "rotating_ips" if self.proxy_type == "residential" else "high_speed",
                "sticky_sessions" if self.proxy_type == "residential" else None,
                "country_targeting" if self.proxy_type == "residential" else None,
                "global_coverage" if self.proxy_type == "residential" else "major_regions"
            ],
            "default_country": self.default_country,
            "protocol": "http"
        }


# Convenience functions

def create_smartproxy_config(username: str, password: str,
                           proxy_type: str = "residential",
                           country: Optional[str] = None) -> ProxyProviderConfig:
    """
    Create SmartProxy provider configuration.

    Args:
        username: SmartProxy username
        password: SmartProxy password
        proxy_type: 'residential' or 'datacenter'
        country: Default country code (residential only)

    Returns:
        ProxyProviderConfig for SmartProxy
    """
    return ProxyProviderConfig(
        name="smartproxy",
        username=username,
        password=password,
        zone=proxy_type,
        country=country,
        base_url="https://smartproxy.com/api"
    )