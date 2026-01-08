"""
Unit tests for data_processing module.
"""
import pytest
from datetime import datetime, timezone, timedelta

from src.data_processing import (
    calculate_days_since,
    get_lead_status,
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
