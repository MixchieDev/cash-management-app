"""
Mercury/Linear-inspired theme for JESUS Company Cash Management Dashboard.
Clean, minimal, professional design system.
"""

# ═══════════════════════════════════════════════════════════════════
# COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════

COLORS = {
    # Base colors
    'background': '#FFFFFF',
    'surface': '#F9FAFB',
    'border': '#E5E7EB',
    'border_light': '#F3F4F6',

    # Text colors
    'text_primary': '#111827',
    'text_secondary': '#6B7280',
    'text_muted': '#9CA3AF',
    'text_inverted': '#FFFFFF',

    # Accent colors
    'primary': '#3B82F6',
    'primary_hover': '#2563EB',
    'primary_light': 'rgba(59, 130, 246, 0.1)',

    # Status colors
    'success': '#10B981',
    'success_light': 'rgba(16, 185, 129, 0.1)',
    'warning': '#F59E0B',
    'warning_light': 'rgba(245, 158, 11, 0.1)',
    'danger': '#EF4444',
    'danger_hover': '#DC2626',
    'danger_light': 'rgba(239, 68, 68, 0.1)',
    'info': '#3B82F6',
    'info_light': 'rgba(59, 130, 246, 0.1)',

    # Entity colors
    'yahshua': '#3B82F6',
    'yahshua_light': 'rgba(59, 130, 246, 0.1)',
    'abba': '#8B5CF6',
    'abba_light': 'rgba(139, 92, 246, 0.1)',

    # Chart colors (accent palette)
    'chart_blue': '#3B82F6',
    'chart_emerald': '#10B981',
    'chart_amber': '#F59E0B',
    'chart_rose': '#F43F5E',
    'chart_violet': '#8B5CF6',
    'chart_cyan': '#06B6D4',
}

# Chart color sequence for multiple series
CHART_COLORS = [
    COLORS['chart_blue'],
    COLORS['chart_emerald'],
    COLORS['chart_amber'],
    COLORS['chart_rose'],
    COLORS['chart_violet'],
    COLORS['chart_cyan'],
]

# ═══════════════════════════════════════════════════════════════════
# TYPOGRAPHY
# ═══════════════════════════════════════════════════════════════════

FONTS = {
    'primary': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    'mono': '"SF Mono", "Fira Code", "JetBrains Mono", Consolas, monospace',
}

FONT_SIZES = {
    'xs': '12px',
    'sm': '14px',
    'base': '16px',
    'lg': '18px',
    'xl': '20px',
    '2xl': '24px',
    '3xl': '32px',
    '4xl': '40px',
}

# ═══════════════════════════════════════════════════════════════════
# SPACING
# ═══════════════════════════════════════════════════════════════════

SPACING = {
    'xs': '4px',
    'sm': '8px',
    'md': '16px',
    'lg': '24px',
    'xl': '32px',
    '2xl': '48px',
}

# ═══════════════════════════════════════════════════════════════════
# COMPONENT STYLES
# ═══════════════════════════════════════════════════════════════════

CARD_STYLE = {
    'background': COLORS['background'],
    'border': f"1px solid {COLORS['border']}",
    'border_radius': '12px',
    'padding': SPACING['lg'],
    'shadow': '0 1px 3px rgba(0, 0, 0, 0.05)',
}

KPI_CARD_STYLE = {
    'background': COLORS['background'],
    'border': f"1px solid {COLORS['border']}",
    'border_radius': '8px',
    'padding': '20px 24px',
    'shadow': '0 1px 2px rgba(0, 0, 0, 0.05)',
}

# ═══════════════════════════════════════════════════════════════════
# PLOTLY CHART CONFIG
# ═══════════════════════════════════════════════════════════════════

def get_chart_layout(title: str = None, height: int = 400) -> dict:
    """Get standard Plotly layout configuration."""
    layout = {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {
            'family': FONTS['primary'],
            'color': COLORS['text_secondary'],
            'size': 12,
        },
        'margin': {'l': 40, 'r': 20, 't': 40, 'b': 40},
        'height': height,
        'xaxis': {
            'gridcolor': COLORS['border'],
            'linecolor': COLORS['border'],
            'tickfont': {'size': 12, 'color': COLORS['text_secondary']},
            'showgrid': True,
            'gridwidth': 1,
        },
        'yaxis': {
            'gridcolor': COLORS['border'],
            'linecolor': COLORS['border'],
            'tickfont': {'size': 12, 'color': COLORS['text_secondary']},
            'showgrid': True,
            'gridwidth': 1,
        },
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': -0.2,
            'xanchor': 'center',
            'x': 0.5,
            'font': {'size': 12},
        },
        'hoverlabel': {
            'bgcolor': COLORS['background'],
            'bordercolor': COLORS['border'],
            'font': {'family': FONTS['primary'], 'size': 13, 'color': COLORS['text_primary']},
        },
    }
    if title:
        layout['title'] = {
            'text': title,
            'font': {'size': 16, 'color': COLORS['text_primary'], 'family': FONTS['primary']},
            'x': 0,
            'xanchor': 'left',
        }
    return layout


def get_line_chart_config() -> dict:
    """Get configuration for line charts."""
    return {
        'line_width': 2,
        'marker_size': 6,
        'colors': {
            'primary': COLORS['chart_blue'],
            'baseline': COLORS['text_muted'],
        }
    }


def get_bar_chart_config() -> dict:
    """Get configuration for bar charts."""
    return {
        'marker': {
            'line': {'width': 0},
        },
        'colors': CHART_COLORS,
    }


def get_pie_chart_config() -> dict:
    """Get configuration for donut/pie charts."""
    return {
        'hole': 0.6,
        'colors': CHART_COLORS,
        'textfont': {'size': 12, 'color': COLORS['text_secondary']},
    }


# ═══════════════════════════════════════════════════════════════════
# CSS HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def kpi_card_css(label: str, value: str, change: str = None, change_positive: bool = True) -> str:
    """Generate HTML for a styled KPI card."""
    change_color = COLORS['success'] if change_positive else COLORS['danger']
    arrow = '↑' if change_positive else '↓'

    change_html = ''
    if change:
        change_html = f'''
        <div style="font-size: 12px; color: {change_color}; margin-top: 4px;">
            {arrow} {change}
        </div>
        '''

    return f'''
    <div style="
        background: {COLORS['background']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 20px 24px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    ">
        <div style="
            font-size: 12px;
            text-transform: uppercase;
            color: {COLORS['text_secondary']};
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        ">{label}</div>
        <div style="
            font-size: 28px;
            font-weight: 700;
            color: {COLORS['text_primary']};
            font-family: {FONTS['mono']};
        ">{value}</div>
        {change_html}
    </div>
    '''


def section_header(title: str, subtitle: str = None) -> str:
    """Generate HTML for a section header."""
    subtitle_html = ''
    if subtitle:
        subtitle_html = f'<div style="font-size: 14px; color: {COLORS["text_secondary"]}; margin-top: 4px;">{subtitle}</div>'

    return f'''
    <div style="margin-bottom: 24px;">
        <div style="font-size: 20px; font-weight: 600; color: {COLORS['text_primary']};">{title}</div>
        {subtitle_html}
    </div>
    '''


def entity_badge(entity: str) -> str:
    """Generate HTML for an entity badge."""
    if entity.upper() == 'YAHSHUA':
        bg = COLORS['yahshua_light']
        color = '#2563EB'
    else:
        bg = COLORS['abba_light']
        color = '#7C3AED'

    return f'''
    <span style="
        background: {bg};
        color: {color};
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
    ">{entity}</span>
    '''


def alert_box(message: str, alert_type: str = 'info') -> str:
    """Generate HTML for an alert box."""
    colors = {
        'info': (COLORS['info_light'], COLORS['info']),
        'success': (COLORS['success_light'], COLORS['success']),
        'warning': (COLORS['warning_light'], COLORS['warning']),
        'error': (COLORS['danger_light'], COLORS['danger']),
    }
    bg, border = colors.get(alert_type, colors['info'])

    return f'''
    <div style="
        background: {bg};
        border-left: 4px solid {border};
        padding: 12px 16px;
        border-radius: 0 6px 6px 0;
        font-size: 14px;
        color: {COLORS['text_primary']};
        margin: 8px 0;
    ">{message}</div>
    '''
