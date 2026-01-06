#!/usr/bin/env python3
"""
Account management CLI commands for radar.

Provides commands to manage social media accounts in the pool.
"""

import argparse
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path

from .account_pool import AccountPool, AccountStatus, Account
from .account_scheduler import AccountScheduler


class AccountCLI:
    """Command-line interface for account management."""

    def __init__(self):
        self.account_pool = AccountPool()
        self.scheduler = AccountScheduler(self.account_pool)

    def setup_parser(self, subparsers: argparse._SubParsersAction) -> None:
        """Set up the account subcommand parser."""

        # Main accounts parser
        accounts_parser = subparsers.add_parser(
            'accounts',
            help='Manage social media accounts'
        )
        accounts_subparsers = accounts_parser.add_subparsers(
            dest='accounts_command',
            help='Account operations'
        )

        # accounts add
        add_parser = accounts_subparsers.add_parser(
            'add',
            help='Add a new account to the pool'
        )
        add_parser.add_argument(
            'platform',
            choices=['tiktok', 'instagram'],
            help='Social media platform'
        )
        add_parser.add_argument(
            'username',
            help='Account username'
        )
        add_parser.add_argument(
            '--password',
            help='Account password (prompt if not provided)'
        )
        add_parser.add_argument(
            '--email',
            help='Associated email address'
        )
        add_parser.add_argument(
            '--proxy-id',
            help='Bind to specific proxy ID'
        )
        add_parser.add_argument(
            '--tags',
            nargs='*',
            help='Tags for account categorization'
        )

        # accounts remove
        remove_parser = accounts_subparsers.add_parser(
            'remove',
            help='Remove an account from the pool'
        )
        remove_parser.add_argument(
            'account_id',
            help='Account ID to remove'
        )

        # accounts list
        list_parser = accounts_subparsers.add_parser(
            'list',
            help='List all accounts'
        )
        list_parser.add_argument(
            '--platform',
            choices=['tiktok', 'instagram'],
            help='Filter by platform'
        )
        list_parser.add_argument(
            '--status',
            choices=['active', 'inactive', 'banned', 'suspended'],
            help='Filter by status'
        )
        list_parser.add_argument(
            '--json',
            action='store_true',
            help='Output as JSON'
        )

        # accounts status
        status_parser = accounts_subparsers.add_parser(
            'status',
            help='Show account pool status'
        )
        status_parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed statistics'
        )

        # accounts update
        update_parser = accounts_subparsers.add_parser(
            'update',
            help='Update account information'
        )
        update_parser.add_argument(
            'account_id',
            help='Account ID to update'
        )
        update_parser.add_argument(
            '--status',
            choices=['active', 'inactive', 'banned', 'suspended'],
            help='Update account status'
        )
        update_parser.add_argument(
            '--tags',
            nargs='*',
            help='Update account tags'
        )
        update_parser.add_argument(
            '--proxy-id',
            help='Rebind to different proxy'
        )

        # accounts bind-proxy
        bind_parser = accounts_subparsers.add_parser(
            'bind-proxy',
            help='Bind account to a proxy'
        )
        bind_parser.add_argument(
            'account_id',
            help='Account ID'
        )
        bind_parser.add_argument(
            'proxy_id',
            help='Proxy ID to bind'
        )

        # accounts unbind-proxy
        unbind_parser = accounts_subparsers.add_parser(
            'unbind-proxy',
            help='Remove proxy binding from account'
        )
        unbind_parser.add_argument(
            'account_id',
            help='Account ID'
        )

    def run_command(self, args: argparse.Namespace) -> None:
        """Execute the account command."""

        command = args.accounts_command

        if command == 'add':
            self._add_account(args)
        elif command == 'remove':
            self._remove_account(args)
        elif command == 'list':
            self._list_accounts(args)
        elif command == 'status':
            self._show_status(args)
        elif command == 'update':
            self._update_account(args)
        elif command == 'bind-proxy':
            self._bind_proxy(args)
        elif command == 'unbind-proxy':
            self._unbind_proxy(args)
        else:
            print(f"Unknown accounts command: {command}")
            sys.exit(1)

    def _add_account(self, args: argparse.Namespace) -> None:
        """Add a new account to the pool."""
        from uuid import uuid4

        # Get password if not provided
        password = args.password
        if not password:
            import getpass
            password = getpass.getpass(f"Password for {args.username}: ")
            if not password:
                print("❌ Password is required")
                sys.exit(1)

        # Create account object (generate ID)
        account_id = str(uuid4())[:8]
        account = Account(
            id=account_id,
            platform=args.platform,
            username=args.username,
            tags=set(args.tags or [])
        )

        # Store password in custom_data (in real implementation this would be encrypted)
        account.custom_data['password'] = password
        if args.email:
            account.custom_data['email'] = args.email
        if args.proxy_id:
            # This should be handled by binding after account creation
            pass

        try:
            self.account_pool.add_account(account)

            # Bind proxy if specified
            if args.proxy_id:
                self.account_pool.bind_to_proxy(account_id, args.proxy_id)

            print(f"✅ Added account {args.username} ({args.platform}) with ID: {account_id}")
        except Exception as e:
            print(f"❌ Failed to add account: {e}")
            sys.exit(1)

    def _remove_account(self, args: argparse.Namespace) -> None:
        """Remove an account from the pool."""
        try:
            success = self.account_pool.remove_account(args.account_id)
            if success:
                print(f"✅ Removed account {args.account_id}")
            else:
                print(f"❌ Account {args.account_id} not found")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to remove account: {e}")
            sys.exit(1)

    def _list_accounts(self, args: argparse.Namespace) -> None:
        """List accounts with optional filtering."""
        try:
            # Get all accounts (load from DB first)
            # Note: list_accounts() should load from DB, but let's be explicit
            self.account_pool.load_all_accounts() if hasattr(self.account_pool, 'load_all_accounts') else None
            accounts = self.account_pool.list_accounts()

            # Apply filters
            if args.platform:
                accounts = [a for a in accounts if a.platform == args.platform]

            if args.status:
                accounts = [a for a in accounts if a.status.value == args.status]

            if args.json:
                # JSON output
                import json
                account_dicts = []
                for account in accounts:
                    account_dict = {
                        'id': account.id,
                        'platform': account.platform,
                        'username': account.username,
                        'email': account.email,
                        'status': account.status.value,
                        'proxy_id': account.proxy_id,
                        'tags': account.tags,
                        'created_at': account.created_at.isoformat() if account.created_at else None,
                        'last_used': account.last_used.isoformat() if account.last_used else None,
                        'success_rate': account.success_rate,
                        'session_count': account.session_count
                    }
                    account_dicts.append(account_dict)

                print(json.dumps(account_dicts, indent=2))
            else:
                # Table output
                if not accounts:
                    print("No accounts found")
                    return

                print(f"📋 Accounts ({len(accounts)})")
                print("-" * 80)
                print(f"{'ID':<8} {'Platform':<10} {'Username':<20} {'Status':<10} {'Proxy':<10} {'Tags'}")
                print("-" * 80)

                for account in accounts:
                    tags_str = ','.join(account.tags) if account.tags else ''
                    proxy_id = account.proxy_id[:8] + '...' if account.proxy_id and len(account.proxy_id) > 8 else (account.proxy_id or '')
                    print(f"{account.id:<8} {account.platform:<10} {account.username:<20} {account.status.value:<10} {proxy_id:<10} {tags_str}")

        except Exception as e:
            print(f"❌ Failed to list accounts: {e}")
            sys.exit(1)

    def _show_status(self, args: argparse.Namespace) -> None:
        """Show account pool status."""
        try:
            stats = self.account_pool.get_pool_stats()

            if args.detailed:
                print("📊 Detailed Account Pool Status")
                print("=" * 40)

                for platform, platform_stats in stats.items():
                    print(f"\n🏷️  {platform.upper()}")
                    print(f"   Total: {platform_stats['total']}")
                    print(f"   Active: {platform_stats['active']}")
                    print(f"   Banned: {platform_stats['banned']}")
                    print(f"   Suspended: {platform_stats['suspended']}")
                    print(f"   Avg Success Rate: {platform_stats['avg_success_rate']:.2%}")
                    print(f"   Total Sessions: {platform_stats['total_sessions']}")

                    if platform_stats['recent_sessions'] > 0:
                        print(f"   Recent Sessions (24h): {platform_stats['recent_sessions']}")
            else:
                print("📊 Account Pool Summary")
                print("=" * 30)

                total_accounts = stats.get('total_accounts', 0)
                active_accounts = stats.get('active_accounts', 0)
                quarantined_accounts = stats.get('quarantined_accounts', 0)

                print(f"Total Accounts: {total_accounts}")
                print(f"Active Accounts: {active_accounts}")
                print(f"Quarantined Accounts: {quarantined_accounts}")

                platform_stats = stats.get('platform_stats', {})
                for platform, plat_stats in platform_stats.items():
                    if plat_stats['total'] > 0:
                        print(f"  {platform.title()}: {plat_stats['active']}/{plat_stats['total']} active")

        except Exception as e:
            print(f"❌ Failed to get status: {e}")
            sys.exit(1)

    def _update_account(self, args: argparse.Namespace) -> None:
        """Update account information."""

        updates = {}

        if args.status:
            updates['status'] = AccountStatus(args.status)

        if args.tags is not None:
            updates['tags'] = args.tags

        if args.proxy_id:
            updates['proxy_id'] = args.proxy_id

        if not updates:
            print("❌ No updates specified")
            sys.exit(1)

        try:
            success = self.account_pool.update_account(args.account_id, **updates)
            if success:
                print(f"✅ Updated account {args.account_id}")
            else:
                print(f"❌ Account {args.account_id} not found")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to update account: {e}")
            sys.exit(1)

    def _bind_proxy(self, args: argparse.Namespace) -> None:
        """Bind account to a proxy."""
        try:
            success = self.account_pool.bind_to_proxy(args.account_id, args.proxy_id)
            if success:
                print(f"✅ Bound account {args.account_id} to proxy {args.proxy_id}")
            else:
                print(f"❌ Account {args.account_id} or proxy {args.proxy_id} not found")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to bind proxy: {e}")
            sys.exit(1)

    def _unbind_proxy(self, args: argparse.Namespace) -> None:
        """Remove proxy binding from account."""
        try:
            success = self.account_pool.unbind_proxy(args.account_id)
            if success:
                print(f"✅ Unbound proxy from account {args.account_id}")
            else:
                print(f"❌ Account {args.account_id} not found")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to unbind proxy: {e}")
            sys.exit(1)


def main():
    """Main entry point for account CLI."""
    parser = argparse.ArgumentParser(description='Radar Account Management CLI')
    subparsers = parser.add_subparsers(dest='command')

    cli = AccountCLI()
    cli.setup_parser(subparsers)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cli.run_command(args)


if __name__ == '__main__':
    main()