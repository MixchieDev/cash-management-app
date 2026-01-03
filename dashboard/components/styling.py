"""
Styling helper functions for dashboard pages.
Provides consistent styling across all pages.
"""
import streamlit as st
from pathlib import Path


def load_css():
    """Load custom CSS styles."""
    css_path = Path(__file__).parent.parent / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def page_header(title: str, subtitle: str = None, icon: str = None):
    """
    Render a styled page header.

    Args:
        title: Page title
        subtitle: Optional subtitle/description
        icon: Optional emoji icon
    """
    if icon:
        st.markdown(f"# {icon} {title}")
    else:
        st.markdown(f"# {title}")

    if subtitle:
        st.markdown(f'<p style="color: #6B7280; font-size: 14px; margin-top: -10px;">{subtitle}</p>',
                   unsafe_allow_html=True)


def kpi_card(label: str, value: str, change: str = None, change_positive: bool = True):
    """
    Render a styled KPI card using st.markdown.

    Args:
        label: KPI label (e.g., "CURRENT CASH")
        value: KPI value (e.g., "₱23,450,000.00")
        change: Optional change indicator (e.g., "12.5% vs last month")
        change_positive: Whether the change is positive (green) or negative (red)
    """
    change_color = '#10B981' if change_positive else '#EF4444'
    arrow = '↑' if change_positive else '↓'

    change_html = ''
    if change:
        change_html = f'''
        <div style="font-size: 12px; color: {change_color}; margin-top: 4px;">
            {arrow} {change}
        </div>
        '''

    st.markdown(f'''
    <div style="
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 20px 24px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        height: 100%;
    ">
        <div style="
            font-size: 12px;
            text-transform: uppercase;
            color: #6B7280;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        ">{label}</div>
        <div style="
            font-size: 28px;
            font-weight: 700;
            color: #111827;
            font-family: 'SF Mono', 'Fira Code', monospace;
        ">{value}</div>
        {change_html}
    </div>
    ''', unsafe_allow_html=True)


def section_card(content_func, title: str = None):
    """
    Wrap content in a styled section card.

    Args:
        content_func: Function that renders the content
        title: Optional section title
    """
    st.markdown('''
    <div style="
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 24px;
    ">
    ''', unsafe_allow_html=True)

    if title:
        st.markdown(f"### {title}")

    content_func()

    st.markdown('</div>', unsafe_allow_html=True)


def entity_badge(entity: str) -> str:
    """
    Return HTML for an entity badge.

    Args:
        entity: Entity name ("YAHSHUA" or "ABBA")

    Returns:
        HTML string for the badge
    """
    if entity.upper() == 'YAHSHUA':
        bg = 'rgba(59, 130, 246, 0.1)'
        color = '#2563EB'
    else:
        bg = 'rgba(139, 92, 246, 0.1)'
        color = '#7C3AED'

    return f'''<span style="
        background: {bg};
        color: {color};
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
    ">{entity}</span>'''


def empty_state(title: str, description: str, icon: str = "📭"):
    """
    Render an empty state message.

    Args:
        title: Main message
        description: Helper text
        icon: Emoji icon
    """
    st.markdown(f'''
    <div style="
        text-align: center;
        padding: 48px 24px;
        color: #9CA3AF;
    ">
        <div style="font-size: 48px; margin-bottom: 16px; opacity: 0.5;">{icon}</div>
        <div style="font-size: 16px; font-weight: 500; color: #6B7280; margin-bottom: 8px;">{title}</div>
        <div style="font-size: 14px; color: #9CA3AF;">{description}</div>
    </div>
    ''', unsafe_allow_html=True)


def alert_box(message: str, alert_type: str = 'info'):
    """
    Render a styled alert box.

    Args:
        message: Alert message
        alert_type: Type of alert ('info', 'success', 'warning', 'error')
    """
    colors = {
        'info': ('rgba(59, 130, 246, 0.1)', '#3B82F6'),
        'success': ('rgba(16, 185, 129, 0.1)', '#10B981'),
        'warning': ('rgba(245, 158, 11, 0.1)', '#F59E0B'),
        'error': ('rgba(239, 68, 68, 0.1)', '#EF4444'),
    }
    bg, border = colors.get(alert_type, colors['info'])

    st.markdown(f'''
    <div style="
        background: {bg};
        border-left: 4px solid {border};
        padding: 12px 16px;
        border-radius: 0 6px 6px 0;
        font-size: 14px;
        color: #111827;
        margin: 8px 0;
    ">{message}</div>
    ''', unsafe_allow_html=True)


def metric_row(metrics: list):
    """
    Render a row of metrics using custom KPI card styling.

    Args:
        metrics: List of dicts with keys: label, value, change (optional), positive (optional)
    """
    cols = st.columns(len(metrics))
    for i, metric in enumerate(metrics):
        with cols[i]:
            kpi_card(
                label=metric.get('label', ''),
                value=metric.get('value', ''),
                change=metric.get('change'),
                change_positive=metric.get('positive', True)
            )
