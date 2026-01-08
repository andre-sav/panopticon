"""
Unit tests for data_processing module.
"""
import pytest
from datetime import datetime, timezone, timedelta

from src.data_processing import (
    calculate_days_since,
    get_lead_status,
    format_date,
    safe_display,
    format_leads_for_display,
    format_last_updated,
    format_phone_link,
    format_email_link,
    STALE_THRESHOLD_DAYS,
    AT_RISK_THRESHOLD_DAYS,
)


class TestCalculateDaysSince:
    """Tests for calculate_days_since function."""

    def test_past_date_returns_positive_days(self):
        """Past appointments return positive day count."""
        past_date = datetime.now(timezone.utc) - timedelta(days=5)
        result = calculate_days_since(past_date)
        assert result == 5

    def test_today_returns_zero(self):
        """Today's date returns 0 days."""
        today = datetime.now(timezone.utc)
        result = calculate_days_since(today)
        assert result == 0

    def test_future_date_returns_negative_days(self):
        """Future appointments return negative day count."""
        future_date = datetime.now(timezone.utc) + timedelta(days=3)
        result = calculate_days_since(future_date)
        assert result == -3

    def test_handles_naive_datetime(self):
        """Works with timezone-naive datetime objects."""
        past_date = datetime.now() - timedelta(days=2)
        result = calculate_days_since(past_date)
        assert result == 2


class TestGetLeadStatus:
    """Tests for get_lead_status function."""

    def test_stale_at_threshold(self):
        """Exactly 7 days is stale."""
        assert get_lead_status(STALE_THRESHOLD_DAYS) == "stale"

    def test_stale_above_threshold(self):
        """More than 7 days is stale."""
        assert get_lead_status(10) == "stale"

    def test_at_risk_at_threshold(self):
        """Exactly 5 days is at_risk."""
        assert get_lead_status(AT_RISK_THRESHOLD_DAYS) == "at_risk"

    def test_at_risk_between_thresholds(self):
        """6 days (between 5 and 7) is at_risk."""
        assert get_lead_status(6) == "at_risk"

    def test_healthy_below_at_risk(self):
        """Less than 5 days is healthy."""
        assert get_lead_status(4) == "healthy"

    def test_healthy_at_zero(self):
        """0 days is healthy."""
        assert get_lead_status(0) == "healthy"

    def test_healthy_negative_days(self):
        """Negative days (future appointment) is healthy."""
        assert get_lead_status(-3) == "healthy"


class TestThresholdConstants:
    """Verify threshold constants match expected values."""

    def test_stale_threshold_is_seven(self):
        """Stale threshold should be 7 days."""
        assert STALE_THRESHOLD_DAYS == 7

    def test_at_risk_threshold_is_five(self):
        """At-risk threshold should be 5 days."""
        assert AT_RISK_THRESHOLD_DAYS == 5


class TestFormatDate:
    """Tests for format_date function (Story 1.4)."""

    def test_formats_datetime_correctly(self):
        """Formats datetime as 'Jan 7, 2026'."""
        dt = datetime(2026, 1, 7, 10, 30, 0, tzinfo=timezone.utc)
        result = format_date(dt)
        assert result == "Jan 7, 2026"

    def test_formats_different_months(self):
        """Handles different months correctly."""
        dt = datetime(2026, 12, 25, 0, 0, 0, tzinfo=timezone.utc)
        result = format_date(dt)
        assert result == "Dec 25, 2026"

    def test_returns_dash_for_none(self):
        """Returns '—' for None input."""
        result = format_date(None)
        assert result == "—"

    def test_formats_single_digit_day(self):
        """Single digit days have no leading zero."""
        dt = datetime(2026, 3, 5, 0, 0, 0, tzinfo=timezone.utc)
        result = format_date(dt)
        assert result == "Mar 5, 2026"

    def test_formats_double_digit_day(self):
        """Double digit days display correctly."""
        dt = datetime(2026, 6, 15, 0, 0, 0, tzinfo=timezone.utc)
        result = format_date(dt)
        assert result == "Jun 15, 2026"


class TestSafeDisplay:
    """Tests for safe_display function (Story 1.4)."""

    def test_returns_value_for_string(self):
        """Returns the value if it's a non-empty string."""
        assert safe_display("Hello") == "Hello"

    def test_returns_dash_for_none(self):
        """Returns '—' for None input."""
        assert safe_display(None) == "—"

    def test_returns_dash_for_empty_string(self):
        """Returns '—' for empty string input."""
        assert safe_display("") == "—"

    def test_preserves_whitespace(self):
        """Preserves strings with whitespace."""
        assert safe_display("  spaces  ") == "  spaces  "


class TestFormatLeadsForDisplay:
    """Tests for format_leads_for_display function (Story 1.4)."""

    def test_formats_complete_lead(self):
        """Formats a lead with all fields correctly."""
        leads = [
            {
                "id": "123",
                "name": "John Smith",
                "appointment_date": datetime(2026, 1, 7, 10, 30, tzinfo=timezone.utc),
                "current_stage": "Appt Set",
                "locator_name": "Marcus Johnson",
                "locator_phone": "(555) 123-4567",
                "locator_email": "marcus@example.com",
            }
        ]

        result = format_leads_for_display(leads)

        assert len(result) == 1
        assert result[0]["Lead Name"] == "John Smith"
        assert result[0]["Appointment Date"] == "Jan 7, 2026"
        assert result[0]["Stage"] == "Appt Set"
        assert result[0]["Locator"] == "Marcus Johnson"

    def test_handles_missing_fields_with_dash(self):
        """Missing fields display as '—'."""
        leads = [
            {
                "id": "123",
                "name": None,
                "appointment_date": None,
                "current_stage": None,
                "locator_name": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Lead Name"] == "—"
        assert result[0]["Appointment Date"] == "—"
        assert result[0]["Stage"] == "—"
        assert result[0]["Locator"] == "—"

    def test_handles_empty_list(self):
        """Returns empty list for empty input."""
        result = format_leads_for_display([])
        assert result == []

    def test_handles_multiple_leads(self):
        """Correctly formats multiple leads."""
        leads = [
            {"name": "Lead One", "appointment_date": None, "current_stage": "Green", "locator_name": "A"},
            {"name": "Lead Two", "appointment_date": None, "current_stage": "Blue", "locator_name": "B"},
            {"name": "Lead Three", "appointment_date": None, "current_stage": "Red", "locator_name": "C"},
        ]

        result = format_leads_for_display(leads)

        assert len(result) == 3
        assert result[0]["Lead Name"] == "Lead One"
        assert result[1]["Lead Name"] == "Lead Two"
        assert result[2]["Lead Name"] == "Lead Three"

    def test_only_includes_display_columns(self):
        """Result only includes display columns, not internal fields."""
        leads = [
            {
                "id": "123",
                "name": "Test",
                "appointment_date": None,
                "current_stage": "Test",
                "locator_name": "Test",
                "locator_phone": "(555) 555-5555",
                "locator_email": "test@test.com",
            }
        ]

        result = format_leads_for_display(leads)

        # Raw field names should not be present
        assert "id" not in result[0]
        assert "locator_phone" not in result[0]
        assert "locator_email" not in result[0]
        # Should have display columns including contact links (Story 1.7)
        assert set(result[0].keys()) == {"Lead Name", "Appointment Date", "Stage", "Locator", "Phone", "Email"}


class TestFormatLastUpdated:
    """Tests for format_last_updated function (Story 1.5)."""

    def test_returns_never_for_none(self):
        """Returns 'Never' for None input."""
        result = format_last_updated(None)
        assert result == "Never"

    def test_returns_just_now_for_under_60_seconds(self):
        """Returns 'Just now' for timestamps less than 60 seconds ago."""
        timestamp = datetime.now(timezone.utc) - timedelta(seconds=30)
        result = format_last_updated(timestamp)
        assert result == "Just now"

    def test_returns_just_now_for_zero_seconds(self):
        """Returns 'Just now' for current timestamp."""
        timestamp = datetime.now(timezone.utc)
        result = format_last_updated(timestamp)
        assert result == "Just now"

    def test_returns_1_minute_ago_singular(self):
        """Returns '1 minute ago' for exactly 1 minute."""
        timestamp = datetime.now(timezone.utc) - timedelta(minutes=1)
        result = format_last_updated(timestamp)
        assert result == "1 minute ago"

    def test_returns_minutes_ago_plural(self):
        """Returns 'X minutes ago' for multiple minutes."""
        timestamp = datetime.now(timezone.utc) - timedelta(minutes=5)
        result = format_last_updated(timestamp)
        assert result == "5 minutes ago"

    def test_returns_59_minutes_ago(self):
        """Returns '59 minutes ago' just under an hour."""
        timestamp = datetime.now(timezone.utc) - timedelta(minutes=59)
        result = format_last_updated(timestamp)
        assert result == "59 minutes ago"

    def test_returns_1_hour_ago_singular(self):
        """Returns '1 hour ago' for exactly 1 hour."""
        timestamp = datetime.now(timezone.utc) - timedelta(hours=1)
        result = format_last_updated(timestamp)
        assert result == "1 hour ago"

    def test_returns_hours_ago_plural(self):
        """Returns 'X hours ago' for multiple hours."""
        timestamp = datetime.now(timezone.utc) - timedelta(hours=5)
        result = format_last_updated(timestamp)
        assert result == "5 hours ago"

    def test_returns_23_hours_ago(self):
        """Returns '23 hours ago' just under a day."""
        timestamp = datetime.now(timezone.utc) - timedelta(hours=23)
        result = format_last_updated(timestamp)
        assert result == "23 hours ago"

    def test_returns_date_format_for_over_24_hours(self):
        """Returns date format for timestamps over 24 hours ago."""
        timestamp = datetime(2026, 1, 6, 14, 30, 0, tzinfo=timezone.utc)
        result = format_last_updated(timestamp)
        # Verify full format: "Jan 6 at 02:30 PM"
        assert result == "Jan 6 at 02:30 PM"

    def test_handles_future_timestamp(self):
        """Returns 'Just now' for future timestamps (edge case)."""
        future_timestamp = datetime.now(timezone.utc) + timedelta(minutes=5)
        result = format_last_updated(future_timestamp)
        # Future timestamps fall into "Just now" bucket (negative seconds < 60)
        assert result == "Just now"


class TestFormatPhoneLink:
    """Tests for format_phone_link function (Story 1.7)."""

    def test_formats_phone_number_as_tel_link(self):
        """Formats phone number as tel: URL."""
        result = format_phone_link("(555) 123-4567")
        assert result == "tel:(555) 123-4567"

    def test_returns_none_for_none_phone(self):
        """Returns None for None input."""
        result = format_phone_link(None)
        assert result is None

    def test_returns_none_for_empty_phone(self):
        """Returns None for empty string."""
        result = format_phone_link("")
        assert result is None

    def test_preserves_phone_format(self):
        """Preserves original phone format in link."""
        result = format_phone_link("555-123-4567")
        assert result == "tel:555-123-4567"


class TestFormatEmailLink:
    """Tests for format_email_link function (Story 1.7)."""

    def test_formats_email_as_mailto_link(self):
        """Formats email as mailto: URL."""
        result = format_email_link("marcus@example.com")
        assert result == "mailto:marcus@example.com"

    def test_returns_none_for_none_email(self):
        """Returns None for None input."""
        result = format_email_link(None)
        assert result is None

    def test_returns_none_for_empty_email(self):
        """Returns None for empty string."""
        result = format_email_link("")
        assert result is None

    def test_preserves_email_format(self):
        """Preserves original email format in link."""
        result = format_email_link("Test.User@Company.COM")
        assert result == "mailto:Test.User@Company.COM"


class TestFormatLeadsForDisplayContacts:
    """Tests for contact link columns in format_leads_for_display (Story 1.7)."""

    def test_includes_phone_link_when_present(self):
        """Phone column contains tel: link when phone exists."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime(2026, 1, 7, tzinfo=timezone.utc),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": "(555) 123-4567",
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Phone"] == "tel:(555) 123-4567"

    def test_phone_is_none_when_missing(self):
        """Phone column is None when phone doesn't exist (AC#4)."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime(2026, 1, 7, tzinfo=timezone.utc),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": "m@x.com",
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Phone"] is None

    def test_includes_email_link_when_present(self):
        """Email column contains mailto: link when email exists."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime(2026, 1, 7, tzinfo=timezone.utc),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": "marcus@example.com",
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Email"] == "mailto:marcus@example.com"

    def test_email_is_none_when_missing(self):
        """Email column is None when email doesn't exist."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime(2026, 1, 7, tzinfo=timezone.utc),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": "(555) 123-4567",
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Email"] is None

    def test_both_contact_links_present(self):
        """Both phone and email links present when both exist."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime(2026, 1, 7, tzinfo=timezone.utc),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": "(555) 123-4567",
                "locator_email": "marcus@example.com",
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Phone"] == "tel:(555) 123-4567"
        assert result[0]["Email"] == "mailto:marcus@example.com"
