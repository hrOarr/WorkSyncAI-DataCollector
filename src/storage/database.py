from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
import json

load_dotenv()

EMPLOYEE_NAME = os.getenv("EMPLOYEE_NAME", "unknown")
EMPLOYEE_ID = os.getenv("EMPLOYEE_ID", "unknown")

Base = declarative_base()

db_path = "data/worksync.db"
db_dir = os.path.dirname(db_path)
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

class Event(Base):
    __tablename__ = "events"
    user_id = Column(String, primary_key=True, index=True)
    employee_info = Column(String, primary_key=True)
    event_type = Column(String, primary_key=True)
    event_detail = Column(String, primary_key=True)
    timestamp = Column(String, primary_key=True)
    duration = Column(Integer)

class Database:
    def __init__(self):
        db_url = f"sqlite:///{db_path}"
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})  # SQLite thread safety
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.employee_info = {
            "id": EMPLOYEE_ID,
            "name": EMPLOYEE_NAME
        }

    async def log_event(self, user_id, event_type, event_detail, duration=0):
        session = self.Session()
        try:
            event = Event(
                user_id=user_id,
                employee_info=json.dumps(self.employee_info),
                event_type=event_type,
                event_detail=json.dumps(event_detail),
                timestamp=datetime.now().isoformat(),
                duration=duration
            )
            session.add(event)
            session.commit()
            print(f"Logged: {event.employee_info}, {event.event_type}, {event.event_detail}, {event.duration}s")
        except Exception as e:
            session.rollback()
            print(f"Database error: {e}")
        finally:
            session.close()

    async def get_events(self, event_type=None, user_id=None):
        session = self.Session()
        try:
            query = session.query(Event)
            if event_type:
                query = query.filter(Event.event_type == event_type)
            if user_id:
                query = query.filter(Event.user_id == user_id)
            return query.all()
        finally:
            session.close()

    def close(self):
        self.engine.dispose()