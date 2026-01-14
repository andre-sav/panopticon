"""
Zoho CRM field name mappings.

Maps Zoho field names to internal snake_case names.
"""

# Zoho field to internal name mapping
# Based on ZOHO_API_REFERENCE.md - Locatings module
ZOHO_FIELD_MAP = {
    "id": "id",
    "Name": "name",  # Location/business name
    "Stage": "current_stage",
    "Locator_Name": "locator_name",  # Lookup field - returns {id, name} object
    "APPT_Date": "appointment_date",  # Actual appointment date field
    "Street_Address": "street_address",  # For delivery matching
    "Zip_Code": "zip_code",  # For delivery matching
    "Created_Time": "created_time",
    "Modified_Time": "modified_time",
}

# Pipeline stage ordering (for sorting/display)
# Based on ZOHO_API_REFERENCE.md stage flow
STAGE_ORDER = [
    "Appt Not Acknowledged",
    "HLM Follow up",
    "Green - Approved By Locator",
    "Green - SiteSurvey Sent",
    "Green - LLL Approved",
    "Green - LLL Fulfilled",
    "Green/No-operator",
    "Delivery Requested",
    "Green/Delivered",
    "Declined By Operator",
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
