import asyncio
from datetime import datetime, timedelta, timezone
import getpass
import json
import os
import pywinctl
from dotenv import load_dotenv
from browser_history.browsers import Chrome, Firefox, Edge, Brave

load_dotenv()

async def browser_collector(db):
    user_id = getpass.getuser()
    pc_id = os.getenv("PC_ID", "unknown_pc")
    history_file = "logs/browser_history.log"
    last_active = None
    logged_entries = set()

    browser_classes = [Chrome, Firefox, Edge, Brave]

    def get_recent_history_entries(within_secs=60):
        """Fetch recent browser history within a time window."""
        now = datetime.now(timezone.utc)
        entries = []
        for Browser in browser_classes:
            try:
                b = Browser()
                output = b.fetch_history()
                for timestamp, url, title in output.histories:
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                    else:
                        timestamp = timestamp.astimezone(timezone.utc)
                    if (now - timestamp).total_seconds() <= within_secs:
                        entries.append((timestamp, url, title))
            except Exception as e:
                print(f"[History] {Browser.__name__} error: {e}")
        return entries

    while True:
        try:
            print(get_recent_history_entries(55000))
            now = datetime.now(timezone.utc)
            active_win = pywinctl.getActiveWindow()
            active_title = active_win.title if active_win else ""

            is_browser = any(browser in active_title.lower() for browser in ["chrome", "firefox", "edge", "brave"])

            if is_browser and active_title:
                if (
                        last_active is None
                        or last_active["title"] != active_title
                ):
                    # Log previous
                    if last_active:
                        duration = (now - last_active["start_time"]).total_seconds()
                        if duration >= 1:
                            # Match history entry
                            matched_url = "unknown"
                            matched_title = last_active["title"]
                            recent_history = get_recent_history_entries(1000)
                            for ts, url, title in recent_history:
                                if title.strip() == last_active["title"].strip():
                                    matched_url = url
                                    break

                            key = (matched_url, matched_title)
                            if key not in logged_entries:
                                entry = {
                                    "timestamp": now.isoformat(),
                                    "url": matched_url,
                                    "title": matched_title,
                                    "time_spent_seconds": duration,
                                    "monitor": "combined",
                                    "pc_id": pc_id
                                }

                                with open(history_file, "a") as f:
                                    json.dump(entry, f)
                                    f.write("\n")

                                await db.log_event(
                                    user_id,
                                    "browser",
                                    {
                                        "url": matched_url,
                                        "title": matched_title,
                                        "time_spent_seconds": duration,
                                        "monitor": "combined"
                                    },
                                    int(duration)
                                )
                                logged_entries.add(key)

                    # Update last active
                    last_active = {
                        "title": active_title,
                        "start_time": now
                    }

        except Exception as e:
            print(f"[Collector Error] {e}")

        await asyncio.sleep(1)
