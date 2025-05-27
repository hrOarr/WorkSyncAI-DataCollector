from typing import List, Optional
from fastapi import FastAPI, Depends
from src.storage.database import Database

app = FastAPI(title="WorkSyncAI")

async def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()

@app.get("/events", response_model=List[dict])
async def get_events(event_type: Optional[str] = None, user_id: Optional[str] = None, db: Database = Depends(get_db)):
    events = await db.get_events(event_type=event_type, user_id=user_id)
    return [{"employee_info": e.employee_info, "event_type": e.event_type, "event_detail": e.event_detail, "timestamp": e.timestamp, "duration": e.duration} for e in events]