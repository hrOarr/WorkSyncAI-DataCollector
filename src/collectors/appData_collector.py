import asyncio
import getpass
from datetime import datetime
from Xlib import display, X
import psutil

async def appData_collector(db, interval=5):
    user_id = getpass.getuser()
    current_app = None
    start_time = None
    app_usage = {}

    def get_foreground_app_name():
        try:
            d = display.Display()
            root = d.screen().root

            NET_ACTIVE_WINDOW = d.intern_atom('_NET_ACTIVE_WINDOW')
            window_id = root.get_full_property(NET_ACTIVE_WINDOW, X.AnyPropertyType).value[0]
            window = d.create_resource_object('window', window_id)

            # Get window title
            title = window.get_wm_name()

            # Get PID
            NET_WM_PID = d.intern_atom('_NET_WM_PID')
            pid_property = window.get_full_property(NET_WM_PID, X.AnyPropertyType)
            if not pid_property:
                return "unknown", title or "unknown"
            pid = pid_property.value[0]

            # Get app name
            proc = psutil.Process(pid)
            app_name = proc.name()

            return app_name, title or "unknown"
        except Exception as e:
            print(f"[ERROR] Could not get foreground app: {e}")
            return "unknown", "unknown"

    while True:
        app_name, title = get_foreground_app_name()
        now = datetime.utcnow()

        # If app changed, log previous app usage
        if app_name != current_app:
            if current_app:
                duration = (now - start_time).total_seconds()
                app_usage[current_app] = app_usage.get(current_app, 0) + duration

                # Log to DB
                await db.log_event(
                    user_id,
                    "app_usage",
                    {
                        "app_name": current_app,
                        "title": title,
                        "time_spent_seconds": duration
                    },
                    app_usage[current_app]
                )

            current_app = app_name
            start_time = now

        await asyncio.sleep(interval)
