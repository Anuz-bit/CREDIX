
from dash import html
import dash_bootstrap_components as dbc
import uuid

def KPICard(title, value, subtext=None, color="primary", trend="neutral"):
    """
    Creates a standard KPI card with animation support.
    
    Args:
        title (str): The metric label.
        value (str): The main value to display.
        subtext (str, optional): Additional context (e.g. "+5% vs last month").
        color (str): Color theme (mapped to CSS variables conceptually).
        trend (str): "up", "down", or "neutral" to determine arrow.
    """
    # Generate a unique ID if needed, but for animation we use class + data attribute
    # We want to identify the value span specifically for JS to animate
    
    trend_icon = ""
    trend_class = ""
    
    if trend == "up":
        trend_icon = "↑"
        trend_class = "trend-up"
    elif trend == "down":
        trend_icon = "↓"
        trend_class = "trend-down"

    return dbc.Card(
        dbc.CardBody(
            [
                html.H6(title, className="kpi-label"),
                html.H2(
                    # We put the value in a specific span with data attribute
                    html.Span(value, className="kpi-value-animate", **{"data-value": value}),
                    className="kpi-value"
                ),
                html.P([
                    html.Span(trend_icon, className=f"{trend_class} me-1"),
                    html.Span(subtext)
                ], className="kpi-subtext") if subtext else None,
            ]
        ),
        className=f"kpi-card mb-4 border-{color}",
    )
