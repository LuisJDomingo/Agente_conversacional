from datetime import datetime, timedelta, time
from app.models.booking import Booking
from app.models.schedule import WeeklySchedule
from app.database import SessionLocal

# Lista de días festivos (formato YYYY-MM-DD)
HOLIDAYS = [
    "2025-01-01", # Año Nuevo
    "2025-01-06", # Reyes Magos
    "2025-12-25", # Navidad
]

def is_holiday(date_obj):
    return date_obj.strftime("%Y-%m-%d") in HOLIDAYS

def generate_hour_slots(open_time: time, close_time: time):
    slots = []
    current = datetime.combine(datetime.today(), open_time)
    end = datetime.combine(datetime.today(), close_time)
    while current + timedelta(hours=1) <= end:
        slots.append(current.time())
        current += timedelta(hours=1)
    return slots

def get_available_slots(business_id, date, db, target_date=None):
    if date < datetime.now().date():
        return []

    if is_holiday(date):
        return []

    weekday = date.weekday()
    schedule = db.query(WeeklySchedule).filter_by(business_id=business_id, weekday=weekday).first()
    if not schedule:
        return []

    all_slots = generate_hour_slots(schedule.open_time, schedule.close_time)
    bookings = db.query(Booking).filter_by(business_id=business_id, date=date).all()
    booked_slots = [b.start_time for b in bookings]

    free_slots = [s for s in all_slots if s not in booked_slots]
    return free_slots
