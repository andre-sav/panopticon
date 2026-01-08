"""
Unit tests for data_processing module.
"""
import pytest
from datetime import datetime, timezone, timedelta

from src.data_processing import (
    calculate_days_since,
    get_lead_status,
    format_status_display,
    format_date,
    safe_display,
    format_leads_for_display,
    format_last_updated,
    format_phone_link,
    format_email_link,
    sort_by_urgency,
    count_leads_by_status,
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
        # Should have display columns including Days, Status (Story 2.1, 2.2) and contact links (Story 1.7)
        assert set(result[0].keys()) == {"Lead Name", "Appointment Date", "Days", "Status", "Stage", "Locator", "Phone", "Email"}


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


class TestFormatLeadsForDisplayDays:
    """Tests for Days column in format_leads_for_display (Story 2.1)."""

    def test_days_positive_for_past_appointment(self):
        """Days column shows positive value for past appointment (AC#1)."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime.now(timezone.utc) - timedelta(days=5),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Days"] == 5

    def test_days_seven_for_week_old_appointment(self):
        """Days column shows 7 for appointment exactly 7 days ago (AC#2)."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime.now(timezone.utc) - timedelta(days=7),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Days"] == 7

    def test_days_zero_for_today_appointment(self):
        """Days column shows 0 for today's appointment (AC#2)."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime.now(timezone.utc),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Days"] == 0

    def test_days_negative_for_future_appointment(self):
        """Days column shows negative value for future appointment (AC#3)."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime.now(timezone.utc) + timedelta(days=2),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Days"] == -2

    def test_days_column_exists_in_output(self):
        """Days column is present in formatted output (AC#1)."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime.now(timezone.utc) - timedelta(days=3),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert "Days" in result[0]

    def test_days_none_for_missing_appointment_date(self):
        """Days column is None when appointment_date is missing."""
        leads = [
            {
                "name": "John",
                "appointment_date": None,
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Days"] is None


class TestFormatStatusDisplay:
    """Tests for format_status_display function (Story 2.4)."""

    def test_stale_has_red_emoji(self):
        """Stale status shows red circle emoji."""
        result = format_status_display("stale")
        assert result == "🔴 stale"

    def test_at_risk_has_yellow_emoji(self):
        """At-risk status shows yellow circle emoji."""
        result = format_status_display("at_risk")
        assert result == "🟡 at_risk"

    def test_healthy_has_green_emoji(self):
        """Healthy status shows green circle emoji."""
        result = format_status_display("healthy")
        assert result == "🟢 healthy"

    def test_none_returns_none(self):
        """None input returns None."""
        result = format_status_display(None)
        assert result is None

    def test_unknown_status_returns_plain_text_and_logs_warning(self, caplog):
        """Unknown status returns plain text and logs warning."""
        import logging
        with caplog.at_level(logging.WARNING):
            result = format_status_display("unknown_status")
        assert result == "unknown_status"
        assert "Unknown status value: unknown_status" in caplog.text


class TestFormatLeadsForDisplayStatus:
    """Tests for Status column in format_leads_for_display (Story 2.2, 2.4)."""

    def test_status_stale_for_seven_plus_days(self):
        """Status column shows '🔴 stale' for 7+ days (AC#1)."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime.now(timezone.utc) - timedelta(days=7),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Status"] == "🔴 stale"

    def test_status_stale_for_ten_days(self):
        """Status column shows '🔴 stale' for 10 days."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime.now(timezone.utc) - timedelta(days=10),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Status"] == "🔴 stale"

    def test_status_not_stale_for_six_days(self):
        """Status column is NOT 'stale' for 6 days (AC#2)."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime.now(timezone.utc) - timedelta(days=6),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Status"] == "🟡 at_risk"  # 6 days is at_risk, not stale

    def test_status_at_risk_for_five_days(self):
        """Status column shows '🟡 at_risk' for 5 days."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime.now(timezone.utc) - timedelta(days=5),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Status"] == "🟡 at_risk"

    def test_status_healthy_for_four_days(self):
        """Status column shows '🟢 healthy' for < 5 days."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime.now(timezone.utc) - timedelta(days=4),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Status"] == "🟢 healthy"

    def test_status_healthy_for_zero_days(self):
        """Status column shows '🟢 healthy' for today's appointment (0 days)."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime.now(timezone.utc),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Status"] == "🟢 healthy"

    def test_status_healthy_for_future_appointment(self):
        """Status column shows '🟢 healthy' for future appointment (negative days)."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime.now(timezone.utc) + timedelta(days=3),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Status"] == "🟢 healthy"

    def test_status_none_for_missing_appointment_date(self):
        """Status column is None when appointment_date is missing."""
        leads = [
            {
                "name": "John",
                "appointment_date": None,
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Status"] is None


class TestSortByUrgency:
    """Tests for sort_by_urgency function (Story 2.5)."""

    def test_stale_sorted_before_at_risk(self):
        """Stale leads appear before at-risk leads."""
        leads = [
            {"Status": "🟡 at_risk", "Days": 5, "Lead Name": "At Risk Lead"},
            {"Status": "🔴 stale", "Days": 10, "Lead Name": "Stale Lead"},
        ]

        result = sort_by_urgency(leads)

        assert result[0]["Lead Name"] == "Stale Lead"
        assert result[1]["Lead Name"] == "At Risk Lead"

    def test_at_risk_sorted_before_healthy(self):
        """At-risk leads appear before healthy leads."""
        leads = [
            {"Status": "🟢 healthy", "Days": 2, "Lead Name": "Healthy Lead"},
            {"Status": "🟡 at_risk", "Days": 5, "Lead Name": "At Risk Lead"},
        ]

        result = sort_by_urgency(leads)

        assert result[0]["Lead Name"] == "At Risk Lead"
        assert result[1]["Lead Name"] == "Healthy Lead"

    def test_stale_sorted_before_healthy(self):
        """Stale leads appear before healthy leads."""
        leads = [
            {"Status": "🟢 healthy", "Days": 2, "Lead Name": "Healthy Lead"},
            {"Status": "🔴 stale", "Days": 10, "Lead Name": "Stale Lead"},
        ]

        result = sort_by_urgency(leads)

        assert result[0]["Lead Name"] == "Stale Lead"
        assert result[1]["Lead Name"] == "Healthy Lead"

    def test_within_stale_sorted_by_days_descending(self):
        """Within stale group, older leads (more days) come first."""
        leads = [
            {"Status": "🔴 stale", "Days": 7, "Lead Name": "7 Days Stale"},
            {"Status": "🔴 stale", "Days": 14, "Lead Name": "14 Days Stale"},
            {"Status": "🔴 stale", "Days": 10, "Lead Name": "10 Days Stale"},
        ]

        result = sort_by_urgency(leads)

        assert result[0]["Lead Name"] == "14 Days Stale"
        assert result[1]["Lead Name"] == "10 Days Stale"
        assert result[2]["Lead Name"] == "7 Days Stale"

    def test_within_at_risk_sorted_by_days_descending(self):
        """Within at-risk group, older leads (more days) come first."""
        leads = [
            {"Status": "🟡 at_risk", "Days": 5, "Lead Name": "5 Days"},
            {"Status": "🟡 at_risk", "Days": 6, "Lead Name": "6 Days"},
        ]

        result = sort_by_urgency(leads)

        assert result[0]["Lead Name"] == "6 Days"
        assert result[1]["Lead Name"] == "5 Days"

    def test_full_urgency_sort_order(self):
        """Full sort: stale by days desc, then at_risk by days desc, then healthy."""
        leads = [
            {"Status": "🟢 healthy", "Days": 3, "Lead Name": "Healthy 3"},
            {"Status": "🟡 at_risk", "Days": 5, "Lead Name": "At Risk 5"},
            {"Status": "🔴 stale", "Days": 7, "Lead Name": "Stale 7"},
            {"Status": "🟢 healthy", "Days": 1, "Lead Name": "Healthy 1"},
            {"Status": "🔴 stale", "Days": 10, "Lead Name": "Stale 10"},
            {"Status": "🟡 at_risk", "Days": 6, "Lead Name": "At Risk 6"},
        ]

        result = sort_by_urgency(leads)

        # Stale first, by days desc
        assert result[0]["Lead Name"] == "Stale 10"
        assert result[1]["Lead Name"] == "Stale 7"
        # At risk second, by days desc
        assert result[2]["Lead Name"] == "At Risk 6"
        assert result[3]["Lead Name"] == "At Risk 5"
        # Healthy last, by days desc
        assert result[4]["Lead Name"] == "Healthy 3"
        assert result[5]["Lead Name"] == "Healthy 1"

    def test_none_days_sorted_to_end(self):
        """Leads with None days are sorted to the end."""
        leads = [
            {"Status": None, "Days": None, "Lead Name": "No Days"},
            {"Status": "🔴 stale", "Days": 10, "Lead Name": "Stale Lead"},
            {"Status": "🟢 healthy", "Days": 2, "Lead Name": "Healthy Lead"},
        ]

        result = sort_by_urgency(leads)

        assert result[0]["Lead Name"] == "Stale Lead"
        assert result[1]["Lead Name"] == "Healthy Lead"
        assert result[2]["Lead Name"] == "No Days"

    def test_empty_list_returns_empty(self):
        """Empty input returns empty list."""
        result = sort_by_urgency([])
        assert result == []

    def test_returns_new_list(self):
        """sort_by_urgency returns a new list, not modifying original."""
        leads = [
            {"Status": "🟢 healthy", "Days": 2, "Lead Name": "Healthy"},
            {"Status": "🔴 stale", "Days": 10, "Lead Name": "Stale"},
        ]
        original_order = [lead["Lead Name"] for lead in leads]

        result = sort_by_urgency(leads)

        # Original list unchanged
        assert [lead["Lead Name"] for lead in leads] == original_order
        # Result is different order
        assert result[0]["Lead Name"] == "Stale"


class TestCountLeadsByStatus:
    """Tests for count_leads_by_status function (Story 2.6)."""

    def test_count_with_mixed_statuses(self):
        """Returns correct counts for mixed statuses (AC#1, AC#2)."""
        leads = [
            {"Status": "🔴 stale", "Days": 10},
            {"Status": "🔴 stale", "Days": 8},
            {"Status": "🔴 stale", "Days": 7},
            {"Status": "🟡 at_risk", "Days": 6},
            {"Status": "🟡 at_risk", "Days": 5},
            {"Status": "🟢 healthy", "Days": 4},
            {"Status": "🟢 healthy", "Days": 2},
        ]

        result = count_leads_by_status(leads)

        assert result["stale"] == 3
        assert result["at_risk"] == 2
        assert result["healthy"] == 2

    def test_count_all_stale(self):
        """Returns correct counts when all leads are stale."""
        leads = [
            {"Status": "🔴 stale", "Days": 10},
            {"Status": "🔴 stale", "Days": 7},
        ]

        result = count_leads_by_status(leads)

        assert result["stale"] == 2
        assert result["at_risk"] == 0
        assert result["healthy"] == 0

    def test_count_all_healthy(self):
        """Returns correct counts when all leads are healthy."""
        leads = [
            {"Status": "🟢 healthy", "Days": 2},
            {"Status": "🟢 healthy", "Days": 1},
            {"Status": "🟢 healthy", "Days": 0},
        ]

        result = count_leads_by_status(leads)

        assert result["stale"] == 0
        assert result["at_risk"] == 0
        assert result["healthy"] == 3

    def test_count_empty_list_returns_zeros(self):
        """Returns all zeros for empty list (AC#3)."""
        result = count_leads_by_status([])

        assert result["stale"] == 0
        assert result["at_risk"] == 0
        assert result["healthy"] == 0

    def test_count_handles_none_status(self):
        """Leads with None status are counted as healthy."""
        leads = [
            {"Status": None, "Days": None},
            {"Status": "🔴 stale", "Days": 10},
        ]

        result = count_leads_by_status(leads)

        assert result["stale"] == 1
        assert result["at_risk"] == 0
        assert result["healthy"] == 1

    def test_count_returns_dict_with_all_keys(self):
        """Result always has stale, at_risk, and healthy keys."""
        result = count_leads_by_status([])

        assert "stale" in result
        assert "at_risk" in result
        assert "healthy" in result

    def test_count_handles_empty_string_status(self):
        """Leads with empty string status are counted as healthy."""
        leads = [
            {"Status": "", "Days": 3},
            {"Status": "🔴 stale", "Days": 10},
        ]

        result = count_leads_by_status(leads)

        assert result["stale"] == 1
        assert result["at_risk"] == 0
        assert result["healthy"] == 1

    def test_count_total_equals_input_length(self):
        """Sum of all counts equals total number of leads."""
        leads = [
            {"Status": "🔴 stale", "Days": 10},
            {"Status": "🟡 at_risk", "Days": 6},
            {"Status": "🟢 healthy", "Days": 2},
            {"Status": None, "Days": None},
            {"Status": "", "Days": 3},
        ]

        result = count_leads_by_status(leads)

        total = result["stale"] + result["at_risk"] + result["healthy"]
        assert total == len(leads)
