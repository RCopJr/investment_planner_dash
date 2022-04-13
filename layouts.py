from dash import dash_table, html, dcc
import dash_bootstrap_components as dbc
import dash
import plotly.graph_objs as go

from functions import (
    get_column_configs,
    init_from_db,
)

# TODO: use keyword arguements, fix region chart section and add graph, handle too many dropdown selections

navbar = dbc.NavbarSimple(
    children=[
        dbc.Row(
            [
                dbc.Col(
                    dbc.Alert(
                        id="exception-alert-table",
                        color="danger",
                        is_open=False,
                        dismissable=True,
                        duration=4000,
                    ),
                    align="center",
                    lg="auto",
                ),
                dbc.Col("User Chooser (Coming Soon)", align="center", lg="auto"),
            ]
        )
    ],
    brand="Investment Planner",
    brand_style={
        "fontWeight": "900",
        "fontSize": "35px",
    },
)

# TODO: Create function for the three col elements since they will be very similar
def get_headline_data(invest_amount):
    """Generates layout for headline data and loads in invest amount"""
    return [
        dbc.Col(
            dbc.Row(
                dbc.Col(
                    children=dbc.Card(
                        class_name="info invest-amount",
                        children=[
                            dbc.CardBody(
                                [
                                    html.H3("Investment"),
                                    dcc.Input(
                                        id="invest-amount",
                                        value="",
                                        placeholder="$",
                                    ),
                                ]
                            ),
                        ],
                    ),
                    lg=8,
                ),
            ),
            lg=6,
        ),
        dbc.Col(
            children=dbc.Row(
                [
                    dbc.Col(
                        dbc.Row(
                            dbc.Col(
                                children=dbc.Card(
                                    class_name="info secondary",
                                    children=[
                                        dbc.CardBody(
                                            [
                                                html.H3("Cost"),
                                                html.H1(
                                                    id="total-cost", children=["$"]
                                                ),
                                            ]
                                        )
                                    ],
                                ),
                            ),
                            justify="end",
                        ),
                        lg="auto",
                    ),
                    dbc.Col(
                        dbc.Row(
                            dbc.Col(
                                children=dbc.Card(
                                    class_name="info secondary cash",
                                    children=[
                                        dbc.CardBody(
                                            [
                                                html.H3("Cash Left"),
                                                html.H1(id="cash-left", children=["$"]),
                                            ]
                                        )
                                    ],
                                ),
                            ),
                            justify="end",
                        ),
                        lg="auto",
                    ),
                ],
                justify="end",
            ),
            lg=6,
        ),
    ]


def get_plan_controller(investment_data, invest_data_columns):
    """Return initial layour for planner section"""
    return [
        dbc.Col(
            class_name='col-row-adder',
            children=dbc.Card(
                class_name="row-adder",
                children=[
                    dbc.CardBody(
                        [
                            html.H3("Add a Stock"),
                            dcc.Input(
                                id="row-ticker",
                                className="region-input",
                                placeholder="Ticker...",
                            ),
                            dcc.Input(
                                id="row-region",
                                className="region-input",
                                placeholder="Region...",
                            ),
                            dcc.Input(
                                id="row-allocation",
                                className="region-input",
                                placeholder="Allocation...",
                            ),
                            dbc.Button(
                                id="add-btn",
                                children=[html.H3("Add")],
                                n_clicks=0,
                            ),
                        ]
                    )
                ],
            ),
            lg=2,
        ),
        dbc.Col(
            [
                dbc.Row(
                    [
                        dbc.Col(class_name='col-planning-title', children=[html.H2("Planning")], lg=2),
                        dbc.Col(class_name='col-table-buttons',children=[
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dcc.Upload(
                                            id='planner-upload',
                                            children=[html.H3(id='upload-text', children=["Upload"])],
                                            accept='.xlsx',
                                            style={
                                                'padding': '7px 20px',
                                                'backgroundColor': 'white',
                                                'width': 'auto',
                                                'height': '38px',
                                                'lineHeight': '32px',
                                                'borderWidth': '1px',
                                                'borderStyle': 'dashed',
                                                'borderRadius': '15px',
                                                'textAlign': 'center',
                                                'fontSize': '15px'
                                            },
                                        ),
                                        xs=2,
                                        lg='auto',
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            id="clear-ma-btn",
                                            class_name="table-editor",
                                            children=[html.H3("Clear")],
                                            n_clicks=0,
                                        ),
                                        xs=2,
                                        lg="auto",
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            id="default-alloc-btn",
                                            class_name="table-editor",
                                            children=[html.H3("Default")],
                                            n_clicks=0,
                                        ),
                                        xs=2,
                                        lg="auto",
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            id="update-price-btn",
                                            class_name="table-editor",
                                            children=[html.H3("Update")],
                                            n_clicks=0,
                                        ),
                                        xs=2,
                                        lg="auto",
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            id="undo-btn",
                                            class_name="table-editor",
                                            children=[html.H3("Undo")],
                                            n_clicks=0,
                                        ),
                                        xs=2,
                                        lg="auto",
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            id="export-btn",
                                            class_name="table-editor",
                                            children=[html.H3("Export")],
                                            n_clicks=0,
                                        ),
                                        xs=2,
                                        lg="auto",
                                    ),
                                ],
                                align="center",
                                justify="end",
                            )],
                            lg=10,
                        ),
                    ],
                    align="center",
                ),
                dbc.Row(
                    [
                        dbc.Col(class_name='col-table',
                            children=dbc.Card(
                                class_name="table-card",
                                children=dbc.CardBody(
                                    class_name="table-card-body",
                                    children=[
                                        dbc.Spinner(
                                            dash_table.DataTable(
                                                id="investment-data",
                                                columns=invest_data_columns,
                                                row_deletable=True,
                                                css=[
                                                    {
                                                        "selector": "table",
                                                        "rule": "border-collapse: separate; border-spacing: 0 8px;",
                                                    }
                                                ],
                                                style_table={
                                                    "borderRadius": "1.093rem",  # Needed to be adjusted to account for position change
                                                    "overflow-x": "scroll",
                                                },
                                                style_cell={
                                                    "fontSize": "17px",
                                                    "textAlign": "left",
                                                    "padding": "7px",
                                                },
                                                style_data={
                                                    "backgroundColor": "#f9f9f9",
                                                    "border": "none",
                                                    "color": "#2c2c2c",
                                                },
                                                style_as_list_view=True,
                                                style_data_conditional=[
                                                    {
                                                        "if": {"column_editable": True},
                                                        "backgroundColor": "white",
                                                        "color": "#2c2c2c",
                                                    },
                                                    {
                                                        "if": {"state": "selected"},
                                                        "backgroundColor": "inherit !important",
                                                        "border": "inherit !important",
                                                    },
                                                ],
                                                style_header={
                                                    "backgroundColor": "white",
                                                    "borderTop": "none",
                                                    "color": "#2c2c2c",
                                                    "fontWeight": "900",
                                                    "fontSize": "18px",
                                                },
                                                style_header_conditional=[
                                                    {
                                                        "if": {"column_editable": True},
                                                        "backgroundColor": "white",
                                                        "color": "#2c2c2c",
                                                    }
                                                ],
                                                page_size=4,
                                            )
                                        ),
                                    ],
                                ),
                            ),
                        )
                    ]
                ),
            ],
            lg=10,
        ),
    ]


hist_graph_display = [
    dbc.Row(
        [
            dbc.Col(class_name='col-stock-hist-title', children=[html.H2("Stock History")], align="center", lg=4),
            dbc.Col(class_name='col-stock-hist-dropdown', children=[
                dbc.Row(
                    dbc.Col(
                        dcc.Dropdown(
                            id="etf-dropdown",
                            options=["VCN.TO", "HXQ.TO", "XIT.TO"],
                            placeholder="Stocks...",
                            multi=True,
                        ),
                        lg="auto",
                    ),
                    justify="end",
                )],
                align="center",
                lg="8",
            ),
        ]
    ),
    dbc.Row(
        children=[
            dbc.Col(class_name='col-hist-graph',children=[
                dbc.Card(
                    dbc.CardBody(
                        dcc.Graph(
                            id="etf-graph",
                            config={
                                "modeBarButtonsToRemove": [
                                    "sendDataToCloud",
                                    "toImage",
                                    "autoScale2d",
                                    "hoverClosestCartesian",
                                    "hoverCompareCartesian",
                                    "select2d",
                                    "lasso2d",
                                    "zoomIn2d",
                                    "zoomOut2d",
                                ]
                            },
                        )
                    )
                )]
            )
        ],
    ),
]


def get_region_display(region_data_columns):
    "Get region graph and table"
    return [
        dbc.Row(class_name='col-region-graph-title', children=[dbc.Col(children=html.H2("Region Chart"))], align="center"),
        dbc.Row(
            children=[
                dbc.Col(class_name='col-region-graph', children=[
                    dbc.Card(
                        class_name="region-card",
                        children=[
                            dbc.CardBody(
                                children=[
                                    dash_table.DataTable(
                                        id="region-data",
                                        columns=region_data_columns,
                                        css=[
                                            {
                                                "selector": "table",
                                                "rule": "border-collapse: separate; border-spacing: 0 8px;",
                                            }
                                        ],
                                        style_table={
                                            "borderRadius": "1.093rem",  # Needed to be adjusted to account for position change
                                            "overflow": "hidden",
                                        },
                                        style_cell={
                                            "fontSize": 18,
                                            "textAlign": "left",
                                        },
                                        style_data={
                                            "backgroundColor": "#f9f9f9",
                                            "border": "none",
                                            "color": "#2c2c2c",
                                        },
                                        style_as_list_view=True,
                                        style_data_conditional=[
                                            {
                                                "if": {"column_editable": True},
                                                "backgroundColor": "white",
                                                "color": "#2c2c2c",
                                            },
                                            {
                                                "if": {"state": "selected"},
                                                "backgroundColor": "inherit !important",
                                                "border": "inherit !important",
                                            },
                                        ],
                                        style_header={
                                            "backgroundColor": "white",
                                            "borderTop": "none",
                                            "color": "#2c2c2c",
                                            "fontWeight": "900",
                                            "fontSize": "16px",
                                        },
                                        style_header_conditional=[
                                            {
                                                "if": {"column_editable": True},
                                                "backgroundColor": "white",
                                                "color": "#2c2c2c",
                                            }
                                        ],
                                        page_size=4,
                                    )
                                ],
                            )
                        ],
                    )],
                )
            ],
        ),
    ]


def get_graph_data(region_data_columns):
    """Get graph layout"""
    return [
        dbc.Col(hist_graph_display, lg=7),
        dbc.Col(get_region_display(region_data_columns), lg=5),
    ]


def get_main_layout(collection):
    # Connect to local server and access document
    main_document = collection.find_one()  # Only have my document for now

    investment_data, invest_amount = init_from_db(main_document)

    # Create column configs for dataframes
    invest_data_columns = get_column_configs(
        investment_data.columns.values,
        ["Manual Adjustments", "Planned Allocation"],
        ["Price", "Costs"],
        ["Planned Allocation", "Actual Allocation"],
    )

    region_data_columns = get_column_configs(
        ["Region", "Costs", "Allocation"],
        [],
        ["Costs"],
        ["Allocation"],
    )
    return html.Div(
        id="main-div",
        children=[
            dcc.Download(id="download-xlsx-dataframe"),
            dcc.Store(id="app-status", data="Not started"),
            dcc.Store(id="saved-status-store", clear_data=True),
            dcc.Store(id='initial-table-store', storage_type='session'),
            navbar,
            dbc.Container(
                children=[
                    dbc.Row(
                        class_name="row-main info-section",
                        children=get_headline_data(invest_amount),
                    ),
                    dbc.Row(
                        class_name="row-main table-section",
                        children=get_plan_controller(
                            investment_data, invest_data_columns
                        ),
                    ),
                    dbc.Row(
                        class_name="row-main graph-section",
                        children=get_graph_data(region_data_columns),
                    ),
                ],
                fluid=True,
            ),
        ],
    )
