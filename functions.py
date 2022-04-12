from dash.dash_table import FormatTemplate
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objs as go
import dash

from db_functions import get_column

# TODO: refactor these functions into separate files as well


def generate_spending_summary(invest_data_df, invest_amount):
    """Generates spending summary (total cost and cash left)"""
    # Get total buy cost and cash left
    total_cost = invest_data_df["Costs"].sum()
    cash_left = invest_amount - total_cost if invest_amount else 0

    return total_cost, cash_left


def generate_invest_summary(invest_data_df):
    """Generates investment summary of what etfs to buy"""
    etfs = invest_data_df["Ticker"].tolist()
    final_quants = invest_data_df["Final Quantities"].tolist()
    invest_summary = ""

    for etf, quant in zip(etfs, final_quants):
        invest_summary = invest_summary + "{}: {} | ".format(etf, int(quant))

    return invest_summary

#TODO: update functionality with data from a store
def get_default_allocs(collection, invest_data_df):
    """Returns the default planned allocations saved in the db"""
    #planned_allocs = get_column(collection, "ramonito", "planned_alloc")
    # Make sure that lengths correspond to each other
    #if len(planned_allocs) < len(invest_data_df):
    #    for i in range(len(planned_allocs), len(invest_data_df)):
    #        planned_allocs.append(float(invest_data_df.loc[i, ["Planned Allocation"]]))
    #elif len(invest_data_df) < len(planned_allocs):
    #    planned_allocs = planned_allocs[: len(invest_data_df)]

    #return planned_allocs
    return invest_data_df['Planned Allocation']


def generate_row(new_ticker, new_region, new_allocation):
    """Generates new df row with base information"""
    stock_info = yf.Ticker(new_ticker).info
    price = stock_info["regularMarketPrice"]
    # This means that ticker could not be found
    if price == None:
        return None, False
    else:
        return (
            pd.DataFrame(
                {
                    "Region": [new_region],
                    "Ticker": [new_ticker.upper()],
                    "Price": [price],
                    "Planned Allocation": [new_allocation],
                }
            ),
            True,
        )


def handle_btn_actions(
    changed_id,
    collection,
    new_ticker,
    new_region,
    new_allocation,
    invest_data_df,
    prev_table_rows,
    table_columns,
):
    """Update front-end based on the button clicked"""
    # TODO: refactor to remove the dash.update stuff
    error_info = None
    if "clear-ma-btn" in changed_id:
        invest_data_df["Manual Adjustments"].values[:] = 0
    elif "default-alloc-btn" in changed_id:
        # Query db for planned_alloc and set df column
        planned_allocs = get_default_allocs(collection, invest_data_df)
        invest_data_df["Planned Allocation"] = np.array(planned_allocs)
    elif "add-btn" in changed_id:
        if new_ticker and new_region and new_allocation:
            try:
                new_allocation = float(new_allocation)
                new_row, found = generate_row(new_ticker, new_region, new_allocation)
                if found:
                    invest_data_df = pd.concat([invest_data_df, new_row]).fillna(0)
                else:
                    # If ticker data could not be retrieved
                    error_info = "Could not get data for new ticker. Are you sure your ticker exists?"
            except ValueError:  # If float conversion failed
                error_info = "Make sure allocation is valid."
        else:
            error_info = "Fill in all fields before trying to add a row."

    elif "update-price-btn" in changed_id:
        # TODO: Better implementation so no need to save after every update
        etf_prices = [
            yf.Ticker(etf).info["regularMarketPrice"]
            for etf in invest_data_df["Ticker"]
        ]
        if None in etf_prices:
            error_info = "Could not get price data for one of the tickers"
        else:
            invest_data_df.loc[:, ["Price"]] = etf_prices
    elif "undo-btn" in changed_id:
        if prev_table_rows:
            invest_data_df = get_df(prev_table_rows, table_columns)

    return invest_data_df, error_info


def init_from_db(main_document):
    """Return df generated from DB document"""
    # Populate global vars with document values
    invest_amount = float(main_document["invest_amount"])
    regions = main_document["region"]
    etf_list = main_document["ticker"]
    planned_allocation = np.array(main_document["planned_alloc"])
    manual_adjusts = np.array(main_document["manual_adjusts"])
    etf_prices = np.array(main_document["price"])

    # Calculate document dependant lists
    quantities = np.floor(planned_allocation * invest_amount / etf_prices).astype(int)
    final_quantities = quantities + manual_adjusts
    costs = final_quantities * etf_prices
    actual_allocations = costs / invest_amount

    # Create initial dataframe
    data = {
        "Region": regions,
        "Ticker": etf_list,
        "Price": etf_prices,
        "Planned Allocation": planned_allocation,
        "Quantities": quantities,
        "Manual Adjustments": manual_adjusts,
        "Final Quantities": final_quantities,
        "Costs": costs,
        "Actual Allocation": actual_allocations,
    }
    return pd.DataFrame(data), invest_amount


def create_history_graph(fig, etfs):
    """Generate graph given a figure object and list of etfs"""
    title = ""
    if etfs:
        for etf in etfs:
            title = title + ", " + str(etf)
            data = yf.Ticker(str(etf))
            hist = data.history(period="max", interval="1d")
            fig.add_trace(
                go.Scatter(x=hist.index, y=hist["Close"], mode="lines", name=str(etf))
            )
    # edit margins
    fig.update_layout(margin=dict(l=15, r=15, t=15, b=15), height=241)

    # X-Axes
    fig.update_xaxes(
        title=None,
        rangeselector=dict(
            buttons=list(
                [
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(step="all", label="MAX"),
                ]
            )
        ),
    )

    return fig


def get_df(table_rows, table_columns):
    """Convert dash_table to df in callback"""
    df = (
        pd.DataFrame(table_rows, columns=[c["name"] for c in table_columns])
        .fillna(0)
        .replace("", 0)
    )
    return df


def create_doc_obj(invest_data_df, invest_amount):
    """Creates document object to be saved into collection"""
    obj = {
        "invest_amount": invest_amount,
        "region": invest_data_df["Region"].tolist(),
        "ticker": invest_data_df["Ticker"].tolist(),
        "price": invest_data_df["Price"].tolist(),
        "planned_alloc": invest_data_df["Planned Allocation"].tolist(),
        "manual_adjusts": invest_data_df["Manual Adjustments"].tolist(),
    }
    return obj


def get_column_configs(
    column_values,
    editable,
    currency_related,
    percentage_related,
):
    """Return config list for dashtable given column data"""
    # Setup formatting objects
    money = FormatTemplate.money(2)
    percentage = FormatTemplate.percentage(0)
    columns = []
    # create configs
    for column in column_values:
        col_config = {"name": str(column), "id": str(column)}
        if column in editable:
            # TODO: find better way to set type of column (acceptable for now since all editable columns are numeric)
            col_config.update({"editable": True, "type": "numeric"})
        if column in currency_related:
            col_config.update({"type": "numeric", "format": money})
        elif column in percentage_related:
            col_config.update({"type": "numeric", "format": percentage})
        columns.append(col_config)
    return columns


def update_investment_plan_table(invest_data_df, invest_amount, using_ma_only=False):
    """Updates investment plan table values depending on investment amount"""
    # Update quantities based on investment amount
    if not using_ma_only:
        invest_data_df["Quantities"] = np.floor(
            invest_data_df["Planned Allocation"].astype(float)
            * invest_amount
            / invest_data_df["Price"]
        ).astype(int)
    # Update Final Quantities
    invest_data_df["Final Quantities"] = (
        invest_data_df["Quantities"] + invest_data_df["Manual Adjustments"]
    )
    # Update Costs
    invest_data_df["Costs"] = (
        invest_data_df["Final Quantities"] * invest_data_df["Price"]
    )
    # Update Actual Allocations
    if not using_ma_only:
        invest_data_df["Actual Allocation"] = invest_data_df["Costs"].div(invest_amount)
    else:
        invest_data_df.loc[:, "Actual Allocation"] = (
            invest_data_df["Costs"].div(invest_amount) if invest_amount else 0
        )

    return invest_data_df


def update_region_data_table(
    invest_data_df, invest_amount, cash_left, region_table_columns, using_ma_only=False
):
    """Update region table depending on investman plan table data and invest amount"""
    region_data = []
    for region in set(invest_data_df["Region"].to_list()):
        region_costs = invest_data_df.loc[
            invest_data_df["Region"] == region, "Costs"
        ].sum()
        if not using_ma_only:  # Need to check divide by 0
            region_allocation = region_costs / invest_amount
        else:
            region_allocation = (region_costs / invest_amount) if invest_amount else 0
        region_data.append([region, region_costs, region_allocation])

    # Add cash to region dataframe as extra row
    region_data.append(
        [
            "Cash",
            cash_left if invest_amount else 0,
            cash_left / invest_amount if invest_amount else 0,
        ]
    )

    return pd.DataFrame(
        data=region_data, columns=[c["name"] for c in region_table_columns]
    )
