# Kenyan public holidays (2024-2026)
from datetime import date

KENYA_HOLIDAYS = [
    # 2024
    date(2024, 1, 1),   # New Year's Day
    date(2024, 3, 29),  # Good Friday
    date(2024, 4, 1),   # Easter Monday
    date(2024, 5, 1),   # Labour Day
    date(2024, 6, 1),   # Madaraka Day
    date(2024, 10, 10), # Moi Day
    date(2024, 10, 20), # Mashujaa Day
    date(2024, 12, 12), # Jamhuri Day
    date(2024, 12, 25), # Christmas Day
    date(2024, 12, 26), # Boxing Day
    # 2025
    date(2025, 1, 1),
    date(2025, 4, 18),
    date(2025, 4, 21),
    date(2025, 5, 1),
    date(2025, 6, 1),
    date(2025, 10, 20),
    date(2025, 12, 12),
    date(2025, 12, 25),
    date(2025, 12, 26),
    # 2026
    date(2026, 1, 1),
    date(2026, 4, 3),
    date(2026, 4, 6),
    date(2026, 5, 1),
    date(2026, 6, 1),
    date(2026, 10, 20),
    date(2026, 12, 12),
    date(2026, 12, 25),
    date(2026, 12, 26),
]

def is_weekend_or_holiday(check_date):
    """Returns True if date is weekend or Kenyan public holiday"""
    if check_date.weekday() >= 5:  # Saturday=5, Sunday=6
        return True
    return check_date in KENYA_HOLIDAYS

def working_days_between(start_date, end_date):
    """Calculate working days excluding weekends and Kenyan holidays"""
    if start_date > end_date:
        return 0
    
    days = 0
    current = start_date
    while current <= end_date:
        if not is_weekend_or_holiday(current):
            days += 1
        current = current.replace(day=current.day + 1)
    return days
