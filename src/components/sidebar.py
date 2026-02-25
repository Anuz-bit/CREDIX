import dash_bootstrap_components as dbc
from dash import html

def Sidebar():
    """Returns the sidebar component."""
    return html.Div(
        [
            html.Div(
                [
                    html.H2("CREDIX", className="display-4", style={'color': 'white', 'fontWeight': 'bold', 'fontSize': '24px'}),
                    html.P("Pre-Delinquency Engine", className="lead", style={'color': '#8ca6cc', 'fontSize': '12px'}),
                ],
                className="sidebar-header"
            ),
            html.Hr(style={'borderColor': 'rgba(255,255,255,0.1)'}),
            dbc.Nav(
                [
                    dbc.NavLink("Executive Portfolio", href="/", active="exact"),
                    
                    dbc.NavLink("Risk Analyst", href="/risk", active="exact"),

                    dbc.NavLink("Operations / Collections", href="/operations", active="exact"),

                    html.Hr(style={'borderColor': 'rgba(255,255,255,0.1)'}),
                    dbc.NavLink("Customer Explorer", href="/customer-dashboard", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
            html.Div(
                [
                    html.P("System Status: Online", style={'color': '#28a745', 'fontSize': '10px', 'marginTop': '20px'}),
                    html.P("Last Model Run: Today", style={'color': '#8ca6cc', 'fontSize': '10px'}),
                ],
                style={'marginTop': 'auto'}
            )
        ],
        className="sidebar",
    )
