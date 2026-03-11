from sqlalchemy import Column, Integer, String, Date, Time
from app.database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(String, index=True)
    date = Column(Date)
    start_time = Column(Time)
    customer_name = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    event_date = Column(String, nullable=True)
    event_details = Column(String, nullable=True)
    status = Column(String, default="confirmed", nullable=True)
    google_event_id = Column(String, nullable=True)
