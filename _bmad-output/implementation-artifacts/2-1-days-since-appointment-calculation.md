# Story 2.1: Days Since Appointment Calculation

Status: done

## Story

As **Damione (Coordinator)**,
I want **to see how many days have passed since each lead's appointment**,
So that **I can quickly understand how long a lead has been waiting for follow-up**.

## Acceptance Criteria

1. **Given** a lead with an appointment date
   **When** the dashboard displays the lead
   **Then** a "Days" column shows the number of calendar days since the appointment

2. **Given** today is January 8, 2026 and appointment was January 1, 2026
   **When** days are calculated
   **Then** the value shows "7" (not 6.5 or 168 hours)

3. **Given** an appointment is in the future
   **When** days are calculated
   **Then** the value shows a negative number (e.g., "-2" for 2 days from now)

4. **And** all calculations use the centralized `calculate_days_since()` function in data_processing.py (NFR3)
   **And** calculations are accurate to the calendar day, not hours/minutes

## Tasks / Subtasks

- [x] Task 1: Update format_leads_for_display to include Days column (AC: #1, #4)
  - [x] 1.1: Add `days_since` calculation using existing `calculate_days_since()` function
  - [x] 1.2: Add "Days" key to output dict with integer value
  - [x] 1.3: Handle None appointment_date gracefully (return None)

- [x] Task 2: Update app.py to display Days column (AC: #1)
  - [x] 2.1: Ensure Days column appears in dataframe after Appointment Date
  - [x] 2.2: Configure column display (integer, right-aligned) - N/A: st.dataframe auto-handles

- [x] Task 3: Write unit tests (AC: #1, #2, #3, #4)
  - [x] 3.1: Test days calculation for past appointment (positive days)
  - [x] 3.2: Test days calculation for today's appointment (0 days)
  - [x] 3.3: Test days calculation for future appointment (negative days)
  - [x] 3.4: Test Days column appears in format_leads_for_display output
  - [x] 3.5: Test None appointment_date handling

## Dev Notes

### Architecture Compliance (CRITICAL)

**Files to modify:**
- `src/data_processing.py` - Update `format_leads_for_display()` to include Days column
- `app.py` - No changes needed (st.dataframe auto-displays new columns)
- `tests/test_data_processing.py` - Add tests for Days column

**Files NOT to modify:**
- Do NOT create new files
- Do NOT modify `zoho_client.py` (data fetching is separate concern)

### Existing Implementation to Leverage

The calculation logic ALREADY EXISTS in `data_processing.py`:

```python
# These functions are already implemented and tested (Story 1.x):
def calculate_days_since(appointment_date: datetime) -> int:
    """Returns calendar days since appointment. Negative = future."""
    today = datetime.now(timezone.utc).date()
    return (today - appointment_date.date()).days

# Constants already defined:
STALE_THRESHOLD_DAYS = 7
AT_RISK_THRESHOLD_DAYS = 5
```

**DO NOT re-implement these functions. Just USE them.**

### Implementation Pattern

Update `format_leads_for_display()` to add Days column:

```python
def format_leads_for_display(leads: list[dict]) -> list[dict]:
    return [
        {
            "Lead Name": safe_display(lead.get("name")),
            "Appointment Date": format_date(lead.get("appointment_date")),
            "Days": calculate_days_since(lead["appointment_date"]) if lead.get("appointment_date") else None,  # NEW
            "Stage": safe_display(lead.get("current_stage")),
            "Locator": safe_display(lead.get("locator_name")),
            "Phone": format_phone_link(lead.get("locator_phone")),
            "Email": format_email_link(lead.get("locator_email")),
        }
        for lead in leads
    ]
```

### Column Order (UX Design)

Per UX spec, columns should flow logically:
1. Lead Name - who
2. Appointment Date - when
3. Days - how long ago (NEW)
4. Stage - current status
5. Locator - who's responsible
6. Phone/Email - contact actions

### Previous Story Intelligence

**From Story 1.7 (Locator Contact Actions):**
- `format_leads_for_display()` returns list of dicts with display columns
- Column order in dict determines display order in st.dataframe
- None values in columns are handled gracefully by Streamlit
- Test pattern: verify column exists and has expected value type

**From Story 1.4 (Lead Dashboard Display):**
- `st.dataframe()` auto-displays all columns from dict
- No special column_config needed for integer columns
- Test assertion: `assert set(result[0].keys()) == {expected columns}`

### Testing Standards

Tests go in `tests/test_data_processing.py` in class `TestFormatLeadsForDisplay` or new class `TestFormatLeadsForDisplayDays`.

Pattern from existing tests:
```python
def test_includes_days_for_past_appointment(self):
    """Days column shows positive value for past appointment."""
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
```

### References

- [Source: epics.md#Story-2.1] - Original acceptance criteria
- [Source: architecture.md#Implementation-Patterns] - Staleness calculation pattern
- [Source: architecture.md#Naming-Patterns] - Column naming convention
- [Source: ux-design-specification.md#Core-User-Experience] - Visual triage system

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Added "Days" column to `format_leads_for_display()` using existing `calculate_days_since()` function
- Column shows integer days: positive for past, 0 for today, negative for future appointments
- None returned when appointment_date is missing (Streamlit displays blank)
- No changes needed to app.py - st.dataframe auto-displays new column
- Updated existing test to expect 7 columns (was 6)
- Added 5 new tests in TestFormatLeadsForDisplayDays class
- All 4 acceptance criteria satisfied
- 128 tests total (5 new for this story), all passing

### Senior Developer Review

**Issues Found:** 3 Low
- L1: Task 2 wording implies code change but was verification only - Acceptable, no fix needed
- L2: No test for exact 7-day example from AC#2 - **FIXED** (added `test_days_seven_for_week_old_appointment`)
- L3: Test docstring AC reference imprecise - **FIXED** (updated docstring)

**Verdict:** APPROVED

### Change Log

- 2026-01-08: Implemented Story 2.1 - Days Since Appointment Calculation
- 2026-01-08: Code review completed - 2 LOW issues fixed

### File List

- src/data_processing.py (modified)
- tests/test_data_processing.py (modified)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified)

