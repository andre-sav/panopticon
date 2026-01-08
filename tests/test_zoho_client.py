"""
Unit tests for zoho_client module.

Tests OAuth token management, API request handling, and error scenarios.
Uses mocking to simulate Zoho API responses.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

# Mock streamlit before importing zoho_client
import sys
sys.modules['streamlit'] = MagicMock()

from src import zoho_client


class MockSessionState(dict):
    """Mock Streamlit session state that acts like a dict with attribute access."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(key)


@pytest.fixture
def mock_st():
    """Fixture to mock Streamlit with fresh session state."""
    mock_streamlit = MagicMock()
    mock_streamlit.session_state = MockSessionState()
    mock_streamlit.secrets = {
        "zoho": {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "refresh_token": "test-refresh-token",
            "api_domain": "https://www.zohoapis.com",
        }
    }
    with patch.object(zoho_client, 'st', mock_streamlit):
        yield mock_streamlit


@pytest.fixture
def mock_requests():
    """Fixture to mock the requests library."""
    with patch.object(zoho_client, 'requests') as mock_req:
        yield mock_req


class TestTokenManagement:
    """Tests for OAuth token management functions."""

    def test_refresh_access_token_success(self, mock_st, mock_requests):
        """Successful token refresh stores token in session state."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "expires_in": 3600,
            "api_domain": "https://www.zohoapis.com",
        }
        mock_requests.post.return_value = mock_response

        token = zoho_client.refresh_access_token()

        assert token == "new-access-token"
        assert mock_st.session_state.zoho_access_token == "new-access-token"
        assert mock_st.session_state.zoho_token_expiry is not None
        assert mock_st.session_state.zoho_error is None

    def test_refresh_access_token_auth_failure(self, mock_st, mock_requests):
        """Failed authentication returns None and stores error (AC#4 message)."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_requests.post.return_value = mock_response

        token = zoho_client.refresh_access_token()

        assert token is None
        assert mock_st.session_state.zoho_error is not None
        assert "Session expired" in mock_st.session_state.zoho_error

    def test_refresh_access_token_missing_credentials(self, mock_st, mock_requests):
        """Missing credentials returns None with helpful error."""
        mock_st.secrets = {}  # No zoho section

        token = zoho_client.refresh_access_token()

        assert token is None
        assert mock_st.session_state.zoho_error is not None
        assert "credentials not configured" in mock_st.session_state.zoho_error

    def test_refresh_access_token_timeout(self, mock_st, mock_requests):
        """Timeout during token refresh returns None with error."""
        import requests as real_requests
        mock_requests.post.side_effect = real_requests.exceptions.Timeout()
        mock_requests.exceptions = real_requests.exceptions

        token = zoho_client.refresh_access_token()

        assert token is None
        assert mock_st.session_state.zoho_error is not None
        assert "timed out" in mock_st.session_state.zoho_error

    def test_refresh_access_token_connection_error(self, mock_st, mock_requests):
        """Connection error during token refresh returns None with error."""
        import requests as real_requests
        mock_requests.post.side_effect = real_requests.exceptions.ConnectionError()
        mock_requests.exceptions = real_requests.exceptions

        token = zoho_client.refresh_access_token()

        assert token is None
        assert mock_st.session_state.zoho_error is not None
        assert "Unable to connect" in mock_st.session_state.zoho_error

    def test_get_access_token_returns_cached(self, mock_st, mock_requests):
        """get_access_token returns cached token if not expired."""
        # Set up valid cached token
        mock_st.session_state.zoho_access_token = "cached-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600  # 1 hour from now
        )

        token = zoho_client.get_access_token()

        assert token == "cached-token"
        mock_requests.post.assert_not_called()

    def test_get_access_token_refreshes_when_expired(self, mock_st, mock_requests):
        """get_access_token refreshes token when expired."""
        # Set up expired token
        mock_st.session_state.zoho_access_token = "old-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() - 100  # Expired
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new-token",
            "expires_in": 3600,
        }
        mock_requests.post.return_value = mock_response

        token = zoho_client.get_access_token()

        assert token == "new-token"
        mock_requests.post.assert_called_once()

    def test_get_access_token_refreshes_within_buffer(self, mock_st, mock_requests):
        """get_access_token refreshes when within expiry buffer."""
        # Set up token expiring in 2 minutes (within 5-minute buffer)
        mock_st.session_state.zoho_access_token = "expiring-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 120  # 2 minutes
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "refreshed-token",
            "expires_in": 3600,
        }
        mock_requests.post.return_value = mock_response

        token = zoho_client.get_access_token()

        assert token == "refreshed-token"


class TestMakeRequest:
    """Tests for the _make_request function."""

    def test_make_request_success(self, mock_st, mock_requests):
        """Successful API request returns response."""
        # Set up valid token
        mock_st.session_state.zoho_access_token = "valid-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.request.return_value = mock_response

        result = zoho_client._make_request("GET", "https://api.zoho.com/crm/v2/Leads")

        assert result == mock_response
        assert mock_st.session_state.zoho_error is None

    def test_make_request_uses_30_second_timeout(self, mock_st, mock_requests):
        """API requests use 30-second timeout (NFR5)."""
        mock_st.session_state.zoho_access_token = "valid-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.request.return_value = mock_response

        zoho_client._make_request("GET", "https://api.zoho.com/test")

        # Check that timeout=30 was passed
        call_kwargs = mock_requests.request.call_args[1]
        assert call_kwargs.get("timeout") == 30

    def test_make_request_auto_refresh_on_401(self, mock_st, mock_requests):
        """401 response triggers token refresh and retry."""
        mock_st.session_state.zoho_access_token = "expired-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600
        )

        # First call returns 401, second returns 200
        mock_401 = Mock()
        mock_401.status_code = 401

        mock_200 = Mock()
        mock_200.status_code = 200

        # Token refresh response
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            "access_token": "new-token",
            "expires_in": 3600,
        }

        mock_requests.request.side_effect = [mock_401, mock_200]
        mock_requests.post.return_value = mock_token_response

        result = zoho_client._make_request("GET", "https://api.zoho.com/test")

        assert result == mock_200
        assert mock_requests.request.call_count == 2

    def test_make_request_rate_limit_429_retries(self, mock_st, mock_requests):
        """429 response triggers retry with backoff."""
        mock_st.session_state.zoho_access_token = "valid-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600
        )

        mock_429 = Mock()
        mock_429.status_code = 429
        mock_429.headers = {"Retry-After": "1"}

        mock_200 = Mock()
        mock_200.status_code = 200

        # First call returns 429, second succeeds
        mock_requests.request.side_effect = [mock_429, mock_200]

        with patch.object(zoho_client, 'time') as mock_time:
            result = zoho_client._make_request("GET", "https://api.zoho.com/test")

            # Should have slept for retry_after seconds
            mock_time.sleep.assert_called_once_with(1)
            # Should have retried and succeeded
            assert result == mock_200
            assert mock_requests.request.call_count == 2

    def test_make_request_rate_limit_max_retries_exceeded(self, mock_st, mock_requests):
        """429 after max retries returns error."""
        mock_st.session_state.zoho_access_token = "valid-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600
        )

        mock_429 = Mock()
        mock_429.status_code = 429
        mock_429.headers = {"Retry-After": "1"}

        # Always return 429
        mock_requests.request.return_value = mock_429

        with patch.object(zoho_client, 'time'):
            result = zoho_client._make_request("GET", "https://api.zoho.com/test")

            assert result is None
            assert mock_st.session_state.zoho_error is not None
            assert "Rate limit exceeded after retries" in mock_st.session_state.zoho_error
            # Should have tried 3 times (initial + 2 retries)
            assert mock_requests.request.call_count == 3

    def test_make_request_timeout_error(self, mock_st, mock_requests):
        """Timeout during request returns None with error."""
        mock_st.session_state.zoho_access_token = "valid-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600
        )

        import requests as real_requests
        mock_requests.request.side_effect = real_requests.exceptions.Timeout()
        mock_requests.exceptions = real_requests.exceptions

        result = zoho_client._make_request("GET", "https://api.zoho.com/test")

        assert result is None
        assert mock_st.session_state.zoho_error is not None
        assert "timed out" in mock_st.session_state.zoho_error


class TestErrorHandling:
    """Tests for error handling functions."""

    def test_credentials_never_in_error_messages(self, mock_st, mock_requests):
        """Verify credentials are never exposed in error messages (NFR9)."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_requests.post.return_value = mock_response

        zoho_client.refresh_access_token()

        error = mock_st.session_state.zoho_error
        assert "test-client-id" not in error
        assert "test-client-secret" not in error
        assert "test-refresh-token" not in error

    def test_get_last_error(self, mock_st, mock_requests):
        """get_last_error returns stored error message."""
        mock_st.session_state.zoho_error = "Test error message"

        error = zoho_client.get_last_error()

        assert error == "Test error message"

    def test_clear_error(self, mock_st, mock_requests):
        """clear_error removes stored error message."""
        mock_st.session_state.zoho_error = "Test error"

        zoho_client.clear_error()

        assert mock_st.session_state.zoho_error is None


class TestTestConnection:
    """Tests for the test_connection function."""

    def test_connection_success(self, mock_st, mock_requests):
        """test_connection returns True on successful auth."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test-token",
            "expires_in": 3600,
        }
        mock_requests.post.return_value = mock_response

        success, message = zoho_client.test_connection()

        assert success is True
        assert message == "Connection successful"

    def test_connection_failure(self, mock_st, mock_requests):
        """test_connection returns False with error on failure (AC#4 message)."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_requests.post.return_value = mock_response

        success, message = zoho_client.test_connection()

        assert success is False
        assert "Session expired" in message

    def test_connection_clears_cached_token(self, mock_st, mock_requests):
        """test_connection clears cached token to force fresh auth."""
        mock_st.session_state.zoho_access_token = "old-cached-token"
        mock_st.session_state.zoho_token_expiry = 12345

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "fresh-token",
            "expires_in": 3600,
        }
        mock_requests.post.return_value = mock_response

        zoho_client.test_connection()

        # Should have made a fresh token request
        mock_requests.post.assert_called_once()


class TestParseRetryAfter:
    """Tests for the _parse_retry_after helper function."""

    def test_parse_numeric_string(self):
        """Parses numeric string correctly."""
        assert zoho_client._parse_retry_after("120") == 120

    def test_parse_none_returns_default(self):
        """None returns default value."""
        assert zoho_client._parse_retry_after(None) == zoho_client.DEFAULT_RETRY_AFTER

    def test_parse_invalid_string_returns_default(self):
        """Invalid string returns default value (M3 fix)."""
        assert zoho_client._parse_retry_after("invalid") == zoho_client.DEFAULT_RETRY_AFTER

    def test_parse_date_string_returns_default(self):
        """HTTP date string returns default value."""
        assert zoho_client._parse_retry_after("Wed, 21 Oct 2026 07:28:00 GMT") == zoho_client.DEFAULT_RETRY_AFTER


class TestGetApiDomain:
    """Tests for the get_api_domain function (M2 fix)."""

    def test_returns_configured_domain(self, mock_st):
        """Returns domain from secrets when configured."""
        result = zoho_client.get_api_domain()
        assert result == "https://www.zohoapis.com"

    def test_returns_default_when_not_configured(self, mock_st):
        """Returns default domain when secrets not configured."""
        mock_st.secrets = {}  # No zoho section

        result = zoho_client.get_api_domain()

        assert result == "https://www.zohoapis.com"


class TestConstants:
    """Tests for module constants."""

    def test_request_timeout_is_30_seconds(self):
        """Verify REQUEST_TIMEOUT constant is 30 (NFR5)."""
        assert zoho_client.REQUEST_TIMEOUT == 30

    def test_oauth_token_url(self):
        """Verify OAuth token URL is correct."""
        assert zoho_client.OAUTH_TOKEN_URL == "https://accounts.zoho.com/oauth/v2/token"

    def test_max_rate_limit_retries(self):
        """Verify MAX_RATE_LIMIT_RETRIES constant."""
        assert zoho_client.MAX_RATE_LIMIT_RETRIES == 2

    def test_default_retry_after(self):
        """Verify DEFAULT_RETRY_AFTER constant."""
        assert zoho_client.DEFAULT_RETRY_AFTER == 60


class TestParseZohoDate:
    """Tests for parse_zoho_date function."""

    def test_parse_iso_date_with_timezone(self):
        """Parse ISO 8601 date with timezone to UTC datetime."""
        result = zoho_client.parse_zoho_date("2026-01-07T10:30:00-05:00")

        assert result is not None
        assert result.tzinfo == timezone.utc
        # -05:00 offset means 10:30 local = 15:30 UTC
        assert result.hour == 15
        assert result.minute == 30

    def test_parse_iso_date_utc(self):
        """Parse ISO 8601 date already in UTC."""
        result = zoho_client.parse_zoho_date("2026-01-07T10:30:00+00:00")

        assert result is not None
        assert result.tzinfo == timezone.utc
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_returns_none_for_empty_string(self):
        """Empty string returns None."""
        assert zoho_client.parse_zoho_date("") is None

    def test_parse_returns_none_for_none(self):
        """None input returns None."""
        assert zoho_client.parse_zoho_date(None) is None

    def test_parse_returns_none_for_invalid_date(self):
        """Invalid date string returns None."""
        assert zoho_client.parse_zoho_date("not-a-date") is None
        assert zoho_client.parse_zoho_date("12345") is None

    def test_parse_handles_date_only(self):
        """Parse date without time component."""
        result = zoho_client.parse_zoho_date("2026-01-07")

        assert result is not None
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 7

    def test_parse_naive_datetime_assumes_utc(self):
        """Naive datetime (no timezone) is assumed to be UTC (L3 fix)."""
        result = zoho_client.parse_zoho_date("2026-01-07T10:30:00")

        assert result is not None
        assert result.tzinfo == timezone.utc
        # Should be 10:30 UTC (not converted from local time)
        assert result.hour == 10
        assert result.minute == 30


class TestMapAndParseLead:
    """Tests for _map_and_parse_lead helper function (L2 fix)."""

    def test_maps_fields_and_parses_date(self):
        """_map_and_parse_lead maps fields and parses appointment_date."""
        zoho_record = {
            "id": "123",
            "Full_Name": "Test Lead",
            "Appointment_Date": "2026-01-07T10:30:00-05:00",
            "Stage": "Green",
        }

        result = zoho_client._map_and_parse_lead(zoho_record)

        assert result["id"] == "123"
        assert result["name"] == "Test Lead"
        assert result["current_stage"] == "Green"
        assert isinstance(result["appointment_date"], datetime)
        assert result["appointment_date"].tzinfo == timezone.utc

    def test_handles_missing_appointment_date(self):
        """_map_and_parse_lead handles missing appointment_date."""
        zoho_record = {"id": "123", "Full_Name": "Test Lead"}

        result = zoho_client._map_and_parse_lead(zoho_record)

        assert result["id"] == "123"
        assert result["appointment_date"] is None


class TestGetLeadsWithAppointments:
    """Tests for get_leads_with_appointments function (AC #1, #3, #4)."""

    def test_successful_fetch_returns_list_of_leads(self, mock_st, mock_requests):
        """Successful API call returns list of lead dicts (AC #1)."""
        # Set up valid token
        mock_st.session_state.zoho_access_token = "valid-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "1234567890",
                    "Full_Name": "John Smith",
                    "Appointment_Date": "2026-01-07T10:30:00-05:00",
                    "Stage": "Appt Set",
                    "Locator_Name": "Marcus Johnson",
                    "Locator_Phone": "(555) 123-4567",
                    "Locator_Email": "marcus@example.com",
                }
            ],
            "info": {"per_page": 200, "count": 1, "page": 1, "more_records": False},
        }
        mock_requests.request.return_value = mock_response

        leads = zoho_client.get_leads_with_appointments()

        assert isinstance(leads, list)
        assert len(leads) == 1
        lead = leads[0]
        assert lead["id"] == "1234567890"
        assert lead["name"] == "John Smith"
        assert lead["current_stage"] == "Appt Set"
        assert lead["locator_name"] == "Marcus Johnson"
        assert lead["locator_phone"] == "(555) 123-4567"
        assert lead["locator_email"] == "marcus@example.com"

    def test_appointment_date_is_parsed_to_datetime(self, mock_st, mock_requests):
        """Appointment date is parsed to Python datetime in UTC (AC #1)."""
        mock_st.session_state.zoho_access_token = "valid-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "123",
                    "Appointment_Date": "2026-01-07T10:30:00-05:00",
                }
            ]
        }
        mock_requests.request.return_value = mock_response

        leads = zoho_client.get_leads_with_appointments()

        assert len(leads) == 1
        apt_date = leads[0]["appointment_date"]
        assert isinstance(apt_date, datetime)
        assert apt_date.tzinfo == timezone.utc

    def test_returns_empty_list_on_api_error(self, mock_st, mock_requests):
        """API error returns empty list, not None (AC #3)."""
        mock_st.session_state.zoho_access_token = "valid-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600
        )

        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests.request.return_value = mock_response

        leads = zoho_client.get_leads_with_appointments()

        assert leads == []
        assert isinstance(leads, list)

    def test_returns_empty_list_when_no_token(self, mock_st, mock_requests):
        """Returns empty list when authentication fails (AC #3)."""
        mock_st.session_state.zoho_access_token = None
        mock_st.session_state.zoho_token_expiry = None

        # Token refresh fails
        mock_response = Mock()
        mock_response.status_code = 401
        mock_requests.post.return_value = mock_response

        leads = zoho_client.get_leads_with_appointments()

        assert leads == []

    def test_handles_missing_fields_as_none(self, mock_st, mock_requests):
        """Missing fields are returned as None (AC #4)."""
        mock_st.session_state.zoho_access_token = "valid-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "123",
                    "Full_Name": "John Smith",
                    # Missing: Appointment_Date, Stage, Locator fields
                }
            ]
        }
        mock_requests.request.return_value = mock_response

        leads = zoho_client.get_leads_with_appointments()

        assert len(leads) == 1
        lead = leads[0]
        assert lead["id"] == "123"
        assert lead["name"] == "John Smith"
        assert lead["appointment_date"] is None
        assert lead["current_stage"] is None
        assert lead["locator_name"] is None
        assert lead["locator_phone"] is None
        assert lead["locator_email"] is None

    def test_handles_empty_data_response(self, mock_st, mock_requests):
        """Empty data array returns empty list."""
        mock_st.session_state.zoho_access_token = "valid-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_requests.request.return_value = mock_response

        leads = zoho_client.get_leads_with_appointments()

        assert leads == []

    def test_handles_response_without_data_key(self, mock_st, mock_requests):
        """Response without 'data' key returns empty list."""
        mock_st.session_state.zoho_access_token = "valid-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # No 'data' key
        mock_requests.request.return_value = mock_response

        leads = zoho_client.get_leads_with_appointments()

        assert leads == []

    def test_captures_error_for_display(self, mock_st, mock_requests):
        """Error is captured in session state for display (AC #3)."""
        mock_st.session_state.zoho_access_token = "valid-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600
        )

        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests.request.return_value = mock_response

        zoho_client.get_leads_with_appointments()

        assert mock_st.session_state.zoho_error is not None

    def test_multiple_leads_returned(self, mock_st, mock_requests):
        """Multiple leads are correctly returned."""
        mock_st.session_state.zoho_access_token = "valid-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "1", "Full_Name": "Lead One"},
                {"id": "2", "Full_Name": "Lead Two"},
                {"id": "3", "Full_Name": "Lead Three"},
            ]
        }
        mock_requests.request.return_value = mock_response

        leads = zoho_client.get_leads_with_appointments()

        assert len(leads) == 3
        assert leads[0]["id"] == "1"
        assert leads[1]["id"] == "2"
        assert leads[2]["id"] == "3"

    def test_returns_empty_list_on_json_decode_error(self, mock_st, mock_requests):
        """JSONDecodeError returns empty list with error message (M3 fix)."""
        from json import JSONDecodeError

        mock_st.session_state.zoho_access_token = "valid-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("test", "doc", 0)
        mock_requests.request.return_value = mock_response

        leads = zoho_client.get_leads_with_appointments()

        assert leads == []
        assert mock_st.session_state.zoho_error == "Invalid response from Zoho CRM."

    def test_returns_empty_list_on_processing_error(self, mock_st, mock_requests):
        """Processing error returns empty list with error message (M4 fix)."""
        mock_st.session_state.zoho_access_token = "valid-token"
        mock_st.session_state.zoho_token_expiry = (
            datetime.now(timezone.utc).timestamp() + 3600
        )

        mock_response = Mock()
        mock_response.status_code = 200
        # Return data that will cause TypeError during processing
        mock_response.json.return_value = {"data": "not-a-list"}
        mock_requests.request.return_value = mock_response

        leads = zoho_client.get_leads_with_appointments()

        assert leads == []
        assert "AttributeError" in mock_st.session_state.zoho_error


class TestErrorTypeHandling:
    """Tests for error type classification (Story 1.6)."""

    @pytest.fixture
    def mock_st(self):
        """Fixture that provides a mock Streamlit module."""
        mock = MagicMock()
        mock.session_state = MockSessionState()
        mock.secrets = {
            "zoho": {
                "client_id": "test-client-id",
                "client_secret": "test-client-secret",
                "refresh_token": "test-refresh-token",
                "api_domain": "https://www.zohoapis.com",
            }
        }

        with patch.object(zoho_client, 'st', mock):
            yield mock

    @pytest.fixture
    def mock_requests(self):
        """Fixture that provides a mock requests module."""
        with patch.object(zoho_client, 'requests') as mock:
            yield mock

    def test_timeout_sets_correct_error_type(self, mock_st, mock_requests):
        """Timeout error sets ERROR_TYPE_TIMEOUT."""
        import requests as real_requests
        mock_requests.post.side_effect = real_requests.exceptions.Timeout()
        mock_requests.exceptions = real_requests.exceptions

        zoho_client.refresh_access_token()

        assert mock_st.session_state.zoho_error_type == zoho_client.ERROR_TYPE_TIMEOUT
        assert "timed out" in mock_st.session_state.zoho_error.lower()

    def test_connection_error_sets_correct_error_type(self, mock_st, mock_requests):
        """Connection error sets ERROR_TYPE_CONNECTION."""
        import requests as real_requests
        mock_requests.post.side_effect = real_requests.exceptions.ConnectionError()
        mock_requests.exceptions = real_requests.exceptions

        zoho_client.refresh_access_token()

        assert mock_st.session_state.zoho_error_type == zoho_client.ERROR_TYPE_CONNECTION
        assert "unable to connect" in mock_st.session_state.zoho_error.lower()

    def test_auth_error_sets_correct_error_type(self, mock_st, mock_requests):
        """Auth failure sets ERROR_TYPE_AUTH with AC#4 message."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_requests.post.return_value = mock_response

        zoho_client.refresh_access_token()

        assert mock_st.session_state.zoho_error_type == zoho_client.ERROR_TYPE_AUTH
        assert "session expired" in mock_st.session_state.zoho_error.lower()

    def test_get_error_type_returns_type(self, mock_st):
        """get_error_type returns the stored error type."""
        mock_st.session_state.zoho_error_type = zoho_client.ERROR_TYPE_TIMEOUT

        result = zoho_client.get_error_type()

        assert result == zoho_client.ERROR_TYPE_TIMEOUT

    def test_get_error_type_returns_none_when_no_error(self, mock_st):
        """get_error_type returns None when no error set."""
        result = zoho_client.get_error_type()

        assert result is None

    def test_clear_error_clears_both_message_and_type(self, mock_st):
        """clear_error clears both error message and type."""
        mock_st.session_state.zoho_error = "Some error"
        mock_st.session_state.zoho_error_type = zoho_client.ERROR_TYPE_CONNECTION

        zoho_client.clear_error()

        assert mock_st.session_state.zoho_error is None
        assert mock_st.session_state.zoho_error_type is None


class TestPartialErrorHandling:
    """Tests for partial error state handling (Story 1.6 AC#3)."""

    @pytest.fixture
    def mock_st(self):
        """Fixture that provides a mock Streamlit module."""
        mock = MagicMock()
        mock.session_state = MockSessionState()
        mock.secrets = {
            "zoho": {
                "client_id": "test-client-id",
                "client_secret": "test-client-secret",
                "refresh_token": "test-refresh-token",
                "api_domain": "https://www.zohoapis.com",
            }
        }

        with patch.object(zoho_client, 'st', mock):
            yield mock

    def test_set_partial_error(self, mock_st):
        """set_partial_error stores message in session state."""
        zoho_client.set_partial_error("Some data may be missing")

        assert mock_st.session_state.zoho_partial_error == "Some data may be missing"

    def test_get_partial_error(self, mock_st):
        """get_partial_error returns stored message."""
        mock_st.session_state.zoho_partial_error = "Warning message"

        result = zoho_client.get_partial_error()

        assert result == "Warning message"

    def test_get_partial_error_returns_none_when_not_set(self, mock_st):
        """get_partial_error returns None when no partial error."""
        result = zoho_client.get_partial_error()

        assert result is None

    def test_clear_partial_error(self, mock_st):
        """clear_partial_error removes partial error message."""
        mock_st.session_state.zoho_partial_error = "Warning message"

        zoho_client.clear_partial_error()

        assert mock_st.session_state.zoho_partial_error is None


class TestErrorTypeConstants:
    """Tests for error type constants (Story 1.6)."""

    def test_error_type_constants_exist(self):
        """Verify all error type constants are defined."""
        assert hasattr(zoho_client, 'ERROR_TYPE_CONNECTION')
        assert hasattr(zoho_client, 'ERROR_TYPE_TIMEOUT')
        assert hasattr(zoho_client, 'ERROR_TYPE_AUTH')
        assert hasattr(zoho_client, 'ERROR_TYPE_UNKNOWN')

    def test_error_type_constants_are_strings(self):
        """Error type constants should be strings."""
        assert isinstance(zoho_client.ERROR_TYPE_CONNECTION, str)
        assert isinstance(zoho_client.ERROR_TYPE_TIMEOUT, str)
        assert isinstance(zoho_client.ERROR_TYPE_AUTH, str)
        assert isinstance(zoho_client.ERROR_TYPE_UNKNOWN, str)

    def test_error_type_constants_are_unique(self):
        """Error type constants should be unique values."""
        types = [
            zoho_client.ERROR_TYPE_CONNECTION,
            zoho_client.ERROR_TYPE_TIMEOUT,
            zoho_client.ERROR_TYPE_AUTH,
            zoho_client.ERROR_TYPE_UNKNOWN,
        ]
        assert len(types) == len(set(types))


class TestGetStageHistory:
    """Tests for get_stage_history function (Story 4.2)."""

    def test_successful_fetch_returns_stage_transitions(self, mock_st):
        """Successful API call returns list of stage transitions."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "__timeline": [
                {
                    "done_time": "2026-01-05T10:00:00-05:00",
                    "field_history": [
                        {
                            "api_name": "Stage",
                            "_previous_value": "Appt Set",
                            "_value": "Green",
                        }
                    ]
                },
                {
                    "done_time": "2026-01-03T09:00:00-05:00",
                    "field_history": [
                        {
                            "api_name": "Stage",
                            "_previous_value": None,
                            "_value": "Appt Set",
                        }
                    ]
                }
            ]
        }

        with patch('requests.request', return_value=mock_response):
            with patch.object(zoho_client, 'get_access_token', return_value='test-token'):
                result = zoho_client.get_stage_history("12345")

        assert len(result) == 2
        # Should be sorted chronologically (oldest first)
        assert result[0]["to_stage"] == "Appt Set"
        assert result[1]["to_stage"] == "Green"

    def test_empty_timeline_returns_empty_list(self, mock_st):
        """Empty timeline response returns empty list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"__timeline": []}

        with patch('requests.request', return_value=mock_response):
            with patch.object(zoho_client, 'get_access_token', return_value='test-token'):
                result = zoho_client.get_stage_history("12345")

        assert result == []

    def test_no_stage_changes_returns_empty_list(self, mock_st):
        """Timeline with no Stage field changes returns empty list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "__timeline": [
                {
                    "done_time": "2026-01-05T10:00:00-05:00",
                    "field_history": [
                        {
                            "api_name": "Email",  # Not Stage
                            "_previous_value": "old@email.com",
                            "_value": "new@email.com",
                        }
                    ]
                }
            ]
        }

        with patch('requests.request', return_value=mock_response):
            with patch.object(zoho_client, 'get_access_token', return_value='test-token'):
                result = zoho_client.get_stage_history("12345")

        assert result == []

    def test_api_error_returns_none(self, mock_st):
        """API error returns None (distinguishes from empty history)."""
        with patch.object(zoho_client, '_make_request', return_value=None):
            result = zoho_client.get_stage_history("12345")

        assert result is None

    def test_json_decode_error_returns_none(self, mock_st):
        """JSON decode error returns None (distinguishes from empty history)."""
        from json import JSONDecodeError
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)

        with patch('requests.request', return_value=mock_response):
            with patch.object(zoho_client, 'get_access_token', return_value='test-token'):
                result = zoho_client.get_stage_history("12345")

        assert result is None

    def test_parses_timestamps_correctly(self, mock_st):
        """Timestamps are parsed to datetime objects."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "__timeline": [
                {
                    "done_time": "2026-01-05T10:30:00-05:00",
                    "field_history": [
                        {
                            "api_name": "Stage",
                            "_previous_value": "Appt Set",
                            "_value": "Green",
                        }
                    ]
                }
            ]
        }

        with patch('requests.request', return_value=mock_response):
            with patch.object(zoho_client, 'get_access_token', return_value='test-token'):
                result = zoho_client.get_stage_history("12345")

        assert len(result) == 1
        assert result[0]["changed_at"] is not None
        assert isinstance(result[0]["changed_at"], datetime)
