from pydantic import BaseModel
from datetime import date, time

class BookingCreate(BaseModel):
    business_id: str
    date: date
    start_time: time
    customer_name: str
    customer_email: str
