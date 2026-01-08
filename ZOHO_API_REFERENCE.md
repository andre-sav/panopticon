# Zoho CRM API Reference
**Generated:** 2026-01-07  
**Source:** VendTech/Naturals2Go Zoho CRM Instance  
**Purpose:** Reference for building dashboards and integrations

---

## 1. Authentication

### OAuth 2.0 Setup
Zoho uses OAuth 2.0 with refresh tokens. Access tokens expire in **60 minutes**; refresh at 55 min.

```
Token Endpoint: https://accounts.zoho.com/oauth/v2/token
API Domain:     https://www.zohoapis.com
```

### Refresh Token Flow
```python
POST https://accounts.zoho.com/oauth/v2/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&client_id={ZOHO_CLIENT_ID}
&client_secret={ZOHO_CLIENT_SECRET}
&refresh_token={ZOHO_REFRESH_TOKEN}

Response:
{
  "access_token": "1000.xxxx",
  "api_domain": "https://www.zohoapis.com",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Request Headers
```
Authorization: Zoho-oauthtoken {access_token}
Content-Type: application/json
```

### Required Environment Variables
```bash
ZOHO_CLIENT_ID=1000.XXXXX
ZOHO_CLIENT_SECRET=XXXXX
ZOHO_REFRESH_TOKEN=1000.XXXXX  # Long-lived, doesn't expire
ZOHO_API_DOMAIN=https://www.zohoapis.com
ZOHO_ACCOUNTS_URL=https://accounts.zoho.com
```

---

## 2. API Methods

### Standard REST API v2
- **Base URL:** `https://www.zohoapis.com/crm/v2/{module}`
- **Pagination:** `page=1&per_page=200` (max 200 per page)
- **Lookup expansion:** ✅ Returns `{id: "xxx", name: "John Doe"}` for lookup fields
- **Use for:** Fetching records when you need lookup field names

### COQL (CRM Object Query Language)
- **Endpoint:** `POST https://www.zohoapis.com/crm/v2/coql`
- **Pagination:** `LIMIT 200 OFFSET 0` in query string
- **Lookup expansion:** ❌ Returns IDs only, NOT names
- **Use for:** Complex filtering, date ranges, aggregations

**CRITICAL COQL LIMITATION:** COQL does not expand lookup fields. If you need `Locator_Name.name`, you must use Standard API or build a lookup table.

### Search API
- **Endpoint:** `GET /crm/v2/{module}/search?criteria={criteria}`
- **Criteria syntax:** `((field_name:equals:value)and(field_name:starts_with:value))`
- **Lookup expansion:** ✅ Yes

---

## 3. Modules (Tables)

### Locatings (Primary Module)
Lead records representing visited business locations.

| Field API Name | Type | Description |
|----------------|------|-------------|
| `id` | String | Primary key |
| `Name` | String | Location/business name |
| `Stage` | Picklist | Pipeline stage |
| `Lead_Source` | Picklist | OSL, RBD, NBD, Web, HLM |
| `Locator_Name` | Lookup(Contacts) | Assigned locator (NULL in ~35% of records) |
| `Locating_Programs` | Picklist | OSL, RBD, NBD |
| `LocCampaigns` | Lookup(LocCampaigns) | Associated campaign |
| `Created_Time` | DateTime | Record creation |
| `Modified_Time` | DateTime | Last modification |
| `Modified_By` | Lookup(Users) | ⚠️ UNRELIABLE - overwritten by admin bulk updates |
| `Owner` | Lookup(Users) | Record owner |

**Stage Values (Pipeline):**
- `Appt Not Acknowledged`
- `Declined By Operator`
- `Delivery Requested`
- `Green - Approved By Locator` ← Site Survey Sent
- `Green - LLL Approved` ← LWP Program
- `Green - LLL Fulfilled` ← LWP Complete
- `Green - SiteSurvey Sent`
- `Green/Delivered`
- `Green/No-operator`
- `HLM Follow up` ← Sent to call center

**GREEN_STAGES** (indicates site survey sent):
```python
GREEN_STAGES = [
    "Green - Approved By Locator",
    "Green - LLL Approved", 
    "Green - LLL Fulfilled",
    "Green - SiteSurvey Sent",
    "Green/Delivered",
    "Green/No-operator"
]
```

### Deliveries
Delivery requests submitted by operators.

| Field API Name | Type | Description |
|----------------|------|-------------|
| `id` | String | Primary key |
| `Name` | String | Delivery name (for fuzzy matching) |
| `Locator` | Lookup(Contacts) | ⚠️ Different field name than Locatings! |
| `Locatings` | Lookup(Locatings) | Link to source location |
| `Created_Time` | DateTime | When DR was submitted |

### Contacts (Locators)
Locator master list.

| Field API Name | Type | Description |
|----------------|------|-------------|
| `id` | String | Primary key (JOIN KEY) |
| `Full_Name` | String | Display name |

### Notes
Activity notes attached to Locatings.

| Field API Name | Type | Description |
|----------------|------|-------------|
| `id` | String | Primary key |
| `Parent_Id` | String | Parent Locating ID |
| `Created_By` | Lookup(Users) | ✅ IMMUTABLE - reliable for tracking |
| `Created_Time` | DateTime | When note was created |
| `$se_module` | String | Parent module ("Locatings") |
| `Note_Content` | String | Note text |

**NOTE:** `Created_By` is immutable and should be used for tracking who worked a lead. `Modified_By` on Locatings is overwritten by admin bulk updates.

### Activities
Call and meeting logs.

| Field API Name | Type | Description |
|----------------|------|-------------|
| `id` | String | Primary key |
| `Activity_Type` | Picklist | "Calls", "Meetings", "Tasks" |
| `Owner` | Lookup(Users) | Activity owner |
| `Subject` | String | Activity description |
| `Created_Time` | DateTime | Activity timestamp |

### LocCampaigns
Campaigns for grouping locations.

| Field API Name | Type | Description |
|----------------|------|-------------|
| `id` | String | Primary key |
| `name` | String | Campaign name |
| `Timeline_Warranty` | Boolean | ⚠️ NOT the same as LWP! |

**LWP/LLL Detection:** Campaign names ending in "LLL" indicate Lifetime Warranty Program (LWP). The `Timeline_Warranty` field is a DIFFERENT program.

---

## 4. Query Examples

### COQL: Locatings in Date Range
```sql
select id, Name, Stage, Locator_Name, Created_Time, Modified_Time
from Locatings 
where Created_Time >= '2025-12-01T00:00:00+00:00'
  and Created_Time <= '2025-12-31T23:59:59+00:00'
limit 200 offset 0
```

### COQL: Green Stage Locatings
```sql
select id, Name, Stage, Locator_Name, Modified_Time
from Locatings
where Stage like 'Green%'
limit 200 offset 0
```

### COQL: Deliveries by Locator
```sql
select id, Name, Locator, Locatings, Created_Time
from Deliveries
where Locator = '3524689000012345678'
limit 200 offset 0
```

### COQL: Notes for Locatings Module
```sql
select id, Parent_Id, Created_By, Created_Time
from Notes
where $se_module = 'Locatings'
limit 200 offset 0
```
⚠️ **NOTE:** This query may not work. The Notes search API doesn't reliably support `$se_module` filtering. Fetch all notes and filter in code.

### COQL: Activities (Calls)
```sql
select id, Owner, Activity_Type, Subject, Created_Time
from Activities
where Activity_Type = 'Calls'
  and Created_Time >= '2025-12-01T00:00:00+00:00'
limit 200 offset 0
```

### Standard API: Get Locatings with Lookup Names
```
GET /crm/v2/Locatings?fields=id,Name,Locator_Name,Stage&per_page=200&page=1

Response includes expanded lookup:
{
  "Locator_Name": {
    "id": "3524689000012345678",
    "name": "John Smith"
  }
}
```

### Related Emails (N+1 API Pattern)
```
GET /crm/v2/Locatings/{record_id}/Emails?type=sent_from_crm

Response:
{
  "Emails": [
    {"id": "xxx", "subject": "Site Survey", "sent_time": "2025-12-15T..."}
  ]
}
```
⚠️ **PERFORMANCE:** This requires one API call per Locating record. Avoid in bulk operations.

---

## 5. Join Patterns

### Locatings → Contacts (Locators)
```
Locatings.Locator_Name → Contacts.id
```
⚠️ ~35% of Locatings have NULL Locator_Name. Always use LEFT JOIN.

### Deliveries → Contacts (Locators)
```
Deliveries.Locator → Contacts.id
```
⚠️ Field is named `Locator`, NOT `Locator_Name`. Inconsistent with Locatings.

### Deliveries → Locatings
```
Deliveries.Locatings → Locatings.id
```
Many Deliveries lack this lookup populated. Use fuzzy matching as fallback:
```python
from difflib import SequenceMatcher
ratio = SequenceMatcher(None, locating_name, delivery_name).ratio()
if ratio >= 0.75:  # 75% threshold
    # Consider it a match
```

### Notes → Locatings
```
Notes.Parent_Id → Locatings.id
```
Filter by `$se_module = 'Locatings'` in code (API filtering unreliable).

---

## 6. Rate Limits & Best Practices

### Observed Limits
- **2-minute cooldown** triggered during bulk operations
- No explicit rate limit documentation
- Recommended: max 10 concurrent requests

### Best Practices
1. **Cache locator list** - relatively static, expensive to fetch (pagination)
2. **Use COQL for date filtering** - faster than fetching all + Python filter
3. **Batch commits** - commit every 1000 records during sync
4. **Build lookup tables** - COQL returns IDs; map to names from local cache
5. **Avoid N+1 patterns** - don't call `/Emails` endpoint per record in bulk
6. **Incremental sync** - use `Modified_Time` watermark, not full refresh

### Timestamp Reliability for Sync
| Module | Field | Reliability | Notes |
|--------|-------|-------------|-------|
| Locatings | Created_Time | ✅ High | Immutable |
| Locatings | Modified_Time | ⚠️ Medium | Updated by any change |
| Deliveries | Created_Time | ✅ High | Immutable |
| Notes | Created_Time | ✅ High | Immutable |
| Activities | Created_Time | ✅ High | Immutable |

---

## 7. Common Gotchas

### COQL Doesn't Expand Lookups
```sql
-- Returns: {"Locator_Name": "3524689000012345678"}
-- NOT:     {"Locator_Name": {"id": "xxx", "name": "John"}}
select Locator_Name from Locatings
```
**Solution:** Use Standard API pagination OR build a Contacts lookup table.

### COQL Requires WHERE for Pagination
```sql
-- ❌ Won't paginate properly
select id from Locatings limit 200 offset 200

-- ✅ Works
select id from Locatings where id is not null limit 200 offset 200
```

### Modified_By is Unreliable
Admin bulk updates overwrite `Modified_By` on Locatings. Use `Notes.Created_By` to track who actually worked a lead.

### Field Name Inconsistency
- Locatings: `Locator_Name`
- Deliveries: `Locator`
Both are lookup fields to Contacts, but named differently.

### Null Locator_Name
~35% of Locatings have NULL `Locator_Name`. These records are unattributable to any locator. Always use LEFT JOINs.

### Notes $se_module Filtering
The Notes API doesn't reliably support filtering by `$se_module` in search criteria. Fetch all notes and filter in Python:
```python
for note in all_notes:
    if note.get("$se_module") == "Locatings":
        # Process note
```

---

## 8. Python Client Example

```python
import httpx
from datetime import datetime, timedelta

class ZohoClient:
    def __init__(self, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = None
        self.token_expires_at = None
        self.api_domain = "https://www.zohoapis.com"
        self.accounts_url = "https://accounts.zoho.com"
    
    async def refresh_access_token(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.accounts_url}/oauth/v2/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                }
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data["access_token"]
            self.token_expires_at = datetime.now() + timedelta(minutes=55)
            return self.access_token
    
    async def get_access_token(self):
        if not self.access_token or datetime.now() >= self.token_expires_at:
            return await self.refresh_access_token()
        return self.access_token
    
    async def coql_query(self, query: str):
        token = await self.get_access_token()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_domain}/crm/v2/coql",
                headers={
                    "Authorization": f"Zoho-oauthtoken {token}",
                    "Content-Type": "application/json"
                },
                json={"select_query": query},
                timeout=30.0
            )
            if not response.content:
                return {"data": [], "info": {"count": 0}}
            response.raise_for_status()
            return response.json()
    
    async def get_records(self, module: str, page: int = 1, per_page: int = 200, fields: list = None):
        token = await self.get_access_token()
        params = {"page": page, "per_page": per_page}
        if fields:
            params["fields"] = ",".join(fields)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_domain}/crm/v2/{module}",
                headers={"Authorization": f"Zoho-oauthtoken {token}"},
                params=params,
                timeout=30.0
            )
            if not response.content:
                return {"data": [], "info": {"count": 0}}
            response.raise_for_status()
            return response.json()
```

---

## 9. Appendix: Stage Flow

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

*End of Zoho API Reference*
