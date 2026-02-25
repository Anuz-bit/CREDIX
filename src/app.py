import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output, State

# Import Components & Pages
from components.sidebar import Sidebar
from pages import executive, risk, operations, intervention, customer_dashboard, intervention_low, intervention_moderate

# Initialize App
app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)
app.title = "CREDIX - Pre-Delinquency Engine"

# Define Layout
app.layout = html.Div(
    [
        dcc.Store(id="sidebar-state", data=True),
        dcc.Location(id="url"),
        html.Div(Sidebar(), id="sidebar-container"),
        
        # Main Content Wrapper (Header + Page Content)
        html.Div([
            # Header Band
            html.Div([
                dbc.Button("☰", id="btn-sidebar-toggle", style={"fontSize": "1.2rem", "border": "none", "backgroundColor": "#001f3f", "color": "white"}, className="me-3"),
                html.H4(id="page-title-header", className="mb-0", style={"color": "#FFFFFF", "fontWeight": "bold"})
            ], className="d-flex align-items-center shadow-sm p-3 sticky-top", style={"zIndex": 100, "backgroundColor": "#001f3f"}),

            # Page Content
            html.Div(id="page-content", className="p-2")
        ], id="content-wrapper", className="content")
    ]
)

# Sidebar Toggle & Header Callback
@app.callback(
    [Output("sidebar-container", "style"),
     Output("content-wrapper", "style"),
     Output("sidebar-state", "data"),
     Output("btn-sidebar-toggle", "style"),
     Output("page-title-header", "children")],
    [Input("url", "pathname"),
     Input("btn-sidebar-toggle", "n_clicks")],
    [State("sidebar-state", "data")]
)
def update_layout_state(pathname, n_clicks, is_open):
    # 1. Determine Title
    title = "CREDIX Dashboard"
    if pathname == "/" or pathname == "/executive": title = "Executive Portfolio Dashboard"
    elif pathname == "/risk": title = "Risk Analyst Dashboard"
    elif pathname == "/operations": title = "Operations & Collections Dashboard"

    elif pathname == "/customer-dashboard": title = "Customer Explorer"
    
    # 2. Intervention Logic (Always Full Screen)
    if pathname and ("/intervention" in pathname or "/customer/intervention" in pathname):
        return {'display': 'none'}, {'marginLeft': '0'}, False, {'display': 'none'}, "Customer Intervention Portal"

    # 3. Toggle Logic
    ctx = dash.callback_context
    if ctx.triggered:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger_id == "btn-sidebar-toggle":
            is_open = not is_open
            
    # 4. Apply Styles
    if is_open:
        sidebar_style = {'display': 'block'}
        content_style = {'marginLeft': '18rem', 'transition': 'margin-left 0.3s'}
        btn_style = {'display': 'block'} # Button always visible to close
    else:
        sidebar_style = {'display': 'none'}
        content_style = {'marginLeft': '0', 'transition': 'margin-left 0.3s'}
        btn_style = {'display': 'block'} # Button always visible to open

    return sidebar_style, content_style, is_open, btn_style, title

# Page Router
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/" or pathname == "/executive":
        return executive.layout()
    elif pathname == "/risk":
        return risk.layout()
    elif pathname == "/risk/customer-dashboard" or pathname == "/customer-dashboard":
        return customer_dashboard.layout()
    elif pathname == "/operations":
        return operations.layout()
    elif pathname == "/intervention" or pathname == "/customer/intervention":
        return intervention.layout()
    elif pathname == "/customer/intervention1":
        return intervention_low.layout()
    elif pathname == "/customer/intervention2":
        return intervention_moderate.layout()
    else:
        # Default to executive if unknown
        return executive.layout()

if __name__ == "__main__":
    app.run(debug=True, port=8050)
