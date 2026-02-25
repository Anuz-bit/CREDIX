
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.data_loader import load_data, load_model_metrics
from components.cards import KPICard
from components.charts import (
    get_layout_template, colors, 
    create_density_plot, create_lift_chart, create_psi_chart,
    PRIMARY, SECONDARY, ACCENT, SUCCESS, WARNING, DANGER
)

def layout():
    # Load Initial Data
    df = load_data()
    metrics = load_model_metrics()
    auc = metrics.get('ROC-AUC', '0.87')
    acc = metrics.get('Accuracy', '0.92')
    ks = metrics.get('KS Statistic', '62.4')

    # Initial figures (static or default)
    fig_lift = create_lift_chart(df)
    fig_psi = create_psi_chart(df)
    
    # Feature Importance (Mock/Static for now)
    features = ['Income Stability', 'Credit Utilization', 'Recent Delinquencies', 'Age', 'Loan Tenure']
    importance = [0.35, 0.25, 0.20, 0.10, 0.05]
    fig_feat = go.Figure(go.Bar(x=importance, y=features, orientation='h', marker_color=SECONDARY))
    fig_feat.update_layout(title="Global Feature Importance (SHAP)", **get_layout_template())

    return html.Div([
        
        # 1. Header & Navigation
        # 1. Header REMOVED (Global Header Used)
        # Navigation to Customer Explorer

        # Navigation to Customer Explorer REMOVED (Moved to Sidebar)

        # 2. Model KPIs
        # 2. Model KPIs REMOVED as per user request

        # 2. Control Panel & Strategy Simulation
        dbc.Card([
            dbc.CardHeader("Decision Strategy Simulation", className="bg-white fw-bold border-bottom-0 pt-3 pb-0 rounded-top"),
            dbc.CardBody([
                dbc.Row([
                    # Controls
                    dbc.Col([
                        html.Label("Score Cutoff Threshold", className="fw-bold text-secondary small mb-2"),
                        dcc.Slider(0, 1, 0.01, value=0.5, id='cutoff-slider', 
                                   marks={0:'0', 0.5:'0.5', 1:'1'}, 
                                   tooltip={"placement": "bottom", "always_visible": True}),
                        
                        html.Div(id='confusion-matrix-container', className="mt-4 p-3 rounded text-center small", style={'backgroundColor': 'rgba(255,255,255,0.5)'})
                    ], xs=12, lg=4, className="border-end-lg pe-lg-4 mb-4"),

                    # Dynamic Metrics
                    dbc.Col([
                        dbc.Row([
                            dbc.Col([html.H6("Approval Rate", className="small text-muted"), html.H3(id="metric-approval", className="text-primary fw-bold")], width=6),
                            dbc.Col([html.H6("Bad Rate (Approved)", className="small text-muted"), html.H3(id="metric-bad-rate", className="text-danger fw-bold")], width=6),
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([html.H6("Projected Loss", className="small text-muted"), html.H3(id="metric-loss", className="text-dark fw-bold")], width=6),
                            dbc.Col([html.H6("F1 Score", className="small text-muted"), html.H3(id="metric-f1", className="text-success fw-bold")], width=6),
                        ])
                    ], xs=12, lg=8, className="ps-lg-4 pt-2")
                ])
            ])
        ], className="glass-panel border-0 mb-3"),

        # 3. Main Charts: Density & Lift
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id='density-chart', style={'height': '450px'})), className="glass-panel border-0 h-100"), xs=12, lg=6, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig_lift, style={'height': '450px'})), className="glass-panel border-0 h-100"), xs=12, lg=6, className="mb-3"),
        ], className="mb-3 g-2"),

        # 4. Monitoring: PSI & Features
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig_psi, style={'height': '450px'})), className="glass-panel border-0 h-100"), xs=12, lg=6, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig_feat, style={'height': '450px'})), className="glass-panel border-0 h-100"), xs=12, lg=6, className="mb-3"),
        ], className="mb-4 g-2"),

    ], className="p-4")


# --- Callbacks ---
@callback(
    [Output("density-chart", "figure"),
     Output("metric-approval", "children"),
     Output("metric-bad-rate", "children"),
     Output("metric-loss", "children"),
     Output("metric-f1", "children"),
     Output("confusion-matrix-container", "children")],
    [Input("cutoff-slider", "value")]
)
def update_risk_strategy(threshold):
    threshold = float(threshold)
    df = load_data()
    
    # 1. Update Density Chart Line
    fig_density = create_density_plot(df, threshold)

    # 2. Calculate Metrics
    if df.empty or 'probability_of_default' not in df.columns or 'target' not in df.columns:
        return fig_density, "N/A", "N/A", "N/A", "N/A", "No Data"

    # Decisions: Score > Threshold = Default (Bad), Score <= Threshold = Approved (Good)? 
    # Usually Higher Score = Higher Risk. So "Approved" is Score < Threshold.
    # User asked for "Score Cutoff". If 0.8, then 0.9 is rejected. 
    # Let's assume PD. Approved if PD < Threshold.
    
    df['pred_class'] = (df['probability_of_default'] >= threshold).astype(int)
    
    # Confusion Matrix
    tp = len(df[(df['target'] == 1) & (df['pred_class'] == 1)]) # Correctly Rejected (Default predicted as Default)
    tn = len(df[(df['target'] == 0) & (df['pred_class'] == 0)]) # Correctly Approved
    fp = len(df[(df['target'] == 0) & (df['pred_class'] == 1)]) # False Alarm (Good cust rejected)
    fn = len(df[(df['target'] == 1) & (df['pred_class'] == 0)]) # Missed Default (Bad cust approved) - RISK!

    total = len(df)
    approved = tn + fn
    approval_rate = (approved / total * 100) if total > 0 else 0
    
    bad_in_approved = (fn / approved * 100) if approved > 0 else 0
    
    # Mock Loss Calculation: Exposure * LGD * Missed Defaults
    # Assuming average exposure 50k, LGD 45%
    avg_exposure = 50000
    lgd = 0.45
    proj_loss = fn * avg_exposure * lgd
    
    # Precision/Recall/F1
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # Format Outputs
    approval_text = f"{approval_rate:.1f}%"
    bad_rate_text = f"{bad_in_approved:.2f}%"
    loss_text = f"₹{proj_loss:,.0f}"
    f1_text = f"{f1:.3f}"

    # Confusion Matrix Visual (Simple HTML Table)
    cm_element = html.Table([
        html.Tr([html.Th(""), html.Th("Predicted Good"), html.Th("Predicted Bad")]),
        html.Tr([html.Th("Actual Good"), html.Td(f"{tn} (Approved)", className="text-success bg-light"), html.Td(f"{fp} (Rejected)")]),
        html.Tr([html.Th("Actual Bad"), html.Td(f"{fn} (Missed)", className="text-danger fw-bold bg-light"), html.Td(f"{tp} (Caught)")]),
    ], className="table table-bordered table-sm mb-0 bg-white")

    return fig_density, approval_text, bad_rate_text, loss_text, f1_text, cm_element
