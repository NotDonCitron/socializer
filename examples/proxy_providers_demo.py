#!/usr/bin/env python3
"""
Demo script showing proxy provider integrations.

This example demonstrates how to use BrightData, SmartProxy, and Oxylabs
proxy providers with the enhanced ProxyManager.
"""

import asyncio
from radar.proxy_manager import ProxyManager
from radar.proxy_providers import (
    ProxyProviderConfig,
    create_brightdata_config,
    create_smartproxy_config,
    create_oxylabs_config
)


async def demo_proxy_providers():
    """Demonstrate proxy provider functionality."""

    print("🚀 Proxy Provider Integration Demo")
    print("=" * 50)

    # Initialize proxy manager
    proxy_manager = ProxyManager()

    try:
        # Add providers (using mock credentials for demo)
        print("\n📦 Adding proxy providers...")

        # BrightData provider
        brightdata_config = create_brightdata_config(
            customer_id="demo_customer",
            zone_password="demo_password",
            zone="residential",
            country="us"
        )
        proxy_manager.add_provider("brightdata", brightdata_config)
        print("✅ Added BrightData provider")

        # SmartProxy provider
        smartproxy_config = create_smartproxy_config(
            username="demo_user",
            password="demo_pass",
            proxy_type="residential",
            country="us"
        )
        proxy_manager.add_provider("smartproxy", smartproxy_config)
        print("✅ Added SmartProxy provider")

        # Oxylabs provider
        oxylabs_config = create_oxylabs_config(
            username="demo_user",
            password="demo_pass",
            proxy_type="unblocker",
            country="US"
        )
        proxy_manager.add_provider("oxylabs", oxylabs_config)
        print("✅ Added Oxylabs provider")

        # List configured providers
        providers = proxy_manager.list_providers()
        print(f"\n🔧 Configured providers: {', '.join(providers)}")

        # Demonstrate getting proxies from providers
        print("\n🌐 Getting proxies from providers...")

        for provider_name in providers:
            try:
                print(f"\n--- {provider_name.upper()} ---")

                # Get a single proxy
                proxy = await proxy_manager.get_proxy_from_provider(provider_name, country="US")
                if proxy:
                    print(f"✅ Got proxy: {proxy.host}:{proxy.port} ({proxy.provider})")
                else:
                    print("❌ Failed to get proxy")

                # Get provider stats
                stats = await proxy_manager.get_provider_stats(provider_name)
                if stats and "error" not in stats:
                    print(f"📊 Stats: {stats}")
                else:
                    print("📊 Stats: Mock data (configure real credentials for actual stats)")

            except Exception as e:
                print(f"❌ Error with {provider_name}: {e}")

        # Demonstrate failover
        print("\n🔄 Testing provider failover...")
        proxy = proxy_manager.get_proxy_from_any_provider(country="US")
        if proxy:
            print(f"✅ Got proxy via failover: {proxy.host}:{proxy.port} ({proxy.provider})")
        else:
            print("❌ Failover failed")

        # Show combined stats
        print("\n📈 Combined Statistics:")
        local_stats = proxy_manager.get_stats()
        print(f"Local pool: {local_stats['total_proxies']} proxies")
        print(f"Providers: {len(proxy_manager.list_providers())} configured")

        # Show individual provider stats (already shown above)
        print("Provider stats shown above (configure real credentials for actual usage data)")

    finally:
        # Cleanup
        proxy_manager.stop_health_monitoring()
        print("\n🧹 Cleanup completed")


def demo_provider_configurations():
    """Show how to configure different providers."""

    print("\n🔧 Provider Configuration Examples")
    print("=" * 50)

    # BrightData configuration
    print("\n--- BrightData ---")
    bd_config = ProxyProviderConfig(
        name="brightdata",
        username="your_customer_id",
        password="your_zone_password",
        zone="residential",  # or "datacenter", "mobile", etc.
        country="us"
    )
    print("Configuration:", bd_config.to_dict())

    # SmartProxy configuration
    print("\n--- SmartProxy ---")
    sp_config = ProxyProviderConfig(
        name="smartproxy",
        username="your_username",
        password="your_password",
        zone="residential",  # or "datacenter"
        country="us"
    )
    print("Configuration:", sp_config.to_dict())

    # Oxylabs configuration
    print("\n--- Oxylabs ---")
    oxy_config = ProxyProviderConfig(
        name="oxylabs",
        username="your_username",
        password="your_password",
        zone="unblocker",  # or "residential", "datacenter"
        country="US"
    )
    print("Configuration:", oxy_config.to_dict())


if __name__ == "__main__":
    # Run async demo
    asyncio.run(demo_proxy_providers())

    # Show configurations
    demo_provider_configurations()

    print("\n✨ Demo completed! Configure real credentials to use actual proxy services.")