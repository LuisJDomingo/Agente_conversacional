import sys
import os
from datetime import time

# Asegurar que podemos importar 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models.schedule import WeeklySchedule
from app.models.booking import Booking

def seed_db():
    print(">>> 🗑️  Eliminando tablas antiguas para actualizar esquema...")
    Base.metadata.drop_all(bind=engine)

    print(">>> 🆕 Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    business_id = "demo"  # El ID que usa tu aplicación por defecto

    print(f">>> Sembrando horario semanal para '{business_id}' (Lun-Vie, 09:00 - 18:00)...")
    
    # Crear horario de Lunes (0) a Sábado (5)
    for weekday in range(6):
        schedule = WeeklySchedule(
            business_id=business_id,
            weekday=weekday,
            open_time=time(9, 0),
            close_time=time(18, 0)
        )
        db.add(schedule)

    db.commit()
    print(">>> ¡Base de datos actualizada y sembrada con éxito!")
    db.close()

if __name__ == "__main__":
    seed_db()