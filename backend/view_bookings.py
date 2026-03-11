import sys
import os

# Asegurar que podemos importar 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.booking import Booking

def list_bookings():
    db = SessionLocal()
    print("\n>>> 📅 CALENDARIO DE CITAS REGISTRADAS")
    print(f"{'FECHA CITA':<12} | {'HORA':<8} | {'CLIENTE':<25} | {'EMAIL':<30} | {'FECHA EVENTO'}")
    print("-" * 90)
    
    bookings = db.query(Booking).order_by(Booking.date, Booking.start_time).all()
    
    if not bookings:
        print("📭 No hay citas registradas todavía.")
    else:
        for b in bookings:
            print(f"{str(b.date):<12} | {b.start_time.strftime('%H:%M'):<8} | {b.customer_name or 'N/A':<25} | {b.customer_email or 'N/A':<30} | {b.event_date or 'N/A'}")
    
    print("-" * 90 + "\n")
    db.close()

if __name__ == "__main__":
    list_bookings()