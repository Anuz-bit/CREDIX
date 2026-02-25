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
GOLD = "#FFD700"

# --- Main Layout Container ---
def layout():
    return html.Div([
        dcc.Location(id='intervention-low-url', refresh=False),
        html.Div(id='intervention-low-page-content')
    ])

# --- Content Generation ---
def render_intervention_page(token=None):
    # 1. Resolve Customer
    customer = None
    
    if token:
        try:
            customer_data = CommunicationEngine.get_customer_by_token(token)
            if customer_data:
                customer = customer_data
                OutcomeLogger.log_outcome(customer.get('customer_id'), "N/A", "OPENED_LOW")
        except:
            pass
    
    # Fallback/Demo Mode: Select a LOW risk customer
    if customer is None:
        df = load_data()
        if not df.empty:
            # Low risk: PD < 0.2
            low_risk = df[df['probability_of_default'] < 0.2]
            if not low_risk.empty:
                customer = low_risk.iloc[0].to_dict()
            else:
                # Fallback to first if no low risk found, but force low risk values for display if needed
                customer = df.iloc[0].to_dict()
                customer['probability_of_default'] = 0.05 # Force low risk

    if not customer:
        return html.Div("System Error: No customer data available.", className="p-5 text-center text-danger")

    # Extract Data safely
    def get_val(key, default):
        return customer.get(key, default) if isinstance(customer, dict) else customer.get(key, default)

    full_name = get_val('full_name', get_val('name', 'Valued Customer'))
    customer_id = get_val('customer_id', 'UNKNOWN')
    
    # Logic - Force Low Risk context for this page if needed, or just display as is
    # The requirement says this page represents a Low-Risk profile.
    
    # Financial Metrics
    pd_val = get_val('probability_of_default', 0.1)
    risk_score = int(pd_val * 100) # Low score is good? Usually low PD means low risk.
    # If Risk Score is 0-100 where 100 is high risk, then low PD (0.1) -> 10.
    # If Risk Score is Credit Score-like, it's different.
    # Looking at intervention.py: risk_score = int(pd_val * 100). So 0-100 scale.
    
    cibil_score = get_val('bureau_score', get_val('cibil_score', 820))
    stability_points = RiskEngine.get_stability_points(customer)
    if stability_points < 50: stability_points = 85 # Demo value for low risk

    # Specific Metrics for Low Risk
    emi_consistency = "100% On-Time"
    savings_trend = "+12% YoY"

    # --- Components ---

    # Greeting
    greeting_section = html.Div([
        html.H3(f"Congratulations, {full_name.split()[0]}!", className="fw-bold text-success"),
        html.P("Your excellent financial health qualifies you for exclusive premium benefits.", className="text-muted lead")
    ], className="mb-4")

    # Rewards Section (Replacing Reasons)
    rewards_list = [
        "Qualified for Reduced Interest Rates",
        "Pre-approved for Higher Credit Limits",
        "Priority Customer Support Access"
    ]
    rewards_items = [html.Li(r, className="mb-2") for r in rewards_list]
    
    section_a = dbc.Card([
        dbc.CardHeader("Your Elite Status Benefits", style={"backgroundColor": "transparent", "fontWeight": "bold", "borderBottom": "none", "color": CORPORATE_BLUE}),
        dbc.CardBody([
            html.Ul(rewards_items, style={"paddingLeft": "1.2rem", "color": "#444"})
        ])
    ], className="mb-4 shadow-sm border-0")

    # Section B: Health (Modified for Low Risk)
    section_b = dbc.Card([
        dbc.CardBody([
            html.H6("FINANCIAL HEALTH SUMMARY", className="text-muted small mb-2"),
            html.H3("Excellent", style={"color": SUCCESS_GREEN, "fontWeight": "bold"}),
            html.P(["Risk Band: ", html.Span("Low Risk", style={"fontWeight": "bold", "color": SUCCESS_GREEN})], className="text-muted mt-2 mb-0"),
            html.Hr(),
            
            # Scores Row
            dbc.Row([
                dbc.Col([
                    html.Small("RISK SCORE", className="text-muted fw-bold"),
                    html.H4(f"{risk_score}/100", className="mb-0", style={"color": SUCCESS_GREEN})
                ], width=4, className="text-center border-end"),
                 dbc.Col([
                    html.Small("CIBIL SCORE", className="text-muted fw-bold"),
                    html.H4(f"{cibil_score}", className="mb-0 text-primary")
                ], width=4, className="text-center border-end"),
                dbc.Col([
                    html.Small("STABILITY PTS", className="text-muted fw-bold"),
                    html.H4(f"{stability_points} 🏆", className="mb-0 text-warning")
                ], width=4, className="text-center")
            ], className="mt-3"),
            
            html.Hr(),
            # Extra Low Risk Metrics
             dbc.Row([
                dbc.Col([
                    html.Small("EMI CONSISTENCY", className="text-muted fw-bold d-block"),
                    html.Span(emi_consistency, className="badge bg-success p-2 mt-1")
                ], width=6, className="text-center"),
                 dbc.Col([
                    html.Small("SAVINGS TREND", className="text-muted fw-bold d-block"),
                     html.Span(savings_trend, className="badge bg-info text-dark p-2 mt-1")
                ], width=6, className="text-center"),
            ], className="mt-2"),
        ])
    ], className="mb-4 shadow-sm border-0")

    # Section C: Reward Plans
    # We define specific reward plans here as requested
    reward_plans_data = [
        {
            "id": "rw_1",
            "type": "Premium Offer",
            "title": "Interest Rate Reduction",
            "tagline": "Slash your interest rates on future loans.",
            "impact_amount": "2.5% Lower",
            "description": "As a valued low-risk customer, you are eligible for a significantly reduced interest rate on your next personal or vehicle loan.",
            "reason": "Reward for consistent on-time payments.",
            "eligibility": ["CIBIL > 750", "No defaults in last 24 months"],
            "conditions": ["Valid for 90 days"]
        },
        {
            "id": "rw_2",
            "type": "Credit Limit",
            "title": "2x Credit Limit Boost",
            "tagline": "Instant approval for higher spending power.",
            "impact_amount": "₹5,00,000",
            "description": "Double your current credit card limit with zero paperwork. Enjoy greater financial freedom.",
            "reason": "High credit utilization stability.",
            "eligibility": ["Income stability verified", "Risk Score < 20"],
            "conditions": ["Subject to final confirmation"]
        },
         {
            "id": "rw_3",
            "type": "Service",
            "title": "Priority Support & Processing",
            "tagline": "Skip the queue for all services.",
            "impact_amount": "Instant",
            "description": "Get a dedicated relationship manager and priority processing for all your banking needs.",
            "reason": "Elite customer tier benefit.",
            "eligibility": ["Maintain Stability Points > 80"],
            "conditions": ["Annual renewable benefit"]
        }
    ]

    def create_reward_card(plan):
        card = dbc.Card([
            dbc.CardBody([
                dbc.Badge("REWARD", color="warning", text_color="dark", className="mb-2"),
                html.H5(plan['title'], className="card-title fw-bold text-dark"),
                html.P(plan['tagline'], className="text-muted small mb-3"),
                
                html.Div([
                    html.Span("Benefit Value:", className="d-block small text-muted"),
                    html.Span(plan['impact_amount'], className="fw-bold fs-5 text-success")
                ], className="mb-3 p-2 bg-light rounded text-center"),

                dbc.Button("Claim Offer", id={"type": "view-details-low-btn", "index": plan['id']}, color="primary", className="w-100", style={"backgroundColor": NAVY_BLUE})
            ])
        ], className="mb-3 shadow-sm h-100 hover-card border-warning", style={"borderWidth": "2px"})
        return dbc.Col(card, md=4, className="mb-3")

    plan_cards = [create_reward_card(p) for p in reward_plans_data]

    dashboard_view = html.Div([
        greeting_section,
        dbc.Row([
            dbc.Col(section_a, md=6),
            dbc.Col(section_b, md=6),
        ]),
        html.Hr(className="my-4"),
        
        # Reward Plans
        html.H4("Recommended Rewards & Offers", className="mb-3", style={"color": NAVY_BLUE}),
        dbc.Row(plan_cards),
        
    ], id="dashboard-view-low")

    # --- VIEW 2: PLAN DETAILS (Hidden by default) ---
    details_view = html.Div(id="details-view-low-container", style={"display": "none"})

    # --- Data Stores ---
    store_plans = dcc.Store(id="plans-store-low", data=reward_plans_data)
    
    # Modal
    modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Offer Claimed!", className="text-success")),
        dbc.ModalBody("Congratulations! This offer has been activated on your account. You will receive a confirmation message shortly."),
        dbc.ModalFooter(dbc.Button("Close", id="close-modal-success-low", className="ms-auto", n_clicks=0))
    ], id="success-modal-low", is_open=False)

    return html.Div([
        dbc.Container([
            dashboard_view,
            details_view,
            store_plans,
            modal,
            dcc.Store(id="customer-id-store-low", data=str(customer_id))
        ], fluid="md", style={"maxWidth": "960px", "fontFamily": "'Segoe UI', sans-serif"})
    ], style={"backgroundColor": "#f4f6f8", "minHeight": "100vh"})


# --- CALLBACKS ---

# 1. URL Parser
@callback(
    Output('intervention-low-page-content', 'children'),
    Input('intervention-low-url', 'search')
)
def display_intervention_content(search):
    token = None
    if search:
        try:
            query = urllib.parse.parse_qs(search.lstrip('?'))
            token = query.get('token', [None])[0]
        except:
            pass
    return render_intervention_page(token)

# 2. View Toggler
@callback(
    [Output("dashboard-view-low", "style"),
     Output("details-view-low-container", "style"),
     Output("details-view-low-container", "children")],
    [Input({"type": "view-details-low-btn", "index": ALL}, "n_clicks"),
     Input({"type": "back-low-btn", "index": ALL}, "n_clicks")],
    [State("plans-store-low", "data")]
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

    if action_type == "view-details-low-btn":
        selected_plan = next((p for p in plans_data if p['id'] == plan_id), None)
        if not selected_plan:
            return no_update
        
        detail_layout = build_detail_layout_low(selected_plan)
        return {"display": "none"}, {"display": "block", "animation": "fadeIn 0.3s"}, detail_layout

    elif action_type == "back-low-btn":
        return {"display": "block", "animation": "fadeIn 0.3s"}, {"display": "none"}, no_update

    return no_update

# 3. Detail Builder
def build_detail_layout_low(plan):
    return html.Div([
        html.Div([
            dbc.Button("← Back to Rewards", id={"type": "back-low-btn", "index": "bg"}, color="link", className="p-0 text-decoration-none mb-2"),
            html.H2(plan['title'], className="fw-bold", style={"color": NAVY_BLUE}),
            html.P(plan['description'], className="lead text-muted")
        ], className="mb-4"),

        dbc.Card([
            dbc.CardBody([
                html.H5("Offer Details", className="fw-bold"),
                html.P(plan['reason']),
                html.Hr(),
                html.H6("Eligibility Criteria Met:", className="text-success fw-bold"),
                html.Ul([html.Li(e) for e in plan.get('eligibility', [])]),
                html.H6("Terms & Conditions:", className="text-secondary fw-bold"),
                html.Ul([html.Li(c) for c in plan.get('conditions', [])]),
            ])
        ], className="mb-4 shadow-sm border-0"),

        html.Div([
            dbc.Button("Confirm & Claim Offer", id={"type": "accept-final-low-btn", "index": plan['id']}, color="success", className="w-100 py-3 fw-bold")
        ], className="fixed-bottom bg-white border-top p-3 shadow-lg", style={"zIndex": 1000})
        
    ], className="pb-5 mb-5")

@callback(
    Output("success-modal-low", "is_open"),
    [Input({"type": "accept-final-low-btn", "index": ALL}, "n_clicks"), Input("close-modal-success-low", "n_clicks")],
    [State("success-modal-low", "is_open")],
    prevent_initial_call=True
)
def handle_final_acceptance(n_accept, n_close, is_open):
    from dash import callback_context
    ctx = callback_context
    if not ctx.triggered: return no_update

    button_id_str = ctx.triggered[0]['prop_id'].split('.')[0]
    if "close-modal-success-low" in button_id_str:
        return False
        
    # Assume accept clicked
    return True
