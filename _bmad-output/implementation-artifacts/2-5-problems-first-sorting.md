# Story 2.5: Problems-First Sorting

Status: done

## Story

As **Damione (Coordinator)**,
I want **stale leads sorted to the top of the table by default**,
So that **the most urgent issues are immediately visible without scrolling**.

## Acceptance Criteria

1. **Given** the dashboard loads with mixed lead statuses
   **When** the default view is displayed
   **Then** leads are sorted by urgency:
   - Stale leads first (sorted by days descending - oldest first)
   - At-risk leads second (sorted by days descending)
   - Healthy leads last

2. **Given** I want to sort by a different criteria
   **When** I use the sort controls (Epic 3)
   **Then** I can override the default sort
   *(Note: Sort controls are Epic 3 scope - this story just implements default)*

3. **And** the `sort_by_urgency()` function in data_processing.py handles this logic

## Tasks / Subtasks

- [x] Task 1: Create sort_by_urgency() function (AC: #1, #3)
  - [x] 1.1: Define status priority order (stale > at_risk > healthy)
  - [x] 1.2: Sort by status priority first, then by days descending within each group
  - [x] 1.3: Handle None days values (sort to end)

- [x] Task 2: Apply default sorting in app.py (AC: #1)
  - [x] 2.1: Call sort_by_urgency() on display_data before rendering
  - [x] 2.2: Ensure sorting happens after format_leads_for_display()

- [x] Task 3: Write unit tests (AC: #1, #3)
  - [x] 3.1: Test stale leads sorted before at_risk
  - [x] 3.2: Test at_risk leads sorted before healthy
  - [x] 3.3: Test within-group sorting by days descending
  - [x] 3.4: Test handling of None/missing days

## Dev Notes

### Sorting Logic

Status priority (highest urgency first):
1. stale (status contains "stale")
2. at_risk (status contains "at_risk")
3. healthy (status contains "healthy" or None)

Within each status group, sort by Days column descending (oldest/highest first).

### Implementation Approach

```python
def sort_by_urgency(leads: list[dict]) -> list[dict]:
    """Sort leads by urgency: stale first, then at_risk, then healthy.

    Within each status group, sorts by days descending (oldest first).
    """
    def sort_key(lead):
        status = lead.get("Status") or ""
        days = lead.get("Days")

        # Status priority: stale=0, at_risk=1, healthy=2
        if "stale" in status:
            priority = 0
        elif "at_risk" in status:
            priority = 1
        else:
            priority = 2

        # Days: higher is more urgent, None goes last
        days_value = days if days is not None else -999

        return (priority, -days_value)  # Negate for descending

    return sorted(leads, key=sort_key)
```

### Display Data Structure

The function operates on formatted display data (after format_leads_for_display):
- "Status": "🔴 stale", "🟡 at_risk", "🟢 healthy", or None
- "Days": int or None

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Completion Notes List

- Added `sort_by_urgency()` function to data_processing.py
- Status priority: stale=0, at_risk=1, healthy/other=2
- Within each group, sorts by days descending (oldest first)
- None days sorted to end using float("inf")
- Updated app.py to call sort_by_urgency() after format_leads_for_display()
- Added 9 unit tests covering all acceptance criteria
- 151 tests total, all passing

### Change Log

- 2026-01-08: Implemented Story 2.5 - Problems-First Sorting

### File List

- src/data_processing.py (modified)
- app.py (modified)
- tests/test_data_processing.py (modified)
