"""
Supabase cache module for persistent storage.

Caches:
- Stage history: Avoids repeated calls to Zoho Timeline API
- Leads list: Avoids repeated COQL queries for the main leads list
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import streamlit as st

logger = logging.getLogger(__name__)

# Cache TTL - how long before we consider cached data stale
CACHE_TTL_HOURS = 24

# Supabase client singleton
_supabase_client = None


def _get_supabase_client():
    """Get or create Supabase client singleton."""
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    try:
        from supabase import create_client

        url = st.secrets.get("supabase", {}).get("url")
        key = st.secrets.get("supabase", {}).get("key")

        if not url or not key:
            logger.warning("Supabase credentials not configured - caching disabled")
            return None

        _supabase_client = create_client(url, key)
        logger.info("Supabase client initialized")
        return _supabase_client

    except ImportError:
        logger.warning("Supabase package not installed - caching disabled")
        return None
    except Exception as e:
        logger.error("Failed to initialize Supabase client: %s", e)
        return None


def is_cache_enabled() -> bool:
    """Check if caching is enabled and configured."""
    return _get_supabase_client() is not None


def get_cached_stage_history(lead_id: str) -> Optional[list]:
    """
    Get cached stage history for a lead.

    Args:
        lead_id: The Zoho lead ID

    Returns:
        List of stage transitions if cached and not expired, None otherwise
    """
    client = _get_supabase_client()
    if not client:
        return None

    try:
        response = client.table("stage_history_cache").select("*").eq("lead_id", lead_id).execute()

        if not response.data:
            return None

        record = response.data[0]
        cached_at = datetime.fromisoformat(record["cached_at"].replace("Z", "+00:00"))

        # Check if cache is still valid
        if datetime.now(timezone.utc) - cached_at > timedelta(hours=CACHE_TTL_HOURS):
            logger.debug("Cache expired for lead %s", lead_id)
            return None

        logger.debug("Cache hit for lead %s", lead_id)
        return record["stage_history"]

    except Exception as e:
        logger.error("Error reading from cache: %s", e)
        return None


def get_cached_stage_histories_batch(lead_ids: list[str]) -> dict[str, list]:
    """
    Get cached stage history for multiple leads in a single query.

    Args:
        lead_ids: List of Zoho lead IDs

    Returns:
        Dict mapping lead_id to stage history list. Missing leads not included.
    """
    client = _get_supabase_client()
    if not client or not lead_ids:
        return {}

    try:
        response = (
            client.table("stage_history_cache")
            .select("lead_id, stage_history, cached_at")
            .in_("lead_id", lead_ids)
            .execute()
        )

        if not response.data:
            return {}

        result = {}
        now = datetime.now(timezone.utc)
        for record in response.data:
            cached_at = datetime.fromisoformat(record["cached_at"].replace("Z", "+00:00"))
            # Check if cache is still valid
            if now - cached_at <= timedelta(hours=CACHE_TTL_HOURS):
                result[record["lead_id"]] = record["stage_history"]

        logger.debug("Batch cache hit for %d/%d leads", len(result), len(lead_ids))
        return result

    except Exception as e:
        logger.error("Error reading batch stage history from cache: %s", e)
        return {}


def set_cached_stage_history(lead_id: str, stage_history: list) -> bool:
    """
    Cache stage history for a lead.

    Args:
        lead_id: The Zoho lead ID
        stage_history: List of stage transitions to cache

    Returns:
        True if cached successfully, False otherwise
    """
    client = _get_supabase_client()
    if not client:
        return False

    try:
        # Upsert (insert or update)
        client.table("stage_history_cache").upsert({
            "lead_id": lead_id,
            "stage_history": stage_history,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

        logger.debug("Cached stage history for lead %s", lead_id)
        return True

    except Exception as e:
        logger.error("Error writing to cache: %s", e)
        return False


def clear_cache(lead_id: Optional[str] = None) -> bool:
    """
    Clear cached data.

    Args:
        lead_id: If provided, clear only this lead's cache. Otherwise clear all.

    Returns:
        True if cleared successfully, False otherwise
    """
    client = _get_supabase_client()
    if not client:
        return False

    try:
        if lead_id:
            client.table("stage_history_cache").delete().eq("lead_id", lead_id).execute()
            logger.info("Cleared cache for lead %s", lead_id)
        else:
            client.table("stage_history_cache").delete().neq("lead_id", "").execute()
            logger.info("Cleared all cache")
        return True

    except Exception as e:
        logger.error("Error clearing cache: %s", e)
        return False


# --- Leads List Cache ---

LEADS_CACHE_KEY = "leads_with_appointments"


def get_cached_leads() -> Optional[list]:
    """
    Get cached leads list.

    Returns:
        List of lead dictionaries if cached and not expired, None otherwise.
        Also returns the cached_at timestamp for display purposes.
    """
    client = _get_supabase_client()
    if not client:
        return None

    try:
        response = client.table("leads_cache").select("*").eq("cache_key", LEADS_CACHE_KEY).execute()

        if not response.data:
            return None

        record = response.data[0]
        cached_at = datetime.fromisoformat(record["cached_at"].replace("Z", "+00:00"))

        # Check if cache is still valid
        if datetime.now(timezone.utc) - cached_at > timedelta(hours=CACHE_TTL_HOURS):
            logger.info("Leads cache expired")
            return None

        logger.info("Leads cache hit (%d leads)", len(record["data"]))
        return record["data"]

    except Exception as e:
        logger.error("Error reading leads from cache: %s", e)
        return None


def get_leads_cache_age() -> Optional[datetime]:
    """
    Get the timestamp when leads were last cached.

    Returns:
        datetime of when cache was last updated, or None if no cache
    """
    client = _get_supabase_client()
    if not client:
        return None

    try:
        response = client.table("leads_cache").select("cached_at").eq("cache_key", LEADS_CACHE_KEY).execute()

        if not response.data:
            return None

        return datetime.fromisoformat(response.data[0]["cached_at"].replace("Z", "+00:00"))

    except Exception as e:
        logger.error("Error reading leads cache age: %s", e)
        return None


def set_cached_leads(leads: list) -> bool:
    """
    Cache the leads list.

    Args:
        leads: List of lead dictionaries to cache

    Returns:
        True if cached successfully, False otherwise
    """
    client = _get_supabase_client()
    if not client:
        return False

    try:
        client.table("leads_cache").upsert({
            "cache_key": LEADS_CACHE_KEY,
            "data": leads,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

        logger.info("Cached %d leads", len(leads))
        return True

    except Exception as e:
        logger.error("Error writing leads to cache: %s", e)
        return False


def clear_leads_cache() -> bool:
    """
    Clear the leads cache (used by Refresh button).

    Returns:
        True if cleared successfully, False otherwise
    """
    client = _get_supabase_client()
    if not client:
        return False

    try:
        client.table("leads_cache").delete().eq("cache_key", LEADS_CACHE_KEY).execute()
        logger.info("Cleared leads cache")
        return True

    except Exception as e:
        logger.error("Error clearing leads cache: %s", e)
        return False


def get_all_cached_stage_history() -> list[dict]:
    """
    Get all cached stage history for Sankey diagram visualization.

    Returns:
        List of all stage transitions from cache:
        [{"from_stage": str, "to_stage": str}, ...]
    """
    client = _get_supabase_client()
    if not client:
        return []

    try:
        response = client.table("stage_history_cache").select("stage_history").execute()

        if not response.data:
            return []

        # Flatten all transitions from all leads
        all_transitions = []
        for record in response.data:
            history = record.get("stage_history", [])
            for transition in history:
                if transition.get("from_stage") and transition.get("to_stage"):
                    all_transitions.append({
                        "from_stage": transition["from_stage"],
                        "to_stage": transition["to_stage"],
                    })

        logger.info("Retrieved %d stage transitions from cache", len(all_transitions))
        return all_transitions

    except Exception as e:
        logger.error("Error reading all stage history from cache: %s", e)
        return []


# --- Status Snapshots for Trend Tracking ---

def get_today_snapshot() -> Optional[dict]:
    """
    Check if today's status snapshot already exists.

    Returns:
        Snapshot dict if exists, None otherwise
    """
    client = _get_supabase_client()
    if not client:
        return None

    try:
        today = datetime.now(timezone.utc).date().isoformat()
        response = client.table("status_snapshots").select("*").eq("snapshot_date", today).execute()

        if response.data:
            return response.data[0]
        return None

    except Exception as e:
        logger.error("Error checking today's snapshot: %s", e)
        return None


def save_status_snapshot(counts: dict) -> bool:
    """
    Save today's status snapshot.

    Args:
        counts: Dict with keys: stale, at_risk, needs_attention, healthy

    Returns:
        True if saved successfully, False otherwise
    """
    client = _get_supabase_client()
    if not client:
        return False

    try:
        today = datetime.now(timezone.utc).date().isoformat()
        total = counts.get("stale", 0) + counts.get("at_risk", 0) + counts.get("needs_attention", 0) + counts.get("healthy", 0)

        client.table("status_snapshots").upsert({
            "snapshot_date": today,
            "stale_count": counts.get("stale", 0),
            "at_risk_count": counts.get("at_risk", 0),
            "needs_attention_count": counts.get("needs_attention", 0),
            "healthy_count": counts.get("healthy", 0),
            "total_count": total,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

        logger.info("Saved status snapshot for %s", today)
        return True

    except Exception as e:
        logger.error("Error saving status snapshot: %s", e)
        return False


def get_status_snapshots(days: int = 30) -> list[dict]:
    """
    Get status snapshots for the last N days.

    Args:
        days: Number of days of history to retrieve (default 30)

    Returns:
        List of snapshot dicts sorted by date ascending
    """
    client = _get_supabase_client()
    if not client:
        return []

    try:
        cutoff_date = (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()

        response = (
            client.table("status_snapshots")
            .select("*")
            .gte("snapshot_date", cutoff_date)
            .order("snapshot_date", desc=False)
            .execute()
        )

        return response.data or []

    except Exception as e:
        logger.error("Error retrieving status snapshots: %s", e)
        return []


# --- Notes Cache ---

# Marker for leads that have been checked but have no notes
NO_NOTES_MARKER = "__NO_NOTES__"


def get_cached_notes(lead_ids: list[str]) -> dict[str, str]:
    """
    Get cached notes for multiple leads.

    Uses session state to cache Supabase responses within a render cycle,
    preventing duplicate network calls on Streamlit reruns.

    Args:
        lead_ids: List of Zoho lead IDs

    Returns:
        Dict mapping lead_id to last_note text.
        Leads with NO_NOTES_MARKER are returned as empty string.
    """
    import streamlit as st

    if not lead_ids:
        return {}

    # Check session state cache first (per-render deduplication)
    cache_key = "notes_cache_session"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = {}

    session_cache = st.session_state[cache_key]

    # Find which lead_ids we already have in session cache
    result = {}
    missing_ids = []
    for lead_id in lead_ids:
        if lead_id in session_cache:
            result[lead_id] = session_cache[lead_id]
        else:
            missing_ids.append(lead_id)

    # If all requested IDs are cached, return early
    if not missing_ids:
        return result

    # Fetch missing IDs from Supabase
    client = _get_supabase_client()
    if not client:
        return result

    try:
        response = (
            client.table("notes_cache")
            .select("lead_id, last_note")
            .in_("lead_id", missing_ids)
            .execute()
        )

        # Process response and update both result and session cache
        fetched_ids = set()
        if response.data:
            for record in response.data:
                lead_id = record["lead_id"]
                note = record.get("last_note", "")
                fetched_ids.add(lead_id)
                if note == NO_NOTES_MARKER:
                    result[lead_id] = ""
                    session_cache[lead_id] = ""
                elif note:
                    result[lead_id] = note
                    session_cache[lead_id] = note

        # Mark IDs not found in Supabase as empty (prevents re-fetching)
        for lead_id in missing_ids:
            if lead_id not in fetched_ids:
                session_cache[lead_id] = ""

        return result

    except Exception as e:
        logger.error("Error reading notes from cache: %s", e)
        return result


def set_cached_notes(notes: dict[str, str]) -> bool:
    """
    Cache notes for multiple leads.

    Args:
        notes: Dict mapping lead_id to last_note text

    Returns:
        True if cached successfully, False otherwise
    """
    client = _get_supabase_client()
    if not client or not notes:
        return False

    try:
        now = datetime.now(timezone.utc).isoformat()
        records = [
            {
                "lead_id": lead_id,
                "last_note": note,
                "cached_at": now,
            }
            for lead_id, note in notes.items()
        ]

        client.table("notes_cache").upsert(records).execute()
        logger.info("Cached notes for %d leads", len(records))
        return True

    except Exception as e:
        logger.error("Error writing notes to cache: %s", e)
        return False


def clear_notes_cache() -> bool:
    """
    Clear all cached notes (used by Refresh button).

    Clears both session state cache and Supabase cache.

    Returns:
        True if cleared successfully, False otherwise
    """
    import streamlit as st

    # Clear session state cache
    st.session_state.pop("notes_cache_session", None)

    client = _get_supabase_client()
    if not client:
        return False

    try:
        client.table("notes_cache").delete().neq("lead_id", "").execute()
        logger.info("Cleared notes cache")
        return True

    except Exception as e:
        logger.error("Error clearing notes cache: %s", e)
        return False


def get_uncached_lead_ids(lead_ids: list[str]) -> list[str]:
    """
    Get list of lead IDs that don't have cached notes.

    Args:
        lead_ids: List of Zoho lead IDs to check

    Returns:
        List of lead IDs not in cache (including NO_NOTES_MARKER means cached)
    """
    client = _get_supabase_client()
    if not client or not lead_ids:
        return lead_ids

    try:
        response = (
            client.table("notes_cache")
            .select("lead_id, last_note")
            .in_("lead_id", lead_ids)
            .execute()
        )

        # Consider leads as "cached" if they have any entry (including NO_NOTES_MARKER)
        cached_ids = {
            record["lead_id"]
            for record in (response.data or [])
            if record.get("last_note")  # Any non-empty value including NO_NOTES_MARKER
        }
        return [lid for lid in lead_ids if lid not in cached_ids]

    except Exception as e:
        logger.error("Error checking notes cache: %s", e)
        return lead_ids
