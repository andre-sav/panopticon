---
stepsCompleted: [1, 2, 3, 4, 7, 8, 9, 10]
inputDocuments:
  - product-brief-panopticon-2026-01-07.md
workflowType: 'prd'
lastStep: 10
documentCounts:
  briefs: 1
  research: 0
  projectDocs: 0
---

# Product Requirements Document - Panopticon

**Author:** Andre
**Date:** 2026-01-07

---

## Executive Summary

**Panopticon** is an operational dashboard for lead follow-up accountability at Naturals2Go/VendTech. Built as a custom Streamlit application integrated with Zoho CRM, it gives the Lead Gen Coordinator (Damione Blasdell) real-time visibility into appointed leads that require attention, replacing memory-based tracking with systematic, proactive monitoring.

The dashboard focuses exclusively on leads with scheduled appointments—the "hot leads" in the sales pipeline—and tracks their progression through stage changes. When a lead's appointment date passes without progress, Panopticon surfaces it for intervention, enabling timely locator contact and lead reassignment when necessary.

**Problem:** The Lead Gen Coordinator currently tracks lead follow-up status from memory. When locators fail to follow up on appointed leads, this failure goes unnoticed until the lead has already gone cold. There is no systematic way to see which hot leads are stagnating or which locators are falling behind on follow-up responsibilities.

**Solution:** A daily-use dashboard that displays all appointed leads, flags stale leads (7+ days without stage change), and shows locator ownership for accountability and targeted intervention.

### What Makes This Special

- **Appointment-centric focus:** Unlike general CRM dashboards, Panopticon tracks only what matters—leads with appointments
- **Proactive surfacing:** Problems identified before leads go cold, not after
- **Operational simplicity:** Single-purpose tool for daily accountability, not a complex reporting platform
- **Locator accountability:** Clear visibility into who owns each stale lead
- **Custom flexibility:** Tailored to exact workflow needs vs. generic CRM reporting

## Project Classification

**Technical Type:** web_app (Streamlit dashboard)
**Domain:** general (business operations/CRM)
**Complexity:** Low
**Project Context:** Greenfield - new project

This is an internal operational tool with a single user (Damione Blasdell). Standard web application patterns apply with Zoho CRM API integration as the primary external dependency. No regulatory compliance requirements. Desktop-only for MVP.

---

## Success Criteria

### User Success

| Criteria | Target | Measurement |
|----------|--------|-------------|
| **Daily Actionability** | < 5 minutes to identify leads needing intervention | Time from dashboard open to action list visible |
| **Stale Lead Visibility** | 100% of stale leads flagged | All leads 7+ days post-appointment without stage change are highlighted |
| **Confidence in Coverage** | Zero leads falling through cracks | Damione can trust that if it's not flagged, it's progressing |

**User Success Moment:** Damione opens the dashboard, immediately sees which leads need attention, identifies the responsible locator, and can take action—all within 5 minutes of his morning routine.

### Business Success

| Criteria | Target | Measurement |
|----------|--------|-------------|
| **Increased Conversion Rate** | Improvement over baseline | % of appointed leads reaching Green/Delivered |
| **Reduced Stale Leads** | Fewer leads sitting idle | Count of leads 7+ days post-appointment without progress |
| **Improved Accountability** | Consistent locator follow-up | Locators acting on assigned appointments |
| **Proactive Intervention** | Problems caught early | Issues identified at 7 days vs. 30+ days |

*No specific numeric targets—baseline will be established in first 2-4 weeks of operation.*

### Technical Success

| Criteria | Target | Measurement |
|----------|--------|-------------|
| **Data Accuracy** | 100% | All leads with appointments appear with correct stage and locator data |
| **Data Freshness** | Current | Zoho CRM data reflects recent updates |
| **Reliability** | Available when needed | Dashboard accessible during business hours |

**Accuracy is paramount.** If data is wrong, trust is lost and the tool becomes useless.

### Measurable Outcomes

**Definitions:**
- **Converted Lead:** Reaches "Green/Delivered" stage
- **Stale Lead:** 7+ days since appointment with no stage change
- **Hot Lead:** Has scheduled appointment

**KPIs (Weekly/Biweekly review):**
- Conversion Rate: % of appointed leads reaching Green/Delivered
- Stale Lead Count: Number of leads flagged as stale
- Time to Intervention: Days between appointment and coordinator action
- Pipeline Health: Distribution of leads across stages

---

## Product Scope

### MVP - Minimum Viable Product

**Core Features:**

1. **Lead Display with Appointments**
   - Show all leads with scheduled appointments
   - Display lead name, appointment date/time, current stage, assigned locator
   - Pull real-time data from Zoho CRM

2. **Appointment Calendar View**
   - Visual calendar showing appointments by date
   - Today/this week/custom date range views

3. **Stage Tracking & History**
   - Display current stage for each lead
   - Show stage transition history and progression
   - Track time spent in each stage

4. **Stale Lead Flagging**
   - Flag leads 7+ days post-appointment with no stage change
   - Visual indicators for leads needing attention
   - Sortable/filterable by staleness

5. **Filtering & Sorting**
   - Filter by stage
   - Filter by date range
   - Filter by locator

6. **Green → Delivery Tracking**
   - Track Green-approved leads through to delivery
   - Surface leads stuck in Green stages

### Growth Features (Post-MVP)

- **Alerts/Notifications:** Email or Slack when leads go stale
- **In-Dashboard Actions:** Reassign leads or send locator nudges
- **Export Functionality:** Download reports for offline review

### Vision (Future)

- **Multi-User Support:** Expand to other coordinators or managers
- **Performance Dashboards:** Locator metrics and accountability trends
- **Mobile Access:** Responsive design for on-the-go checks
- **Predictive Analytics:** Identify at-risk leads before they go stale

---

## User Journeys

### Journey 1: Damione Blasdell - Catching Leads Before They Go Cold

Damione is the Lead Gen Coordinator at Naturals2Go/VendTech, responsible for ensuring locators follow up on appointed leads. For months, he's been tracking lead status from memory—mentally juggling dozens of appointments, trying to remember which locators should have called back, and which leads might be slipping away. When he catches a stale lead, it's usually too late. The prospect has gone cold, the opportunity is lost, and he's left wondering how many others he missed.

One morning, Damione opens Panopticon for the first time. Instead of the usual mental gymnastics, he sees a clean dashboard showing every lead with an appointment. The stale leads—those sitting 7+ days without progress—are flagged in red at the top. He spots three immediately: leads assigned to two different locators who clearly dropped the ball.

He clicks on the first stale lead and sees the full story: appointment was 12 days ago, still sitting in "Appt Not Acknowledged," assigned to Marcus. He picks up the phone, calls Marcus, and learns the locator forgot about this one entirely. Within minutes, Marcus is back on it. Damione moves to the next flagged lead, then the next.

But the real value comes from the "about to go stale" view—leads at 5-6 days post-appointment. These are the ones he never would have caught before. He sees a lead assigned to Jessica that's been sitting for 6 days. A quick call reveals she's been waiting on paperwork. Damione helps unblock her, and the lead moves forward that same day.

Twenty minutes later, Damione closes Panopticon. He's reviewed all the flagged leads, contacted the locators who needed a nudge, and caught two leads that would have gone cold by end of week. For the first time in months, he's confident nothing is slipping through the cracks.

**Damione's Daily Flow:**
1. Opens Panopticon (whenever he wants—he's the boss)
2. Reviews stale leads (7+ days, flagged red) first
3. Checks "about to go stale" leads (5-6 days)
4. Contacts locators who need intervention
5. Closes dashboard confident that nothing is falling through

### Journey Requirements Summary

This journey reveals the following capabilities needed:

| Capability | Requirement |
|------------|-------------|
| **Stale Lead View** | Prominently display leads 7+ days post-appointment without stage change |
| **At-Risk Lead View** | Show leads approaching stale threshold (5-6 days) |
| **Lead Details** | Display appointment date, current stage, days since appointment, assigned locator |
| **Locator Information** | Show who owns each lead for targeted intervention |
| **Stage History** | Show progression (or lack thereof) since appointment |
| **Filtering** | Allow focus on specific stages, date ranges, or locators |
| **Visual Hierarchy** | Stale leads most prominent, at-risk leads secondary |

---

## Web Application Requirements

### Project-Type Overview

Panopticon is a Streamlit-based web dashboard - a Python framework that generates interactive web applications. Streamlit handles the frontend rendering automatically, allowing focus on data logic rather than UI implementation.

**Technology Choice Rationale:**
- Single codebase (Python only)
- Rapid development for data-focused dashboards
- Built-in components for tables, charts, and filters
- Automatic state management

### Technical Architecture Considerations

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Framework** | Streamlit | Python-native, rapid dashboard development |
| **Browser Support** | Chrome only | Damione's primary browser; simplifies testing |
| **Data Refresh** | Manual | User-triggered refresh sufficient for daily use |
| **Hosting** | TBD | Local, cloud, or internal server |
| **Authentication** | TBD | May need basic auth if exposed beyond localhost |

### Browser Requirements

| Requirement | Specification |
|-------------|---------------|
| **Primary Browser** | Google Chrome (latest) |
| **Other Browsers** | Not required for MVP |
| **Mobile Support** | Not required (desktop only) |

### Performance Targets

| Metric | Target |
|--------|--------|
| **Page Load** | No specific requirement |
| **Data Freshness** | Current on manual refresh |
| **Concurrent Users** | 1 (single user tool) |

### Data Integration

| Component | Specification |
|-----------|---------------|
| **Data Source** | Zoho CRM API |
| **Refresh Method** | Manual (user-triggered) |
| **Caching** | Optional - local SQLite cache for performance |
| **Authentication** | Zoho OAuth 2.0 |

### Implementation Considerations

**Streamlit-Specific:**
- Use `st.dataframe()` or `st.table()` for lead display
- Use `st.selectbox()` / `st.multiselect()` for filtering
- Use `st.metric()` for KPI display
- Consider `st.cache_data` for API response caching
- Use Streamlit's built-in session state for filter persistence

**Zoho CRM Integration:**
- OAuth 2.0 authentication flow
- Rate limiting awareness (Zoho API limits)
- Handle token refresh automatically
- Map Zoho fields to dashboard display

**Deployment Options:**
- Streamlit Community Cloud (free, public)
- Internal server (private, controlled access)
- Local machine (simplest, Damione's desktop)

---

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Problem-Solving MVP
Solve the core problem (memory-based lead tracking) with minimal features that deliver immediate value. Damione should be able to open the dashboard and identify stale leads within the first use.

**Resource Requirements:**
- Single developer (Python/Streamlit)
- Zoho CRM API access
- No dedicated infrastructure initially (can run locally)

**Scope Classification:** Simple MVP - single user, focused scope, lean features

### MVP Feature Set (Phase 1)

**Core User Journey Supported:**
- Damione's daily lead review and intervention workflow

**Must-Have Capabilities:**

| # | Feature | Justification |
|---|---------|---------------|
| 1 | Lead Display with Appointments | Core data visibility |
| 2 | Appointment Calendar View | Temporal context for leads |
| 3 | Stage Tracking & History | Progression visibility |
| 4 | Stale Lead Flagging (7+ days) | Primary value proposition |
| 5 | Filtering & Sorting | Actionable data navigation |
| 6 | Green → Delivery Tracking | Complete pipeline visibility |

**MVP Success Gate:** Damione uses the dashboard daily and catches stale leads he would have missed before.

### Post-MVP Features

**Phase 2 (Growth):**
- Alerts/notifications (email or Slack when leads go stale)
- Export functionality (download reports)
- At-risk lead highlighting (5-6 days pre-stale warning)

**Phase 3 (Expansion):**
- In-dashboard actions (reassign leads, send nudges)
- Multi-user support (other coordinators)
- Performance dashboards (locator metrics)
- Mobile access

### Risk Mitigation Strategy

| Risk Type | Risk | Mitigation |
|-----------|------|------------|
| **Technical** | Zoho API rate limits or changes | Cache data locally; design for API resilience |
| **Technical** | Data accuracy issues | Validate data on fetch; show "last updated" timestamp |
| **Market** | Low adoption by Damione | Involve Damione in design; iterate based on feedback |
| **Resource** | Developer availability | Lean scope; single codebase (Streamlit) |

### Scope Boundaries

**In Scope (MVP):**
- Read-only dashboard (no CRM modifications)
- Desktop Chrome browser only
- Single user (Damione)
- Manual data refresh
- Zoho CRM data only

**Explicitly Out of Scope (MVP):**
- Mobile support
- Multi-user authentication
- Automated notifications
- CRM write operations
- Integration with other systems

---

## Functional Requirements

### Lead Data Display

- **FR1:** Coordinator can view a list of all leads that have scheduled appointments
- **FR2:** Coordinator can see lead name, appointment date/time, current stage, and assigned locator for each lead
- **FR3:** Coordinator can see how many days have passed since each lead's appointment
- **FR4:** Coordinator can click on a lead to view detailed information
- **FR5:** Coordinator can see the total count of leads in the current view

### Stale Lead Detection

- **FR6:** System flags leads as "stale" when 7+ days have passed since appointment with no stage change
- **FR7:** Coordinator can view all stale leads prominently highlighted
- **FR8:** Coordinator can view "at-risk" leads (5-6 days post-appointment without stage change)
- **FR9:** Coordinator can see visual distinction between stale, at-risk, and healthy leads
- **FR10:** Coordinator can sort leads by staleness (days since appointment)

### Calendar & Timeline View

- **FR11:** Coordinator can view appointments on a calendar interface
- **FR12:** Coordinator can view appointments for today
- **FR13:** Coordinator can view appointments for the current week
- **FR14:** Coordinator can select a custom date range to view appointments
- **FR15:** Coordinator can navigate between different time periods

### Stage Tracking

- **FR16:** Coordinator can see the current stage of each lead
- **FR17:** Coordinator can view the history of stage transitions for a lead
- **FR18:** Coordinator can see when each stage change occurred
- **FR19:** Coordinator can see how long a lead has been in its current stage
- **FR20:** Coordinator can track leads through the Green → Delivery pipeline stages

### Filtering & Navigation

- **FR21:** Coordinator can filter leads by current stage
- **FR22:** Coordinator can filter leads by appointment date range
- **FR23:** Coordinator can filter leads by assigned locator
- **FR24:** Coordinator can combine multiple filters simultaneously
- **FR25:** Coordinator can clear all filters to see full lead list
- **FR26:** Coordinator can sort leads by different criteria (date, stage, locator, staleness)

### Data Integration

- **FR27:** System retrieves lead data from Zoho CRM via API
- **FR28:** Coordinator can manually trigger a data refresh
- **FR29:** System displays timestamp of last data refresh
- **FR30:** System retrieves appointment data from Zoho CRM
- **FR31:** System retrieves stage transition history from Zoho CRM
- **FR32:** System retrieves locator assignment data from Zoho CRM

---

## Non-Functional Requirements

### Data Accuracy

| Requirement | Specification |
|-------------|---------------|
| **NFR1: Data Fidelity** | Dashboard displays data exactly as it exists in Zoho CRM |
| **NFR2: Refresh Transparency** | Last refresh timestamp is always visible to user |
| **NFR3: Stale Calculation** | Days-since-appointment calculation is accurate to the calendar day |

### Integration Reliability

| Requirement | Specification |
|-------------|---------------|
| **NFR4: API Error Handling** | If Zoho CRM API is unavailable, display clear error message to user |
| **NFR5: API Timeout** | If API response takes too long, show timeout message rather than hanging |
| **NFR6: Token Management** | OAuth tokens refresh automatically without user intervention |
| **NFR7: Rate Limit Handling** | Respect Zoho API rate limits; queue requests if necessary |

### Security

| Requirement | Specification |
|-------------|---------------|
| **NFR8: Credential Storage** | Zoho API credentials stored in Streamlit Community Cloud secrets (not in code) |
| **NFR9: No Credential Exposure** | API credentials never displayed in UI or logged |

### Availability

| Requirement | Specification |
|-------------|---------------|
| **NFR10: Business Hours Access** | Dashboard accessible during normal business hours |
| **NFR11: Graceful Degradation** | If partial data available, show what's available with warning |
