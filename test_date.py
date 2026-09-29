from datetime import datetime, timedelta, timezone

def get_next_review_time(days_ahead):
    now_utc = datetime.now(timezone.utc)
    if now_utc.hour < 3:
        current_logical_day = now_utc.date() - timedelta(days=1)
    else:
        current_logical_day = now_utc.date()
        
    target_date = current_logical_day + timedelta(days=days_ahead)
    target_dt = datetime(target_date.year, target_date.month, target_date.day, 3, 0, 0, tzinfo=timezone.utc)
    target_local = target_dt.astimezone()
    return target_local.replace(tzinfo=None).isoformat()

print("Now local:", datetime.now().isoformat())
print("Next day (+1):", get_next_review_time(1))
print("Day after (+2):", get_next_review_time(2))
