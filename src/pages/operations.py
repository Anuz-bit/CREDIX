
import dash
from dash import html, dcc, dash_table, Input, Output, callback
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import os
from utils.data_loader import load_data
from components.cards import KPICard

# dash.register_page(__name__, path='/operations', name="Operations") # Removed to fix app.py import error

def get_risk_tag(pd_val):
    if pd_val > 0.85: return "critical-risk"
    if pd_val > 0.70: return "high-risk"
    if pd_val > 0.40: return "medium-risk"
    return "low-risk"

def get_risk_label(pd_val):
    if pd_val > 0.85: return "ESCALATION"
    if pd_val > 0.70: return "High Priority"
    if pd_val > 0.40: return "Follow-Up"
    return "Low Monitor"

def get_action_recommendation(pd, trend, exposure):
    # Trend: 0=Stable, 1=Increasing Risk, 2=Decreasing Risk
    # Logic: High PD + Increasing Trend = Maximum Urgency
    
    if pd > 0.85:
        return "Field Visit / Legal"
    elif pd > 0.70:
        if trend == 1: return "Escalate to Senior Manager"
        return "Call Within 24h"
    elif pd > 0.40:
        if trend == 1: return "Priority Call"
        return "SMS / Email Reminder"
    else:
        return "Automated Statement"
def load_interaction_metrics():
    """Parses the real-time audit log to get counts."""
    opened = set()
    accepted = set()
    
    # Calculate path relative to this file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(base_dir, "intervention_audit_log.txt")
    
    try:
        with open(log_path, "r") as f:
            for line in f:
                if "INTERVENTION_LOG" in line:
                    parts = line.split(",")
                    cust_part = [p for p in parts if "Customer=" in p]
                    status_part = [p for p in parts if "Status=" in p]
                    
                    if cust_part and status_part:
                        cust_id = cust_part[0].split("=")[1].strip()
                        status = status_part[0].split("=")[1].strip()
                        
                        if status == "OPENED":
                            opened.add(cust_id)
                        elif "ACCEPTED" in status:
                            accepted.add(cust_id)
    except FileNotFoundError:
        print(f"Log file not found at: {log_path}")
        return 0, 0
        
    return len(opened), len(accepted)

def layout():
    # 1. Load Real Data
    df_raw = load_data()
    
    if df_raw.empty:
        return html.Div("Data Not Available.", className="text-center p-5")

    # 2. Process Data for Execution
    df = df_raw.copy()
    
    # Generate Mock Customer IDs if missing (Sample data didn't have ID)
    if 'customer_id' not in df.columns:
        df['customer_id'] = [f"CUST-{10001+i}" for i in range(len(df))]

    # Ensure numeric columns
    cols_check = ['probability_of_default', 'existing_liabilities_inr', 'emi_amount', 'risk_trend', 'failed_auto_debits_last_3m']
    for c in cols_check:
        if c not in df.columns:
            df[c] = 0
            
    # Calculate Expected Loss = PD * Exposure
    df['expected_loss'] = df['probability_of_default'] * df['existing_liabilities_inr']

    # 3. Calculate Banking Priority Score
    # Score = (PD * Exposure) + (Bounce Weight) + EMI Factor
    # This aligns heavily with "Value at Risk"
    bounce_weight = 50000 # Heavy penalty for checking bounce history
    emi_weight = 2 # Multiplier for EMI importance
    
    df['priority_score_raw'] = (df['expected_loss']) + \
                               (df['failed_auto_debits_last_3m'] * bounce_weight) + \
                               (df['emi_amount'] * emi_weight)
                               
    # Normalize score for display (0-100 is easier for humans, but let's keep raw density for sorting)
    # We will sort by Raw Score descending
    df = df.sort_values(by='priority_score_raw', ascending=False)
    
    # Add Display Columns
    df['Risk Segment'] = df['probability_of_default'].apply(get_risk_label)
    df['Action'] = df.apply(lambda row: get_action_recommendation(row['probability_of_default'], row['risk_trend'], row['existing_liabilities_inr']), axis=1)
    
    # Logic for Trend Text
    trend_map = {0: 'Stable', 1: 'Increasing ↗', 2: 'Decreasing ↘'}
    df['Trend_Text'] = df['risk_trend'].map(trend_map).fillna('Unknown')
    
    # Logic for formatting
    df['PD %'] = (df['probability_of_default'] * 100).round(1).astype(str) + '%'
    df['Exposure'] = df['existing_liabilities_inr'].apply(lambda x: f"₹{x:,.0f}")
    df['EMI'] = df['emi_amount'].apply(lambda x: f"₹{x:,.0f}")
    df['Priority Score'] = df['priority_score_raw'].apply(lambda x: f"{x:,.0f}") # Raw score is clearer for operations prioritization

    # Select columns for Table
    table_cols = ['customer_id', 'Risk Segment', 'PD %', 'Exposure', 'EMI', 'Trend_Text', 'Priority Score', 'Action']
    table_data = df[table_cols].to_dict('records')

    # 4. KPI Calculations (Portfolio Level)
    total_exposure = df['existing_liabilities_inr'].sum()
    
    high_risk_df = df[df['probability_of_default'] > 0.70]
    high_risk_exposure = high_risk_df['existing_liabilities_inr'].sum()
    total_expected_loss = df['expected_loss'].sum()
    avg_emi_high_risk = high_risk_df['emi_amount'].mean() if not high_risk_df.empty else 0
    
    # Operational KPIs
    # Action Required Today: High Risk customers (PD > 0.7)
    action_today = len(high_risk_df)
    pending_followups = len(df[(df['probability_of_default'] > 0.4) & (df['probability_of_default'] <= 0.7)])
    
    # New Engagement Metrics from REAL-TIME LOGS
    real_opened_count, real_accepted_count = load_interaction_metrics()
    
    opened_url_count = real_opened_count
    to_be_followed_up = real_accepted_count

    # Mock operational metrics
    avg_resolution = "4.2 Days" 
    success_rate = "68%"

    # --- LAYOUT ---
    return html.Div([
        
        # Header
        # Header REMOVED (Global Header Used)
        
        # Top KPI Row - Exposure Risk

        # Top KPI Row - Exposure Risk
        dbc.Row([
            dbc.Col(KPICard("Customers Opened URL", str(opened_url_count), "Engagement (Clicks)", color="info"), xs=12, md=6, lg=3, className="mb-3"),
            dbc.Col(KPICard("Customers to Follow Up", str(to_be_followed_up), "Accepted Plan - Call RM", color="warning"), xs=12, md=6, lg=3, className="mb-3"),
            dbc.Col(KPICard("Intervention Success", success_rate, "PTP (Promise to Pay) Ratio", color="success"), xs=12, md=6, lg=3, className="mb-2"),
            dbc.Col(KPICard("Avg EMI (High Risk)", f"₹{avg_emi_high_risk:,.0f}", "Monthly Impact"), xs=12, md=6, lg=3, className="mb-2"),
        ], className="mb-3 g-2"),

        # Operational Metrics Row
        dbc.Row([
            dbc.Col(KPICard("Action Required Today", str(action_today), "Critical Escalations", color="danger"), xs=12, md=6, lg=3, className="mb-3"),
            dbc.Col(KPICard("Pending Follow-ups", str(pending_followups), "Medium Priority Queue", color="primary"), xs=12, md=6, lg=3, className="mb-3"),
            dbc.Col(KPICard("Avg Resolution Time", avg_resolution, "-12% vs Last Week", color="success"), xs=12, md=6, lg=3, className="mb-3"),
            # Intervention Success moved to top row, leaving slot empty or we can add something else?
            # Let's keep appearance balanced by making columns wider or adding a placeholder. 
            # Actually, let's just span the last card or leave 3 columns. 
            # Or duplicte? No.
            # Let's remove the 4th column here for now.
        ], className="mb-3 g-2"),

        # Main Execution Table
        dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col(html.H5("Daily Intervention Worklist", className="mb-0 fw-bold"), xs=12, md=8, className="mb-2 mb-md-0"),
                    dbc.Col(html.Span("Sorted by Priority Score (VaR Impact)", className="badge bg-light text-dark float-md-end"), xs=12, md=4)
                ])
            ], className="bg-white border-bottom-0 pt-3 pb-2"),
            
            dbc.CardBody([
                dash_table.DataTable(
                    id='operations-table',
                    columns=[
                        {'name': 'ID', 'id': 'customer_id'},
                        {'name': 'Segment', 'id': 'Risk Segment'},
                        {'name': 'PD %', 'id': 'PD %'},
                        {'name': 'Exposure', 'id': 'Exposure'},
                        {'name': 'EMI', 'id': 'EMI'},
                        {'name': 'Trend', 'id': 'Trend_Text'},
                        {'name': 'Priority Score', 'id': 'Priority Score'},
                        {'name': 'Recommended Action', 'id': 'Action'},
                    ],
                    data=table_data,
                    sort_action='native',
                    filter_action='native', # Enable search/filter
                    page_size=15, # Pagination
                    style_as_list_view=True,
                    style_header={
                        'backgroundColor': '#f8f9fa',
                        'fontWeight': 'bold',
                        'color': '#495057',
                        'borderBottom': '2px solid #0A1F44'
                    },
                    style_cell={
                        'padding': '12px 15px',
                        'textAlign': 'left',
                        'fontFamily': 'Segoe UI, sans-serif',
                        'fontSize': '14px',
                        'color': '#2c3e50'
                    },
                    style_data_conditional=[
                        # Striped rows
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgba(248, 249, 250, 0.5)'
                        },
                        # Risk Segment Colors
                        {
                            'if': {'filter_query': '{Risk Segment} = "ESCALATION"'},
                            'color': '#c0392b',
                            'fontWeight': 'bold'
                        },
                        {
                            'if': {'filter_query': '{Risk Segment} = "High Priority"'},
                            'color': '#e67e22',
                            'fontWeight': 'bold'
                        },
                         {
                            'if': {'filter_query': '{Risk Segment} = "Follow-Up"'},
                            'color': '#f1c40f',
                            'fontWeight': 'bold'
                        },
                        {
                            'if': {'filter_query': '{Risk Segment} = "Low Monitor"'},
                            'color': '#27ae60'
                        },
                        # Trend Colors
                        {
                            'if': {'filter_query': '{Trend_Text} contains "Increasing"'},
                            'color': '#e74c3c'
                        },
                         {
                            'if': {'filter_query': '{Trend_Text} contains "Decreasing"'},
                            'color': '#2ecc71'
                        },
                    ]
                )
            ])
        ], className="shadow-sm border-0 mb-3")

    ], className="p-4")
