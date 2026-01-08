# Story 2.2: Stale Lead Detection Logic

Status: done

## Story

As **Damione (Coordinator)**,
I want **leads to be flagged as "stale" when 7+ days have passed since their appointment**,
So that **I can identify leads that have been sitting too long without progress**.

## Acceptance Criteria

1. **Given** a lead with an appointment 7 or more days ago
   **When** the dashboard displays the lead
   **Then** the lead is marked with status "stale"

2. **Given** a lead with an appointment 6 days ago
   **When** status is determined
   **Then** the lead is NOT marked as stale (threshold is 7+)

3. **And** the constant `STALE_THRESHOLD_DAYS = 7` is defined once in data_processing.py
   **And** all status determinations use the centralized `get_lead_status()` function

## Tasks / Subtasks

- [x] Task 1: Add Status column to format_leads_for_display (AC: #1, #2, #3)
  - [x] 1.1: Call get_lead_status() with Days value to determine status
  - [x] 1.2: Add "Status" key to output dict with status string
  - [x] 1.3: Handle None Days gracefully (return None)

- [x] Task 2: Write unit tests (AC: #1, #2, #3)
  - [x] 2.1: Test Status column shows "stale" for 7+ days
  - [x] 2.2: Test Status column shows "healthy" for < 5 days
  - [x] 2.3: Test Status column shows "at_risk" for 5-6 days
  - [x] 2.4: Test Status column handling for None appointment_date

## Dev Notes

### Architecture Compliance (CRITICAL)

**Files to modify:**
- `src/data_processing.py` - Update `format_leads_for_display()` to include Status column
- `tests/test_data_processing.py` - Add tests for Status column

### Existing Implementation to Leverage

The status logic ALREADY EXISTS in `data_processing.py`:

```python
STALE_THRESHOLD_DAYS = 7
AT_RISK_THRESHOLD_DAYS = 5

def get_lead_status(days_since: int) -> str:
    """Returns 'stale', 'at_risk', or 'healthy'."""
    if days_since >= STALE_THRESHOLD_DAYS:
        return "stale"
    elif days_since >= AT_RISK_THRESHOLD_DAYS:
        return "at_risk"
    return "healthy"
```

**DO NOT re-implement. Just USE `get_lead_status()` with the Days value.**

### Implementation Pattern

```python
def format_leads_for_display(leads: list[dict]) -> list[dict]:
    return [
        {
            ...
            "Days": days := (calculate_days_since(lead["appointment_date"]) if lead.get("appointment_date") else None),
            "Status": get_lead_status(days) if days is not None else None,
            ...
        }
        for lead in leads
    ]
```

Note: Python 3.8+ walrus operator `:=` can be used, or compute Days first then Status.

### Column Order

1. Lead Name
2. Appointment Date
3. Days
4. Status (NEW)
5. Stage
6. Locator
7. Phone/Email

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Added "Status" column to `format_leads_for_display()` using existing `get_lead_status()` function
- Refactored function from list comprehension to loop to compute Days then Status
- Status shows: "stale" (7+ days), "at_risk" (5-6 days), "healthy" (<5 days)
- None returned when appointment_date is missing
- Updated existing column test to expect 8 columns (was 7)
- Added 6 new tests in TestFormatLeadsForDisplayStatus class
- All 3 acceptance criteria satisfied
- 135 tests total (6 new for this story), all passing

### Senior Developer Review

**Issues Found:** 3 Low
- L1: Story scope includes at_risk (Story 2.3 territory) - Acceptable, no fix needed
- L2: No Status test for 0 or negative days - **FIXED** (added 2 tests)
- L3: Status values not explained in docstring - **FIXED** (updated docstring)

**Verdict:** APPROVED

### Change Log

- 2026-01-08: Implemented Story 2.2 - Stale Lead Detection Logic
- 2026-01-08: Code review completed - 2 LOW issues fixed

### File List

- src/data_processing.py (modified)
- tests/test_data_processing.py (modified)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified)

