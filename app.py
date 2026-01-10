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
from streamlit_scroll_to_top import scroll_to_here

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
    get_closing_ratio_summary,
    get_closing_ratio_by_month,
    get_conversion_funnel,
    get_status_chart_config,
    calculate_historical_status_trend,
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

# Custom CSS for visual hierarchy, contrast, and polish
st.markdown("""
<style>
    /* Reduce top padding */
    .block-container {
        padding-top: 2rem;
    }

    /* Hero metric styling for Stale count */
    .stale-hero {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
    }
    .stale-hero .metric-value {
        font-size: 4rem;
        font-weight: 700;
        line-height: 1;
    }
    .stale-hero .metric-label {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }

    /* Secondary metrics */
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border-left: 4px solid;
    }
    .metric-card.at-risk { border-left-color: #ffc107; }
    .metric-card.needs-attention { border-left-color: #fd7e14; }
    .metric-card.healthy { border-left-color: #28a745; }

    /* Alert tables with max height */
    .alert-table {
        max-height: 300px;
        overflow-y: auto;
    }

    /* Lead card spacing */
    div[data-testid="stExpander"] {
        margin-bottom: 0.5rem;
    }

    /* Section headers */
    .section-header {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #6c757d;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }

    /* Compact dataframe styling */
    .stDataFrame {
        font-size: 0.9rem;
    }

    /* Hide expander chevron/arrow icons for cleaner look */
    div[data-testid="stExpander"] svg,
    div[data-testid="stExpander"] details summary svg,
    [data-testid="stExpanderToggleIcon"],
    div[data-testid="stExpander"] summary::before,
    div[data-testid="stExpander"] summary::after,
    div[data-testid="stExpander"] summary > span:first-child svg,
    details[data-testid="stExpander"] summary svg,
    .streamlit-expanderHeader svg,
    /* Additional selectors for newer Streamlit versions */
    [data-testid="stExpander"] summary svg,
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] + svg,
    details summary > svg,
    details summary > span > svg,
    [class*="stExpander"] summary svg {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
    }
</style>
""", unsafe_allow_html=True)

# Header - more compact
st.markdown("# 👁️ Panopticon")
st.caption("Lead Follow-up Management Dashboard")

# Scroll-to-top target and trigger
if st.session_state.get("scroll_to_top", False):
    scroll_to_here(0, key="scroll_top")
    st.session_state.scroll_to_top = False


def fetch_and_cache_leads(bypass_cache: bool = False):
    """Fetch leads from Zoho CRM and cache in session state.

    Implements graceful degradation (AC#3, NFR11):
    - On success: Updates leads and clears any partial error
    - On failure with cached data: Keeps cached data and shows warning
    - On failure without cached data: Shows error (handled by display_dashboard)

    Args:
        bypass_cache: If True, skip Supabase cache and fetch fresh from API
    """
    from src.cache import get_leads_cache_age

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
        # Use cache timestamp if available, otherwise current time (fresh API call)
        cache_age = get_leads_cache_age()
        st.session_state.last_refresh = cache_age if cache_age else datetime.now(timezone.utc)
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
            from src.cache import clear_notes_cache

            # Clear session state and set flag to bypass Supabase cache
            st.session_state.pop("leads", None)
            st.session_state.refreshing = True
            st.session_state.bypass_cache = True

            # Clear notes cache so fresh notes are fetched
            clear_notes_cache()

            # Clear stage history and notes from session state (will be re-fetched)
            keys_to_clear = [k for k in st.session_state.keys()
                             if k.startswith("stage_history_") or k.startswith("notes_")]
            for key in keys_to_clear:
                st.session_state.pop(key, None)

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


def _reset_all_filters():
    """Callback to reset all filters to defaults. Must be called via on_click."""
    st.session_state.filter_stage = ALL_STAGES
    st.session_state.filter_locator = ALL_LOCATORS
    st.session_state.filter_date_range = DEFAULT_DATE_RANGE
    st.session_state.filter_status = ALL_STATUSES
    st.session_state.sort_option = DEFAULT_SORT
    st.session_state.leads_page = 0  # Reset pagination


def display_filters(display_data: list[dict]):
    """Display filter controls in a collapsible section.

    Uses Gestalt principle of enclosure to group filter controls.
    Collapsed by default to prioritize metrics visibility.
    """
    initialize_filter_and_sort_state()

    # Get unique values for dropdowns
    stages = [ALL_STAGES] + get_unique_stages(display_data)
    locators = [ALL_LOCATORS] + get_unique_locators(display_data)

    # Validate current filter values exist in options (data may have changed)
    if st.session_state.filter_stage not in stages:
        st.session_state.filter_stage = ALL_STAGES
    if st.session_state.filter_locator not in locators:
        st.session_state.filter_locator = ALL_LOCATORS

    # Check if any filters or non-default sort are active
    filters_active = (
        st.session_state.filter_stage != ALL_STAGES
        or st.session_state.filter_locator != ALL_LOCATORS
        or st.session_state.filter_date_range != DEFAULT_DATE_RANGE
        or st.session_state.filter_status != ALL_STATUSES
        or st.session_state.sort_option != DEFAULT_SORT
    )

    # Create filter summary for collapsed state
    filter_label = "Filters & Sort"
    if filters_active:
        active_filters = []
        if st.session_state.filter_stage != ALL_STAGES:
            active_filters.append(f"Stage: {st.session_state.filter_stage[:15]}...")
        if st.session_state.filter_locator != ALL_LOCATORS:
            active_filters.append(f"Locator: {st.session_state.filter_locator[:10]}...")
        if st.session_state.filter_status != ALL_STATUSES:
            active_filters.append(st.session_state.filter_status)
        filter_label = f"Filters & Sort ({len(active_filters)} active)"

    with st.expander(filter_label, expanded=filters_active):
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.selectbox(
                "Stage",
                options=stages,
                key="filter_stage",
            )

        with col2:
            st.selectbox(
                "Locator",
                options=locators,
                key="filter_locator",
            )

        with col3:
            st.selectbox(
                "Date Range",
                options=DATE_RANGE_PRESETS,
                key="filter_date_range",
            )

        with col4:
            st.selectbox(
                "Status",
                options=STATUS_FILTER_OPTIONS,
                key="filter_status",
            )

        with col5:
            st.selectbox(
                "Sort By",
                options=SORT_OPTIONS,
                key="sort_option",
            )

        if filters_active:
            st.button(
                "Reset All Filters",
                use_container_width=True,
                on_click=_reset_all_filters,
            )

    # Apply filters
    filtered_data = apply_filters(
        display_data,
        st.session_state.filter_stage,
        st.session_state.filter_locator,
        st.session_state.filter_date_range,
        st.session_state.filter_status,
    )

    return filtered_data


def _render_metric_card(count: int, label: str, color: str, bg_color: str, text_color: str, is_grayed: bool):
    """Render a single metric card with consistent styling."""
    if is_grayed:
        st.markdown(f"""
            <div style="background: #e9ecef; padding: 1rem; border-radius: 8px;
                        border-left: 4px solid #adb5bd; text-align: center; opacity: 0.6;">
                <div style="font-size: 2rem; font-weight: 600; color: #adb5bd;">0</div>
                <div style="font-size: 0.85rem; color: #adb5bd;">{label}</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style="background: {bg_color}; padding: 1rem; border-radius: 8px;
                        border-left: 4px solid {color}; text-align: center;">
                <div style="font-size: 2rem; font-weight: 600; color: {text_color};">{count}</div>
                <div style="font-size: 0.85rem; color: {text_color};">{label}</div>
            </div>
        """, unsafe_allow_html=True)


# Secondary metric card configurations: (key, label, border_color, bg_color, text_color)
METRIC_CARD_CONFIG = [
    ("at_risk", "At Risk", "#ffc107", "#fff8e6", "#856404"),
    ("needs_attention", "Needs Attention", "#fd7e14", "#fff3e6", "#a04000"),
    ("healthy", "Healthy", "#28a745", "#e8f5e9", "#1e7e34"),
]


def display_metrics_cards(display_data: list[dict]):
    """Display summary metrics with visual hierarchy.

    Uses scale and contrast to emphasize the most critical metric (Stale).
    Applies Gestalt principle of similarity with consistent color coding.
    Grays out zero-value cards when a status filter is active.
    """
    counts = count_leads_by_status(display_data)
    total = len(display_data)

    # Check if status filter is active (for graying out zero cards)
    status_filter_active = st.session_state.get("filter_status", ALL_STATUSES) != ALL_STATUSES

    # Layout: Hero metric (Stale) on left, secondary metrics stacked on right
    hero_col, metrics_col = st.columns([1, 2])

    # Hero card (Stale) - special styling
    with hero_col:
        stale_count = counts["stale"]
        is_grayed = status_filter_active and stale_count == 0

        if is_grayed:
            st.markdown("""
                <div style="background: #e9ecef; color: #adb5bd; padding: 1.5rem;
                            border-radius: 12px; text-align: center; opacity: 0.6;">
                    <div style="font-size: 3.5rem; font-weight: 700; line-height: 1;">0</div>
                    <div style="font-size: 1rem; margin-top: 0.5rem;">Stale Leads</div>
                </div>
            """, unsafe_allow_html=True)
        elif stale_count == 0:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                            color: white; padding: 1.5rem; border-radius: 12px;
                            text-align: center; box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);">
                    <div style="font-size: 3.5rem; font-weight: 700; line-height: 1;">0</div>
                    <div style="font-size: 1rem; opacity: 0.9; margin-top: 0.5rem;">Stale Leads</div>
                    <div style="font-size: 0.85rem; margin-top: 0.25rem;">All clear!</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                            color: white; padding: 1.5rem; border-radius: 12px;
                            text-align: center; box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);">
                    <div style="font-size: 3.5rem; font-weight: 700; line-height: 1;">{stale_count}</div>
                    <div style="font-size: 1rem; opacity: 0.9; margin-top: 0.5rem;">Stale Leads</div>
                </div>
            """, unsafe_allow_html=True)

    # Secondary metrics using data-driven loop
    with metrics_col:
        columns = st.columns(len(METRIC_CARD_CONFIG))
        for col, (key, label, color, bg_color, text_color) in zip(columns, METRIC_CARD_CONFIG):
            with col:
                count = counts[key]
                is_grayed = status_filter_active and count == 0
                _render_metric_card(count, label, color, bg_color, text_color, is_grayed)

        # Summary bar showing proportions (Gestalt: continuation)
        if total > 0:
            st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
            stale_pct = (counts["stale"] / total) * 100
            at_risk_pct = (counts["at_risk"] / total) * 100
            needs_pct = (counts["needs_attention"] / total) * 100
            healthy_pct = (counts["healthy"] / total) * 100

            st.markdown(f"""
                <div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; margin-top: 0.5rem;">
                    <div style="width: {stale_pct}%; background: #dc3545;" title="Stale: {counts['stale']}"></div>
                    <div style="width: {at_risk_pct}%; background: #ffc107;" title="At Risk: {counts['at_risk']}"></div>
                    <div style="width: {needs_pct}%; background: #fd7e14;" title="Needs Attention: {counts['needs_attention']}"></div>
                    <div style="width: {healthy_pct}%; background: #28a745;" title="Healthy: {counts['healthy']}"></div>
                </div>
                <div style="font-size: 0.75rem; color: #6c757d; text-align: center; margin-top: 0.25rem;">
                    {total} total leads
                </div>
            """, unsafe_allow_html=True)


import html as html_module


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    if not text:
        return ""
    return html_module.escape(str(text))


def _truncate_note(note: str, max_len: int = 50) -> str:
    """Truncate note text for display."""
    if not note:
        return "—"
    if len(note) <= max_len:
        return note
    return note[:max_len].rsplit(" ", 1)[0] + "..."


def display_priority_list(display_data: list[dict], max_visible: int = 5):
    """Display 'At Risk' leads priority list with in-place expansion.

    Shows top items by default with toggle button to show all.
    Lead names are hyperlinks to cards, Zoho column links to CRM.
    """
    from src.data_processing import format_zoho_link

    # Filter to at_risk leads only
    at_risk_leads = [
        lead for lead in display_data
        if "at_risk" in (lead.get("Status") or "").lower()
    ]

    if not at_risk_leads:
        return

    # Build table data
    table_data = []
    for lead in at_risk_leads:
        # Format appointment date as MM.DD.YYYY
        appt_date = lead.get("Appointment Date", "—")
        if appt_date and appt_date != "—":
            try:
                from datetime import datetime as dt
                parsed = dt.strptime(appt_date, "%b %d, %Y")
                appt_date_formatted = parsed.strftime("%m.%d.%Y")
            except (ValueError, TypeError):
                appt_date_formatted = appt_date
        else:
            appt_date_formatted = "—"

        lead_id = lead.get("id", "")
        days = lead.get("Days")
        # For at-risk (future appointments), show just the number (days until)
        days_display = str(abs(days)) if days is not None else "—"

        table_data.append({
            "id": lead_id,
            "Lead": lead.get("Lead Name", "Unknown"),
            "Appt Date": appt_date_formatted,
            "Days Until": days_display,
            "Locator": lead.get("Locator", "—"),
            "zoho_url": format_zoho_link(lead_id) if lead_id else "",
        })

    total_count = len(table_data)

    # Header with count and reason in parentheses
    st.markdown(f"""
        <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 0.75rem 1rem;
                    border-radius: 0 4px 4px 0; margin-bottom: 0.5rem;">
            <strong>⚠️ {total_count} lead{'s' if total_count != 1 else ''} at risk</strong>
            <span style="color: #856404;"> (Appointment unacknowledged by Locator)</span>
        </div>
    """, unsafe_allow_html=True)

    # Initialize expansion state
    if "at_risk_expanded" not in st.session_state:
        st.session_state.at_risk_expanded = False

    # Determine which rows to show
    visible_data = table_data if (total_count <= max_visible or st.session_state.at_risk_expanded) else table_data[:max_visible]

    # Render as HTML table with clickable lead names
    html_rows = []
    for row in visible_data:
        lead_id = _escape_html(row["id"])
        lead_name = _escape_html(row["Lead"])
        lead_cell = f'<a href="#lead-{lead_id}" style="color: #1a73e8; text-decoration: none;">{lead_name}</a>'
        appt_date = _escape_html(row["Appt Date"])
        days = _escape_html(row["Days Until"])
        locator = _escape_html(row["Locator"])
        zoho_url = row.get("zoho_url", "")
        zoho_cell = f'<a href="{zoho_url}" target="_blank" style="color: #1a73e8; text-decoration: none;">{lead_id}</a>' if zoho_url else "—"
        html_rows.append(f'<tr><td style="padding: 8px; border-bottom: 1px solid #eee; width: 35%;">{lead_cell}</td><td style="padding: 8px; border-bottom: 1px solid #eee; width: 12%;">{appt_date}</td><td style="padding: 8px; border-bottom: 1px solid #eee; width: 10%;">{days}</td><td style="padding: 8px; border-bottom: 1px solid #eee; width: 18%;">{locator}</td><td style="padding: 8px; border-bottom: 1px solid #eee; width: 25%;">{zoho_cell}</td></tr>')

    html_table = f'<table style="width: 100%; border-collapse: collapse; font-size: 0.9rem; table-layout: fixed;"><thead><tr style="background: #f8f9fa; text-align: left;"><th style="padding: 8px; border-bottom: 2px solid #dee2e6; width: 35%;">Lead</th><th style="padding: 8px; border-bottom: 2px solid #dee2e6; width: 12%;">Appt Date</th><th style="padding: 8px; border-bottom: 2px solid #dee2e6; width: 10%;">Days Until</th><th style="padding: 8px; border-bottom: 2px solid #dee2e6; width: 18%;">Locator</th><th style="padding: 8px; border-bottom: 2px solid #dee2e6; width: 25%;">Zoho</th></tr></thead><tbody>{"".join(html_rows)}</tbody></table>'
    st.markdown(html_table, unsafe_allow_html=True)

    # Show expand/collapse button if needed
    if total_count > max_visible:
        if st.session_state.at_risk_expanded:
            if st.button("Show less", key="at_risk_collapse"):
                st.session_state.at_risk_expanded = False
                st.rerun()
        else:
            st.caption(f"Showing {max_visible} of {total_count}")
            if st.button(f"Show all {total_count}", key="at_risk_expand"):
                st.session_state.at_risk_expanded = True
                st.rerun()


def display_needs_attention_list(display_data: list[dict], max_visible: int = 5):
    """Display 'Needs Attention' leads list with in-place expansion.

    Shows leads that need attention (e.g., Green - Approved By Locator
    with no update in 7+ days). Shows top N by default with toggle button.
    Lead names are hyperlinks to Zoho CRM. Notes are shown in expandable cards.
    """
    from src.data_processing import format_zoho_link

    # Filter to needs_attention leads only
    needs_attention_leads = [
        lead for lead in display_data
        if "needs_attention" in (lead.get("Status") or "").lower()
    ]

    if not needs_attention_leads:
        return

    total_count = len(needs_attention_leads)

    # Custom styled header with alert styling and reason in parentheses
    st.markdown(f"""
        <div style="background: #fff3cd; border-left: 4px solid #fd7e14; padding: 0.75rem 1rem; margin-bottom: 0.5rem; border-radius: 0 4px 4px 0;">
            <strong style="color: #856404;">🟠 {total_count} lead{'s' if total_count != 1 else ''} need{'s' if total_count == 1 else ''} attention</strong>
            <span style="color: #856404;"> (have not progressed from Green - Approved by Locator in 7+ days)</span>
        </div>
    """, unsafe_allow_html=True)

    # Create table data
    table_data = []
    for lead in needs_attention_leads:
        # Format appointment date as MM.DD.YYYY
        appt_date = lead.get("Appointment Date", "—")
        if appt_date and appt_date != "—":
            try:
                from datetime import datetime as dt
                parsed = dt.strptime(appt_date, "%b %d, %Y")
                appt_date_formatted = parsed.strftime("%m.%d.%Y")
            except (ValueError, TypeError):
                appt_date_formatted = appt_date
        else:
            appt_date_formatted = "—"

        lead_id = lead.get("id", "")
        days = lead.get("Days")
        # For needs-attention (past appointments), show just the number (days since)
        days_display = str(abs(days)) if days is not None else "—"

        table_data.append({
            "id": lead_id,
            "Lead": lead.get("Lead Name", "Unknown"),
            "Appt Date": appt_date_formatted,
            "Days Since": days_display,
            "Locator": lead.get("Locator", "—"),
            "zoho_url": format_zoho_link(lead_id) if lead_id else "",
        })

    # Initialize expansion state
    if "needs_attention_expanded" not in st.session_state:
        st.session_state.needs_attention_expanded = False

    # Determine which rows to show
    visible_data = table_data if (total_count <= max_visible or st.session_state.needs_attention_expanded) else table_data[:max_visible]

    # Render as HTML table with clickable lead names
    html_rows = []
    for row in visible_data:
        lead_id = _escape_html(row["id"])
        lead_name = _escape_html(row["Lead"])
        lead_cell = f'<a href="#lead-{lead_id}" style="color: #1a73e8; text-decoration: none;">{lead_name}</a>'
        appt_date = _escape_html(row["Appt Date"])
        days = _escape_html(row["Days Since"])
        locator = _escape_html(row["Locator"])
        zoho_url = row["zoho_url"]
        zoho_cell = f'<a href="{zoho_url}" target="_blank" style="color: #1a73e8; text-decoration: none;">{lead_id}</a>' if zoho_url else "—"
        html_rows.append(f'<tr><td style="padding: 8px; border-bottom: 1px solid #eee; width: 35%;">{lead_cell}</td><td style="padding: 8px; border-bottom: 1px solid #eee; width: 12%;">{appt_date}</td><td style="padding: 8px; border-bottom: 1px solid #eee; width: 10%;">{days}</td><td style="padding: 8px; border-bottom: 1px solid #eee; width: 18%;">{locator}</td><td style="padding: 8px; border-bottom: 1px solid #eee; width: 25%;">{zoho_cell}</td></tr>')

    html_table = f'<table style="width: 100%; border-collapse: collapse; font-size: 0.9rem; table-layout: fixed;"><thead><tr style="background: #f8f9fa; text-align: left;"><th style="padding: 8px; border-bottom: 2px solid #dee2e6; width: 35%;">Lead</th><th style="padding: 8px; border-bottom: 2px solid #dee2e6; width: 12%;">Appt Date</th><th style="padding: 8px; border-bottom: 2px solid #dee2e6; width: 10%;">Days Since</th><th style="padding: 8px; border-bottom: 2px solid #dee2e6; width: 18%;">Locator</th><th style="padding: 8px; border-bottom: 2px solid #dee2e6; width: 25%;">Zoho</th></tr></thead><tbody>{"".join(html_rows)}</tbody></table>'
    st.markdown(html_table, unsafe_allow_html=True)

    # Show expand/collapse button if needed
    if total_count > max_visible:
        if st.session_state.needs_attention_expanded:
            if st.button("Show less", key="needs_attention_collapse"):
                st.session_state.needs_attention_expanded = False
                st.rerun()
        else:
            st.caption(f"Showing {max_visible} of {total_count}")
            if st.button(f"Show all {total_count}", key="needs_attention_expand"):
                st.session_state.needs_attention_expanded = True
                st.rerun()


def display_stage_pipeline(display_data: list[dict]):
    """Display horizontal bar chart showing lead counts by stage.

    Visualizes the pipeline to identify where leads are getting stuck.
    Bars are color-coded by status breakdown within each stage.
    Click on a stage bar to filter the dashboard to that stage.
    """
    stage_data = count_leads_by_stage(display_data)

    if not stage_data:
        st.info("No stage data available")
        return

    # Sort by total count descending for better visualization
    stages = [d["stage"] for d in stage_data]

    # Build stacked horizontal bar chart with Plotly
    fig = go.Figure()

    # Use centralized status configuration
    for status_key, status_label, color in get_status_chart_config():
        values = [d[status_key] for d in stage_data]
        fig.add_trace(go.Bar(
            name=status_label,
            y=stages,
            x=values,
            orientation="h",
            marker_color=color,
            customdata=stages,
        ))

    fig.update_layout(
        title_text="Stage Pipeline (click to filter)",
        barmode="stack",
        xaxis_title="",
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

    # Enable click-to-filter with on_select
    event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="stage_pipeline_chart")

    # Handle click events - filter to selected stage
    if event and event.selection and event.selection.points:
        clicked_point = event.selection.points[0]
        # Get the stage name from the y-axis value
        clicked_stage = clicked_point.get("y")
        if clicked_stage and clicked_stage != st.session_state.get("filter_stage"):
            st.session_state.filter_stage = clicked_stage
            st.session_state.leads_page = 0  # Reset pagination when filter changes
            st.rerun()


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
    # Reverse the standard config order for bottom-up stacking
    status_configs = get_status_chart_config()[::-1]

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


def display_status_trend(display_data: list[dict]):
    """Display line chart showing health rate percentage over time.

    Shows a single line tracking the percentage of leads that are healthy,
    making it easy to see if things are improving or getting worse.

    Args:
        display_data: List of formatted lead dictionaries
    """
    # Create a cache key from lead data (count + sample of IDs for uniqueness)
    cache_key = f"trend_{len(display_data)}"
    if display_data:
        # Include first and last lead IDs to detect data changes
        cache_key += f"_{display_data[0].get('id', '')}_{display_data[-1].get('id', '')}"

    # Check session state cache first
    if "trend_cache_key" in st.session_state and st.session_state.trend_cache_key == cache_key:
        trend_data = st.session_state.trend_data
    else:
        # Calculate and cache
        trend_data = calculate_historical_status_trend(display_data, weeks=13)
        st.session_state.trend_cache_key = cache_key
        st.session_state.trend_data = trend_data

    if len(trend_data) < 2:
        st.info("Not enough data for trend chart.")
        return

    # Calculate health rate % for each week
    dates = [d["date_label"] for d in trend_data]
    health_rates = []
    for d in trend_data:
        total = d.get("stale", 0) + d.get("at_risk", 0) + d.get("needs_attention", 0) + d.get("healthy", 0)
        if total > 0:
            rate = (d.get("healthy", 0) / total) * 100
        else:
            rate = 0
        health_rates.append(round(rate, 1))

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        name="Health Rate",
        x=dates,
        y=health_rates,
        mode="lines+markers",
        line=dict(color="#28a745", width=3),
        marker=dict(size=10),
        hovertemplate="%{y:.1f}%<extra></extra>",
    ))

    # Calculate Y-axis range to show meaningful variation
    min_rate = min(health_rates)
    max_rate = max(health_rates)
    # Add padding and ensure we show a reasonable range
    y_min = max(0, min_rate - 5)
    y_max = min(100, max_rate + 5)
    # Ensure at least 10% range for visual clarity
    if y_max - y_min < 10:
        mid = (y_min + y_max) / 2
        y_min = max(0, mid - 5)
        y_max = min(100, mid + 5)

    fig.update_layout(
        title_text="Health Rate Trend (Last 90 Days)",
        xaxis_title="",
        yaxis_title="% Healthy",
        yaxis=dict(
            range=[y_min, y_max],
            ticksuffix="%",
        ),
        margin=dict(t=40, b=40, l=50, r=20),
        height=280,
        hovermode="x unified",
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)


def display_conversion_funnel(display_data: list[dict]):
    """Display conversion funnel showing lead progression through pipeline.

    Shows how leads progress from appointment → acknowledged → approved → closed.
    """
    funnel_data = get_conversion_funnel(display_data)

    if not funnel_data:
        st.info("No data for conversion funnel")
        return

    st.markdown("### Conversion Funnel")

    # Build funnel chart with Plotly
    stages = [d["stage"] for d in funnel_data]
    counts = [d["count"] for d in funnel_data]
    percentages = [d["pct"] for d in funnel_data]

    # Create hover text with count and percentage
    hover_text = [f"{stage}<br>{count:,} leads ({pct}%)"
                  for stage, count, pct in zip(stages, counts, percentages)]

    fig = go.Figure(go.Funnel(
        y=stages,
        x=counts,
        textinfo="value+percent initial",
        textposition="inside",
        hovertext=hover_text,
        hoverinfo="text",
        marker=dict(
            color=["#17a2b8", "#28a745", "#ffc107", "#28a745"],
            line=dict(width=2, color="white")
        ),
        connector=dict(line=dict(color="lightgray", width=1)),
    ))

    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=250,
        funnelmode="stack",
    )

    st.plotly_chart(fig, use_container_width=True)


def display_closing_ratio(filtered_data: list[dict], all_data: list[dict]):
    """Display closing ratio summary metric and monthly trend chart.

    Shows:
    - Summary metric: Overall closing ratio for filtered leads
    - Trend chart: Monthly closing ratios for last 6 months (always full history)

    Args:
        filtered_data: Filtered leads list (for summary metric)
        all_data: Unfiltered leads list (for trend chart - always shows 6 months)
    """
    # Header with tooltip using expander for explanation
    col_title, col_help = st.columns([6, 1])
    with col_title:
        st.markdown("### Closing Ratio")
    with col_help:
        with st.popover("ⓘ"):
            st.markdown("""
**How this is calculated:**

**SUCCESS stages:**
- Green/ Delivered
- Delivery Requested
- Green - LLL Fulfilled

**FAILED stages:**
- Red/ Rejected
- Declined by Operator
- Red/Not Viable

**EXCLUDED (not counted):**
- Green/No operator

*Note: Leads are grouped by appointment date, not the date they reached their current stage. Recent closes from older appointments may not appear in short date filters.*
            """)

    # Calculate summary from filtered data
    summary = get_closing_ratio_summary(filtered_data)

    # Calculate monthly data from ALL data (always show 6 months history)
    monthly_data = get_closing_ratio_by_month(all_data, months=6)

    # Layout: Summary metric on left, trend chart on right
    metric_col, chart_col = st.columns([1, 2])

    with metric_col:
        if summary["ratio"] is not None:
            ratio_display = f"{summary['ratio']:.1f}%"
            # Color based on ratio
            if summary["ratio"] >= 70:
                color = "#28a745"  # Green
                bg_color = "#e8f5e9"
            elif summary["ratio"] >= 50:
                color = "#ffc107"  # Yellow
                bg_color = "#fff8e6"
            else:
                color = "#dc3545"  # Red
                bg_color = "#ffeaea"

            st.markdown(f"""
                <div style="background: {bg_color}; padding: 1.5rem; border-radius: 12px;
                            text-align: center; border-left: 4px solid {color};">
                    <div style="font-size: 3rem; font-weight: 700; color: {color}; line-height: 1;">
                        {ratio_display}
                    </div>
                    <div style="font-size: 0.9rem; color: #666; margin-top: 0.5rem;">
                        Closing Ratio
                    </div>
                    <div style="font-size: 0.8rem; color: #888; margin-top: 0.25rem;">
                        {summary['successful']} successful / {summary['total_completed']} completed
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 12px;
                            text-align: center; border-left: 4px solid #6c757d;">
                    <div style="font-size: 2rem; font-weight: 700; color: #6c757d; line-height: 1;">
                        —
                    </div>
                    <div style="font-size: 0.9rem; color: #666; margin-top: 0.5rem;">
                        Closing Ratio
                    </div>
                    <div style="font-size: 0.8rem; color: #888; margin-top: 0.25rem;">
                        No completed leads yet
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Show breakdown below metric
        st.markdown(f"""
            <div style="margin-top: 1rem; font-size: 0.85rem; color: #666;">
                <div>✓ Successful: {summary['successful']}</div>
                <div>✗ Failed: {summary['failed']}</div>
                <div>◉ Still Active: {summary['active']}</div>
            </div>
        """, unsafe_allow_html=True)

    with chart_col:
        if not monthly_data:
            st.info("Not enough data for trend chart")
            return

        # Filter to months that have completed leads for meaningful ratios
        months_with_data = [m for m in monthly_data if m["ratio"] is not None]

        if len(months_with_data) < 2:
            st.info("Trend data will appear after more leads reach terminal stages")
            return

        # Build bar chart showing closing ratio by month
        fig = go.Figure()

        # Add bars for closing ratio
        fig.add_trace(go.Bar(
            name="Closing Ratio",
            x=[m["month_label"] for m in months_with_data],
            y=[m["ratio"] for m in months_with_data],
            marker_color="#1a73e8",
            text=[f"{m['ratio']:.0f}%" for m in months_with_data],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Ratio: %{y:.1f}%<br>Completed: %{customdata}<extra></extra>",
            customdata=[m["total_completed"] for m in months_with_data],
        ))

        # Add a reference line at overall average
        if summary["ratio"] is not None:
            fig.add_hline(
                y=summary["ratio"],
                line_dash="dash",
                line_color="#888",
                annotation_text=f"Avg: {summary['ratio']:.0f}%",
                annotation_position="right",
            )

        fig.update_layout(
            title_text="Monthly Closing Ratio Trend",
            xaxis_title="",
            yaxis_title="Closing Ratio (%)",
            yaxis=dict(range=[0, 105]),  # 0-100% with room for labels
            showlegend=False,
            margin=dict(t=40, b=40, l=40, r=60),
            height=300,
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
            if days < 0:
                st.write(f"📊 Days until: {abs(days)}")
            else:
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

    # Notes section - use prefetched notes from session state
    st.divider()
    lead_id = lead.get("id")
    if lead_id:
        cache_key = f"notes_{lead_id}"
        note_data = st.session_state.get(cache_key, {"content": "", "time": None})
        note_content = note_data.get("content", "") if isinstance(note_data, dict) else note_data
        note_time = note_data.get("time") if isinstance(note_data, dict) else None

        # Format the timestamp if available
        if note_time:
            from src.zoho_client import parse_zoho_date
            parsed_time = parse_zoho_date(note_time) if isinstance(note_time, str) else note_time
            if parsed_time:
                time_str = parsed_time.strftime("%b %d, %Y at %I:%M %p")
                st.markdown(f"**Latest Note** ({time_str})")
            else:
                st.markdown("**Latest Note**")
        else:
            st.markdown("**Latest Note**")

        if note_content:
            st.write(note_content)
        else:
            st.write("No notes available")
    else:
        st.markdown("**Latest Note**")
        st.write("No notes available")

    # Stage History section (Story 4.2)
    st.divider()
    display_stage_history(lead)

    # Back to top button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        if st.button("↑ Back to top", key=f"back_top_{lead.get('id', '')}", use_container_width=True):
            st.session_state.scroll_to_top = True
            st.rerun()


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

    st.markdown("### Stage History")

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
        st.info("No stage changes recorded yet. The lead may be new or still in its initial stage.")
        return

    # Build vertical timeline HTML
    timeline_items = []
    for i, item in enumerate(history):
        transition = item["transition"]
        timestamp = item["timestamp"]
        is_delivered = item["is_delivered"]
        is_last = i == len(history) - 1

        # Determine color based on stage content
        transition_lower = transition.lower()
        if is_delivered or "delivered" in transition_lower:
            color = "#28a745"  # Green for delivered
            icon = "✓"
        elif "rejected" in transition_lower or "red" in transition_lower:
            color = "#dc3545"  # Red for rejection
            icon = "✗"
        elif "pending" in transition_lower or "decision" in transition_lower:
            color = "#ffc107"  # Yellow for pending
            icon = "◉"
        elif "approved" in transition_lower or "green" in transition_lower:
            color = "#28a745"  # Green for approved
            icon = "●"
        else:
            color = "#1a73e8"  # Blue for general progress
            icon = "●"

        # Line continues unless it's the last item
        line_style = f"border-left: 2px solid {color};" if not is_last else ""

        timeline_items.append(
            f'<div style="display:flex;margin-bottom:0;">'
            f'<div style="display:flex;flex-direction:column;align-items:center;margin-right:12px;">'
            f'<div style="width:24px;height:24px;border-radius:50%;background:{color};display:flex;align-items:center;justify-content:center;color:white;font-size:12px;font-weight:bold;">{icon}</div>'
            f'<div style="flex-grow:1;min-height:20px;{line_style}"></div>'
            f'</div>'
            f'<div style="padding-bottom:16px;">'
            f'<div style="font-weight:500;color:#333;font-size:14px;">{_escape_html(transition)}</div>'
            f'<div style="color:#666;font-size:12px;margin-top:2px;">{_escape_html(timestamp)}</div>'
            f'</div>'
            f'</div>'
        )

    timeline_html = f'<div style="padding:10px 0;">{"".join(timeline_items)}</div>'
    st.markdown(timeline_html, unsafe_allow_html=True)


def _prefetch_stage_histories(leads: list[dict]):
    """Prefetch stage histories with concurrent API fetching for uncached leads.

    Uses batch Supabase cache query AND concurrent Zoho API fetching for
    any leads not in cache. This eliminates the N+1 query pattern.

    Results are stored in session state for use by display_stage_history().

    Args:
        leads: List of formatted lead dictionaries with 'id' and 'Stage' fields
    """
    from src.zoho_client import get_stage_histories_batch

    # Get leads that don't already have stage history in session state
    leads_to_fetch = []
    for lead in leads:
        lead_id = lead.get("id")
        if not lead_id:
            continue
        cache_key = f"stage_history_{lead_id}"
        if cache_key not in st.session_state:
            leads_to_fetch.append(lead)

    if not leads_to_fetch:
        return

    # Batch fetch: checks Supabase cache AND fetches uncached from API concurrently
    histories = get_stage_histories_batch(leads_to_fetch)

    # Store results in session state
    for lead_id, history in histories.items():
        cache_key = f"stage_history_{lead_id}"
        st.session_state[cache_key] = format_stage_history(history)
        st.session_state[f"stage_history_error_{lead_id}"] = False


def _prefetch_notes(leads: list[dict]):
    """Prefetch notes for all leads in a single batch operation.

    Stores results in session state for use by display_lead_detail.
    This avoids N+1 queries when rendering lead cards.
    """
    from src.zoho_client import get_notes_for_leads

    # Get lead IDs that don't already have notes in session state
    lead_ids_to_fetch = []
    for lead in leads:
        lead_id = lead.get("id")
        if not lead_id:
            continue
        cache_key = f"notes_{lead_id}"
        if cache_key not in st.session_state:
            lead_ids_to_fetch.append(lead_id)

    if not lead_ids_to_fetch:
        return

    # Single batch fetch for all leads
    notes_map = get_notes_for_leads(lead_ids_to_fetch)

    # Store in session state (now stores dict with 'content' and 'time')
    for lead_id in lead_ids_to_fetch:
        cache_key = f"notes_{lead_id}"
        st.session_state[cache_key] = notes_map.get(lead_id, {"content": "", "time": None})


LEADS_PER_PAGE = 50


def _find_lead_page(leads: list[dict], lead_id: str) -> int:
    """Find which page a lead is on given its ID.

    Returns page number (0-indexed) or -1 if not found.
    """
    for idx, lead in enumerate(leads):
        if lead.get("id") == lead_id:
            return idx // LEADS_PER_PAGE
    return -1


def display_lead_cards(leads: list[dict]):
    """Display leads as expandable cards with detail views and pagination.

    Cards have colored status indicators for quick visual identification.
    Shows LEADS_PER_PAGE leads at a time with navigation controls.

    Args:
        leads: List of formatted lead dictionaries
    """
    total_leads = len(leads)

    # Initialize pagination state
    if "leads_page" not in st.session_state:
        st.session_state.leads_page = 0

    # Check for scroll target (set by JavaScript when clicking a lead link)
    scroll_target = st.session_state.get("scroll_to_lead")
    if scroll_target:
        # Find which page the lead is on
        target_page = _find_lead_page(leads, scroll_target)
        if target_page >= 0:
            st.session_state.leads_page = target_page
        # Clear the scroll target after processing (will be re-added by JS for scroll)
        # Keep it for one more render so JS can use it
        if st.session_state.get("scroll_target_processed"):
            del st.session_state.scroll_to_lead
            del st.session_state.scroll_target_processed
        else:
            st.session_state.scroll_target_processed = True

    # Calculate pagination
    total_pages = max(1, (total_leads + LEADS_PER_PAGE - 1) // LEADS_PER_PAGE)

    # Ensure current page is valid
    if st.session_state.leads_page >= total_pages:
        st.session_state.leads_page = total_pages - 1
    if st.session_state.leads_page < 0:
        st.session_state.leads_page = 0

    current_page = st.session_state.leads_page
    start_idx = current_page * LEADS_PER_PAGE
    end_idx = min(start_idx + LEADS_PER_PAGE, total_leads)

    # Get leads for current page
    page_leads = leads[start_idx:end_idx]

    # Prefetch stage histories and notes for current page only
    _prefetch_stage_histories(page_leads)
    _prefetch_notes(page_leads)

    # Pagination controls at top if more than one page
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("← Previous", disabled=(current_page == 0), key="prev_page"):
                st.session_state.leads_page -= 1
                st.rerun()
        with col2:
            st.markdown(
                f"<div style='text-align: center; padding: 0.5rem;'>"
                f"Page {current_page + 1} of {total_pages} "
                f"<span style='color: #666;'>({start_idx + 1}-{end_idx} of {total_leads})</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        with col3:
            if st.button("Next →", disabled=(current_page >= total_pages - 1), key="next_page"):
                st.session_state.leads_page += 1
                st.rerun()

    # Render lead cards for current page
    for lead in page_leads:
        lead_id = lead.get("id", "")
        lead_name = lead.get("Lead Name", "Unknown")
        stage = lead.get("Stage", "—")
        status = lead.get("Status", "")

        # Get colored circle indicator based on status (uses existing helper)
        status_emoji = get_status_emoji(status)
        emoji_prefix = f"{status_emoji} " if status_emoji else ""

        expander_label = f"{emoji_prefix}{lead_name} — {stage}"

        # Add anchor for scrolling with data attribute for lead name
        st.markdown(f'<div id="lead-{lead_id}" data-leadname="{lead_name}"></div>', unsafe_allow_html=True)

        with st.expander(expander_label, expanded=False):
            display_lead_detail(lead)

    # Pagination controls at bottom too if many leads
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("← Previous", disabled=(current_page == 0), key="prev_page_bottom"):
                st.session_state.leads_page -= 1
                st.rerun()
        with col2:
            st.markdown(
                f"<div style='text-align: center; padding: 0.5rem;'>"
                f"Page {current_page + 1} of {total_pages}"
                f"</div>",
                unsafe_allow_html=True
            )
        with col3:
            if st.button("Next →", disabled=(current_page >= total_pages - 1), key="next_page_bottom"):
                st.session_state.leads_page += 1
                st.rerun()


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
    # Initialize last_refresh from cache if not set (for fresh page loads)
    if "last_refresh" not in st.session_state:
        from src.cache import get_leads_cache_age
        cache_age = get_leads_cache_age()
        if cache_age:
            st.session_state.last_refresh = cache_age

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

        # Display status distribution and appointments timeline
        # Hide distribution chart when status filter is active (becomes meaningless)
        status_filter_active = st.session_state.get("filter_status", ALL_STATUSES) != ALL_STATUSES

        if status_filter_active:
            # Just show timeline at full width when distribution is hidden
            display_appointments_timeline(filtered_data)
        else:
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                display_status_donut(filtered_data)
            with chart_col2:
                display_appointments_timeline(filtered_data)

        st.divider()

        # Display status trend over time (uses all data, not filtered)
        display_status_trend(display_data)

        # Display conversion funnel and closing ratio side by side
        date_filter = st.session_state.get("filter_date_range", DEFAULT_DATE_RANGE)
        if date_filter not in ("Last 7 Days + Future", "Future"):
            st.divider()
            funnel_col, ratio_col = st.columns(2)
            with funnel_col:
                display_conversion_funnel(filtered_data)
            with ratio_col:
                display_closing_ratio(filtered_data, display_data)

        st.divider()

        # Display lead count - show filtered vs total if filters active
        if len(filtered_data) == len(display_data):
            st.markdown(f"**Showing {len(filtered_data)} leads with appointments**")
        else:
            st.markdown(f"**Showing {len(filtered_data)} of {len(display_data)} leads** (filtered)")

        # Handle empty filtered results (AC#12)
        if not filtered_data:
            st.info("No leads match your current filters. Try adjusting the filters or click 'Reset All Filters' above.")
            return

        # Display leads as expandable cards (Story 4.1)
        display_lead_cards(filtered_data)
    else:
        st.info("No leads with appointments found. Check that leads in Zoho CRM have appointment dates set.")


# Run dashboard
display_dashboard()

# Add JavaScript for lead navigation (must be at end after all content rendered)
import streamlit.components.v1 as components

# Check for scroll_to query param and set session state
scroll_to_param = st.query_params.get("scroll_to")
if scroll_to_param:
    st.session_state.scroll_to_lead = scroll_to_param
    # Clear the query param
    st.query_params.clear()
    st.rerun()

# Get current scroll target for JS
current_scroll_target = st.session_state.get("scroll_to_lead", "")

components.html(f"""
<script>
(function() {{
    const doc = window.parent.document;
    const scrollTarget = "{current_scroll_target}";

    // Scroll to lead and expand
    const scrollToLead = (leadId) => {{
        const anchor = doc.getElementById('lead-' + leadId);
        if (!anchor) {{
            // Lead not on current page - redirect with query param to navigate
            const currentUrl = new URL(window.parent.location.href);
            currentUrl.searchParams.set('scroll_to', leadId);
            window.parent.location.href = currentUrl.toString();
            return;
        }}

        // Get lead name from data attribute
        const leadName = anchor.getAttribute('data-leadname');

        // First, find and expand the expander by matching lead name in summary text
        const allDetails = doc.querySelectorAll('details');
        let targetDetails = null;

        for (const details of allDetails) {{
            const summary = details.querySelector('summary');
            if (summary && leadName && summary.textContent.includes(leadName)) {{
                targetDetails = details;
                break;
            }}
        }}

        if (targetDetails && !targetDetails.open) {{
            const summary = targetDetails.querySelector('summary');
            if (summary) {{
                summary.click();
            }}
        }}

        // After expanding, scroll to show the card with padding at top
        setTimeout(() => {{
            const target = targetDetails || anchor;
            target.scrollIntoView({{behavior: 'smooth', block: 'start'}});
            // Add more padding after scroll completes
            setTimeout(() => {{
                window.parent.scrollBy({{top: -120, behavior: 'smooth'}});
            }}, 400);
        }}, 200);
    }};

    // Handle clicks on lead links
    const handleClick = (e) => {{
        const link = e.target.closest('a[href^="#lead-"]');
        if (link) {{
            e.preventDefault();
            e.stopPropagation();
            const leadId = link.getAttribute('href').replace('#lead-', '');
            scrollToLead(leadId);
        }}
    }};

    // Attach listener to parent document
    doc.addEventListener('click', handleClick, true);

    // If we have a scroll target from Python, scroll to it on load
    if (scrollTarget) {{
        setTimeout(() => scrollToLead(scrollTarget), 500);
    }}
}})();
</script>
""", height=0)
