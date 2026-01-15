"""
Unit tests for data_processing module.
"""
import pytest
from datetime import datetime, timezone, timedelta

from src.data_processing import (
    calculate_days_since,
    get_lead_status,
    format_status_display,
    get_status_emoji,
    format_date,
    safe_display,
    format_leads_for_display,
    format_last_updated,
    format_time_in_stage,
    format_stage_timestamp,
    format_stage_history,
    format_phone_link,
    format_email_link,
    sort_by_urgency,
    sort_leads,
    count_leads_by_status,
    filter_by_stage,
    filter_by_locator,
    filter_by_date_range,
    apply_filters,
    get_unique_stages,
    get_unique_locators,
    STALE_THRESHOLD_DAYS,
    STALE_NO_ACTIVITY_DAYS,
    AT_RISK_THRESHOLD_DAYS,
    DEFAULT_SORT,
    SORT_OPTIONS,
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
    """Tests for get_lead_status function (deprecated - aligned with v2 14-day threshold)."""

    def test_stale_at_threshold(self):
        """Exactly 14 days is stale (aligned with v2 classification)."""
        assert get_lead_status(STALE_NO_ACTIVITY_DAYS) == "stale"

    def test_stale_above_threshold(self):
        """More than 14 days is stale."""
        assert get_lead_status(15) == "stale"

    def test_at_risk_at_threshold(self):
        """Exactly 5 days is at_risk."""
        assert get_lead_status(AT_RISK_THRESHOLD_DAYS) == "at_risk"

    def test_at_risk_between_thresholds(self):
        """10 days (between 5 and 14) is at_risk."""
        assert get_lead_status(10) == "at_risk"

    def test_healthy_below_at_risk(self):
        """Less than 5 days is healthy."""
        assert get_lead_status(4) == "healthy"

    def test_healthy_at_zero(self):
        """0 days is healthy."""
        assert get_lead_status(0) == "healthy"

    def test_healthy_negative_days(self):
        """Negative days (future appointment) is healthy."""
        assert get_lead_status(-3) == "healthy"

    # Tests for "Appt Not Acknowledged" stage-specific behavior
    def test_appt_not_acknowledged_stale_at_fourteen_plus_days(self):
        """Appt Not Acknowledged still becomes stale at 14+ days."""
        assert get_lead_status(14, stage="Appt Not Acknowledged") == "stale"
        assert get_lead_status(15, stage="Appt Not Acknowledged") == "stale"

    def test_appt_not_acknowledged_at_risk_at_five_six_days(self):
        """Appt Not Acknowledged is at_risk at 5-6 days (same as normal)."""
        assert get_lead_status(5, stage="Appt Not Acknowledged") == "at_risk"
        assert get_lead_status(6, stage="Appt Not Acknowledged") == "at_risk"

    def test_appt_not_acknowledged_at_risk_below_five_days(self):
        """Appt Not Acknowledged is at_risk even below 5 days (unlike normal leads)."""
        assert get_lead_status(4, stage="Appt Not Acknowledged") == "at_risk"
        assert get_lead_status(2, stage="Appt Not Acknowledged") == "at_risk"
        assert get_lead_status(0, stage="Appt Not Acknowledged") == "at_risk"

    def test_appt_not_acknowledged_at_risk_future_appointment(self):
        """Appt Not Acknowledged is at_risk even for future appointments."""
        assert get_lead_status(-1, stage="Appt Not Acknowledged") == "at_risk"


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

        # Raw field names should not be present (except id which is needed for stage history)
        assert "locator_phone" not in result[0]
        assert "locator_email" not in result[0]
        # Should have display columns including id (Story 4.2), Days, Status (Story 2.1, 2.2),
        # contact links (Story 1.7), zoho_link, classification_reason (v2), and misc_notes fields
        expected_keys = {
            "id", "Lead Name", "Appointment Date", "Days", "Status", "Stage",
            "Locator", "Phone", "Email", "zoho_link", "classification_reason",
            "misc_notes", "misc_notes_long"
        }
        assert set(result[0].keys()) == expected_keys


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
    """Tests for Status column in format_leads_for_display (Story 2.2, 2.4).

    Note: Legacy classification uses STALE_NO_ACTIVITY_DAYS (14 days) threshold,
    aligned with v2 classification.
    """

    def test_status_stale_for_fourteen_plus_days(self):
        """Status column shows '🔴 stale' for 14+ days."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime.now(timezone.utc) - timedelta(days=14),
                "current_stage": "Appt Set",
                "locator_name": "Marcus",
                "locator_phone": None,
                "locator_email": None,
            }
        ]

        result = format_leads_for_display(leads)

        assert result[0]["Status"] == "🔴 stale"

    def test_status_stale_for_fifteen_days(self):
        """Status column shows '🔴 stale' for 15 days."""
        leads = [
            {
                "name": "John",
                "appointment_date": datetime.now(timezone.utc) - timedelta(days=15),
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


class TestFilterByStage:
    """Tests for filter_by_stage function (Story 3.1)."""

    def test_filter_returns_only_matching_stage(self):
        """Filter by specific stage returns only leads with that stage (AC#2)."""
        leads = [
            {"Stage": "Appt Set", "Lead Name": "John"},
            {"Stage": "Green", "Lead Name": "Jane"},
            {"Stage": "Appt Set", "Lead Name": "Bob"},
        ]

        result = filter_by_stage(leads, "Appt Set")

        assert len(result) == 2
        assert all(lead["Stage"] == "Appt Set" for lead in result)

    def test_filter_all_stages_returns_all(self):
        """Filter with 'All Stages' returns all leads (AC#3)."""
        leads = [
            {"Stage": "Appt Set", "Lead Name": "John"},
            {"Stage": "Green", "Lead Name": "Jane"},
        ]

        result = filter_by_stage(leads, "All Stages")

        assert len(result) == 2

    def test_filter_empty_list_returns_empty(self):
        """Filter on empty list returns empty list."""
        result = filter_by_stage([], "Appt Set")
        assert result == []

    def test_filter_no_matches_returns_empty(self):
        """Filter with no matching stage returns empty list."""
        leads = [
            {"Stage": "Green", "Lead Name": "John"},
            {"Stage": "Delivered", "Lead Name": "Jane"},
        ]

        result = filter_by_stage(leads, "Appt Set")

        assert result == []

    def test_filter_handles_none_stage(self):
        """Filter handles leads with None stage."""
        leads = [
            {"Stage": None, "Lead Name": "John"},
            {"Stage": "Appt Set", "Lead Name": "Jane"},
        ]

        result = filter_by_stage(leads, "Appt Set")

        assert len(result) == 1
        assert result[0]["Lead Name"] == "Jane"


class TestFilterByLocator:
    """Tests for filter_by_locator function (Story 3.1)."""

    def test_filter_returns_only_matching_locator(self):
        """Filter by specific locator returns only matching leads (AC#5)."""
        leads = [
            {"Locator": "Marcus Johnson", "Lead Name": "John"},
            {"Locator": "Sarah Smith", "Lead Name": "Jane"},
            {"Locator": "Marcus Johnson", "Lead Name": "Bob"},
        ]

        result = filter_by_locator(leads, "Marcus Johnson")

        assert len(result) == 2
        assert all(lead["Locator"] == "Marcus Johnson" for lead in result)

    def test_filter_all_locators_returns_all(self):
        """Filter with 'All Locators' returns all leads (AC#6)."""
        leads = [
            {"Locator": "Marcus Johnson", "Lead Name": "John"},
            {"Locator": "Sarah Smith", "Lead Name": "Jane"},
        ]

        result = filter_by_locator(leads, "All Locators")

        assert len(result) == 2

    def test_filter_case_insensitive(self):
        """Filter is case-insensitive for matching."""
        leads = [
            {"Locator": "Marcus Johnson", "Lead Name": "John"},
            {"Locator": "Sarah Smith", "Lead Name": "Jane"},
        ]

        result = filter_by_locator(leads, "marcus johnson")

        assert len(result) == 1
        assert result[0]["Locator"] == "Marcus Johnson"

    def test_filter_handles_none_locator(self):
        """Filter handles leads with None locator."""
        leads = [
            {"Locator": None, "Lead Name": "John"},
            {"Locator": "Marcus Johnson", "Lead Name": "Jane"},
        ]

        result = filter_by_locator(leads, "Marcus Johnson")

        assert len(result) == 1


class TestFilterByDateRange:
    """Tests for filter_by_date_range function (Story 3.1).

    Note: Date range presets include Future appointments where noted.
    """

    def test_filter_all_dates_returns_all(self):
        """Filter with 'All Dates' returns all leads."""
        leads = [
            {"Appointment Date": "Jan 1, 2026", "Lead Name": "John", "Days": 5},
            {"Appointment Date": "Jan 15, 2026", "Lead Name": "Jane", "Days": 10},
        ]

        result = filter_by_date_range(leads, "All Dates")

        assert len(result) == 2

    def test_filter_future(self):
        """Filter 'Future' returns only leads with future appointments."""
        leads = [
            {"Days": -2, "Lead Name": "Future Lead"},
            {"Days": 0, "Lead Name": "Today Lead"},
            {"Days": 1, "Lead Name": "Yesterday Lead"},
        ]

        result = filter_by_date_range(leads, "Future")

        assert len(result) == 1
        assert result[0]["Lead Name"] == "Future Lead"

    def test_filter_last_7_days_plus_future_includes_day_6(self):
        """Filter 'Last 7 Days + Future' includes leads up to 6 days ago and future."""
        leads = [
            {"Days": -1, "Lead Name": "Future"},
            {"Days": 0, "Lead Name": "Today"},
            {"Days": 6, "Lead Name": "6 Days Ago"},
            {"Days": 7, "Lead Name": "7 Days Ago"},
        ]

        result = filter_by_date_range(leads, "Last 7 Days + Future")

        assert len(result) == 3
        names = [lead["Lead Name"] for lead in result]
        assert "Future" in names
        assert "Today" in names
        assert "6 Days Ago" in names
        assert "7 Days Ago" not in names

    def test_filter_last_7_days_plus_future_excludes_day_7(self):
        """Filter 'Last 7 Days + Future' excludes leads 7+ days ago."""
        leads = [
            {"Days": 3, "Lead Name": "3 Days Ago"},
            {"Days": 10, "Lead Name": "10 Days Ago"},
        ]

        result = filter_by_date_range(leads, "Last 7 Days + Future")

        assert len(result) == 1
        assert result[0]["Lead Name"] == "3 Days Ago"

    def test_filter_last_30_days_plus_future_includes_day_29(self):
        """Filter 'Last 30 Days + Future' includes leads up to 29 days ago."""
        leads = [
            {"Days": 5, "Lead Name": "5 Days"},
            {"Days": 29, "Lead Name": "29 Days"},
            {"Days": 30, "Lead Name": "30 Days"},
        ]

        result = filter_by_date_range(leads, "Last 30 Days + Future")

        assert len(result) == 2
        names = [lead["Lead Name"] for lead in result]
        assert "5 Days" in names
        assert "29 Days" in names
        assert "30 Days" not in names

    def test_filter_last_30_days_plus_future_excludes_day_30(self):
        """Filter 'Last 30 Days + Future' excludes leads 30+ days ago."""
        leads = [
            {"Days": 15, "Lead Name": "15 Days"},
            {"Days": 45, "Lead Name": "45 Days"},
        ]

        result = filter_by_date_range(leads, "Last 30 Days + Future")

        assert len(result) == 1
        assert result[0]["Lead Name"] == "15 Days"

    def test_filter_last_6_months_excludes_future(self):
        """'Last 6 Months' filter excludes future appointments (negative Days)."""
        leads = [
            {"Days": -2, "Lead Name": "Future"},
            {"Days": 0, "Lead Name": "Today"},
            {"Days": 3, "Lead Name": "Past"},
        ]

        result = filter_by_date_range(leads, "Last 6 Months")

        assert len(result) == 2
        names = [lead["Lead Name"] for lead in result]
        assert "Future" not in names

    def test_filter_handles_none_days(self):
        """Leads with None days are excluded from date range filters."""
        leads = [
            {"Days": None, "Lead Name": "No Date"},
            {"Days": 3, "Lead Name": "Has Date"},
        ]

        result = filter_by_date_range(leads, "Last 7 Days + Future")

        assert len(result) == 1
        assert result[0]["Lead Name"] == "Has Date"


class TestApplyFilters:
    """Tests for apply_filters function (Story 3.1)."""

    def test_apply_all_filters_combined(self):
        """Apply multiple filters uses AND logic (AC#10, AC#11)."""
        leads = [
            {"Stage": "Appt Set", "Locator": "Marcus", "Days": 3},
            {"Stage": "Appt Set", "Locator": "Sarah", "Days": 3},
            {"Stage": "Green", "Locator": "Marcus", "Days": 3},
            {"Stage": "Appt Set", "Locator": "Marcus", "Days": 10},  # Outside Last 7 Days + Future (>6)
        ]

        result = apply_filters(leads, "Appt Set", "Marcus", "Last 7 Days + Future")

        assert len(result) == 1
        assert result[0]["Stage"] == "Appt Set"
        assert result[0]["Locator"] == "Marcus"
        assert result[0]["Days"] == 3

    def test_apply_filters_all_defaults_returns_all(self):
        """Apply filters with all defaults returns all leads."""
        leads = [
            {"Stage": "Appt Set", "Locator": "Marcus", "Days": 3},
            {"Stage": "Green", "Locator": "Sarah", "Days": 10},
        ]

        result = apply_filters(leads, "All Stages", "All Locators", "All Dates")

        assert len(result) == 2

    def test_apply_filters_empty_result(self):
        """Apply filters that match nothing returns empty list (AC#12)."""
        leads = [
            {"Stage": "Green", "Locator": "Sarah", "Days": 3},
        ]

        result = apply_filters(leads, "Appt Set", "Marcus", "All Dates")

        assert result == []


class TestGetUniqueStages:
    """Tests for get_unique_stages helper function."""

    def test_returns_unique_stages(self):
        """Returns unique stage values from leads."""
        leads = [
            {"Stage": "Appt Set"},
            {"Stage": "Green"},
            {"Stage": "Appt Set"},
            {"Stage": "Delivered"},
        ]

        result = get_unique_stages(leads)

        assert set(result) == {"Appt Set", "Green", "Delivered"}

    def test_excludes_none_and_dash(self):
        """Excludes None and '—' from unique stages."""
        leads = [
            {"Stage": "Appt Set"},
            {"Stage": None},
            {"Stage": "—"},
        ]

        result = get_unique_stages(leads)

        assert result == ["Appt Set"]

    def test_returns_sorted_list(self):
        """Returns stages in sorted order."""
        leads = [
            {"Stage": "Zebra"},
            {"Stage": "Apple"},
            {"Stage": "Middle"},
        ]

        result = get_unique_stages(leads)

        assert result == ["Apple", "Middle", "Zebra"]


class TestGetUniqueLocators:
    """Tests for get_unique_locators helper function."""

    def test_returns_unique_locators(self):
        """Returns unique locator names from leads."""
        leads = [
            {"Locator": "Marcus Johnson"},
            {"Locator": "Sarah Smith"},
            {"Locator": "Marcus Johnson"},
        ]

        result = get_unique_locators(leads)

        assert set(result) == {"Marcus Johnson", "Sarah Smith"}

    def test_excludes_none_and_dash(self):
        """Excludes None and '—' from unique locators."""
        leads = [
            {"Locator": "Marcus Johnson"},
            {"Locator": None},
            {"Locator": "—"},
        ]

        result = get_unique_locators(leads)

        assert result == ["Marcus Johnson"]


class TestSortLeads:
    """Tests for sort_leads function (Story 3.2)."""

    def test_default_sort_uses_last_activity(self):
        """Default sort option sorts by last activity (most recent first)."""
        leads = [
            {"Status": "🟢 healthy", "Days": 2, "Lead Name": "Old Activity", "days_since_activity": 10},
            {"Status": "🔴 stale", "Days": 10, "Lead Name": "Recent Activity", "days_since_activity": 1},
        ]

        result = sort_leads(leads, DEFAULT_SORT)

        # Most recent activity (lowest days_since_activity) should come first
        assert result[0]["Lead Name"] == "Recent Activity"
        assert result[1]["Lead Name"] == "Old Activity"

    def test_days_most_first_descending(self):
        """Days (Most First) sorts by days descending."""
        leads = [
            {"Days": 3, "Lead Name": "3 Days"},
            {"Days": 10, "Lead Name": "10 Days"},
            {"Days": 1, "Lead Name": "1 Day"},
        ]

        result = sort_leads(leads, "Days (Most First)")

        assert result[0]["Lead Name"] == "10 Days"
        assert result[1]["Lead Name"] == "3 Days"
        assert result[2]["Lead Name"] == "1 Day"

    def test_days_least_first_ascending(self):
        """Days (Least First) sorts by days ascending."""
        leads = [
            {"Days": 3, "Lead Name": "3 Days"},
            {"Days": 10, "Lead Name": "10 Days"},
            {"Days": 1, "Lead Name": "1 Day"},
        ]

        result = sort_leads(leads, "Days (Least First)")

        assert result[0]["Lead Name"] == "1 Day"
        assert result[1]["Lead Name"] == "3 Days"
        assert result[2]["Lead Name"] == "10 Days"

    def test_days_sort_puts_none_at_end(self):
        """Days sort puts None values at end."""
        leads = [
            {"Days": None, "Lead Name": "No Days"},
            {"Days": 5, "Lead Name": "5 Days"},
            {"Days": 2, "Lead Name": "2 Days"},
        ]

        result = sort_leads(leads, "Days (Least First)")

        assert result[0]["Lead Name"] == "2 Days"
        assert result[1]["Lead Name"] == "5 Days"
        assert result[2]["Lead Name"] == "No Days"

    def test_appointment_date_newest_first(self):
        """Appointment Date (Newest) sorts by most recent (least days) first."""
        leads = [
            {"Days": 10, "Lead Name": "10 Days Ago"},
            {"Days": 1, "Lead Name": "1 Day Ago"},
            {"Days": 5, "Lead Name": "5 Days Ago"},
        ]

        result = sort_leads(leads, "Appointment Date (Newest)")

        assert result[0]["Lead Name"] == "1 Day Ago"
        assert result[1]["Lead Name"] == "5 Days Ago"
        assert result[2]["Lead Name"] == "10 Days Ago"

    def test_appointment_date_oldest_first(self):
        """Appointment Date (Oldest) sorts by oldest (most days) first."""
        leads = [
            {"Days": 10, "Lead Name": "10 Days Ago"},
            {"Days": 1, "Lead Name": "1 Day Ago"},
            {"Days": 5, "Lead Name": "5 Days Ago"},
        ]

        result = sort_leads(leads, "Appointment Date (Oldest)")

        assert result[0]["Lead Name"] == "10 Days Ago"
        assert result[1]["Lead Name"] == "5 Days Ago"
        assert result[2]["Lead Name"] == "1 Day Ago"

    def test_lead_name_alphabetical(self):
        """Lead Name (A-Z) sorts alphabetically."""
        leads = [
            {"Lead Name": "Charlie"},
            {"Lead Name": "Alice"},
            {"Lead Name": "Bob"},
        ]

        result = sort_leads(leads, "Lead Name (A-Z)")

        assert result[0]["Lead Name"] == "Alice"
        assert result[1]["Lead Name"] == "Bob"
        assert result[2]["Lead Name"] == "Charlie"

    def test_lead_name_case_insensitive(self):
        """Lead Name sort is case-insensitive."""
        leads = [
            {"Lead Name": "charlie"},
            {"Lead Name": "Alice"},
            {"Lead Name": "BOB"},
        ]

        result = sort_leads(leads, "Lead Name (A-Z)")

        assert result[0]["Lead Name"] == "Alice"
        assert result[1]["Lead Name"] == "BOB"
        assert result[2]["Lead Name"] == "charlie"

    def test_lead_name_dash_at_end(self):
        """Lead Name sort puts '—' values at end."""
        leads = [
            {"Lead Name": "—"},
            {"Lead Name": "Alice"},
            {"Lead Name": "Bob"},
        ]

        result = sort_leads(leads, "Lead Name (A-Z)")

        assert result[0]["Lead Name"] == "Alice"
        assert result[1]["Lead Name"] == "Bob"
        assert result[2]["Lead Name"] == "—"

    def test_stage_alphabetical(self):
        """Stage (A-Z) sorts alphabetically."""
        leads = [
            {"Stage": "Green"},
            {"Stage": "Appt Set"},
            {"Stage": "Delivered"},
        ]

        result = sort_leads(leads, "Stage (A-Z)")

        assert result[0]["Stage"] == "Appt Set"
        assert result[1]["Stage"] == "Delivered"
        assert result[2]["Stage"] == "Green"

    def test_stage_dash_at_end(self):
        """Stage sort puts '—' values at end."""
        leads = [
            {"Stage": "—"},
            {"Stage": "Appt Set"},
        ]

        result = sort_leads(leads, "Stage (A-Z)")

        assert result[0]["Stage"] == "Appt Set"
        assert result[1]["Stage"] == "—"

    def test_locator_alphabetical(self):
        """Locator (A-Z) sorts alphabetically."""
        leads = [
            {"Locator": "Sarah Smith"},
            {"Locator": "Marcus Johnson"},
            {"Locator": "Anna Lee"},
        ]

        result = sort_leads(leads, "Locator (A-Z)")

        assert result[0]["Locator"] == "Anna Lee"
        assert result[1]["Locator"] == "Marcus Johnson"
        assert result[2]["Locator"] == "Sarah Smith"

    def test_locator_dash_at_end(self):
        """Locator sort puts '—' values at end."""
        leads = [
            {"Locator": "—"},
            {"Locator": "Marcus Johnson"},
        ]

        result = sort_leads(leads, "Locator (A-Z)")

        assert result[0]["Locator"] == "Marcus Johnson"
        assert result[1]["Locator"] == "—"

    def test_unknown_sort_option_uses_last_activity(self):
        """Unknown sort option falls back to last activity sort."""
        leads = [
            {"Status": "🟢 healthy", "Days": 2, "Lead Name": "Old Activity", "days_since_activity": 10},
            {"Status": "🔴 stale", "Days": 10, "Lead Name": "Recent Activity", "days_since_activity": 1},
        ]

        result = sort_leads(leads, "Unknown Option")

        # Should fall back to last activity sort (most recent first)
        assert result[0]["Lead Name"] == "Recent Activity"

    def test_empty_list_returns_empty(self):
        """Sorting empty list returns empty list."""
        result = sort_leads([], "Days (Most First)")
        assert result == []

    def test_sort_options_constant_exists(self):
        """SORT_OPTIONS constant contains expected options."""
        assert DEFAULT_SORT in SORT_OPTIONS
        assert "Days (Most First)" in SORT_OPTIONS
        assert "Days (Least First)" in SORT_OPTIONS
        assert "Appointment Date (Newest)" in SORT_OPTIONS
        assert "Appointment Date (Oldest)" in SORT_OPTIONS
        assert "Lead Name (A-Z)" in SORT_OPTIONS
        assert "Stage (A-Z)" in SORT_OPTIONS
        assert "Locator (A-Z)" in SORT_OPTIONS

    def test_sort_with_filtered_data(self):
        """Sort works correctly on filtered data (AC#4 integration)."""
        # Simulate filtered data (subset of leads)
        filtered_leads = [
            {"Stage": "Appt Set", "Locator": "Marcus", "Days": 10, "Lead Name": "John"},
            {"Stage": "Appt Set", "Locator": "Marcus", "Days": 3, "Lead Name": "Alice"},
            {"Stage": "Appt Set", "Locator": "Marcus", "Days": 7, "Lead Name": "Bob"},
        ]

        # Apply sort to filtered data
        result = sort_leads(filtered_leads, "Lead Name (A-Z)")

        # Verify sort works on the filtered subset
        assert len(result) == 3
        assert result[0]["Lead Name"] == "Alice"
        assert result[1]["Lead Name"] == "Bob"
        assert result[2]["Lead Name"] == "John"

    def test_sort_preserves_data_integrity(self):
        """Sort returns new list without modifying original."""
        original = [
            {"Days": 5, "Lead Name": "First"},
            {"Days": 2, "Lead Name": "Second"},
        ]
        original_order = [lead["Lead Name"] for lead in original]

        result = sort_leads(original, "Days (Least First)")

        # Original unchanged
        assert [lead["Lead Name"] for lead in original] == original_order
        # Result is sorted differently
        assert result[0]["Lead Name"] == "Second"
        assert result[1]["Lead Name"] == "First"


class TestFormatTimeInStage:
    """Tests for format_time_in_stage function (Story 4.1)."""

    def test_none_returns_unknown(self):
        """None days returns 'Unknown'."""
        result = format_time_in_stage(None)
        assert result == "Unknown"

    def test_zero_days_returns_less_than_one_day(self):
        """Zero days returns 'Less than 1 day'."""
        result = format_time_in_stage(0)
        assert result == "Less than 1 day"

    def test_one_day_singular(self):
        """One day returns '1 day' (singular)."""
        result = format_time_in_stage(1)
        assert result == "1 day"

    def test_multiple_days_plural(self):
        """Multiple days returns 'X days' (plural)."""
        result = format_time_in_stage(3)
        assert result == "3 days"

    def test_large_number_of_days(self):
        """Large number of days formats correctly."""
        result = format_time_in_stage(100)
        assert result == "100 days"

    def test_negative_days_formats_as_future(self):
        """Negative days (future) formats as 'In X days'."""
        result = format_time_in_stage(-2)
        assert result == "In 2 days"

    def test_negative_one_day_singular(self):
        """Negative one day returns 'In 1 day' (singular)."""
        result = format_time_in_stage(-1)
        assert result == "In 1 day"


class TestGetStatusEmoji:
    """Tests for get_status_emoji function (Story 4.1)."""

    def test_stale_returns_red_circle(self):
        """Stale status returns red circle emoji."""
        assert get_status_emoji("stale") == "🔴"

    def test_at_risk_returns_yellow_circle(self):
        """At risk status returns yellow circle emoji."""
        assert get_status_emoji("at_risk") == "🟡"

    def test_healthy_returns_green_circle(self):
        """Healthy status returns green circle emoji."""
        assert get_status_emoji("healthy") == "🟢"

    def test_formatted_status_with_stale(self):
        """Formatted status containing 'stale' returns red circle."""
        assert get_status_emoji("🔴 stale") == "🔴"

    def test_formatted_status_with_at_risk(self):
        """Formatted status containing 'at_risk' returns yellow circle."""
        assert get_status_emoji("🟡 at_risk") == "🟡"

    def test_formatted_status_with_healthy(self):
        """Formatted status containing 'healthy' returns green circle."""
        assert get_status_emoji("🟢 healthy") == "🟢"

    def test_none_returns_empty_string(self):
        """None status returns empty string."""
        assert get_status_emoji(None) == ""

    def test_unknown_status_returns_empty_string(self):
        """Unknown status returns empty string."""
        assert get_status_emoji("unknown") == ""

    def test_empty_string_returns_empty_string(self):
        """Empty string status returns empty string."""
        assert get_status_emoji("") == ""


class TestFormatStageTimestamp:
    """Tests for format_stage_timestamp function (Story 4.2)."""

    def test_none_returns_unknown(self):
        """None datetime returns 'Unknown'."""
        result = format_stage_timestamp(None)
        assert result == "Unknown"

    def test_today_returns_today_format(self):
        """Today's datetime returns 'Today at X:XX PM'."""
        now = datetime.now(timezone.utc)
        # Set time to 2:30 PM
        today_at_230pm = now.replace(hour=14, minute=30, second=0, microsecond=0)
        result = format_stage_timestamp(today_at_230pm)
        assert result.startswith("Today at ")
        assert "2:30 PM" in result

    def test_yesterday_returns_yesterday_format(self):
        """Yesterday's datetime returns 'Yesterday at X:XX AM'."""
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        # Set time to 10:00 AM
        yesterday_at_10am = yesterday.replace(hour=10, minute=0, second=0, microsecond=0)
        result = format_stage_timestamp(yesterday_at_10am)
        assert result.startswith("Yesterday at ")
        assert "10:00 AM" in result

    def test_older_date_returns_full_format(self):
        """Older datetime returns 'Jan 5, 2026 at X:XX PM'."""
        # Use a fixed date in the past
        old_date = datetime(2026, 1, 5, 14, 30, 0, tzinfo=timezone.utc)
        result = format_stage_timestamp(old_date)
        assert "Jan" in result
        assert "5" in result
        assert "2026" in result
        assert "2:30 PM" in result

    def test_handles_midnight(self):
        """Midnight time formats correctly as 12:00 AM."""
        now = datetime.now(timezone.utc)
        today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        result = format_stage_timestamp(today_midnight)
        assert "12:00 AM" in result

    def test_handles_noon(self):
        """Noon time formats correctly as 12:00 PM."""
        now = datetime.now(timezone.utc)
        today_noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
        result = format_stage_timestamp(today_noon)
        assert "12:00 PM" in result


class TestFormatStageHistory:
    """Tests for format_stage_history function (Story 4.2)."""

    def test_empty_list_returns_empty(self):
        """Empty transitions list returns empty list."""
        result = format_stage_history([])
        assert result == []

    def test_single_transition_with_from_stage(self):
        """Single transition with from_stage formats correctly."""
        transitions = [{
            "from_stage": "Appt Set",
            "to_stage": "Green",
            "changed_at": datetime(2026, 1, 5, 10, 0, 0, tzinfo=timezone.utc),
        }]
        result = format_stage_history(transitions)
        assert len(result) == 1
        assert result[0]["transition"] == "Appt Set → Green"
        assert "Jan" in result[0]["timestamp"]
        assert result[0]["is_delivered"] is False

    def test_transition_without_from_stage_shows_initial(self):
        """Transition without from_stage shows 'Initial: Stage'."""
        transitions = [{
            "from_stage": None,
            "to_stage": "Appt Set",
            "changed_at": datetime(2026, 1, 3, 9, 0, 0, tzinfo=timezone.utc),
        }]
        result = format_stage_history(transitions)
        assert len(result) == 1
        assert result[0]["transition"] == "Initial: Appt Set"

    def test_multiple_transitions_in_order(self):
        """Multiple transitions are returned in same order."""
        transitions = [
            {"from_stage": None, "to_stage": "New", "changed_at": datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc)},
            {"from_stage": "New", "to_stage": "Appt Set", "changed_at": datetime(2026, 1, 2, 10, 0, 0, tzinfo=timezone.utc)},
            {"from_stage": "Appt Set", "to_stage": "Green", "changed_at": datetime(2026, 1, 3, 11, 0, 0, tzinfo=timezone.utc)},
        ]
        result = format_stage_history(transitions)
        assert len(result) == 3
        assert result[0]["transition"] == "Initial: New"
        assert result[1]["transition"] == "New → Appt Set"
        assert result[2]["transition"] == "Appt Set → Green"

    def test_delivered_stage_is_marked(self):
        """Delivered stage sets is_delivered flag."""
        transitions = [
            {"from_stage": "Green", "to_stage": "Delivered", "changed_at": datetime(2026, 1, 5, 14, 0, 0, tzinfo=timezone.utc)},
        ]
        result = format_stage_history(transitions)
        assert result[0]["is_delivered"] is True

    def test_delivery_requested_not_marked_as_delivered(self):
        """Delivery Requested is not marked as delivered."""
        transitions = [
            {"from_stage": "Green", "to_stage": "Delivery Requested", "changed_at": datetime(2026, 1, 5, 14, 0, 0, tzinfo=timezone.utc)},
        ]
        result = format_stage_history(transitions)
        assert result[0]["is_delivered"] is False

    def test_handles_none_changed_at(self):
        """Handles None changed_at gracefully."""
        transitions = [{
            "from_stage": "New",
            "to_stage": "Green",
            "changed_at": None,
        }]
        result = format_stage_history(transitions)
        assert result[0]["timestamp"] == "Unknown"

    def test_handles_missing_to_stage(self):
        """Handles missing to_stage with default 'Unknown'."""
        transitions = [{
            "from_stage": "Appt Set",
            "changed_at": datetime(2026, 1, 5, 10, 0, 0, tzinfo=timezone.utc),
        }]
        result = format_stage_history(transitions)
        assert result[0]["transition"] == "Appt Set → Unknown"


class TestFormatLeadsIncludesId:
    """Tests that format_leads_for_display includes lead ID (Story 4.2)."""

    def test_includes_lead_id(self):
        """Formatted lead includes the lead ID."""
        leads = [{
            "id": "12345",
            "name": "Test Lead",
            "appointment_date": datetime.now(timezone.utc),
            "current_stage": "Green",
            "locator_name": "Marcus",
            "locator_phone": "555-1234",
            "locator_email": "marcus@example.com",
        }]
        result = format_leads_for_display(leads)
        assert result[0]["id"] == "12345"

    def test_handles_none_id(self):
        """Handles leads with None ID."""
        leads = [{
            "name": "Test Lead",
            "appointment_date": datetime.now(timezone.utc),
            "current_stage": "Green",
        }]
        result = format_leads_for_display(leads)
        assert result[0]["id"] is None
