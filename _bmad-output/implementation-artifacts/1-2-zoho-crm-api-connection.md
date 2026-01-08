# Story 1.2: Zoho CRM API Connection

Status: done

## Story

As a **developer**,
I want **a Zoho API client that handles OAuth 2.0 authentication with automatic token refresh**,
so that **the dashboard can securely connect to Zoho CRM without manual intervention**.

## Acceptance Criteria

1. **Given** valid Zoho credentials in `.streamlit/secrets.toml`
   **When** the zoho_client module is initialized
   **Then** it reads client_id, client_secret, and refresh_token from st.secrets

2. **Given** an expired access token
   **When** an API call is attempted
   **Then** the client automatically refreshes the access token using the refresh token
   **And** retries the original request

3. **Given** invalid credentials
   **When** authentication is attempted
   **Then** a clear error message is returned (not an exception crash)
   **And** credentials are never logged or displayed

4. **And** all API requests use a 30-second timeout (NFR5)

5. **And** the client respects Zoho API rate limits (NFR7)

## Tasks / Subtasks

- [x] Task 1: Create OAuth token management (AC: #1, #2)
  - [x] 1.1: Implement `get_access_token()` that reads refresh_token from st.secrets
  - [x] 1.2: Implement `refresh_access_token()` to exchange refresh token for access token
  - [x] 1.3: Store access token in `st.session_state` for reuse during session
  - [x] 1.4: Implement token expiry checking before API calls

- [x] Task 2: Create API request wrapper (AC: #3, #4, #5)
  - [x] 2.1: Implement `_make_request()` internal method with 30-second timeout
  - [x] 2.2: Add automatic token refresh on 401 responses
  - [x] 2.3: Implement rate limit handling (retry with backoff on 429)
  - [x] 2.4: Return empty list [] on errors, never None

- [x] Task 3: Implement error handling (AC: #3)
  - [x] 3.1: Create user-friendly error messages for common failures
  - [x] 3.2: Ensure credentials are NEVER logged or displayed in errors
  - [x] 3.3: Store last error in session state for UI display

- [x] Task 4: Create basic test endpoint (AC: #1, #2, #3)
  - [x] 4.1: Implement `test_connection()` function to verify credentials work
  - [x] 4.2: Write unit tests for token refresh logic (mock API responses)

## Dev Notes

### Architecture Compliance (CRITICAL)

**File:** `src/zoho_client.py` - This is the ONLY file that should:
- Import `requests` library
- Read `st.secrets["zoho"]` credentials
- Make HTTP calls to Zoho API

**Responsibility Boundaries (from architecture.md):**
- `zoho_client.py`: HTTP requests, OAuth, error handling
- Does NOT: UI rendering, staleness logic, Streamlit components

### Zoho OAuth 2.0 Flow

**Token Refresh Endpoint:**
```
POST https://accounts.zoho.com/oauth/v2/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
client_id={client_id}
client_secret={client_secret}
refresh_token={refresh_token}
```

**Response:**
```json
{
  "access_token": "1000.xxxx.xxxx",
  "api_domain": "https://www.zohoapis.com",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Implementation Pattern

**Token Storage Pattern (from architecture.md):**
```python
# Store access token in session state for reuse
if "zoho_access_token" not in st.session_state:
    st.session_state.zoho_access_token = None
    st.session_state.zoho_token_expiry = None
```

**Error Handling Standards (from architecture.md):**

| Scenario | User Message | Technical Action |
|----------|--------------|------------------|
| API connection failed | "Unable to connect to Zoho CRM. Please check your connection and try again." | Return empty list, log error |
| Auth token expired | "Session expired. Please refresh the page to reconnect." | Attempt token refresh first |
| Rate limit hit | "Too many requests. Please wait a moment and try again." | Implement backoff |

**Return Pattern:**
```python
def get_leads() -> list[dict]:
    """Returns list of lead dicts. Empty list on error (not None)."""
    try:
        response = requests.get(...)
        return response.json().get("data", [])
    except Exception as e:
        # Store error for UI to display
        st.session_state.zoho_error = "Unable to connect to Zoho CRM."
        return []  # Always return list, never None
```

### Secrets Configuration

**Expected structure in `.streamlit/secrets.toml`:**
```toml
[zoho]
client_id = "your-client-id"
client_secret = "your-client-secret"
refresh_token = "your-refresh-token"
api_domain = "https://www.zohoapis.com"
```

**Access pattern:**
```python
import streamlit as st

client_id = st.secrets["zoho"]["client_id"]
client_secret = st.secrets["zoho"]["client_secret"]
refresh_token = st.secrets["zoho"]["refresh_token"]
api_domain = st.secrets["zoho"]["api_domain"]
```

### Technical Requirements

- **Timeout:** 30 seconds for all API requests (NFR5)
- **Rate Limits:** Zoho allows 10,000 API calls/day, 100 calls/minute
- **Token Expiry:** Access tokens expire in 1 hour (3600 seconds)
- **Retry Logic:** On 401, refresh token and retry once; on 429, wait and retry

### Zoho API Base URLs

- **OAuth Token:** `https://accounts.zoho.com/oauth/v2/token`
- **API Domain:** Use `api_domain` from secrets (typically `https://www.zohoapis.com`)
- **CRM API:** `{api_domain}/crm/v2/` endpoints

### Security Requirements (CRITICAL)

From NFR8 & NFR9:
- Credentials stored in Streamlit Secrets ONLY (not in code)
- Credentials NEVER displayed in UI
- Credentials NEVER logged (even in error messages)
- Access tokens stored only in session state (ephemeral)

**Anti-pattern to avoid:**
```python
# WRONG - Never log credentials
logger.error(f"Auth failed with client_id={client_id}")

# CORRECT - Generic error message
logger.error("Authentication failed - check credentials in Streamlit secrets")
```

### Project Structure Notes

Files to modify/create:
- `src/zoho_client.py` - Main implementation (replace placeholder)

Files NOT to modify:
- `app.py` - UI layer, separate concern
- `src/data_processing.py` - Business logic, already has staleness functions
- `src/field_mapping.py` - Will be updated in Story 1.3

### Previous Story Intelligence

**From Story 1.1:**
- Project structure established with `src/` package
- `src/zoho_client.py` exists as placeholder with docstring
- pytest available in requirements.txt
- Tests go in `tests/` directory

**Code patterns from previous story:**
- Module docstrings at top of file
- Functions have type hints and docstrings
- Tests use pytest with class-based organization

### Testing This Story

1. Create `.streamlit/secrets.toml` with real Zoho credentials
2. Run: `python -c "from src.zoho_client import test_connection; print(test_connection())"`
3. Verify: Returns True if connection works, False with error message if not
4. Run: `python -m pytest tests/test_zoho_client.py -v`

### References

- [Source: architecture.md#Authentication-Security] - OAuth pattern
- [Source: architecture.md#API-Communication-Patterns] - Error handling standards
- [Source: architecture.md#Project-Structure-Boundaries] - File responsibilities
- [Source: epics.md#Story-1.2] - Original acceptance criteria
- [Zoho OAuth Documentation](https://www.zoho.com/crm/developer/docs/api/v2/oauth-overview.html)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - Implementation successful without debug issues

### Completion Notes List

- Implemented complete OAuth 2.0 token management with automatic refresh
- Token stored in st.session_state with expiry tracking (5-minute buffer before refresh)
- `_make_request()` wrapper handles all API calls with 30-second timeout (NFR5)
- Automatic 401 retry with token refresh (single retry to prevent infinite loops)
- Rate limit (429) handling with actual backoff retry (up to 2 retries with sleep)
- Safe Retry-After header parsing with fallback to default (handles non-numeric values)
- All error messages are user-friendly and NEVER expose credentials (NFR9)
- `test_connection()` function for verifying credentials
- `get_api_domain()` function with test coverage
- 30 comprehensive unit tests with mocked API responses covering:
  - Token refresh success/failure scenarios
  - Token caching and expiry
  - API request handling (success, 401 retry, 429 rate limit with retry)
  - Rate limit max retries exceeded
  - Retry-After header parsing edge cases
  - Error message security (no credential exposure)
  - Timeout and connection error handling
  - API domain retrieval
- All 43 tests pass (13 data_processing + 30 zoho_client)

### Change Log

- 2026-01-08: Implemented zoho_client.py with OAuth 2.0 token management
- 2026-01-08: Added 21 unit tests for zoho_client module
- 2026-01-08: Code review fixes - implemented actual 429 retry with backoff, safe Retry-After parsing, added get_api_domain tests

### File List

- src/zoho_client.py (modified - replaced placeholder with full implementation, added retry backoff)
- tests/test_zoho_client.py (created - 30 unit tests)
