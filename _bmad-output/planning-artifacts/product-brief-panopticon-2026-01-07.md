---
stepsCompleted: [1, 2, 3, 4, 5, 6]
workflowComplete: true
inputDocuments:
  - DAMIONE_DASHBOARD_PROJECT_SETUP.md
  - ZOHO_API_REFERENCE.md
date: 2026-01-07
author: Andre
---

# Product Brief: Panopticon

## Executive Summary

**Panopticon** is an operational dashboard for lead follow-up accountability at Naturals2Go/VendTech. It gives the Lead Gen Coordinator (Damione Blasdell) real-time visibility into appointed leads that require attention, replacing memory-based tracking with systematic, proactive monitoring.

The dashboard focuses exclusively on leads with scheduled appointments—the "hot leads" in the sales pipeline—and tracks their progression through stage changes. When a lead's appointment date passes without progress, Panopticon surfaces it for intervention, enabling timely locator contact and lead reassignment when necessary.

Built as a custom Streamlit application integrated with Zoho CRM, Panopticon transforms reactive "I noticed it went cold" discovery into proactive "here's what needs attention today" operations.

---

## Core Vision

### Problem Statement

The Lead Gen Coordinator currently tracks lead follow-up status from memory. When locators fail to follow up on appointed leads, this failure goes unnoticed until the lead has already gone cold. There is no systematic way to see which hot leads are stagnating or which locators are falling behind on follow-up responsibilities.

### Problem Impact

- **Lost revenue:** Hot leads with scheduled appointments fall through the cracks
- **Delayed intervention:** Problems discovered reactively rather than proactively
- **Accountability gaps:** No visibility into which locators are following up and which aren't
- **Operational burden:** Coordinator must mentally track dozens of leads across a 30-60 day cycle

### Why Existing Solutions Fall Short

Zoho CRM contains all the necessary data but does not surface it in an operationally useful way. Built-in reporting requires manual effort to configure and check, and doesn't provide the focused, appointment-centric view needed for daily accountability tracking. A custom solution provides the flexibility to show exactly what matters: appointed leads that need attention.

### Proposed Solution

Panopticon is a Streamlit-based dashboard that:

1. **Displays all leads with appointments** - past, present, and future
2. **Tracks stage transitions** - monitors progression after appointment generation
3. **Flags stale leads** - surfaces leads where appointment date passed without stage change
4. **Shows locator ownership** - enables accountability and targeted intervention
5. **Supports quick action** - facilitates locator contact and lead reassignment

### Key Differentiators

- **Appointment-centric focus:** Unlike general CRM dashboards, Panopticon tracks only what matters—leads with appointments
- **Proactive surfacing:** Alerts before leads go cold, not after
- **Operational simplicity:** Single-purpose tool for daily accountability, not a complex reporting platform
- **Locator accountability:** Clear visibility into who owns each stale lead
- **Custom flexibility:** Tailored to exact workflow needs vs. generic CRM reporting

---

## Target Users

### Primary User

**Damione Blasdell** - Lead Gen Coordinator

**Context & Role:**
Damione oversees the lead follow-up process at Naturals2Go/VendTech, ensuring locators follow up on appointed leads and move them through the pipeline to delivery. He works from a desktop at the office and checks lead status once daily as part of his operational routine.

**Current Pain:**
- Tracks dozens of appointed leads from memory
- Discovers stale leads reactively—after they've already gone cold
- No systematic view of which leads need attention or which locators are falling behind
- Manual effort to piece together lead status from Zoho CRM

**Goals & Motivations:**
- Ensure no hot lead falls through the cracks
- Intervene early when locators aren't following up
- Maintain accountability across the locator team
- Spend less mental energy tracking and more time acting

**Success Vision:**
A beautiful visualization of the appointment-to-close pipeline that surfaces leads getting lost in follow-up—before it's too late to save them.

**Daily Workflow with Panopticon:**
1. Opens dashboard once daily (morning routine)
2. Sees at-a-glance which leads need attention
3. Identifies stale leads and their assigned locators
4. Manually intervenes—contacts locator or reassigns lead
5. Moves on with confidence that nothing is slipping through

### Secondary Users

N/A - This is a single-user tool built specifically for the Lead Gen Coordinator role.

### User Journey

| Stage | Experience |
|-------|------------|
| **Discovery** | Internal tool—Damione is the stakeholder who requested it |
| **Onboarding** | Minimal—dashboard is built for his exact workflow |
| **Core Usage** | Daily check: open dashboard → spot stale leads → intervene |
| **Success Moment** | "I can finally see what's falling through the cracks" |
| **Long-term** | Becomes essential part of daily operations; leads stop going cold |

---

## Success Metrics

### Definitions

| Term | Definition |
|------|------------|
| **Converted Lead** | Lead reaches "Green/Delivered" stage |
| **Stale Lead** | 30+ days since appointment with no stage change |
| **Hot Lead** | Lead with scheduled appointment |

### User Success Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Dashboard Accuracy** | All leads with appointments are displayed with correct stage and outcome data | 100% data accuracy |
| **Stale Lead Visibility** | Stale leads (30+ days post-appointment, no progress) are flagged and surfaced | All stale leads visible |
| **Daily Actionability** | Damione can identify which leads need intervention within 5 minutes of opening dashboard | < 5 min to actionable view |

### Business Objectives

| Objective | Description |
|-----------|-------------|
| **Increase Conversion Rate** | More appointed leads reach "Green/Delivered" stage |
| **Reduce Stale Leads** | Fewer leads sitting 30+ days without progress |
| **Improve Locator Accountability** | Locators follow up on assigned appointments consistently |
| **Proactive Intervention** | Problems caught before leads go cold, not after |

### Key Performance Indicators

| KPI | Measurement | Cadence |
|-----|-------------|---------|
| **Conversion Rate** | % of appointed leads reaching Green/Delivered | Weekly/Biweekly |
| **Stale Lead Count** | Number of leads 30+ days post-appointment without stage change | Weekly/Biweekly |
| **Time to Intervention** | Average days between appointment and first intervention (when needed) | Weekly/Biweekly |
| **Pipeline Health** | Distribution of leads across stages (visual trend) | Weekly/Biweekly |

### Baseline & Measurement Plan

No baseline data exists today. Panopticon will establish baseline metrics in its first 2-4 weeks of operation, enabling before/after comparison of:
- Lead conversion rate
- Stale lead count
- Average time leads spend in each stage

---

## MVP Scope

### Core Features

**1. Lead Display with Appointments**
- Show all leads that have/had scheduled appointments
- Display lead name, appointment date/time, current stage, assigned locator
- Pull real-time data from Zoho CRM via API

**2. Appointment Calendar View**
- Visual calendar showing appointments by date
- Today/this week/custom date range views
- Quick identification of upcoming and past appointments

**3. Stage Tracking & History**
- Display current stage for each lead
- Show stage transition history and progression over time
- Track time spent in each stage

**4. Stale Lead Flagging**
- Automatically flag leads 30+ days post-appointment with no stage change
- Visual indicators for leads needing attention
- Sortable/filterable by staleness

**5. Filtering & Sorting**
- Filter by stage (pipeline segment)
- Filter by date range (appointment date)
- Filter by locator (accountability view)

**6. Green → Delivery Tracking**
- Track Green-approved leads through to delivery
- Monitor time from Green stage to Delivery Requested
- Surface leads stuck in Green stages

### Out of Scope for MVP

| Feature | Rationale |
|---------|-----------|
| **Mobile-friendly views** | Desktop-only for MVP; Damione works from office |
| **Export functionality** | Focus on viewing first; export can come later |
| **Alerts/notifications** | Damione checks daily; proactive alerts are future enhancement |
| **In-dashboard lead reassignment** | Actions taken in Zoho CRM; dashboard is read-only |
| **Multi-user support** | Single user (Damione) for MVP |
| **HLM feedback visibility** | Pending clarification with stakeholder |

### MVP Success Criteria

The MVP is successful when:

1. **Data Accuracy** - All appointed leads appear with correct stage and locator data
2. **Stale Lead Visibility** - Damione can immediately see which leads need intervention
3. **Daily Adoption** - Dashboard becomes part of Damione's daily routine
4. **Time Savings** - Identifying problem leads takes minutes, not mental effort
5. **Actionable Insights** - Damione intervenes on leads that would have previously gone cold

### Future Vision

If Panopticon succeeds, it could evolve into:

| Phase | Enhancement |
|-------|-------------|
| **V2: Alerts** | Automated email/Slack notifications when leads go stale |
| **V2: Actions** | Reassign leads or send locator nudges directly from dashboard |
| **V3: Multi-user** | Expand access to other coordinators or managers |
| **V3: Performance** | Locator performance metrics and accountability dashboards |
| **V4: Mobile** | Responsive design for on-the-go pipeline checks |
| **V4: Analytics** | Historical trends, conversion funnels, predictive insights |
