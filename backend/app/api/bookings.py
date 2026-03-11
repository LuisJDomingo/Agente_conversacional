from fastapi import APIRouter, Depends
from app.database import SessionLocal
from app.schemas.booking import BookingCreate
from app.services.booking_service import create_booking

router = APIRouter()

@router.post("/book")
def book(booking: BookingCreate, db=Depends(SessionLocal)):
    new_booking = create_booking(db, booking)
    return {
        "message": "Reserva creada",
        "booking": {
            "date": str(new_booking.date),
            "start_time": new_booking.start_time.strftime("%H:%M"),
            "customer_name": new_booking.customer_name
        }
    }
