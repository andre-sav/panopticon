---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
workflowComplete: true
lastStep: 14
inputDocuments:
  - product-brief-panopticon-2026-01-07.md
  - prd.md
completedDate: 2026-01-07
---

# UX Design Specification - Panopticon

**Author:** Andre
**Date:** 2026-01-07

---

## Executive Summary

### Project Vision

Panopticon is an operational dashboard that transforms reactive lead management into proactive accountability. Built for speed and simplicity, it gives the Lead Gen Coordinator instant visibility into appointed leads requiring intervention—replacing mental tracking with systematic, visual triage.

The dashboard answers one question every morning: "Which leads need my attention right now?"

### Target Users

**Primary User: Damione Blasdell**
- **Role:** Lead Gen Coordinator at Naturals2Go/VendTech
- **Context:** Desktop at office, once-daily check while rushing between tasks
- **Tech comfort:** Prefers simple, obvious interfaces—no learning curve
- **Information preference:** Dense data visibility; wants everything at once
- **Action pattern:** Identifies problem → calls or emails the responsible locator

**Key User Needs:**
- Instant recognition of which leads are stale or at-risk
- Locator contact info immediately accessible for action
- Zero navigation required to see what matters
- Confidence that nothing is slipping through the cracks

### Key Design Challenges

1. **Speed over polish:** Interface must surface critical info instantly with zero hunting. Damione is rushing—every click costs time.

2. **Dense but scannable:** Everything visible at once, but stale/at-risk leads must visually pop. Density without overwhelm.

3. **Action-ready data:** Path from "see problem" to "contact locator" must be frictionless. Locator info immediately available.

### Design Opportunities

1. **Visual triage system:** Color-coded status (red=stale, yellow=at-risk, green=healthy) enables scanning 50+ leads in seconds.

2. **Morning briefing default:** App opens directly to "what needs attention"—no configuration, no navigation required.

3. **Locator-centric grouping:** Group stale leads by locator to enable batched intervention ("Marcus has 3 stale leads" → one call).

## Core User Experience

### Defining Experience

The core experience of Panopticon is **visual triage**: Damione opens the dashboard and within seconds knows which leads need intervention and who is responsible.

**Core User Action:** Find stale/at-risk leads → identify the responsible locator → take action (call or email)

This single loop defines the product's value. Every design decision must optimize for speed and clarity in this flow.

### Platform Strategy

| Aspect | Decision |
|--------|----------|
| **Platform** | Web application (Streamlit) |
| **Browser** | Desktop Chrome only |
| **Input** | Mouse/keyboard |
| **Connectivity** | Online only; manual refresh |
| **Responsiveness** | Desktop-optimized; no mobile required |

Streamlit provides rapid development for data-focused dashboards with built-in components for tables, filters, and metrics—ideal for this single-user operational tool.

### Effortless Interactions

**Must be effortless (zero thought required):**
- Identifying stale leads (7+ days) — visual color coding, no mental calculation
- Identifying at-risk leads (5-6 days) — distinct warning state
- Finding locator contact info — visible inline, no click-through required
- Understanding lead status — current stage immediately visible

**Should happen automatically:**
- Default view shows "needs attention" leads first
- Staleness calculation (days since appointment)
- Sorting by urgency (most stale first)

### Critical Success Moments

1. **First Glance (0-2 seconds):** Damione opens the app and instantly knows if there are problems today. Red flags visible immediately, or a clear "all healthy" signal.

2. **The "Aha" Moment:** He spots a lead he would have forgotten about. The tool caught it before it went cold—this is when trust is built.

3. **Action Ready:** He sees a stale lead, the locator's name and contact info are right there. No searching, no clicking through—he can pick up the phone immediately.

### Experience Principles

1. **Instant Triage:** Stale and at-risk leads must be visually unmissable within 2 seconds of opening. No hunting, no clicking—problems announce themselves.

2. **Action-Ready Data:** Every problem lead displays everything needed to act (locator name, contact info, lead details). See it → act on it.

3. **Zero Configuration:** The app opens to exactly what Damione needs. No setup, no filters to apply, no navigation to reach value.

4. **Trust Through Completeness:** If it's not flagged, it's fine. The dashboard must show everything so Damione can close it with confidence.

## Desired Emotional Response

### Primary Emotional Goals

**Primary:** Empowered and in control
Damione should feel like he has complete visibility over his pipeline. The dashboard is his command center—problems are visible, actionable, and manageable.

**Secondary:** Confidence that nothing slips through
After closing the dashboard, Damione walks away knowing that if there were problems, he saw them. No nagging worry about forgotten leads.

### Emotional Journey Mapping

| Stage | Desired Feeling | Design Implication |
|-------|-----------------|-------------------|
| **Opens dashboard** | Immediate clarity | No loading confusion; instant data display |
| **Sees stale leads** | Empowered | Clear visual flags; "I caught this" |
| **Takes action** | In control | Locator info visible; frictionless path to act |
| **Closes dashboard** | Confidence | Summary confirmation; "all reviewed" signal |
| **Returns tomorrow** | Trust | Consistent, reliable, accurate every time |

### Micro-Emotions

**Must cultivate:**
- **Confidence:** Interface is instantly understandable—no guessing
- **Trust:** Data is always accurate; what you see is reality
- **Accomplishment:** Clear path from "see problem" to "took action"

**Must avoid:**
- **Confusion:** Unclear status, ambiguous information
- **Skepticism:** Data that seems wrong or outdated
- **Frustration:** Missing info, extra clicks, hunting for details

### Design Implications

| Emotional Goal | UX Design Approach |
|----------------|-------------------|
| Empowered | Dashboard opens to action-ready view; problems front and center |
| In control | All data visible at once; no hidden states or buried info |
| Confident | "Last updated" timestamp visible; data accuracy paramount |
| Trusting | Consistent behavior; same layout every day; no surprises |

### Emotional Design Principles

1. **Clarity builds confidence:** Every element should be immediately understandable. If Damione has to think about what something means, we've failed.

2. **Accuracy builds trust:** Wrong data destroys trust permanently. Better to show "loading" than wrong information.

3. **Completeness builds peace of mind:** Damione must believe the dashboard shows everything. Hidden or filtered data creates anxiety.

4. **Consistency builds habit:** Same layout, same colors, same location of elements. Predictability enables speed.

## UX Pattern Analysis & Inspiration

### Inspiring Products Analysis

| Product Category | Example Products | Key UX Strengths |
|------------------|------------------|------------------|
| **Monitoring Dashboards** | Datadog, Grafana | Color-coded status (red/yellow/green), problems surface immediately, "all healthy" is visually obvious, real-time confidence |
| **Email Triage** | Gmail, Superhuman | Scan-and-act workflow, bold/unread draws attention, keyboard shortcuts for power users, batch operations |
| **CRM List Views** | Zoho, Salesforce | Dense data tables, inline info without click-through, column sorting, saved filters, familiar patterns |

### Transferable UX Patterns

**Visual Status Patterns:**
- **Traffic light system:** Red = stale (7+ days), Yellow = at-risk (5-6 days), Green = healthy. Enables instant visual scanning of 50+ items.
- **Problems-first sorting:** Stale leads appear at top by default, not buried in alphabetical or chronological order.

**Information Density Patterns:**
- **Inline action data:** Locator name and contact info visible directly in the row—no modal, detail page, or hover required.
- **Sticky header with counts:** "3 stale, 5 at-risk, 42 healthy" always visible at top for instant pipeline health.

**Trust-Building Patterns:**
- **"Last updated" timestamp:** Prominently displayed to confirm data freshness. Builds confidence that what you see is current reality.
- **No empty states without explanation:** If no stale leads, show "All leads healthy" rather than empty space.

### Anti-Patterns to Avoid

| Anti-Pattern | Why It's Wrong for Panopticon |
|--------------|-------------------------------|
| **Pagination** | Hides leads on page 2+; Damione needs to see everything at once |
| **Click-to-reveal details** | Adds friction; locator info must be visible inline |
| **Complex filter UI** | Multi-step filtering wastes time; simple dropdowns only |
| **Dashboard with scattered widgets** | Cognitive load; one dense table beats multiple cards |
| **Modal dialogs** | Interrupts scanning flow; keep everything in main view |
| **Loading spinners without data** | Creates anxiety; show cached data while refreshing |

### Design Inspiration Strategy

**Adopt Directly:**
- Traffic light color coding (red/yellow/green status)
- Problems-first default sorting
- Sticky summary header with counts
- "Last updated" timestamp

**Adapt for Simplicity:**
- CRM table patterns simplified (fewer columns, no expandable rows)
- Filtering reduced to essential dropdowns only (stage, locator, date range)

**Avoid Entirely:**
- Pagination (show all leads)
- Click-to-reveal patterns (all data inline)
- Multi-widget dashboard layouts (single table view)
- Complex saved filter systems (overkill for single user)

## Design System Foundation

### Design System Choice

**Streamlit Default + Minimal Custom CSS**

Panopticon will use Streamlit's built-in component library with targeted CSS customizations only where essential for the core experience.

### Rationale for Selection

| Factor | Decision Driver |
|--------|-----------------|
| **Speed** | Single user, internal tool—no need for brand polish |
| **Simplicity** | Damione prefers simple interfaces; Streamlit defaults are clean |
| **Development** | Faster to build; focus effort on data accuracy, not UI polish |
| **Maintenance** | Less custom code = less to maintain |
| **Familiarity** | Streamlit's default look is professional and unobtrusive |

### Implementation Approach

**Use Streamlit Defaults For:**
- Data tables (`st.dataframe()`)
- Filters (`st.selectbox()`, `st.multiselect()`)
- Metrics display (`st.metric()`)
- Layout (`st.columns()`, `st.container()`)
- Buttons (`st.button()`)

**Custom CSS Only For:**
- Row background colors for status (red/yellow/green)
- Status badge styling
- Summary header emphasis

### Customization Strategy

**Color Palette (Status-Driven):**

| Status | Color | Hex | Usage |
|--------|-------|-----|-------|
| Stale (7+ days) | Red | `#FF4B4B` | Row background, status badge |
| At-Risk (5-6 days) | Yellow/Amber | `#FFA500` | Row background, status badge |
| Healthy | Green | `#28A745` | Status badge only (no row highlight) |
| Neutral | Gray | `#6C757D` | Secondary text, timestamps |

**Typography:**
- Use Streamlit defaults (system fonts)
- No custom fonts required

**Spacing:**
- Use Streamlit defaults
- Rely on built-in padding and margins

**Custom Components Needed:**
- None for MVP—Streamlit's built-in components cover all requirements

## Defining Experience Details

### The Core Interaction

**"Open → See red → Call the locator"**

Panopticon's defining experience is instant visual triage. In under 30 seconds, Damione opens the dashboard, spots red-highlighted stale leads, sees the responsible locator's name, and picks up the phone.

This single interaction loop—if executed perfectly—makes everything else work. Every design decision must serve this moment.

### User Mental Model

**Current Approach (Without Panopticon):**
- Tracks lead status from memory
- Discovers problems reactively when leads have already gone cold
- Pieces together status by digging through Zoho CRM manually
- No systematic way to see the full picture

**Expected Experience (With Panopticon):**
- "Show me what's broken" — problems surface automatically
- "Tell me who's responsible" — locator info is immediate
- "Let me close this confident I saw everything" — completeness builds trust

**Mental Model Shift:**
From: "I need to remember to check on leads"
To: "The dashboard tells me what needs attention"

### Success Criteria

| Criteria | Target | Measurement |
|----------|--------|-------------|
| **Time to awareness** | < 2 seconds | From page load to knowing if problems exist |
| **Clicks to locator info** | 0 | Locator name/contact visible inline |
| **Lead visibility** | 100% | All stale leads visible without scrolling or pagination |
| **Confidence on close** | Complete | User trusts that if there were problems, they saw them |

### Experience Mechanics

**Phase 1: Open**
- User navigates to dashboard URL
- Page loads with data already fetched
- Summary counts appear at top: "3 stale, 5 at-risk, 42 healthy"
- "Last updated" timestamp confirms freshness

**Phase 2: Scan**
- Eyes immediately drawn to red rows (stale leads, 7+ days)
- Yellow rows visible for at-risk leads (5-6 days)
- Green/neutral rows recede visually—not distracting
- Problems-first sorting ensures worst cases at top

**Phase 3: Identify**
- Each stale lead row displays:
  - Lead name
  - Appointment date
  - Days since appointment (calculated)
  - Current stage
  - Locator name
  - Locator contact info (phone/email)

**Phase 4: Act**
- Damione calls or emails the locator directly
- Action happens outside the app (phone, email client)
- No in-app action required for MVP

**Phase 5: Done**
- Close browser tab
- Confidence that all problems were surfaced
- Return tomorrow for next check

### Pattern Classification

**Established Patterns Used:**
- Traffic light color coding (monitoring dashboards)
- Dense data tables (CRM interfaces)
- Problems-first sorting (alerting systems)
- Inline data display (email clients)

**No Novel Patterns Required:**
Panopticon uses proven patterns in a focused, single-purpose way. No user education needed—the interface is immediately understandable.

## Visual Design Foundation

### Color System

**Functional, Status-Driven Palette**

No brand colors required. The color system is purely functional—colors communicate lead status, nothing more.

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| **Stale (Critical)** | Red | `#FF4B4B` | Row background for 7+ day leads |
| **At-Risk (Warning)** | Amber | `#FFA500` | Row background for 5-6 day leads |
| **Healthy (OK)** | Green | `#28A745` | Status badge only; no row highlight |
| **Neutral** | Gray | `#6C757D` | Timestamps, secondary text |
| **Background** | White | `#FFFFFF` | Streamlit default |
| **Text** | Dark Gray | `#262730` | Streamlit default |

**Color Principles:**
- Red/amber rows draw the eye instantly—problems announce themselves
- Healthy leads have minimal visual weight—they recede
- No decorative colors; every color has functional meaning

### Typography System

**Streamlit System Fonts**

| Element | Style | Notes |
|---------|-------|-------|
| **Page Title** | Streamlit H1 | "Panopticon" or "Lead Dashboard" |
| **Section Headers** | Streamlit H3 | Summary counts, filter labels |
| **Table Headers** | Streamlit default | Column names |
| **Table Data** | Streamlit default | Lead names, dates, locator info |
| **Timestamps** | Small, gray | "Last updated: 2 min ago" |

**Typography Principles:**
- No custom fonts—faster load, simpler maintenance
- Hierarchy through size and weight, not font variety
- Data readability is paramount

### Spacing & Layout Foundation

**Single-Page, Dense Layout**

| Element | Spacing | Notes |
|---------|---------|-------|
| **Header** | Fixed top | Summary metrics + last updated |
| **Filters** | Below header | Single row of dropdowns |
| **Data Table** | Main content | Full width, scrollable if needed |
| **Margins** | Streamlit default | Standard page padding |

**Layout Principles:**
- Everything visible without scrolling horizontally
- Vertical scroll only for long lead lists
- No sidebar navigation—single view
- Dense but readable; optimize for scanning speed

### Accessibility Considerations

| Consideration | Approach |
|---------------|----------|
| **Color Contrast** | Red/amber on white exceeds WCAG AA (4.5:1) |
| **Color Blindness** | Status also indicated by text badge, not just color |
| **Font Size** | Streamlit defaults are readable; no tiny text |
| **Keyboard Nav** | Not required for MVP (single user, mouse-only confirmed) |

**Accessibility Note:** Since this is a single-user internal tool for a known user (Damione) with no reported vision issues, accessibility is "good enough" rather than WCAG-strict. If deployed more broadly, full accessibility audit would be needed.

## Layout Specification

### Page Structure

**Single-Page Dashboard Layout**

The entire application consists of one view with four stacked sections:

1. **Header Bar** - Title, last updated timestamp, refresh button
2. **Summary Metrics** - Three cards showing stale/at-risk/healthy counts
3. **Filter Row** - Dropdowns for stage, locator, date range
4. **Lead Table** - Full-width data table with all lead information

### Component Specifications

**Summary Metrics Cards:**
- Three `st.metric()` components in a row
- Stale count (red indicator), At-Risk count (amber), Healthy count (green)
- Clicking a card could filter table to that status (optional enhancement)

**Filter Controls:**
- Stage filter: `st.selectbox()` with all pipeline stages
- Locator filter: `st.selectbox()` with all locator names
- Date range filter: `st.selectbox()` with presets (Today, This Week, This Month, Custom)
- All filters in single row using `st.columns()`

**Lead Data Table:**

| Column | Content | Notes |
|--------|---------|-------|
| Status | Color indicator | Red/Amber or blank |
| Lead Name | Full name | Primary identifier |
| Appt Date | Appointment date | MM/DD format |
| Days | Days since appointment | Calculated field |
| Stage | Current pipeline stage | From Zoho |
| Locator | Name + contact icons | Phone/Email clickable |

**Contact Action Icons:**
- Phone icon: `tel:` link for one-click call
- Email icon: `mailto:` link for one-click email
- Both visible inline, no hover required

### Visual Hierarchy

1. **Most prominent:** Red/stale rows (background color)
2. **Secondary:** Amber/at-risk rows (background color)
3. **Tertiary:** Summary counts at top
4. **Recedes:** Healthy leads (no row highlight)

## User Journey Flows

### Primary Journey: Daily Lead Triage

**Goal:** Identify stale leads and contact responsible locators before leads go cold.

**Trigger:** Damione opens the dashboard as part of his morning routine.

**Step-by-Step Breakdown:**

| Step | User Action | System Response | Success Signal |
|------|-------------|-----------------|----------------|
| 1. Open | Navigate to dashboard URL | Load data from Zoho CRM | Summary counts appear |
| 2. Scan | Glance at summary metrics | Display stale/at-risk/healthy counts | Know instantly if problems exist |
| 3. Review | Look at red rows (stale) | Show lead details with locator info | All info visible inline |
| 4. Identify | Find locator for problem lead | Display name + phone + email icons | No searching required |
| 5. Act | Click phone or email icon | Open tel: or mailto: link | Communication app launches |
| 6. Repeat | Check for more stale leads | Table scrolls, filtering available | Process all red rows |
| 7. Preview | Review yellow rows (at-risk) | Show 5-6 day leads | Proactive awareness |
| 8. Close | Close browser tab | N/A | Confidence nothing missed |

### Error Handling Flows

**API Unavailable:**
- Open Dashboard → API Error → Show "Unable to load data" message → Display Retry button → User clicks Retry → Attempt reload

**Partial Data:**
- Open Dashboard → Some data loads → Show available data with warning banner → User sees "Some leads may be missing" → Continue with available data

### Journey Patterns

**Navigation Pattern:**
- Single page, no navigation required
- All actions available from main view
- Filters modify view without page change

**Action Pattern:**
- See problem → Click contact icon → External app handles action
- No in-app confirmation or tracking of contact attempts

**Feedback Pattern:**
- Summary counts = instant health check
- Row colors = immediate status recognition
- Timestamp = data freshness confidence

### Flow Optimization Principles

1. **Minimize steps to value:** Dashboard opens directly to actionable view (no login, no landing page, no configuration)

2. **Reduce decision complexity:** Binary decisions only (call or email, stale or not)

3. **Enable batch processing:** Multiple stale leads visible at once; can contact same locator about multiple leads in one call

4. **Graceful degradation:** If API fails, show clear error rather than confusing partial state

## Component Strategy

### Streamlit Components Used

| Component | Streamlit API | Usage |
|-----------|---------------|-------|
| **Page Title** | `st.title()` | "Panopticon" header |
| **Summary Metrics** | `st.metric()` | Stale/At-Risk/Healthy counts |
| **Filter Dropdowns** | `st.selectbox()` | Stage, Locator, Date Range filters |
| **Data Table** | `st.dataframe()` | Lead list with all columns |
| **Refresh Button** | `st.button()` | Manual data refresh trigger |
| **Timestamp** | `st.caption()` | "Last updated: X min ago" |
| **Layout Columns** | `st.columns()` | Arrange metrics and filters in rows |
| **Containers** | `st.container()` | Group related elements |

### Custom Implementations

**1. Colored Row Backgrounds**

| Requirement | Implementation Approach |
|-------------|------------------------|
| **What** | Red background for stale rows, amber for at-risk |
| **How** | Use `st.dataframe()` with Pandas Styler or custom CSS |
| **Fallback** | If styling limited, add explicit "Status" column with colored badges |

**2. Clickable Contact Links**

| Requirement | Implementation Approach |
|-------------|------------------------|
| **What** | Phone and email icons that open tel:/mailto: links |
| **How** | Render HTML links in dataframe or use `st.markdown()` with HTML |
| **Format** | Phone icon → `tel:+1234567890` / Email icon → `mailto:name@email.com` |

### Component Implementation Strategy

**Approach: Minimal Custom Code**

1. Use Streamlit defaults wherever possible
2. Custom CSS only for row coloring (essential for visual triage)
3. HTML rendering only for contact links (essential for action flow)
4. No custom components or third-party libraries for MVP

**Technical Constraints:**
- Streamlit's `st.dataframe()` has limited styling options
- May need `st.write()` with `unsafe_allow_html=True` for full control
- Test row coloring approach early to confirm feasibility

### Implementation Phases

**Phase 1: Core (MVP)**
- All Streamlit default components
- Basic data table without row coloring
- Contact info as text (not clickable)

**Phase 2: Polish**
- Add row background colors for status
- Add clickable phone/email links
- Refine visual styling with CSS

## UX Consistency Patterns

### Loading State Pattern

**When:** Initial page load, manual refresh, filter change

| Element | Behavior |
|---------|----------|
| **Summary Metrics** | Show spinner or "Loading..." placeholder |
| **Data Table** | Show Streamlit spinner or skeleton |
| **Timestamp** | Show "Updating..." |
| **Duration** | If > 3 seconds, show "Still loading..." message |

### Error State Pattern

**When:** API unavailable, authentication failure, timeout

| Scenario | Message | Action |
|----------|---------|--------|
| **API Down** | "Unable to connect to Zoho CRM" | Show Retry button |
| **Auth Failure** | "Authentication error - please contact admin" | No retry (needs fix) |
| **Timeout** | "Request timed out - Zoho may be slow" | Show Retry button |
| **Partial Failure** | "Some data may be missing" | Show available data + warning banner |

**Visual Treatment:**
- Error messages in red/warning color
- Clear, non-technical language
- Always provide next action (Retry or contact info)

### Empty State Pattern

**When:** No leads match current filters, no stale leads

| Scenario | Message | Visual |
|----------|---------|--------|
| **No stale leads** | "All leads healthy - no action needed" | Green checkmark, positive tone |
| **No leads match filter** | "No leads match your filters" | Neutral, show "Clear filters" link |
| **No leads at all** | "No appointed leads found" | Neutral, suggest checking Zoho |

**Design Principle:** Empty states should be informative, not just blank space.

### Filter Behavior Pattern

**Interaction Rules:**

| Behavior | Implementation |
|----------|----------------|
| **Default state** | All filters set to "All" (no filtering) |
| **Filter change** | Immediate table update (no Apply button) |
| **Multiple filters** | AND logic (stage=X AND locator=Y) |
| **Clear filters** | Single "Clear all" link resets to defaults |
| **Persistence** | Filters reset on page refresh (no URL state) |

**Filter Options:**

| Filter | Options |
|--------|---------|
| **Stage** | All, Appt Set, Appt Ack, Green, Delivered, etc. |
| **Locator** | All, [List of locator names from data] |
| **Date Range** | All, Today, This Week, This Month, Custom |

### Refresh Pattern

**Manual Refresh Behavior:**

| Element | Behavior |
|---------|----------|
| **Button** | "Refresh" button in header area |
| **During refresh** | Button shows spinner, disabled state |
| **After refresh** | Timestamp updates to "Just now" |
| **On error** | Show error message, button re-enabled |

**No Auto-Refresh:** Dashboard is checked once daily; auto-refresh adds complexity without value.

## Responsive Design & Accessibility

### Responsive Strategy

**Desktop-Only Design**

Panopticon is designed exclusively for desktop Chrome browser. No responsive breakpoints or mobile layouts are required for MVP.

| Aspect | Decision |
|--------|----------|
| **Target Device** | Desktop (1024px+ width) |
| **Browser** | Chrome only |
| **Mobile Support** | Not required |
| **Tablet Support** | Not required |

**Rationale:** Single user (Damione) accesses from office desktop only. Mobile/tablet support would add development complexity without user value.

**Future Consideration:** If expanded to multiple users or remote access, responsive design would be Phase 3+ enhancement.

### Accessibility Strategy

**Minimal Accessibility (Single Known User)**

| Requirement | Approach |
|-------------|----------|
| **WCAG Compliance** | Not targeted for MVP |
| **Color Contrast** | Meets basic contrast (Streamlit defaults) |
| **Keyboard Navigation** | Not required (mouse user confirmed) |
| **Screen Reader** | Not required |

**Rationale:** Damione is the sole user with no reported vision, motor, or cognitive accessibility needs. Building for broader accessibility would be premature optimization.

**Built-in Accessibility:**
- Streamlit provides reasonable default contrast
- Status indicated by color AND text (not color alone)
- Clear, readable typography from Streamlit defaults

**Future Consideration:** If deployed to additional users, conduct accessibility audit and implement WCAG AA compliance.

### Testing Strategy

**MVP Testing:**
- Manual testing in Chrome desktop only
- Verify data accuracy from Zoho
- Test error states and edge cases
- User acceptance testing with Damione

**No Device/Accessibility Testing Required:** Single user, single browser, known environment.
