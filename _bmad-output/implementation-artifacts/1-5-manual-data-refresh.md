# Story 1.5: Manual Data Refresh

Status: done

## Story

As **Damione (Coordinator)**,
I want **to manually refresh the data and see when it was last updated**,
So that **I know I'm looking at current information and can get fresh data when needed**.

## Acceptance Criteria

1. **Given** the dashboard is displayed
   **When** looking at the header area
   **Then** a "Last updated: X" timestamp is visible (NFR2)
   **And** a "Refresh" button is visible

2. **Given** I click the Refresh button
   **When** the refresh is in progress
   **Then** a loading spinner displays
   **And** the button is disabled

3. **Given** the refresh completes successfully
   **When** data is updated
   **Then** the table shows new data
   **And** the timestamp updates to "Just now" or current time

## Tasks / Subtasks

- [x] Task 1: Add "Last updated" timestamp display (AC: #1)
  - [x] 1.1: Store last refresh timestamp in `st.session_state`
  - [x] 1.2: Create `format_last_updated()` function for display
  - [x] 1.3: Display timestamp in header area

- [x] Task 2: Add Refresh button (AC: #1, #2)
  - [x] 2.1: Add "Refresh" button to header area
  - [x] 2.2: Implement button click handler to clear cached data
  - [x] 2.3: Show loading spinner during refresh
  - [x] 2.4: Disable button while loading (use st.button disabled state)

- [x] Task 3: Implement refresh logic (AC: #3)
  - [x] 3.1: Clear `st.session_state.leads` on refresh
  - [x] 3.2: Update timestamp after successful refresh
  - [x] 3.3: Trigger re-render to show new data

- [x] Task 4: Write unit tests (AC: #1, #3)
  - [x] 4.1: Test timestamp formatting function
  - [x] 4.2: Test "Just now" display for recent timestamps
  - [x] 4.3: Test relative time display

## Dev Notes

### Architecture Compliance (CRITICAL)

**Files to modify:**
- `app.py` - Add refresh button and timestamp display
- `src/data_processing.py` - Add timestamp formatting function

**Session State Variables:**
- `st.session_state.leads` - Cached lead data (existing)
- `st.session_state.last_refresh` - Timestamp of last data fetch (new)

### Timestamp Display Pattern

**From UX Design - "Last updated" must always be visible (NFR2):**

```python
from datetime import datetime, timezone

def format_last_updated(timestamp: datetime | None) -> str:
    """Format timestamp for display."""
    if timestamp is None:
        return "Never"

    now = datetime.now(timezone.utc)
    diff = now - timestamp

    if diff.total_seconds() < 60:
        return "Just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return timestamp.strftime("%I:%M %p")
```

### Refresh Implementation Pattern

**Streamlit re-run on button click:**
```python
col1, col2 = st.columns([3, 1])
with col1:
    st.caption(f"Last updated: {format_last_updated(st.session_state.get('last_refresh'))}")
with col2:
    if st.button("🔄 Refresh", disabled=st.session_state.get("refreshing", False)):
        # Clear cached data to trigger re-fetch
        st.session_state.pop("leads", None)
        st.session_state.refreshing = True
        st.rerun()
```

### Button Disabled State

**Preventing double-clicks during refresh:**
- Set `st.session_state.refreshing = True` before rerun
- Set `st.session_state.refreshing = False` after data loads
- Button uses `disabled=st.session_state.get("refreshing", False)`

### Previous Story Intelligence

**From Story 1.4:**
- `st.session_state.leads` stores cached lead data
- Data is fetched on first load if not in session state
- `display_dashboard()` handles the main display logic

**Pattern to follow:**
- Check for cached data in session state
- Fetch if missing
- Store timestamp when data is fetched

### Testing Considerations

**Unit testable:**
- `format_last_updated()` timestamp formatting
- Relative time calculations

**Manual testing:**
- Click Refresh button, verify data reloads
- Verify timestamp updates after refresh
- Verify button is disabled during loading

### References

- [Source: architecture.md#Session-Caching] - st.session_state patterns
- [Source: ux-design-specification.md#Trust-Building] - "Last updated" timestamp
- [Source: epics.md#Story-1.5] - Original acceptance criteria

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Added `format_last_updated()` function to `src/data_processing.py`
- Displays "Never", "Just now", "X minute(s) ago", "X hour(s) ago", or date format
- Platform-aware strftime for date format (Unix vs Windows)
- Updated `app.py` with `fetch_and_cache_leads()` and `display_header()` functions
- Refresh button clears cached data and triggers rerun
- Button disabled during refresh to prevent double-clicks
- Last refresh timestamp stored in `st.session_state.last_refresh`
- `st.session_state.refreshing` flag controls button disabled state
- 11 unit tests for `format_last_updated()` function (including edge cases)
- All 3 acceptance criteria satisfied
- 97 tests total (11 new for this story), all passing

### Change Log

- 2026-01-08: Implemented Story 1.5 - Manual Data Refresh
- 2026-01-08: Code review fixes - improved test assertions, added future timestamp edge case test

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
| M1 | Medium | Missing test for future/negative timestamps | Added `test_handles_future_timestamp` test |
| M2 | Medium | Loose test assertions for >24h format | Changed to exact format assertion |
| L1 | Low | Unused pytest import | Not fixed (minor, doesn't affect functionality) |
| L2 | Low | Magic numbers in format_last_updated | Not fixed (well-known values) |
| L3 | Low | Time format uses leading zero for hours | Not fixed (minor style preference) |

### Action Items

- [x] M1: Add test for future timestamp edge case
- [x] M2: Improve >24h format test to verify exact output

