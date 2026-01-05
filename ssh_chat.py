#!/usr/bin/env python3
"""
SSH Chat - Terminal-basierter Chat über SSH zwischen zwei Laptops
"""

import argparse
import subprocess
import sys
import time
import os
from ssh_chat.server import ChatServer
from ssh_chat.client import ChatClient

def start_server(host='localhost', port=5000):
    """Startet den Chat-Server"""
    print("🚀 Starte Chat-Server...")
    server = ChatServer(host=host, port=port)
    server.start()

def start_client(host='localhost', port=5000):
    """Startet den Chat-Client"""
    print("🔗 Starte Chat-Client...")
    client = ChatClient(host=host, port=port)
    if not client.connect():
        print("❌ Verbindung fehlgeschlagen")
        return False
    return True

def setup_ssh_tunnel(remote_host, remote_user, remote_port=5000, local_port=5000):
    """Richtet SSH-Tunnel ein"""
    print(f"🔒 Richte SSH-Tunnel ein: {remote_user}@{remote_host}")

    # SSH-Tunnel-Befehl
    tunnel_cmd = [
        'ssh',
        '-L', f'{local_port}:localhost:{remote_port}',
        '-N',  # Nur Tunnel, kein Command
        f'{remote_user}@{remote_host}'
    ]

    try:
        print(f"Starte Tunnel: {' '.join(tunnel_cmd)}")
        process = subprocess.Popen(tunnel_cmd)
        time.sleep(2)  # Warten bis Tunnel steht

        if process.poll() is None:
            print("✅ SSH-Tunnel aktiv")
            return process
        else:
            print("❌ SSH-Tunnel fehlgeschlagen")
            return None

    except Exception as e:
        print(f"❌ Tunnel-Fehler: {e}")
        return None

def main():
    """Hauptfunktion"""
    parser = argparse.ArgumentParser(
        description='SSH Chat - Terminal Chat über SSH',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:

  # Server starten (auf deinem Laptop)
  python ssh_chat.py server

  # Client starten (auf deinem Laptop, verbindet sich zu Freund)
  python ssh_chat.py client --host localhost --port 5000

  # SSH-Tunnel + Client (empfohlen)
  python ssh_chat.py tunnel-client --remote-host 192.168.1.100 --remote-user freund

  # Beide Modi kombinieren
  python ssh_chat.py both --remote-host 192.168.1.100 --remote-user freund
        """
    )

    parser.add_argument('mode', choices=['server', 'client', 'tunnel-client', 'both'],
                       help='Modus: server (hört), client (verbindet), tunnel-client (SSH-Tunnel + Client), both (Server + Tunnel-Client)')

    parser.add_argument('--host', default='localhost', help='Server-Host (default: localhost)')
    parser.add_argument('--port', type=int, default=5000, help='Port (default: 5000)')
    parser.add_argument('--remote-host', help='IP/Host des anderen Laptops für SSH-Tunnel')
    parser.add_argument('--remote-user', help='Benutzername auf dem anderen Laptop')
    parser.add_argument('--remote-port', type=int, default=5000, help='Port auf dem anderen Laptop (default: 5000)')

    args = parser.parse_args()

    print("💬 SSH Chat System")
    print("=" * 30)

    if args.mode == 'server':
        # Nur Server starten
        start_server(host=args.host, port=args.port)

    elif args.mode == 'client':
        # Nur Client starten
        if not start_client(host=args.host, port=args.port):
            sys.exit(1)

    elif args.mode == 'tunnel-client':
        # SSH-Tunnel + Client
        if not args.remote_host or not args.remote_user:
            print("❌ --remote-host und --remote-user erforderlich für tunnel-client Modus")
            sys.exit(1)

        print(f"🔧 Erstelle SSH-Tunnel zu {args.remote_user}@{args.remote_host}...")

        # SSH-Tunnel starten
        tunnel_process = setup_ssh_tunnel(
            args.remote_host,
            args.remote_user,
            args.remote_port,
            args.port
        )

        if tunnel_process:
            print("🚀 Starte Client...")
            if not start_client(host='localhost', port=args.port):
                tunnel_process.terminate()
                sys.exit(1)
        else:
            print("❌ Tunnel-Setup fehlgeschlagen")
            sys.exit(1)

    elif args.mode == 'both':
        # Server + SSH-Tunnel-Client (für bidirektionale Kommunikation)
        if not args.remote_host or not args.remote_user:
            print("❌ --remote-host und --remote-user erforderlich für both Modus")
            sys.exit(1)

        print("🔄 Starte bidirektionale Kommunikation...")
        print("Server läuft lokal, Client verbindet sich über SSH-Tunnel")

        # SSH-Tunnel für Client starten
        tunnel_process = setup_ssh_tunnel(
            args.remote_host,
            args.remote_user,
            args.remote_port,
            args.port
        )

        if tunnel_process:
            # Server in eigenem Thread starten
            import threading
            server_thread = threading.Thread(
                target=start_server,
                args=(args.host, args.port)
            )
            server_thread.daemon = True
            server_thread.start()

            time.sleep(1)  # Server starten lassen

            # Client starten
            if not start_client(host='localhost', port=args.port):
                tunnel_process.terminate()
                sys.exit(1)
        else:
            print("❌ Setup fehlgeschlagen")
            sys.exit(1)

if __name__ == '__main__':
    main()