# Story 2.3: At-Risk Lead Detection

Status: done

## Story

As **Damione (Coordinator)**,
I want **to see leads that are approaching the stale threshold (5-6 days)**,
So that **I can proactively intervene before they become stale**.

## Acceptance Criteria

1. **Given** a lead with an appointment 5 or 6 days ago
   **When** status is determined
   **Then** the lead is marked with status "at_risk"

2. **Given** a lead with an appointment 4 days ago
   **When** status is determined
   **Then** the lead is marked as "healthy" (not yet at-risk)

3. **Given** a lead with an appointment 7 days ago
   **When** status is determined
   **Then** the lead is marked as "stale" (not at-risk, already stale)

4. **And** the constant `AT_RISK_THRESHOLD_DAYS = 5` is defined once in data_processing.py

## Tasks / Subtasks

- [x] Task 1: Implement at_risk detection logic (AC: #1, #2, #3, #4)
  - [x] 1.1: Define AT_RISK_THRESHOLD_DAYS = 5 constant
  - [x] 1.2: Update get_lead_status() to return "at_risk" for 5-6 days
  - [x] 1.3: Ensure Status column displays "at_risk"

- [x] Task 2: Write unit tests (AC: #1, #2, #3)
  - [x] 2.1: Test at_risk for 5 days
  - [x] 2.2: Test at_risk for 6 days
  - [x] 2.3: Test healthy for 4 days
  - [x] 2.4: Test stale for 7 days (boundary)

## Dev Notes

### Implementation Note

This story's functionality was implemented across earlier stories:
- `AT_RISK_THRESHOLD_DAYS = 5` constant: Defined in initial architecture setup
- `get_lead_status()` function: Returns "at_risk" for 5-6 days (initial setup)
- Status column integration: Implemented in Story 2.2
- Tests: Added in Story 2.2 (`test_status_at_risk_for_five_days`, etc.)

All acceptance criteria were verified against existing implementation.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- All functionality was already implemented in prior stories
- AC verification confirmed all criteria satisfied
- Tests exist: test_status_at_risk_for_five_days, test_status_not_stale_for_six_days, test_status_healthy_for_four_days
- Constant AT_RISK_THRESHOLD_DAYS = 5 at data_processing.py:16
- No additional code changes required

### Change Log

- 2026-01-08: Story verified complete (functionality from Stories 2.1/2.2)

### File List

- No changes (functionality already exists)

