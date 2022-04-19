from dash import Dash
import dash_bootstrap_components as dbc

from layouts import get_main_layout

import app_callbacks

external_stylesheets = [dbc.themes.SANDSTONE]

app = Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

app.layout = get_main_layout()

if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)
