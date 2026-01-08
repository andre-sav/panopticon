# Story 1.3: Fetch Leads with Appointments

Status: done

## Story

As a **developer**,
I want **to retrieve all leads with scheduled appointments from Zoho CRM**,
So that **the dashboard has the data needed to display the lead list**.

## Acceptance Criteria

1. **Given** a valid Zoho API connection
   **When** `get_leads_with_appointments()` is called
   **Then** it returns a list of lead dictionaries containing:
   - Lead ID
   - Lead name
   - Appointment date/time
   - Current stage
   - Locator name
   - Locator phone
   - Locator email

2. **Given** Zoho field names differ from internal names
   **When** data is fetched
   **Then** field_mapping.py maps Zoho fields to snake_case internal names

3. **Given** an API error occurs
   **When** fetching leads
   **Then** an empty list is returned (not None)
   **And** the error is captured for display (not silently swallowed)

4. **Given** a lead has missing locator info
   **When** data is returned
   **Then** missing fields are None (to be displayed as "—" in UI)

## Tasks / Subtasks

- [x] Task 1: Define Zoho field mappings (AC: #2)
  - [x] 1.1: Research Zoho CRM Leads module field names via API documentation
  - [x] 1.2: Populate `ZOHO_FIELD_MAP` in `src/field_mapping.py` with lead field mappings
  - [x] 1.3: Define `STAGE_ORDER` list with pipeline stage sequence

- [x] Task 2: Implement `get_leads_with_appointments()` function (AC: #1, #3, #4)
  - [x] 2.1: Add function to `src/zoho_client.py` that calls Zoho CRM Leads API
  - [x] 2.2: Use `_make_request()` for authenticated API calls
  - [x] 2.3: Parse response and map fields using `field_mapping.py`
  - [x] 2.4: Return empty list `[]` on any error
  - [x] 2.5: Handle missing/null fields gracefully (set to None)

- [x] Task 3: Add date parsing and validation (AC: #1)
  - [x] 3.1: Parse Zoho date strings to Python datetime objects
  - [x] 3.2: Handle timezone conversion (store as UTC internally)
  - [x] 3.3: Handle invalid or missing dates gracefully

- [x] Task 4: Write unit tests (AC: #1, #2, #3, #4)
  - [x] 4.1: Test successful lead fetch with all fields
  - [x] 4.2: Test field mapping from Zoho names to internal names
  - [x] 4.3: Test empty list returned on API error
  - [x] 4.4: Test handling of missing/null fields

## Dev Notes

### Architecture Compliance (CRITICAL)

**Files to modify:**
- `src/zoho_client.py` - Add `get_leads_with_appointments()` function
- `src/field_mapping.py` - Populate field mappings and stage order

**Responsibility Boundaries:**
- `zoho_client.py`: API calls, response parsing, field mapping application
- `field_mapping.py`: Static field name mappings only
- Does NOT: Staleness calculations (that's `data_processing.py` in Story 2.x)

### Zoho CRM API Details

**Leads Module Endpoint:**
```
GET {api_domain}/crm/v2/Leads
Authorization: Zoho-oauthtoken {access_token}
```

**Query Parameters:**
- `fields`: Comma-separated list of fields to retrieve
- `criteria`: Optional COQL filter (e.g., `(Appointment_Date:is_not_empty:)`)
- `per_page`: Number of records (max 200)
- `page`: Page number for pagination

**Example Request:**
```python
url = f"{get_api_domain()}/crm/v2/Leads"
params = {
    "fields": "id,Full_Name,Appointment_Date,Stage,Locator_Name,Locator_Phone,Locator_Email",
    "criteria": "(Appointment_Date:is_not_empty:)",
    "per_page": 200
}
response = _make_request("GET", url, params=params)
```

**Example Response:**
```json
{
  "data": [
    {
      "id": "1234567890",
      "Full_Name": "John Smith",
      "Appointment_Date": "2026-01-07T10:30:00-05:00",
      "Stage": "Appt Set",
      "Locator_Name": "Marcus Johnson",
      "Locator_Phone": "(555) 123-4567",
      "Locator_Email": "marcus@example.com"
    }
  ],
  "info": {
    "per_page": 200,
    "count": 1,
    "page": 1,
    "more_records": false
  }
}
```

### Field Mapping Pattern

**In `src/field_mapping.py`:**
```python
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
    """Map Zoho field names to internal names."""
    return {
        internal_name: zoho_record.get(zoho_name)
        for zoho_name, internal_name in ZOHO_FIELD_MAP.items()
    }
```

### Implementation Pattern

**Return Data Structure (from architecture.md):**
```python
lead = {
    "id": "12345",
    "name": "John Smith",
    "appointment_date": datetime(...),  # Python datetime in UTC
    "current_stage": "Appt Set",
    "locator_name": "Marcus Johnson",
    "locator_phone": "(555) 123-4567",
    "locator_email": "marcus@example.com",
}
```

**Function Signature:**
```python
def get_leads_with_appointments() -> list[dict]:
    """
    Fetch all leads with scheduled appointments from Zoho CRM.

    Returns:
        List of lead dictionaries with mapped field names.
        Empty list if API error occurs.
    """
```

### Date Handling

**Zoho Date Format:** ISO 8601 with timezone (e.g., `2026-01-07T10:30:00-05:00`)

**Parsing Pattern:**
```python
from dateutil import parser
from datetime import timezone

def parse_zoho_date(date_string: str) -> datetime | None:
    """Parse Zoho date string to UTC datetime."""
    if not date_string:
        return None
    try:
        dt = parser.parse(date_string)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None
```

### Error Handling Standards

**From architecture.md - Return empty list, capture error:**
```python
def get_leads_with_appointments() -> list[dict]:
    """Returns list of lead dicts. Empty list on error (not None)."""
    try:
        response = _make_request("GET", url, params=params)
        if response is None:
            return []  # Error already captured in _make_request
        return [map_and_parse_lead(lead) for lead in response.json().get("data", [])]
    except Exception:
        st.session_state.zoho_error = "Error processing lead data."
        return []
```

### Previous Story Intelligence

**From Story 1.2:**
- `_make_request()` is available for authenticated API calls
- `get_api_domain()` returns the API base URL
- Error handling stores messages in `st.session_state.zoho_error`
- 30-second timeout is built into `_make_request()`
- Rate limit handling with backoff is implemented

**Code patterns established:**
- Type hints on all functions
- Docstrings for public functions
- Tests use pytest with mocking

### Testing This Story

1. Ensure `.streamlit/secrets.toml` has valid Zoho credentials
2. Run: `python -c "from src.zoho_client import get_leads_with_appointments; print(get_leads_with_appointments())"`
3. Verify: Returns list of lead dicts with correct field names
4. Run: `python -m pytest tests/test_zoho_client.py -v -k leads`

### Zoho CRM Field Discovery

**NOTE:** Zoho field names may vary based on your CRM configuration. Common field naming patterns:
- Custom fields often have `_c` suffix
- System fields use Title_Case or camelCase
- Lookup fields may return objects instead of strings

If field names don't match, update `ZOHO_FIELD_MAP` in `field_mapping.py` accordingly.

### Pagination Consideration

For MVP with expected <200 leads, pagination is not required. If more leads exist:
- API returns `info.more_records: true`
- Implement pagination in a future story if needed

### References

- [Source: architecture.md#Project-Structure-Boundaries] - File responsibilities
- [Source: architecture.md#Communication-Patterns] - Data shape and error handling
- [Source: epics.md#Story-1.3] - Original acceptance criteria
- [Zoho CRM API - Get Records](https://www.zoho.com/crm/developer/docs/api/v2/get-records.html)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Implemented `ZOHO_FIELD_MAP` and `STAGE_ORDER` constants in `field_mapping.py`
- Added `map_zoho_lead()` function for field name transformation
- Implemented `parse_zoho_date()` for ISO 8601 date parsing with UTC conversion
- Implemented `get_leads_with_appointments()` using `_make_request()` for authenticated API calls
- Added `_map_and_parse_lead()` helper for combined mapping and date parsing
- All 4 acceptance criteria satisfied
- 67 tests total (24 new for this story), all passing

### Change Log

- 2026-01-08: Implemented Story 1.3 - Fetch Leads with Appointments
- 2026-01-08: Code review fixes - specific exception handling, naive datetime handling, 5 new tests

### File List

- src/field_mapping.py (modified)
- src/zoho_client.py (modified)
- tests/test_field_mapping.py (created)
- tests/test_zoho_client.py (modified)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified)

## Senior Developer Review (AI)

**Review Date:** 2026-01-08
**Review Outcome:** Approved (after fixes)
**Reviewer:** Claude Opus 4.5

### Issues Found and Resolved

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| M1 | Medium | File List missing sprint-status.yaml | Added to File List |
| M2 | Medium | Broad `except Exception:` handler | Changed to specific exceptions (JSONDecodeError, KeyError, TypeError, AttributeError) |
| M3 | Medium | No test for JSON decode error | Added `test_returns_empty_list_on_json_decode_error` |
| M4 | Medium | No test for processing exception path | Added `test_returns_empty_list_on_processing_error` |
| L1 | Low | STAGE_ORDER unused | Acceptable - reserved for future stories |
| L2 | Low | No direct tests for `_map_and_parse_lead()` | Added `TestMapAndParseLead` class with 2 tests |
| L3 | Low | Naive datetime handling | Added explicit UTC assumption for naive datetimes |

### Action Items

- [x] M1: Update File List to include sprint-status.yaml
- [x] M2: Replace broad exception with specific JSONDecodeError, KeyError, TypeError, AttributeError
- [x] M3: Add test for JSONDecodeError handling
- [x] M4: Add test for processing exception path
- [x] L2: Add direct tests for _map_and_parse_lead helper
- [x] L3: Handle naive datetimes by assuming UTC
