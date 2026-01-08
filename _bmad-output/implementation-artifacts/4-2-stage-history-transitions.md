# Story 4.2: Stage History & Transitions

Status: done

## Story

As **Damione (Coordinator)**,
I want **to view the history of stage transitions with timestamps**,
So that **I can see how the lead has progressed (or stalled) over time**.

## Acceptance Criteria

**Stage History Display:**

1. **Given** I open the detail view for a lead
   **When** I look at the stage history section
   **Then** I see a list of all stage changes in chronological order:
   - Previous stage → New stage
   - Date/time of change

2. **Given** a lead has moved through 4 stages
   **When** viewing history
   **Then** all 4 transitions are shown (e.g., "New → Appt Set → Appt Ack → Green")

3. **Given** a lead has only been in one stage (no transitions)
   **When** viewing history
   **Then** a message shows: "No stage changes recorded" or shows initial stage only

**Timestamp Formatting:**

4. **Given** the stage history is displayed
   **When** I look at each transition
   **Then** the date and time of the change is shown (e.g., "Jan 5, 2026 at 2:30 PM")

5. **Given** a stage change happened today
   **When** displayed
   **Then** it shows "Today at 2:30 PM" or similar relative format

6. **Given** a stage change happened yesterday
   **When** displayed
   **Then** it shows "Yesterday at 10:00 AM" or the full date

7. **And** timestamps are displayed in a consistent format throughout
   **And** timezone is handled appropriately (display in local time)

**Pipeline Context:**

8. **Given** a lead has reached "Green" stage
   **When** viewing the stage history
   **Then** the progression through Green → Delivery pipeline is visible

9. **Given** a lead reaches "Delivered" stage
   **When** viewing the lead
   **Then** it's clear this lead has completed the pipeline successfully

## Tasks / Subtasks

- [x] Task 1: Implement get_stage_history() in zoho_client.py (AC: #1, #2, #3)
  - [x] 1.1: Research Zoho CRM API for stage history endpoint
  - [x] 1.2: Implement get_stage_history(lead_id) function
  - [x] 1.3: Handle empty history (no transitions)
  - [x] 1.4: Add error handling consistent with existing patterns

- [x] Task 2: Add stage history formatting in data_processing.py (AC: #4, #5, #6, #7)
  - [x] 2.1: Create format_stage_timestamp() for relative dates
  - [x] 2.2: Handle "Today at X", "Yesterday at X", full date formats
  - [x] 2.3: Create format_stage_history() to format history list
  - [x] 2.4: Write unit tests for timestamp formatting

- [x] Task 3: Update detail view to display stage history (AC: #1, #8, #9)
  - [x] 3.1: Add stage history section to display_lead_detail()
  - [x] 3.2: Fetch and cache stage history when detail view opens
  - [x] 3.3: Display transitions in chronological order
  - [x] 3.4: Handle "No stage changes recorded" case
  - [x] 3.5: Visual indication for pipeline completion (Delivered)

## Dev Notes

### Architecture Compliance

**Files to modify:**
- `src/zoho_client.py` - Add get_stage_history()
- `src/data_processing.py` - Add timestamp formatting
- `app.py` - Update detail view
- `tests/test_zoho_client.py` - Add tests
- `tests/test_data_processing.py` - Add tests

### Zoho CRM Stage History

Zoho CRM provides stage history via the Timeline API or by accessing the `$field_states` or record history. Key approaches:
1. Timeline API: `/crm/v2/Leads/{id}/__timeline` - Gets field change history
2. Field History: May require specific Zoho edition with audit logs

For MVP, we'll use the Timeline API to fetch stage changes.

### Data Flow

```
User expands lead detail
    ↓
get_stage_history(lead_id) fetches from Zoho
    ↓
format_stage_history() formats timestamps
    ↓
Display in detail view with transitions
```

### Timestamp Formatting Logic

```python
def format_stage_timestamp(dt: datetime) -> str:
    today = datetime.now(timezone.utc).date()
    if dt.date() == today:
        return f"Today at {dt.strftime('%I:%M %p')}"
    elif dt.date() == today - timedelta(days=1):
        return f"Yesterday at {dt.strftime('%I:%M %p')}"
    else:
        return dt.strftime("%b %-d, %Y at %I:%M %p")
```

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Completion Notes List

- Implemented get_stage_history(lead_id) in zoho_client.py using Zoho Timeline API
- Added format_stage_timestamp() for relative timestamps (Today, Yesterday, full date)
- Added format_stage_history() to format transition list for display
- Updated format_leads_for_display() to include lead ID for history fetching
- Created display_stage_history() function in app.py with caching per lead
- Stage history displayed in chronological order (oldest first)
- "No stage changes recorded" message for empty history
- "Delivered" transitions highlighted with success styling
- Pipeline completion celebration with balloons effect
- Added 23 new tests: 6 for format_stage_timestamp, 9 for format_stage_history, 6 for get_stage_history, 2 for format_leads includes ID
- All 240 tests pass (no regressions)

### Change Log

- 2026-01-08: Created story file, began implementation
- 2026-01-08: Completed implementation, ready for review
- 2026-01-08: Code review fixes applied (8 issues), story done

### File List

- src/zoho_client.py (modified) - Added get_stage_history()
- src/data_processing.py (modified) - Added format_stage_timestamp(), format_stage_history(), updated format_leads_for_display()
- app.py (modified) - Added display_stage_history(), updated display_lead_detail()
- tests/test_data_processing.py (modified) - Added tests for stage formatting
- tests/test_zoho_client.py (modified) - Added tests for get_stage_history()
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified)
- _bmad-output/planning-artifacts/epics.md (modified) - Epic 4 consolidation from previous session
