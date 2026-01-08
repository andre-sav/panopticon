# Story 3.2: User-Selectable Sorting

Status: done

## Story

As **Damione (Coordinator)**,
I want **to sort leads by different columns**,
So that **I can organize the data in the way that's most useful for my current task**.

## Acceptance Criteria

1. **Given** the lead table is displayed
   **When** I interact with sort controls
   **Then** I can sort by:
   - Days since appointment (default: descending/most stale first)
   - Appointment date (ascending/descending)
   - Lead name (alphabetical)
   - Stage
   - Locator name

2. **Given** I sort by "Appointment Date (Oldest First)"
   **When** the sort is applied
   **Then** leads are ordered by appointment date ascending
   **And** the current sort is visually indicated

3. **Given** I want to return to default sorting
   **When** I select "Default (Urgency)"
   **Then** problems-first sorting (from Story 2.5) is restored

4. **And** sorting works in combination with active filters
   **And** sort preference is maintained during the session

## Tasks / Subtasks

- [x] Task 1: Define sort options and constants (AC: #1)
  - [x] 1.1: Add SORT_OPTIONS constant with all sort choices
  - [x] 1.2: Add DEFAULT_SORT constant for urgency sort

- [x] Task 2: Implement sort functions (AC: #1, #2)
  - [x] 2.1: Create sort_leads() dispatcher function
  - [x] 2.2: Implement sort by Days (ascending/descending)
  - [x] 2.3: Implement sort by Appointment Date
  - [x] 2.4: Implement sort by Lead Name (alphabetical)
  - [x] 2.5: Implement sort by Stage
  - [x] 2.6: Implement sort by Locator
  - [x] 2.7: Write unit tests for each sort option

- [x] Task 3: Add sort UI control (AC: #2, #3)
  - [x] 3.1: Add sort selectbox in app.py
  - [x] 3.2: Store sort preference in st.session_state
  - [x] 3.3: Apply selected sort after filtering

- [x] Task 4: Integration with filters (AC: #4)
  - [x] 4.1: Verify sort applies to filtered data
  - [x] 4.2: Verify sort persists across filter changes
  - [x] 4.3: Write integration test for filter + sort

## Dev Notes

### Architecture Compliance

**Files to modify:**
- `src/data_processing.py` - Add sort functions
- `app.py` - Add sort UI control
- `tests/test_data_processing.py` - Add sort tests

### Data Flow

```
Raw leads from API
    ↓
format_leads_for_display()
    ↓
display_filters() → apply_filters()
    ↓
sort_leads(sort_option)  ← NEW (replaces hardcoded sort_by_urgency)
    ↓
display_metrics_cards(filtered_data)
    ↓
st.dataframe(sorted_data)
```

### Sort Options

- "Default (Urgency)" - sort_by_urgency() from Story 2.5
- "Days (Most First)" - Days descending
- "Days (Least First)" - Days ascending
- "Appointment Date (Newest)" - Date descending
- "Appointment Date (Oldest)" - Date ascending
- "Lead Name (A-Z)"
- "Stage (A-Z)"
- "Locator (A-Z)"

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Completion Notes List

- Added DEFAULT_SORT and SORT_OPTIONS constants
- Implemented sort_leads() dispatcher function with 8 sort options:
  - Default (Urgency) - uses existing sort_by_urgency()
  - Days (Most First) / Days (Least First)
  - Appointment Date (Newest) / Appointment Date (Oldest)
  - Lead Name (A-Z)
  - Stage (A-Z)
  - Locator (A-Z)
- All sorts handle None values (placed at end)
- All string sorts handle "—" placeholder (placed at end)
- Added sort selectbox in filter row (col4)
- Sort state stored in st.session_state.sort_option
- Replaced hardcoded sort_by_urgency with sort_leads in display_dashboard
- Added 18 unit tests for sort_leads function
- All 202 tests pass (no regressions)

### Code Review Fixes

- Consolidated duplicate sort logic (Days/Appointment Date options share implementation)
- Added `_sort_key_string()` helper with tuple-based sorting for robustness
- Defined constants for all sort options (SORT_DAYS_MOST, SORT_NAME_AZ, etc.)
- Renamed `initialize_filter_state()` to `initialize_filter_and_sort_state()`
- Renamed "Clear Filters" button to "Reset All" - now resets both filters AND sort
- Added 2 integration tests (filter+sort, data integrity)
- All 202 tests pass

### Change Log

- 2026-01-08: Created story file, began implementation
- 2026-01-08: Completed implementation, ready for review
- 2026-01-08: Code review fixes applied, story complete

### File List

- src/data_processing.py (modified)
- app.py (modified)
- tests/test_data_processing.py (modified)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified)
