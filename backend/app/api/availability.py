@router.get("/availability")
def availability(business_id: str, date: str, db=Depends(SessionLocal)):
    from datetime import datetime

    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "Formato de fecha inválido. Usa YYYY-MM-DD"}

    slots = get_available_slots(business_id, target_date, db)

    return {
        "date": date,
        "available_slots": [s.strftime("%H:%M") for s in slots]
    }
