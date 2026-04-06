from datetime import date, datetime, timedelta
from icalendar import Calendar, Event
import uuid


def generate_ics(deadlines: list[dict]) -> bytes:
    """
    Generate an .ics file from a list of deadline dicts.

    Each dict should have:
      - program_name (str)
      - university_name (str)
      - deadline (date | str)
      - url (str, optional)
    """
    cal = Calendar()
    cal.add("prodid", "-//UniMatch Bot//unimatch//RU")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", "UniMatch — Дедлайны")

    for item in deadlines:
        deadline = item.get("deadline")
        if isinstance(deadline, str):
            deadline = date.fromisoformat(deadline)

        event = Event()
        event.add("uid", str(uuid.uuid4()))
        event.add("summary", f"Дедлайн: {item['program_name']} — {item['university_name']}")
        event.add("dtstart", deadline)
        event.add("dtend", deadline + timedelta(days=1))
        event.add("dtstamp", datetime.utcnow())

        description_parts = [
            f"Программа: {item['program_name']}",
            f"Вуз: {item['university_name']}",
        ]
        if item.get("url"):
            description_parts.append(f"Ссылка: {item['url']}")
        event.add("description", "\n".join(description_parts))

        if item.get("url"):
            event.add("url", item["url"])

        # Reminder 7 days before
        from icalendar import Alarm
        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add("description", f"Через 7 дней: дедлайн {item['program_name']}")
        alarm.add("trigger", timedelta(days=-7))
        event.add_component(alarm)

        cal.add_component(event)

    return cal.to_ical()
