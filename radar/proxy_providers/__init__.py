"""
Proxy provider integrations for multi-account social media automation.

This package provides integrations with various proxy services:
- BrightData (Luminati)
- SmartProxy
- Oxylabs

All providers implement a common interface for unified proxy management.
"""

from .base import ProxyProvider, ProxyProviderConfig, create_provider
from .brightdata import BrightDataProvider, create_brightdata_config
from .smartproxy import SmartProxyProvider, create_smartproxy_config
from .oxylabs import OxylabsProvider, create_oxylabs_config

__all__ = [
    "ProxyProvider",
    "ProxyProviderConfig",
    "create_provider",
    "BrightDataProvider",
    "SmartProxyProvider",
    "OxylabsProvider",
    "create_brightdata_config",
    "create_smartproxy_config",
    "create_oxylabs_config"
]