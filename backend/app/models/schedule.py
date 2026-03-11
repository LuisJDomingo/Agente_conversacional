from sqlalchemy import Column, Integer, String, Time
from app.database import Base

class WeeklySchedule(Base):
    __tablename__ = "weekly_schedule"

    id = Column(Integer, primary_key=True)
    business_id = Column(String)
    weekday = Column(Integer)  # 0=Monday
    open_time = Column(Time)
    close_time = Column(Time)
