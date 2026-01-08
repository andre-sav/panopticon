# Story 4.1: Lead Detail View

Status: done

## Story

As **Damione (Coordinator)**,
I want **to click on a lead to see detailed information including current stage status**,
So that **I can understand the full context of a lead before taking action**.

## Acceptance Criteria

**Detail View Display:**

1. **Given** the lead table is displayed
   **When** I click on a lead row (or a "View Details" action)
   **Then** a detail view expands or displays showing:
   - Lead name (header)
   - Appointment date and time
   - Days since appointment
   - Locator name with contact info (phone/email links)

2. **Given** the detail view is open
   **When** I want to close it
   **Then** I can collapse/close the detail view and return to the table

3. **And** the detail view does not navigate away from the main dashboard
   **And** detail information is loaded from cached data (no additional API call)

**Current Stage Display:**

4. **Given** a lead is displayed in the detail view
   **When** I look at the stage section
   **Then** the current stage is prominently displayed
   **And** it's visually emphasized (larger text or highlighted)

5. **Given** the stage value from Zoho is "Appt Not Acknowledged"
   **When** displayed
   **Then** it shows exactly as received from Zoho (no transformation)

**Time in Current Stage:**

6. **Given** a lead's detail view is displayed
   **When** I look at the current stage section
   **Then** I see "In this stage for: X days" (or hours if less than 1 day)

7. **Given** a lead entered current stage 3 days ago
   **When** time is calculated
   **Then** it shows "In this stage for: 3 days"

8. **And** calculation uses the most recent stage change timestamp
   **And** this is calculated in data_processing.py (pure function)

## Tasks / Subtasks

- [x] Task 1: Implement expandable detail view UI (AC: #1, #2, #3)
  - [x] 1.1: Add row selection or expander to lead table
  - [x] 1.2: Create display_lead_detail() function in app.py
  - [x] 1.3: Display lead name, appointment date, days, status
  - [x] 1.4: Display locator contact info with clickable links
  - [x] 1.5: Ensure no additional API calls (use cached data)

- [x] Task 2: Implement current stage display (AC: #4, #5)
  - [x] 2.1: Display current stage prominently in detail view
  - [x] 2.2: Add visual emphasis (styling)
  - [x] 2.3: Ensure stage displayed exactly as from Zoho

- [x] Task 3: Implement time in current stage (AC: #6, #7, #8)
  - [x] 3.1: Create format_time_in_stage() in data_processing.py
  - [x] 3.2: Format as "X days" or "Less than 1 day" based on duration
  - [x] 3.3: Display in detail view below current stage
  - [x] 3.4: Write unit tests for time calculation

## Dev Notes

### Architecture Compliance

**Files to modify:**
- `app.py` - Add detail view UI
- `src/data_processing.py` - Add time in stage calculation
- `tests/test_data_processing.py` - Add tests

### UI Approach

Using Streamlit expander for detail view:
```python
for lead in leads:
    with st.expander(f"{lead['Lead Name']} - {lead['Stage']}"):
        # Detail content here
```

Or using row selection with separate detail panel.

### Data Flow

```
Cached leads from session_state
    ↓
format_leads_for_display() (already done)
    ↓
Display in table with expander/selection
    ↓
On expand: show detail view with calculate_time_in_stage()
```

### Time in Stage Calculation

Note: For Story 4.1, we need stage change timestamp data. Options:
1. Use appointment_date as proxy (simple, available now)
2. Wait for Story 4.2 which fetches actual stage history

For MVP, use appointment_date as the "entered current stage" timestamp.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Completion Notes List

- Replaced dataframe table with expandable lead cards using st.expander
- Each card shows status emoji + lead name + stage in header
- Created display_lead_detail() function for expanded content
- Detail view shows: lead name header, current stage (h3), status, time in stage
- Two-column layout for appointment details and locator contact
- Clickable phone (tel:) and email (mailto:) links in detail view
- Created format_time_in_stage() function in data_processing.py
- Handles: None → "Unknown", 0 → "Less than 1 day", 1 → "1 day", N → "N days"
- Handles negative days for future appointments: -2 → "In 2 days"
- Added get_status_emoji() helper to extract emoji from status values
- Refactored display_lead_cards to use get_status_emoji (DRY)
- Added 8 unit tests for format_time_in_stage() (including negative days)
- Added 9 unit tests for get_status_emoji()
- All 218 tests pass (no regressions)

### Change Log

- 2026-01-08: Created story file, began implementation
- 2026-01-08: Completed implementation, ready for review
- 2026-01-08: Code review fixes applied (5 issues), story done

### File List

- app.py (modified)
- src/data_processing.py (modified)
- tests/test_data_processing.py (modified)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified)
