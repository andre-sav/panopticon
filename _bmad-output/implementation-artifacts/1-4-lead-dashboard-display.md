# Story 1.4: Lead Dashboard Display

Status: done

## Story

As **Damione (Coordinator)**,
I want **to see all leads with appointments in a data table showing key information**,
So that **I can quickly review my pipeline and identify leads needing attention**.

## Acceptance Criteria

1. **Given** the dashboard is opened
   **When** data loads successfully
   **Then** a data table displays with columns:
   - Lead Name
   - Appointment Date (formatted as "Jan 7, 2026")
   - Current Stage
   - Locator Name

2. **And** the total count of leads is displayed above the table (FR5)

3. **And** all leads with appointments are shown (no pagination)

4. **And** data matches exactly what exists in Zoho CRM (NFR1)

5. **Given** no leads have appointments
   **When** the dashboard loads
   **Then** a message displays: "No leads with appointments found"

6. **Given** data is loading
   **When** the dashboard first opens
   **Then** a loading indicator is shown

## Tasks / Subtasks

- [x] Task 1: Create main app.py dashboard structure (AC: #1, #6)
  - [x] 1.1: Replace placeholder with dashboard layout (header, main content area)
  - [x] 1.2: Import zoho_client and call `get_leads_with_appointments()`
  - [x] 1.3: Add loading spinner while fetching data
  - [x] 1.4: Store leads in `st.session_state` for caching

- [x] Task 2: Format and display lead data table (AC: #1, #3, #4)
  - [x] 2.1: Create display function to format leads for table
  - [x] 2.2: Format appointment_date as "Jan 7, 2026" using strftime
  - [x] 2.3: Display table with columns: Lead Name, Appointment Date, Stage, Locator
  - [x] 2.4: Show all leads without pagination (scrollable table)
  - [x] 2.5: Handle None values - display as "—" in UI

- [x] Task 3: Display lead count above table (AC: #2)
  - [x] 3.1: Add lead count display: "Showing X leads with appointments"
  - [x] 3.2: Position count above the data table

- [x] Task 4: Handle empty state (AC: #5)
  - [x] 4.1: Check if leads list is empty
  - [x] 4.2: Display message "No leads with appointments found" when empty

- [x] Task 5: Write unit tests (AC: #1, #2, #4, #5)
  - [x] 5.1: Test date formatting function
  - [x] 5.2: Test empty state handling
  - [x] 5.3: Test None value handling (display as "—")

## Dev Notes

### Architecture Compliance (CRITICAL)

**Files to modify:**
- `app.py` - Main dashboard layout and data display

**Files to use (read-only):**
- `src/zoho_client.py` - Use `get_leads_with_appointments()` function
- `src/field_mapping.py` - Reference field names

**Responsibility Boundaries:**
- `app.py`: UI rendering, Streamlit components, data formatting for display
- `zoho_client.py`: Already handles API calls (from Story 1.3)
- `data_processing.py`: Will handle staleness logic in Epic 2 (NOT this story)

### Streamlit Components to Use

**From UX Design Specification:**
- `st.dataframe()` or `st.table()` for lead table
- `st.spinner()` for loading state
- `st.metric()` for count display (optional)
- `st.columns()` for layout

### Date Formatting Pattern

**Python strftime for "Jan 7, 2026" format:**
```python
from datetime import datetime

def format_date(dt: datetime | None) -> str:
    """Format datetime as 'Jan 7, 2026' or '—' if None."""
    if dt is None:
        return "—"
    return dt.strftime("%b %-d, %Y")  # Use %#d on Windows
```

**Note:** `%-d` removes leading zero (Linux/Mac). Use `%#d` on Windows.

### Data Table Structure

**Expected columns from get_leads_with_appointments():**
```python
lead = {
    "id": "12345",
    "name": "John Smith",           # Display as "Lead Name"
    "appointment_date": datetime,   # Format as "Jan 7, 2026"
    "current_stage": "Appt Set",    # Display as "Stage"
    "locator_name": "Marcus",       # Display as "Locator"
    "locator_phone": "(555) 123-4567",  # For Story 1.7
    "locator_email": "marcus@example.com",  # For Story 1.7
}
```

**Table columns for this story:**
| Display Name | Data Key | Format |
|--------------|----------|--------|
| Lead Name | name | As-is or "—" if None |
| Appointment Date | appointment_date | "Jan 7, 2026" or "—" |
| Stage | current_stage | As-is or "—" if None |
| Locator | locator_name | As-is or "—" if None |

### Implementation Pattern

**app.py structure:**
```python
import streamlit as st
from src.zoho_client import get_leads_with_appointments

st.set_page_config(page_title="Panopticon", layout="wide")

# Header
st.title("Panopticon")
st.caption("Lead Follow-up Dashboard")

# Fetch data (with caching)
if "leads" not in st.session_state:
    with st.spinner("Loading leads..."):
        st.session_state.leads = get_leads_with_appointments()

leads = st.session_state.leads

# Display count
st.write(f"**Showing {len(leads)} leads with appointments**")

# Display table or empty state
if leads:
    # Format data for display
    display_data = format_leads_for_display(leads)
    st.dataframe(display_data, use_container_width=True)
else:
    st.info("No leads with appointments found")
```

### None Value Handling (NFR1, AC #4)

**From Architecture - Display missing data as "—":**
```python
def safe_display(value: str | None) -> str:
    """Return value or '—' for None."""
    return value if value is not None else "—"
```

### Error State Handling

**Note:** Full error handling UI is Story 1.6. For this story:
- If `get_leads_with_appointments()` returns [], show empty state
- Error messages are stored in `st.session_state.zoho_error` (from Story 1.2)
- Basic error display can show the error if present

### Previous Story Intelligence

**From Story 1.3:**
- `get_leads_with_appointments()` returns `list[dict]`
- Returns `[]` on API errors
- Each lead dict has: id, name, appointment_date, current_stage, locator_name, locator_phone, locator_email
- appointment_date is a Python datetime in UTC

**From Story 1.2:**
- `get_last_error()` returns any error message
- Error stored in `st.session_state.zoho_error`

### Testing Considerations

**Unit testable functions:**
- Date formatting function
- None value handling
- Lead list to display data transformation

**Integration testing (manual):**
- Verify table displays correctly with real Zoho data
- Verify empty state when no leads have appointments

### References

- [Source: architecture.md#Project-Structure] - app.py responsibilities
- [Source: ux-design-specification.md#Design-System] - Streamlit components
- [Source: epics.md#Story-1.4] - Original acceptance criteria

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Implemented main dashboard in `app.py` with header, data fetching, and display
- Added `format_date()`, `safe_display()`, and `format_leads_for_display()` to `data_processing.py`
- Date formatting uses platform-aware strftime for day without leading zero
- Displays "—" for None/missing values per NFR1 requirements
- Loading spinner shown during initial data fetch
- Session state caching prevents redundant API calls
- All 6 acceptance criteria satisfied
- 86 tests total (14 new for this story), all passing

### Change Log

- 2026-01-08: Implemented Story 1.4 - Lead Dashboard Display
- 2026-01-08: Code review fixes - removed redundant count on empty state, inlined fetch_leads()

### File List

- app.py (modified)
- src/data_processing.py (modified)
- tests/test_data_processing.py (modified)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified)

## Senior Developer Review (AI)

**Review Date:** 2026-01-08
**Review Outcome:** Approved (after fixes)
**Reviewer:** Claude Opus 4.5

### Issues Found and Resolved

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| M1 | Medium | File List missing sprint-status.yaml | Added to File List |
| L1 | Low | Redundant "Showing 0 leads" before empty state | Moved count inside `if leads:` block |
| L2 | Low | Trivial `fetch_leads()` wrapper function | Inlined call to `get_leads_with_appointments()` |
| L3 | Low | No app.py integration tests | Noted - acceptable for Streamlit apps |

### Action Items

- [x] M1: Update File List to include sprint-status.yaml
- [x] L1: Only show lead count when leads exist
- [x] L2: Remove trivial wrapper, inline API call

