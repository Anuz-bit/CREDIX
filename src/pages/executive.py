

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from utils.data_loader import load_data
from components.cards import KPICard
from components.charts import (
    create_risk_migration_matrix,
    create_vintage_curve,
    create_exposure_concentration,
    create_early_warnings,
    get_layout_template,
    colors,
    PRIMARY, DANGER, WARNING, SUCCESS
)

# --- Scenario Data ---
SCENARIOS = {
    'high': {
        'data': [3.4, 3.8, 4.3, 4.9, 5.6, 6.4],
        'color': DANGER,
        'fill': 'rgba(192, 57, 43, 0.2)', # Higher opacity for "premium" feel
        'title': 'High Risk Scenario',
        'desc': "Risk migration toward high band accelerating. Concentration in SME segment driving projected NPA above 6% within 6 months. Immediate intervention recommended.",
        'metric_npa': "6.4%", 'metric_ecl': "₹7.2 Cr", 'metric_risk': "45%",
        'gradient': 'rgba(192, 57, 43, 0.05)' # Ending gradient
    },
    'moderate': {
        'data': [3.4, 3.6, 3.9, 4.2, 4.5, 4.8],
        'color': WARNING,
        'fill': 'rgba(243, 156, 18, 0.2)',
        'title': 'Moderate Risk Scenario',
        'desc': "Portfolio stable under current risk mix. Gradual increase in NPA driven by vintage seasoning. Monitoring recommended.",
        'metric_npa': "4.8%", 'metric_ecl': "₹5.6 Cr", 'metric_risk': "33%",
        'gradient': 'rgba(243, 156, 18, 0.05)'
    },
    'low': {
        'data': [3.4, 3.3, 3.2, 3.1, 3.0, 2.9],
        'color': SUCCESS,
        'fill': 'rgba(39, 174, 96, 0.2)',
        'title': 'Low Risk Scenario',
        'desc': "Improved collections and controlled migration reduce projected NPA below 3%. Positive recovery momentum visible.",
        'metric_npa': "2.9%", 'metric_ecl': "₹3.1 Cr", 'metric_risk': "15%",
        'gradient': 'rgba(39, 174, 96, 0.05)'
    }
}

def layout():
    df = load_data()
    
    # ... (Backend Calculations for Top KPIs remain same) ...
    if 'existing_liabilities_inr' in df.columns:
        total_exposure = df['existing_liabilities_inr'].sum()
    else:
        total_exposure = 0

    if 'probability_of_default' in df.columns and 'existing_liabilities_inr' in df.columns:
        pd_series = df['probability_of_default'].fillna(0)
        ead_series = df['existing_liabilities_inr'].fillna(0)
        lgd = 0.45
        ecl_value = (pd_series * lgd * ead_series).sum()
    else:
        ecl_value = 0

    high_risk_count = 0
    if 'probability_of_default' in df.columns and 'existing_liabilities_inr' in df.columns:
        high_risk_mask = df['probability_of_default'] > 0.7
        high_risk_exposure = df.loc[high_risk_mask, 'existing_liabilities_inr'].sum()
        high_risk_count = high_risk_mask.sum()
        high_risk_pct = (high_risk_exposure / total_exposure * 100) if total_exposure > 0 else 0
    else:
        high_risk_pct = 0

    if 'probability_of_default' in df.columns and 'existing_liabilities_inr' in df.columns and total_exposure > 0:
        weighted_pd_sum = (df['probability_of_default'].fillna(0) * df['existing_liabilities_inr'].fillna(0)).sum()
        default_proj_pct = (weighted_pd_sum / total_exposure) * 100
    else:
        default_proj_pct = 0

    # ... (Charts Static Helpers) ...
    fig_migration = create_risk_migration_matrix()
    fig_vintage = create_vintage_curve()
    fig_exposure = create_exposure_concentration()
    fig_warning = create_early_warnings()

    # Helper for safe formatting
    def format_cr(val):
        if val >= 10000000:
            return f"₹{val/10000000:.1f} Cr"
        elif val >= 100000:
            return f"₹{val/100000:.1f} L"
        else:
            return f"₹{val:,.0f}"

    return html.Div([
        
        # Section 1: KPI Cards
        dbc.Row([
            dbc.Col(KPICard("Total Exposure", format_cr(total_exposure), "Active Accounts", trend="neutral"), xs=12, md=6, lg=3, className="d-flex mb-3"),
            dbc.Col(KPICard("Expected Credit Loss", format_cr(ecl_value), "Portfolio (LGD 45%)", color="danger", trend="up"), xs=12, md=6, lg=3, className="d-flex mb-3"),
            dbc.Col(KPICard("High Risk Portfolio", f"{high_risk_pct:.1f}%", f"{high_risk_count} High Risk Cust.", color="warning", trend="down"), xs=12, md=6, lg=3, className="d-flex mb-2"),
            dbc.Col(KPICard("30-Day Default Proj.", f"{default_proj_pct:.1f}%", "Exposure Weighted", color="danger", trend="up"), xs=12, md=6, lg=3, className="d-flex mb-2"),
        ], className="mb-3 align-items-stretch g-2"),

        # Section 2: Dynamic Risk Projection Panel (Standard Card, 30/70)
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # Left Panel (30%) - Control & Summary
                    dbc.Col([
                        html.H5("Portfolio Risk Outlook", className="mb-4 text-primary fw-bold"),

                        html.Label("Select Risk Scenario", className="text-secondary small fw-bold mb-3 ls-1"),
                        html.Div([
                            dbc.Button("High Risk", id="btn-high", n_clicks=0, className="w-100 mb-3 text-start ps-4", color="danger", outline=True),
                            dbc.Button("Moderate Risk", id="btn-mod", n_clicks=0, className="w-100 mb-3 text-start ps-4", color="warning", outline=True, active=True),
                            dbc.Button("Low Risk", id="btn-low", n_clicks=0, className="w-100 mb-5 text-start ps-4", color="success", outline=True),
                        ]),

                        # Insight Box (Standard)
                        html.Div([
                            html.H6("Current Gross NPA", className="text-secondary small text-uppercase ls-1"),
                            html.H3("3.4%", className="fw-bold text-dark mb-3 animate-count-up",  **{'data-value': "3.4%"}),
                            
                            html.H6("Scenario Insight", className="text-secondary small text-uppercase ls-1 mt-4"),
                            html.P(id="scenario-desc", className="small text-muted mb-0 animate-fade-in", style={'lineHeight': '1.8'}),
                        ], className="bg-light p-4 rounded-3 border bg-white shadow-sm")

                    ], xs=12, lg=4, className="pe-lg-5 mb-4 border-end-lg border-light"),

                    # Right Panel (70%) - Graph
                    dbc.Col([
                        # Graph Container
                        html.Div(dcc.Graph(id="projection-graph", config={'displayModeBar': False}, style={'height': '500px'}), className="graph-container mb-3"),
                        
                        # Mini Metrics Strip
                        dbc.Row([
                            dbc.Col([
                                html.H6("Projected NPA (6M)", className="text-secondary small mb-1"), 
                                html.H4(id="metric-npa", className="fw-bold text-primary kpi-value-animate")
                            ], width=4, className="text-center border-end"),
                            
                            dbc.Col([
                                html.H6("Projected ECL", className="text-secondary small mb-1"), 
                                html.H4(id="metric-ecl", className="fw-bold text-primary kpi-value-animate")
                            ], width=4, className="text-center border-end"),
                            
                            dbc.Col([
                                html.H6("High Risk Exposure", className="text-secondary small mb-1"), 
                                html.H4(id="metric-risk", className="fw-bold text-primary kpi-value-animate")
                            ], xs=4, className="text-center"),
                        ], className="pt-3")
                    ], xs=12, lg=8, className="ps-lg-4")
                ])
            ])
        ], className="shadow-sm border-0 mb-3"),

        # Section 3: Risk Graphs (Grid 2x2)
        html.H5("Core Risk Metrics", className="mb-3 text-secondary"),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig_migration, config={'displayModeBar': False})), className="shadow-sm border-0 h-100"), xs=12, lg=6, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig_vintage, config={'displayModeBar': False})), className="shadow-sm border-0 h-100"), xs=12, lg=6, className="mb-3"),
        ], className="g-2"),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig_exposure, config={'displayModeBar': False})), className="shadow-sm border-0 h-100"), xs=12, lg=6, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig_warning, config={'displayModeBar': False})), className="shadow-sm border-0 h-100"), xs=12, lg=6, className="mb-3"),
        ], className="mb-3 g-2"),

        # Section 4: Insights Panel
        dbc.Card([
            dbc.CardHeader("Executive Insights", className="bg-white border-bottom-0 fw-bold"),
            dbc.CardBody([
                html.Ul([
                    html.Li("Structural deterioration observed in Mid-Risk segment (12% migration to High).", className="mb-2"),
                    html.Li("Vintage Q1 2024 showing higher early default rates compared to 2023 cohorts.", className="mb-2"),
                    html.Li(f"Top 10% of customers hold {42}% of total exposure, indicating moderate concentration risk.", className="mb-2"),
                    html.Li("Early warning indicators (Bounce Rate) trending upward over last 3 months.", className="mb-0")
                ], className="text-secondary small")
            ])
        ], className="shadow-sm border-0 bg-light")

    ], className="p-4")


# --- Callbacks ---
@callback(
    [Output("projection-graph", "figure"),
     Output("scenario-desc", "children"),
     Output("metric-npa", "children"),
     Output("metric-npa", "data-value"), # For animation trigger
     Output("metric-ecl", "children"),
     Output("metric-ecl", "data-value"),
     Output("metric-risk", "children"),
     Output("metric-risk", "data-value"),
     Output("btn-high", "active"),
     Output("btn-mod", "active"),
     Output("btn-low", "active")],
    [Input("btn-high", "n_clicks"),
     Input("btn-mod", "n_clicks"),
     Input("btn-low", "n_clicks")]
)
def update_scenario(n_high, n_mod, n_low):
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'btn-mod'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'btn-high':
        key = 'high'
        actives = (True, False, False)
    elif button_id == 'btn-low':
        key = 'low'
        actives = (False, False, True)
    else:
        key = 'moderate'
        actives = (False, True, False)

    scen = SCENARIOS[key]
    months = ['Month 1', 'Month 2', 'Month 3', 'Month 4', 'Month 5', 'Month 6']
    
    # Create Premium Spline Graph
    fig = go.Figure()
    
    # 1. Main Projection Line with Gradient Fill (Simulated)
    # Plotly's 'tozeroy' fills with 'fillcolor'. We use rgba for semi-transparency.
    fig.add_trace(go.Scatter(
        x=months, 
        y=scen['data'],
        mode='lines',
        name='Projected NPA',
        line=dict(color=scen['color'], width=5, shape='spline', smoothing=1.3),
        fill='tozeroy',
        fillcolor=scen['fill'], # Semi-transparent fill
        hoverinfo='y',
    ))

    # 2. Add "Ghost Lines" for simulation effect (Monte Carlo style background)
    # Just simple offsets for visual flair
    import numpy as np
    base_data = np.array(scen['data'])
    fig.add_trace(go.Scatter(
        x=months, y=base_data * 1.05, mode='lines', 
        line=dict(color='rgba(200,200,200,0.3)', width=1, dash='dot', shape='spline'), 
        hoverinfo='skip', showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=months, y=base_data * 0.95, mode='lines', 
        line=dict(color='rgba(200,200,200,0.3)', width=1, dash='dot', shape='spline'), 
        hoverinfo='skip', showlegend=False
    ))

    # Layout Styling
    layout = get_layout_template()
    layout['paper_bgcolor'] = 'rgba(0,0,0,0)' # Transparent for glass effect
    layout['plot_bgcolor'] = 'rgba(0,0,0,0)'
    layout['margin'] = dict(l=50, r=20, t=40, b=40)
    
    # Axis Styling
    layout['xaxis'].update(
        title="Months Ahead", 
        showgrid=False, 
        linecolor='rgba(0,0,0,0.1)',
        tickfont=dict(size=12, color='#7f8c8d')
    )
    layout['yaxis'].update(
        title="Projected Gross NPA %", 
        showgrid=True, 
        gridcolor='rgba(0,0,0,0.03)', # Very subtle grid
        zeroline=False,
        range=[2, 7.5], # Fixed range for stability
        tickfont=dict(size=12, color='#7f8c8d')
    )


    fig.update_layout(
        title=dict(text=scen['title'], font=dict(size=18, family="Segoe UI", color=PRIMARY)),
        **layout
    )

    # Return values for Graph, Text, and Metrics (Children + Data-Value for Animation)
    return (
        fig, 
        scen['desc'], 
        scen['metric_npa'], scen['metric_npa'], # Output to Children AND Data-Value
        scen['metric_ecl'], scen['metric_ecl'],
        scen['metric_risk'], scen['metric_risk'],
        actives[0], actives[1], actives[2]
    )
