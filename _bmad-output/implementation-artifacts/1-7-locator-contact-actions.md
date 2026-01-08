# Story 1.7: Locator Contact Actions

Status: done

## Story

As **Damione (Coordinator)**,
I want **to see phone and email icons next to each locator that I can click to contact them**,
So that **I can immediately call or email a locator without copying/pasting contact info**.

## Acceptance Criteria

1. **Given** a lead row with locator contact info
   **When** viewing the Locator column
   **Then** a phone icon is displayed (if phone number exists)
   **And** an email icon is displayed (if email exists)
   **And** both icons are visible inline (no hover required)

2. **Given** I click the phone icon
   **When** the click is registered
   **Then** a `tel:` link opens (triggering phone dialer on desktop)

3. **Given** I click the email icon
   **When** the click is registered
   **Then** a `mailto:` link opens (triggering email client)

4. **Given** a locator has no phone number
   **When** viewing the row
   **Then** the phone icon is not shown (or shows "—")

## Tasks / Subtasks

- [x] Task 1: Update format_leads_for_display to include contact links (AC: #1, #2, #3, #4)
  - [x] 1.1: Create `format_phone_link()` function for tel: URLs
  - [x] 1.2: Create `format_email_link()` function for mailto: URLs
  - [x] 1.3: Add Phone and Email columns to display data
  - [x] 1.4: Handle missing phone/email gracefully (return None)

- [x] Task 2: Update app.py to render clickable links (AC: #1)
  - [x] 2.1: Configure st.dataframe with column_config
  - [x] 2.2: Use LinkColumn for Phone with 📞 icon
  - [x] 2.3: Use LinkColumn for Email with ✉️ icon

- [x] Task 3: Write unit tests (AC: #1, #2, #3, #4)
  - [x] 3.1: Test format_phone_link function (4 tests)
  - [x] 3.2: Test format_email_link function (4 tests)
  - [x] 3.3: Test contact columns in format_leads_for_display (5 tests)

## Dev Notes

### Architecture Compliance (CRITICAL)

**Files to modify:**
- `src/data_processing.py` - Add locator cell formatting function
- `app.py` - Update dataframe rendering for HTML support

### Streamlit HTML in Dataframe

Streamlit's `st.dataframe()` doesn't render HTML by default. Options:
1. Use `st.markdown()` with `unsafe_allow_html=True` for custom table
2. Use column configuration with `st.column_config.LinkColumn`
3. Build HTML table manually

**Recommended approach:** Use markdown links which Streamlit renders:
```python
def format_locator_cell(name, phone, email):
    parts = [name or "—"]
    if phone:
        parts.append(f"[📞](tel:{phone})")
    if email:
        parts.append(f"[✉️](mailto:{email})")
    return " ".join(parts)
```

### Previous Story Intelligence

**From Story 1.4:**
- `format_leads_for_display()` transforms lead data for table
- Returns list of dicts with "Lead Name", "Appointment Date", "Stage", "Locator"
- Lead dict has: locator_name, locator_phone, locator_email

### References

- [Source: ux-design-specification.md] - Contact action icons inline
- [Source: epics.md#Story-1.7] - Original acceptance criteria

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Added `format_phone_link()` function to generate tel: URLs
- Added `format_email_link()` function to generate mailto: URLs
- Updated `format_leads_for_display()` to include Phone and Email columns
- Configured st.dataframe with column_config using LinkColumn for clickable icons
- Phone column shows 📞 emoji, Email column shows ✉️ emoji
- Missing contact info shows as empty (None) - Streamlit hides empty link cells
- All 4 acceptance criteria satisfied
- 123 tests total (13 new for this story), all passing

### Senior Developer Review

**Issues Found:** 1
- L1: Misleading docstring comment in `format_phone_link()` said "Strip any non-numeric characters" but code preserved original format - **FIXED** (removed misleading comment)

**Verdict:** APPROVED

### Change Log

- 2026-01-08: Implemented Story 1.7 - Locator Contact Actions
- 2026-01-08: Code review completed - L1 fixed (removed misleading comment)

### File List

- src/data_processing.py (modified)
- app.py (modified)
- tests/test_data_processing.py (modified)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified)

