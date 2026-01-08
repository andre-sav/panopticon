"""
Business logic and data processing module.

Responsibilities:
- Staleness calculations
- Lead status determination
- Filtering and sorting logic
"""
from datetime import datetime, timezone

# Staleness thresholds (single source of truth)
STALE_THRESHOLD_DAYS = 7
AT_RISK_THRESHOLD_DAYS = 5


def calculate_days_since(appointment_date: datetime) -> int:
    """Returns calendar days since appointment. Negative = future."""
    today = datetime.now(timezone.utc).date()
    return (today - appointment_date.date()).days


def get_lead_status(days_since: int) -> str:
    """Returns 'stale', 'at_risk', or 'healthy'."""
    if days_since >= STALE_THRESHOLD_DAYS:
        return "stale"
    elif days_since >= AT_RISK_THRESHOLD_DAYS:
        return "at_risk"
    return "healthy"
