"""
Zoho CRM API client module.

Responsibilities:
- OAuth 2.0 token management
- Access token refresh
- API request execution
- Error handling for API calls
- Lead data fetching
"""
import logging
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

import requests
import streamlit as st
from dateutil import parser as dateutil_parser
from json import JSONDecodeError

from src.field_mapping import ZOHO_FIELD_MAP, map_zoho_lead

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

    Returns:
        Response object if successful, None if failed.
        On failure, stores error in st.session_state.zoho_error
    """
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
        if response.status_code == 401 and retry_on_401:
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
                )
            else:
                # Max retries exceeded
                logger.error("Rate limit retries exhausted")
                _set_error(
                    "Too many requests to Zoho CRM. "
                    "Rate limit exceeded after retries. Please try again later.",
                    ERROR_TYPE_CONNECTION,
                )
                return None

        # Handle other error status codes
        if response.status_code >= 400:
            logger.error("API error: HTTP %d", response.status_code)
            _set_error(
                f"Zoho CRM returned an error (status {response.status_code}). "
                "Please try again or contact support if the issue persists.",
                ERROR_TYPE_UNKNOWN,
            )
            return None

        # Success - clear any previous errors
        _clear_error()
        return response

    except requests.exceptions.Timeout:
        logger.error("API request timed out after %ds", REQUEST_TIMEOUT)
        _set_error(
            "Request timed out. Zoho may be slow. Please try again.",
            ERROR_TYPE_TIMEOUT,
        )
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error("API connection error: %s", type(e).__name__)
        _set_error(
            "Unable to connect to Zoho CRM. "
            "Please check your connection and try again.",
            ERROR_TYPE_CONNECTION,
        )
        return None
    except requests.exceptions.RequestException as e:
        logger.error("API request error: %s", type(e).__name__)
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
    # Parse appointment_date to datetime
    lead["appointment_date"] = parse_zoho_date(lead.get("appointment_date"))
    return lead


def get_leads_with_appointments() -> list[dict]:
    """
    Fetch all leads with scheduled appointments from Zoho CRM.

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
            "locator_phone": str | None,
            "locator_email": str | None,
        }
    """
    _init_session_state()
    logger.info("Fetching leads with appointments")

    # Build field list from mapping
    fields = ",".join(ZOHO_FIELD_MAP.keys())

    url = f"{get_api_domain()}/crm/v2/Leads"
    params = {
        "fields": fields,
        "criteria": "(Appointment_Date:is_not_empty:)",
        "per_page": 200,
    }

    try:
        response = _make_request("GET", url, params=params)
        if response is None:
            logger.warning("Failed to fetch leads (no response)")
            return []  # Error already captured in _make_request

        data = response.json()
        leads_data = data.get("data", [])

        leads = [_map_and_parse_lead(lead) for lead in leads_data]
        logger.info("Fetched %d leads with appointments", len(leads))
        return leads

    except JSONDecodeError:
        logger.error("Invalid JSON response from Zoho CRM")
        _set_error("Invalid response from Zoho CRM.", ERROR_TYPE_UNKNOWN)
        return []
    except (KeyError, TypeError, AttributeError) as e:
        logger.error("Error processing lead data: %s", type(e).__name__)
        _set_error(f"Error processing lead data: {type(e).__name__}", ERROR_TYPE_UNKNOWN)
        return []


def get_stage_history(lead_id: str) -> list[dict] | None:
    """
    Fetch stage transition history for a lead from Zoho CRM Timeline API.

    Args:
        lead_id: The Zoho CRM lead ID

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
    logger.info("Fetching stage history for lead %s", lead_id)

    url = f"{get_api_domain()}/crm/v2/Leads/{lead_id}/__timeline"
    params = {
        "per_page": 100,  # Get up to 100 timeline events
        "filter": "field_update",  # Only field updates
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
            field_history = event.get("field_history", [])
            for field_change in field_history:
                if field_change.get("api_name") == "Stage":
                    # Parse the timestamp
                    done_time = event.get("done_time")
                    changed_at = parse_zoho_date(done_time)

                    transition = {
                        "from_stage": field_change.get("_previous_value"),
                        "to_stage": field_change.get("_value"),
                        "changed_at": changed_at,
                    }
                    stage_transitions.append(transition)

        # Sort by timestamp (oldest first for chronological order)
        stage_transitions.sort(
            key=lambda x: x["changed_at"] if x["changed_at"] else datetime.min.replace(tzinfo=timezone.utc)
        )

        logger.info("Found %d stage transitions for lead %s", len(stage_transitions), lead_id)
        return stage_transitions

    except JSONDecodeError:
        logger.error("Invalid JSON response from Zoho CRM timeline API")
        return None  # API error
    except (KeyError, TypeError, AttributeError) as e:
        logger.error("Error processing stage history: %s", type(e).__name__)
        return None  # Processing error
