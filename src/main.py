import asyncio
import os
import sys


from src.storage.database import Database
from src.collectors.appData_collector import appData_collector
from src.collectors.browser_collector import browser_collector
# from src.collectors.technology_detector import detect_technologies
from src.api.routes import app
import uvicorn

async def main():
    db = Database()
    tasks = [
        browser_collector(db)
        # appData_collector(db),
        # detect_technologies(db)
    ]
    print("Running.....")
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    import multiprocessing  

    def run_api():
        uvicorn.run(app, host="0.0.0.0", port=8000)

    api_process = multiprocessing.Process(target=run_api)
    api_process.start()

    asyncio.run(main())
    api_process.terminate()
