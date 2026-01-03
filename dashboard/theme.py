"""
Apple-inspired theme for JESUS Company Cash Management Dashboard.
Clean, minimal design with generous whitespace and subtle shadows.
"""

# ═══════════════════════════════════════════════════════════════════
# COLOR PALETTE - Apple Design Language
# ═══════════════════════════════════════════════════════════════════

COLORS = {
    # Base colors
    'background': '#F5F5F7',      # Light gray page background
    'surface': '#FFFFFF',          # White card surfaces
    'border': '#E5E5E7',           # Subtle borders

    # Text colors
    'text_primary': '#1D1D1F',     # Near-black for primary text
    'text_secondary': '#86868B',   # Muted gray for secondary
    'text_muted': '#AEAEB2',       # Even lighter for tertiary

    # Accent color - Apple Blue
    'accent': '#007AFF',
    'accent_hover': '#0066D6',
    'accent_light': 'rgba(0, 122, 255, 0.1)',

    # Status colors - Apple system colors
    'success': '#34C759',
    'success_light': 'rgba(52, 199, 89, 0.1)',
    'warning': '#FF9500',
    'warning_light': 'rgba(255, 149, 0, 0.1)',
    'danger': '#FF3B30',
    'danger_light': 'rgba(255, 59, 48, 0.1)',
    'info': '#007AFF',
    'info_light': 'rgba(0, 122, 255, 0.1)',

    # Entity colors
    'yahshua': '#007AFF',
    'yahshua_light': 'rgba(0, 122, 255, 0.1)',
    'abba': '#AF52DE',             # Apple purple
    'abba_light': 'rgba(175, 82, 222, 0.1)',

    # Chart colors - Apple-inspired palette
    'chart_blue': '#007AFF',
    'chart_green': '#34C759',
    'chart_orange': '#FF9500',
    'chart_red': '#FF3B30',
    'chart_purple': '#AF52DE',
    'chart_teal': '#5AC8FA',
}

# Chart color sequence
CHART_COLORS = [
    COLORS['chart_blue'],
    COLORS['chart_green'],
    COLORS['chart_orange'],
    COLORS['chart_purple'],
    COLORS['chart_teal'],
    COLORS['chart_red'],
]

# ═══════════════════════════════════════════════════════════════════
# TYPOGRAPHY - Apple SF Pro inspired
# ═══════════════════════════════════════════════════════════════════

FONTS = {
    'primary': "-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif",
    'mono': "'SF Mono', 'Fira Code', 'JetBrains Mono', Consolas, monospace",
}

FONT_SIZES = {
    'xs': '11px',    # Labels, captions
    'sm': '13px',    # Secondary text
    'base': '15px',  # Body text
    'lg': '17px',    # Subheadings
    'xl': '22px',    # Section titles
    '2xl': '28px',   # Page titles
    '3xl': '34px',   # Large metrics
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
# SHADOWS - Subtle Apple-style
# ═══════════════════════════════════════════════════════════════════

SHADOWS = {
    'sm': '0 1px 3px rgba(0, 0, 0, 0.06)',
    'md': '0 2px 8px rgba(0, 0, 0, 0.08)',
    'lg': '0 4px 16px rgba(0, 0, 0, 0.10)',
}

# ═══════════════════════════════════════════════════════════════════
# BORDER RADIUS
# ═══════════════════════════════════════════════════════════════════

RADIUS = {
    'sm': '8px',
    'md': '12px',
    'lg': '16px',
    'xl': '20px',
}

# ═══════════════════════════════════════════════════════════════════
# PLOTLY CHART CONFIG
# ═══════════════════════════════════════════════════════════════════

def get_chart_layout(title: str = None, height: int = 400) -> dict:
    """Get Apple-styled Plotly layout configuration."""
    layout = {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {
            'family': FONTS['primary'],
            'color': COLORS['text_secondary'],
            'size': 13,
        },
        'margin': {'l': 48, 'r': 24, 't': 48, 'b': 48},
        'height': height,
        'xaxis': {
            'gridcolor': COLORS['border'],
            'linecolor': 'rgba(0,0,0,0)',
            'tickfont': {'size': 12, 'color': COLORS['text_secondary']},
            'showgrid': True,
            'gridwidth': 1,
            'zeroline': False,
        },
        'yaxis': {
            'gridcolor': COLORS['border'],
            'linecolor': 'rgba(0,0,0,0)',
            'tickfont': {'size': 12, 'color': COLORS['text_secondary']},
            'showgrid': True,
            'gridwidth': 1,
            'zeroline': False,
        },
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': -0.15,
            'xanchor': 'center',
            'x': 0.5,
            'font': {'size': 12, 'color': COLORS['text_secondary']},
            'bgcolor': 'rgba(0,0,0,0)',
        },
        'hoverlabel': {
            'bgcolor': COLORS['surface'],
            'bordercolor': COLORS['border'],
            'font': {
                'family': FONTS['primary'],
                'size': 13,
                'color': COLORS['text_primary']
            },
        },
    }
    if title:
        layout['title'] = {
            'text': title,
            'font': {
                'size': 17,
                'color': COLORS['text_primary'],
                'family': FONTS['primary']
            },
            'x': 0,
            'xanchor': 'left',
        }
    return layout


def get_line_chart_trace_style() -> dict:
    """Get styling for line chart traces."""
    return {
        'line_width': 2.5,
        'line_shape': 'spline',  # Smooth curves
    }


def get_bar_chart_trace_style() -> dict:
    """Get styling for bar chart traces."""
    return {
        'marker': {
            'cornerradius': 6,
        },
    }
