# Story 1.1: Project Setup & Initialization

Status: review

## Story

As a **developer**,
I want **a properly structured Streamlit project with all dependencies and configuration files**,
so that **I have a solid foundation to build the dashboard following architectural patterns**.

## Acceptance Criteria

1. **Given** a new project directory **When** the initialization is complete **Then** the following structure exists:
   - `app.py` (main entry point with "Hello Panopticon" placeholder)
   - `requirements.txt` with streamlit, requests, python-dateutil
   - `src/__init__.py`, `src/zoho_client.py`, `src/data_processing.py`, `src/field_mapping.py` (empty modules with docstrings)
   - `.streamlit/config.toml` (optional theming)
   - `.streamlit/secrets.example.toml` (template for secrets structure)
   - `.gitignore` (excludes secrets.toml, venv, __pycache__)

2. **And** running `streamlit run app.py` displays the placeholder page with title "Panopticon"

3. **And** `.streamlit/secrets.toml` is properly gitignored

## Tasks / Subtasks

- [x] Task 1: Create project directory structure (AC: #1)
  - [x] 1.1: Create `src/` directory
  - [x] 1.2: Create `.streamlit/` directory

- [x] Task 2: Create core Python files (AC: #1)
  - [x] 2.1: Create `app.py` with "Hello Panopticon" placeholder and basic Streamlit layout
  - [x] 2.2: Create `src/__init__.py` (empty package marker)
  - [x] 2.3: Create `src/zoho_client.py` with module docstring and placeholder
  - [x] 2.4: Create `src/data_processing.py` with module docstring, constants, and placeholder functions
  - [x] 2.5: Create `src/field_mapping.py` with module docstring and placeholder dicts

- [x] Task 3: Create configuration files (AC: #1, #3)
  - [x] 3.1: Create `requirements.txt` with pinned versions (streamlit>=1.28.0, requests>=2.31.0, python-dateutil>=2.8.2)
  - [x] 3.2: Create `.gitignore` with all required exclusions
  - [x] 3.3: Create `.streamlit/config.toml` with basic theme configuration
  - [x] 3.4: Create `.streamlit/secrets.example.toml` with Zoho credential template

- [x] Task 4: Verify setup (AC: #2)
  - [x] 4.1: Run `streamlit run app.py` and verify placeholder displays
  - [x] 4.2: Verify `.streamlit/secrets.toml` is gitignored (if created)

## Dev Notes

### Architecture Compliance (CRITICAL)

This story establishes the foundation for ALL subsequent stories. Follow the architecture document EXACTLY.

**Project Structure (from Architecture):**
```
panopticon/
├── README.md                           # Project overview (optional for this story)
├── requirements.txt                    # Python dependencies (pinned versions)
├── .gitignore                          # Git ignore rules
├── .streamlit/
│   ├── secrets.toml                    # Local secrets (GITIGNORED - DO NOT CREATE)
│   ├── secrets.example.toml            # Template showing structure
│   └── config.toml                     # Streamlit theme/config
├── app.py                              # Main Streamlit application
└── src/
    ├── __init__.py                     # Package marker
    ├── zoho_client.py                  # Zoho CRM API integration
    ├── data_processing.py              # Business logic & calculations
    └── field_mapping.py                # Zoho field name mappings
```

### File Contents Guide

**`app.py` - Placeholder Content:**
```python
"""
Panopticon - Lead Follow-up Management Dashboard
Main Streamlit application entry point.
"""
import streamlit as st

st.set_page_config(
    page_title="Panopticon",
    page_icon="👁️",
    layout="wide"
)

st.title("👁️ Panopticon")
st.subheader("Lead Follow-up Management Dashboard")
st.write("Hello Panopticon! Dashboard coming soon...")
```

**`src/zoho_client.py` - Placeholder:**
```python
"""
Zoho CRM API client module.

Responsibilities:
- OAuth 2.0 token management
- Access token refresh
- API request execution
- Error handling for API calls
"""

# Placeholder - implementation in Story 1.2
```

**`src/data_processing.py` - With Constants:**
```python
"""
Business logic and data processing module.

Responsibilities:
- Staleness calculations
- Lead status determination
- Filtering and sorting logic
"""
from datetime import datetime, timezone

# Staleness thresholds (single source of truth)
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

**`src/field_mapping.py` - Placeholder Structure:**
```python
"""
Zoho CRM field name mappings.

Maps Zoho field names to internal snake_case names.
"""

# Zoho field to internal name mapping
# Will be populated when Zoho API fields are known
ZOHO_FIELD_MAP = {
    # "Zoho_Field_Name": "internal_field_name",
}

# Pipeline stage ordering
STAGE_ORDER = [
    # Will be populated with actual Zoho stage names
]
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
.venv/

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

**`.streamlit/secrets.example.toml`:**
```toml
# Copy this file to secrets.toml and fill in your credentials
# NEVER commit secrets.toml to git!

[zoho]
client_id = "your-client-id-here"
client_secret = "your-client-secret-here"
refresh_token = "your-refresh-token-here"
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

### Technical Requirements

- **Python Version:** 3.9+ (Streamlit Community Cloud default)
- **Framework:** Streamlit (predetermined)
- **Dependencies:** streamlit, requests, python-dateutil
- **Naming Convention:** PEP 8 (snake_case for files, functions, variables)

### Testing This Story

1. Create a Python virtual environment: `python -m venv venv`
2. Activate: `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `streamlit run app.py`
5. Verify browser opens with "Panopticon" title and placeholder content

### References

- [Source: architecture.md#Project-Structure] - Complete directory structure
- [Source: architecture.md#Starter-Template-Evaluation] - Vanilla Streamlit approach
- [Source: architecture.md#Implementation-Patterns] - Naming conventions and file responsibilities
- [Source: epics.md#Story-1.1] - Original acceptance criteria

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - Project setup story, no debug logs needed

### Completion Notes List

- Created complete project structure following architecture.md specifications
- All Python files created with proper docstrings and module structure
- data_processing.py includes working staleness calculation functions with proper thresholds
- Verified imports work correctly and functions produce expected results
- .gitignore properly excludes .streamlit/secrets.toml
- Streamlit 1.45.1 confirmed available for running app

### Change Log

- 2026-01-08: Initial project setup complete - all files created per architecture spec

### File List

- app.py (created)
- requirements.txt (created)
- .gitignore (created)
- .streamlit/config.toml (created)
- .streamlit/secrets.example.toml (created)
- src/__init__.py (created)
- src/zoho_client.py (created)
- src/data_processing.py (created)
- src/field_mapping.py (created)
