#!/usr/bin/env python3
"""
Quick Web Fetch Examples

Demonstriert verschiedene Möglichkeiten, Web-Inhalte mit dem Radar-System zu fetchen.
"""

import asyncio
from radar.sources import webpage_diff, github
from radar.models import SourceConfig

async def fetch_github_releases_example():
    """Beispiel: GitHub Releases fetchen."""
    print("📦 GitHub Releases Beispiel:")

    # Beispiel für ein beliebtes Repo
    source_config = SourceConfig(
        id="example_repo",
        type="github_releases",
        repo="microsoft/vscode",
        tags=["editor", "ide"]
    )

    try:
        # Fetch die letzten Releases
        releases = await github.fetch_releases(source_config, token="")

        print(f"✅ Gefunden: {len(releases)} Releases")
        for i, release in enumerate(releases[:3]):  # Zeige nur die ersten 3
            print(f"   {i+1}. {release.title} ({release.external_id})")
            print(f"      URL: {release.url}")
            print(f"      Datum: {release.published_at}")
            print()

    except Exception as e:
        print(f"❌ Fehler: {e}")

async def fetch_webpage_example():
    """Beispiel: Webseite fetchen."""
    print("🌐 Webseite Fetch Beispiel:")

    source_config = SourceConfig(
        id="example_webpage",
        type="webpage_diff",
        url="https://github.com/trending",
        tags=["trending", "github"]
    )

    try:
        # Fetch Webseite
        webpage_item = await webpage_diff.fetch_page(source_config)

        print("✅ Webseite erfolgreich gefetcht:")
        print(f"   Titel: {webpage_item.title}")
        print(f"   URL: {webpage_item.url}")
        print(f"   Hash: {webpage_item.raw_hash}")
        print(f"   Inhalt-Länge: {len(webpage_item.raw_text)} Zeichen")
        print(f"   Erste 200 Zeichen: {webpage_item.raw_text[:200]}...")

    except Exception as e:
        print(f"❌ Fehler: {e}")

async def fetch_multiple_sources_example():
    """Beispiel: Mehrere Quellen gleichzeitig fetchen."""
    print("🔄 Mehrere Quellen gleichzeitig fetchen:")

    sources = [
        SourceConfig(
            id="vscode_releases",
            type="github_releases",
            repo="microsoft/vscode",
            tags=["editor"]
        ),
        SourceConfig(
            id="github_trending",
            type="webpage_diff",
            url="https://github.com/trending",
            tags=["trending"]
        ),
        SourceConfig(
            id="python_releases",
            type="github_releases",
            repo="python/cpython",
            tags=["python", "language"]
        )
    ]

    results = []

    for source in sources:
        try:
            print(f"📡 Fetche {source.id}...")

            if source.type == "github_releases":
                items = await github.fetch_releases(source, token="")
                results.append((source.id, len(items), "Releases"))
            elif source.type == "webpage_diff":
                item = await webpage_diff.fetch_page(source)
                results.append((source.id, 1, "Webpage"))

            print(f"   ✅ {source.id}: Erfolgreich")

        except Exception as e:
            print(f"   ❌ {source.id}: {e}")
            results.append((source.id, 0, "Error"))

    print("\n📊 Zusammenfassung:")
    for name, count, type_ in results:
        print(f"   {name}: {count} {type_}")

def run_sync_examples():
    """Synchrones Beispiel für einzelne Fetches."""
    print("🔧 Synchrone Beispiele (ohne async/await):")

    # Diese würden normalerweise in der CLI verwendet werden
    print("   • radar run (für vollständigen Pipeline-Lauf)")
    print("   • Einzelne Source-Tests in der Entwicklung")
    print("   • Debugging und Troubleshooting")

def main():
    """Hauptfunktion mit allen Beispielen."""
    print("🚀 Radar Web Fetch Beispiele")
    print("=" * 40)

    # Async Beispiele
    asyncio.run(fetch_github_releases_example())
    print()

    asyncio.run(fetch_webpage_example())
    print()

    asyncio.run(fetch_multiple_sources_example())
    print()

    # Sync Beispiele
    run_sync_examples()
    print()

    print("💡 Tipps:")
    print("   • Verwende GitHub Token für höhere Rate-Limits")
    print("   • Webseiten-Fetching respektiert robots.txt")
    print("   • Alle Fetches werden automatisch dedupliziert")
    print("   • Ergebnisse werden in der SQLite Datenbank gespeichert")

if __name__ == "__main__":
    main()