# Story 2.6: Summary Metrics Cards

Status: done

## Story

As **Damione (Coordinator)**,
I want **to see counts of stale, at-risk, and healthy leads at the top of the dashboard**,
So that **I instantly know the overall health of my pipeline before looking at details**.

## Acceptance Criteria

1. **Given** the dashboard is displayed
   **When** looking at the header/summary area
   **Then** three metric cards are visible:
   - "Stale" with count and red indicator
   - "At Risk" with count and amber indicator
   - "Healthy" with count and green indicator

2. **Given** there are 3 stale, 5 at-risk, and 42 healthy leads
   **When** the metrics display
   **Then** the cards show "3", "5", and "42" respectively

3. **Given** there are 0 stale leads
   **When** the stale metric displays
   **Then** it shows "0" (not hidden)
   **And** a positive signal is conveyed (e.g., checkmark or green styling)

4. **And** metrics update when data is refreshed

5. **And** metrics reflect current filter state (if filters are applied in Epic 3)
   *(Note: Filter integration is Epic 3 scope - this story implements the metrics display)*

## Tasks / Subtasks

- [x] Task 1: Create count_leads_by_status() function (AC: #1, #2)
  - [x] 1.1: Define function that takes formatted display_data list
  - [x] 1.2: Count leads by status (stale, at_risk, healthy)
  - [x] 1.3: Return dictionary with counts for each status
  - [x] 1.4: Handle leads with None status (count as uncategorized or healthy)

- [x] Task 2: Add summary metrics cards section in app.py (AC: #1, #2, #3)
  - [x] 2.1: Create display_metrics_cards() function
  - [x] 2.2: Use st.columns() with 3 columns for the cards
  - [x] 2.3: Use st.metric() for each card with appropriate labels
  - [x] 2.4: Apply color styling (red/amber/green) to metrics via emoji
  - [x] 2.5: Show positive signal when stale count is 0

- [x] Task 3: Write unit tests (AC: #1, #2, #3)
  - [x] 3.1: Test count with mixed statuses returns correct counts
  - [x] 3.2: Test count with all stale leads
  - [x] 3.3: Test count with all healthy leads
  - [x] 3.4: Test count with empty list returns zeros
  - [x] 3.5: Test count handles None status values

## Dev Notes

### Implementation Approach

The `count_leads_by_status()` function:
- Takes the formatted display_data (after `format_leads_for_display()`)
- Counts leads by parsing the Status field (contains emoji prefix like "stale", "at_risk", "healthy")
- Returns a dict: `{"stale": N, "at_risk": N, "healthy": N}`

### UI Layout

Metrics cards placed between header and lead table:
1. Header (title, last updated, refresh)
2. **Metrics Cards (3 columns)** - Uses st.metric() with emoji labels
3. Divider
4. Lead count + Data table

### Status Colors
- Stale: Red emoji indicator (🔴)
- At Risk: Amber emoji indicator (🟡)
- Healthy: Green emoji indicator (🟢)

## Senior Developer Review (AI)

**Review Date:** 2026-01-08
**Review Outcome:** Approve (after fixes)
**Reviewer Model:** Claude Opus 4.5

### Findings Summary
- **High:** 0
- **Medium:** 1 (fixed)
- **Low:** 6 (fixed)

### Action Items
- [x] [Medium] File List incomplete - sprint-status.yaml not documented
- [x] [Low] Missing edge case test for empty string status
- [x] [Low] Type inconsistency - "0 ✓" string vs integer (fixed with delta parameter)
- [x] [Low] Hardcoded threshold values in help text
- [x] [Low] Incomplete docstring for count_leads_by_status
- [x] [Low] No test for total count verification

### Fixes Applied
1. Updated File List to include sprint-status.yaml
2. Added test_count_handles_empty_string_status test
3. Changed stale=0 display to use `value=0, delta="All clear"` for type consistency
4. Imported STALE_THRESHOLD_DAYS and AT_RISK_THRESHOLD_DAYS in app.py
5. Updated help text to use f-strings with threshold constants
6. Enhanced docstring to document None/empty status handling
7. Added test_count_total_equals_input_length test

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Completion Notes List

- Added `count_leads_by_status()` function to data_processing.py
- Function counts leads by status category using Status field pattern matching
- Leads with None or empty status are counted as healthy
- Added `display_metrics_cards()` function to app.py
- Uses st.columns(3) and st.metric() for the three cards
- Stale card shows value=0 with delta="All clear" when count is 0
- Help text uses threshold constants for maintainability
- Added 8 unit tests for count_leads_by_status()
- All 159 tests pass (no regressions)

### Change Log

- 2026-01-08: Implemented Story 2.6 - Summary Metrics Cards
- 2026-01-08: Code review fixes - improved tests, docstrings, and threshold handling

### File List

- src/data_processing.py (modified)
- app.py (modified)
- tests/test_data_processing.py (modified)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified)
