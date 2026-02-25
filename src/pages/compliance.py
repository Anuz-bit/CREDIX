from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from components.cards import KPICard
from components.charts import get_layout_template, colors
from utils.data_loader import load_data

def layout():
    df = load_data()
    
    # Mock Fairness Metrics
    # In a real app, we'd calculate disparate impact, etc.
    # Here we simulate risk distribution across a protected attribute like 'gender' (0/1) or 'age' (bins).
    if 'gender' in df.columns:
        # Check if values need mapping (assume numeric 0/1 are codes)
        # Using a safer check than map() which overwrites strings with NaN
        unique_vals = df['gender'].unique()
        # If we see 0 or 1 in the values, we apply mapping
        if any(x in [0, 1, 0.0, 1.0, '0', '1'] for x in unique_vals):
            df['gender'] = df['gender'].map({0: 'Male', 1: 'Female', '0': 'Male', '1': 'Female', 0.0: 'Male', 1.0: 'Female'}).fillna('Unknown')
        else:
            df['gender'] = df['gender'].fillna('Unknown')
            
    elif 'Gender' in df.columns:
         df['gender'] = df['Gender'].fillna('Unknown')
    else:
        # Fallback if no gender column
        df['gender'] = 'Unknown'
    
    # Define explicit color map to avoid KeyErrors if categories are missing/present
    gender_color_map = {
        'Male': colors()[0],
        'Female': colors()[1],
        'Unknown': colors()[2]
    }
    
    fig_fairness = px.box(df, x='gender', y='probability_of_default', 
                          title="Risk Score Distribution by Gender",
                          color='gender',
                          color_discrete_map=gender_color_map)
    fig_fairness.update_layout(**get_layout_template())
    
    # Audit Logs (Mock Data)
    audit_data = [
        {"Timestamp": "2024-05-20 10:23", "User": "Analyst_01", "Action": "Overrode Risk Score", "ID": "CUST-102"},
        {"Timestamp": "2024-05-20 09:15", "User": "System", "Action": "Model Retrain Triggered", "ID": "N/A"},
        {"Timestamp": "2024-05-19 16:45", "User": "Manager_05", "Action": "Approved Payment Plan", "ID": "CUST-881"},
        {"Timestamp": "2024-05-19 14:20", "User": "Analyst_02", "Action": "Viewed Sensitive Data", "ID": "CUST-334"},
        {"Timestamp": "2024-05-19 11:00", "User": "System", "Action": "Batch Prediction Run", "ID": "BATCH-99"}
    ]
    audit_df = pd.DataFrame(audit_data)

    return html.Div([
        # Header REMOVED (Global Header Used)
        
        # Governance KPIs
        dbc.Row([
            dbc.Col(KPICard("Fairness Index", "0.98", "No significant bias detected"), width=3),
            dbc.Col(KPICard("Consent Coverage", "99.2%", "GDPR/DPDP Compliant", color="success"), width=3),
            dbc.Col(KPICard("Audit Logs", "145", "Actions today"), width=3),
            dbc.Col(KPICard("Model Drift", "Low", "PSI < 0.1", color="success"), width=3),
        ]),
        
        # Charts
        dbc.Row([
             dbc.Col(dbc.Card([dbc.CardBody([dcc.Graph(figure=fig_fairness)])]), width=12),
        ], className="mb-4"),
        
        # Audit Table
        dbc.Card([
            dbc.CardHeader("Recent Audit Activity"),
            dbc.CardBody([
                dbc.Table.from_dataframe(audit_df, striped=True, bordered=True, hover=True)
            ])
        ])
    ])
