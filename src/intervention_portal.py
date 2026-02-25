import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from pages import intervention

# Initialize App (Standalone)
app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="CREDIX | Secure Support"
)

# Define Layout - Single Page Focus
app.layout = html.Div(
    [
        dcc.Location(id="url"), # Needed for callback compatibility
        html.Div(id="page-content", className="content-standalone") 
    ],
    style={"backgroundColor": "#f4f6f8", "minHeight": "100vh"}
)

# Reuse the existing intervention layout and callbacks
# We manually trigger the layout rendering since there's no sidebar/router
app.layout.children.append(intervention.layout())

# Register Callbacks (Indirectly via import, but need to ensure app context)
# The callbacks in intervention.py are registered to 'callback' which defaults to the active app.
# Since this is the main script, it should work.

if __name__ == "__main__":
    print("[INFO] Starting Standalone Intervention Portal on Port 8051...")
    # Serve on 8051 as requested
    app.run(debug=True, port=8051)
