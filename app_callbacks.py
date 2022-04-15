from subprocess import call
import pandas as pd
import io
import base64
from dash import dcc, html, Input, Output, State, callback, callback_context
import dash
import plotly.graph_objs as go

# TODO: Finish setting up callbacks for the rest of the buttons and what not

# Functions
from functions import (
    get_df,
    update_investment_plan_table,
    update_region_data_table,
    create_doc_obj,
    create_history_graph,
    handle_btn_actions,
    init_from_db,
    generate_spending_summary,
    verify_xlsx,
)

from db_functions import get_collection, update_from_obj

from try_excepts import try_invest_amount_conv

collection = get_collection("investment_plans")

# TODO: store prices in store so that it happens in background, store region data in store and show pie chart

@callback(
    Output('exception-alert-xlsx', 'is_open'),
    Output('exception-alert-xlsx', 'children'),
    Output('success-alert-xlsx', 'is_open'),
    Output('success-alert-xlsx', 'children'),
    Output('initial-table-store', 'data'),
    Output('planner-upload', 'children'),
    Output('planner-upload', 'contents'),
    Input('planner-upload', 'contents'),
    State('planner-upload', 'filename'),
    State('initial-table-store', 'data')
)
def store_xlsx_in_store(content, filename, data):
    """Updates store data with uploaded xlsx file"""
    if content:
        content_type, content_string = content.split(',')

        decoded = base64.b64decode(content_string)
        #TODO: omit this column when exportin as well and avoid dropping it here
        df = pd.read_excel(io.BytesIO(decoded), index_col=None).drop(columns=['Unnamed: 0'])
        alert_msg, is_valid = verify_xlsx(df) 
        if not is_valid:
            return True, alert_msg, False, "", dash.no_update, dash.no_update, None

        json_data = df.to_json()
        invest_data_df = pd.read_json(json_data)
        return False, "", True, alert_msg, json_data, html.H3(id='upload-text', children=[filename]), None
    return False, "", False, "", None, dash.no_update, dash.no_update

@callback(
    Output("download-xlsx-dataframe", "data"),
    Input("export-btn", "n_clicks"),
    State("investment-data", "data"),
    State("investment-data", "columns"),
    prevent_initial_call=True,
)
def export_investment_plan(export_btn, table_rows, table_columns):
    """Exports investment data to Excel"""
    invest_data = get_df(table_rows, table_columns)
    return dcc.send_data_frame(invest_data.to_excel, "my_investment_plan.xlsx")


@callback(
    Output("invest-amount", "value"),
    Input("invest-amount", "value"),
    State("app-status", "data"),
)
def handle_invest_amount(value, app_status):
    """Makes sure that '$' is at beginning of each input"""
    invest_amount = value
    value = str(invest_amount)
    if value:
        if value == "$ ":
            return ""
        elif value[0] == "$":
            return dash.no_update
        else:
            return "$ " + value
    return dash.no_update


@callback(
    Output("etf-dropdown", "options"),
    Input("investment-data", "data"),
    State("investment-data", "columns"),
)
def update_etf_options(table_rows, table_columns):
    """Updates etf dropdown options based on etfs in table"""
    invest_data_df = get_df(table_rows, table_columns)
    etf_list = invest_data_df["Ticker"].tolist()
    return etf_list


@callback(
    Output("etf-graph", "figure"),
    Input("etf-dropdown", "value"),
    State("investment-data", "data"),
    State("investment-data", "columns"),
)
def update_etf_graph(dropdown_value, table_rows, table_columns):
    """Updates ETF graph based on provided ETF ticker"""
    invest_data_df = get_df(table_rows, table_columns)
    # TODO: add placeholder and check if etf exists or etf list is empty
    # For multi-dropdowns, if one value, passes string, if multiple, passes list

    etfs = [dropdown_value] if isinstance(dropdown_value, str) else dropdown_value
    fig = go.Figure(layout={"template": "xgridoff"})
    return create_history_graph(fig, etfs)


# Remember: Only have on callback for every output you want, have an input parameter for each input
@callback(
    Output("investment-data", "data"),
    Output("total-cost", "children"),
    Output("cash-left", "children"),
    Output("region-data", "data"),
    Output("exception-alert-table", "children"),
    Output("exception-alert-table", "is_open"),
    Output("app-status", "data"),
    Input("invest-amount", "value"),
    Input("investment-data", "data"),
    State("investment-data", "data_previous"),
    Input("investment-data", "columns"),
    State("region-data", "columns"),
    Input("clear-ma-btn", "n_clicks"),
    Input("default-alloc-btn", "n_clicks"),
    Input("add-btn", "n_clicks"),
    Input("update-price-btn", "n_clicks"),
    Input("undo-btn", "n_clicks"),
    Input('initial-table-store', 'data'),
    State("row-ticker", "value"),
    State("row-region", "value"),
    State("row-allocation", "value"),
    Input("app-status", "data"),
)
def update_invest_data(
    invest_amount_,
    table_rows,
    prev_table_rows,
    table_columns,
    region_table_columns,
    clear_ma_btn,
    default_alloc_btn,
    add_btn,
    update_price_btn,
    undo_btn,
    json_data,
    new_ticker,
    new_region,
    new_allocation,
    app_status,
):
    """Updates investment datatable, region datable, and general info"""
    # TODO: Add Exception handling (i.e. passing a str as the investment amount)
    # Stores data of changed or initial dataframe
    # Handle button actions
    changed_id = [p["prop_id"] for p in callback_context.triggered][0]
    has_started = True
    if json_data:
        if changed_id == "initial-table-store.data":
            invest_data_df = pd.read_json(json_data)
        else:
            invest_data_df = get_df(table_rows, table_columns)
        # TODO: Put all try except in here
        if invest_amount_:
            invest_amount_ = invest_amount_[1:]
        invest_amount_float, error_info = try_invest_amount_conv(invest_amount_)
        # Returns errors from trying conversion
        if error_info:
            #TODO: find solution for when changed_id changes while uploading xlsx
            if changed_id == "initial-table-store.data":
                table_df = invest_data_df.to_dict("records")
            else:
                table_df = dash.no_update
            return (
                table_df,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                html.P(error_info),
                True,
                dash.no_update,
            )
        # Set investment amount to input value or outcome of manual adjustments
        invest_amount = (
            invest_amount_float
            if invest_amount_
            else (invest_data_df["Manual Adjustments"] * invest_data_df["Price"]).sum()
        )
        no_invest_amount = invest_amount == 0
        # Make sure to convert to correct datatypes before processing
        # TODO: Check why highlighting and deleting invest_amount does not update correctly
        for col in invest_data_df.columns.values:
            try:
                invest_data_df[col] = invest_data_df[col].astype(float)
            except ValueError:
                pass
        invest_data_df, error_info = handle_btn_actions(
            changed_id,
            collection,
            new_ticker,
            new_region,
            new_allocation,
            invest_data_df,
            prev_table_rows,
            table_columns,
        )

        # Returns errors from trying to handle the button actions
        if error_info:
            return (
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                html.P(error_info),
                True,
                dash.no_update,
            )

        # Update table values
        invest_data_df = update_investment_plan_table(
            invest_data_df, invest_amount, no_invest_amount
        )

        total_cost, cash_left = generate_spending_summary(invest_data_df, invest_amount)

        # Update Region Dataframe
        region_df = update_region_data_table(
            invest_data_df,
            invest_amount,
            cash_left,
            region_table_columns,
            no_invest_amount,
        )

        return (
            invest_data_df.to_dict("records"),
            "$ {:.2f}".format(total_cost),
            "$ {:.2f}".format(cash_left),
            region_df.to_dict("records"),
            dash.no_update,
            False,
            dash.no_update if has_started else "Started",
        )
    else:
        return dash.no_update,  dash.no_update,  dash.no_update,  dash.no_update,  dash.no_update, False, dash.no_update   
