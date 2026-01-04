"""
Styling helper functions for dashboard pages.
Provides consistent Apple-inspired styling across all pages.
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
    Render a styled page header with Apple typography.

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
        st.markdown(f'<p style="color: #86868B; font-size: 15px; margin-top: -10px; font-weight: 400;">{subtitle}</p>',
                   unsafe_allow_html=True)


def kpi_card(label: str, value: str, change: str = None, change_positive: bool = True):
    """
    Render a styled KPI card with Apple design language.

    Args:
        label: KPI label (e.g., "CURRENT CASH")
        value: KPI value (e.g., "₱23,450,000.00")
        change: Optional change indicator (e.g., "12.5% vs last month")
        change_positive: Whether the change is positive (green) or negative (red)
    """
    change_color = '#34C759' if change_positive else '#FF3B30'
    arrow = '↑' if change_positive else '↓'

    change_html = ''
    if change:
        change_html = f'<div style="font-size: 13px; color: {change_color}; margin-top: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 500;">{arrow} {change}</div>'

    html = f'''<div style="background: #FFFFFF; border-radius: 16px; padding: 20px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); min-width: 0;">
<div style="font-size: 11px; text-transform: uppercase; color: #86868B; letter-spacing: 0.5px; margin-bottom: 8px; white-space: nowrap; font-weight: 600;">{label}</div>
<div style="font-size: clamp(20px, 2.5vw, 28px); font-weight: 700; color: #1D1D1F; font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{value}</div>
{change_html}</div>'''

    st.markdown(html, unsafe_allow_html=True)


def section_card(content_func, title: str = None):
    """
    Wrap content in a styled section card with Apple design.

    Args:
        content_func: Function that renders the content
        title: Optional section title
    """
    st.markdown('''
    <div style="
        background: #FFFFFF;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        margin-bottom: 24px;
    ">
    ''', unsafe_allow_html=True)

    if title:
        st.markdown(f"### {title}")

    content_func()

    st.markdown('</div>', unsafe_allow_html=True)


def entity_badge(entity: str) -> str:
    """
    Return HTML for an entity badge with Apple colors.

    Args:
        entity: Entity name ("YAHSHUA" or "ABBA")

    Returns:
        HTML string for the badge
    """
    if entity.upper() == 'YAHSHUA':
        bg = 'rgba(0, 122, 255, 0.1)'
        color = '#007AFF'
    else:
        bg = 'rgba(175, 82, 222, 0.1)'
        color = '#AF52DE'

    return f'''<span style="background: {bg}; color: {color}; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600;">{entity}</span>'''


def empty_state(title: str, description: str, icon: str = "📭"):
    """
    Render an empty state message with Apple styling.

    Args:
        title: Main message
        description: Helper text
        icon: Emoji icon
    """
    st.markdown(f'''
    <div style="
        text-align: center;
        padding: 48px 24px;
        color: #AEAEB2;
    ">
        <div style="font-size: 48px; margin-bottom: 16px; opacity: 0.5;">{icon}</div>
        <div style="font-size: 17px; font-weight: 600; color: #86868B; margin-bottom: 8px;">{title}</div>
        <div style="font-size: 15px; color: #AEAEB2;">{description}</div>
    </div>
    ''', unsafe_allow_html=True)


def alert_box(message: str, alert_type: str = 'info'):
    """
    Render a styled alert box with Apple system colors.

    Args:
        message: Alert message
        alert_type: Type of alert ('info', 'success', 'warning', 'error')
    """
    colors = {
        'info': ('rgba(0, 122, 255, 0.1)', '#007AFF'),
        'success': ('rgba(52, 199, 89, 0.1)', '#34C759'),
        'warning': ('rgba(255, 149, 0, 0.1)', '#FF9500'),
        'error': ('rgba(255, 59, 48, 0.1)', '#FF3B30'),
    }
    bg, border = colors.get(alert_type, colors['info'])

    st.markdown(f'''
    <div style="
        background: {bg};
        border-left: 4px solid {border};
        padding: 14px 18px;
        border-radius: 0 10px 10px 0;
        font-size: 15px;
        color: #1D1D1F;
        margin: 8px 0;
    ">{message}</div>
    ''', unsafe_allow_html=True)


def metric_row(metrics: list):
    """
    Render a row of metrics using Apple-styled KPI cards.

    Args:
        metrics: List of dicts with keys: label, value, change (optional), positive (optional)
    """
    cols = st.columns(len(metrics), gap="medium")
    for i, metric in enumerate(metrics):
        with cols[i]:
            kpi_card(
                label=metric.get('label', ''),
                value=metric.get('value', ''),
                change=metric.get('change'),
                change_positive=metric.get('positive', True)
            )
