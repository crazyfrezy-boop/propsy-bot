from datetime import datetime, timedelta

class CalendarAPI:
    def __init__(self):
        print("✅ Календарь готов (упрощённый режим)")

    def get_available_slots(self, psychologist_id, days=7):
        slots = []
        now = datetime.now()
        for i in range(1, days+1):
            date = now + timedelta(days=i)
            if date.weekday() < 5:
                for hour in [10, 12, 14, 16, 18]:
                    slot_time = datetime(date.year, date.month, date.day, hour, 0)
                    if slot_time > now:
                        slots.append({
                            'id': len(slots)+1,
                            'datetime': slot_time,
                            'time': slot_time.strftime('%d.%m %H:%M'),
                            'psychologist_id': psychologist_id
                        })
        return slots

    def book_slot(self, slot_id, client_id):
        print(f"📅 Забронирован слот {slot_id} для клиента {client_id}")
        return True