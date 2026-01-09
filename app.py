"""
Panopticon - Lead Follow-up Management Dashboard
Main Streamlit application entry point.
"""
import logging
import platform
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    count_leads_by_stage,
    get_locator_workload,
    get_about_to_go_stale,
    apply_filters,
    get_unique_stages,
    get_unique_locators,
    ALL_STAGES,
    ALL_LOCATORS,
    ALL_DATES,
    ALL_STATUSES,
    DATE_RANGE_PRESETS,
    STATUS_FILTER_OPTIONS,
    DEFAULT_SORT,
    DEFAULT_DATE_RANGE,
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


def fetch_and_cache_leads(bypass_cache: bool = False):
    """Fetch leads from Zoho CRM and cache in session state.

    Implements graceful degradation (AC#3, NFR11):
    - On success: Updates leads and clears any partial error
    - On failure with cached data: Keeps cached data and shows warning
    - On failure without cached data: Shows error (handled by display_dashboard)

    Args:
        bypass_cache: If True, skip Supabase cache and fetch fresh from API
    """
    # Check if we have existing cached data before fetch
    had_cached_data = "leads" in st.session_state and st.session_state.leads

    # Clear partial error before fetch attempt
    clear_partial_error()

    # Attempt to fetch new data
    leads = get_leads_with_appointments(bypass_cache=bypass_cache)
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
            # Clear session state and set flag to bypass Supabase cache
            st.session_state.pop("leads", None)
            st.session_state.refreshing = True
            st.session_state.bypass_cache = True
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
        st.session_state.filter_date_range = DEFAULT_DATE_RANGE
    if "filter_status" not in st.session_state:
        st.session_state.filter_status = ALL_STATUSES
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
        or st.session_state.filter_date_range != DEFAULT_DATE_RANGE
        or st.session_state.filter_status != ALL_STATUSES
        or st.session_state.sort_option != DEFAULT_SORT
    )

    # Filter and sort row layout - two rows for better organization
    col1, col2, col3, col4 = st.columns(4)

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
        status_filter = st.selectbox(
            "Status",
            options=STATUS_FILTER_OPTIONS,
            index=STATUS_FILTER_OPTIONS.index(st.session_state.filter_status),
            key="status_filter_select",
        )
        st.session_state.filter_status = status_filter

    # Second row: Sort and Reset
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        sort_option = st.selectbox(
            "Sort By",
            options=SORT_OPTIONS,
            index=SORT_OPTIONS.index(st.session_state.sort_option),
            key="sort_option_select",
        )
        st.session_state.sort_option = sort_option

    with col8:
        st.write("")  # Spacing to align with dropdowns
        if filters_active:
            if st.button("Reset All", use_container_width=True):
                st.session_state.filter_stage = ALL_STAGES
                st.session_state.filter_locator = ALL_LOCATORS
                st.session_state.filter_date_range = DEFAULT_DATE_RANGE
                st.session_state.filter_status = ALL_STATUSES
                st.session_state.sort_option = DEFAULT_SORT
                st.rerun()

    # Apply filters
    filtered_data = apply_filters(
        display_data,
        st.session_state.filter_stage,
        st.session_state.filter_locator,
        st.session_state.filter_date_range,
        st.session_state.filter_status,
    )

    return filtered_data


def display_metrics_cards(display_data: list[dict]):
    """Display summary metrics cards for lead status counts (Story 2.6).

    Shows four metric cards:
    - Stale count (red indicator)
    - At Risk count (amber indicator)
    - Needs Attention count (orange indicator)
    - Healthy count (green indicator)

    When stale count is 0, shows a positive signal.
    """
    counts = count_leads_by_status(display_data)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        stale_count = counts["stale"]
        if stale_count == 0:
            st.metric(label="🔴 Stale", value=0, delta="All clear", delta_color="normal", help="No stale leads!")
        else:
            st.metric(label="🔴 Stale", value=stale_count, help="Leads 7+ days post appointment with no change in Stage")

    with col2:
        st.metric(label="🟡 At Risk", value=counts["at_risk"], help="Leads approaching 7 days post appointment with no change in Stage OR with unacknowledged appointment")

    with col3:
        st.metric(label="🟠 Needs Attention", value=counts["needs_attention"], help="Green - Approved By Locator > 7 days without update")

    with col4:
        st.metric(label="🟢 Healthy", value=counts["healthy"])


def display_priority_list(display_data: list[dict]):
    """Display 'At Risk' leads priority list.

    Shows all at-risk leads with the reason they are flagged,
    helping prioritize follow-up actions.
    """
    # Filter to at_risk leads only
    at_risk_leads = [
        lead for lead in display_data
        if "at_risk" in (lead.get("Status") or "").lower()
    ]

    if not at_risk_leads:
        # No at-risk items - show positive message
        st.success("**No leads at risk** - You're ahead of the game!")
        return

    # Show warning header with count
    st.warning(f"**⚠️ {len(at_risk_leads)} lead{'s' if len(at_risk_leads) != 1 else ''} at risk** - Action needed!")

    # Create compact table for at-risk leads
    table_data = []
    for lead in at_risk_leads:
        days = lead.get("Days")
        stage = lead.get("Stage", "—")

        # Determine reason for at-risk status
        if stage and "appt not acknowledged" in stage.lower():
            reason = "Awaiting acknowledgment"
        elif days is not None and days >= AT_RISK_THRESHOLD_DAYS:
            reason = f"{days} days since appt"
        else:
            reason = "Needs follow-up"

        table_data.append({
            "Lead": lead.get("Lead Name", "Unknown"),
            "Reason": reason,
            "Stage": stage,
            "Locator": lead.get("Locator", "—"),
            "Zoho": lead.get("zoho_link", ""),
        })

    df = pd.DataFrame(table_data)

    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Lead": st.column_config.TextColumn("Lead", width="medium"),
            "Reason": st.column_config.TextColumn("Reason", width="medium"),
            "Stage": st.column_config.TextColumn("Stage", width="medium"),
            "Locator": st.column_config.TextColumn("Locator", width="medium"),
            "Zoho": st.column_config.LinkColumn("Zoho", width="small", display_text="Open"),
        },
    )


def display_needs_attention_list(display_data: list[dict]):
    """Display 'Needs Attention' leads list.

    Shows leads that need attention (e.g., Green - Approved By Locator
    with no update in 7+ days).
    """
    # Filter to needs_attention leads only
    needs_attention_leads = [
        lead for lead in display_data
        if "needs_attention" in (lead.get("Status") or "").lower()
    ]

    if not needs_attention_leads:
        return

    # Show info header with count
    st.info(f"**🟠 {len(needs_attention_leads)} lead{'s' if len(needs_attention_leads) != 1 else ''} need{'s' if len(needs_attention_leads) == 1 else ''} attention**")

    # Create compact table
    table_data = []
    for lead in needs_attention_leads:
        days = lead.get("Days")
        stage = lead.get("Stage", "—")

        # Reason for needs_attention is typically stale in Green - Approved stage
        reason = "No update in 7+ days"

        table_data.append({
            "Lead": lead.get("Lead Name", "Unknown"),
            "Reason": reason,
            "Stage": stage,
            "Locator": lead.get("Locator", "—"),
            "Zoho": lead.get("zoho_link", ""),
        })

    df = pd.DataFrame(table_data)

    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Lead": st.column_config.TextColumn("Lead", width="medium"),
            "Reason": st.column_config.TextColumn("Reason", width="medium"),
            "Stage": st.column_config.TextColumn("Stage", width="medium"),
            "Locator": st.column_config.TextColumn("Locator", width="medium"),
            "Zoho": st.column_config.LinkColumn("Zoho", width="small", display_text="Open"),
        },
    )


def display_stage_pipeline(display_data: list[dict]):
    """Display horizontal bar chart showing lead counts by stage.

    Visualizes the pipeline to identify where leads are getting stuck.
    Bars are color-coded by status breakdown within each stage.
    """
    stage_data = count_leads_by_stage(display_data)

    if not stage_data:
        st.info("No stage data available")
        return

    # Sort by total count descending for better visualization
    stages = [d["stage"] for d in stage_data]

    # Build stacked horizontal bar chart with Plotly
    fig = go.Figure()

    status_configs = [
        ("stale", "Stale", "#dc3545"),
        ("at_risk", "At Risk", "#ffc107"),
        ("needs_attention", "Needs Attention", "#fd7e14"),
        ("healthy", "Healthy", "#28a745"),
    ]

    for status_key, status_label, color in status_configs:
        values = [d[status_key] for d in stage_data]
        fig.add_trace(go.Bar(
            name=status_label,
            y=stages,
            x=values,
            orientation="h",
            marker_color=color,
        ))

    fig.update_layout(
        title_text="Stage Pipeline",
        barmode="stack",
        xaxis_title="Leads",
        yaxis_title="",
        yaxis=dict(automargin=True),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5,
            entrywidth=90,
        ),
        margin=dict(t=40, b=60, l=10, r=20),
        height=max(300, len(stages) * 25 + 100),
    )

    st.plotly_chart(fig, use_container_width=True)


def display_locator_workload(display_data: list[dict]):
    """Display locator workload table with status breakdown.

    Shows which locators have the most urgent leads needing attention.
    Sorted by urgency (stale + at_risk + needs_attention).
    """
    workload_data = get_locator_workload(display_data)

    if not workload_data:
        st.info("No locator data available")
        return

    st.markdown("### Locator Workload")

    # Create DataFrame for display
    df = pd.DataFrame(workload_data)

    # Rename columns for display
    df = df.rename(columns={
        "locator": "Locator",
        "total": "Total",
        "stale": "🔴 Stale",
        "at_risk": "🟡 At Risk",
        "needs_attention": "🟠 Needs Attn",
        "healthy": "🟢 Healthy",
    })

    # Display as styled dataframe
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Locator": st.column_config.TextColumn("Locator", width="medium"),
            "Total": st.column_config.NumberColumn("Total", width="small"),
            "🔴 Stale": st.column_config.NumberColumn("🔴 Stale", width="small"),
            "🟡 At Risk": st.column_config.NumberColumn("🟡 At Risk", width="small"),
            "🟠 Needs Attn": st.column_config.NumberColumn("🟠 Needs Attn", width="small"),
            "🟢 Healthy": st.column_config.NumberColumn("🟢 Healthy", width="small"),
        },
    )


def display_status_donut(display_data: list[dict]):
    """Display donut chart showing status distribution.

    Provides a visual breakdown of lead health across the pipeline.
    """
    counts = count_leads_by_status(display_data)

    # Prepare data for donut chart
    labels = ["Stale", "At Risk", "Needs Attention", "Healthy"]
    values = [counts["stale"], counts["at_risk"], counts["needs_attention"], counts["healthy"]]
    colors = ["#dc3545", "#ffc107", "#fd7e14", "#28a745"]

    # Filter out zero values for cleaner chart
    filtered_data = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]

    if not filtered_data:
        st.info("No status data available")
        return

    labels, values, colors = zip(*filtered_data)

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        marker_colors=colors,
        textinfo="value+percent",
        textposition="outside",
        showlegend=True,
    )])

    fig.update_layout(
        title_text="Status Distribution",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=40, b=40, l=20, r=20),
        height=350,
    )

    st.plotly_chart(fig, use_container_width=True)


def display_appointments_timeline(display_data: list[dict]):
    """Display bar chart showing appointment volume by week, color-coded by status.

    Helps identify trends and busy periods in the appointment pipeline.

    Args:
        display_data: List of formatted lead dictionaries
    """
    from collections import defaultdict
    from datetime import datetime, timedelta

    if not display_data:
        st.info("No appointment data available")
        return

    # Group appointments by week and status
    week_status_counts = defaultdict(lambda: {"stale": 0, "at_risk": 0, "needs_attention": 0, "healthy": 0})

    for lead in display_data:
        days = lead.get("Days")
        if days is None:
            continue

        # Calculate the appointment date from days since
        today = datetime.now(timezone.utc).date()
        appt_date = today - timedelta(days=days)

        # Get the Monday of that week (week start)
        week_start = appt_date - timedelta(days=appt_date.weekday())
        week_key = week_start.strftime("%Y-%m-%d")

        # Get status
        status = lead.get("Status") or ""
        if "stale" in status.lower():
            week_status_counts[week_key]["stale"] += 1
        elif "at_risk" in status.lower():
            week_status_counts[week_key]["at_risk"] += 1
        elif "needs_attention" in status.lower():
            week_status_counts[week_key]["needs_attention"] += 1
        else:
            week_status_counts[week_key]["healthy"] += 1

    if not week_status_counts:
        st.info("No appointment data to display")
        return

    # Sort by week and prepare data for chart
    sorted_weeks = sorted(week_status_counts.keys())

    # Format week labels nicely (e.g., "Jan 6")
    week_labels = []
    for week in sorted_weeks:
        dt = datetime.strptime(week, "%Y-%m-%d")
        week_labels.append(dt.strftime("%b %-d") if platform.system() != "Windows" else dt.strftime("%b %#d"))

    # Build traces for stacked bar chart
    fig = go.Figure()

    # Add bars in order: healthy (bottom), needs_attention, at_risk, stale (top)
    status_configs = [
        ("healthy", "Healthy", "#28a745"),
        ("needs_attention", "Needs Attention", "#fd7e14"),
        ("at_risk", "At Risk", "#ffc107"),
        ("stale", "Stale", "#dc3545"),
    ]

    for status_key, status_label, color in status_configs:
        values = [week_status_counts[week][status_key] for week in sorted_weeks]
        fig.add_trace(go.Bar(
            name=status_label,
            x=week_labels,
            y=values,
            marker_color=color,
        ))

    fig.update_layout(
        title_text="Appointments by Week",
        barmode="stack",
        xaxis_title="",
        yaxis_title="Appointments",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            entrywidth=100,
        ),
        margin=dict(t=40, b=80, l=40, r=20),
        height=380,
    )

    st.plotly_chart(fig, use_container_width=True)


def display_status_trend():
    """Display line chart showing status counts over time.

    Uses daily snapshots stored in Supabase to show trends.
    """
    from src.cache import get_status_snapshots

    snapshots = get_status_snapshots(days=30)

    if len(snapshots) < 2:
        st.info("Trend data will appear after a few days of usage.")
        return

    # Prepare data for chart
    dates = []
    for s in snapshots:
        dt = datetime.strptime(s["snapshot_date"], "%Y-%m-%d")
        dates.append(dt.strftime("%b %-d") if platform.system() != "Windows" else dt.strftime("%b %#d"))

    fig = go.Figure()

    # Add lines for each status
    status_configs = [
        ("stale_count", "Stale", "#dc3545"),
        ("at_risk_count", "At Risk", "#ffc107"),
        ("needs_attention_count", "Needs Attention", "#fd7e14"),
        ("healthy_count", "Healthy", "#28a745"),
    ]

    for field, label, color in status_configs:
        values = [s.get(field, 0) for s in snapshots]
        fig.add_trace(go.Scatter(
            name=label,
            x=dates,
            y=values,
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=6),
        ))

    fig.update_layout(
        title_text="Status Trend (Last 30 Days)",
        xaxis_title="",
        yaxis_title="Leads",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            entrywidth=90,
        ),
        margin=dict(t=40, b=60, l=40, r=20),
        height=350,
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)


def display_lead_detail(lead: dict):
    """Display detailed information for a single lead (Stories 4.1, 4.2).

    Shows:
    - Lead name header with Zoho CRM link
    - Current stage prominently with time in stage
    - Appointment details
    - Locator contact information
    - Stage history with timestamps (Story 4.2)

    Args:
        lead: Formatted lead dictionary from format_leads_for_display()
    """
    # Lead name header with Zoho link
    lead_name = lead.get("Lead Name", "Unknown")
    zoho_link = lead.get("zoho_link")

    if zoho_link:
        st.markdown(f"## {lead_name} [↗]({zoho_link})")
    else:
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
    Includes smart cache invalidation and manual refresh button.

    Args:
        lead: Formatted lead dictionary with 'id' and 'Stage' fields
    """
    from src.cache import clear_cache

    lead_id = lead.get("id")
    if not lead_id:
        st.markdown("### Stage History")
        st.write("Stage history not available (no lead ID)")
        return

    current_stage = lead.get("Stage")

    # Session state keys
    cache_key = f"stage_history_{lead_id}"
    error_key = f"stage_history_error_{lead_id}"
    refresh_key = f"refresh_history_{lead_id}"

    # Handle refresh button click
    if st.session_state.get(refresh_key, False):
        # Clear both session state and Supabase cache
        st.session_state.pop(cache_key, None)
        st.session_state.pop(error_key, None)
        st.session_state[refresh_key] = False
        clear_cache(lead_id)

    # Header row with title and refresh button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Stage History")
    with col2:
        if st.button("🔄 Refresh", key=f"btn_refresh_{lead_id}", use_container_width=True):
            st.session_state[refresh_key] = True
            st.rerun()

    # Fetch stage history (cached per lead in session state)
    if cache_key not in st.session_state:
        with st.spinner("Loading stage history..."):
            # Pass current_stage for smart cache invalidation
            raw_history = get_stage_history(lead_id, current_stage=current_stage)
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
    for item in history:
        transition = item["transition"]
        timestamp = item["timestamp"]
        is_delivered = item["is_delivered"]

        if is_delivered:
            st.success(f"**{transition}** - {timestamp}")
        else:
            st.write(f"**{transition}** - {timestamp}")


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


def _capture_daily_snapshot(display_data: list[dict]):
    """Capture today's status snapshot if not already captured.

    Called once per day on dashboard load to track trends.
    """
    from src.cache import get_today_snapshot, save_status_snapshot

    # Check if already captured today
    if get_today_snapshot() is not None:
        return

    # Calculate counts from unfiltered data
    counts = count_leads_by_status(display_data)
    save_status_snapshot(counts)


def display_dashboard():
    """Main dashboard display logic."""
    # Display header with refresh controls
    display_header()

    st.divider()

    # Check if we need to fetch data
    if "leads" not in st.session_state:
        # Check if this is a forced refresh (bypass cache)
        bypass_cache = st.session_state.pop("bypass_cache", False)
        spinner_msg = "Refreshing leads from Zoho CRM..." if bypass_cache else "Loading leads..."
        with st.spinner(spinner_msg):
            fetch_and_cache_leads(bypass_cache=bypass_cache)

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

        # Capture daily status snapshot for trend tracking (uses unfiltered data)
        _capture_daily_snapshot(display_data)

        # Display filters and get filtered data (Story 3.1)
        filtered_data = display_filters(display_data)

        # Sort filtered data by selected option (Story 3.2)
        filtered_data = sort_leads(filtered_data, st.session_state.sort_option)

        # Display summary metrics cards with filtered data (Story 2.6, AC#2, AC#5, AC#10)
        display_metrics_cards(filtered_data)

        st.divider()

        # Display priority list - at risk leads (most actionable)
        display_priority_list(filtered_data)

        # Display needs attention list
        display_needs_attention_list(filtered_data)

        st.divider()

        # Display visualizations side by side
        viz_col1, viz_col2 = st.columns(2)

        with viz_col1:
            display_stage_pipeline(filtered_data)

        with viz_col2:
            display_locator_workload(filtered_data)

        st.divider()

        # Display status distribution and stage transitions
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            display_status_donut(filtered_data)

        with chart_col2:
            display_appointments_timeline(filtered_data)

        st.divider()

        # Display status trend over time
        display_status_trend()

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
