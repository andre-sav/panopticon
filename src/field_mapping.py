"""
Zoho CRM field name mappings.

Maps Zoho field names to internal snake_case names.
"""

# Zoho field to internal name mapping
ZOHO_FIELD_MAP = {
    "id": "id",
    "Full_Name": "name",
    "Appointment_Date": "appointment_date",
    "Stage": "current_stage",
    "Locator_Name": "locator_name",
    "Locator_Phone": "locator_phone",
    "Locator_Email": "locator_email",
}

# Pipeline stage ordering (for sorting/display)
STAGE_ORDER = [
    "Appt Set",
    "Appt Acknowledged",
    "Green",
    "Green - Pending",
    "Delivery Requested",
    "Delivered",
]


def map_zoho_lead(zoho_record: dict) -> dict:
    """
    Map Zoho field names to internal names.

    Args:
        zoho_record: Dictionary with Zoho field names as keys

    Returns:
        Dictionary with internal snake_case field names
    """
    return {
        internal_name: zoho_record.get(zoho_name)
        for zoho_name, internal_name in ZOHO_FIELD_MAP.items()
    }
