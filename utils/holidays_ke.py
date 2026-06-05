# Kenyan public holidays (2024-2026)
from datetime import date, timedelta

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
        start_date, end_date = end_date, start_date
    
    days = 0
    current = start_date
    while current <= end_date:
        if not is_weekend_or_holiday(current):
            days += 1
        current = current + timedelta(days=1)
    return days

def add_working_days(start_date, days):
    """
    Add working days (Monday-Friday) to a date, excluding Kenyan holidays
    Returns the new date after adding the specified number of working days
    """
    if days <= 0:
        return start_date
    
    current = start_date
    days_added = 0
    
    while days_added < days:
        current = current + timedelta(days=1)
        if not is_weekend_or_holiday(current):
            days_added += 1
    
    return current

def get_next_working_day(start_date):
    """Get the next working day after the given date"""
    return add_working_days(start_date, 1)

def is_working_day(check_date):
    """Returns True if date is a working day (not weekend and not holiday)"""
    return not is_weekend_or_holiday(check_date)

def working_days_in_month(year, month):
    """Calculate number of working days in a specific month"""
    from calendar import monthrange
    _, last_day = monthrange(year, month)
    days = 0
    for day in range(1, last_day + 1):
        check_date = date(year, month, day)
        if is_working_day(check_date):
            days += 1
    return days

def get_upcoming_holidays(from_date, days_ahead=30):
    """Get list of upcoming holidays within the next X days"""
    upcoming = []
    for holiday in KENYA_HOLIDAYS:
        if from_date <= holiday <= from_date + timedelta(days=days_ahead):
            upcoming.append(holiday)
    return sorted(upcoming)
