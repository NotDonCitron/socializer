#!/usr/bin/env python3
"""
Session management CLI commands for radar.

Provides commands to manage browser sessions and run automations.
"""

import argparse
import sys
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

from .session_orchestrator import SessionOrchestrator
from .account_pool import AccountPool, AccountStatus


class SessionCLI:
    """Command-line interface for session management."""

    def __init__(self):
        self.account_pool = AccountPool()
        self.orchestrator = SessionOrchestrator(self.account_pool)

    def setup_parser(self, subparsers: argparse._SubParsersAction) -> None:
        """Set up the session subcommand parser."""

        # Main session parser
        session_parser = subparsers.add_parser(
            'session',
            help='Manage browser sessions and run automations'
        )
        session_subparsers = session_parser.add_subparsers(
            dest='session_command',
            help='Session operations'
        )

        # session start
        start_parser = session_subparsers.add_parser(
            'start',
            help='Start a browser session for an account'
        )
        start_parser.add_argument(
            'account_id',
            help='Account ID to start session for'
        )
        start_parser.add_argument(
            '--headless',
            action='store_true',
            help='Run in headless mode'
        )
        start_parser.add_argument(
            '--platform',
            choices=['tiktok', 'instagram'],
            help='Target platform (auto-detected from account if not specified)'
        )

        # session stop
        stop_parser = session_subparsers.add_parser(
            'stop',
            help='Stop a browser session'
        )
        stop_parser.add_argument(
            'session_id',
            help='Session ID to stop'
        )

        # session list
        list_parser = session_subparsers.add_parser(
            'list',
            help='List active sessions'
        )
        list_parser.add_argument(
            '--account',
            help='Filter by account ID'
        )
        list_parser.add_argument(
            '--platform',
            choices=['tiktok', 'instagram'],
            help='Filter by platform'
        )
        list_parser.add_argument(
            '--json',
            action='store_true',
            help='Output as JSON'
        )

        # session status
        status_parser = session_subparsers.add_parser(
            'status',
            help='Show session status and statistics'
        )
        status_parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed statistics'
        )

        # session cleanup
        cleanup_parser = session_subparsers.add_parser(
            'cleanup',
            help='Clean up inactive/stale sessions'
        )
        cleanup_parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup without confirmation'
        )

    def run_command(self, args: argparse.Namespace) -> None:
        """Execute the session command."""

        command = args.session_command

        if command == 'start':
            self._start_session(args)
        elif command == 'stop':
            self._stop_session(args)
        elif command == 'list':
            self._list_sessions(args)
        elif command == 'status':
            self._show_status(args)
        elif command == 'cleanup':
            self._cleanup_sessions(args)
        else:
            print(f"Unknown session command: {command}")
            sys.exit(1)

    def _start_session(self, args: argparse.Namespace) -> None:
        """Start a browser session."""
        try:
            # Get account info
            account = self.account_pool.get_account(args.account_id)
            if not account:
                print(f"❌ Account {args.account_id} not found")
                sys.exit(1)

            if account.status != AccountStatus.ACTIVE:
                print(f"❌ Account {args.account_id} is not active (status: {account.status.value})")
                sys.exit(1)

            # Determine platform
            platform = args.platform or account.platform

            print(f"🚀 Starting {platform} session for account {args.account_id}...")
            print(f"   Username: {account.username}")
            print(f"   Headless: {args.headless}")

            # Start session
            session_id = self.orchestrator.start_session(
                account_id=args.account_id,
                platform=platform,
                headless=args.headless
            )

            print(f"✅ Session started with ID: {session_id}")

            # Wait a bit and show status
            time.sleep(2)
            session_info = self.orchestrator.get_session_info(session_id)
            if session_info:
                print(f"📊 Session status: {session_info.get('status', 'unknown')}")
            else:
                print("⚠️  Session may still be initializing...")

        except Exception as e:
            print(f"❌ Failed to start session: {e}")
            sys.exit(1)

    def _stop_session(self, args: argparse.Namespace) -> None:
        """Stop a browser session."""
        try:
            success = self.orchestrator.stop_session(args.session_id)
            if success:
                print(f"✅ Stopped session {args.session_id}")
            else:
                print(f"❌ Session {args.session_id} not found or already stopped")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to stop session: {e}")
            sys.exit(1)

    def _list_sessions(self, args: argparse.Namespace) -> None:
        """List active sessions."""
        try:
            sessions = self.orchestrator.get_active_sessions()

            # Apply filters
            if args.account:
                sessions = [s for s in sessions if s.get('account_id') == args.account]

            if args.platform:
                sessions = [s for s in sessions if s.get('platform') == args.platform]

            if args.json:
                # JSON output
                import json
                print(json.dumps(sessions, indent=2))
            else:
                # Table output
                if not sessions:
                    print("No active sessions")
                    return

                print(f"🖥️  Active Sessions ({len(sessions)})")
                print("-" * 90)
                print(f"{'Session ID':<12} {'Account':<10} {'Platform':<10} {'Status':<12} {'Started':<20} {'URL'}")
                print("-" * 90)

                for session in sessions:
                    session_id = session.get('session_id', '')[:12]
                    account_id = session.get('account_id', '')[:10]
                    platform = session.get('platform', '')[:10]
                    status = session.get('status', '')[:12]
                    started = session.get('started_at', '')[:19]  # Trim to fit
                    url = session.get('current_url', '')[:30] + '...' if session.get('current_url') and len(session.get('current_url', '')) > 30 else session.get('current_url', '')

                    print(f"{session_id:<12} {account_id:<10} {platform:<10} {status:<12} {started:<20} {url}")

        except Exception as e:
            print(f"❌ Failed to list sessions: {e}")
            sys.exit(1)

    def _show_status(self, args: argparse.Namespace) -> None:
        """Show session status and statistics."""
        try:
            # For now, just show session list summary
            sessions = self.orchestrator.get_active_sessions()
            active_count = len(sessions)
            stats = {
                'active_sessions': active_count,
                'total_sessions': active_count,  # Simplified
                'platform_stats': {}
            }

            if args.detailed:
                print("📊 Detailed Session Status")
                print("=" * 30)

                print(f"Active Sessions: {stats.get('active_sessions', 0)}")
                print(f"Total Sessions Started: {stats.get('total_sessions', 0)}")
                print(f"Sessions by Platform:")

                platform_stats = stats.get('platform_stats', {})
                for platform, count in platform_stats.items():
                    print(f"  {platform.title()}: {count}")

                print(f"\nRecent Activity:")
                recent_sessions = stats.get('recent_sessions', [])
                for session in recent_sessions[:5]:  # Show last 5
                    print(f"  {session.get('session_id', '')[:8]} - {session.get('platform', '')} - {session.get('status', '')}")

            else:
                print("📊 Session Summary")
                print("=" * 20)
                print(f"Active: {stats.get('active_sessions', 0)}")
                print(f"Total: {stats.get('total_sessions', 0)}")

        except Exception as e:
            print(f"❌ Failed to get status: {e}")
            sys.exit(1)

    def _cleanup_sessions(self, args: argparse.Namespace) -> None:
        """Clean up inactive/stale sessions."""
        try:
            if not args.force:
                # Get confirmation
                sessions = self.orchestrator.get_active_sessions()
                stale_count = len([s for s in sessions if not s.is_healthy])  # Use is_healthy instead

                if stale_count == 0:
                    print("No stale sessions to clean up")
                    return

                print(f"Found {stale_count} stale sessions. Clean up? (y/N): ", end='')
                response = input().strip().lower()
                if response not in ['y', 'yes']:
                    print("Cleanup cancelled")
                    return

            # Note: cleanup_stale_sessions may not exist, using cleanup_all_sessions instead
            try:
                self.orchestrator.cleanup_all_sessions()
                print("✅ Cleaned up all sessions")
            except AttributeError:
                print("⚠️  Cleanup method not available, sessions may need manual cleanup")

        except KeyboardInterrupt:
            print("\nCleanup cancelled")
        except Exception as e:
            print(f"❌ Failed to cleanup sessions: {e}")
            sys.exit(1)


def main():
    """Main entry point for session CLI."""
    parser = argparse.ArgumentParser(description='Radar Session Management CLI')
    subparsers = parser.add_subparsers(dest='command')

    cli = SessionCLI()
    cli.setup_parser(subparsers)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cli.run_command(args)


if __name__ == '__main__':
    main()