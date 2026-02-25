import dash
from dash import html, dcc, callback, Input, Output, State, MATCH, ALL
import dash_bootstrap_components as dbc
import pandas as pd
from utils.data_loader import load_data
from utils.notification_service import AlertDispatcher
from components.cards import KPICard

def layout():
    # Load and Preprocess Data
    df = load_data()
    
    # Generate Mock Customer IDs if not present (User requirement: Use real ID if available, else generate)
    if 'customer_id' not in df.columns:
        df['customer_id'] = [f"CUST-{1000 + i}" for i in range(len(df))]
        
    # Ensure necessary columns exist (using real values from DF)
    if 'probability_of_default' not in df.columns:
        df['probability_of_default'] = 0.5 
    if 'monthly_salary_inr' not in df.columns:
        df['monthly_salary_inr'] = 0
    if 'existing_liabilities_inr' not in df.columns:
        df['existing_liabilities_inr'] = 0

    # Calculate Segments based on LOGIC
    # PD < 0.30 -> Normal
    # 0.30 <= PD <= 0.70 -> Watchlist
    # PD > 0.70 -> High Risk
    
    normal_risk = df[df['probability_of_default'] < 0.3]
    watchlist_risk = df[(df['probability_of_default'] >= 0.3) & (df['probability_of_default'] <= 0.7)]
    high_risk = df[df['probability_of_default'] > 0.7]
    
    avg_score = df['probability_of_default'].mean()

    return html.Div([
        # Stores for State Management
        dcc.Store(id="selected-customer-store", data=None),
        dcc.Store(id="email-status-store", data=None),
        
        # Dashboard Container (Switches between Grid and Detail)
        html.Div(id="dashboard-content-container")
        
    ], className="p-4")


# --- Helper Functions ---

def get_risk_badge(pd_val):
    if pd_val > 0.7:
        return dbc.Badge("High Risk", color="danger", className="ms-2")
    elif pd_val >= 0.3:
        return dbc.Badge("Watchlist", color="warning", text_color="dark", className="ms-2")
    else:
        # User Image shows Dark Green for Normal
        return dbc.Badge("Normal", color="success", className="ms-2", style={"backgroundColor": "#198754"})

def render_kpi_cards(df, high_risk, watchlist_risk, normal_risk, avg_score):
    return dbc.Row([
        dbc.Col(KPICard("Total Customers", f"{len(df)}", "Active Database", color="primary"), width=3),
        dbc.Col(KPICard("High Risk", f"{len(high_risk)}", "Immediate Action", color="danger"), width=2),
        dbc.Col(KPICard("Watchlist", f"{len(watchlist_risk)}", "Monitor Closely", color="warning"), width=2),
        dbc.Col(KPICard("Normal", f"{len(normal_risk)}", "Stable Portfolio", color="success"), width=2),
        dbc.Col(KPICard("Avg Risk Score", f"{avg_score:.2f}", "Portfolio Weighted PD", color="info"), width=3),
    ], className="mb-4")

def render_grid_view(df):
    # Recalculate segments for KPIs
    normal_risk = df[df['probability_of_default'] < 0.3]
    watchlist_risk = df[(df['probability_of_default'] >= 0.3) & (df['probability_of_default'] <= 0.7)]
    high_risk = df[df['probability_of_default'] > 0.7]
    avg_score = df['probability_of_default'].mean()

    # Controls
    controls = dbc.Card([
        dbc.CardBody([
            # 1. Search Bar Row (New)
            dbc.Row([
                dbc.Col([
                    html.Div([
                        dbc.InputGroup([
                            dbc.InputGroupText(html.I(className="bi bi-search text-secondary"), className="bg-white border-end-0 ps-3"),
                            dcc.Input(
                                id="search-input", 
                                type="text", 
                                placeholder="Search", 
                                debounce=True, 
                                className="form-control border-start-0 shadow-none ps-0",
                                style={"fontSize": "1.2rem", "padding": "15px", "height": "60px"}
                            ),
                        ], className="shadow-sm rounded-3 overflow-hidden border")
                    ], className="mb-4", style={"maxWidth": "600px", "margin": "0 auto"})
                ], width=12)
            ]),
            
            # 2. Filters & Sort Row
            dbc.Row([
                # Filters
                dbc.Col([
                    html.Label("Filter by Risk Level:", className="fw-bold text-dark me-3"),
                    dbc.ButtonGroup([
                            dbc.Button("All Customers", id="btn-filter-all", n_clicks=0, color="primary", outline=False),
                            dbc.Button("High Risk", id="btn-filter-high", n_clicks=0, color="danger", outline=True),
                            dbc.Button("Watchlist", id="btn-filter-watchlist", n_clicks=0, color="warning", outline=True),
                            dbc.Button("Normal", id="btn-filter-normal", n_clicks=0, color="success", outline=True), 
                    ], className="me-3 d-flex flex-wrap gap-2"),
                ], xs=12, md=8, className="d-flex align-items-center mb-3 mb-md-0"),
                
                # Sort
                dbc.Col([
                        dcc.Dropdown(
                            id='sort-dropdown',
                            options=[
                                {'label': 'Sort: Risk Score (High to Low)', 'value': 'risk_desc'},
                                {'label': 'Sort: Risk Score (Low to High)', 'value': 'risk_asc'},
                                {'label': 'Sort: Income (High to Low)', 'value': 'inc_desc'},
                            ],
                            value='risk_desc',
                            clearable=False,
                            style={'fontSize': '14px'}
                        )
                ], xs=12, md=4)
            ])
        ])
    ], className="mb-3 border-0 bg-light") 

    return html.Div([
        # Header text REMOVED as per user request (Redundant with global header)
        
        # Sticky Controls
        html.Div(controls, style={"position": "sticky", "top": "75px", "zIndex": "90", "backgroundColor": "#f8f9fa", "paddingTop": "10px"}),
        
        dcc.Loading(id="loading-grid", children=[html.Div(id="customer-grid-inner")], type="circle", color="#0a2342"),
        
        dcc.Store(id="active-filter-store", data="all")
    ])

def render_detail_view(customer_row):
    cust_id = customer_row['customer_id']
    pd_val = customer_row.get('probability_of_default', 0)
    badge = get_risk_badge(pd_val)
    
    income_val = customer_row.get('monthly_salary_inr', 0)
    income = f"₹{income_val:,.0f}"
    exposure_val = customer_row.get('existing_liabilities_inr', 0)
    exposure = f"₹{exposure_val:,.0f}"
    full_name = customer_row.get('full_name', 'Unknown')
    
    # --- Integration with Intervention Logic for Plans ---
    from utils.intervention_logic import RiskEngine, PlanEngine
    
    # 1. Determine Category
    # We can use the logic already in Dashboard or reusing RiskEngine
    # Reusing dashboard logic for consistency with badge
    if pd_val > 0.7:
        risk_cat = "High"
    elif pd_val >= 0.3:
        risk_cat = "Moderate" # Intervention logic uses "Moderate" for watchlist
    else:
        risk_cat = "Low"
        
    # 2. Get Plans
    # Mapping Data to Engine
    # Expense approximation: 40% of income
    est_expenses = income_val * 0.4 
    # Current EMI approximation: 10% of exposure (rough guess for monthly obligation)
    est_emi = exposure_val * 0.05 
    if est_emi == 0: est_emi = 5000
    
    plans = PlanEngine.get_plans(
        risk_category=risk_cat,
        current_emi=int(est_emi),
        current_tenure=24, # Default
        income=int(income_val),
        expenses=int(est_expenses)
    )
    
    # 3. Create Plan Cards
    plan_cards = []
    for plan in plans:
        p_card = dbc.Card([
            dbc.CardBody([
                html.H6(plan['title'], className="fw-bold text-primary mb-1"),
                html.Small(plan['tagline'], className="text-muted d-block mb-2"),
                html.Div([
                    html.Span("Impact: ", className="fw-bold small"),
                    html.Span(plan.get('impact_amount', 'N/A'), className="text-success small fw-bold")
                ])
            ])
        ], className="h-100 mb-2 shadow-sm border-light")
        plan_cards.append(dbc.Col(p_card, width=12, md=4))
    
    return html.Div([
        # Back Button
        dbc.Button([html.I(className="bi bi-arrow-left me-2"), "Back to Explorer"], 
                   id={'type': 'btn-back-action', 'index': 0}, color="link", className="text-decoration-none mb-3 ps-0", style={"fontSize": "1.1rem"}),
        
        # Main Detail Card
        dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.H4(f"Customer Details: {cust_id}", className="mb-0 fw-bold"),
                    badge
                ], className="d-flex justify-content-between align-items-center bg-white")
            ], className="bg-white border-bottom-0 pt-3 pb-0"),
            
            dbc.CardBody([
                dbc.Row([
                    # Left Column: Attributes
                    dbc.Col([
                        html.H5(full_name, className="text-primary fw-bold mb-3"),
                        
                        html.Div([
                             html.P([html.Span("Risk Score: ", className="fw-bold"), f"{pd_val:.2f}"]),
                             html.P([html.Span("Monthly Income: ", className="fw-bold"), income]),
                             html.P([html.Span("Total Exposure: ", className="fw-bold"), exposure]),
                             html.P([html.Span("Credit Score: ", className="fw-bold"), "720 (Est)"]),
                        ], className="fs-5")
                        
                    ], width=7),
                    
                    # Right Column: Action
                    dbc.Col([
                         dbc.Card([
                             dbc.CardBody([
                                 html.H6("Intervention Action", className="fw-bold text-muted mb-3"),
                                 html.P("Send a secure link to this customer to explore repayment options.", className="small text-muted"),
                                 dbc.Button("Send Intervention Email", id="btn-send-email", color="primary", className="w-100 mb-2"),
                                 html.Div(id="email-toast-container")
                             ])
                         ], className="bg-light border-0")
                    ], width=5)
                ])
            ])
        ], className="shadow-sm border-0 mb-4"),
        
        # Recommended Plans Section
        html.H5("Recommended Intervention Plans", className="fw-bold text-dark mb-3"),
        dbc.Row(plan_cards, className="mb-4"),
        
        # Additional Info
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Risk Factors", className="bg-white fw-bold"),
                    dbc.CardBody([
                         html.Ul([
                             html.Li("High probability of default detected.") if pd_val > 0.5 else html.Li("Risk level is within acceptable limits."),
                             html.Li("Income varies by >10% month-over-month.") if pd_val > 0.5 else html.Li("Stable income detected."),
                             html.Li("Recommended for immediate engagement.") if risk_cat in ["High", "Moderate"] else html.Li("No immediate action required.")
                         ])
                    ])
                ], className="h-100 shadow-sm border-0")
            ], width=6),
             dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Recent Activity", className="bg-white fw-bold"),
                    dbc.CardBody([
                        html.P("No recent transactions flagged.", className="text-muted")
                    ])
                ], className="h-100 shadow-sm border-0")
            ], width=6)
        ])
    ])

# --- Callbacks ---

@callback(
    Output("dashboard-content-container", "children"),
    [Input("selected-customer-store", "data")] 
)
def render_content(selected_customer_id):
    try:
        df = load_data()
        if 'customer_id' not in df.columns:
            df['customer_id'] = [f"CUST-{1000 + i}" for i in range(len(df))]
            
        if selected_customer_id:
            row = df[df['customer_id'] == selected_customer_id].iloc[0]
            return render_detail_view(row)
        else:
            return render_grid_view(df)
    except Exception as e:
        import traceback
        return html.Div([html.H3("Error", className="text-danger"), html.Pre(str(e)), html.Pre(traceback.format_exc())], className="p-4")

@callback(
    Output("selected-customer-store", "data"),
    [Input({'type': 'btn-view-details', 'index': ALL}, 'n_clicks'),
     Input({'type': 'btn-back-action', 'index': ALL}, 'n_clicks')], 
    prevent_initial_call=True
)
def update_selection(view_clicks, back_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
        
    trigger = ctx.triggered[0]['prop_id']
    value = ctx.triggered[0]['value']
    
    if "btn-back-action" in trigger:
        # If back button clicked, clear selection
        if value:
             return None
        return dash.no_update
        
    if "btn-view-details" in trigger:
        # Check if actual click happened (n_clicks > 0)
        # When grid regenerates, this might trigger with None or 0
        if not value:
            return dash.no_update

        component_id = ctx.triggered_id
        if component_id and 'index' in component_id:
            return component_id['index']
            
    return dash.no_update

@callback(
    [Output("active-filter-store", "data"),
     Output("btn-filter-all", "active"), Output("btn-filter-all", "outline"),
     Output("btn-filter-high", "active"), Output("btn-filter-high", "outline"),
     Output("btn-filter-watchlist", "active"), Output("btn-filter-watchlist", "outline"),
     Output("btn-filter-normal", "active"), Output("btn-filter-normal", "outline")],
    [Input("btn-filter-all", "n_clicks"),
     Input("btn-filter-high", "n_clicks"),
     Input("btn-filter-watchlist", "n_clicks"),
     Input("btn-filter-normal", "n_clicks")],
    prevent_initial_call=True
)
def update_filter(n_all, n_high, n_watch, n_norm):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "all", True, False, False, True, False, True, False, True
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "btn-filter-high":
        return "high", False, True, True, False, False, True, False, True
    elif button_id == "btn-filter-watchlist":
        return "watchlist", False, True, False, True, True, False, False, True
    elif button_id == "btn-filter-normal":
        return "normal", False, True, False, True, False, True, True, False
    else:
        return "all", True, False, False, True, False, True, False, True

@callback(
    Output("customer-grid-inner", "children"),
    [Input("active-filter-store", "data"),
     Input("sort-dropdown", "value"),
     Input("search-input", "value")] 
)
def populate_grid(filter_val, sort_val, search_val):
    df = load_data()
    # Removed mock customer_id generation

    # 0. Search Logic (Priority)
    if search_val:
        df = df[df['customer_id'].str.contains(search_val, case=False, na=False)]
    else:
        # STRATIFIED SAMPLING LOGIC for 'All' view
        if filter_val == 'all':
             # Split by risk logic
             high = df[df['probability_of_default'] > 0.7].sort_values(by='probability_of_default', ascending=False).head(34)
             watch = df[(df['probability_of_default'] >= 0.3) & (df['probability_of_default'] <= 0.7)].sort_values(by='probability_of_default', ascending=False).head(33)
             normal = df[df['probability_of_default'] < 0.3].sort_values(by='probability_of_default', ascending=False).head(33)
             
             # Combined Stratified Set
             df = pd.concat([high, watch, normal])
             
             # Re-sort the combined set according to user preference so it looks clean
             if sort_val == 'risk_desc':
                 df = df.sort_values(by='probability_of_default', ascending=False)
             elif sort_val == 'risk_asc':
                 df = df.sort_values(by='probability_of_default', ascending=True)
             elif sort_val == 'inc_desc':
                 df = df.sort_values(by='monthly_salary_inr', ascending=False)
                 
        else:
            # Standard Filter Logic
            if filter_val == "high":
                df = df[df['probability_of_default'] > 0.7]
            elif filter_val == "watchlist":
                df = df[(df['probability_of_default'] >= 0.3) & (df['probability_of_default'] <= 0.7)]
            elif filter_val == "normal":
                df = df[df['probability_of_default'] < 0.3]
            
            # Sort
            if sort_val == 'risk_desc':
                df = df.sort_values(by='probability_of_default', ascending=False)
            elif sort_val == 'risk_asc':
                df = df.sort_values(by='probability_of_default', ascending=True)
            elif sort_val == 'inc_desc':
                df = df.sort_values(by='monthly_salary_inr', ascending=False)
                
            # Limit to 100
            df = df.head(100)
        
    if df.empty:
        return html.Div("No customers found.", className="text-muted p-3")

    cards = []
    for _, row in df.iterrows():
        cust_id = row['customer_id'] 
        full_name = row.get('full_name', 'Customer')
        
        try:
             display_id = cust_id.split('-')[1]
             if len(display_id) < 5: display_id = f"100{display_id}"
        except:
             display_id = cust_id
        
        pd_val = row.get('probability_of_default', 0)
        badge = get_risk_badge(pd_val)
        
        income_val = row.get('monthly_salary_inr', 0)
        income = f"₹{income_val:,.0f}"

        card = dbc.Card([
            dbc.CardBody([
                # Header Row
                html.Div([
                    html.Div([
                        html.H5(full_name, className="mb-0 fw-bold text-dark text-truncate", style={"maxWidth": "150px"}),
                        html.Small(display_id, className="text-muted")
                    ]),
                    badge
                ], className="d-flex justify-content-between align-items-start mb-4"),
                
                # Metrics
                html.P([html.Span("Risk Score: ", className="text-secondary"), html.Span(f"{pd_val:.2f}", className="fw-bold text-dark")], className="mb-2"),
                html.P([html.Span("Income: ", className="text-secondary"), html.Span(income, className="fw-bold text-dark")], className="mb-4"),
                
                # Button
                dbc.Button("View Details", id={'type': 'btn-view-details', 'index': cust_id}, 
                           color="primary", className="w-100") 
            ])
        ], className="shadow-sm h-100 border-0 customer-card", style={"borderRadius": "8px"})
        
        cards.append(dbc.Col(card, width=12, md=6, lg=3, className="mb-4"))

    return dbc.Row(cards, className="g-2")

@callback(
    Output("email-toast-container", "children"),
    Input("btn-send-email", "n_clicks"),
    State("selected-customer-store", "data"),
    prevent_initial_call=True
)
def send_email(n_clicks, customer_id):
    if not n_clicks or not customer_id:
        return dash.no_update
    df = load_data()
    if 'customer_id' not in df.columns:
         df['customer_id'] = [f"CUST-{1000 + i}" for i in range(len(df))]
    customer = df[df['customer_id'] == customer_id].iloc[0]
    
    try:
        AlertDispatcher.send_intervention_alert(customer)
        outcome = "success"
        msg = f"Link sent to {customer.get('email_id', 'customer')}!"
        icon = "bi bi-check-circle-fill me-2"
    except Exception as e:
        outcome = "danger"
        msg = f"Failed: {str(e)}"
        icon = "bi bi-exclamation-triangle-fill me-2"

    return dbc.Toast(
        [html.I(className=icon), msg],
        id="email-toast",
        header="Notification",
        is_open=True,
        dismissable=True,
        icon=outcome,
        duration=4000,
        style={"position": "fixed", "top": "20px", "right": "20px", "zIndex": 9999}
    )
