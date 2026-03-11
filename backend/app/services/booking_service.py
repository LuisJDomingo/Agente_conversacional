from app.models.booking import Booking
from app.database import SessionLocal
from datetime import timedelta

def create_booking(db, booking_data):
    end_time = (datetime.combine(datetime.today(), booking_data.start_time) + timedelta(hours=1)).time()
    booking = Booking(
        business_id=booking_data.business_id,
        date=booking_data.date,
        start_time=booking_data.start_time,
        end_time=end_time,
        customer_name=booking_data.customer_name,
        customer_email=booking_data.customer_email
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking
