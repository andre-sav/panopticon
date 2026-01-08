"""
Business logic and data processing module.

Responsibilities:
- Staleness calculations
- Lead status determination
- Filtering and sorting logic
- Display formatting
- Stage history formatting
"""
import logging
import platform
from datetime import datetime, timezone, timedelta
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


STATUS_EMOJI_MAP = {
    "stale": "🔴",
    "at_risk": "🟡",
    "healthy": "🟢",
}


def get_status_emoji(status: Optional[str]) -> str:
    """
    Get emoji for a status value.

    Args:
        status: Status string ('stale', 'at_risk', 'healthy'),
                formatted status with emoji, or None

    Returns:
        Status emoji ('🔴', '🟡', '🟢') or empty string if unknown
    """
    if status is None:
        return ""
    # Check if status contains a known status keyword
    status_lower = status.lower() if status else ""
    for key, emoji in STATUS_EMOJI_MAP.items():
        if key in status_lower:
            return emoji
    return ""


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
    emoji = STATUS_EMOJI_MAP.get(status)
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
        - id (for fetching stage history)
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
            "id": lead.get("id"),
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


# Filter constants
ALL_STAGES = "All Stages"
ALL_LOCATORS = "All Locators"
ALL_DATES = "All Dates"

DATE_RANGE_PRESETS = [
    "All Dates",
    "Today",
    "Last 7 Days",
    "Last 30 Days",
]


def filter_by_stage(leads: list[dict], stage: str) -> list[dict]:
    """
    Filter leads by stage.

    Args:
        leads: List of formatted lead dictionaries
        stage: Stage to filter by, or "All Stages" to return all

    Returns:
        Filtered list of leads matching the stage
    """
    if stage == ALL_STAGES:
        return leads
    return [lead for lead in leads if lead.get("Stage") == stage]


def filter_by_locator(leads: list[dict], locator: str) -> list[dict]:
    """
    Filter leads by locator name (case-insensitive).

    Args:
        leads: List of formatted lead dictionaries
        locator: Locator name to filter by, or "All Locators" to return all

    Returns:
        Filtered list of leads matching the locator
    """
    if locator == ALL_LOCATORS:
        return leads
    locator_lower = locator.lower()
    return [
        lead for lead in leads
        if lead.get("Locator") and lead["Locator"].lower() == locator_lower
    ]


def filter_by_date_range(leads: list[dict], date_range: str) -> list[dict]:
    """
    Filter leads by appointment date range preset.

    Uses the Days column (days since appointment) for filtering:
    - All Dates: No filter
    - Today: Days == 0
    - Last 7 Days: Days >= 0 and Days <= 6 (today + past 6 days = 7 days)
    - Last 30 Days: Days >= 0 and Days <= 29 (today + past 29 days = 30 days)

    Note: Future appointments (negative Days) are excluded from date range filters.

    Args:
        leads: List of formatted lead dictionaries with Days column
        date_range: Date range preset string

    Returns:
        Filtered list of leads within the date range
    """
    if date_range == ALL_DATES:
        return leads

    result = []
    for lead in leads:
        days = lead.get("Days")
        if days is None:
            continue

        include = False
        if date_range == "Today":
            include = days == 0
        elif date_range == "Last 7 Days":
            include = 0 <= days <= 6
        elif date_range == "Last 30 Days":
            include = 0 <= days <= 29

        if include:
            result.append(lead)

    return result


def apply_filters(
    leads: list[dict],
    stage: str = ALL_STAGES,
    locator: str = ALL_LOCATORS,
    date_range: str = ALL_DATES,
) -> list[dict]:
    """
    Apply all filters in sequence (AND logic).

    Args:
        leads: List of formatted lead dictionaries
        stage: Stage filter value
        locator: Locator filter value
        date_range: Date range filter value

    Returns:
        List of leads matching ALL filter criteria
    """
    result = leads
    result = filter_by_stage(result, stage)
    result = filter_by_locator(result, locator)
    result = filter_by_date_range(result, date_range)
    return result


def get_unique_stages(leads: list[dict]) -> list[str]:
    """
    Extract unique stage values from leads.

    Args:
        leads: List of formatted lead dictionaries

    Returns:
        Sorted list of unique stage values (excludes None and "—")
    """
    stages = set()
    for lead in leads:
        stage = lead.get("Stage")
        if stage and stage != "—":
            stages.add(stage)
    return sorted(stages)


def get_unique_locators(leads: list[dict]) -> list[str]:
    """
    Extract unique locator names from leads.

    Args:
        leads: List of formatted lead dictionaries

    Returns:
        Sorted list of unique locator names (excludes None and "—")
    """
    locators = set()
    for lead in leads:
        locator = lead.get("Locator")
        if locator and locator != "—":
            locators.add(locator)
    return sorted(locators)


# Sort constants
DEFAULT_SORT = "Default (Urgency)"
SORT_DAYS_MOST = "Days (Most First)"
SORT_DAYS_LEAST = "Days (Least First)"
SORT_DATE_NEWEST = "Appointment Date (Newest)"
SORT_DATE_OLDEST = "Appointment Date (Oldest)"
SORT_NAME_AZ = "Lead Name (A-Z)"
SORT_STAGE_AZ = "Stage (A-Z)"
SORT_LOCATOR_AZ = "Locator (A-Z)"

SORT_OPTIONS = [
    DEFAULT_SORT,
    SORT_DAYS_MOST,
    SORT_DAYS_LEAST,
    SORT_DATE_NEWEST,
    SORT_DATE_OLDEST,
    SORT_NAME_AZ,
    SORT_STAGE_AZ,
    SORT_LOCATOR_AZ,
]


def _sort_key_string(value: str | None, field_name: str) -> tuple[int, str]:
    """
    Create sort key for string field, placing None/"—" at end.

    Returns tuple (priority, lowercase_value) where priority 0 = real value, 1 = placeholder.
    """
    val = value or "—"
    if val == "—":
        return (1, "")
    return (0, val.lower())


def sort_leads(leads: list[dict], sort_option: str) -> list[dict]:
    """
    Sort leads by the specified option.

    Args:
        leads: List of formatted lead dictionaries
        sort_option: One of SORT_OPTIONS

    Returns:
        New list sorted by the specified option
    """
    if sort_option == DEFAULT_SORT:
        return sort_by_urgency(leads)

    # Days descending (most days first) - same logic for "oldest" dates
    if sort_option in (SORT_DAYS_MOST, SORT_DATE_OLDEST):
        return sorted(
            leads,
            key=lambda x: (-x["Days"] if x.get("Days") is not None else float("inf"))
        )

    # Days ascending (least days first) - same logic for "newest" dates
    if sort_option in (SORT_DAYS_LEAST, SORT_DATE_NEWEST):
        return sorted(
            leads,
            key=lambda x: (x["Days"] if x.get("Days") is not None else float("inf"))
        )

    if sort_option == SORT_NAME_AZ:
        return sorted(leads, key=lambda x: _sort_key_string(x.get("Lead Name"), "Lead Name"))

    if sort_option == SORT_STAGE_AZ:
        return sorted(leads, key=lambda x: _sort_key_string(x.get("Stage"), "Stage"))

    if sort_option == SORT_LOCATOR_AZ:
        return sorted(leads, key=lambda x: _sort_key_string(x.get("Locator"), "Locator"))

    # Fallback to urgency sort
    return sort_by_urgency(leads)


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


def format_time_in_stage(days: int | None) -> str:
    """
    Format time in current stage as human-readable string.

    For MVP, uses days since appointment as proxy for time in stage.
    Will be updated in Story 4.2 when stage history is available.

    Args:
        days: Days since appointment (or stage entry), or None.
              Negative values indicate future appointments.

    Returns:
        Formatted string like "3 days", "Less than 1 day", "In 2 days", or "Unknown"
    """
    if days is None:
        return "Unknown"

    if days < 0:
        # Future appointment
        future_days = abs(days)
        if future_days == 1:
            return "In 1 day"
        return f"In {future_days} days"
    elif days == 0:
        return "Less than 1 day"
    elif days == 1:
        return "1 day"
    else:
        return f"{days} days"


def format_stage_timestamp(dt: Optional[datetime]) -> str:
    """
    Format a stage change timestamp with relative dates for today/yesterday.

    Args:
        dt: datetime of the stage change (UTC), or None

    Returns:
        Formatted string like:
        - "Today at 2:30 PM" for today's changes
        - "Yesterday at 10:00 AM" for yesterday's changes
        - "Jan 5, 2026 at 2:30 PM" for older changes
        - "Unknown" if dt is None

    Note:
        Uses UTC for "Today/Yesterday" calculation since server-side rendering
        cannot determine user's local timezone. For most business hours usage,
        UTC provides consistent and predictable behavior.
    """
    if dt is None:
        return "Unknown"

    # Compare dates in UTC (server-side cannot know user's local timezone)
    now = datetime.now(timezone.utc)
    today = now.date()
    yesterday = today - timedelta(days=1)
    dt_date = dt.date()

    # Format time portion consistently
    # Use %#I on Windows, %-I on Unix for hour without leading zero
    if platform.system() == "Windows":
        time_format = "%#I:%M %p"
        date_format = "%b %#d, %Y"
    else:
        time_format = "%-I:%M %p"
        date_format = "%b %-d, %Y"

    time_str = dt.strftime(time_format)

    if dt_date == today:
        return f"Today at {time_str}"
    elif dt_date == yesterday:
        return f"Yesterday at {time_str}"
    else:
        date_str = dt.strftime(date_format)
        return f"{date_str} at {time_str}"


def format_stage_history(transitions: list[dict]) -> list[dict]:
    """
    Format stage transition history for display.

    Args:
        transitions: List of transition dictionaries from get_stage_history()
                    Each contains: from_stage, to_stage, changed_at

    Returns:
        List of formatted dictionaries with:
        - "transition": "Previous Stage → New Stage" or "Initial: Stage"
        - "timestamp": Formatted timestamp string
        - "is_delivered": True if to_stage is "Delivered"
    """
    formatted = []
    for t in transitions:
        from_stage = t.get("from_stage")
        to_stage = t.get("to_stage", "Unknown")
        changed_at = t.get("changed_at")

        # Format transition text
        if from_stage:
            transition_text = f"{from_stage} → {to_stage}"
        else:
            # First recorded stage (no previous)
            transition_text = f"Initial: {to_stage}"

        # Check if this is a delivered stage (pipeline completion)
        is_delivered = to_stage and "delivered" in to_stage.lower()

        formatted.append({
            "transition": transition_text,
            "timestamp": format_stage_timestamp(changed_at),
            "is_delivered": is_delivered,
        })

    return formatted
