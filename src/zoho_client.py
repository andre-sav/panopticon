"""
Zoho CRM API client module.

Responsibilities:
- OAuth 2.0 token management
- Access token refresh
- API request execution
- Error handling for API calls
- Lead data fetching
- Locator lookup from CSV
"""
import csv
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

import requests
import streamlit as st
from dateutil import parser as dateutil_parser
from json import JSONDecodeError

import re

from src.field_mapping import ZOHO_FIELD_MAP, map_zoho_lead
from src.cache import (
    get_cached_stage_history,
    set_cached_stage_history,
    set_cached_stage_histories_batch,
    get_cached_leads,
    set_cached_leads,
)

# Locator lookup cache (loaded from CSV)
_locator_lookup: Optional[dict] = None
LOCATORS_CSV_PATH = Path(__file__).parent.parent / "data" / "locators.csv"

# Constants
REQUEST_TIMEOUT = 30  # seconds (NFR5)
OAUTH_TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
TOKEN_EXPIRY_BUFFER = 300  # Refresh 5 minutes before expiry
MAX_RATE_LIMIT_RETRIES = 2  # Max retries on 429 rate limit
DEFAULT_RETRY_AFTER = 60  # Default wait time if Retry-After header missing

# Error types for UI differentiation (Story 1.6)
ERROR_TYPE_CONNECTION = "connection"
ERROR_TYPE_TIMEOUT = "timeout"
ERROR_TYPE_AUTH = "auth"
ERROR_TYPE_UNKNOWN = "unknown"


def _load_locator_lookup() -> dict:
    """
    Load locator lookup from CSV file.

    Returns:
        Dictionary mapping locator ID to locator info dict.
        Each entry contains: name, email.
    """
    global _locator_lookup
    if _locator_lookup is not None:
        return _locator_lookup

    _locator_lookup = {}

    if not LOCATORS_CSV_PATH.exists():
        logger.warning("Locators CSV not found at %s", LOCATORS_CSV_PATH)
        return _locator_lookup

    try:
        with open(LOCATORS_CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                locator_id = row.get("id", "").strip()
                if locator_id:
                    _locator_lookup[locator_id] = {
                        "name": row.get("name", "").strip() or None,
                        "email": row.get("email", "").strip() or None,
                    }
        logger.info("Loaded %d locators from CSV", len(_locator_lookup))
    except Exception as e:
        logger.error("Failed to load locators CSV: %s", e)

    return _locator_lookup


def get_locator_by_id(locator_id: str) -> Optional[dict]:
    """
    Get locator info by Zoho locator ID.

    Args:
        locator_id: Zoho locator ID (e.g., "1003657000068296073")

    Returns:
        Dict with 'name', 'email' or None if not found.
    """
    lookup = _load_locator_lookup()
    return lookup.get(locator_id)


def _init_session_state() -> None:
    """Initialize session state variables for token management."""
    if "zoho_access_token" not in st.session_state:
        st.session_state.zoho_access_token = None
    if "zoho_token_expiry" not in st.session_state:
        st.session_state.zoho_token_expiry = None
    if "zoho_error" not in st.session_state:
        st.session_state.zoho_error = None
    if "zoho_error_type" not in st.session_state:
        st.session_state.zoho_error_type = None
    if "zoho_partial_error" not in st.session_state:
        st.session_state.zoho_partial_error = None


def _set_error(message: str, error_type: str) -> None:
    """Set error message and type in session state."""
    st.session_state.zoho_error = message
    st.session_state.zoho_error_type = error_type


def _clear_error() -> None:
    """Clear error state."""
    st.session_state.zoho_error = None
    st.session_state.zoho_error_type = None


def _get_credentials() -> dict:
    """
    Read Zoho credentials from Streamlit secrets.

    Returns:
        dict with client_id, client_secret, refresh_token, api_domain

    Raises:
        KeyError: If required secrets are missing
    """
    return {
        "client_id": st.secrets["zoho"]["client_id"],
        "client_secret": st.secrets["zoho"]["client_secret"],
        "refresh_token": st.secrets["zoho"]["refresh_token"],
        "api_domain": st.secrets["zoho"]["api_domain"],
    }


def refresh_access_token() -> Optional[str]:
    """
    Exchange refresh token for a new access token.

    Returns:
        Access token string if successful, None if failed.
        On failure, stores error message in st.session_state.zoho_error
    """
    _init_session_state()
    logger.info("Refreshing Zoho access token")

    try:
        credentials = _get_credentials()
    except KeyError:
        logger.error("Zoho credentials not configured in secrets")
        _set_error(
            "Zoho credentials not configured. "
            "Please check .streamlit/secrets.toml configuration.",
            ERROR_TYPE_AUTH,
        )
        return None

    payload = {
        "grant_type": "refresh_token",
        "client_id": credentials["client_id"],
        "client_secret": credentials["client_secret"],
        "refresh_token": credentials["refresh_token"],
    }

    try:
        start_time = time.time()
        response = requests.post(
            OAUTH_TOKEN_URL,
            data=payload,
            timeout=REQUEST_TIMEOUT,
        )
        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)

            # Store token and calculate expiry time
            st.session_state.zoho_access_token = access_token
            st.session_state.zoho_token_expiry = (
                datetime.now(timezone.utc).timestamp() + expires_in
            )
            _clear_error()

            logger.info("Token refresh successful (%.2fs), expires in %ds", elapsed, expires_in)
            return access_token
        else:
            # Auth failed - do NOT log credentials (AC#4)
            logger.error("Token refresh failed: HTTP %d (%.2fs)", response.status_code, elapsed)
            _set_error(
                "Session expired. Please refresh the page to reconnect.",
                ERROR_TYPE_AUTH,
            )
            return None

    except requests.exceptions.Timeout:
        logger.error("Token refresh timed out after %ds", REQUEST_TIMEOUT)
        _set_error(
            "Request timed out. Zoho may be slow. Please try again.",
            ERROR_TYPE_TIMEOUT,
        )
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error("Token refresh connection error: %s", type(e).__name__)
        _set_error(
            "Unable to connect to Zoho CRM. "
            "Please check your connection and try again.",
            ERROR_TYPE_CONNECTION,
        )
        return None
    except requests.exceptions.RequestException as e:
        logger.error("Token refresh request error: %s", type(e).__name__)
        _set_error(
            "An error occurred while connecting to Zoho CRM. "
            "Please try again.",
            ERROR_TYPE_UNKNOWN,
        )
        return None


def _is_token_expired() -> bool:
    """Check if the current access token is expired or about to expire."""
    _init_session_state()

    if st.session_state.zoho_access_token is None:
        return True

    if st.session_state.zoho_token_expiry is None:
        return True

    # Check if token expires within buffer time
    current_time = datetime.now(timezone.utc).timestamp()
    return current_time >= (st.session_state.zoho_token_expiry - TOKEN_EXPIRY_BUFFER)


def get_access_token() -> Optional[str]:
    """
    Get a valid access token, refreshing if necessary.

    Returns:
        Valid access token string, or None if unable to obtain one.
    """
    _init_session_state()

    if _is_token_expired():
        return refresh_access_token()

    return st.session_state.zoho_access_token


def _parse_retry_after(header_value: Optional[str]) -> int:
    """
    Parse Retry-After header value safely.

    Args:
        header_value: The Retry-After header value (may be seconds or date)

    Returns:
        Number of seconds to wait, defaults to DEFAULT_RETRY_AFTER on parse error
    """
    if header_value is None:
        return DEFAULT_RETRY_AFTER
    try:
        return int(header_value)
    except (ValueError, TypeError):
        # Header might be a date string or invalid - use default
        return DEFAULT_RETRY_AFTER


def _make_request(
    method: str,
    url: str,
    params: Optional[dict] = None,
    json_data: Optional[dict] = None,
    retry_on_401: bool = True,
    _rate_limit_retries: int = 0,
    _prefetched_token: Optional[str] = None,
) -> Optional[requests.Response]:
    """
    Make an authenticated API request to Zoho CRM.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Full URL to request
        params: Query parameters
        json_data: JSON body data
        retry_on_401: Whether to retry with fresh token on 401
        _rate_limit_retries: Internal counter for rate limit retries (do not set)
        _prefetched_token: Pre-fetched access token (for use in worker threads)

    Returns:
        Response object if successful, None if failed.
        On failure, stores error in st.session_state.zoho_error
    """
    # Use prefetched token if provided (avoids st.session_state in worker threads)
    if _prefetched_token:
        access_token = _prefetched_token
    else:
        _init_session_state()
        access_token = get_access_token()
        if access_token is None:
            return None

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
    }

    # Log request (exclude auth header)
    logger.debug("API request: %s %s", method, url)

    try:
        start_time = time.time()
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data,
            timeout=REQUEST_TIMEOUT,
        )
        elapsed = time.time() - start_time

        logger.debug("API response: %d (%.2fs)", response.status_code, elapsed)

        # Handle 401 Unauthorized - token may have expired
        # Skip retry if using prefetched token (can't refresh from worker threads)
        if response.status_code == 401 and retry_on_401 and not _prefetched_token:
            logger.warning("Got 401, refreshing token and retrying")
            # Force token refresh and retry once
            st.session_state.zoho_access_token = None
            st.session_state.zoho_token_expiry = None
            return _make_request(
                method=method,
                url=url,
                params=params,
                json_data=json_data,
                retry_on_401=False,  # Don't retry again
                _rate_limit_retries=_rate_limit_retries,
            )

        # Handle 429 Rate Limit with backoff retry
        if response.status_code == 429:
            retry_after = _parse_retry_after(response.headers.get("Retry-After"))

            # Retry if we haven't exceeded max retries
            if _rate_limit_retries < MAX_RATE_LIMIT_RETRIES:
                logger.warning(
                    "Rate limited (429), retry %d/%d after %ds",
                    _rate_limit_retries + 1,
                    MAX_RATE_LIMIT_RETRIES,
                    retry_after,
                )
                time.sleep(retry_after)
                return _make_request(
                    method=method,
                    url=url,
                    params=params,
                    json_data=json_data,
                    retry_on_401=retry_on_401,
                    _rate_limit_retries=_rate_limit_retries + 1,
                    _prefetched_token=_prefetched_token,
                )
            else:
                # Max retries exceeded
                logger.error("Rate limit retries exhausted")
                # Don't set error in session_state if using prefetched token (worker thread)
                if not _prefetched_token:
                    _set_error(
                        "Too many requests to Zoho CRM. "
                        "Rate limit exceeded after retries. Please try again later.",
                        ERROR_TYPE_CONNECTION,
                    )
                return None

        # Handle other error status codes
        if response.status_code >= 400:
            logger.error("API error: HTTP %d", response.status_code)
            if not _prefetched_token:
                _set_error(
                    f"Zoho CRM returned an error (status {response.status_code}). "
                    "Please try again or contact support if the issue persists.",
                    ERROR_TYPE_UNKNOWN,
                )
            return None

        # Success - clear any previous errors (skip in worker threads)
        if not _prefetched_token:
            _clear_error()
        return response

    except requests.exceptions.Timeout:
        logger.error("API request timed out after %ds", REQUEST_TIMEOUT)
        if not _prefetched_token:
            _set_error(
                "Request timed out. Zoho may be slow. Please try again.",
                ERROR_TYPE_TIMEOUT,
            )
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error("API connection error: %s", type(e).__name__)
        if not _prefetched_token:
            _set_error(
                "Unable to connect to Zoho CRM. "
                "Please check your connection and try again.",
                ERROR_TYPE_CONNECTION,
            )
        return None
    except requests.exceptions.RequestException as e:
        logger.error("API request error: %s", type(e).__name__)
        if not _prefetched_token:
            _set_error(
                "An error occurred while communicating with Zoho CRM. "
                "Please try again.",
                ERROR_TYPE_UNKNOWN,
            )
        return None


def get_api_domain() -> str:
    """Get the Zoho API domain from secrets."""
    try:
        return st.secrets["zoho"]["api_domain"]
    except KeyError:
        return "https://www.zohoapis.com"


def test_connection() -> tuple[bool, str]:
    """
    Test the Zoho CRM connection by attempting to get an access token.

    Returns:
        Tuple of (success: bool, message: str)
        - (True, "Connection successful") if credentials are valid
        - (False, error_message) if connection failed
    """
    _init_session_state()

    # Clear any cached token to force a fresh authentication
    st.session_state.zoho_access_token = None
    st.session_state.zoho_token_expiry = None
    _clear_error()  # Clear both error and error_type (M1 fix)

    token = refresh_access_token()

    if token is not None:
        return (True, "Connection successful")
    else:
        error = st.session_state.zoho_error or "Unknown error occurred"
        return (False, error)


def get_last_error() -> Optional[str]:
    """
    Get the last error message from Zoho API operations.

    Returns:
        Error message string, or None if no error.
    """
    _init_session_state()
    return st.session_state.zoho_error


def get_error_type() -> Optional[str]:
    """
    Get the type of the last error.

    Returns:
        Error type constant (ERROR_TYPE_*) or None if no error.
    """
    _init_session_state()
    return st.session_state.zoho_error_type


def get_partial_error() -> Optional[str]:
    """
    Get partial error message (when some data loaded but with warnings).

    Returns:
        Partial error message string, or None if no partial error.
    """
    _init_session_state()
    return st.session_state.zoho_partial_error


def set_partial_error(message: str) -> None:
    """Set a partial error warning message."""
    _init_session_state()
    st.session_state.zoho_partial_error = message


def clear_partial_error() -> None:
    """Clear the partial error warning message."""
    _init_session_state()
    st.session_state.zoho_partial_error = None


def clear_error() -> None:
    """Clear all stored error messages."""
    _init_session_state()
    st.session_state.zoho_error = None
    st.session_state.zoho_error_type = None


def parse_zoho_date(date_string: Optional[str]) -> Optional[datetime]:
    """
    Parse Zoho date string to UTC datetime.

    Args:
        date_string: ISO 8601 date string from Zoho (e.g., "2026-01-07T10:30:00-05:00")

    Returns:
        datetime object in UTC timezone, or None if parsing fails or input is empty

    Note:
        Naive datetimes (without timezone) are assumed to be UTC.
    """
    if not date_string:
        return None
    try:
        dt = dateutil_parser.parse(date_string)
        # Handle naive datetime by assuming UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _map_and_parse_lead(zoho_record: dict) -> dict:
    """
    Map Zoho field names to internal names and parse date fields.

    Args:
        zoho_record: Raw lead record from Zoho API

    Returns:
        Lead dictionary with internal field names and parsed dates
    """
    lead = map_zoho_lead(zoho_record)

    # Handle Locator_Name lookup field
    # COQL returns {id} only, so look up name/email from CSV
    locator_data = lead.get("locator_name")
    if isinstance(locator_data, dict):
        locator_id = locator_data.get("id")
        locator_name = locator_data.get("name")  # May be present from standard API

        # Look up locator details from CSV
        if locator_id:
            locator_info = get_locator_by_id(locator_id)
            if locator_info:
                if not locator_name:
                    locator_name = locator_info.get("name")
                lead["locator_email"] = locator_info.get("email")

        lead["locator_name"] = locator_name

    # Parse date fields
    lead["appointment_date"] = parse_zoho_date(lead.get("appointment_date"))
    lead["modified_time"] = parse_zoho_date(lead.get("modified_time"))

    return lead


def _serialize_leads_for_cache(leads: list[dict]) -> list[dict]:
    """Convert datetime objects to ISO strings for JSON storage."""
    serialized = []
    for lead in leads:
        lead_copy = lead.copy()
        if lead_copy.get("appointment_date"):
            lead_copy["appointment_date"] = lead_copy["appointment_date"].isoformat()
        if lead_copy.get("modified_time"):
            lead_copy["modified_time"] = lead_copy["modified_time"].isoformat()
        serialized.append(lead_copy)
    return serialized


def _deserialize_leads_from_cache(leads: list[dict]) -> list[dict]:
    """Convert ISO strings back to datetime objects from cache."""
    deserialized = []
    for lead in leads:
        lead_copy = lead.copy()
        if lead_copy.get("appointment_date"):
            lead_copy["appointment_date"] = parse_zoho_date(lead_copy["appointment_date"])
        if lead_copy.get("modified_time"):
            lead_copy["modified_time"] = parse_zoho_date(lead_copy["modified_time"])
        deserialized.append(lead_copy)
    return deserialized


def get_leads_with_appointments(bypass_cache: bool = False) -> list[dict]:
    """
    Fetch all leads with scheduled appointments from Zoho CRM.

    Uses Supabase cache with 24-hour TTL to reduce API calls.
    Uses COQL to filter records with appointments server-side.
    Locator names/emails are looked up from local CSV cache.

    Args:
        bypass_cache: If True, skip cache and fetch fresh from API (for Refresh button)

    Returns:
        List of lead dictionaries with mapped field names.
        Empty list if API error occurs.

    Lead dictionary structure:
        {
            "id": str,
            "name": str | None,
            "appointment_date": datetime | None,
            "current_stage": str | None,
            "locator_name": str | None,
            "locator_email": str | None,
        }
    """
    _init_session_state()

    # Check cache first (unless bypassed)
    if not bypass_cache:
        cached_leads = get_cached_leads()
        if cached_leads is not None:
            return _deserialize_leads_from_cache(cached_leads)

    logger.info("Fetching leads with appointments from API")

    # Use COQL to filter records with appointments server-side (efficient)
    # Note: COQL doesn't expand lookup fields, so Locator_Name returns ID only
    # Locator details are looked up from local CSV cache
    coql_query = """
        SELECT id, Name, APPT_Date, Stage, Locator_Name, Street_Address, Zip_Code, Created_Time, Modified_Time, Misc_Notes, Misc_Notes_Long
        FROM Locatings
        WHERE APPT_Date is not null
        ORDER BY APPT_Date DESC
        LIMIT 2000
    """.strip()

    url = f"{get_api_domain()}/crm/v8/coql"

    try:
        response = _make_request("POST", url, json_data={"select_query": coql_query})
        if response is None:
            logger.warning("Failed to fetch leads (no response)")
            return []  # Error already captured in _make_request

        data = response.json()
        leads_data = data.get("data", [])

        leads = [_map_and_parse_lead(lead) for lead in leads_data]
        logger.info("Fetched %d leads with appointments from API", len(leads))

        # Cache the results
        set_cached_leads(_serialize_leads_for_cache(leads))

        return leads

    except JSONDecodeError:
        logger.error("Invalid JSON response from Zoho CRM")
        _set_error("Invalid response from Zoho CRM.", ERROR_TYPE_UNKNOWN)
        return []
    except (KeyError, TypeError, AttributeError) as e:
        logger.error("Error processing lead data: %s", type(e).__name__)
        _set_error(f"Error processing lead data: {type(e).__name__}", ERROR_TYPE_UNKNOWN)
        return []


def get_stage_history(lead_id: str, current_stage: str = None) -> list[dict] | None:
    """
    Fetch stage transition history for a lead from Zoho CRM Timeline API.

    Uses Supabase cache to reduce API calls. Cached data is used if available
    and not expired (24-hour TTL). Smart invalidation compares the lead's
    current stage against cached history to detect changes.

    Args:
        lead_id: The Zoho CRM lead ID
        current_stage: The lead's current stage (for smart cache invalidation).
            If provided and doesn't match the last cached stage, cache is invalidated.

    Returns:
        List of stage transition dictionaries in chronological order (oldest first).
        Each dictionary contains:
            - "from_stage": Previous stage (None for initial stage)
            - "to_stage": New stage
            - "changed_at": datetime of the change (UTC)

        Returns empty list [] if no stage history exists.
        Returns None if API error occurs (distinguishes error from empty).

    Note:
        Uses Zoho CRM Timeline API to get field change history.
        Filters for Stage field changes only.
    """
    _init_session_state()

    # Check cache first
    cached = get_cached_stage_history(lead_id)
    if cached is not None:
        # Smart invalidation: compare current stage with last cached stage
        if current_stage and cached:
            last_cached_stage = cached[-1].get("to_stage")
            if last_cached_stage and last_cached_stage != current_stage:
                logger.info(
                    "Cache invalidated for lead %s: stage changed from '%s' to '%s'",
                    lead_id, last_cached_stage, current_stage
                )
                cached = None  # Invalidate - will fetch fresh below

    if cached is not None:
        # Convert cached datetime strings back to datetime objects
        for transition in cached:
            if isinstance(transition.get("changed_at"), str):
                transition["changed_at"] = parse_zoho_date(transition["changed_at"])
        logger.debug("Using cached stage history for lead %s (%d transitions)", lead_id, len(cached))
        return cached

    logger.info("Fetching stage history for lead %s from API", lead_id)

    # Timeline API requires v5+
    url = f"{get_api_domain()}/crm/v5/Locatings/{lead_id}/__timeline"
    params = {
        "per_page": 100,  # Get up to 100 timeline events
    }

    try:
        response = _make_request("GET", url, params=params)
        if response is None:
            logger.warning("Failed to fetch stage history for lead %s", lead_id)
            return None  # API error - distinct from empty history

        data = response.json()
        timeline_events = data.get("__timeline", [])

        # Filter for Stage field changes and extract transition info
        stage_transitions = []
        for event in timeline_events:
            # Check if this event contains a Stage field change
            field_history = event.get("field_history") or []
            for field_change in field_history:
                if field_change.get("api_name") == "Stage":
                    # Parse the timestamp (v5 uses audited_time)
                    audited_time = event.get("audited_time")
                    changed_at = parse_zoho_date(audited_time)

                    # v5 format: _value contains {new, old}
                    value_obj = field_change.get("_value", {})
                    transition = {
                        "from_stage": value_obj.get("old"),
                        "to_stage": value_obj.get("new"),
                        "changed_at": changed_at,
                    }
                    stage_transitions.append(transition)

        # Sort by timestamp (oldest first for chronological order)
        stage_transitions.sort(
            key=lambda x: x["changed_at"] if x["changed_at"] else datetime.min.replace(tzinfo=timezone.utc)
        )

        logger.info("Found %d stage transitions for lead %s", len(stage_transitions), lead_id)

        # If current stage doesn't match last transition's to_stage,
        # add a synthetic entry to prevent cache invalidation loops
        # (Zoho timeline API sometimes misses transitions)
        if current_stage and stage_transitions:
            last_to_stage = stage_transitions[-1].get("to_stage")
            if last_to_stage and last_to_stage != current_stage:
                logger.info(
                    "Adding synthetic transition for lead %s: '%s' -> '%s' (timeline gap)",
                    lead_id, last_to_stage, current_stage
                )
                synthetic_entry = {
                    "from_stage": last_to_stage,
                    "to_stage": current_stage,
                    "changed_at": datetime.now(timezone.utc),
                }
                stage_transitions.append(synthetic_entry)

        # Cache the result (convert datetimes to ISO strings for JSON storage)
        cache_data = []
        for t in stage_transitions:
            cache_entry = {
                "from_stage": t["from_stage"],
                "to_stage": t["to_stage"],
                "changed_at": t["changed_at"].isoformat() if t["changed_at"] else None,
            }
            cache_data.append(cache_entry)
        set_cached_stage_history(lead_id, cache_data)

        return stage_transitions

    except JSONDecodeError:
        logger.error("Invalid JSON response from Zoho CRM timeline API")
        return None  # API error
    except (KeyError, TypeError, AttributeError) as e:
        logger.error("Error processing stage history: %s", type(e).__name__)
        return None  # Processing error


def get_stage_histories_batch(leads: list[dict]) -> dict[str, list]:
    """
    Fetch stage history for multiple leads concurrently.

    Uses Supabase cache for leads that are cached. For uncached leads,
    fetches from Zoho Timeline API using concurrent requests for performance.

    Args:
        leads: List of lead dicts with 'id' and 'Stage' keys

    Returns:
        Dict mapping lead_id to stage history list.
        Missing/error leads are not included in the result.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from src.cache import get_cached_stage_histories_batch

    if not leads:
        return {}

    lead_ids = [lead.get("id") for lead in leads if lead.get("id")]
    leads_by_id = {lead.get("id"): lead for lead in leads if lead.get("id")}

    if not lead_ids:
        return {}

    # Batch fetch from cache first
    cached = get_cached_stage_histories_batch(lead_ids)
    result = {}
    uncached_leads = []

    for lead_id in lead_ids:
        if lead_id in cached:
            history = cached[lead_id]
            lead = leads_by_id.get(lead_id)
            # Support both formatted ('Stage') and raw ('current_stage') field names
            current_stage = lead.get("Stage") or lead.get("current_stage") if lead else None

            # Smart invalidation: check if cache matches current stage
            if current_stage and history:
                last_cached_stage = history[-1].get("to_stage") if history else None
                if last_cached_stage and last_cached_stage != current_stage:
                    # Cache is stale, need to refetch
                    uncached_leads.append(lead)
                    continue

            # Convert datetime strings to datetime objects
            for transition in history:
                if isinstance(transition.get("changed_at"), str):
                    transition["changed_at"] = parse_zoho_date(transition["changed_at"])

            result[lead_id] = history
        else:
            lead = leads_by_id.get(lead_id)
            if lead:
                uncached_leads.append(lead)

    if not uncached_leads:
        logger.debug("All %d stage histories served from cache", len(result))
        return result

    logger.info("Fetching stage history for %d uncached leads concurrently", len(uncached_leads))

    # Pre-fetch credentials in main thread to avoid Streamlit context issues in workers
    prefetched_token = get_access_token()
    prefetched_domain = get_api_domain()

    if not prefetched_token:
        logger.error("Cannot fetch stage history: no access token")
        return result

    # Fetch uncached leads concurrently (max 10 concurrent to avoid rate limits)
    # Note: Workers only fetch data - caching happens in main thread to avoid
    # Streamlit context issues with ThreadPoolExecutor
    def fetch_single(lead, token, domain):
        lead_id = lead.get("id")
        current_stage = lead.get("Stage")
        # Use internal fetch logic without cache check (we already checked)
        # Pass prefetched credentials to avoid st.session_state/st.secrets access in threads
        return lead_id, _fetch_stage_history_from_api(
            lead_id, current_stage,
            skip_cache=True,
            _prefetched_token=token,
            _api_domain=domain,
        )

    to_cache = {}  # Collect results to cache in main thread (dict for batch upsert)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_single, lead, prefetched_token, prefetched_domain) for lead in uncached_leads]
        for future in as_completed(futures):
            try:
                lead_id, history = future.result()
                if history is not None:
                    result[lead_id] = history
                    # Prepare cache data (convert datetime to ISO string)
                    cache_data = []
                    for t in history:
                        cache_data.append({
                            "from_stage": t["from_stage"],
                            "to_stage": t["to_stage"],
                            "changed_at": t["changed_at"].isoformat() if t["changed_at"] else None,
                        })
                    to_cache[lead_id] = cache_data
            except Exception as e:
                logger.error("Error in concurrent stage history fetch: %s", e)

    # Batch cache all results in a single request (much faster than individual writes)
    if to_cache:
        set_cached_stage_histories_batch(to_cache)

    logger.info("Batch fetch complete: %d total stage histories", len(result))
    return result


def _fetch_stage_history_from_api(
    lead_id: str,
    current_stage: str = None,
    skip_cache: bool = False,
    _prefetched_token: str = None,
    _api_domain: str = None,
) -> list[dict] | None:
    """
    Internal function to fetch stage history directly from Zoho API.

    This bypasses cache checks and is used by batch fetching.
    Results are cached after fetching unless skip_cache=True.

    Args:
        lead_id: The Zoho CRM lead ID
        current_stage: The lead's current stage (for synthetic entry if needed)
        skip_cache: If True, don't cache results (used when called from worker threads)
        _prefetched_token: Pre-fetched access token (avoids st.session_state in threads)
        _api_domain: Pre-fetched API domain (avoids st.secrets in threads)

    Returns:
        List of stage transitions or None on error
    """
    logger.info("Fetching stage history for lead %s from API", lead_id)

    api_domain = _api_domain or get_api_domain()
    url = f"{api_domain}/crm/v5/Locatings/{lead_id}/__timeline"
    params = {"per_page": 100}

    try:
        response = _make_request("GET", url, params=params, _prefetched_token=_prefetched_token)
        if response is None:
            logger.warning("Failed to fetch stage history for lead %s", lead_id)
            return None

        data = response.json()
        timeline_events = data.get("__timeline", [])

        stage_transitions = []
        for event in timeline_events:
            field_history = event.get("field_history") or []
            for field_change in field_history:
                if field_change.get("api_name") == "Stage":
                    audited_time = event.get("audited_time")
                    changed_at = parse_zoho_date(audited_time)
                    value_obj = field_change.get("_value", {})
                    transition = {
                        "from_stage": value_obj.get("old"),
                        "to_stage": value_obj.get("new"),
                        "changed_at": changed_at,
                    }
                    stage_transitions.append(transition)

        stage_transitions.sort(
            key=lambda x: x["changed_at"] if x["changed_at"] else datetime.min.replace(tzinfo=timezone.utc)
        )

        logger.info("Found %d stage transitions for lead %s", len(stage_transitions), lead_id)

        # Add synthetic entry if needed
        if current_stage and stage_transitions:
            last_to_stage = stage_transitions[-1].get("to_stage")
            if last_to_stage and last_to_stage != current_stage:
                logger.info(
                    "Adding synthetic transition for lead %s: '%s' -> '%s' (timeline gap)",
                    lead_id, last_to_stage, current_stage
                )
                stage_transitions.append({
                    "from_stage": last_to_stage,
                    "to_stage": current_stage,
                    "changed_at": datetime.now(timezone.utc),
                })

        # Cache the result (unless called from worker thread)
        if not skip_cache:
            cache_data = []
            for t in stage_transitions:
                cache_data.append({
                    "from_stage": t["from_stage"],
                    "to_stage": t["to_stage"],
                    "changed_at": t["changed_at"].isoformat() if t["changed_at"] else None,
                })
            set_cached_stage_history(lead_id, cache_data)

        return stage_transitions

    except JSONDecodeError:
        logger.error("Invalid JSON response from Zoho CRM timeline API")
        return None
    except (KeyError, TypeError, AttributeError) as e:
        logger.error("Error processing stage history: %s", type(e).__name__)
        return None


def get_notes_for_leads(lead_ids: list[str]) -> dict[str, dict]:
    """
    Fetch the most recent note for multiple leads from Zoho CRM.

    Uses Supabase cache to minimize API calls. Only fetches from API
    for leads not already in cache.

    Args:
        lead_ids: List of Zoho lead IDs

    Returns:
        Dict mapping lead_id to dict with 'content' and 'time' keys.
        Leads without notes will have empty content and None time.
    """
    from src.cache import get_cached_notes, set_cached_notes, NO_NOTES_MARKER

    _init_session_state()

    if not lead_ids:
        return {}

    # Get cached notes first (single query)
    cached_notes = get_cached_notes(lead_ids)

    # Compute uncached IDs from the result (no extra query needed)
    uncached_ids = [lid for lid in lead_ids if lid not in cached_notes]

    if not uncached_ids:
        logger.debug("All %d notes served from cache", len(lead_ids))
        return cached_notes

    logger.info("Fetching notes for %d uncached leads", len(uncached_ids))

    # Pre-fetch credentials in main thread to avoid Streamlit context issues in workers
    prefetched_token = get_access_token()
    prefetched_domain = get_api_domain()

    if not prefetched_token:
        logger.error("Cannot fetch notes: no access token")
        return cached_notes

    # Fetch notes from API for uncached leads - use concurrent requests for speed
    from concurrent.futures import ThreadPoolExecutor, as_completed

    fresh_notes = {}
    notes_to_cache = {}

    # Use thread pool for concurrent API calls (max 10 concurrent to avoid rate limits)
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_lead = {
            executor.submit(_fetch_latest_note_for_lead, lead_id, prefetched_token, prefetched_domain): lead_id
            for lead_id in uncached_ids
        }
        for future in as_completed(future_to_lead):
            lead_id = future_to_lead[future]
            try:
                result = future.result()
                if result:
                    fresh_notes[lead_id] = {"content": result["content"], "time": result["time"]}
                    notes_to_cache[lead_id] = {"content": result["content"], "time": result["time"]}
                else:
                    fresh_notes[lead_id] = {"content": "", "time": None}
                    notes_to_cache[lead_id] = {"content": NO_NOTES_MARKER, "time": None}
            except Exception as e:
                logger.error("Error fetching note for lead %s: %s", lead_id, e)
                fresh_notes[lead_id] = {"content": "", "time": None}
                notes_to_cache[lead_id] = {"content": NO_NOTES_MARKER, "time": None}

    # Cache all results (including "no notes" markers)
    if notes_to_cache:
        set_cached_notes(notes_to_cache)
        logger.debug("Cached notes for %d leads", len(notes_to_cache))

    # Combine cached and fresh
    all_notes = {**cached_notes, **fresh_notes}
    return all_notes


def _fetch_latest_note_for_lead(
    lead_id: str,
    _prefetched_token: str = None,
    _api_domain: str = None,
) -> dict | None:
    """
    Fetch the most recent note for a single lead from Zoho CRM API.

    Args:
        lead_id: The Zoho lead ID
        _prefetched_token: Pre-fetched access token (for worker threads)
        _api_domain: Pre-fetched API domain (for worker threads)

    Returns:
        Dict with 'content' and 'time' keys, or None if no notes or error.
    """
    # Use v2 API - v8 requires 'fields' parameter for Related Notes endpoint
    api_domain = _api_domain or get_api_domain()
    url = f"{api_domain}/crm/v2/Locatings/{lead_id}/Notes"

    try:
        response = _make_request(
            "GET", url,
            params={"per_page": 1, "sort_by": "Modified_Time", "sort_order": "desc"},
            _prefetched_token=_prefetched_token,
        )
        if response is None:
            return None

        # Handle empty response body (Zoho returns empty for leads with no notes)
        if not response.text or not response.text.strip():
            return None

        data = response.json()
        notes = data.get("data", [])

        if not notes:
            return None

        # Get the most recent note's content and timestamp
        latest_note = notes[0]
        # Try multiple possible field names, also check Note_Title as fallback
        note_content = (
            latest_note.get("Note_Content")
            or latest_note.get("note_content")
            or latest_note.get("Content")
            or latest_note.get("content")
            or latest_note.get("Note_Title")  # Fallback to title if no content
            or ""
        )

        # Strip HTML tags (Zoho notes contain <p>...</p> etc)
        if note_content:
            note_content = re.sub(r"<[^>]+>", "", note_content).strip()

        # Get the timestamp (Modified_Time or Created_Time)
        note_time = (
            latest_note.get("Modified_Time")
            or latest_note.get("modified_time")
            or latest_note.get("Created_Time")
            or latest_note.get("created_time")
        )

        if not note_content:
            return None

        return {"content": note_content, "time": note_time}

    except JSONDecodeError:
        # Empty response or invalid JSON means no notes
        return None
    except Exception as e:
        logger.error("Error fetching notes for lead %s: %s", lead_id, e)
        return None


def get_deliveries(bypass_cache: bool = False) -> list[dict]:
    """
    Fetch all delivery records from Zoho CRM Deliveries module.

    Uses Supabase cache with 24-hour TTL to reduce API calls.
    Used for cross-referencing with Locatings to determine if a lead
    has a corresponding delivery request.

    Args:
        bypass_cache: If True, skip cache and fetch fresh from API

    Returns:
        List of delivery dictionaries with fields:
            - id: Delivery record ID
            - name: Delivery name (for fuzzy matching)
            - locating_id: Linked Locating ID (if populated)
            - created_time: When delivery was created
    """
    from src.cache import get_cached_deliveries, set_cached_deliveries

    _init_session_state()

    # Check cache first (unless bypassed)
    if not bypass_cache:
        cached_deliveries = get_cached_deliveries()
        if cached_deliveries is not None:
            logger.debug("Using cached deliveries (%d records)", len(cached_deliveries))
            return cached_deliveries

    logger.info("Fetching deliveries from API")

    # Use COQL to fetch all deliveries
    # Note: Locatings lookup field returns ID only in COQL
    coql_query = """
        SELECT id, Name, Locatings, Address, Zip_Code, Created_Time
        FROM Deliveries
        WHERE id is not null
        ORDER BY Created_Time DESC
        LIMIT 2000
    """.strip()

    url = f"{get_api_domain()}/crm/v8/coql"

    try:
        response = _make_request("POST", url, json_data={"select_query": coql_query})
        if response is None:
            logger.warning("Failed to fetch deliveries (no response)")
            return []

        data = response.json()
        deliveries_data = data.get("data", [])

        deliveries = []
        for delivery in deliveries_data:
            # Extract Locatings lookup (returns {id} or None)
            locatings_lookup = delivery.get("Locatings")
            locating_id = None
            if isinstance(locatings_lookup, dict):
                locating_id = locatings_lookup.get("id")

            deliveries.append({
                "id": delivery.get("id"),
                "name": delivery.get("Name"),
                "locating_id": locating_id,
                "address": delivery.get("Address"),
                "zip_code": delivery.get("Zip_Code"),
                "created_time": delivery.get("Created_Time"),
            })

        logger.info("Fetched %d deliveries from API", len(deliveries))

        # Cache the results
        set_cached_deliveries(deliveries)

        return deliveries

    except JSONDecodeError:
        logger.error("Invalid JSON response from Zoho CRM for deliveries")
        _set_error("Invalid response from Zoho CRM.", ERROR_TYPE_UNKNOWN)
        return []
    except (KeyError, TypeError, AttributeError) as e:
        logger.error("Error processing delivery data: %s", type(e).__name__)
        _set_error(f"Error processing delivery data: {type(e).__name__}", ERROR_TYPE_UNKNOWN)
        return []
