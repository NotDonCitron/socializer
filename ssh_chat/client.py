#!/usr/bin/env python3
"""
SSH Chat Client
Connects to chat server over SSH tunnel.
"""

import socket
import threading
import time
import sys
import signal
import os
from datetime import datetime

class ChatClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.client_socket = None
        self.running = False
        self.username = os.getenv('USER', 'Client')

    def connect(self):
        """Verbindet mit dem Chat-Server"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.running = True

            print(f"🔗 Verbunden mit {self.host}:{self.port}")
            print("Drücke Ctrl+C zum Beenden")

            # Signal handler für sauberes Beenden
            signal.signal(signal.SIGINT, self.stop)

            # Receive-Thread starten
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()

            # Haupt-Loop für Eingabe
            self.input_loop()

        except ConnectionRefusedError:
            print(f"❌ Verbindung zu {self.host}:{self.port} fehlgeschlagen")
            print("Stellen Sie sicher, dass der Server läuft und der SSH-Tunnel aktiv ist")
            return False
        except Exception as e:
            print(f"❌ Verbindungsfehler: {e}")
            return False

        return True

    def receive_messages(self):
        """Empfängt Nachrichten vom Server"""
        while self.running:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break

                message = data.decode('utf-8')
                print(message.strip())  # Nachricht anzeigen

            except ConnectionResetError:
                print("❌ Verbindung zum Server verloren")
                break
            except Exception as e:
                if self.running:
                    print(f"❌ Receive-Fehler: {e}")
                break

        self.stop()

    def send_message(self, message):
        """Sendet Nachricht an Server"""
        if self.client_socket and self.running:
            try:
                self.client_socket.send(message.encode('utf-8'))
                return True
            except Exception as e:
                print(f"❌ Send-Fehler: {e}")
                return False
        return False

    def input_loop(self):
        """Haupt-Loop für Benutzereingabe"""
        print("💬 Chat ist bereit! Tippe deine Nachrichten:")

        while self.running:
            try:
                # Eingabe ohne Blockierung
                message = input()

                if message.strip():
                    if not self.send_message(message):
                        break

            except EOFError:
                # Ctrl+D gedrückt
                break
            except KeyboardInterrupt:
                # Ctrl+C wird vom Signal-Handler behandelt
                break

    def stop(self, signum=None, frame=None):
        """Stoppt den Client sauber"""
        print("\n👋 Chat wird beendet...")
        self.running = False

        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass

        print("✅ Client beendet")
        sys.exit(0)


def main():
    """Hauptfunktion"""
    import argparse

    parser = argparse.ArgumentParser(description='SSH Chat Client')
    parser.add_argument('--host', default='localhost', help='Server-Host (default: localhost)')
    parser.add_argument('--port', type=int, default=5000, help='Server-Port (default: 5000)')

    args = parser.parse_args()

    print("🚀 Starte SSH Chat Client...")
    print(f"Verbinde mit {args.host}:{args.port}")
    print("Stellen Sie sicher, dass der SSH-Tunnel aktiv ist!")
    print()

    client = ChatClient(host=args.host, port=args.port)

    if not client.connect():
        sys.exit(1)


if __name__ == '__main__':
    main()