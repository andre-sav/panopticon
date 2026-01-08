---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - product-brief-panopticon-2026-01-07.md
  - prd.md
  - ux-design-specification.md
workflowType: 'architecture'
project_name: 'panopticon'
user_name: 'Andre'
date: '2026-01-07'
status: 'complete'
completedDate: '2026-01-07'
---

# Architecture Decision Document - Panopticon

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements (32 total):**

| Category | Count | Architectural Implication |
|----------|-------|---------------------------|
| Lead Data Display | 5 | Core data model, Zoho field mapping |
| Stale Lead Detection | 5 | Business logic layer, date calculations |
| Calendar & Timeline View | 5 | Date filtering, view components |
| Stage Tracking | 5 | Stage history retrieval from Zoho |
| Filtering & Navigation | 6 | Client-side filtering, Streamlit state |
| Data Integration | 6 | Zoho API client, OAuth, error handling |

**Non-Functional Requirements (11 total):**

| Category | Key Requirements | Architectural Impact |
|----------|------------------|---------------------|
| Data Accuracy | Exact Zoho fidelity, correct calculations | No data transformation that could introduce errors |
| Integration Reliability | Error handling, timeouts, token refresh | Robust API client with retry logic |
| Security | Secrets in Streamlit Cloud, no credential exposure | Environment-based config, no hardcoded secrets |
| Availability | Business hours access, graceful degradation | Error states, partial data handling |

### Scale & Complexity Assessment

| Dimension | Assessment |
|-----------|------------|
| **Complexity Level** | Low |
| **Technical Domain** | Web dashboard with API integration |
| **Users** | Single user (Damione) |
| **Data Sources** | Single (Zoho CRM) |
| **Real-time Requirements** | None (manual refresh) |
| **Compliance Requirements** | None |
| **Estimated Components** | 4-5 (API client, data processor, UI components, config) |

### Technical Constraints & Dependencies

**Framework Constraint:**
- Streamlit (Python) - predetermined, shapes entire architecture
- Streamlit Community Cloud for deployment

**External Dependencies:**
- Zoho CRM API (OAuth 2.0 authentication)
- Zoho API rate limits must be respected

**Environment Constraints:**
- Desktop Chrome only
- Single user, no multi-tenancy
- Internet connectivity required

### Cross-Cutting Concerns

1. **Error Handling:** API failures must show clear messages, never corrupt data display
2. **Token Management:** OAuth refresh must happen automatically without user intervention
3. **Data Freshness:** "Last updated" timestamp must always be visible and accurate
4. **Staleness Calculation:** Days-since-appointment logic must be consistent everywhere

## Starter Template Evaluation

### Primary Technology Domain

**Streamlit (Python) web dashboard** - predetermined in project requirements. This is a read-only data visualization dashboard with single external API integration.

### Starter Options Considered

Unlike React/Next.js ecosystems with complex starter templates (T3 Stack, create-next-app options, etc.), Streamlit projects have a fundamentally simpler initialization pattern:

| Option | Description | Assessment |
|--------|-------------|------------|
| **Vanilla Streamlit** | `pip install streamlit` + manual structure | ✓ Recommended for this scope |
| **Streamlit Templates Gallery** | Pre-built layouts from Streamlit Community | Too generic, adds unnecessary complexity |
| **Custom Cookiecutter** | Template with boilerplate | Overkill for 4-5 component project |

### Selected Approach: Vanilla Streamlit with Modular Structure

**Rationale:**
- Low complexity project (single user, single data source)
- Streamlit handles UI rendering, state management, and deployment
- No benefit from starter templates designed for complex apps
- Simple structure allows clear code organization without framework overhead

**Project Structure:**

```
panopticon/
├── app.py                    # Main Streamlit application entry point
├── requirements.txt          # Python dependencies (pinned versions)
├── .streamlit/
│   ├── secrets.toml          # Local secrets (gitignored)
│   └── config.toml           # Streamlit theming/config (optional)
├── src/
│   ├── __init__.py
│   ├── zoho_client.py        # Zoho CRM API integration (OAuth, requests)
│   ├── data_processing.py    # Business logic (staleness, filtering)
│   └── components.py         # Reusable UI components (optional)
└── .gitignore
```

**Initialization Command:**

```bash
mkdir panopticon && cd panopticon
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install streamlit requests python-dateutil
pip freeze > requirements.txt
```

### Architectural Decisions Provided by This Approach

**Language & Runtime:**
- Python 3.9+ (Streamlit Community Cloud default)
- No TypeScript/JavaScript required
- Standard library for date/time handling

**Styling Solution:**
- Streamlit's built-in theming system
- Minimal custom CSS for traffic-light status colors only
- No external CSS framework needed

**Build Tooling:**
- None required - Streamlit handles everything
- `streamlit run app.py` for local development
- Streamlit Community Cloud for production deployment

**Testing Framework:**
- pytest (to be added as needed)
- No testing infrastructure in initial setup

**Code Organization:**
- `app.py`: Page layout, user interactions, Streamlit components
- `src/zoho_client.py`: API calls, OAuth token management, error handling
- `src/data_processing.py`: Staleness calculations, filtering logic, data transforms

**Development Experience:**
- Hot reload built into Streamlit (automatic on file save)
- No separate dev server configuration
- Streamlit Cloud secrets management for credentials

**Note:** Project initialization should be the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
1. Zoho OAuth token management approach
2. Secrets management strategy

**Important Decisions (Shape Architecture):**
1. Data caching strategy
2. Error handling patterns

**Deferred Decisions (Post-MVP):**
- Database/persistence (not needed - read-only from Zoho)
- Multi-user authentication (single user for MVP)
- Notifications/alerts (future enhancement)

### Data Architecture

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Primary Data Source** | Zoho CRM API | Single source of truth for lead data |
| **Persistence** | None | Read-only dashboard; all data lives in Zoho |
| **Session Caching** | `st.session_state` | Fast access during session, clears on refresh |
| **Data Refresh** | Manual button | User-triggered; avoids rate limits |

**Data Flow:**
```
Zoho CRM API → zoho_client.py → data_processing.py → st.session_state → UI components
```

### Authentication & Security

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **User Authentication** | None | Single-user tool; Streamlit Cloud provides basic access |
| **Zoho API Auth** | OAuth 2.0 with refresh tokens | Industry standard; seamless token refresh |
| **Token Storage** | Streamlit Secrets | Native integration; secure in Cloud deployment |
| **Credential Exposure** | Never in code or logs | NFR9 requirement |

**Token Management Pattern:**
- Store `client_id`, `client_secret`, `refresh_token` in Streamlit Secrets
- `zoho_client.py` handles automatic access token refresh
- Check token validity before each API call
- Refresh transparently without user intervention

### API & Communication Patterns

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **API Client** | Custom `zoho_client.py` | Simple, focused on Zoho CRM endpoints needed |
| **HTTP Library** | `requests` | Standard, well-documented, sufficient for needs |
| **Error Handling** | User-friendly messages | Non-technical user; clear actionable feedback |
| **Rate Limiting** | Respect Zoho limits | Cache data in session to minimize calls |
| **Timeout** | 30 seconds | Fail fast with clear message |

**Error Handling Standards:**
- API failures: `st.error("Unable to connect to Zoho CRM. Please try again.")`
- Auth failures: `st.error("Session expired. Please refresh the page.")`
- Partial data: `st.warning("Some data could not be loaded.")` + show available data
- Always display: "Last updated: {timestamp}"

### Frontend Architecture

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Framework** | Streamlit | Predetermined; handles all UI rendering |
| **State Management** | `st.session_state` | Built-in; sufficient for single-page app |
| **Styling** | Streamlit defaults + minimal CSS | Traffic light colors only |
| **Components** | Native Streamlit | `st.dataframe`, `st.selectbox`, `st.metric` |

**Custom CSS (minimal):**
```css
/* Traffic light status colors */
.stale { background-color: #ffebee; }      /* Red tint */
.at-risk { background-color: #fff3e0; }    /* Amber tint */
.healthy { background-color: #e8f5e9; }    /* Green tint */
```

### Infrastructure & Deployment

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Hosting** | Streamlit Community Cloud | Free, simple, built for Streamlit |
| **Secrets** | Streamlit Cloud Secrets | Native integration; no external vault needed |
| **CI/CD** | GitHub integration | Auto-deploy on push to main |
| **Monitoring** | Streamlit Cloud dashboard | Basic logs and metrics included |
| **Local Dev** | `.streamlit/secrets.toml` | Gitignored; mirrors production secrets structure |

**Environment Configuration:**
- Local: `.streamlit/secrets.toml` (gitignored)
- Production: Streamlit Cloud Secrets dashboard
- Access pattern: `st.secrets["zoho"]["client_id"]`

### Decision Impact Analysis

**Implementation Sequence:**
1. Project initialization (structure, dependencies)
2. Secrets configuration (local `.streamlit/secrets.toml`)
3. Zoho API client with OAuth (`src/zoho_client.py`)
4. Data processing logic (`src/data_processing.py`)
5. Main application UI (`app.py`)
6. Streamlit Cloud deployment

**Cross-Component Dependencies:**
- `app.py` depends on `zoho_client.py` for data
- `zoho_client.py` depends on Streamlit Secrets for credentials
- `data_processing.py` is pure functions, no external dependencies
- All staleness calculations centralized in `data_processing.py`

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** 5 areas where AI agents could make different choices

Given the project's simplicity (Streamlit + Python, single data source), patterns focus on the areas that matter most: naming consistency, date handling, and code organization.

### Naming Patterns

**Python Naming Conventions (PEP 8):**

| Element | Convention | Example |
|---------|------------|---------|
| Files | snake_case | `zoho_client.py`, `data_processing.py` |
| Functions | snake_case | `get_stale_leads()`, `calculate_days_since()` |
| Variables | snake_case | `lead_data`, `appointment_date` |
| Constants | UPPER_SNAKE | `STALE_THRESHOLD_DAYS = 7`, `AT_RISK_THRESHOLD_DAYS = 5` |
| Classes | PascalCase | `ZohoClient` (if used) |

**Zoho Field Mapping:**
- Map Zoho CRM field names to internal names in `zoho_client.py`
- Internal names use snake_case regardless of Zoho's format
- Example: `"Appointment_Date"` → `appointment_date`

### Structure Patterns

**File Organization:**

```
panopticon/
├── app.py                    # UI only - no business logic
├── src/
│   ├── __init__.py
│   ├── zoho_client.py        # API calls only - no UI code
│   └── data_processing.py    # Pure functions - no I/O, no API calls
```

**Import Pattern:**
```python
# In app.py - explicit imports from src/
from src.zoho_client import get_leads, get_stage_history, refresh_token
from src.data_processing import calculate_staleness, filter_leads, sort_by_urgency
```

**Responsibility Boundaries:**

| File | Does | Does NOT |
|------|------|----------|
| `app.py` | Streamlit components, layout, user interaction | API calls, business logic |
| `zoho_client.py` | HTTP requests, OAuth, error handling | UI rendering, staleness logic |
| `data_processing.py` | Calculations, filtering, sorting | API calls, Streamlit components |

### Format Patterns

**Date/Time Handling (Critical for Staleness):**

| Decision | Standard |
|----------|----------|
| **Internal Storage** | Python `datetime` objects in UTC |
| **Timezone** | All calculations in UTC; convert for display |
| **Date Library** | `datetime` (stdlib) + `python-dateutil` for parsing |
| **Staleness Unit** | Calendar days (not hours/minutes) |

**Staleness Calculation (Single Source of Truth):**
```python
# In data_processing.py - THE ONLY place staleness is calculated
from datetime import datetime, timezone

STALE_THRESHOLD_DAYS = 7
AT_RISK_THRESHOLD_DAYS = 5

def calculate_days_since(appointment_date: datetime) -> int:
    """Returns calendar days since appointment. Negative = future."""
    today = datetime.now(timezone.utc).date()
    return (today - appointment_date.date()).days

def get_lead_status(days_since: int) -> str:
    """Returns 'stale', 'at_risk', or 'healthy'."""
    if days_since >= STALE_THRESHOLD_DAYS:
        return "stale"
    elif days_since >= AT_RISK_THRESHOLD_DAYS:
        return "at_risk"
    return "healthy"
```

**Display Formats:**

| Data Type | Display Format | Example |
|-----------|---------------|---------|
| Date | "Mon D, YYYY" | "Jan 7, 2026" |
| Relative time | "X days ago" | "3 days ago" |
| Missing data | Em dash | "—" |
| Phone number | As-is from Zoho | "(555) 123-4567" |

**Null/Missing Data Handling:**
- Zoho returns `null` → Python `None`
- Display `None` as "—" in UI
- Never crash on missing fields

### Communication Patterns

**Zoho API Response Handling:**

```python
# In zoho_client.py
def get_leads() -> list[dict]:
    """Returns list of lead dicts. Empty list on error (not None)."""
    try:
        response = requests.get(...)
        return response.json().get("data", [])
    except Exception as e:
        st.error("Unable to connect to Zoho CRM.")
        return []  # Always return list, never None
```

**Data Shape (dicts, not classes):**
```python
# Lead data structure - consistent everywhere
lead = {
    "id": "12345",
    "name": "John Smith",
    "appointment_date": datetime(...),
    "current_stage": "Appt Set",
    "locator_name": "Marcus Johnson",
    "locator_phone": "(555) 123-4567",
    "locator_email": "marcus@example.com",
    "days_since_appointment": 8,
    "status": "stale"  # "stale", "at_risk", or "healthy"
}
```

### Process Patterns

**Error Handling Standards:**

| Scenario | User Message | Technical Action |
|----------|--------------|------------------|
| API connection failed | "Unable to connect to Zoho CRM. Please check your connection and try again." | Return empty list, log error |
| Auth token expired | "Session expired. Please refresh the page to reconnect." | Attempt token refresh first |
| Partial data failure | "Some leads could not be loaded. Showing available data." | Display what we have |
| No leads found | "No leads with appointments found." | Show empty state, not error |
| Rate limit hit | "Too many requests. Please wait a moment and try again." | Implement backoff |

**Loading State Pattern:**
```python
# In app.py
if "leads" not in st.session_state:
    with st.spinner("Loading leads from Zoho CRM..."):
        st.session_state.leads = get_leads()
        st.session_state.last_refresh = datetime.now()
```

**Refresh Pattern:**
```python
# Manual refresh button
if st.button("🔄 Refresh Data"):
    with st.spinner("Refreshing..."):
        st.session_state.leads = get_leads()
        st.session_state.last_refresh = datetime.now()
    st.rerun()
```

### Enforcement Guidelines

**All AI Agents MUST:**

1. Use `data_processing.py` for ALL staleness calculations - never calculate inline
2. Return empty lists `[]` on API errors, never `None`
3. Display missing data as "—", never as "None" or empty string
4. Use UTC internally, convert only for display
5. Follow the responsibility boundaries (UI in app.py, API in zoho_client.py, logic in data_processing.py)

**Pattern Verification:**
- All date calculations must use `calculate_days_since()` function
- All status determinations must use `get_lead_status()` function
- Constants `STALE_THRESHOLD_DAYS` and `AT_RISK_THRESHOLD_DAYS` defined once in `data_processing.py`

### Pattern Examples

**Good Examples:**
```python
# Correct: Using centralized function
from src.data_processing import calculate_days_since, get_lead_status

days = calculate_days_since(lead["appointment_date"])
status = get_lead_status(days)

# Correct: Empty list on error
def get_leads():
    try:
        ...
    except Exception:
        return []

# Correct: Display missing as dash
locator_phone = lead.get("locator_phone") or "—"
```

**Anti-Patterns:**
```python
# WRONG: Inline staleness calculation
days = (datetime.now() - lead["appointment_date"]).days  # Should use function!

# WRONG: Returning None on error
def get_leads():
    try:
        ...
    except Exception:
        return None  # Should return []

# WRONG: Displaying None
st.write(lead.get("locator_phone"))  # Could display "None"
```

## Project Structure & Boundaries

### Complete Project Directory Structure

```
panopticon/
├── README.md                           # Project overview, setup instructions
├── requirements.txt                    # Python dependencies (pinned versions)
├── .gitignore                          # Git ignore rules
├── .streamlit/
│   ├── secrets.toml                    # Local secrets (GITIGNORED)
│   └── config.toml                     # Streamlit theme/config (optional)
├── app.py                              # Main Streamlit application
└── src/
    ├── __init__.py                     # Package marker
    ├── zoho_client.py                  # Zoho CRM API integration
    ├── data_processing.py              # Business logic & calculations
    └── field_mapping.py                # Zoho field name mappings
```

### File Responsibilities

**`app.py` (Main Application)**
```
Responsibilities:
- Page layout and structure
- Streamlit component rendering
- Filter controls (st.selectbox, st.multiselect)
- Data table display (st.dataframe)
- Metric cards (st.metric)
- Refresh button handling
- Session state management

Handles FRs: FR1-5, FR11-15, FR21-26 (display aspects)
```

**`src/zoho_client.py` (API Integration)**
```
Responsibilities:
- OAuth 2.0 token management
- Access token refresh
- API request execution
- Error handling for API calls
- Rate limit awareness
- Response parsing

Handles FRs: FR27-32 (data integration)
Functions:
- get_access_token() -> str
- refresh_access_token() -> str
- get_leads_with_appointments() -> list[dict]
- get_stage_history(lead_id: str) -> list[dict]
```

**`src/data_processing.py` (Business Logic)**
```
Responsibilities:
- Staleness calculations
- Lead status determination
- Filtering logic
- Sorting logic
- Data transformation

Handles FRs: FR6-10 (stale detection), FR16-20 (stage tracking logic)
Functions:
- calculate_days_since(appointment_date) -> int
- get_lead_status(days_since) -> str
- filter_leads(leads, stage, locator, date_range) -> list
- sort_by_urgency(leads) -> list
- enrich_lead_data(leads) -> list
```

**`src/field_mapping.py` (Zoho Field Mapping)**
```
Responsibilities:
- Map Zoho field names to internal names
- Centralized field configuration
- Handle field name changes in one place

Contents:
- ZOHO_FIELD_MAP = {"Appointment_Date": "appointment_date", ...}
- STAGE_ORDER = ["Appt Set", "Appt Acknowledged", ...]
```

### Architectural Boundaries

**API Boundary:**
```
┌─────────────────────────────────────────────────────────────────┐
│                        app.py (UI Layer)                        │
│  - Never makes direct HTTP calls                                │
│  - Calls zoho_client functions only                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   src/zoho_client.py (API Layer)                │
│  - Only file that imports 'requests'                            │
│  - Only file that reads st.secrets["zoho"]                      │
│  - Returns Python dicts, never raw JSON                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Zoho CRM API                             │
│  - External system, not our control                             │
│  - OAuth 2.0 authentication                                     │
└─────────────────────────────────────────────────────────────────┘
```

**Data Processing Boundary:**
```
┌─────────────────────────────────────────────────────────────────┐
│                        app.py (UI Layer)                        │
│  - Displays processed data                                      │
│  - Passes raw data to processing functions                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               src/data_processing.py (Logic Layer)              │
│  - Pure functions (no I/O, no API, no st.* calls)              │
│  - Testable in isolation                                        │
│  - All staleness logic lives here                               │
└─────────────────────────────────────────────────────────────────┘
```

### Integration Points

**External Integration (Zoho CRM):**

| Integration | Location | Pattern |
|-------------|----------|---------|
| OAuth Token Refresh | `zoho_client.py` | Automatic before API calls |
| Lead Data Fetch | `zoho_client.py` | On-demand via refresh button |
| Stage History Fetch | `zoho_client.py` | On lead detail view |

**Internal Communication:**

| From | To | Data |
|------|-----|------|
| `app.py` | `zoho_client.py` | Request leads/history |
| `zoho_client.py` | `app.py` | List of lead dicts |
| `app.py` | `data_processing.py` | Raw leads for processing |
| `data_processing.py` | `app.py` | Enriched/filtered leads |

### Data Flow

```
User clicks "Refresh"
        │
        ▼
┌───────────────────┐
│      app.py       │  1. Triggers refresh
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  zoho_client.py   │  2. Fetches from Zoho API
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ data_processing.py│  3. Calculates staleness, enriches data
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  st.session_state │  4. Stores processed leads
└───────────────────┘
        │
        ▼
┌───────────────────┐
│      app.py       │  5. Renders table, metrics, filters
└───────────────────┘
```

### Configuration Files

**`.streamlit/secrets.toml` (Local Development):**
```toml
[zoho]
client_id = "your-client-id"
client_secret = "your-client-secret"
refresh_token = "your-refresh-token"
api_domain = "https://www.zohoapis.com"
```

**`.streamlit/config.toml` (Optional Theming):**
```toml
[theme]
primaryColor = "#1976D2"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F5F5"
textColor = "#212121"
```

**`requirements.txt`:**
```
streamlit>=1.28.0
requests>=2.31.0
python-dateutil>=2.8.2
```

**`.gitignore`:**
```
# Secrets (NEVER commit)
.streamlit/secrets.toml

# Python
__pycache__/
*.py[cod]
*$py.class
.env
venv/

# IDE
.vscode/
.idea/
```

### Development Workflow

**Local Development:**
```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure secrets
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
# Edit secrets.toml with actual credentials

# Run
streamlit run app.py
```

**Deployment (Streamlit Cloud):**
1. Push to GitHub (secrets.toml NOT included)
2. Connect repo to Streamlit Cloud
3. Add secrets via Streamlit Cloud dashboard
4. Auto-deploys on push to main

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
All technology choices (Streamlit, Python, requests, python-dateutil) work together natively. No version conflicts. Streamlit Community Cloud supports OAuth 2.0 via Secrets management.

**Pattern Consistency:**
PEP 8 naming conventions throughout. Centralized business logic in `data_processing.py`. Clear responsibility boundaries prevent overlap. Error handling patterns consistent across all components.

**Structure Alignment:**
Project structure directly supports all architectural decisions. Module pattern enables clean imports. Secrets configuration aligns with deployment target.

### Requirements Coverage Validation ✅

**Functional Requirements (32 total):** All covered
- Lead Data Display (FR1-5): `app.py`, `zoho_client.py`
- Stale Lead Detection (FR6-10): `data_processing.py`
- Calendar & Timeline View (FR11-15): `app.py`
- Stage Tracking (FR16-20): `zoho_client.py`, `app.py`
- Filtering & Navigation (FR21-26): `app.py`, `data_processing.py`
- Data Integration (FR27-32): `zoho_client.py`

**Non-Functional Requirements (11 total):** All addressed
- Data accuracy: No-transform data pipeline
- Integration reliability: Error handling, timeouts, token refresh
- Security: Streamlit Secrets, no credential exposure
- Availability: Graceful degradation patterns

### Implementation Readiness Validation ✅

**Decision Completeness:** All critical decisions documented with clear choices
**Structure Completeness:** All files, functions, and responsibilities defined
**Pattern Completeness:** Naming, error handling, and data flow patterns specified with examples

### Gap Analysis Results

**Critical Gaps:** None
**Important Gaps:** None
**Minor Observations:**
- Zoho field names: Will be discovered during API integration (story-level detail)
- Stage order: Will be populated with actual Zoho stage names

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed (Low)
- [x] Technical constraints identified (Streamlit, Zoho API)
- [x] Cross-cutting concerns mapped (error handling, token management)

**✅ Architectural Decisions**
- [x] Critical decisions documented
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed (session caching)

**✅ Implementation Patterns**
- [x] Naming conventions established (PEP 8)
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented (error handling, loading states)

**✅ Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**
- Simple, focused architecture matching low-complexity requirements
- Clear separation of concerns (UI / API / Logic)
- Comprehensive patterns prevent AI agent conflicts
- Direct mapping from FRs to specific files

**Areas for Future Enhancement:**
- Testing infrastructure (pytest) can be added as needed
- Mobile responsive design (post-MVP)
- Notification system (post-MVP)

### Implementation Handoff

**AI Agent Guidelines:**
1. Follow all architectural decisions exactly as documented
2. Use implementation patterns consistently across all components
3. Respect project structure and file responsibility boundaries
4. Refer to this document for all architectural questions
5. Centralize staleness logic in `data_processing.py` - never calculate inline

**First Implementation Priority:**
Project initialization: Create directory structure, `requirements.txt`, `.gitignore`, and secrets template

## Architecture Completion Summary

### Workflow Completion

**Architecture Decision Workflow:** COMPLETED ✅
**Total Steps Completed:** 8
**Date Completed:** 2026-01-07
**Document Location:** `_bmad-output/planning-artifacts/architecture.md`

### Final Architecture Deliverables

**Complete Architecture Document**
- All architectural decisions documented with specific versions
- Implementation patterns ensuring AI agent consistency
- Complete project structure with all files and directories
- Requirements to architecture mapping
- Validation confirming coherence and completeness

**Implementation Ready Foundation**
- 12 architectural decisions made
- 5 implementation pattern categories defined
- 4 architectural components specified (app.py, zoho_client.py, data_processing.py, field_mapping.py)
- 43 requirements fully supported (32 FRs + 11 NFRs)

**AI Agent Implementation Guide**
- Technology stack: Streamlit, Python 3.9+, requests, python-dateutil
- Consistency rules that prevent implementation conflicts
- Project structure with clear boundaries
- Integration patterns and communication standards

### Implementation Handoff

**For AI Agents:**
This architecture document is your complete guide for implementing Panopticon. Follow all decisions, patterns, and structures exactly as documented.

**First Implementation Priority:**
```bash
mkdir panopticon && cd panopticon
python -m venv venv
source venv/bin/activate
pip install streamlit requests python-dateutil
pip freeze > requirements.txt
```

**Development Sequence:**
1. Initialize project using documented structure
2. Set up `.streamlit/secrets.toml` for local development
3. Implement `src/zoho_client.py` (OAuth, API calls)
4. Implement `src/data_processing.py` (staleness logic)
5. Build `app.py` (UI layer)
6. Deploy to Streamlit Community Cloud

### Quality Assurance Checklist

**✅ Architecture Coherence**
- [x] All decisions work together without conflicts
- [x] Technology choices are compatible
- [x] Patterns support the architectural decisions
- [x] Structure aligns with all choices

**✅ Requirements Coverage**
- [x] All 32 functional requirements are supported
- [x] All 11 non-functional requirements are addressed
- [x] Cross-cutting concerns are handled
- [x] Integration points are defined

**✅ Implementation Readiness**
- [x] Decisions are specific and actionable
- [x] Patterns prevent agent conflicts
- [x] Structure is complete and unambiguous
- [x] Examples are provided for clarity

---

**Architecture Status:** READY FOR IMPLEMENTATION ✅

**Next Phase:** Begin implementation using the architectural decisions and patterns documented herein.

**Document Maintenance:** Update this architecture when major technical decisions are made during implementation.
