"""
Business logic and data processing module.

Responsibilities:
- Staleness calculations
- Lead status determination
- Filtering and sorting logic
- Display formatting
"""
import logging
import platform
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

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


def format_status_display(status: Optional[str]) -> Optional[str]:
    """
    Format status with emoji prefix for visual indicator.

    Args:
        status: Status string ('stale', 'at_risk', 'healthy') or None

    Returns:
        Formatted status with emoji (e.g., '🔴 stale') or None
    """
    if status is None:
        return None
    emoji_map = {
        "stale": "🔴",
        "at_risk": "🟡",
        "healthy": "🟢",
    }
    emoji = emoji_map.get(status)
    if emoji is None:
        logger.warning("Unknown status value: %s", status)
        return status
    return f"{emoji} {status}"


# Display formatting functions

def format_date(dt: Optional[datetime]) -> str:
    """
    Format datetime as 'Jan 7, 2026' for display.

    Args:
        dt: datetime object or None

    Returns:
        Formatted date string or "—" if None
    """
    if dt is None:
        return "—"
    # Use %#d on Windows, %-d on Unix for day without leading zero
    if platform.system() == "Windows":
        return dt.strftime("%b %#d, %Y")
    return dt.strftime("%b %-d, %Y")


def safe_display(value: Optional[str]) -> str:
    """
    Return value or '—' for None/empty values.

    Args:
        value: String value or None

    Returns:
        Original value or "—" if None or empty
    """
    if value is None or value == "":
        return "—"
    return value


def format_phone_link(phone: Optional[str]) -> Optional[str]:
    """
    Format phone number as tel: URL for clickable link.

    Args:
        phone: Phone number string or None

    Returns:
        tel: URL string or None if no phone
    """
    if not phone:
        return None
    return f"tel:{phone}"


def format_email_link(email: Optional[str]) -> Optional[str]:
    """
    Format email address as mailto: URL for clickable link.

    Args:
        email: Email address string or None

    Returns:
        mailto: URL string or None if no email
    """
    if not email:
        return None
    return f"mailto:{email}"


def format_leads_for_display(leads: list[dict]) -> list[dict]:
    """
    Transform lead data for table display.

    Args:
        leads: List of lead dictionaries from get_leads_with_appointments()

    Returns:
        List of dictionaries formatted for display with columns:
        - Lead Name
        - Appointment Date
        - Days (days since appointment)
        - Status: stale (7+ days), at_risk (5-6 days), healthy (<5 days)
        - Stage
        - Locator
        - Phone (tel: link or None)
        - Email (mailto: link or None)
    """
    result = []
    for lead in leads:
        days = calculate_days_since(lead["appointment_date"]) if lead.get("appointment_date") else None
        status = get_lead_status(days) if days is not None else None
        result.append({
            "Lead Name": safe_display(lead.get("name")),
            "Appointment Date": format_date(lead.get("appointment_date")),
            "Days": days,
            "Status": format_status_display(status),
            "Stage": safe_display(lead.get("current_stage")),
            "Locator": safe_display(lead.get("locator_name")),
            "Phone": format_phone_link(lead.get("locator_phone")),
            "Email": format_email_link(lead.get("locator_email")),
        })
    return result


def sort_by_urgency(leads: list[dict]) -> list[dict]:
    """
    Sort leads by urgency: stale first, then at_risk, then healthy.

    Within each status group, sorts by days descending (oldest/most days first).
    Leads with None days are sorted to the end.

    Args:
        leads: List of formatted lead dictionaries (from format_leads_for_display)

    Returns:
        New list sorted by urgency
    """
    def sort_key(lead):
        status = lead.get("Status") or ""
        days = lead.get("Days")

        # Status priority: stale=0, at_risk=1, healthy/other=2
        if "stale" in status:
            priority = 0
        elif "at_risk" in status:
            priority = 1
        else:
            priority = 2

        # Days: higher is more urgent (negate for descending), None goes last
        days_value = -days if days is not None else float("inf")

        return (priority, days_value)

    return sorted(leads, key=sort_key)


def count_leads_by_status(leads: list[dict]) -> dict[str, int]:
    """
    Count leads by status category.

    Args:
        leads: List of formatted lead dictionaries (from format_leads_for_display)

    Returns:
        Dictionary with counts: {"stale": N, "at_risk": N, "healthy": N}
        Note: Leads with None or empty Status are counted as "healthy".
        The sum of all counts always equals len(leads).
    """
    counts = {"stale": 0, "at_risk": 0, "healthy": 0}
    for lead in leads:
        status = lead.get("Status") or ""
        if "stale" in status:
            counts["stale"] += 1
        elif "at_risk" in status:
            counts["at_risk"] += 1
        else:
            counts["healthy"] += 1
    return counts


def format_last_updated(timestamp: Optional[datetime]) -> str:
    """
    Format last refresh timestamp for display.

    Args:
        timestamp: datetime of last refresh, or None if never refreshed

    Returns:
        Human-readable string like "Just now", "5 minutes ago", or time
    """
    if timestamp is None:
        return "Never"

    now = datetime.now(timezone.utc)
    diff = now - timestamp
    seconds = diff.total_seconds()

    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        return timestamp.strftime("%b %-d at %I:%M %p") if platform.system() != "Windows" else timestamp.strftime("%b %#d at %I:%M %p")
