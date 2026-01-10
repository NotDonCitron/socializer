import os
from radar.browser import BrowserManager
from radar.instagram import InstagramAutomator
from radar.ig_config import IG_SESSION_DIR


def parse_prefixes(value: str) -> list[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def matches_prefix(username: str, prefixes: list[str]) -> bool:
    if not prefixes:
        return True
    return any(username.lower().startswith(p) for p in prefixes)


def main() -> None:
    query = os.getenv("IG_SEARCH_QUERY", "").strip()
    if not query:
        query = input("Search query: ").strip()
    if not query:
        print("No query provided.")
        return

    prefixes_raw = os.getenv("IG_ALLOWED_USERNAME_PREFIXES", "").strip()
    if not prefixes_raw:
        prefixes_raw = input("Username prefixes (comma-separated): ").strip()
    prefixes = parse_prefixes(prefixes_raw)
    if not prefixes:
        print("No prefixes provided.")
        return

    do_follow = os.getenv("IG_DO_FOLLOW", "1") == "1"
    do_like = os.getenv("IG_DO_LIKE", "1") == "1"
    do_comment = os.getenv("IG_DO_COMMENT", "0") == "1"
    comment_text = os.getenv("IG_COMMENT_TEXT", "").strip()

    if do_comment and not comment_text:
        comment_text = input("Comment text: ").strip()
    if do_comment and not comment_text:
        print("Comment enabled but no text provided.")
        return

    with BrowserManager() as manager:
        automator = InstagramAutomator(manager, user_data_dir=IG_SESSION_DIR)
        automator._ensure_page()

        results = automator.search_accounts(query)
        if not results:
            print(f"No results. Error: {automator.last_error}")
            return

        targets = [r for r in results if matches_prefix(r["username"], prefixes)]
        print(f"Targets: {len(targets)} of {len(results)} from query '{query}'")

        for item in targets:
            username = item["username"]
            print(f"\n@{username}")
            if do_follow:
                ok = automator.follow_user(username, prefixes=prefixes)
                print(f" follow: {'ok' if ok else automator.last_error}")
            if do_like:
                ok = automator.like_recent_post(username, prefixes=prefixes)
                print(f" like: {'ok' if ok else automator.last_error}")
            if do_comment:
                ok = automator.comment_recent_post(username, comment_text, prefixes=prefixes)
                print(f" comment: {'ok' if ok else automator.last_error}")


if __name__ == "__main__":
    main()
