"""
Unit tests for field_mapping module.

Tests Zoho field name mapping to internal names.
"""
import pytest
from src.field_mapping import ZOHO_FIELD_MAP, STAGE_ORDER, map_zoho_lead


class TestZohoFieldMap:
    """Tests for ZOHO_FIELD_MAP constant."""

    def test_contains_required_fields(self):
        """ZOHO_FIELD_MAP contains all required lead fields."""
        required_internal_names = [
            "id",
            "name",
            "appointment_date",
            "current_stage",
            "locator_name",
            "locator_phone",
            "locator_email",
        ]
        internal_names = list(ZOHO_FIELD_MAP.values())
        for name in required_internal_names:
            assert name in internal_names, f"Missing required field: {name}"

    def test_maps_zoho_field_names(self):
        """ZOHO_FIELD_MAP maps expected Zoho field names."""
        assert ZOHO_FIELD_MAP["id"] == "id"
        assert ZOHO_FIELD_MAP["Full_Name"] == "name"
        assert ZOHO_FIELD_MAP["Appointment_Date"] == "appointment_date"
        assert ZOHO_FIELD_MAP["Stage"] == "current_stage"
        assert ZOHO_FIELD_MAP["Locator_Name"] == "locator_name"
        assert ZOHO_FIELD_MAP["Locator_Phone"] == "locator_phone"
        assert ZOHO_FIELD_MAP["Locator_Email"] == "locator_email"


class TestStageOrder:
    """Tests for STAGE_ORDER constant."""

    def test_contains_expected_stages(self):
        """STAGE_ORDER contains all pipeline stages."""
        expected_stages = [
            "Appt Set",
            "Appt Acknowledged",
            "Green",
            "Green - Pending",
            "Delivery Requested",
            "Delivered",
        ]
        assert STAGE_ORDER == expected_stages

    def test_stage_order_is_list(self):
        """STAGE_ORDER is a list for ordered iteration."""
        assert isinstance(STAGE_ORDER, list)


class TestMapZohoLead:
    """Tests for map_zoho_lead function."""

    def test_maps_all_fields(self):
        """map_zoho_lead correctly maps all Zoho fields to internal names."""
        zoho_record = {
            "id": "1234567890",
            "Full_Name": "John Smith",
            "Appointment_Date": "2026-01-07T10:30:00-05:00",
            "Stage": "Appt Set",
            "Locator_Name": "Marcus Johnson",
            "Locator_Phone": "(555) 123-4567",
            "Locator_Email": "marcus@example.com",
        }

        result = map_zoho_lead(zoho_record)

        assert result["id"] == "1234567890"
        assert result["name"] == "John Smith"
        assert result["appointment_date"] == "2026-01-07T10:30:00-05:00"
        assert result["current_stage"] == "Appt Set"
        assert result["locator_name"] == "Marcus Johnson"
        assert result["locator_phone"] == "(555) 123-4567"
        assert result["locator_email"] == "marcus@example.com"

    def test_handles_missing_fields_as_none(self):
        """map_zoho_lead returns None for missing fields (AC #4)."""
        zoho_record = {
            "id": "1234567890",
            "Full_Name": "John Smith",
            # Missing: Appointment_Date, Stage, Locator fields
        }

        result = map_zoho_lead(zoho_record)

        assert result["id"] == "1234567890"
        assert result["name"] == "John Smith"
        assert result["appointment_date"] is None
        assert result["current_stage"] is None
        assert result["locator_name"] is None
        assert result["locator_phone"] is None
        assert result["locator_email"] is None

    def test_handles_null_values_as_none(self):
        """map_zoho_lead preserves None values from Zoho API."""
        zoho_record = {
            "id": "1234567890",
            "Full_Name": "John Smith",
            "Appointment_Date": None,
            "Stage": None,
            "Locator_Name": None,
            "Locator_Phone": None,
            "Locator_Email": None,
        }

        result = map_zoho_lead(zoho_record)

        assert result["appointment_date"] is None
        assert result["current_stage"] is None
        assert result["locator_name"] is None
        assert result["locator_phone"] is None
        assert result["locator_email"] is None

    def test_handles_empty_record(self):
        """map_zoho_lead handles empty record gracefully."""
        result = map_zoho_lead({})

        for value in result.values():
            assert value is None

    def test_ignores_extra_zoho_fields(self):
        """map_zoho_lead ignores fields not in ZOHO_FIELD_MAP."""
        zoho_record = {
            "id": "123",
            "Full_Name": "Test",
            "Extra_Field": "should be ignored",
            "Another_Field": "also ignored",
        }

        result = map_zoho_lead(zoho_record)

        assert "Extra_Field" not in result
        assert "Another_Field" not in result
        assert "extra_field" not in result
