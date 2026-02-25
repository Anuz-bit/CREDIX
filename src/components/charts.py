
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from scipy.stats import gaussian_kde

# Theme Colors - Minimal Banking
PRIMARY = "#0A1F44"    # Navy Blue
SECONDARY = "#5da4d6"  # Soft Blue
ACCENT = "#ecf0f1"     # Light Grey
SUCCESS = "#27ae60"    # Muted Green
WARNING = "#f39c12"    # Muted Orange
DANGER = "#c0392b"     # Muted Red
BACKGROUND = "#FFFFFF"
TEXT = "#2c3e50"       # Dark Grey

def get_layout_template():
    """Returns a dictionary for consistent Plotly layout with animations."""
    return dict(
        font=dict(family="Segoe UI", color=TEXT, size=11),
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
        margin=dict(l=30, r=20, t=40, b=30),
        xaxis=dict(
            showgrid=False, 
            zeroline=False, 
            showline=True, 
            linecolor='#ecf0f1',
            tickfont=dict(color=TEXT)
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor="#f7f9fa", 
            zeroline=False,
            tickfont=dict(color=TEXT)
        ),
        # Animation settings
        transition={'duration': 1000, 'easing': 'cubic-out'},
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

def colors():
    return [PRIMARY, SECONDARY, SUCCESS, WARNING, DANGER]

def empty_chart(text="No Data Available"):
    """Returns an empty chart with text."""
    fig = go.Figure()
    fig.add_annotation(
        text=text,
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14, color=TEXT)
    )
    fig.update_layout(**get_layout_template())
    return fig

# --- New Chart Helpers ---

def create_portfolio_risk_projection():
    """Reserved for potential reuse, but main logic is now dynamic in page callback."""
    # Placeholder or can be removed if fully dynamic
    return empty_chart("Select Scenario")

def create_risk_migration_matrix():
    """Creates a Risk Migration Matrix Heatmap."""
    x = ['Low', 'Medium', 'High'] # Current
    y = ['Low', 'Medium', 'High'] # Previous
    z = [
        [85, 12, 3],   # Low -> Low, Med, High
        [10, 75, 15],  # Med -> Low, Med, High
        [2, 18, 80]    # High -> Low, Med, High
    ]
    
    # Custom colorscale: Minimal Green to Red
    colorscale = [
        [0, "#eafaf1"],   # Very light green
        [0.5, "#fef9e7"], # Very light orange
        [1, "#fadbd8"]    # Very light red
    ]

    fig = go.Figure(data=go.Heatmap(
        z=z, x=x, y=y,
        colorscale=colorscale,
        text=z, texttemplate="%{text}%",
        hoverongaps=False,
        showscale=False
    ))
    
    fig.update_layout(
        title="Risk Migration Matrix",
        xaxis_title="Current Risk Band",
        yaxis_title="Previous Risk Band",
        **get_layout_template()
    )
    return fig

def create_vintage_curve():
    """Creates a Vintage Default Curve."""
    months = np.arange(1, 13)
    # Cumulative default rates
    v1 = np.cumsum(np.random.beta(2, 15, 12) * 1.5) 
    v2 = np.cumsum(np.random.beta(2, 15, 12) * 1.8) 
    v3 = np.cumsum(np.random.beta(2, 15, 12) * 1.2) 

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months, y=v1, mode='lines', name='Q1 2024', line=dict(width=2, color=PRIMARY)))
    fig.add_trace(go.Scatter(x=months, y=v2, mode='lines', name='Q4 2023', line=dict(width=2, color=WARNING)))
    fig.add_trace(go.Scatter(x=months, y=v3, mode='lines', name='Q3 2023', line=dict(width=2, color=SUCCESS)))

    fig.update_layout(
        title="Vintage Default Curve",
        xaxis_title="Months on Book",
        yaxis_title="Cumulative Default %",
        **get_layout_template()
    )
    return fig

def create_exposure_concentration():
    """Creates a Pareto chart for Exposure Concentration."""
    deciles = [f"D{i}" for i in range(1, 11)]
    exposure = [42, 18, 12, 8, 6, 5, 4, 3, 1, 1] 
    cumulative = np.cumsum(exposure)

    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=deciles, y=exposure, name='Exposure %',
        marker_color=SECONDARY,
        opacity=0.8
    ))
    
    fig.add_trace(go.Scatter(
        x=deciles, y=cumulative, name='Cumulative %',
        yaxis='y2', mode='lines',
        line=dict(color=DANGER, width=2)
    ))

    layout = get_layout_template()
    layout['yaxis2'] = dict(
        overlaying='y',
        side='right',
        showgrid=False,
        range=[0, 110],
        tickfont=dict(color=TEXT)
    )
    
    fig.update_layout(
        title="Exposure Concentration",
        xaxis_title="Deciles",
        yaxis_title="Exposure %",
        **layout
    )
    return fig

def create_early_warnings():
    """Creates Multi-line chart for Early Warning Signals."""
    import datetime
    dates = pd.date_range(end=datetime.date.today(), periods=12, freq='ME') # Monthly view
    
    # Mock signals
    bounces = [4.1, 4.2, 4.3, 4.5, 4.8, 4.7, 4.9, 5.1, 5.3, 5.2, 5.5, 5.8]
    utilization = [38, 39, 39, 40, 42, 41, 43, 45, 44, 46, 48, 49]
    dpd = [2, 3, 2, 4, 5, 4, 6, 7, 6, 8, 9, 10]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=bounces, name='Bounce Rate %', line=dict(color=DANGER, width=2)))
    fig.add_trace(go.Scatter(x=dates, y=utilization, name='Avg Utilization %', line=dict(color=WARNING, width=2)))
    fig.add_trace(go.Scatter(x=dates, y=dpd, name='Avg Days Past Due', line=dict(color=SECONDARY, width=2)))

    fig.update_layout(
        title="Early Warning Trends",
        **get_layout_template()
    )
    return fig

def create_density_plot(df, threshold=0.5):
    """Creates an overlapping density plot for Score Distribution."""
    fig = go.Figure()
    
    if df.empty or 'probability_of_default' not in df.columns or 'target' not in df.columns:
        return empty_chart("No Data for Density Plot")

    # Separate data
    default = df[df['target'] == 1]['probability_of_default']
    non_default = df[df['target'] == 0]['probability_of_default']

    # Generate KDE if enough data, else Histogram
    try:
        x_grid = np.linspace(0, 1, 200)
        
        # Non-Default Curve
        if len(non_default) > 1:
            kde_non = gaussian_kde(non_default)
            y_non = kde_non(x_grid)
            fig.add_trace(go.Scatter(
                x=x_grid, y=y_non, mode='lines', name='Non-Default',
                line=dict(color=SUCCESS, width=2),
                fill='tozeroy', fillcolor='rgba(39, 174, 96, 0.1)'
            ))
            
        # Default Curve
        if len(default) > 1:
            kde_def = gaussian_kde(default)
            y_def = kde_def(x_grid)
            fig.add_trace(go.Scatter(
                x=x_grid, y=y_def, mode='lines', name='Default',
                line=dict(color=DANGER, width=2),
                fill='tozeroy', fillcolor='rgba(192, 57, 43, 0.1)'
            ))
            
    except Exception as e:
        # Fallback to simple histogram if KDE fails
        fig.add_trace(go.Histogram(x=non_default, name='Non-Default', marker_color=SUCCESS, opacity=0.5))
        fig.add_trace(go.Histogram(x=default, name='Default', marker_color=DANGER, opacity=0.5))

    # Add Threshold Line
    fig.add_vline(x=threshold, line_width=2, line_dash="dash", line_color=PRIMARY)
    fig.add_annotation(x=threshold, y=0.95, yref="paper", text=f"Cutoff: {threshold:.2f}", showarrow=False, xanchor="left", font=dict(color=PRIMARY))

    layout = get_layout_template()
    layout['xaxis']['title'] = "Probability of Default"
    layout['yaxis']['title'] = "Density"
    
    fig.update_layout(title="Score Distribution (Density)", **layout)
    return fig

def create_lift_chart(df):
    """Creates a Lift Chart with Cumulative Bad Rate."""
    if df.empty or 'probability_of_default' not in df.columns or 'target' not in df.columns:
        return empty_chart("No Data for Lift Chart")

    # Create Deciles
    df = df.copy()
    try:
        df['decile'] = pd.qcut(df['probability_of_default'], 10, labels=False, duplicates='drop')
    except:
        return empty_chart("Not enough data for Deciles")

    grouped = df.groupby('decile')['target'].agg(['count', 'sum']).reset_index()
    grouped['bad_rate'] = grouped['sum'] / grouped['count']
    overall_bad_rate = df['target'].mean()
    grouped['lift'] = grouped['bad_rate'] / overall_bad_rate
    
    # Sort by Decile (High Risk first? usually PD implies higher decile is higher risk)
    # If qcut is ascending, Decile 9 is highest probability.
    
    fig = go.Figure()

    # Bar: Lift per Decile
    fig.add_trace(go.Bar(
        x=grouped['decile'], y=grouped['lift'], name='Decile Lift',
        marker_color=SECONDARY, opacity=0.7
    ))

    # Line: Cumulative Captured Bad % (Gain Chart style) usually, but asked for "Cumulative % of defaulters"
    # Let's calculate Cumulative % of Total Defaults captured
    total_defaults = df['target'].sum()
    grouped_sorted = grouped.sort_values(by='decile', ascending=False) # Highest risk first
    grouped_sorted['cum_defaults'] = grouped_sorted['sum'].cumsum()
    grouped_sorted['cum_captured_pct'] = (grouped_sorted['cum_defaults'] / total_defaults) * 100
    
    fig.add_trace(go.Scatter(
        x=grouped_sorted['decile'], y=grouped_sorted['cum_captured_pct'], 
        name='Cum. Captured Bad %',
        yaxis='y2', mode='lines+markers',
        line=dict(color=WARNING, width=3)
    ))

    layout = get_layout_template()
    layout['xaxis']['title'] = "Risk Decile (9=Highest Risk)"
    layout['yaxis']['title'] = "Lift (vs Avg)"
    layout['yaxis2'] = dict(
        title="Cumulative Captured %",
        overlaying='y',
        side='right',
        showgrid=False,
        range=[0, 110]
    )
    
    fig.update_layout(title="Lift & Cumulative Capture", **layout)
    return fig

def create_psi_chart(df=None):
    """Calculates and plots PSI (Real Current vs Mock Dev)."""
    
    # 1. Current Distribution (Real)
    if df is not None and not df.empty and 'probability_of_default' in df.columns:
        # Bin into 10 buckets (0.0-0.1, 0.1-0.2, etc.)
        counts, _ = np.histogram(df['probability_of_default'], bins=10, range=(0, 1))
        curr_dist = counts / counts.sum()
    else:
        # Fallback if no data
        curr_dist = [0.1] * 10
        
    # 2. Dev Distribution (Mock Baseline - e.g. uniform or slightly different)
    # In a real app, this would come from a reference file
    dev_dist = [0.05, 0.08, 0.12, 0.15, 0.18, 0.15, 0.12, 0.08, 0.05, 0.02] 
    # Normalize Dev to be safe
    dev_dist = np.array(dev_dist) / np.sum(dev_dist)

    buckets = [f"B{i+1}" for i in range(10)]
    
    # PSI Calculation
    psi_values = []
    for d, c in zip(dev_dist, curr_dist):
        if d == 0 or c == 0: 
            psi = 0 
        else: 
            psi = (c - d) * np.log(c / d)
        psi_values.append(psi)
        
    total_psi = sum(psi_values)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=buckets, y=dev_dist, name='Dev (Baseline)', marker_color=ACCENT))
    fig.add_trace(go.Bar(x=buckets, y=curr_dist, name='Current (Real)', marker_color=PRIMARY))
    
    # PSI Status
    status_color = SUCCESS if total_psi < 0.1 else (WARNING if total_psi < 0.25 else DANGER)
    
    layout = get_layout_template()
    layout['title'] = f"Population Stability (PSI = {total_psi:.3f})"
    
    fig.update_layout(**layout)
    fig.add_annotation(
        text=f"<b>Stability Status: {'Stable' if total_psi < 0.1 else 'Drift Detected'}</b>",
        xref="paper", yref="paper",
        x=1, y=1.1, showarrow=False,
        font=dict(color=status_color, size=12)
    )
    
    return fig
