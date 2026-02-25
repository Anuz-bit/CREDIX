from dash import html, dcc, callback, Input, Output, State, no_update, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from utils.data_loader import load_data
from utils.intervention_logic import RiskEngine, PlanEngine, OutcomeLogger, CommunicationEngine
import urllib.parse

# --- Styling Constants ---
NAVY_BLUE = "#0a2342"
CORPORATE_BLUE = "#1F4E79"
WHITE = "#ffffff"
LIGHT_GREY = "#f8f9fa"
SUCCESS_GREEN = "#28a745"
TEXT_GREY = "#6c757d"

# --- Main Layout Container ---
# We use a wrapper to allow dynamic updates based on URL params (Token)
def layout():
    return html.Div([
        dcc.Location(id='intervention-url', refresh=False),
        html.Div(id='intervention-page-content')
    ])

# --- Content Generation ---
def render_intervention_page(token=None):
    # 1. Resolve Customer
    customer = None
    
    if token:
        print(f"Resolving token: {token}")
        customer_data = CommunicationEngine.get_customer_by_token(token)
        if customer_data:
            # Convert dict back to Series-like object/dict for compatibility
            customer = customer_data
            
            # LOG OPEN EVENT
            try:
                # Avoid duplicate logging if reloaded quickly? For now, log every open to verify functionality.
                OutcomeLogger.log_outcome(customer.get('customer_id'), "N/A", "OPENED")
            except:
                pass
    
    # Fallback/Demo Mode if no token or invalid
    if customer is None:
        df = load_data()
        if not df.empty:
            # Default to a high risk customer for demo
            high_risk = df[df['probability_of_default'] > 0.6]
            if not high_risk.empty:
                customer = high_risk.iloc[0].to_dict()
            else:
                customer = df.iloc[0].to_dict()

    if not customer:
        return html.Div("System Error: No customer data available.", className="p-5 text-center text-danger")

    # Extract Data safely
    # Customer can be dict or Series, handle both
    def get_val(key, default):
        return customer.get(key, default) if isinstance(customer, dict) else customer.get(key, default)

    full_name = get_val('full_name', get_val('name', 'Valued Customer'))
    customer_id = get_val('customer_id', 'UNKNOWN')
    
    # Logic
    risk_category = RiskEngine.get_risk_category(customer)
    reasons = RiskEngine.get_risk_reasons(customer)
    plans = PlanEngine.get_plans(risk_category)
    stability_points = RiskEngine.get_stability_points(customer)
    
    # Financial Metrics
    pd_val = get_val('probability_of_default', 0.0)
    risk_score = int(pd_val * 100) # Convert 0.75 to 75
    cibil_score = get_val('bureau_score', get_val('cibil_score', 750)) # Fallback to 750 if missing
    
    # Financial Health Status
    health_status = "Needs Attention" if risk_category in ["High", "Moderate"] else "Stable"
    health_color = "#dc3545" if risk_category == "High" else "#ffc107" if risk_category == "Moderate" else "#28a745"

    # --- Components ---



    # Greeting
    greeting_section = html.Div([
        html.H3(f"Hi, {full_name.split()[0]}", className="fw-bold"),
        html.P("We have prepared some personalized options to support your financial goals.", className="text-muted lead")
    ], className="mb-4")

    # Section A: Reasons
    reason_items = [html.Li(r, className="mb-2") for r in reasons]
    section_a = dbc.Card([
        dbc.CardHeader("Why we sent this message", style={"backgroundColor": "transparent", "fontWeight": "bold", "borderBottom": "none"}),
        dbc.CardBody([
            html.Ul(reason_items, style={"paddingLeft": "1.2rem", "color": "#444"})
        ])
    ], className="mb-4 shadow-sm border-0")

    # Section B: Health
    section_b = dbc.Card([
        dbc.CardBody([
            html.H6("FINANCIAL HEALTH SUMMARY", className="text-muted small mb-2"),
            html.H3(health_status, style={"color": health_color, "fontWeight": "bold"}),
            html.P(["Status as of ", html.Span("Today", style={"fontWeight": "bold"})], className="text-muted small mt-2 mb-0"),
            html.Hr(),
            
            # Scores Row
            dbc.Row([
                dbc.Col([
                    html.Small("RISK SCORE", className="text-muted fw-bold"),
                    html.H4(f"{risk_score}/100", className="mb-0", style={"color": health_color})
                ], width=6, className="text-center border-end"),
                dbc.Col([
                    html.Small("CIBIL SCORE", className="text-muted fw-bold"),
                    html.H4(f"{cibil_score}", className="mb-0 text-primary")
                ], width=6, className="text-center")
            ], className="mt-3"),
            
            # Stability Points Display
            html.Div([
                html.Hr(),
                html.H6("STABILITY REWARDS SCORE", className="text-muted small mb-2"),
                html.H3(f"{stability_points} 🏆", className="text-primary fw-bold"),
                html.Small("You are unlocking premium benefits!", className="text-success")
            ]) if stability_points > 0 else None
        ])
    ], className="mb-4 shadow-sm border-0")

    # Section C: Plan Cards
    
    # Helper to create a card col
    def create_plan_card(plan):
        is_reward = plan.get('type') == 'Stability Reward'
        border_style = {"border": "2px solid #ffc107"} if is_reward else {"border": "0"}
        
        card = dbc.Card([
            dbc.CardBody([
                dbc.Badge(plan['type'].upper(), color="warning" if is_reward else "info", className="mb-2", style={"fontSize": "0.7rem"}),
                html.H5(plan['title'], className="card-title fw-bold"),
                html.P(plan['tagline'], className="text-muted small mb-3"),
                
                html.Div([
                    html.Span("Estimated Relief:" if not is_reward else "Benefit Value:", className="d-block small text-muted"),
                    html.Span(plan.get('impact_amount', 'N/A'), className="fw-bold fs-5 text-success")
                ], className="mb-3 p-2 bg-light rounded text-center"),

                dbc.Button("View Details", id={"type": "view-details-btn", "index": plan['id']}, color="primary", outline=True, className="w-100")
            ])
        ], className="mb-3 shadow-sm h-100 hover-card", style=border_style)
        return dbc.Col(card, md=4, className="mb-3")

    # Split Plans
    reward_plans = [p for p in plans if p.get('type') == "Stability Reward"]
    standard_plans = [p for p in plans if p.get('type') != "Stability Reward"]

    plan_cards_standard = [create_plan_card(p) for p in standard_plans]
    plan_cards_reward = [create_plan_card(p) for p in reward_plans]

    dashboard_view = html.Div([
        greeting_section,
        dbc.Row([
            dbc.Col(section_a, md=7),
            dbc.Col(section_b, md=5),
        ]),
        html.Hr(className="my-4"),
        
        # Standard Plans
        html.H4("Recommended Plans", className="mb-3", style={"color": NAVY_BLUE}) if plan_cards_standard else None,
        dbc.Row(plan_cards_standard) if plan_cards_standard else (html.P("No standard plans recommended.") if not plan_cards_reward else None),
        
        # Reward Plans Section
        html.Div([
            html.Hr(className="my-4"),
            html.H4("Recommended Plans (For Stability Rewards Customers)", className="mb-3 text-warning fw-bold"),
            dbc.Row(plan_cards_reward)
        ]) if plan_cards_reward else None,
        
        # Support Block
        dbc.Row([
            dbc.Col([
                html.H5("We are here to help", className="fw-bold mt-5"),
                html.P("These options are proactive support. No negative impact to your credit score for viewing.", className="text-muted small"),
            ])
        ])
    ], id="dashboard-view")

    # --- VIEW 2: PLAN DETAILS (Hidden by default) ---
    details_view = html.Div(id="details-view-container", style={"display": "none"})

    # --- Data Stores ---
    store_plans = dcc.Store(id="plans-store", data=plans)
    
    # Modal for success
    modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Plan Accepted")),
        dbc.ModalBody("Thank you. Your request has been logged. You will receive a confirmation email shortly."),
        dbc.ModalFooter(dbc.Button("Close", id="close-modal-success", className="ms-auto", n_clicks=0))
    ], id="success-modal-interactive", is_open=False)

    return html.Div([

        dbc.Container([
            dashboard_view,
            details_view,
            store_plans,
            modal,
            dcc.Store(id="customer-id-store-2", data=str(customer_id))
        ], fluid="md", style={"maxWidth": "960px", "fontFamily": "'Segoe UI', sans-serif"})
    ], style={"backgroundColor": "#f4f6f8", "minHeight": "100vh"})


# --- CALLBACKS ---

# 1. URL Parser Callback
@callback(
    Output('intervention-page-content', 'children'),
    Input('intervention-url', 'search')
)
def display_intervention_content(search):
    token = None
    if search:
        # Simple parse: ?token=123
        try:
            query = urllib.parse.parse_qs(search.lstrip('?'))
            token = query.get('token', [None])[0]
        except:
            pass
    
    return render_intervention_page(token)


# 2. View Toggler
@callback(
    [Output("dashboard-view", "style"),
     Output("details-view-container", "style"),
     Output("details-view-container", "children")],
    [Input({"type": "view-details-btn", "index": ALL}, "n_clicks"),
     Input({"type": "back-btn", "index": ALL}, "n_clicks")],
    [State("plans-store", "data")]
)
def toggle_views(n_clicks_view, n_clicks_back, plans_data):
    from dash import callback_context
    ctx = callback_context

    if not ctx.triggered:
        return no_update

    button_id_str = ctx.triggered[0]['prop_id'].split('.')[0]
    
    import json
    try:
        button_id = json.loads(button_id_str)
        action_type = button_id.get('type')
        plan_id = button_id.get('index')
    except:
        return no_update

    if action_type == "view-details-btn":
        selected_plan = next((p for p in plans_data if p['id'] == plan_id), None)
        if not selected_plan:
            return no_update
        
        detail_layout = build_detail_layout(selected_plan)
        return {"display": "none"}, {"display": "block", "animation": "fadeIn 0.3s"}, detail_layout

    elif action_type == "back-btn":
        return {"display": "block", "animation": "fadeIn 0.3s"}, {"display": "none"}, no_update

    return no_update

# 3. Acceptance/Detail Builder
def build_detail_layout(plan):
    sim = plan.get('simulation')
    
    # 1. VISUALIZATIONS
    charts = []
    if sim:
        # EMI Comparison Chart
        fig_emi = go.Figure(data=[
            go.Bar(name='Current EMI', x=['Payments'], y=[sim['current_emi']], marker_color='#6c757d'),
            go.Bar(name='New EMI', x=['Payments'], y=[sim['new_emi']], marker_color=SUCCESS_GREEN)
        ])
        fig_emi.update_layout(title="Monthly Payment Comparison", barmode='group', height=300, template="plotly_white", showlegend=True)
        
        # Cashflow Stack
        cf = sim['cashflow']
        fig_cf = go.Figure()
        fig_cf.add_trace(go.Bar(y=['Cashflow'], x=[cf['expenses']], name='Expenses', orientation='h', marker_color='#dc3545'))
        fig_cf.add_trace(go.Bar(y=['Cashflow'], x=[sim['new_emi']], name='New EMI', orientation='h', marker_color=CORPORATE_BLUE))
        fig_cf.add_trace(go.Bar(y=['Cashflow'], x=[cf['new_balance']], name='Savings/Balance', orientation='h', marker_color=SUCCESS_GREEN))
        fig_cf.update_layout(title="Estimated Monthly Cashflow", barmode='stack', height=250, template="plotly_white")

        charts = [
            html.H5("Visual Impact", className="mb-3 mt-4 text-muted"),
            dbc.Row([
                dbc.Col(dcc.Graph(figure=fig_emi, config={'displayModeBar': False}), md=6),
                dbc.Col(dcc.Graph(figure=fig_cf, config={'displayModeBar': False}), md=6),
            ])
        ]
    
    # 2. METRICS CARDS
    metrics = []
    if sim:
        metrics = dbc.Row([
            dbc.Col(html.Div([
                html.Small("New Monthly EMI", className="text-muted"),
                html.H4(f"₹{sim['new_emi']:,}", className="text-primary fw-bold")
            ], className="border p-3 rounded bg-white text-center"), width=6, md=3),
             dbc.Col(html.Div([
                html.Small("Estimated Savings", className="text-muted"),
                html.H4(f"₹{sim['monthly_relief']:,}", className="text-success fw-bold")
            ], className="border p-3 rounded bg-white text-center"), width=6, md=3),
             dbc.Col(html.Div([
                html.Small("Tenure Change", className="text-muted"),
                html.H4(f"+{sim['new_tenure'] - sim['current_tenure']} Months", className="text-warning fw-bold")
            ], className="border p-3 rounded bg-white text-center"), width=6, md=3),
        ], className="mb-4 g-2")

    return html.Div([
        # Header with Back Button
        html.Div([
            dbc.Button("← Back to Plans", id={"type": "back-btn", "index": "bg"}, color="link", className="p-0 text-decoration-none mb-2"),
            html.H2(plan['title'], className="fw-bold", style={"color": NAVY_BLUE}),
            html.P(plan['description'], className="lead text-muted")
        ], className="mb-4"),

        # Metrics
        metrics,

        # Condition / Overview
        dbc.Card([
            dbc.CardBody([
                html.H5("Why this plan?", className="fw-bold"),
                html.P(plan['reason']),
                html.Hr(),
                html.H6("Eligibility Checks Passed:", className="text-success fw-bold"),
                html.Ul([html.Li(e) for e in plan.get('eligibility', [])]),
                html.H6("Important Conditions:", className="text-warning fw-bold"),
                html.Ul([html.Li(c) for c in plan.get('conditions', [])]),
            ])
        ], className="mb-4 shadow-sm border-0"),
        
        # Charts
        *charts,

        # Action Bar (Sticky Bottom)
        html.Div([
            dbc.Container([
                dbc.Row([
                    dbc.Col(
                         dbc.Button("Accept This Plan", id={"type": "accept-final-btn", "index": plan['id']}, color="primary", className="w-100 py-3 fw-bold", style={"backgroundColor": NAVY_BLUE}),
                         width=12, md=8
                    ),
                     dbc.Col(
                         dbc.Button("Compare Plans", color="light", className="w-100 py-3 border"),
                         width=12, md=4
                    )
                ], className="align-items-center")
            ])
        ], className="fixed-bottom bg-white border-top p-3 shadow-lg", style={"zIndex": 1000})
        
    ], className="pb-5 mb-5")


@callback(
    Output("success-modal-interactive", "is_open"),
    [Input({"type": "accept-final-btn", "index": ALL}, "n_clicks"), Input("close-modal-success", "n_clicks")],
    [State("success-modal-interactive", "is_open"), State("customer-id-store-2", "data")],
    prevent_initial_call=True
)
def handle_final_acceptance(n_accept, n_close, is_open, customer_id):
    from dash import callback_context
    ctx = callback_context
    if not ctx.triggered: return no_update

    button_id_str = ctx.triggered[0]['prop_id'].split('.')[0]
    if "close-modal-success" in button_id_str:
        return False
        
    # LOG LOGIC
    import json
    try:
        button_id = json.loads(button_id_str)
        if button_id.get('type') == 'accept-final-btn':
            # Check for truthy click
            clicked_value = ctx.triggered[0]['value']
            if not clicked_value:
                return no_update

            OutcomeLogger.log_outcome(customer_id, button_id.get('index'), "ACCEPTED_FROM_DETAILS")
            return True
    except:
        pass
        
    return is_open