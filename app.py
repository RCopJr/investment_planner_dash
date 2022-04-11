from dash import Dash
import dash_bootstrap_components as dbc

from layouts import get_main_layout

import app_callbacks

from db_functions import get_collection


external_stylesheets = [dbc.themes.SANDSTONE]

app = Dash(__name__, external_stylesheets=external_stylesheets)

collection = get_collection("investment_plans")
app.layout = get_main_layout(collection)

if __name__ == "__main__":
    app.run_server(
        debug=True, use_reloader=False
    )  # Need to set debug=False to avoid connection issues with yfinance
