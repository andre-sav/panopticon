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
    get_stage_history,
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
    format_time_in_stage,
    format_stage_history,
    get_status_emoji,
    sort_leads,
    count_leads_by_status,
    apply_filters,
    get_unique_stages,
    get_unique_locators,
    ALL_STAGES,
    ALL_LOCATORS,
    ALL_DATES,
    DATE_RANGE_PRESETS,
    DEFAULT_SORT,
    SORT_OPTIONS,
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


def initialize_filter_and_sort_state():
    """Initialize filter and sort session state with defaults."""
    if "filter_stage" not in st.session_state:
        st.session_state.filter_stage = ALL_STAGES
    if "filter_locator" not in st.session_state:
        st.session_state.filter_locator = ALL_LOCATORS
    if "filter_date_range" not in st.session_state:
        st.session_state.filter_date_range = ALL_DATES
    if "sort_option" not in st.session_state:
        st.session_state.sort_option = DEFAULT_SORT


def display_filters(display_data: list[dict]):
    """Display filter controls and return filtered data (Story 3.1).

    Args:
        display_data: Formatted lead data to filter

    Returns:
        Filtered lead data based on current filter selections
    """
    initialize_filter_and_sort_state()

    # Get unique values for dropdowns
    stages = [ALL_STAGES] + get_unique_stages(display_data)
    locators = [ALL_LOCATORS] + get_unique_locators(display_data)

    # Check if any filters or non-default sort are active
    filters_active = (
        st.session_state.filter_stage != ALL_STAGES
        or st.session_state.filter_locator != ALL_LOCATORS
        or st.session_state.filter_date_range != ALL_DATES
        or st.session_state.sort_option != DEFAULT_SORT
    )

    # Filter and sort row layout
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])

    with col1:
        # Reset to default if selected stage no longer exists in data
        if st.session_state.filter_stage not in stages:
            st.session_state.filter_stage = ALL_STAGES
        stage = st.selectbox(
            "Stage",
            options=stages,
            index=stages.index(st.session_state.filter_stage),
            key="stage_filter_select",
        )
        st.session_state.filter_stage = stage

    with col2:
        # Reset to default if selected locator no longer exists in data
        if st.session_state.filter_locator not in locators:
            st.session_state.filter_locator = ALL_LOCATORS
        locator = st.selectbox(
            "Locator",
            options=locators,
            index=locators.index(st.session_state.filter_locator),
            key="locator_filter_select",
        )
        st.session_state.filter_locator = locator

    with col3:
        date_range = st.selectbox(
            "Date Range",
            options=DATE_RANGE_PRESETS,
            index=DATE_RANGE_PRESETS.index(st.session_state.filter_date_range),
            key="date_range_filter_select",
        )
        st.session_state.filter_date_range = date_range

    with col4:
        sort_option = st.selectbox(
            "Sort By",
            options=SORT_OPTIONS,
            index=SORT_OPTIONS.index(st.session_state.sort_option),
            key="sort_option_select",
        )
        st.session_state.sort_option = sort_option

    with col5:
        st.write("")  # Spacing to align with dropdowns
        if filters_active:
            if st.button("Reset All", use_container_width=True):
                st.session_state.filter_stage = ALL_STAGES
                st.session_state.filter_locator = ALL_LOCATORS
                st.session_state.filter_date_range = ALL_DATES
                st.session_state.sort_option = DEFAULT_SORT
                st.rerun()

    # Apply filters
    filtered_data = apply_filters(
        display_data,
        st.session_state.filter_stage,
        st.session_state.filter_locator,
        st.session_state.filter_date_range,
    )

    return filtered_data


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


def display_lead_detail(lead: dict):
    """Display detailed information for a single lead (Stories 4.1, 4.2).

    Shows:
    - Lead name header
    - Current stage prominently with time in stage
    - Appointment details
    - Locator contact information
    - Stage history with timestamps (Story 4.2)

    Args:
        lead: Formatted lead dictionary from format_leads_for_display()
    """
    # Lead name header
    lead_name = lead.get("Lead Name", "Unknown")
    st.markdown(f"## {lead_name}")

    # Current stage section - prominently displayed
    stage = lead.get("Stage", "—")
    status = lead.get("Status", "")
    days = lead.get("Days")
    time_in_stage = format_time_in_stage(days)

    # Stage with visual emphasis
    st.markdown(f"### Current Stage: {stage}")
    if status:
        st.markdown(f"**Status:** {status}")
    st.markdown(f"**In this stage for:** {time_in_stage}")

    st.divider()

    # Appointment details
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Appointment Details**")
        st.write(f"📅 Date: {lead.get('Appointment Date', '—')}")
        if days is not None:
            st.write(f"📊 Days since: {days}")

    with col2:
        st.markdown("**Locator Contact**")
        locator = lead.get("Locator", "—")
        st.write(f"👤 {locator}")

        # Contact links
        phone = lead.get("Phone")
        email = lead.get("Email")

        if phone:
            st.markdown(f"📞 [{phone.replace('tel:', '')}]({phone})")
        if email:
            st.markdown(f"✉️ [{email.replace('mailto:', '')}]({email})")

        if not phone and not email:
            st.write("No contact info available")

    # Stage History section (Story 4.2)
    st.divider()
    display_stage_history(lead)


def display_stage_history(lead: dict):
    """Display stage transition history for a lead (Story 4.2).

    Fetches and displays the chronological stage history with timestamps.
    Handles empty history and pipeline completion status.

    Args:
        lead: Formatted lead dictionary with 'id' field
    """
    st.markdown("### Stage History")

    lead_id = lead.get("id")
    if not lead_id:
        st.write("Stage history not available (no lead ID)")
        return

    # Fetch stage history (cached per lead in session state)
    cache_key = f"stage_history_{lead_id}"
    error_key = f"stage_history_error_{lead_id}"
    if cache_key not in st.session_state:
        with st.spinner("Loading stage history..."):
            raw_history = get_stage_history(lead_id)
            if raw_history is None:
                # API error - mark as error, don't cache empty list
                st.session_state[error_key] = True
                st.session_state[cache_key] = []
            else:
                st.session_state[error_key] = False
                st.session_state[cache_key] = format_stage_history(raw_history)

    # Check if there was an API error
    if st.session_state.get(error_key, False):
        st.warning("Unable to load stage history")
        return

    history = st.session_state[cache_key]

    if not history:
        st.info("No stage changes recorded")
        return

    # Display transitions in chronological order
    pipeline_complete = False
    for item in history:
        transition = item["transition"]
        timestamp = item["timestamp"]
        is_delivered = item["is_delivered"]

        if is_delivered:
            pipeline_complete = True
            st.success(f"**{transition}** - {timestamp}")
        else:
            st.write(f"**{transition}** - {timestamp}")

    # Show balloons once per lead when pipeline completed (avoid repeat on every rerender)
    if pipeline_complete:
        balloons_key = f"balloons_shown_{lead_id}"
        if balloons_key not in st.session_state:
            st.session_state[balloons_key] = True
            st.balloons()


def display_lead_cards(leads: list[dict]):
    """Display leads as expandable cards with detail views (Story 4.1).

    Args:
        leads: List of formatted lead dictionaries
    """
    for lead in leads:
        lead_name = lead.get("Lead Name", "Unknown")
        stage = lead.get("Stage", "—")
        status = lead.get("Status", "")

        # Create expander label with key info
        status_emoji = get_status_emoji(status)
        emoji_prefix = f"{status_emoji} " if status_emoji else ""

        expander_label = f"{emoji_prefix}{lead_name} — {stage}"

        with st.expander(expander_label):
            display_lead_detail(lead)


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
        # Format leads for display
        display_data = format_leads_for_display(leads)

        # Display filters and get filtered data (Story 3.1)
        filtered_data = display_filters(display_data)

        # Sort filtered data by selected option (Story 3.2)
        filtered_data = sort_leads(filtered_data, st.session_state.sort_option)

        # Display summary metrics cards with filtered data (Story 2.6, AC#2, AC#5, AC#10)
        display_metrics_cards(filtered_data)

        st.divider()

        # Display lead count - show filtered vs total if filters active
        if len(filtered_data) == len(display_data):
            st.markdown(f"**Showing {len(filtered_data)} leads with appointments**")
        else:
            st.markdown(f"**Showing {len(filtered_data)} of {len(display_data)} leads** (filtered)")

        # Handle empty filtered results (AC#12)
        if not filtered_data:
            st.info("No leads match your filters")
            return

        # Display leads as expandable cards (Story 4.1)
        display_lead_cards(filtered_data)
    else:
        st.info("No leads with appointments found")


# Run dashboard
display_dashboard()
