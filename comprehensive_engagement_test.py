#!/usr/bin/env python3
"""
Comprehensive Engagement Test Script

⚠️  WICHTIGE SICHERHEITSHINWEISE:
- Verwende NUR Test-Accounts, niemals persönliche Accounts!
- Starte mit minimalen Aktionen
- Überwache Erfolgsraten (>90% sollten normal sein)
- Stoppe sofort bei hohen Fehlerraten
- Respektiere Rate-Limits (30-60 Sekunden zwischen Aktionen)

Dieses Skript testet jede Engagement-Methode einmal mit echten Accounts.
"""

import time
import sys
from radar.browser import BrowserManager
from radar.engagement import EngagementManager

# ⚠️ KONFIGURATION - ÄNDERE DIESE URLS/USERNAMES!
TEST_TARGETS = {
    "instagram": {
        "like_url": "https://www.instagram.com/p/DC123456789/",  # ÄNDERE!
        "follow_username": "test_account_123",  # ÄNDERE!
        "comment_url": "https://www.instagram.com/p/DC123456789/",  # ÄNDERE!
        "comment_text": "Test comment from automation system 👋",
        "save_url": "https://www.instagram.com/p/DC123456789/",  # ÄNDERE!
    },
    "tiktok": {
        "like_url": "https://www.tiktok.com/@testuser/video/1234567890123456789",  # ÄNDERE!
        "follow_username": "test_creator",  # ÄNDERE!
        "comment_url": "https://www.tiktok.com/@testuser/video/1234567890123456789",  # ÄNDERE!
        "comment_text": "Test comment from automation 🎵",
        "save_url": "https://www.tiktok.com/@testuser/video/1234567890123456789",  # ÄNDERE!
    }
}

def print_header():
    """Druckt Sicherheitswarnungen und Header."""
    print("🚨" * 50)
    print("⚠️  WICHTIGE SICHERHEITSWARNUNGEN:")
    print("🚨" * 50)
    print("• Verwende NUR Test-Accounts!")
    print("• Niemals persönliche Accounts!")
    print("• Überwache Erfolgsraten (>90% normal)")
    print("• Stoppe bei Fehlerraten >10%")
    print("• 30-60 Sekunden zwischen Aktionen")
    print("• Bei Problemen: Sofort stoppen!")
    print("🚨" * 50)
    print()

def confirm_execution():
    """Fragt nach Bestätigung vor Ausführung."""
    print("🎯 Dieses Skript wird folgende Aktionen ausführen:")
    print("   Instagram: Like, Follow, Comment, Save")
    print("   TikTok: Like, Follow, Comment, Save")
    print()
    print("💡 Empfohlen: Starte mit einem Test-Account")
    print()

    response = input("✅ Fortfahren? (tippe 'JA' in Großbuchstaben): ")
    if response != "JA":
        print("❌ Abbruch durch User")
        sys.exit(0)

def test_instagram_engagement():
    """Testet alle Instagram Engagement-Methoden."""
    print("\n📸 Teste Instagram Engagement...")

    try:
        with BrowserManager() as manager:
            engagement_manager = EngagementManager()

            if not engagement_manager.initialize_instagram(manager, "ig_session"):
                print("❌ Instagram-Initialisierung fehlgeschlagen")
                return False

            # Authentifizierung prüfen
            print("🔐 Prüfe Instagram-Authentifizierung...")
            if not engagement_manager.instagram_automator.login("", "", headless=True):
                print("❌ Instagram-Authentifizierung fehlgeschlagen")
                return False

            print("✅ Instagram-Authentifizierung erfolgreich!")

            results = []

            # 1. Like Test
            print("👍 Teste Like-Funktion...")
            time.sleep(2)
            result = engagement_manager.instagram_automator.like_post(TEST_TARGETS["instagram"]["like_url"])
            results.append(("Like", result))
            print(f"   {'✅' if result.success else '❌'} {result.message}")

            # Sicherheitsdelay
            print("⏱️  Warte 30 Sekunden...")
            time.sleep(30)

            # 2. Follow Test
            print("👥 Teste Follow-Funktion...")
            time.sleep(2)
            result = engagement_manager.instagram_automator.follow_user(TEST_TARGETS["instagram"]["follow_username"])
            results.append(("Follow", result))
            print(f"   {'✅' if result.success else '❌'} {result.message}")

            # Sicherheitsdelay
            print("⏱️  Warte 45 Sekunden...")
            time.sleep(45)

            # 3. Comment Test
            print("💬 Teste Comment-Funktion...")
            time.sleep(2)
            result = engagement_manager.instagram_automator.comment_on_post(
                TEST_TARGETS["instagram"]["comment_url"],
                TEST_TARGETS["instagram"]["comment_text"]
            )
            results.append(("Comment", result))
            print(f"   {'✅' if result.success else '❌'} {result.message}")

            # Sicherheitsdelay
            print("⏱️  Warte 60 Sekunden...")
            time.sleep(60)

            # 4. Save Test
            print("💾 Teste Save-Funktion...")
            time.sleep(2)
            result = engagement_manager.instagram_automator.save_post(TEST_TARGETS["instagram"]["save_url"])
            results.append(("Save", result))
            print(f"   {'✅' if result.success else '❌'} {result.message}")

            # Zusammenfassung
            successful = sum(1 for _, result in results if result.success)
            print(f"\n📊 Instagram Ergebnisse: {successful}/{len(results)} erfolgreich")

            for action, result in results:
                status = "✅" if result.success else "❌"
                print(f"   {status} {action}: {result.message}")

            return successful >= 3  # Mindestens 75% Erfolg

    except Exception as e:
        print(f"❌ Instagram-Test fehlgeschlagen: {e}")
        return False

def test_tiktok_engagement():
    """Testet alle TikTok Engagement-Methoden."""
    print("\n🎵 Teste TikTok Engagement...")

    try:
        with BrowserManager() as manager:
            engagement_manager = EngagementManager()

            if not engagement_manager.initialize_tiktok(manager, "tiktok_session"):
                print("❌ TikTok-Initialisierung fehlgeschlagen")
                return False

            # Authentifizierung prüfen
            print("🔐 Prüfe TikTok-Authentifizierung...")
            if not engagement_manager.tiktok_automator.login(headless=True):
                print("❌ TikTok-Authentifizierung fehlgeschlagen")
                return False

            print("✅ TikTok-Authentifizierung erfolgreich!")

            results = []

            # 1. Like Test
            print("👍 Teste Like-Funktion...")
            time.sleep(2)
            result = engagement_manager.tiktok_automator.like_video(TEST_TARGETS["tiktok"]["like_url"])
            results.append(("Like", result))
            print(f"   {'✅' if result.success else '❌'} {result.message}")

            # Sicherheitsdelay
            print("⏱️  Warte 30 Sekunden...")
            time.sleep(30)

            # 2. Follow Test
            print("👥 Teste Follow-Funktion...")
            time.sleep(2)
            result = engagement_manager.tiktok_automator.follow_creator(TEST_TARGETS["tiktok"]["follow_username"])
            results.append(("Follow", result))
            print(f"   {'✅' if result.success else '❌'} {result.message}")

            # Sicherheitsdelay
            print("⏱️  Warte 45 Sekunden...")
            time.sleep(45)

            # 3. Comment Test
            print("💬 Teste Comment-Funktion...")
            time.sleep(2)
            result = engagement_manager.tiktok_automator.comment_on_video(
                TEST_TARGETS["tiktok"]["comment_url"],
                TEST_TARGETS["tiktok"]["comment_text"]
            )
            results.append(("Comment", result))
            print(f"   {'✅' if result.success else '❌'} {result.message}")

            # Sicherheitsdelay
            print("⏱️  Warte 60 Sekunden...")
            time.sleep(60)

            # 4. Save Test
            print("💾 Teste Save-Funktion...")
            time.sleep(2)
            result = engagement_manager.tiktok_automator.save_video(TEST_TARGETS["tiktok"]["save_url"])
            results.append(("Save", result))
            print(f"   {'✅' if result.success else '❌'} {result.message}")

            # Zusammenfassung
            successful = sum(1 for _, result in results if result.success)
            print(f"\n📊 TikTok Ergebnisse: {successful}/{len(results)} erfolgreich")

            for action, result in results:
                status = "✅" if result.success else "❌"
                print(f"   {status} {action}: {result.message}")

            return successful >= 3  # Mindestens 75% Erfolg

    except Exception as e:
        print(f"❌ TikTok-Test fehlgeschlagen: {e}")
        return False

def main():
    """Hauptfunktion für umfassende Engagement-Tests."""
    print_header()

    # Konfiguration anzeigen
    print("🎯 Test-Konfiguration:")
    print("   Instagram Like URL:", TEST_TARGETS["instagram"]["like_url"])
    print("   Instagram Follow User:", TEST_TARGETS["instagram"]["follow_username"])
    print("   TikTok Like URL:", TEST_TARGETS["tiktok"]["like_url"])
    print("   TikTok Follow User:", TEST_TARGETS["tiktok"]["follow_username"])
    print()

    # WICHTIG: Bestätigung einholen
    confirm_execution()

    print("\n🚀 Starte umfassende Engagement-Tests...")
    print("⏰ Geschätzte Dauer: 5-8 Minuten")
    print()

    # Tests ausführen
    ig_success = test_instagram_engagement()
    tt_success = test_tiktok_engagement()

    # Finale Zusammenfassung
    print("\n" + "="*50)
    print("🎉 TESTS ABGESCHLOSSEN")
    print("="*50)

    print("📊 Endergebnisse:")
    print(f"   Instagram: {'✅ Erfolgreich' if ig_success else '❌ Fehlgeschlagen'}")
    print(f"   TikTok: {'✅ Erfolgreich' if tt_success else '❌ Fehlgeschlagen'}")

    if ig_success and tt_success:
        print("\n🎯 ALLE TESTS ERFOLGREICH!")
        print("💡 Das Engagement-System funktioniert perfekt mit echten Accounts!")
    elif ig_success or tt_success:
        print("\n⚠️ Teilweise erfolgreich - ein Platform funktioniert")
    else:
        print("\n❌ Alle Tests fehlgeschlagen - Überprüfe Konfiguration")

    print("\n🔒 Sicherheitshinweise:")
    print("• Überwache Account-Status in den nächsten Tagen")
    print("• Bei ungewöhnlicher Aktivität: Sofort stoppen")
    print("• Verwende weiterhin Rate-Limits")
    print("• Regelmäßige Pausen einlegen")

if __name__ == "__main__":
    main()