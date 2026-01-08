# Damione Lead Follow-Up Dashboard - Project Setup
**Created:** 2026-01-07  
**Stakeholder:** Damione Blasdell (Lead Gen Coordinator)  
**Primary User:** Damione Blasdell

---

## 1. Project Overview

### Purpose
Build a **lead follow-up management dashboard** for Damione to monitor appointment pipelines, track stage transitions, and ensure locators are following up on leads.

### Core Problem Statement
> "A lot of our leads are lost in follow-up... it takes 30 to 60 days for them to accept"

Damione needs operational visibility to intervene when locators aren't following up, not historical KPI metrics.

---

## 2. Requirements (from Damione's Transcript)

### Primary Use Cases

#### 1. Appointment Calendar View
> "What I would like to see is... the appointment dates... for that day the appointments that are scheduled"

- Show appointments by date (today, tomorrow, this week)
- Filter by locator
- Flag overdue appointments (appointment date passed but no stage change)

#### 2. Stage Transition Monitoring
> "Would it be possible if a lead is changed from a stage that I can tell that or see that?"

- Track when leads change stages
- Flag leads stuck in the same stage for 30+ days
- Alert on "stale" leads (no activity since appointment)

#### 3. Follow-Up Pipeline
> "A lot of our leads are lost in follow-up... it takes 30 to 60 days for them to accept"

- Show leads in follow-up stages with days since last activity
- Prioritize leads approaching follow-up deadlines
- Track HLM feedback submissions
- **Normal follow-up cycle:** 30-60 days

#### 4. Green → Delivery Tracking
> "To be able to look at it quickly to know... this lead went in and then... if I look back I can know this has delivery tied to this location"

- Show Green-approved leads pending delivery
- Link to actual Deliveries (not just stage)
- Track time from Green to Delivery Request

#### 5. HLM Feedback Visibility
> "To get a visual on what they're inputting... they can manually put in lead thrust follow-up under the HLM feedback tab"

- Show leads sent to call center (HLM Follow up stage)
- Track HLM submissions by locator
- Monitor call center queue

---

## 3. Zoho Fields (Verified)

### Appointment Tracking (from Locatings module)
| Field | API Name (probable) | Purpose |
|-------|---------------------|---------|
| APPT Date | `APPT_Date` | Scheduled appointment date |
| APPT Time | `APPT_Time` | Scheduled appointment time |
| Who is attending Appt | `Who_is_attending_Appt` | "Locator" or other attendee |
| SentEmail APPTDTTM | `SentEmail_APPTDTTM` | When appointment email was sent |
| Acknowledgment APPTDTTM | `Acknowledgment_APPTDTTM` | When appointment was acknowledged |
| ReminderEmail APPTDTTM | `ReminderEmail_APPTDTTM` | When reminder was sent |
| FollowUpEmail APPTDTTM | `FollowUpEmail_APPTDTTM` | When follow-up email was sent |

### Stage & Pipeline
| Field | API Name | Purpose |
|-------|----------|---------|
| Stage | `Stage` | Current pipeline stage |
| Modified_Time | `Modified_Time` | Last modification timestamp |

### Lead Source History
The Locatings module has a **Lead Source History** related list that tracks changes:
- Lead Source value
- Duration (Days)
- Modified Time
- Modified By

**Note:** Stage field may have similar history tracking if configured. Need to verify via API.

### HLM-Related Fields
| Field | API Name | Purpose |
|-------|----------|---------|
| Lead Source | `Lead_Source` | "HLM" indicates call center lead |
| HLM Trigger | `HLM_Trigger` | Workflow trigger field |
| Vanillasoft ID | `Vanillasoft_ID` | Call center system reference |

---

## 4. Stage Values (Pipeline)

```
Lead Entry
    │
    ▼
Appt Not Acknowledged
    │
    ├──► Declined By Operator (rejected)
    │
    ├──► HLM Follow up (sent to call center)
    │
    ▼
Green - Approved By Locator (site survey sent)
    │
    ├──► Green/No-operator (no operator available)
    │
    ├──► Green - LLL Approved (LWP machine relocation)
    │       │
    │       ▼
    │   Green - LLL Fulfilled (LWP complete)
    │
    ▼
Delivery Requested
    │
    ▼
Green/Delivered (machine placed)
```

---

## 5. Technical Architecture

### Stack
```
┌─────────────────────────────────────────┐
│           Frontend (React)               │
│   - Appointment Calendar View            │
│   - Stale Leads Table                    │
│   - Follow-Up Pipeline                   │
│   - Green → Delivery Tracker             │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│           Backend (FastAPI)              │
│   - Zoho API client with OAuth           │
│   - SQLite for caching                   │
│   - Daily sync from Zoho                 │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│             Zoho CRM                     │
│   - Locatings, Deliveries, Notes         │
│   - OAuth 2.0 authentication             │
└─────────────────────────────────────────┘
```

---

## 6. Project File Structure

```
damione-dashboard/
├── backend/
│   ├── main.py             # FastAPI routes
│   ├── services.py         # Business logic
│   ├── zoho_client.py      # Zoho API client
│   ├── sync_service.py     # Zoho → SQLite sync
│   ├── models.py           # SQLAlchemy models
│   ├── database.py         # SQLite setup
│   ├── config.py           # Environment config
│   ├── requirements.txt
│   └── .env                # Zoho credentials
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── appointments.tsx    # Appointment calendar
    │   │   ├── stale-leads.tsx     # Stale lead tracker
    │   │   ├── follow-up.tsx       # Follow-up pipeline
    │   │   └── green-delivery.tsx  # Green → Delivery
    │   ├── components/
    │   └── lib/
    │       └── api.ts
    └── package.json
```

---

## 7. Implementation Plan

### Phase 1: Foundation (Week 1)
1. Set up project structure
2. Implement Zoho OAuth client
3. Verify APPT_Date field API name
4. Create SQLite models for caching

### Phase 2: Core Views (Week 2-3)
1. Appointment Calendar - today/week view
2. Stale Leads Table - leads with no activity in 30+ days
3. Basic filtering by locator

### Phase 3: Pipeline Tracking (Week 3-4)
1. Green → Delivery tracker
2. HLM feedback visibility
3. Stage transition detection (using Modified_Time)

### Phase 4: Alerts & Polish (Week 4+)
1. Follow-up reminders
2. Export functionality
3. Mobile-friendly views

---

## 8. Audit Log Analysis

**From uploaded audit logs (100k+ records):**
- Logs show high-level actions: `updated`, `added`, `MailSent`, `called` (Deluge functions)
- **No field-level change details** visible (e.g., "Stage changed from X to Y")
- Stage transition tracking will need to use:
  1. `Modified_Time` as proxy (when record was last changed)
  2. Field History API (if Stage history is enabled in Zoho)
  3. Custom Zoho workflow to log stage changes to Notes

---

## 9. Open Questions

| # | Question | Status |
|---|----------|--------|
| 1 | What is the exact API name for APPT Date field? | ✅ Field exists (need API name verification) |
| 2 | Is Stage field history enabled in Zoho? | ⚠️ Lead Source History exists; Stage may be similar |
| 3 | What UI section is "HLM feedback tab"? | ⚠️ Appears to be related to HLM Follow up stage workflow |

---

## 10. Stakeholder Contacts

| Role | Name | Email |
|------|------|-------|
| Project Owner | Damione Blasdell | damione.blasdell@naturals2go.com |
| Zoho Admin | Ash Ghanbari | ash.ghanbari@vendtech.com |
| Operations Manager | Melissa Sexton | melissa@vendtech.com |

---

## 11. Reference Documents

- `ZOHO_API_REFERENCE.md` - Comprehensive Zoho CRM API documentation
- Zoho Dashboard Documentation:
  - https://help.zoho.com/portal/en/kb/crm/analytics-and-dashboards/analytics-or-dashboards/overview/articles/create-dashboard
  - https://help.zoho.com/portal/en/kb/crm-nextgen/analytics-and-dashboards/analytics-dashboards/articles/nextgen-analytical-components
  - https://help.zoho.com/portal/en/kb/crm-nextgen/analytics-and-dashboards/analytics-dashboards/articles/nextgen-create-dashboard

---

*End of Project Setup*
