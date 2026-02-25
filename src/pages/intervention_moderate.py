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
WARNING_AMBER = "#ffc107"
DANGER_RED = "#dc3545"

# --- Main Layout Container ---
def layout():
    return html.Div([
        dcc.Location(id='intervention-mod-url', refresh=False),
        html.Div(id='intervention-mod-page-content')
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
                OutcomeLogger.log_outcome(customer.get('customer_id'), "N/A", "OPENED_MOD")
        except:
            pass
    
    # Fallback/Demo Mode: Select a MODERATE risk customer
    if customer is None:
        df = load_data()
        if not df.empty:
            # Moderate risk: 0.2 < PD <= 0.6
            mod_risk = df[(df['probability_of_default'] >= 0.2) & (df['probability_of_default'] <= 0.6)]
            if not mod_risk.empty:
                customer = mod_risk.iloc[0].to_dict()
            else:
                 # Fallback to first
                customer = df.iloc[0].to_dict()
                customer['probability_of_default'] = 0.35 # Force moderate risk

    if not customer:
        return html.Div("System Error: No customer data available.", className="p-5 text-center text-danger")

    # Extract Data safely
    def get_val(key, default):
        return customer.get(key, default) if isinstance(customer, dict) else customer.get(key, default)

    full_name = get_val('full_name', get_val('name', 'Valued Customer'))
    customer_id = get_val('customer_id', 'UNKNOWN')
    
    # Logic
    
    # Financial Metrics
    pd_val = get_val('probability_of_default', 0.35)
    risk_score = int(pd_val * 100) 
    cibil_score = get_val('bureau_score', get_val('cibil_score', 680))
    
    # Specific Metrics for Moderate Risk
    emi_delay_trend = "Avg 3-5 Days"
    credit_utilization = "75% (High)"
    financial_stress = "Moderate"

    # --- Components ---

    # Greeting
    greeting_section = html.Div([
        html.H3(f"Hello, {full_name.split()[0]}", className="fw-bold"),
        html.P("We noticed some recent changes in your payments and want to help you stay on track.", className="text-muted lead")
    ], className="mb-4")

    # Support / Reasons Section
    reasons_list = [
        "Recent delays in EMI payments observed",
        "High credit utilization detected",
        "Proactive support to prevent credit score impact"
    ]
    reasons_items = [html.Li(r, className="mb-2") for r in reasons_list]
    
    section_a = dbc.Card([
        dbc.CardHeader("Why we are reaching out", style={"backgroundColor": "transparent", "fontWeight": "bold", "borderBottom": "none", "color": CORPORATE_BLUE}),
        dbc.CardBody([
            html.Ul(reasons_items, style={"paddingLeft": "1.2rem", "color": "#444"})
        ])
    ], className="mb-4 shadow-sm border-0")

    # Section B: Health (Modified for Moderate Risk)
    section_b = dbc.Card([
        dbc.CardBody([
            html.H6("FINANCIAL HEALTH SUMMARY", className="text-muted small mb-2"),
            html.H3("Needs Attention", style={"color": WARNING_AMBER, "fontWeight": "bold"}),
            html.P(["Risk Band: ", html.Span("Moderate", style={"fontWeight": "bold", "color": WARNING_AMBER})], className="text-muted mt-2 mb-0"),
            html.Hr(),
            
            # Scores Row
            dbc.Row([
                dbc.Col([
                    html.Small("RISK SCORE", className="text-muted fw-bold"),
                    html.H4(f"{risk_score}/100", className="mb-0", style={"color": WARNING_AMBER})
                ], width=6, className="text-center border-end"),
                 dbc.Col([
                    html.Small("CIBIL SCORE", className="text-muted fw-bold"),
                    html.H4(f"{cibil_score}", className="mb-0 text-primary")
                ], width=6, className="text-center"),
            ], className="mt-3"),
            
            html.Hr(),
            # Extra Moderate Risk Metrics
             dbc.Row([
                dbc.Col([
                    html.Small("EMI DELAY TREND", className="text-muted fw-bold d-block"),
                    html.Span(emi_delay_trend, className="text-danger fw-bold")
                ], width=4, className="text-center border-end"),
                 dbc.Col([
                    html.Small("CREDIT UTILIZATION", className="text-muted fw-bold d-block"),
                     html.Span(credit_utilization, className="text-warning fw-bold")
                ], width=4, className="text-center border-end"),
                 dbc.Col([
                    html.Small("STRESS LEVEL", className="text-muted fw-bold d-block"),
                     html.Span(financial_stress, className="text-warning fw-bold")
                ], width=4, className="text-center"),
            ], className="mt-2"),
        ])
    ], className="mb-4 shadow-sm border-0")

    # Section C: Support Plans
    # We define specific support plans here
    support_plans_data = [
        {
            "id": "sup_1",
            "type": "Restructuring",
            "title": "Flexible EMI Restructuring",
            "tagline": "Reduce your monthly burden immediately.",
            "impact_amount": "↓ 30% EMI",
            "description": "Convert your current outstanding balance into a longer tenure loan to reduce monthly EMI outflow.",
            "reason": "High monthly obligation detected.",
            "eligibility": ["3 recent payments made", "Income proof"],
            "conditions": ["Tenure extends by 12 months"]
        },
        {
            "id": "sup_2",
            "type": "Grace Period",
            "title": "5-Day Payment Grace Period",
            "tagline": "Extra time to pay without penalties.",
            "impact_amount": "0 Late Fees",
            "description": "Get an automatic 5-day extension on your due date for the next 3 months to align with your salary cycle.",
            "reason": "Payment timing mismatch.",
            "eligibility": ["Salary credit date verification"],
            "conditions": ["Valid for 3 months"]
        },
         {
            "id": "sup_3",
            "type": "Partial Pay",
            "title": "Partial EMI Acceptance",
            "tagline": "Pay what you can now.",
            "impact_amount": "Avoid Default",
            "description": "Pay 50% of your EMI now and the rest later to keep your account standard.",
            "reason": "Temporary cash flow issue.",
            "eligibility": ["Minimum 50% payment"],
            "conditions": ["Remaining balance due in 15 days"]
        },
        {
            "id": "sup_4",
            "type": "Advisory",
            "title": "Financial Health Alerts",
            "tagline": "Stay on top of your finances.",
            "impact_amount": "FREE",
            "description": "Subscribe to weekly SMS/WhatsApp summaries of your spending and upcoming dues.",
            "reason": "Proactive monitoring.",
            "eligibility": ["All customers"],
            "conditions": ["Opt-in required"]
        }
    ]

    def create_support_card(plan):
        card = dbc.Card([
            dbc.CardBody([
                dbc.Badge(plan['type'].upper(), color="info", className="mb-2"),
                html.H5(plan['title'], className="card-title fw-bold text-dark"),
                html.P(plan['tagline'], className="text-muted small mb-3"),
                
                html.Div([
                    html.Span("Relief Impact:", className="d-block small text-muted"),
                    html.Span(plan['impact_amount'], className="fw-bold fs-5 text-success")
                ], className="mb-3 p-2 bg-light rounded text-center"),

                dbc.Button("View Options", id={"type": "view-details-mod-btn", "index": plan['id']}, color="primary", outline=True, className="w-100")
            ])
        ], className="mb-3 shadow-sm h-100 hover-card")
        return dbc.Col(card, md=4, className="mb-3")

    plan_cards = [create_support_card(p) for p in support_plans_data]

    dashboard_view = html.Div([
        greeting_section,
        dbc.Row([
            dbc.Col(section_a, md=6),
            dbc.Col(section_b, md=6),
        ]),
        html.Hr(className="my-4"),
        
        # Support Plans
        html.H4("Recommended Support Plans", className="mb-3", style={"color": NAVY_BLUE}),
        dbc.Row(plan_cards),
        
    ], id="dashboard-view-mod")

    # --- VIEW 2: PLAN DETAILS (Hidden by default) ---
    details_view = html.Div(id="details-view-mod-container", style={"display": "none"})

    # --- Data Stores ---
    store_plans = dcc.Store(id="plans-store-mod", data=support_plans_data)
    
    # Modal
    modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Request Submitted", className="text-primary")),
        dbc.ModalBody("Your request for this support plan has been received. Our team will review and contact you within 24 hours."),
        dbc.ModalFooter(dbc.Button("Close", id="close-modal-success-mod", className="ms-auto", n_clicks=0))
    ], id="success-modal-mod", is_open=False)

    return html.Div([
        dbc.Container([
            dashboard_view,
            details_view,
            store_plans,
            modal,
            dcc.Store(id="customer-id-store-mod", data=str(customer_id))
        ], fluid="md", style={"maxWidth": "960px", "fontFamily": "'Segoe UI', sans-serif"})
    ], style={"backgroundColor": "#f4f6f8", "minHeight": "100vh"})


# --- CALLBACKS ---

# 1. URL Parser
@callback(
    Output('intervention-mod-page-content', 'children'),
    Input('intervention-mod-url', 'search')
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
    [Output("dashboard-view-mod", "style"),
     Output("details-view-mod-container", "style"),
     Output("details-view-mod-container", "children")],
    [Input({"type": "view-details-mod-btn", "index": ALL}, "n_clicks"),
     Input({"type": "back-mod-btn", "index": ALL}, "n_clicks")],
    [State("plans-store-mod", "data")]
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

    if action_type == "view-details-mod-btn":
        selected_plan = next((p for p in plans_data if p['id'] == plan_id), None)
        if not selected_plan:
            return no_update
        
        detail_layout = build_detail_layout_mod(selected_plan)
        return {"display": "none"}, {"display": "block", "animation": "fadeIn 0.3s"}, detail_layout

    elif action_type == "back-mod-btn":
        return {"display": "block", "animation": "fadeIn 0.3s"}, {"display": "none"}, no_update

    return no_update

# 3. Detail Builder
def build_detail_layout_mod(plan):
    return html.Div([
        html.Div([
            dbc.Button("← Back to Options", id={"type": "back-mod-btn", "index": "bg"}, color="link", className="p-0 text-decoration-none mb-2"),
            html.H2(plan['title'], className="fw-bold", style={"color": NAVY_BLUE}),
            html.P(plan['description'], className="lead text-muted")
        ], className="mb-4"),

        dbc.Card([
            dbc.CardBody([
                html.H5("Plan Details", className="fw-bold"),
                html.P(plan['reason']),
                html.Hr(),
                html.H6("Eligibility:", className="text-info fw-bold"),
                html.Ul([html.Li(e) for e in plan.get('eligibility', [])]),
                html.H6("Conditions:", className="text-warning fw-bold"),
                html.Ul([html.Li(c) for c in plan.get('conditions', [])]),
            ])
        ], className="mb-4 shadow-sm border-0"),

        html.Div([
            dbc.Button("Apply for Support", id={"type": "accept-final-mod-btn", "index": plan['id']}, color="primary", className="w-100 py-3 fw-bold", style={"backgroundColor": NAVY_BLUE})
        ], className="fixed-bottom bg-white border-top p-3 shadow-lg", style={"zIndex": 1000})
        
    ], className="pb-5 mb-5")

@callback(
    Output("success-modal-mod", "is_open"),
    [Input({"type": "accept-final-mod-btn", "index": ALL}, "n_clicks"), Input("close-modal-success-mod", "n_clicks")],
    [State("success-modal-mod", "is_open")],
    prevent_initial_call=True
)
def handle_final_acceptance(n_accept, n_close, is_open):
    from dash import callback_context
    ctx = callback_context
    if not ctx.triggered: return no_update

    button_id_str = ctx.triggered[0]['prop_id'].split('.')[0]
    if "close-modal-success-mod" in button_id_str:
        return False
        
    # Assume accept clicked
    return True
