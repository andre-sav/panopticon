---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - prd.md
  - architecture.md
  - ux-design-specification.md
---

# Panopticon - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Panopticon, decomposing the requirements from the PRD, UX Design, and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

**Lead Data Display (FR1-5):**
- FR1: Coordinator can view a list of all leads that have scheduled appointments
- FR2: Coordinator can see lead name, appointment date/time, current stage, and assigned locator for each lead
- FR3: Coordinator can see how many days have passed since each lead's appointment
- FR4: Coordinator can click on a lead to view detailed information
- FR5: Coordinator can see the total count of leads in the current view

**Stale Lead Detection (FR6-10):**
- FR6: System flags leads as "stale" when 7+ days have passed since appointment with no stage change
- FR7: Coordinator can view all stale leads prominently highlighted
- FR8: Coordinator can view "at-risk" leads (5-6 days post-appointment without stage change)
- FR9: Coordinator can see visual distinction between stale, at-risk, and healthy leads
- FR10: Coordinator can sort leads by staleness (days since appointment)

**Calendar & Timeline View (FR11-15):**
- FR11: Coordinator can view appointments on a calendar interface
- FR12: Coordinator can view appointments for today
- FR13: Coordinator can view appointments for the current week
- FR14: Coordinator can select a custom date range to view appointments
- FR15: Coordinator can navigate between different time periods

**Stage Tracking (FR16-20):**
- FR16: Coordinator can see the current stage of each lead
- FR17: Coordinator can view the history of stage transitions for a lead
- FR18: Coordinator can see when each stage change occurred
- FR19: Coordinator can see how long a lead has been in its current stage
- FR20: Coordinator can track leads through the Green -> Delivery pipeline stages

**Filtering & Navigation (FR21-26):**
- FR21: Coordinator can filter leads by current stage
- FR22: Coordinator can filter leads by appointment date range
- FR23: Coordinator can filter leads by assigned locator
- FR24: Coordinator can combine multiple filters simultaneously
- FR25: Coordinator can clear all filters to see full lead list
- FR26: Coordinator can sort leads by different criteria (date, stage, locator, staleness)

**Data Integration (FR27-32):**
- FR27: System retrieves lead data from Zoho CRM via API
- FR28: Coordinator can manually trigger a data refresh
- FR29: System displays timestamp of last data refresh
- FR30: System retrieves appointment data from Zoho CRM
- FR31: System retrieves stage transition history from Zoho CRM
- FR32: System retrieves locator assignment data from Zoho CRM

### NonFunctional Requirements

**Data Accuracy (NFR1-3):**
- NFR1: Data Fidelity - Dashboard displays data exactly as it exists in Zoho CRM
- NFR2: Refresh Transparency - Last refresh timestamp is always visible to user
- NFR3: Stale Calculation - Days-since-appointment calculation is accurate to the calendar day

**Integration Reliability (NFR4-7):**
- NFR4: API Error Handling - If Zoho CRM API is unavailable, display clear error message to user
- NFR5: API Timeout - If API response takes too long, show timeout message rather than hanging
- NFR6: Token Management - OAuth tokens refresh automatically without user intervention
- NFR7: Rate Limit Handling - Respect Zoho API rate limits; queue requests if necessary

**Security (NFR8-9):**
- NFR8: Credential Storage - Zoho API credentials stored in Streamlit Community Cloud secrets (not in code)
- NFR9: No Credential Exposure - API credentials never displayed in UI or logged

**Availability (NFR10-11):**
- NFR10: Business Hours Access - Dashboard accessible during normal business hours
- NFR11: Graceful Degradation - If partial data available, show what's available with warning

### Additional Requirements

**From Architecture - Starter Template & Project Setup:**
- Initialize project with Vanilla Streamlit + modular structure
- Create project structure: app.py, src/zoho_client.py, src/data_processing.py, src/field_mapping.py
- Set up requirements.txt with streamlit, requests, python-dateutil
- Configure .streamlit/secrets.toml for local development
- Set up .gitignore to exclude secrets

**From Architecture - Technical Patterns:**
- Implement OAuth 2.0 with refresh tokens for Zoho API
- Use st.session_state for session caching
- Implement 30-second API timeout
- Follow PEP 8 naming conventions throughout
- Centralize staleness calculation in data_processing.py
- Return empty lists [] on API errors, never None
- Display missing data as "—" in UI

**From UX Design - Visual Requirements:**
- Traffic light color coding (red=stale 7+ days, amber=at-risk 5-6 days, green=healthy)
- Problems-first default sorting (stale leads at top)
- Contact action icons: Phone (tel:) and Email (mailto:) links inline
- Single-page dashboard layout with 4 sections (header, summary metrics, filters, lead table)
- Summary metrics cards showing stale/at-risk/healthy counts
- "Last updated" timestamp prominently displayed
- No pagination - show all leads in scrollable table
- All locator info inline (no click-to-reveal patterns)

**From UX Design - Error Handling:**
- Show "Unable to connect to Zoho CRM" with Retry button on API failure
- Show "Some data may be missing" warning banner for partial data
- Show "All leads healthy - no action needed" when no stale leads
- Show "No leads match your filters" when filters return empty

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR1 | Epic 1 | View list of leads with appointments |
| FR2 | Epic 1 | See lead name, date, stage, locator |
| FR3 | Epic 2 | See days since appointment |
| FR4 | Epic 4 | Click lead for details |
| FR5 | Epic 1 | See total lead count |
| FR6 | Epic 2 | Flag stale leads (7+ days) |
| FR7 | Epic 2 | Highlight stale leads prominently |
| FR8 | Epic 2 | View at-risk leads (5-6 days) |
| FR9 | Epic 2 | Visual distinction stale/at-risk/healthy |
| FR10 | Epic 2 | Sort by staleness |
| FR11 | Epic 5 | View appointments on calendar |
| FR12 | Epic 5 | View today's appointments |
| FR13 | Epic 5 | View this week's appointments |
| FR14 | Epic 5 | Custom date range selection |
| FR15 | Epic 5 | Navigate time periods |
| FR16 | Epic 4 | See current stage |
| FR17 | Epic 4 | View stage transition history |
| FR18 | Epic 4 | See when stage changes occurred |
| FR19 | Epic 4 | See time in current stage |
| FR20 | Epic 4 | Track Green -> Delivery pipeline |
| FR21 | Epic 3 | Filter by stage |
| FR22 | Epic 3 | Filter by date range |
| FR23 | Epic 3 | Filter by locator |
| FR24 | Epic 3 | Combine multiple filters |
| FR25 | Epic 3 | Clear all filters |
| FR26 | Epic 3 | Sort by various criteria |
| FR27 | Epic 1 | Retrieve data from Zoho API |
| FR28 | Epic 1 | Manual data refresh |
| FR29 | Epic 1 | Display last refresh timestamp |
| FR30 | Epic 1 | Retrieve appointment data |
| FR31 | Epic 4 | Retrieve stage history |
| FR32 | Epic 1 | Retrieve locator data |

## Epic List

### Epic 1: Foundation & Lead Dashboard
Damione can open the dashboard and see all leads with appointments, with locator contact info ready for action.

**FRs covered:** FR1, FR2, FR5, FR27, FR28, FR29, FR30, FR32
**NFRs covered:** NFR1, NFR2, NFR4, NFR5, NFR6, NFR7, NFR8, NFR9, NFR10, NFR11
**Additional:** Project setup (Architecture starter), Zoho OAuth, error handling, secrets config, inline phone/email contact icons

### Epic 2: Stale Lead Detection
Damione can instantly identify stale (7+ days) and at-risk (5-6 days) leads through visual color coding, with problems sorted to the top.

**FRs covered:** FR3, FR6, FR7, FR8, FR9, FR10
**NFRs covered:** NFR3 (accurate staleness calculation)
**Additional:** Traffic light colors (red/amber/green), problems-first sorting, summary metrics cards

### Epic 3: Filtering & Sorting
Damione can filter leads by stage, locator, or date range, and sort by various criteria to focus on specific subsets.

**FRs covered:** FR21, FR22, FR23, FR24, FR25, FR26

### Epic 4: Lead Details & Stage History
Damione can click on a lead to see detailed stage progression, when changes occurred, and time spent in each stage.

**FRs covered:** FR4, FR16, FR17, FR18, FR19, FR20, FR31

### Epic 5: Calendar & Timeline View
Damione can view appointments on a calendar interface and navigate by day, week, or custom date range.

**FRs covered:** FR11, FR12, FR13, FR14, FR15

---

## Epic 1: Foundation & Lead Dashboard

Damione can open the dashboard and see all leads with appointments, with locator contact info ready for action.

### Story 1.1: Project Setup & Initialization

As a **developer**,
I want **a properly structured Streamlit project with all dependencies and configuration files**,
So that **I have a solid foundation to build the dashboard following architectural patterns**.

**Acceptance Criteria:**

**Given** a new project directory
**When** the initialization is complete
**Then** the following structure exists:
- `app.py` (main entry point with "Hello Panopticon" placeholder)
- `requirements.txt` with streamlit, requests, python-dateutil
- `src/__init__.py`, `src/zoho_client.py`, `src/data_processing.py`, `src/field_mapping.py` (empty modules)
- `.streamlit/config.toml` (optional theming)
- `.streamlit/secrets.example.toml` (template for secrets)
- `.gitignore` (excludes secrets.toml, venv, __pycache__)

**And** running `streamlit run app.py` displays the placeholder page
**And** `.streamlit/secrets.toml` is gitignored

---

### Story 1.2: Zoho CRM API Connection

As a **developer**,
I want **a Zoho API client that handles OAuth 2.0 authentication with automatic token refresh**,
So that **the dashboard can securely connect to Zoho CRM without manual intervention**.

**Acceptance Criteria:**

**Given** valid Zoho credentials in `.streamlit/secrets.toml`
**When** the zoho_client module is initialized
**Then** it reads client_id, client_secret, and refresh_token from st.secrets

**Given** an expired access token
**When** an API call is attempted
**Then** the client automatically refreshes the access token using the refresh token
**And** retries the original request

**Given** invalid credentials
**When** authentication is attempted
**Then** a clear error message is returned (not an exception crash)
**And** credentials are never logged or displayed

**And** all API requests use a 30-second timeout (NFR5)
**And** the client respects Zoho API rate limits (NFR7)

---

### Story 1.3: Fetch Leads with Appointments

As a **developer**,
I want **to retrieve all leads with scheduled appointments from Zoho CRM**,
So that **the dashboard has the data needed to display the lead list**.

**Acceptance Criteria:**

**Given** a valid Zoho API connection
**When** `get_leads_with_appointments()` is called
**Then** it returns a list of lead dictionaries containing:
- Lead ID
- Lead name
- Appointment date/time
- Current stage
- Locator name
- Locator phone
- Locator email

**Given** Zoho field names differ from internal names
**When** data is fetched
**Then** field_mapping.py maps Zoho fields to snake_case internal names

**Given** an API error occurs
**When** fetching leads
**Then** an empty list is returned (not None)
**And** the error is captured for display (not silently swallowed)

**Given** a lead has missing locator info
**When** data is returned
**Then** missing fields are None (to be displayed as "—" in UI)

---

### Story 1.4: Lead Dashboard Display

As **Damione (Coordinator)**,
I want **to see all leads with appointments in a data table showing key information**,
So that **I can quickly review my pipeline and identify leads needing attention**.

**Acceptance Criteria:**

**Given** the dashboard is opened
**When** data loads successfully
**Then** a data table displays with columns:
- Lead Name
- Appointment Date (formatted as "Jan 7, 2026")
- Current Stage
- Locator Name

**And** the total count of leads is displayed above the table (FR5)
**And** all leads with appointments are shown (no pagination)
**And** data matches exactly what exists in Zoho CRM (NFR1)

**Given** no leads have appointments
**When** the dashboard loads
**Then** a message displays: "No leads with appointments found"

---

### Story 1.5: Manual Data Refresh

As **Damione (Coordinator)**,
I want **to manually refresh the data and see when it was last updated**,
So that **I know I'm looking at current information and can get fresh data when needed**.

**Acceptance Criteria:**

**Given** the dashboard is displayed
**When** looking at the header area
**Then** a "Last updated: X" timestamp is visible (NFR2)
**And** a "Refresh" button is visible

**Given** I click the Refresh button
**When** the refresh is in progress
**Then** a loading spinner displays
**And** the button is disabled

**Given** the refresh completes successfully
**When** data is updated
**Then** the table shows new data
**And** the timestamp updates to "Just now" or current time

---

### Story 1.6: Error Handling & Graceful Degradation

As **Damione (Coordinator)**,
I want **clear error messages when something goes wrong**,
So that **I understand what happened and can take appropriate action**.

**Acceptance Criteria:**

**Given** the Zoho API is unavailable
**When** the dashboard tries to load data
**Then** a clear error message displays: "Unable to connect to Zoho CRM. Please check your connection and try again."
**And** a Retry button is shown (NFR4)

**Given** an API request times out
**When** 30 seconds elapse without response
**Then** a message displays: "Request timed out. Zoho may be slow. Please try again." (NFR5)

**Given** partial data is available
**When** some API calls succeed and others fail
**Then** available data is displayed
**And** a warning banner shows: "Some data may be missing" (NFR11)

**Given** an authentication error occurs
**When** tokens cannot be refreshed
**Then** a message displays: "Session expired. Please refresh the page to reconnect."

---

### Story 1.7: Locator Contact Actions

As **Damione (Coordinator)**,
I want **to see phone and email icons next to each locator that I can click to contact them**,
So that **I can immediately call or email a locator without copying/pasting contact info**.

**Acceptance Criteria:**

**Given** a lead row with locator contact info
**When** viewing the Locator column
**Then** a phone icon is displayed (if phone number exists)
**And** an email icon is displayed (if email exists)
**And** both icons are visible inline (no hover required)

**Given** I click the phone icon
**When** the click is registered
**Then** a `tel:` link opens (triggering phone dialer on desktop)

**Given** I click the email icon
**When** the click is registered
**Then** a `mailto:` link opens (triggering email client)

**Given** a locator has no phone number
**When** viewing the row
**Then** the phone icon is not shown (or shows "—")

---

## Epic 2: Stale Lead Detection

Damione can instantly identify stale (7+ days) and at-risk (5-6 days) leads through visual color coding, with problems sorted to the top.

### Story 2.1: Days Since Appointment Calculation

As **Damione (Coordinator)**,
I want **to see how many days have passed since each lead's appointment**,
So that **I can quickly understand how long a lead has been waiting for follow-up**.

**Acceptance Criteria:**

**Given** a lead with an appointment date
**When** the dashboard displays the lead
**Then** a "Days" column shows the number of calendar days since the appointment

**Given** today is January 8, 2026 and appointment was January 1, 2026
**When** days are calculated
**Then** the value shows "7" (not 6.5 or 168 hours)

**Given** an appointment is in the future
**When** days are calculated
**Then** the value shows a negative number (e.g., "-2" for 2 days from now)

**And** all calculations use the centralized `calculate_days_since()` function in data_processing.py (NFR3)
**And** calculations are accurate to the calendar day, not hours/minutes

---

### Story 2.2: Stale Lead Detection Logic

As **Damione (Coordinator)**,
I want **leads to be flagged as "stale" when 7+ days have passed since their appointment with no stage change**,
So that **I can identify leads that have been sitting too long without progress**.

**Acceptance Criteria:**

**Given** a lead with an appointment 7 or more days ago
**When** the lead has not had a stage change since the appointment
**Then** the lead is marked with status "stale"

**Given** a lead with an appointment 7 or more days ago
**When** the lead HAS had a stage change since the appointment
**Then** the lead is NOT marked as stale (it's progressing)

**Given** a lead with an appointment 6 days ago
**When** status is determined
**Then** the lead is NOT marked as stale (threshold is 7+)

**And** the constant `STALE_THRESHOLD_DAYS = 7` is defined once in data_processing.py
**And** all status determinations use the centralized `get_lead_status()` function

---

### Story 2.3: At-Risk Lead Detection

As **Damione (Coordinator)**,
I want **to see leads that are approaching the stale threshold (5-6 days)**,
So that **I can proactively intervene before they become stale**.

**Acceptance Criteria:**

**Given** a lead with an appointment 5 or 6 days ago
**When** the lead has not had a stage change since the appointment
**Then** the lead is marked with status "at_risk"

**Given** a lead with an appointment 4 days ago
**When** status is determined
**Then** the lead is marked as "healthy" (not yet at-risk)

**Given** a lead with an appointment 7 days ago
**When** status is determined
**Then** the lead is marked as "stale" (not at-risk, already stale)

**And** the constant `AT_RISK_THRESHOLD_DAYS = 5` is defined once in data_processing.py

---

### Story 2.4: Visual Status Indicators

As **Damione (Coordinator)**,
I want **stale leads highlighted in red and at-risk leads in amber**,
So that **I can instantly spot problems by scanning the table visually**.

**Acceptance Criteria:**

**Given** a lead with status "stale"
**When** the table is rendered
**Then** the row has a red background tint (#FF4B4B or similar)
**And** a red status badge/indicator is visible

**Given** a lead with status "at_risk"
**When** the table is rendered
**Then** the row has an amber background tint (#FFA500 or similar)
**And** an amber status badge/indicator is visible

**Given** a lead with status "healthy"
**When** the table is rendered
**Then** the row has no special background color (default white)
**And** a green status badge is visible (or no badge)

**And** status is indicated by BOTH color AND text (not color alone, for accessibility)
**And** red/amber rows are visually prominent; healthy rows recede

---

### Story 2.5: Problems-First Sorting

As **Damione (Coordinator)**,
I want **stale leads sorted to the top of the table by default**,
So that **the most urgent issues are immediately visible without scrolling**.

**Acceptance Criteria:**

**Given** the dashboard loads with mixed lead statuses
**When** the default view is displayed
**Then** leads are sorted by urgency:
1. Stale leads first (sorted by days descending - oldest first)
2. At-risk leads second (sorted by days descending)
3. Healthy leads last

**Given** I want to sort by a different criteria
**When** I use the sort controls (Epic 3)
**Then** I can override the default sort

**And** the `sort_by_urgency()` function in data_processing.py handles this logic

---

### Story 2.6: Summary Metrics Cards

As **Damione (Coordinator)**,
I want **to see counts of stale, at-risk, and healthy leads at the top of the dashboard**,
So that **I instantly know the overall health of my pipeline before looking at details**.

**Acceptance Criteria:**

**Given** the dashboard is displayed
**When** looking at the header/summary area
**Then** three metric cards are visible:
- "Stale" with count and red indicator
- "At Risk" with count and amber indicator
- "Healthy" with count and green indicator

**Given** there are 3 stale, 5 at-risk, and 42 healthy leads
**When** the metrics display
**Then** the cards show "3", "5", and "42" respectively

**Given** there are 0 stale leads
**When** the stale metric displays
**Then** it shows "0" (not hidden)
**And** a positive signal is conveyed (e.g., "All leads healthy" or green checkmark)

**And** metrics update when data is refreshed
**And** metrics reflect current filter state (if filters are applied in Epic 3)

---

## Epic 3: Filtering & Sorting

Damione can filter leads by stage, locator, or date range, and sort by various criteria to focus on specific subsets.

> **Note:** This epic was consolidated from 6 stories to 2 during the Epic 2 retrospective to avoid redundancy. All original acceptance criteria are preserved.

### Story 3.1: Filter Implementation

As **Damione (Coordinator)**,
I want **to filter leads by stage, locator, and date range, with the ability to combine and clear filters**,
So that **I can focus on specific subsets of leads relevant to my current task**.

**Acceptance Criteria:**

**Stage Filter (FR21):**

1. **Given** the filter row is displayed
   **When** I look at the stage filter
   **Then** a dropdown shows "All Stages" plus all available stage options from the data

2. **Given** I select "Appt Set" from the stage filter
   **When** the filter is applied
   **Then** only leads with stage "Appt Set" are shown in the table
   **And** the summary metrics update to reflect the filtered count

3. **Given** I select "All Stages"
   **When** the filter is applied
   **Then** all leads are shown regardless of stage

**Locator Filter (FR23):**

4. **Given** the filter row is displayed
   **When** I look at the locator filter
   **Then** a dropdown shows "All Locators" plus all locator names from the data

5. **Given** I select "Marcus Johnson" from the locator filter
   **When** the filter is applied
   **Then** only leads assigned to Marcus Johnson are shown
   **And** the summary metrics update to reflect the filtered count

6. **Given** I select "All Locators"
   **When** the filter is applied
   **Then** all leads are shown regardless of locator

**Date Range Filter (FR22):**

7. **Given** the filter row is displayed
   **When** I look at the date range filter
   **Then** a dropdown shows preset options:
   - "All Dates"
   - "Today"
   - "This Week"
   - "This Month"
   - "Last 7 Days"
   - "Last 30 Days"

8. **Given** I select "This Week"
   **When** the filter is applied
   **Then** only leads with appointments in the current week are shown

9. **Given** I select "Last 7 Days"
   **When** the filter is applied
   **Then** only leads with appointments in the past 7 days are shown

**Combined Filters (FR24):**

10. **Given** I select "Appt Set" for stage AND "Marcus Johnson" for locator
    **When** both filters are applied
    **Then** only leads that match BOTH criteria are shown (AND logic)
    **And** the summary metrics reflect the combined filter result

11. **Given** I have stage="Appt Set", locator="Marcus", date="This Week"
    **When** all three filters are applied
    **Then** only leads matching ALL three criteria are shown

12. **Given** the combined filters result in zero matches
    **When** the table displays
    **Then** a message shows: "No leads match your filters"
    **And** a "Clear filters" option is visible

**Clear Filters (FR25):**

13. **Given** one or more filters are applied
    **When** I click "Clear all filters" (or similar)
    **Then** all filters reset to their default "All" state
    **And** the full lead list is displayed
    **And** the summary metrics reflect the full data

14. **Given** no filters are applied
    **When** looking at the filter area
    **Then** the "Clear all filters" option is hidden or disabled

**Implementation Notes:**

- Use `st.selectbox()` for stage and locator filters
- Use `st.selectbox()` with preset options for date range filter
- Stage options dynamically populated from data
- Locator names dynamically populated from data
- Locator filter matching is case-insensitive
- Clearing filters is a single action (not one per filter)
- All filters stored in `st.session_state`

---

### Story 3.2: User-Selectable Sorting

As **Damione (Coordinator)**,
I want **to sort leads by different columns**,
So that **I can organize the data in the way that's most useful for my current task**.

**Acceptance Criteria:**

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

**Implementation Notes:**

- Default sort remains `sort_by_urgency()` from Epic 2
- Sort control uses `st.selectbox()` with sort options
- Sort applied after filtering (filter first, then sort)
- Sort preference stored in `st.session_state`

---

## Epic 4: Lead Details & Stage History

Damione can click on a lead to see detailed stage progression, when changes occurred, and time spent in each stage.

### Story 4.1: Lead Detail View

As **Damione (Coordinator)**,
I want **to click on a lead to see more detailed information**,
So that **I can understand the full context of a lead before taking action**.

**Acceptance Criteria:**

**Given** the lead table is displayed
**When** I click on a lead row (or a "View Details" action)
**Then** a detail view expands or displays showing:
- Lead name (header)
- Appointment date and time
- Days since appointment
- Current stage
- Locator name with contact info
- Stage history (from Story 4.3)

**Given** the detail view is open
**When** I want to close it
**Then** I can collapse/close the detail view and return to the table

**And** the detail view does not navigate away from the main dashboard
**And** detail information is loaded from cached data (no additional API call if already fetched)

---

### Story 4.2: Current Stage Display

As **Damione (Coordinator)**,
I want **to see the current stage of each lead clearly displayed**,
So that **I know where each lead is in the pipeline at a glance**.

**Acceptance Criteria:**

**Given** a lead is displayed in the table
**When** I look at the Stage column
**Then** the current stage is displayed (e.g., "Appt Set", "Green", "Delivered")

**Given** a lead is displayed in the detail view
**When** I look at the stage section
**Then** the current stage is prominently displayed
**And** it's visually emphasized (larger text or highlighted)

**Given** the stage value from Zoho is "Appt Not Acknowledged"
**When** displayed
**Then** it shows exactly as received from Zoho (no transformation that could cause confusion)

---

### Story 4.3: Stage Transition History

As **Damione (Coordinator)**,
I want **to view the history of stage transitions for a lead**,
So that **I can see how the lead has progressed (or stalled) over time**.

**Acceptance Criteria:**

**Given** I open the detail view for a lead
**When** I look at the stage history section
**Then** I see a list of all stage changes in chronological order:
- Previous stage -> New stage
- Date/time of change

**Given** a lead has moved through 4 stages
**When** viewing history
**Then** all 4 transitions are shown (e.g., "New -> Appt Set -> Appt Ack -> Green")

**Given** a lead has only been in one stage (no transitions)
**When** viewing history
**Then** a message shows: "No stage changes recorded" or shows initial stage only

**And** stage history is fetched via `get_stage_history()` in zoho_client.py (FR31)

---

### Story 4.4: Stage Change Timestamps

As **Damione (Coordinator)**,
I want **to see when each stage change occurred**,
So that **I can understand the timeline of the lead's progression**.

**Acceptance Criteria:**

**Given** the stage history is displayed
**When** I look at each transition
**Then** the date and time of the change is shown (e.g., "Jan 5, 2026 at 2:30 PM")

**Given** a stage change happened today
**When** displayed
**Then** it shows "Today at 2:30 PM" or similar relative format

**Given** a stage change happened yesterday
**When** displayed
**Then** it shows "Yesterday at 10:00 AM" or the full date

**And** timestamps are displayed in a consistent format throughout
**And** timezone is handled appropriately (display in local time)

---

### Story 4.5: Time in Current Stage

As **Damione (Coordinator)**,
I want **to see how long a lead has been in its current stage**,
So that **I can identify leads that are stuck even if they're not flagged as stale**.

**Acceptance Criteria:**

**Given** a lead's detail view is displayed
**When** I look at the current stage section
**Then** I see "In this stage for: X days" (or hours if less than 1 day)

**Given** a lead entered current stage 3 days ago
**When** time is calculated
**Then** it shows "In this stage for: 3 days"

**Given** a lead entered current stage 2 hours ago
**When** time is calculated
**Then** it shows "In this stage for: 2 hours"

**And** calculation uses the most recent stage change timestamp
**And** this is calculated in data_processing.py (pure function)

---

### Story 4.6: Green to Delivery Pipeline Tracking

As **Damione (Coordinator)**,
I want **to track leads through the Green -> Delivery pipeline stages**,
So that **I can ensure approved leads actually get delivered**.

**Acceptance Criteria:**

**Given** a lead has reached "Green" stage
**When** viewing the lead in the table or detail view
**Then** I can see its current position in the Green -> Delivery pipeline

**Given** I want to see all leads in Green stages
**When** I filter by stage (Epic 3)
**Then** I can filter to "Green", "Green - Pending", "Delivery Requested", "Delivered", etc.

**Given** a lead has been in "Green" for an extended period
**When** viewing the lead
**Then** the time in stage (Story 4.5) helps identify stuck leads

**Given** a lead reaches "Delivered" stage
**When** viewing the lead
**Then** it's clear this lead has completed the pipeline successfully

**And** the stage progression for Green -> Delivery is defined in field_mapping.py

---

## Epic 5: Calendar & Timeline View

Damione can view appointments on a calendar interface and navigate by day, week, or custom date range.

### Story 5.1: Calendar Interface

As **Damione (Coordinator)**,
I want **to view appointments on a calendar interface**,
So that **I can see the temporal distribution of appointments and identify busy/quiet periods**.

**Acceptance Criteria:**

**Given** the dashboard has a calendar view option
**When** I switch to or access the calendar view
**Then** I see a monthly calendar grid showing appointment counts per day

**Given** January 7, 2026 has 5 appointments
**When** looking at that date on the calendar
**Then** the date cell shows "5" or a visual indicator of appointment density

**Given** I click on a date with appointments
**When** the date is selected
**Then** the lead table below/beside filters to show only appointments for that date

**And** the calendar uses Streamlit-compatible components
**And** past dates with appointments are still visible
**And** stale/at-risk indicators are visible on calendar dates (color coding)

---

### Story 5.2: Today's Appointments View

As **Damione (Coordinator)**,
I want **to quickly see all appointments scheduled for today**,
So that **I can focus on what's happening right now**.

**Acceptance Criteria:**

**Given** the calendar or timeline view is displayed
**When** I select "Today" view
**Then** only leads with appointments on today's date are shown

**Given** today is January 8, 2026
**When** "Today" filter is applied
**Then** only leads with appointment date = January 8, 2026 are displayed

**Given** there are no appointments today
**When** "Today" view is selected
**Then** a message shows: "No appointments scheduled for today"

**And** "Today" is a quick-access button or prominent option
**And** the view updates if the dashboard is left open past midnight

---

### Story 5.3: Weekly Appointments View

As **Damione (Coordinator)**,
I want **to view all appointments for the current week**,
So that **I can plan my follow-up activities for the week ahead**.

**Acceptance Criteria:**

**Given** the calendar or timeline view is displayed
**When** I select "This Week" view
**Then** only leads with appointments in the current calendar week are shown

**Given** today is Wednesday, January 8, 2026
**When** "This Week" is selected
**Then** appointments from Monday Jan 6 through Sunday Jan 12 are shown

**Given** viewing the week
**When** looking at the display
**Then** appointments are organized by day or clearly show their date

**And** "This Week" includes both past days (Mon-Tue) and future days (Thu-Sun) of the current week

---

### Story 5.4: Custom Date Range Selection

As **Damione (Coordinator)**,
I want **to select a custom date range to view appointments**,
So that **I can analyze any specific time period I'm interested in**.

**Acceptance Criteria:**

**Given** the timeline/date filter options are displayed
**When** I select "Custom Range"
**Then** date picker controls appear for start date and end date

**Given** I select start = "January 1, 2026" and end = "January 15, 2026"
**When** the custom range is applied
**Then** only leads with appointments between Jan 1-15 (inclusive) are shown

**Given** I select an invalid range (start after end)
**When** attempting to apply
**Then** a validation message shows: "Start date must be before end date"

**Given** I select a range with no appointments
**When** the filter is applied
**Then** a message shows: "No appointments in selected date range"

**And** the date pickers use Streamlit's `st.date_input()` component

---

### Story 5.5: Time Period Navigation

As **Damione (Coordinator)**,
I want **to navigate between different time periods easily**,
So that **I can move forward and backward through the calendar without re-selecting ranges**.

**Acceptance Criteria:**

**Given** I'm viewing "This Week" (Jan 6-12)
**When** I click "Next Week" or a forward arrow
**Then** the view shifts to the next week (Jan 13-19)

**Given** I'm viewing "This Week"
**When** I click "Previous Week" or a back arrow
**Then** the view shifts to the previous week (Dec 30 - Jan 5)

**Given** I'm viewing a specific month on the calendar
**When** I use month navigation
**Then** I can move to previous/next month

**Given** I've navigated away from the current period
**When** I want to return quickly
**Then** a "Today" or "Current Week" button returns me to the present

**And** navigation controls are intuitive (arrows, buttons)
**And** the current viewed period is clearly displayed (e.g., "Week of Jan 6, 2026")
