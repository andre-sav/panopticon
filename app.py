"""
Panopticon - Lead Follow-up Management Dashboard
Main Streamlit application entry point.
"""
import logging
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s"
)

from src.zoho_client import (
    get_leads_with_appointments,
    get_last_error,
    get_error_type,
    get_partial_error,
    set_partial_error,
    clear_error,
    clear_partial_error,
    ERROR_TYPE_AUTH,
)
from src.data_processing import (
    format_leads_for_display,
    format_last_updated,
    sort_by_urgency,
    count_leads_by_status,
    STALE_THRESHOLD_DAYS,
    AT_RISK_THRESHOLD_DAYS,
)

# Page configuration
st.set_page_config(
    page_title="Panopticon",
    page_icon="👁️",
    layout="wide"
)

# Header
st.title("👁️ Panopticon")
st.caption("Lead Follow-up Management Dashboard")


def fetch_and_cache_leads():
    """Fetch leads from Zoho CRM and cache in session state.

    Implements graceful degradation (AC#3, NFR11):
    - On success: Updates leads and clears any partial error
    - On failure with cached data: Keeps cached data and shows warning
    - On failure without cached data: Shows error (handled by display_dashboard)
    """
    # Check if we have existing cached data before fetch
    had_cached_data = "leads" in st.session_state and st.session_state.leads

    # Clear partial error before fetch attempt
    clear_partial_error()

    # Attempt to fetch new data
    leads = get_leads_with_appointments()
    error = get_last_error()

    if leads:
        # Success - update cache and clear errors
        st.session_state.leads = leads
        st.session_state.last_refresh = datetime.now(timezone.utc)
        clear_error()
    elif had_cached_data and error:
        # Failed to fetch but have cached data - graceful degradation (AC#3)
        set_partial_error("Some data may be missing. Showing cached data.")
        # Keep existing leads, don't update last_refresh
    else:
        # No cached data - store empty list (error will be displayed)
        st.session_state.leads = []
        st.session_state.last_refresh = datetime.now(timezone.utc)

    st.session_state.refreshing = False
    return st.session_state.get("leads", [])


def display_header():
    """Display header with last updated timestamp and refresh button."""
    col1, col2 = st.columns([4, 1])

    with col1:
        last_refresh = st.session_state.get("last_refresh")
        st.caption(f"Last updated: {format_last_updated(last_refresh)}")

    with col2:
        is_refreshing = st.session_state.get("refreshing", False)
        if st.button("🔄 Refresh", disabled=is_refreshing, use_container_width=True):
            # Clear cached data to trigger re-fetch
            st.session_state.pop("leads", None)
            st.session_state.refreshing = True
            st.rerun()


def display_error_with_retry():
    """Display error message with Retry button (AC#1, AC#2, AC#4)."""
    error = get_last_error()
    error_type = get_error_type()

    if not error:
        return

    # Display appropriate error message
    st.error(error)

    # Show Retry button for non-auth errors (auth errors suggest page refresh)
    if error_type == ERROR_TYPE_AUTH:
        st.info("Please refresh the page to reconnect.")
    else:
        if st.button("Retry", type="primary"):
            # Clear error state and cached data
            clear_error()
            st.session_state.pop("leads", None)
            st.rerun()


def display_partial_warning():
    """Display warning banner for partial data (AC#3)."""
    partial_error = get_partial_error()
    if partial_error:
        st.warning(partial_error)


def display_metrics_cards(display_data: list[dict]):
    """Display summary metrics cards for lead status counts (Story 2.6).

    Shows three metric cards:
    - Stale count (red indicator)
    - At Risk count (amber indicator)
    - Healthy count (green indicator)

    When stale count is 0, shows a positive signal.
    """
    counts = count_leads_by_status(display_data)

    col1, col2, col3 = st.columns(3)

    with col1:
        stale_count = counts["stale"]
        if stale_count == 0:
            st.metric(label="🔴 Stale", value=0, delta="All clear", delta_color="normal", help="No stale leads!")
        else:
            st.metric(label="🔴 Stale", value=stale_count, help=f"Leads {STALE_THRESHOLD_DAYS}+ days since appointment")

    with col2:
        st.metric(label="🟡 At Risk", value=counts["at_risk"], help=f"Leads {AT_RISK_THRESHOLD_DAYS}-{STALE_THRESHOLD_DAYS - 1} days since appointment")

    with col3:
        st.metric(label="🟢 Healthy", value=counts["healthy"], help=f"Leads < {AT_RISK_THRESHOLD_DAYS} days since appointment")


def display_dashboard():
    """Main dashboard display logic."""
    # Display header with refresh controls
    display_header()

    st.divider()

    # Check if we need to fetch data
    if "leads" not in st.session_state:
        with st.spinner("Loading leads from Zoho CRM..."):
            fetch_and_cache_leads()

    leads = st.session_state.get("leads", [])

    # Check for errors - if error and no data, show error with retry
    error = get_last_error()
    if error and not leads:
        display_error_with_retry()
        return

    # Display partial data warning if applicable (AC#3)
    display_partial_warning()

    # Display table or empty state
    if leads:
        # Format leads for display and sort by urgency (Story 2.5)
        display_data = format_leads_for_display(leads)
        display_data = sort_by_urgency(display_data)

        # Display summary metrics cards (Story 2.6)
        display_metrics_cards(display_data)

        st.divider()

        # Display lead count above table
        st.markdown(f"**Showing {len(leads)} leads with appointments**")

        # Convert to DataFrame for styling (Story 2.4)
        df = pd.DataFrame(display_data)

        # Style function for row background colors based on status
        def style_status_rows(row):
            """Apply background color based on Status column."""
            status = row.get("Status", "")
            if status and "stale" in status:
                return ["background-color: #ffcccc"] * len(row)  # Light red
            elif status and "at_risk" in status:
                return ["background-color: #fff3cd"] * len(row)  # Light amber
            return [""] * len(row)  # No color for healthy

        # Apply row styling
        styled_df = df.style.apply(style_status_rows, axis=1)

        # Configure columns with clickable contact links (Story 1.7)
        column_config = {
            "Phone": st.column_config.LinkColumn(
                "📞",
                help="Click to call locator",
                display_text="📞",
            ),
            "Email": st.column_config.LinkColumn(
                "✉️",
                help="Click to email locator",
                display_text="✉️",
            ),
        }

        # Display as dataframe with styling and contact action columns
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
        )
    else:
        st.info("No leads with appointments found")


# Run dashboard
display_dashboard()
