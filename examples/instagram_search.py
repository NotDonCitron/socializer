import os
from radar.browser import BrowserManager
from radar.instagram import InstagramAutomator
from radar.ig_config import IG_SESSION_DIR


def main() -> None:
    query = os.getenv("IG_SEARCH_QUERY", "").strip()
    if not query:
        query = input("Search query: ").strip()
    if not query:
        print("No query provided.")
        return

    with BrowserManager() as manager:
        automator = InstagramAutomator(manager, user_data_dir=IG_SESSION_DIR)
        automator._ensure_page()

        results = automator.search_accounts(query)
        if not results:
            print(f"No results. Error: {automator.last_error}")
            return

        print(f"Found {len(results)} accounts for '{query}':")
        for item in results:
            name = item["display_name"] or ""
            print(f"- {item['username']} {name} {item['profile_url']}")


if __name__ == "__main__":
    main()
