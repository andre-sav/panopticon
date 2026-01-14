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

from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

# Staleness thresholds (single source of truth)
STALE_THRESHOLD_DAYS = 7
AT_RISK_THRESHOLD_DAYS = 5

# New classification thresholds
STALE_NO_ACTIVITY_DAYS = 14  # No activity for 14+ days = Stale
FUZZY_MATCH_THRESHOLD = 60  # 60% name similarity for delivery matching

# Stage that indicates acknowledgment
ACKNOWLEDGED_STAGE = "appt acknowledged"

# Zoho CRM org ID for deep links
ZOHO_ORG_ID = "org31352869"
ZOHO_LOCATINGS_MODULE = "CustomModule5"
ZOHO_DELIVERIES_MODULE = "CustomModule22"


def calculate_days_since(appointment_date: datetime) -> int:
    """Returns calendar days since appointment. Negative = future."""
    today = datetime.now(timezone.utc).date()
    return (today - appointment_date.date()).days


def get_lead_status(days_since: int, stage: str = None, days_since_modified: int = None) -> str:
    """Returns 'stale', 'at_risk', 'needs_attention', or 'healthy'.

    Args:
        days_since: Days since appointment (negative = future)
        stage: Current stage name (optional)
        days_since_modified: Days since last record modification (optional)

    Returns:
        Status string: 'stale', 'at_risk', 'needs_attention', or 'healthy'

    Stage-specific rules:
        - Terminal/completion stages are always 'healthy' (no action needed):
          "Green/ Delivered", "Delivery Requested", "Red/ Rejected",
          "Green/No operator", "Declined by Operator", "Green - LLL Fulfilled",
          "Red/Not Viable"
        - "Green - Approved By Locator": 'healthy' unless > 7 days since
          last modification, then 'needs_attention'
        - "Appt Not Acknowledged": 'at_risk' if < 7 days (waiting for response),
          'stale' if 7+ days (standard threshold still applies)
    """
    stage_lower = stage.lower() if stage else ""

    # Terminal/completion stages - always healthy (no action needed)
    terminal_stages = (
        "green/ delivered",
        "delivery requested",
        "red/ rejected",
        "green/no operator",
        "declined by operator",
        "green - lll fulfilled",
        "red/not viable",
    )
    if stage_lower in terminal_stages:
        return "healthy"

    # "Green - Approved By Locator" needs attention if > 7 days since modification
    if stage_lower == "green - approved by locator":
        if days_since_modified is not None and days_since_modified > 7:
            return "needs_attention"
        return "healthy"

    # Standard staleness thresholds apply to all other stages
    if days_since >= STALE_THRESHOLD_DAYS:
        return "stale"

    # "Appt Not Acknowledged" is at_risk even if < 5 days (waiting for locator response)
    # But still becomes stale at 7+ days (handled above)
    if stage_lower == "appt not acknowledged":
        return "at_risk"

    if days_since >= AT_RISK_THRESHOLD_DAYS:
        return "at_risk"
    return "healthy"


# --- Delivery Matching Utilities ---


def format_delivery_link(delivery_id: str) -> str:
    """Format a Zoho CRM link for a delivery record."""
    return f"https://crm.zoho.com/crm/{ZOHO_ORG_ID}/tab/{ZOHO_DELIVERIES_MODULE}/{delivery_id}"


def find_matching_delivery(
    lead_id: str,
    lead_name: str,
    deliveries: list[dict],
    lead_address: str = None,
    lead_zip: str = None,
) -> Optional[dict]:
    """
    Find a matching delivery record for a lead.

    Matching strategy:
    1. Direct ID match via Deliveries.Locatings lookup (most reliable)
    2. Fuzzy name match at 60% threshold + Address AND Zip verification (fallback)

    Args:
        lead_id: The Locating record ID
        lead_name: The Locating record name
        deliveries: List of delivery records
        lead_address: The lead's address (for verification)
        lead_zip: The lead's zip code (for verification)

    Returns:
        Matching delivery dict if found, None otherwise
    """
    if not deliveries:
        return None

    # Strategy 1: Direct ID match via lookup field (most reliable)
    for delivery in deliveries:
        if delivery.get("locating_id") == lead_id:
            return delivery

    # Strategy 2: Fuzzy name match with Address AND Zip verification
    if not lead_name:
        return None

    lead_name_lower = lead_name.lower().strip()
    best_match = None
    best_score = 0

    for delivery in deliveries:
        delivery_name = delivery.get("name")
        if not delivery_name:
            continue

        # Use rapidfuzz for fuzzy matching on name
        score = fuzz.ratio(lead_name_lower, delivery_name.lower().strip())

        if score >= FUZZY_MATCH_THRESHOLD and score > best_score:
            # High-confidence name matches (90%+) don't need address verification
            if score >= 90:
                best_match = delivery
                best_score = score
                continue

            # For lower confidence matches, verify Address AND Zip if available
            delivery_address = delivery.get("address") or ""
            delivery_zip = delivery.get("zip_code") or ""

            # If lead has address/zip info, require both to match
            if lead_address and lead_zip:
                address_match = lead_address.lower().strip() in delivery_address.lower() or \
                               delivery_address.lower() in lead_address.lower().strip()
                zip_match = str(lead_zip).strip() == str(delivery_zip).strip()

                if address_match and zip_match:
                    best_match = delivery
                    best_score = score
            else:
                # No lead address/zip to verify against, accept the name match
                best_match = delivery
                best_score = score

    if best_match:
        logger.debug(
            "Fuzzy matched lead '%s' to delivery '%s' (score: %d%%)",
            lead_name, best_match.get("name"), best_score
        )

    return best_match


def has_been_acknowledged(stage_history: list[dict], current_stage: str) -> bool:
    """
    Check if a lead has ever been in the 'APPT Acknowledged' stage.

    Args:
        stage_history: List of stage transitions [{from_stage, to_stage, changed_at}]
        current_stage: The lead's current stage

    Returns:
        True if lead has been acknowledged, False otherwise
    """
    # Check current stage
    if current_stage and ACKNOWLEDGED_STAGE in current_stage.lower():
        return True

    # Check stage history for any transition to/from acknowledged stage
    for transition in stage_history or []:
        to_stage = (transition.get("to_stage") or "").lower()
        if ACKNOWLEDGED_STAGE in to_stage:
            return True

    return False


def has_progressed_from_unacknowledged(stage_history: list[dict], current_stage: str = "") -> bool:
    """
    Check if a lead has progressed FROM the 'Appt Not Acknowledged' stage.

    Checks multiple indicators:
    1. Any transition with from_stage containing "not acknowledged"
    2. Any transition with to_stage containing "acknowledged" (but not "not acknowledged")
    3. Current stage contains "acknowledged" (but not "not acknowledged")

    Args:
        stage_history: List of stage transitions [{from_stage, to_stage, changed_at}]
        current_stage: The lead's current stage

    Returns:
        True if lead has moved forward from the unacknowledged stage, False otherwise
    """
    # Check if current stage indicates acknowledgment
    if current_stage:
        stage_lower = current_stage.lower()
        if "acknowledged" in stage_lower and "not acknowledged" not in stage_lower:
            return True

    for transition in stage_history or []:
        from_stage = (transition.get("from_stage") or "").lower()
        to_stage = (transition.get("to_stage") or "").lower()

        # Check if this transition moved FROM an unacknowledged stage
        if "not acknowledged" in from_stage:
            return True

        # Check if this transition moved TO an acknowledged stage
        if "acknowledged" in to_stage and "not acknowledged" not in to_stage:
            return True

    return False


def get_days_since_last_activity(
    stage_history: list[dict],
    latest_note: Optional[dict],
) -> int:
    """
    Calculate days since last activity (stage change or note).

    Args:
        stage_history: List of stage transitions
        latest_note: Latest note dict with 'time' field

    Returns:
        Days since last activity, or 9999 if no activity found
    """
    last_activity = None

    # Check stage history for last transition
    if stage_history:
        for transition in stage_history:
            changed_at = transition.get("changed_at")
            # Parse string dates (from cache) to datetime
            if isinstance(changed_at, str):
                try:
                    changed_at = datetime.fromisoformat(changed_at.replace("Z", "+00:00"))
                except ValueError:
                    changed_at = None
            if isinstance(changed_at, datetime):
                if last_activity is None or changed_at > last_activity:
                    last_activity = changed_at

    # Check note timestamp
    if latest_note:
        note_time = latest_note.get("time")
        if note_time:
            # Parse if string
            if isinstance(note_time, str):
                try:
                    # Handle ISO format with timezone
                    if "T" in note_time:
                        note_time = datetime.fromisoformat(note_time.replace("Z", "+00:00"))
                    else:
                        note_time = None
                except ValueError:
                    note_time = None

            if isinstance(note_time, datetime):
                if last_activity is None or note_time > last_activity:
                    last_activity = note_time

    if last_activity is None:
        return 9999  # No activity found

    now = datetime.now(timezone.utc)
    if last_activity.tzinfo is None:
        last_activity = last_activity.replace(tzinfo=timezone.utc)

    return (now - last_activity).days


def has_note_since_appointment(
    latest_note: Optional[dict],
    appointment_date: Optional[datetime],
) -> bool:
    """
    Check if a note was added after the appointment date.

    Args:
        latest_note: Latest note dict with 'time' field
        appointment_date: The appointment date

    Returns:
        True if note exists and was added after appointment, False otherwise
    """
    if not latest_note or not appointment_date:
        return False

    note_time = latest_note.get("time")
    if not note_time:
        return False

    # Parse if string
    if isinstance(note_time, str):
        try:
            if "T" in note_time:
                note_time = datetime.fromisoformat(note_time.replace("Z", "+00:00"))
            else:
                return False
        except ValueError:
            return False

    if not isinstance(note_time, datetime):
        return False

    # Ensure both have timezone info for comparison
    if note_time.tzinfo is None:
        note_time = note_time.replace(tzinfo=timezone.utc)
    if appointment_date.tzinfo is None:
        appointment_date = appointment_date.replace(tzinfo=timezone.utc)

    return note_time > appointment_date


def get_lead_status_v2(
    lead: dict,
    stage_history: list[dict],
    latest_note: Optional[dict],
    deliveries: list[dict],
) -> tuple[str, str]:
    """
    Determine lead status with detailed classification reason.

    New classification logic:
    1. Terminal stage → Healthy ("Completed - [stage]")
    2. Delivery record exists → Healthy ("Delivery record found: [name]")
    3. Recent note since appointment → Healthy ("Actively worked - note added [date]")
    4. Stage skipped to later stage → Healthy ("Stage skipped - procedure not followed")
    5. No activity for 14+ days → Stale ("No activity for X days")
    6. Never acknowledged (early stage) → At Risk ("Appointment not acknowledged")
    7. Acknowledged but stalled → Needs Attention ("Acknowledged but no progress")
    8. Default → Healthy ("Recently created")

    Args:
        lead: Lead dictionary with 'id', 'name', 'current_stage', 'appointment_date'
        stage_history: List of stage transitions for the lead
        latest_note: Latest note dict with 'content' and 'time'
        deliveries: List of all delivery records

    Returns:
        Tuple of (status, reason) where status is 'stale', 'at_risk', 'needs_attention', or 'healthy'
    """
    lead_id = lead.get("id", "")
    lead_name = lead.get("name") or lead.get("Lead Name") or ""
    current_stage = lead.get("current_stage") or lead.get("Stage") or ""
    appointment_date = lead.get("appointment_date") or lead.get("Appointment Date")
    lead_address = lead.get("street_address") or lead.get("Street_Address") or ""
    lead_zip = lead.get("zip_code") or lead.get("Zip_Code") or ""

    stage_lower = current_stage.lower() if current_stage else ""

    # 1. Terminal/completion stages - always healthy
    terminal_stages = (
        "green/ delivered",
        "green/delivered",
        "delivery requested",
        "red/ rejected",
        "red/rejected",
        "green/no operator",
        "green/no-operator",
        "declined by operator",
        "green - lll fulfilled",
        "red/not viable",
    )
    for terminal in terminal_stages:
        if terminal in stage_lower:
            return ("healthy", f"Completed - {current_stage}")

    # 2. Check for matching delivery record
    matching_delivery = find_matching_delivery(lead_id, lead_name, deliveries, lead_address, lead_zip)
    if matching_delivery:
        delivery_name = matching_delivery.get("name", "Unknown")
        delivery_id = matching_delivery.get("id")
        if delivery_id:
            delivery_link = format_delivery_link(delivery_id)
            return ("healthy", f"Delivery record found: [{delivery_name}]({delivery_link})")
        else:
            return ("healthy", f"Delivery record found: {delivery_name}")

    # 3. Check for recent note since appointment
    if has_note_since_appointment(latest_note, appointment_date):
        note_time = latest_note.get("time")
        if isinstance(note_time, str):
            try:
                note_time = datetime.fromisoformat(note_time.replace("Z", "+00:00"))
            except ValueError:
                note_time = None

        if isinstance(note_time, datetime):
            date_str = note_time.strftime("%b %d, %Y")
            return ("healthy", f"Actively worked - note added {date_str}")
        else:
            return ("healthy", "Actively worked - recent note added")

    # 4. Check for no activity (Stale) - must come before other checks
    days_since_activity = get_days_since_last_activity(stage_history, latest_note)
    if days_since_activity >= STALE_NO_ACTIVITY_DAYS:
        return ("stale", f"No activity for {days_since_activity} days")

    # 5. Check if lead has progressed from "Appt Not Acknowledged"
    progressed = has_progressed_from_unacknowledged(stage_history, current_stage)

    # 6. Progressed but no notes - Needs Attention
    # Someone moved the lead forward but didn't document with notes
    if progressed:
        return ("needs_attention", "Stage progressed but no notes added since appointment")

    # 7. Never progressed from unacknowledged - At Risk
    # Lead is still stuck in initial unacknowledged state
    return ("at_risk", "Appointment has never been acknowledged")


# Centralized status configuration - single source of truth for emoji, color, and labels
STATUS_CONFIG = {
    "stale": {"emoji": "🔴", "color": "#dc3545", "label": "Stale"},
    "at_risk": {"emoji": "🟡", "color": "#ffc107", "label": "At Risk"},
    "needs_attention": {"emoji": "🟠", "color": "#fd7e14", "label": "Needs Attention"},
    "healthy": {"emoji": "🟢", "color": "#28a745", "label": "Healthy"},
}

# For backwards compatibility
STATUS_EMOJI_MAP = {k: v["emoji"] for k, v in STATUS_CONFIG.items()}


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
    for key, config in STATUS_CONFIG.items():
        if key in status_lower:
            return config["emoji"]
    return ""


def get_status_color(status_key: str) -> str:
    """
    Get hex color for a status key.

    Args:
        status_key: Status key ('stale', 'at_risk', 'needs_attention', 'healthy')

    Returns:
        Hex color string (e.g., '#dc3545') or gray if unknown
    """
    return STATUS_CONFIG.get(status_key, {}).get("color", "#6c757d")


def get_status_chart_config() -> list[tuple[str, str, str]]:
    """
    Get status configuration for chart rendering.

    Returns:
        List of tuples: (status_key, label, color)
        Ordered: stale, at_risk, needs_attention, healthy
    """
    order = ["stale", "at_risk", "needs_attention", "healthy"]
    return [(key, STATUS_CONFIG[key]["label"], STATUS_CONFIG[key]["color"]) for key in order]


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


def format_zoho_link(lead_id: str) -> str:
    """
    Generate Zoho CRM deep link for a lead record.

    Args:
        lead_id: The Zoho record ID

    Returns:
        URL to open the record in Zoho CRM
    """
    return f"https://crm.zoho.com/crm/{ZOHO_ORG_ID}/tab/{ZOHO_LOCATINGS_MODULE}/{lead_id}"


def format_leads_for_display(
    leads: list[dict],
    stage_histories: Optional[dict[str, list[dict]]] = None,
    notes: Optional[dict[str, dict]] = None,
    deliveries: Optional[list[dict]] = None,
) -> list[dict]:
    """
    Transform lead data for table display.

    Args:
        leads: List of lead dictionaries from get_leads_with_appointments()
        stage_histories: Optional dict mapping lead_id to stage history list
        notes: Optional dict mapping lead_id to note dict
        deliveries: Optional list of delivery records for cross-reference

    Returns:
        List of dictionaries formatted for display with columns:
        - id (for fetching stage history)
        - Lead Name
        - Appointment Date
        - Days (days since appointment)
        - Status: stale, at_risk, needs_attention, healthy
        - classification_reason: Human-readable reason for the classification
        - Stage
        - Locator
        - Phone (tel: link or None)
        - Email (mailto: link or None)
        - zoho_link (URL to Zoho CRM record)
    """
    result = []
    use_v2_classification = stage_histories is not None and deliveries is not None

    for lead in leads:
        days = calculate_days_since(lead["appointment_date"]) if lead.get("appointment_date") else None
        stage = lead.get("current_stage")
        lead_id = lead.get("id")

        status = None
        classification_reason = None

        if use_v2_classification and lead_id:
            # Use new v2 classification with full context
            lead_stage_history = stage_histories.get(lead_id, [])
            lead_note = notes.get(lead_id) if notes else None
            status, classification_reason = get_lead_status_v2(
                lead, lead_stage_history, lead_note, deliveries
            )
        else:
            # Fallback to legacy classification
            days_since_modified = None
            if lead.get("modified_time"):
                days_since_modified = calculate_days_since(lead["modified_time"])
            status = get_lead_status(days, stage, days_since_modified) if days is not None else None
            classification_reason = None

        result.append({
            "id": lead_id,
            "Lead Name": safe_display(lead.get("name")),
            "Appointment Date": format_date(lead.get("appointment_date")),
            "Days": days,
            "Status": format_status_display(status),
            "classification_reason": classification_reason,
            "Stage": safe_display(lead.get("current_stage")),
            "Locator": safe_display(lead.get("locator_name")),
            "Phone": format_phone_link(lead.get("locator_phone")),
            "Email": format_email_link(lead.get("locator_email")),
            "zoho_link": format_zoho_link(lead_id) if lead_id else None,
        })
    return result


def sort_by_urgency(leads: list[dict]) -> list[dict]:
    """
    Sort leads by urgency: stale first, then at_risk, then needs_attention, then healthy.

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

        # Status priority: stale=0, at_risk=1, needs_attention=2, healthy/other=3
        if "stale" in status:
            priority = 0
        elif "at_risk" in status:
            priority = 1
        elif "needs_attention" in status:
            priority = 2
        else:
            priority = 3

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
        Dictionary with counts: {"stale": N, "at_risk": N, "needs_attention": N, "healthy": N}
        Note: Leads with None or empty Status are counted as "healthy".
        The sum of all counts always equals len(leads).
    """
    counts = {"stale": 0, "at_risk": 0, "needs_attention": 0, "healthy": 0}
    for lead in leads:
        status = lead.get("Status") or ""
        if "stale" in status:
            counts["stale"] += 1
        elif "at_risk" in status:
            counts["at_risk"] += 1
        elif "needs_attention" in status:
            counts["needs_attention"] += 1
        else:
            counts["healthy"] += 1
    return counts


def _get_status_key(status: str) -> str:
    """Extract status key from formatted status string."""
    status_lower = (status or "").lower()
    if "stale" in status_lower:
        return "stale"
    elif "at_risk" in status_lower:
        return "at_risk"
    elif "needs_attention" in status_lower:
        return "needs_attention"
    return "healthy"


def get_about_to_go_stale(leads: list[dict]) -> list[dict]:
    """
    Get leads that are about to go stale (at_risk status, 5-6 days).

    These are the highest priority leads that need action TODAY to prevent
    them from crossing the 7-day stale threshold.

    Args:
        leads: List of formatted lead dictionaries (from format_leads_for_display)

    Returns:
        List of at-risk leads sorted by days descending (closest to stale first).
        Each dict includes a 'days_until_stale' field.
    """
    priority_leads = []

    for lead in leads:
        status = lead.get("Status") or ""
        days = lead.get("Days")

        # Only include at_risk leads (5-6 days)
        if "at_risk" in status.lower() and days is not None:
            # Calculate days until stale
            days_until_stale = STALE_THRESHOLD_DAYS - days

            priority_lead = lead.copy()
            priority_lead["days_until_stale"] = days_until_stale
            priority_leads.append(priority_lead)

    # Sort by days descending (6 days before 5 days - closest to stale first)
    priority_leads.sort(key=lambda x: -x.get("Days", 0))

    return priority_leads


def count_leads_by_stage(leads: list[dict]) -> list[dict]:
    """
    Count leads by stage for pipeline visualization.

    Args:
        leads: List of formatted lead dictionaries (from format_leads_for_display)

    Returns:
        List of dicts with stage counts, sorted by total descending:
        [{"stage": "Stage Name", "count": N, "stale": N, "at_risk": N, ...}, ...]
    """
    stage_data = {}
    for lead in leads:
        stage = lead.get("Stage") or "Unknown"
        if stage == "—":
            stage = "Unknown"

        if stage not in stage_data:
            stage_data[stage] = {"stage": stage, "count": 0, "stale": 0, "at_risk": 0, "needs_attention": 0, "healthy": 0}

        stage_data[stage]["count"] += 1
        status_key = _get_status_key(lead.get("Status"))
        stage_data[stage][status_key] += 1

    # Sort by count descending
    return sorted(stage_data.values(), key=lambda x: x["count"], reverse=True)


def get_locator_workload(leads: list[dict]) -> list[dict]:
    """
    Get lead counts by locator with status breakdown.

    Args:
        leads: List of formatted lead dictionaries (from format_leads_for_display)

    Returns:
        List of dicts sorted by urgency (stale + at_risk + needs_attention descending):
        [{"locator": "Name", "total": N, "stale": N, "at_risk": N, "needs_attention": N, "healthy": N}, ...]
    """
    locator_data = {}
    for lead in leads:
        locator = lead.get("Locator") or "Unknown"
        if locator == "—":
            locator = "Unknown"

        if locator not in locator_data:
            locator_data[locator] = {
                "locator": locator,
                "total": 0,
                "stale": 0,
                "at_risk": 0,
                "needs_attention": 0,
                "healthy": 0,
            }

        locator_data[locator]["total"] += 1
        status_key = _get_status_key(lead.get("Status"))
        locator_data[locator][status_key] += 1

    # Sort by urgency: stale first, then at_risk, then needs_attention, then by total
    def urgency_sort(item):
        return (
            -item["stale"],
            -item["at_risk"],
            -item["needs_attention"],
            -item["total"],
        )

    return sorted(locator_data.values(), key=urgency_sort)


# Filter constants
ALL_STAGES = "All Stages"
ALL_LOCATORS = "All Locators"
ALL_DATES = "All Dates"
ALL_STATUSES = "All Statuses"
DEFAULT_DATE_RANGE = "Last 90 Days + Future"

DATE_RANGE_PRESETS = [
    "All Dates",
    "Future",
    "Last 7 Days + Future",
    "Last 30 Days + Future",
    "Last 90 Days + Future",
    "Last 6 Months",
]

STATUS_FILTER_OPTIONS = [
    "All Statuses",
    "Stale",
    "At Risk",
    "Needs Attention",
    "Healthy",
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

    Uses the Days column (days since appointment) for filtering.
    Options with "+ Future" include both past dates and upcoming appointments.

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
        if date_range == "Future":
            include = days < 0
        elif date_range == "Last 7 Days + Future":
            include = days < 0 or (0 <= days <= 6)
        elif date_range == "Last 30 Days + Future":
            include = days < 0 or (0 <= days <= 29)
        elif date_range == "Last 90 Days + Future":
            include = days < 0 or (0 <= days <= 89)
        elif date_range == "Last 6 Months":
            include = 0 <= days <= 182

        if include:
            result.append(lead)

    return result


def filter_by_status(leads: list[dict], status_filter: str) -> list[dict]:
    """
    Filter leads by status category.

    Args:
        leads: List of formatted lead dictionaries
        status_filter: Status to filter by ("Stale", "At Risk", "Needs Attention", "Healthy")
                      or "All Statuses" to return all

    Returns:
        Filtered list of leads matching the status
    """
    if status_filter == ALL_STATUSES:
        return leads

    # Map filter option to status keyword in the formatted Status field
    status_keywords = {
        "Stale": "stale",
        "At Risk": "at_risk",
        "Needs Attention": "needs_attention",
        "Healthy": "healthy",
    }

    keyword = status_keywords.get(status_filter)
    if not keyword:
        return leads

    result = []
    for lead in leads:
        status = lead.get("Status") or ""
        status_lower = status.lower()

        if keyword == "healthy":
            # Healthy is anything that's not stale, at_risk, or needs_attention
            if "stale" not in status_lower and "at_risk" not in status_lower and "needs_attention" not in status_lower:
                result.append(lead)
        elif keyword in status_lower:
            result.append(lead)

    return result


def apply_filters(
    leads: list[dict],
    stage: str = ALL_STAGES,
    locator: str = ALL_LOCATORS,
    date_range: str = ALL_DATES,
    status_filter: str = ALL_STATUSES,
) -> list[dict]:
    """
    Apply all filters in sequence (AND logic).

    Args:
        leads: List of formatted lead dictionaries
        stage: Stage filter value
        locator: Locator filter value
        date_range: Date range filter value
        status_filter: Status filter value

    Returns:
        List of leads matching ALL filter criteria
    """
    result = leads
    result = filter_by_stage(result, stage)
    result = filter_by_locator(result, locator)
    result = filter_by_date_range(result, date_range)
    result = filter_by_status(result, status_filter)
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


# --- Historical Status Trend Calculation ---

def calculate_historical_status_trend(leads: list[dict], weeks: int = 4) -> list[dict]:
    """
    Calculate historical status counts by reconstructing what statuses would have been.

    For each week in the past N weeks, calculates what status each lead would have had
    based on their appointment date and current stage. Uses weekly sampling for clarity.

    Args:
        leads: List of formatted lead dictionaries (from format_leads_for_display)
        weeks: Number of weeks of history to calculate (default 4)

    Returns:
        List of weekly snapshots sorted by date ascending:
        [
            {
                "date": "2025-12-15",
                "date_label": "Dec 15",
                "stale": 45,
                "at_risk": 12,
                "needs_attention": 8,
                "healthy": 120,
            },
            ...
        ]

    Note:
        - Uses current stage values (can't reconstruct stage history)
        - Terminal stages are always healthy regardless of date
        - "Green - Approved By Locator" uses current modification date
    """
    today = datetime.now(timezone.utc).date()
    results = []

    # Pre-process leads to extract appointment dates and stages
    lead_data = []
    for lead in leads:
        days_value = lead.get("Days")
        if days_value is None:
            continue

        # Calculate the actual appointment date
        appt_date = today - timedelta(days=days_value)
        stage = lead.get("Stage", "")

        lead_data.append({
            "appt_date": appt_date,
            "stage": stage,
            "stage_lower": stage.lower() if stage else "",
        })

    # Terminal stages - always healthy regardless of time
    terminal_stages = (
        "green/ delivered",
        "delivery requested",
        "red/ rejected",
        "green/no operator",
        "declined by operator",
        "green - lll fulfilled",
        "red/not viable",
    )

    # Calculate status counts for each week (sample one day per week)
    for weeks_ago in range(weeks, -1, -1):  # Start from oldest to newest, include today
        historical_date = today - timedelta(weeks=weeks_ago)
        counts = {"stale": 0, "at_risk": 0, "needs_attention": 0, "healthy": 0}

        for ld in lead_data:
            # Calculate what "days since appointment" would have been on this historical date
            days_since_on_date = (historical_date - ld["appt_date"]).days

            # Skip leads with appointments after this historical date
            if days_since_on_date < 0:
                continue

            # Determine status for this lead on this historical date
            stage_lower = ld["stage_lower"]

            # Terminal stages are always healthy
            if stage_lower in terminal_stages:
                counts["healthy"] += 1
            # Green - Approved By Locator - simplified, treat as healthy
            # (we can't accurately reconstruct modification dates historically)
            elif stage_lower == "green - approved by locator":
                counts["healthy"] += 1
            # Standard staleness logic
            elif days_since_on_date >= STALE_THRESHOLD_DAYS:
                counts["stale"] += 1
            elif stage_lower == "appt not acknowledged":
                counts["at_risk"] += 1
            elif days_since_on_date >= AT_RISK_THRESHOLD_DAYS:
                counts["at_risk"] += 1
            else:
                counts["healthy"] += 1

        # Format date label
        if platform.system() == "Windows":
            date_label = historical_date.strftime("%b %#d")
        else:
            date_label = historical_date.strftime("%b %-d")

        results.append({
            "date": historical_date.isoformat(),
            "date_label": date_label,
            "stale": counts["stale"],
            "at_risk": counts["at_risk"],
            "needs_attention": counts["needs_attention"],
            "healthy": counts["healthy"],
        })

    return results


# --- Closing Ratio Calculations ---

# Stages that count as successful closes
SUCCESSFUL_CLOSE_STAGES = frozenset([
    "green/ delivered",
    "delivery requested",
    "green - lll fulfilled",
])

# Stages that count as failed closes
FAILED_CLOSE_STAGES = frozenset([
    "red/ rejected",
    "declined by operator",
    "red/not viable",
])

# Stages that are excluded from ratio (neutral outcome - no opportunity existed)
EXCLUDED_STAGES = frozenset([
    "green/no operator",
])


def get_closing_ratio_summary(leads: list[dict]) -> dict:
    """
    Calculate closing ratio summary from leads.

    Only includes leads that have reached a terminal stage (success or failure).
    Excludes "Green/No operator" as it represents no opportunity existing.

    Args:
        leads: List of formatted lead dictionaries (from format_leads_for_display)

    Returns:
        Dictionary with:
        - ratio: Closing ratio as percentage (0-100), or None if no completed leads
        - successful: Count of successfully closed leads
        - failed: Count of failed leads
        - total_completed: Total leads that reached terminal stage (successful + failed)
        - active: Count of leads still in progress
    """
    successful = 0
    failed = 0
    active = 0

    for lead in leads:
        stage = lead.get("Stage", "")
        stage_lower = stage.lower() if stage else ""

        if stage_lower in SUCCESSFUL_CLOSE_STAGES:
            successful += 1
        elif stage_lower in FAILED_CLOSE_STAGES:
            failed += 1
        elif stage_lower not in EXCLUDED_STAGES:
            # Not a terminal stage and not excluded - still active
            active += 1

    total_completed = successful + failed
    ratio = (successful / total_completed * 100) if total_completed > 0 else None

    return {
        "ratio": ratio,
        "successful": successful,
        "failed": failed,
        "total_completed": total_completed,
        "active": active,
    }


def get_closing_ratio_by_month(leads: list[dict], months: int = 6) -> list[dict]:
    """
    Calculate closing ratio by monthly cohort based on appointment date.

    Groups leads by the month of their appointment, then calculates the
    closing ratio for each cohort. Only includes leads with terminal stages.

    Args:
        leads: List of formatted lead dictionaries (from format_leads_for_display)
        months: Number of months of history to include (default 6)

    Returns:
        List of monthly cohort dictionaries sorted by month ascending:
        [
            {
                "month": "2025-10",
                "month_label": "Oct 2025",
                "successful": 35,
                "failed": 12,
                "active": 3,
                "total_completed": 47,
                "ratio": 74.5,
            },
            ...
        ]
    """
    from collections import defaultdict
    from datetime import datetime, timedelta

    # Calculate cutoff date
    today = datetime.now(timezone.utc).date()
    cutoff_date = today - timedelta(days=months * 30)

    # Group leads by month
    monthly_data = defaultdict(lambda: {"successful": 0, "failed": 0, "active": 0})

    for lead in leads:
        days = lead.get("Days")
        if days is None:
            continue

        # Calculate appointment date from days since
        appt_date = today - timedelta(days=days)

        # Skip if before cutoff
        if appt_date < cutoff_date:
            continue

        # Get month key (YYYY-MM format for sorting)
        month_key = appt_date.strftime("%Y-%m")

        # Categorize by stage
        stage = lead.get("Stage", "")
        stage_lower = stage.lower() if stage else ""

        if stage_lower in SUCCESSFUL_CLOSE_STAGES:
            monthly_data[month_key]["successful"] += 1
        elif stage_lower in FAILED_CLOSE_STAGES:
            monthly_data[month_key]["failed"] += 1
        elif stage_lower not in EXCLUDED_STAGES:
            monthly_data[month_key]["active"] += 1

    # Convert to sorted list with calculated ratios
    result = []
    for month_key in sorted(monthly_data.keys()):
        data = monthly_data[month_key]
        total_completed = data["successful"] + data["failed"]
        ratio = (data["successful"] / total_completed * 100) if total_completed > 0 else None

        # Parse month for label
        dt = datetime.strptime(month_key, "%Y-%m")
        month_label = dt.strftime("%b %Y")

        result.append({
            "month": month_key,
            "month_label": month_label,
            "successful": data["successful"],
            "failed": data["failed"],
            "active": data["active"],
            "total_completed": total_completed,
            "ratio": ratio,
        })

    return result


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


def get_conversion_funnel(leads: list[dict]) -> list[dict]:
    """
    Calculate conversion funnel data showing progression through pipeline.

    Tracks how many leads have progressed through each stage of the sales process:
    1. Total - All leads with appointments
    2. Acknowledged - Moved past "Appt Not Acknowledged"
    3. Approved - Reached approval stage or beyond
    4. Closed - Reached terminal success stage

    Args:
        leads: List of formatted lead dictionaries (from format_leads_for_display)

    Returns:
        List of funnel stages with counts:
        [{"stage": "Total Leads", "count": N, "pct": 100.0}, ...]
    """
    total = len(leads)
    if total == 0:
        return []

    # Count leads at each funnel stage
    acknowledged = 0
    approved = 0
    closed = 0

    # Stages that indicate progression past initial
    not_acknowledged_stage = "appt not acknowledged"

    # Stages indicating approval or beyond
    approval_stages = frozenset([
        "green - approved by locator",
        "green/ delivered",
        "delivery requested",
        "green - lll fulfilled",
        "green/no operator",
    ])

    for lead in leads:
        stage = lead.get("Stage", "")
        stage_lower = stage.lower() if stage else ""

        # Not in initial "unacknowledged" stage = acknowledged
        if stage_lower != not_acknowledged_stage:
            acknowledged += 1

        # In approval or terminal success stage
        if stage_lower in approval_stages or stage_lower in SUCCESSFUL_CLOSE_STAGES:
            approved += 1

        # In terminal success stage
        if stage_lower in SUCCESSFUL_CLOSE_STAGES:
            closed += 1

    return [
        {"stage": "Total Leads", "count": total, "pct": 100.0},
        {"stage": "Acknowledged", "count": acknowledged, "pct": round(acknowledged / total * 100, 1) if total else 0},
        {"stage": "Approved", "count": approved, "pct": round(approved / total * 100, 1) if total else 0},
        {"stage": "Closed", "count": closed, "pct": round(closed / total * 100, 1) if total else 0},
    ]
