# Story 2.4: Visual Status Indicators

Status: done

## Story

As **Damione (Coordinator)**,
I want **stale leads highlighted in red and at-risk leads in amber**,
So that **I can instantly spot problems by scanning the table visually**.

## Acceptance Criteria

1. **Given** a lead with status "stale"
   **When** the table is rendered
   **Then** the row has a red background tint
   **And** a red status badge/indicator is visible

2. **Given** a lead with status "at_risk"
   **When** the table is rendered
   **Then** the row has an amber background tint
   **And** an amber status badge/indicator is visible

3. **Given** a lead with status "healthy"
   **When** the table is rendered
   **Then** the row has no special background color (default)
   **And** a green status badge is visible (or no badge)

4. **And** status is indicated by BOTH color AND text (not color alone, for accessibility)

## Tasks / Subtasks

- [x] Task 1: Add status emoji/badge to Status column (AC: #1, #2, #3, #4)
  - [x] 1.1: Create format_status_display() function with emoji prefix
  - [x] 1.2: Update format_leads_for_display to use formatted status
  - [x] 1.3: Stale shows 🔴, at_risk shows 🟡, healthy shows 🟢

- [x] Task 2: Add row background colors using pandas Styler (AC: #1, #2, #3)
  - [x] 2.1: Create style_status_rows() function for row coloring
  - [x] 2.2: Update app.py to apply styling to dataframe
  - [x] 2.3: Stale rows: light red (#ffcccc), at_risk rows: light amber (#fff3cd)

- [x] Task 3: Write unit tests (AC: #1, #2, #3)
  - [x] 3.1: Test format_status_display returns emoji + text (4 tests)
  - [x] 3.2: Test stale, at_risk, healthy formatting (existing tests updated)

## Dev Notes

### Streamlit Row Styling

Streamlit's st.dataframe() supports pandas Styler for row colors:

```python
import pandas as pd

def style_status_rows(row):
    if row["Status"] and "stale" in row["Status"]:
        return ["background-color: #ffcccc"] * len(row)
    elif row["Status"] and "at_risk" in row["Status"]:
        return ["background-color: #fff3cd"] * len(row)
    return [""] * len(row)

df = pd.DataFrame(display_data)
styled_df = df.style.apply(style_status_rows, axis=1)
st.dataframe(styled_df, ...)
```

### Status Display Format

Format status with emoji prefix for accessibility (color + text):
- 🔴 stale
- 🟡 at_risk
- 🟢 healthy

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Added `format_status_display()` function with emoji mapping (🔴 stale, 🟡 at_risk, 🟢 healthy)
- Updated `format_leads_for_display()` to use formatted status with emoji prefix
- Added pandas import to app.py for DataFrame styling
- Added `style_status_rows()` function for row background colors
- Stale rows: light red (#ffcccc), at_risk rows: light amber (#fff3cd)
- Added 4 new tests for format_status_display function
- Updated 8 existing status tests to expect emoji-prefixed format
- All 4 acceptance criteria satisfied (color + text for accessibility)
- 141 tests total (4 new for this story), all passing

### Change Log

- 2026-01-08: Implemented Story 2.4 - Visual Status Indicators

### File List

- src/data_processing.py (modified)
- app.py (modified)
- tests/test_data_processing.py (modified)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified)

## Senior Developer Review

### Review Date
2026-01-08

### Issues Found
- L1: `style_status_rows` defined inside function - acceptable for Streamlit pattern
- L2: No unit test for row styling - acceptable for UI code (integration tested visually)
- L3: Unknown status silently returns without emoji - **FIXED**: Added warning logging

### Fixes Applied
- Added `logging` import and logger to data_processing.py
- Updated `format_status_display()` to log warning for unknown status values
- Added test `test_unknown_status_returns_plain_text_and_logs_warning`

### Final Test Count
142 tests (5 new for this story), all passing

