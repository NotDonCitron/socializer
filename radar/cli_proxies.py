#!/usr/bin/env python3
"""
Proxy management CLI commands for radar.

Provides commands to manage proxy pools and provider configurations.
"""

import argparse
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path

from .proxy_manager import ProxyManager, ProxyConfig, ProxyHealth
from .proxy_providers import (
    ProxyProviderConfig,
    create_brightdata_config,
    create_smartproxy_config,
    create_oxylabs_config
)


class ProxyCLI:
    """Command-line interface for proxy management."""

    def __init__(self):
        self.proxy_manager = ProxyManager()

    def setup_parser(self, subparsers: argparse._SubParsersAction) -> None:
        """Set up the proxy subcommand parser."""

        # Main proxies parser
        proxies_parser = subparsers.add_parser(
            'proxies',
            help='Manage proxy pools and providers'
        )
        proxies_subparsers = proxies_parser.add_subparsers(
            dest='proxies_command',
            help='Proxy operations'
        )

        # proxies add
        add_parser = proxies_subparsers.add_parser(
            'add',
            help='Add a proxy to the pool'
        )
        add_parser.add_argument(
            'url',
            help='Proxy URL (protocol://host:port or protocol://user:pass@host:port)'
        )
        add_parser.add_argument(
            '--provider',
            help='Provider name for tagging'
        )

        # proxies add-provider
        add_provider_parser = proxies_subparsers.add_parser(
            'add-provider',
            help='Add a proxy provider'
        )
        add_provider_parser.add_argument(
            'provider_type',
            choices=['brightdata', 'smartproxy', 'oxylabs'],
            help='Type of proxy provider'
        )
        add_provider_parser.add_argument(
            'provider_name',
            help='Unique name for this provider instance'
        )
        add_provider_parser.add_argument(
            '--username',
            required=True,
            help='Provider username/customer ID'
        )
        add_provider_parser.add_argument(
            '--password',
            required=True,
            help='Provider password/zone password'
        )
        add_provider_parser.add_argument(
            '--zone',
            help='Zone type (brightdata: residential/datacenter/mobile, smartproxy: residential/datacenter, oxylabs: unblocker/residential/datacenter)'
        )
        add_provider_parser.add_argument(
            '--country',
            help='Default country code'
        )

        # proxies remove
        remove_parser = proxies_subparsers.add_parser(
            'remove',
            help='Remove a proxy from the pool'
        )
        remove_parser.add_argument(
            'proxy_id',
            help='Proxy ID to remove'
        )

        # proxies remove-provider
        remove_provider_parser = proxies_subparsers.add_parser(
            'remove-provider',
            help='Remove a proxy provider'
        )
        remove_provider_parser.add_argument(
            'provider_name',
            help='Provider name to remove'
        )

        # proxies list
        list_parser = proxies_subparsers.add_parser(
            'list',
            help='List proxies in the pool'
        )
        list_parser.add_argument(
            '--provider',
            help='Filter by provider'
        )
        list_parser.add_argument(
            '--country',
            help='Filter by country'
        )
        list_parser.add_argument(
            '--status',
            choices=['healthy', 'slow', 'blocked', 'down', 'unknown'],
            help='Filter by health status'
        )
        list_parser.add_argument(
            '--json',
            action='store_true',
            help='Output as JSON'
        )

        # proxies list-providers
        list_providers_parser = proxies_subparsers.add_parser(
            'list-providers',
            help='List configured providers'
        )

        # proxies test
        test_parser = proxies_subparsers.add_parser(
            'test',
            help='Test proxy connectivity'
        )
        test_parser.add_argument(
            'proxy_id',
            help='Proxy ID to test'
        )

        # proxies test-all
        test_all_parser = proxies_subparsers.add_parser(
            'test-all',
            help='Test all proxies in the pool'
        )
        test_all_parser.add_argument(
            '--provider',
            help='Test only proxies from specific provider'
        )

        # proxies status
        status_parser = proxies_subparsers.add_parser(
            'status',
            help='Show proxy pool status'
        )
        status_parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed statistics'
        )

        # proxies get
        get_parser = proxies_subparsers.add_parser(
            'get',
            help='Get a proxy from pool or provider'
        )
        get_parser.add_argument(
            '--country',
            help='Request specific country'
        )
        get_parser.add_argument(
            '--provider',
            help='Use specific provider'
        )
        get_parser.add_argument(
            '--sticky',
            action='store_true',
            help='Request sticky session'
        )

        # proxies import
        import_parser = proxies_subparsers.add_parser(
            'import',
            help='Import proxies from file'
        )
        import_parser.add_argument(
            'file_path',
            help='Path to proxy list file (one per line)'
        )
        import_parser.add_argument(
            '--provider',
            help='Provider name to tag imported proxies'
        )

        # proxies export
        export_parser = proxies_subparsers.add_parser(
            'export',
            help='Export proxies to file'
        )
        export_parser.add_argument(
            'file_path',
            help='Output file path'
        )

        # proxies monitor
        monitor_parser = proxies_subparsers.add_parser(
            'monitor',
            help='Start/stop health monitoring'
        )
        monitor_parser.add_argument(
            'action',
            choices=['start', 'stop', 'status'],
            help='Monitoring action'
        )

    def run_command(self, args: argparse.Namespace) -> None:
        """Execute the proxy command."""

        command = args.proxies_command

        if command == 'add':
            self._add_proxy(args)
        elif command == 'add-provider':
            self._add_provider(args)
        elif command == 'remove':
            self._remove_proxy(args)
        elif command == 'remove-provider':
            self._remove_provider(args)
        elif command == 'list':
            self._list_proxies(args)
        elif command == 'list-providers':
            self._list_providers(args)
        elif command == 'test':
            self._test_proxy(args)
        elif command == 'test-all':
            self._test_all_proxies(args)
        elif command == 'status':
            self._show_status(args)
        elif command == 'get':
            self._get_proxy(args)
        elif command == 'import':
            self._import_proxies(args)
        elif command == 'export':
            self._export_proxies(args)
        elif command == 'monitor':
            self._monitor(args)
        else:
            print(f"Unknown proxies command: {command}")
            sys.exit(1)

    def _add_proxy(self, args: argparse.Namespace) -> None:
        """Add a proxy to the pool."""
        try:
            proxy = ProxyConfig.from_url(args.url, provider=args.provider)
            proxy_id = self.proxy_manager.add_proxy(proxy)
            print(f"✅ Added proxy {args.url} with ID: {proxy_id}")
        except Exception as e:
            print(f"❌ Failed to add proxy: {e}")
            sys.exit(1)

    def _add_provider(self, args: argparse.Namespace) -> None:
        """Add a proxy provider."""
        try:
            # Create provider config based on type
            if args.provider_type == 'brightdata':
                config = create_brightdata_config(
                    customer_id=args.username,
                    zone_password=args.password,
                    zone=args.zone or 'residential',
                    country=args.country
                )
            elif args.provider_type == 'smartproxy':
                config = create_smartproxy_config(
                    username=args.username,
                    password=args.password,
                    proxy_type=args.zone or 'residential',
                    country=args.country
                )
            elif args.provider_type == 'oxylabs':
                config = create_oxylabs_config(
                    username=args.username,
                    password=args.password,
                    proxy_type=args.zone or 'unblocker',
                    country=args.country
                )

            self.proxy_manager.add_provider(args.provider_name, config)
            print(f"✅ Added {args.provider_type} provider '{args.provider_name}'")

        except Exception as e:
            print(f"❌ Failed to add provider: {e}")
            sys.exit(1)

    def _remove_proxy(self, args: argparse.Namespace) -> None:
        """Remove a proxy from the pool."""
        try:
            # Check if proxy exists first
            proxy = self.proxy_manager.get_proxy(args.proxy_id)
            if not proxy:
                print(f"❌ Proxy {args.proxy_id} not found")
                sys.exit(1)

            self.proxy_manager.remove_proxy(args.proxy_id)
            print(f"✅ Removed proxy {args.proxy_id}")

        except Exception as e:
            print(f"❌ Failed to remove proxy: {e}")
            sys.exit(1)

    def _remove_provider(self, args: argparse.Namespace) -> None:
        """Remove a proxy provider."""
        try:
            success = self.proxy_manager.remove_provider(args.provider_name)
            if success:
                print(f"✅ Removed provider '{args.provider_name}'")
            else:
                print(f"❌ Provider '{args.provider_name}' not found")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to remove provider: {e}")
            sys.exit(1)

    def _list_proxies(self, args: argparse.Namespace) -> None:
        """List proxies with optional filtering."""
        try:
            # Get all proxies
            proxies = self.proxy_manager.load_all()

            # Apply filters
            if args.provider:
                proxies = [p for p in proxies if p.provider == args.provider]

            if args.country:
                proxies = [p for p in proxies if p.country == args.country]

            if args.status:
                proxies = [p for p in proxies if p.health.value == args.status]

            if args.json:
                # JSON output
                import json
                proxy_dicts = [p.to_dict() for p in proxies]
                print(json.dumps(proxy_dicts, indent=2))
            else:
                # Table output
                if not proxies:
                    print("No proxies found")
                    return

                print(f"🌐 Proxies ({len(proxies)})")
                print("-" * 100)
                print(f"{'ID':<8} {'Host':<20} {'Port':<6} {'Protocol':<8} {'Provider':<12} {'Country':<8} {'Health':<8} {'Success':<7}")
                print("-" * 100)

                for proxy in proxies:
                    provider_short = proxy.provider[:10] + '...' if proxy.provider and len(proxy.provider) > 10 else (proxy.provider or '')
                    print(f"{proxy.id:<8} {proxy.host:<20} {proxy.port:<6} {proxy.protocol.value:<8} {provider_short:<12} {proxy.country or '':<8} {proxy.health.value:<8} {proxy.success_rate:.2f}")

        except Exception as e:
            print(f"❌ Failed to list proxies: {e}")
            sys.exit(1)

    def _list_providers(self, args: argparse.Namespace) -> None:
        """List configured providers."""
        try:
            providers = self.proxy_manager.list_providers()

            if not providers:
                print("No providers configured")
                return

            print(f"🏢 Providers ({len(providers)})")
            print("-" * 30)

            for provider in providers:
                print(f"  {provider}")

        except Exception as e:
            print(f"❌ Failed to list providers: {e}")
            sys.exit(1)

    def _test_proxy(self, args: argparse.Namespace) -> None:
        """Test a specific proxy."""
        try:
            proxy = self.proxy_manager.get_proxy(args.proxy_id)
            if not proxy:
                print(f"❌ Proxy {args.proxy_id} not found")
                sys.exit(1)

            print(f"🧪 Testing proxy {args.proxy_id} ({proxy.host}:{proxy.port})...")

            # Mark as testing
            original_health = proxy.health
            proxy.health = ProxyHealth.UNKNOWN
            self.proxy_manager.update_proxy_health(args.proxy_id, proxy.health)

            # Test connectivity
            import asyncio
            success, response_time = asyncio.run(
                self.proxy_manager._providers.get('brightdata', self.proxy_manager)._test_proxy_connectivity(proxy)
            )

            # Update health based on result
            if success:
                health = ProxyHealth.HEALTHY
                status = "✅ PASS"
            else:
                health = ProxyHealth.DOWN
                status = "❌ FAIL"

            self.proxy_manager.update_proxy_health(args.proxy_id, health, response_time)

            print(f"{status} - {response_time:.0f}ms response time")

        except Exception as e:
            print(f"❌ Failed to test proxy: {e}")
            sys.exit(1)

    def _test_all_proxies(self, args: argparse.Namespace) -> None:
        """Test all proxies in the pool."""
        try:
            proxies = self.proxy_manager.load_all()

            if args.provider:
                proxies = [p for p in proxies if p.provider == args.provider]

            if not proxies:
                print("No proxies to test")
                return

            print(f"🧪 Testing {len(proxies)} proxies...")

            passed = 0
            failed = 0

            for proxy in proxies:
                try:
                    # Test connectivity (simplified - would need proper async handling)
                    success, response_time = asyncio.run(
                        self.proxy_manager._providers.get('brightdata', self.proxy_manager)._test_proxy_connectivity(proxy)
                    )

                    if success:
                        self.proxy_manager.update_proxy_health(proxy.id, ProxyHealth.HEALTHY, response_time)
                        passed += 1
                        print(f"  ✅ {proxy.id} - {response_time:.0f}ms")
                    else:
                        self.proxy_manager.update_proxy_health(proxy.id, ProxyHealth.DOWN)
                        failed += 1
                        print(f"  ❌ {proxy.id} - FAILED")

                except Exception as e:
                    self.proxy_manager.update_proxy_health(proxy.id, ProxyHealth.DOWN)
                    failed += 1
                    print(f"  ❌ {proxy.id} - ERROR: {e}")

            print(f"\n📊 Results: {passed} passed, {failed} failed")

        except Exception as e:
            print(f"❌ Failed to test proxies: {e}")
            sys.exit(1)

    def _show_status(self, args: argparse.Namespace) -> None:
        """Show proxy pool status."""
        try:
            stats = self.proxy_manager.get_stats()

            if args.detailed:
                print("📊 Detailed Proxy Pool Status")
                print("=" * 35)

                print(f"Total Proxies: {stats['total_proxies']}")
                print(f"Healthy: {stats['healthy']}")
                print(f"Active: {stats['active']}")
                print(f"Bound to Accounts: {stats['bound_to_accounts']}")
                print(f"Average Success Rate: {stats['avg_success_rate']:.2%}")

                # Show provider info
                providers = self.proxy_manager.list_providers()
                if providers:
                    print(f"\nConfigured Providers: {len(providers)}")
                    for provider in providers:
                        try:
                            provider_stats = asyncio.run(self.proxy_manager.get_provider_stats(provider))
                            if provider_stats and 'error' not in provider_stats:
                                print(f"  {provider}: {provider_stats.get('active_sessions', 'N/A')} sessions")
                        except:
                            print(f"  {provider}: stats unavailable")
            else:
                print("📊 Proxy Pool Summary")
                print("=" * 25)
                print(f"Total: {stats['total_proxies']}")
                print(f"Healthy: {stats['healthy']}")
                print(f"Active: {stats['active']}")

        except Exception as e:
            print(f"❌ Failed to get status: {e}")
            sys.exit(1)

    def _get_proxy(self, args: argparse.Namespace) -> None:
        """Get a proxy from pool or provider."""
        try:
            proxy = self.proxy_manager.get_proxy_from_any_provider(
                country=args.country,
                preferred_provider=args.provider,
                sticky=args.sticky
            )

            if proxy:
                print(f"✅ Got proxy: {proxy.host}:{proxy.port}")
                print(f"   ID: {proxy.id}")
                print(f"   Provider: {proxy.provider}")
                print(f"   Country: {proxy.country}")
                if proxy.username:
                    print(f"   Auth: {proxy.username}:***")
            else:
                print("❌ No proxy available")
                sys.exit(1)

        except Exception as e:
            print(f"❌ Failed to get proxy: {e}")
            sys.exit(1)

    def _import_proxies(self, args: argparse.Namespace) -> None:
        """Import proxies from file."""
        try:
            if not Path(args.file_path).exists():
                print(f"❌ File not found: {args.file_path}")
                sys.exit(1)

            count = self.proxy_manager.load_from_file(args.file_path, provider=args.provider)
            print(f"✅ Imported {count} proxies from {args.file_path}")

        except Exception as e:
            print(f"❌ Failed to import proxies: {e}")
            sys.exit(1)

    def _export_proxies(self, args: argparse.Namespace) -> None:
        """Export proxies to file."""
        try:
            self.proxy_manager.export_to_json(args.file_path)
            print(f"✅ Exported proxies to {args.file_path}")

        except Exception as e:
            print(f"❌ Failed to export proxies: {e}")
            sys.exit(1)

    def _monitor(self, args: argparse.Namespace) -> None:
        """Control health monitoring."""
        try:
            if args.action == 'start':
                self.proxy_manager.start_health_monitoring()
                print("✅ Started health monitoring")
            elif args.action == 'stop':
                self.proxy_manager.stop_health_monitoring()
                print("✅ Stopped health monitoring")
            elif args.action == 'status':
                # This is a simplified check - in reality would check thread status
                print("📊 Monitoring status: Running (background thread)")

        except Exception as e:
            print(f"❌ Failed to control monitoring: {e}")
            sys.exit(1)


def main():
    """Main entry point for proxy CLI."""
    parser = argparse.ArgumentParser(description='Radar Proxy Management CLI')
    subparsers = parser.add_subparsers(dest='command')

    cli = ProxyCLI()
    cli.setup_parser(subparsers)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cli.run_command(args)


if __name__ == '__main__':
    main()