#!/usr/bin/env python3
"""
SSH Chat Server
Listens for incoming chat connections over SSH tunnel.
"""

import socket
import threading
import time
from datetime import datetime
import sys
import signal
import os

class ChatServer:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.running = False
        self.username = os.getenv('USER', 'Server')

    def start(self):
        """Start the chat server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True

            print(f"🚀 Chat Server gestartet auf {self.host}:{self.port}")
            print("Drücke Ctrl+C zum Beenden")

            # Signal handler für sauberes Beenden
            signal.signal(signal.SIGINT, self.stop)

            # Accept-Thread starten
            accept_thread = threading.Thread(target=self.accept_connections)
            accept_thread.daemon = True
            accept_thread.start()

            # Haupt-Loop für Server-Nachrichten
            self.server_loop()

        except Exception as e:
            print(f"❌ Server-Fehler: {e}")
            self.stop()

    def accept_connections(self):
        """Akzeptiert eingehende Verbindungen"""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"📱 Neue Verbindung von {client_address}")

                # Client-Handler starten
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()

            except OSError:
                # Socket wurde geschlossen
                break
            except Exception as e:
                if self.running:
                    print(f"❌ Accept-Fehler: {e}")

    def handle_client(self, client_socket, client_address):
        """Verarbeitet Nachrichten von einem Client"""
        self.clients.append(client_socket)

        try:
            # Willkommensnachricht
            welcome_msg = f"[{datetime.now().strftime('%H:%M:%S')}] {self.username}: Willkommen im Chat!\n"
            client_socket.send(welcome_msg.encode('utf-8'))

            while self.running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break

                    message = data.decode('utf-8').strip()
                    if message:
                        # Nachricht an alle Clients weiterleiten
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        formatted_msg = f"[{timestamp}] {self.username}: {message}\n"

                        print(f"📨 {formatted_msg.strip()}")  # Lokale Anzeige

                        # An alle anderen Clients senden
                        self.broadcast(formatted_msg, exclude_socket=client_socket)

                except ConnectionResetError:
                    break
                except Exception as e:
                    print(f"❌ Client-Handler Fehler: {e}")
                    break

        finally:
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()
            print(f"👋 Verbindung zu {client_address} beendet")

    def broadcast(self, message, exclude_socket=None):
        """Sendet Nachricht an alle Clients"""
        for client in self.clients:
            if client != exclude_socket:
                try:
                    client.send(message.encode('utf-8'))
                except:
                    # Client entfernen wenn senden fehlschlägt
                    if client in self.clients:
                        self.clients.remove(client)

    def server_loop(self):
        """Haupt-Loop für Server-Interaktion"""
        while self.running:
            try:
                # Server kann auch Nachrichten senden
                time.sleep(0.1)
            except KeyboardInterrupt:
                self.stop()

    def stop(self, signum=None, frame=None):
        """Stoppt den Server sauber"""
        print("\n🛑 Server wird beendet...")
        self.running = False

        # Alle Clients schließen
        for client in self.clients:
            try:
                client.close()
            except:
                pass

        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        print("✅ Server beendet")
        sys.exit(0)


def main():
    """Hauptfunktion"""
    import argparse

    parser = argparse.ArgumentParser(description='SSH Chat Server')
    parser.add_argument('--host', default='localhost', help='Host-Adresse (default: localhost)')
    parser.add_argument('--port', type=int, default=5000, help='Port (default: 5000)')

    args = parser.parse_args()

    server = ChatServer(host=args.host, port=args.port)
    server.start()


if __name__ == '__main__':
    main()