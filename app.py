"""
JIRA Dashboard Application

A Dash-based dashboard for project managers to track JIRA issues,
deadlines, subtasks, and urgency metrics.
"""

import logging
from datetime import datetime

import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
from flask_caching import Cache

from config import Config
from data import JiraClient, DataProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO if not Config.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Wells Fargo brand palette
WF_RED    = '#D71E28'
WF_DARK   = '#1A1A1A'
WF_GREY1  = '#4A4A4A'   # dark-grey text
WF_GREY2  = '#6C6C6C'   # mid-grey muted
WF_GREY3  = '#F2F2F2'   # light-grey card bg
WF_WHITE  = '#FFFFFF'

CUSTOM_CSS = f"""
body {{
    background-color: {WF_GREY3};
    color: {WF_GREY1};
    font-family: 'Segoe UI', Arial, sans-serif;
}}
h1, h2, h3, h4, h5, h6 {{
    color: {WF_DARK};
}}
.card {{
    border: 1px solid #D9D9D9;
    border-radius: 6px;
    background-color: {WF_WHITE};
}}
.card-header {{
    background-color: {WF_DARK} !important;
    color: {WF_WHITE} !important;
    border-bottom: 3px solid {WF_RED};
    border-radius: 6px 6px 0 0 !important;
}}
.card-header h5 {{
    color: {WF_WHITE} !important;
    margin: 0;
}}
.text-muted {{
    color: {WF_GREY2} !important;
}}
.btn-primary {{
    background-color: {WF_RED} !important;
    border-color: {WF_RED} !important;
    color: {WF_WHITE} !important;
}}
.btn-primary:hover {{
    background-color: #a8161e !important;
    border-color: #a8161e !important;
}}
.btn-success {{
    background-color: {WF_DARK} !important;
    border-color: {WF_DARK} !important;
    color: {WF_WHITE} !important;
}}
.btn-success:hover {{
    background-color: {WF_GREY1} !important;
    border-color: {WF_GREY1} !important;
}}
.nav-link.active, .dropdown-item:active {{
    background-color: {WF_RED} !important;
}}
.Select-control {{
    border-color: #CCCCCC !important;
}}
"""

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="JIRA Dashboard",
    suppress_callback_exceptions=True
)

# Inject custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
''' + CUSTOM_CSS + '''
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Configure caching
cache = Cache(app.server, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': Config.CACHE_TIMEOUT
})

# Global variables
jira_client = None
issues_df = pd.DataFrame()


def initialize_jira_client():
    """Initialize JIRA client with error handling."""
    global jira_client
    
    try:
        Config.validate()
        jira_client = JiraClient()
        
        if jira_client.test_connection():
            logger.info("JIRA client initialized successfully")
            return True
        else:
            logger.error("JIRA connection test failed")
            return False
            
    except Exception as e:
        logger.error(f"Failed to initialize JIRA client: {e}")
        return False


@cache.memoize(timeout=Config.CACHE_TIMEOUT)
def fetch_and_process_data():
    """Fetch issues from JIRA and process them."""
    global jira_client, issues_df
    
    try:
        if jira_client is None:
            if not initialize_jira_client():
                return pd.DataFrame()
        
        logger.info("Fetching issues from JIRA...")
        issues = jira_client.fetch_issues()
        
        logger.info("Processing issue data...")
        issues_df = DataProcessor.issues_to_dataframe(issues)
        
        logger.info(f"Successfully processed {len(issues_df)} issues")
        return issues_df
        
    except Exception as e:
        logger.error(f"Error fetching/processing data: {e}")
        return pd.DataFrame()


def create_header():
    """Create dashboard header."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("JIRA Dashboard", style={'color': WF_RED, 'fontWeight': '700'}),
                html.P(
                    "Issue Tracking Overview",
                    className="lead text-muted"
                )
            ], width=8),
            dbc.Col([
                html.Div([
                    html.P(
                        id="last-updated",
                        className="text-muted mb-2",
                        style={'fontSize': '0.9em'}
                    ),
                    dbc.Button(
                        "Refresh Data",
                        id="refresh-button",
                        color="primary",
                        size="sm"
                    )
                ], className="text-end")
            ], width=4)
        ], className="mb-4")
    ], fluid=True)


def create_filters():
    """Create filter components."""
    return dbc.Container([
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Status Filter"),
                        dcc.Dropdown(
                            id="status-filter",
                            options=[
                                {'label': 'All', 'value': 'all'},
                                {'label': 'Overdue', 'value': 'overdue'},
                                {'label': 'Due This Week', 'value': 'due_this_week'},
                                {'label': 'Upcoming', 'value': 'upcoming'}
                            ],
                            value='all',
                            clearable=False
                        )
                    ], md=3),
                    dbc.Col([
                        html.Label("Priority Filter"),
                        dcc.Dropdown(
                            id="priority-filter",
                            options=[],
                            multi=True,
                            placeholder="All priorities"
                        )
                    ], md=3),
                    dbc.Col([
                        html.Label("Assignee Filter"),
                        dcc.Dropdown(
                            id="assignee-filter",
                            options=[],
                            multi=True,
                            placeholder="All assignees"
                        )
                    ], md=3),
                    dbc.Col([
                        html.Label("Project Filter"),
                        dcc.Dropdown(
                            id="project-filter",
                            options=[],
                            multi=True,
                            placeholder="All projects"
                        )
                    ], md=3)
                ])
            ])
        ], className="mb-4")
    ], fluid=True)


CARD_CLICK_STYLE = {
    'cursor': 'pointer',
    'transition': 'box-shadow 0.2s',
    'userSelect': 'none',
}


def create_metric_cards():
    """Create metric cards for key statistics."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Overdue", className="card-title", style={'color': WF_RED}),
                            html.H2(id="overdue-count", style={'color': WF_RED}),
                            html.P("Issues past due date", className="text-muted")
                        ])
                    ], className="text-center h-100")
                ], id="card-overdue", style=CARD_CLICK_STYLE, n_clicks=0)
            ], md=2),
            dbc.Col([
                html.Div([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Due This Week", className="card-title", style={'color': WF_DARK}),
                            html.H2(id="due-week-count", style={'color': WF_DARK}),
                            html.P("Issues due in 7 days", className="text-muted")
                        ])
                    ], className="text-center h-100")
                ], id="card-due-week", style=CARD_CLICK_STYLE, n_clicks=0)
            ], md=2),
            dbc.Col([
                html.Div([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Upcoming", className="card-title", style={'color': WF_GREY1}),
                            html.H2(id="upcoming-count", style={'color': WF_GREY1}),
                            html.P("Issues due later", className="text-muted")
                        ])
                    ], className="text-center h-100")
                ], id="card-upcoming", style=CARD_CLICK_STYLE, n_clicks=0)
            ], md=2),
            dbc.Col([
                html.Div([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("High Priority", className="card-title", style={'color': WF_DARK}),
                            html.H2(id="high-priority-count", style={'color': WF_DARK}),
                            html.P("High/Highest priority", className="text-muted")
                        ])
                    ], className="text-center h-100")
                ], id="card-high-priority", style=CARD_CLICK_STYLE, n_clicks=0)
            ], md=2),
            dbc.Col([
                html.Div([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Long in Backlog", className="card-title", style={'color': WF_RED}),
                            html.H2(id="backlog-count", style={'color': WF_RED}),
                            html.P("Issues in Backlog > 3 months", className="text-muted")
                        ])
                    ], className="text-center h-100")
                ], id="card-backlog", style=CARD_CLICK_STYLE, n_clicks=0)
            ], md=4),
        ], className="mb-4")
    ], fluid=True)


def create_card_modal():
    """Create a shared modal for card drill-down details."""
    return dbc.Modal([
        dbc.ModalHeader(
            dbc.ModalTitle(id="card-modal-title"),
            style={'backgroundColor': WF_DARK, 'color': WF_WHITE}
        ),
        dbc.ModalBody([
            dash_table.DataTable(
                id="card-modal-table",
                columns=[],
                data=[],
                page_size=20,
                sort_action="native",
                filter_action="native",
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '9px 12px',
                    'fontSize': '13px',
                    'color': WF_GREY1,
                    'backgroundColor': WF_WHITE,
                    'border': '1px solid #E0E0E0',
                    'maxWidth': '260px',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                },
                style_header={
                    'backgroundColor': WF_RED,
                    'color': WF_WHITE,
                    'fontWeight': '700',
                    'fontSize': '13px',
                    'border': f'1px solid {WF_RED}',
                    'textAlign': 'left',
                    'padding': '9px 12px',
                },
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': WF_GREY3},
                ],
                tooltip_data=[],
                tooltip_duration=None,
            )
        ]),
        dbc.ModalFooter(
            dbc.Button("Close", id="card-modal-close", color="secondary", size="sm")
        ),
    ], id="card-modal", is_open=False, size="xl", scrollable=True)


def create_urgency_table():
    """Create interactive urgency breakdown table."""
    return dbc.Container([
        dbc.Card([
            dbc.CardHeader(html.H5("Urgency Breakdown")),
            dbc.CardBody([
                dash_table.DataTable(
                    id="urgency-table",
                    columns=[],
                    data=[],
                    page_size=15,
                    sort_action="native",
                    filter_action="native",
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px 14px',
                        'fontSize': '13px',
                        'color': WF_GREY1,
                        'backgroundColor': WF_WHITE,
                        'border': '1px solid #E0E0E0',
                    },
                    style_header={
                        'backgroundColor': WF_RED,
                        'color': WF_WHITE,
                        'fontWeight': '700',
                        'fontSize': '13px',
                        'border': f'1px solid {WF_RED}',
                        'textAlign': 'left',
                        'padding': '10px 14px',
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': WF_GREY3,
                        },
                        {
                            'if': {'filter_query': '{Days Past Due} > 0'},
                            'color': WF_RED,
                            'fontWeight': '600',
                        }
                    ]
                )
            ])
        ], className="mb-4")
    ], fluid=True)


def create_issues_table():
    """Create detailed issues table."""
    return dbc.Container([
        dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col(html.H5("Detailed Issues"), width=6),
                    dbc.Col([
                        dbc.Button(
                            "Export CSV",
                            id="export-button",
                            color="success",
                            size="sm",
                            className="float-end"
                        )
                    ], width=6)
                ])
            ]),
            dbc.CardBody([
                dash_table.DataTable(
                    id="issues-table",
                    columns=[],
                    data=[],
                    page_size=Config.TABLE_PAGE_SIZE,
                    sort_action="native",
                    filter_action="native",
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px',
                        'fontSize': '14px'
                    },
                    style_header={
                        'backgroundColor': '#f8f9fa',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{is_overdue} = true'},
                            'backgroundColor': '#f8d7da',
                            'color': '#721c24'
                        }
                    ]
                )
            ])
        ])
    ], fluid=True)


# Main layout
app.layout = html.Div([
    dcc.Store(id='data-store'),
    dcc.Store(id='card-context-store'),   # tracks which card was clicked
    dcc.Interval(
        id='interval-component',
        interval=Config.CACHE_TIMEOUT * 1000,  # in milliseconds
        n_intervals=0
    ),
    create_header(),
    create_filters(),
    create_metric_cards(),
    create_card_modal(),
    create_urgency_table(),
    create_issues_table()
])


@app.callback(
    [
        Output('data-store', 'data'),
        Output('last-updated', 'children')
    ],
    [
        Input('refresh-button', 'n_clicks'),
        Input('interval-component', 'n_intervals')
    ]
)
def update_data(n_clicks, n_intervals):
    """Fetch and store data."""
    cache.clear()
    df = fetch_and_process_data()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    last_updated_text = f"Last updated: {timestamp}"
    
    return df.to_dict('records'), last_updated_text


@app.callback(
    [
        Output('priority-filter', 'options'),
        Output('assignee-filter', 'options'),
        Output('project-filter', 'options')
    ],
    Input('data-store', 'data')
)
def update_filter_options(data):
    """Update filter dropdown options based on data."""
    if not data:
        return [], [], []
    
    df = pd.DataFrame(data)
    
    priorities = [{'label': p, 'value': p} for p in DataProcessor.get_unique_values(df, 'priority')]
    assignees = [{'label': a, 'value': a} for a in DataProcessor.get_unique_values(df, 'assignee')]
    projects = [{'label': p, 'value': p} for p in DataProcessor.get_unique_values(df, 'project')]
    
    return priorities, assignees, projects


@app.callback(
    [
        Output('overdue-count', 'children'),
        Output('due-week-count', 'children'),
        Output('upcoming-count', 'children'),
        Output('high-priority-count', 'children'),
        Output('backlog-count', 'children'),
    ],
    [
        Input('data-store', 'data'),
        Input('status-filter', 'value'),
        Input('priority-filter', 'value'),
        Input('assignee-filter', 'value'),
        Input('project-filter', 'value')
    ]
)
def update_metrics(data, status_filter, priority_filter, assignee_filter, project_filter):
    """Update metric cards."""
    if not data:
        return "0", "0", "0", "0", "0"

    df = pd.DataFrame(data)
    df = apply_filters(df, status_filter, priority_filter, assignee_filter, project_filter)

    stats = DataProcessor.get_summary_stats(df)

    # Backlog > 3 months: status contains 'backlog' (case-insensitive), created > 90 days ago
    backlog_count = 0
    if 'status' in df.columns and 'created' in df.columns:
        df['created'] = pd.to_datetime(df['created'], errors='coerce')
        cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=90)
        # Normalise tz — make cutoff naive if created is naive
        if df['created'].dt.tz is None:
            cutoff = cutoff.tz_localize(None)
        backlog_mask = (
            df['status'].str.lower().str.contains('backlog', na=False) &
            (df['created'] < cutoff)
        )
        backlog_count = int(backlog_mask.sum())

    return (
        str(stats['overdue_count']),
        str(stats['due_this_week_count']),
        str(stats['upcoming_count']),
        str(stats['high_priority_count']),
        str(backlog_count),
    )


# ── Card-click → store context ───────────────────────────────────────────────
@app.callback(
    Output('card-context-store', 'data'),
    [
        Input('card-overdue', 'n_clicks'),
        Input('card-due-week', 'n_clicks'),
        Input('card-upcoming', 'n_clicks'),
        Input('card-high-priority', 'n_clicks'),
        Input('card-backlog', 'n_clicks'),
    ],
    prevent_initial_call=True
)
def store_card_context(n1, n2, n3, n4, n5):
    """Record which card was last clicked."""
    from dash import ctx
    return ctx.triggered_id


# ── Card-context → modal open + populate ─────────────────────────────────────
@app.callback(
    [
        Output('card-modal', 'is_open'),
        Output('card-modal-title', 'children'),
        Output('card-modal-table', 'data'),
        Output('card-modal-table', 'columns'),
        Output('card-modal-table', 'tooltip_data'),
    ],
    [
        Input('card-context-store', 'data'),
        Input('card-modal-close', 'n_clicks'),
    ],
    [
        State('data-store', 'data'),
        State('status-filter', 'value'),
        State('priority-filter', 'value'),
        State('assignee-filter', 'value'),
        State('project-filter', 'value'),
    ],
    prevent_initial_call=True
)
def populate_card_modal(card_id, close_clicks,
                        data, status_filter, priority_filter,
                        assignee_filter, project_filter):
    """Open modal and populate its table based on the clicked card."""
    from dash import ctx
    empty = (False, "", [], [], [])

    if ctx.triggered_id == 'card-modal-close':
        return empty
    if not card_id or not data:
        return empty

    df = pd.DataFrame(data)
    df = apply_filters(df, status_filter, priority_filter, assignee_filter, project_filter)

    card_cfg = {
        'card-overdue':       ('Overdue Issues',              lambda d: d[d['is_overdue']]),
        'card-due-week':      ('Issues Due This Week',         DataProcessor.filter_due_this_week),
        'card-upcoming':      ('Upcoming Issues',              DataProcessor.filter_upcoming),
        'card-high-priority': ('High / Highest Priority Issues',
                               lambda d: d[d['priority'].isin(['Highest', 'High'])]),
        'card-backlog':       ('Issues in Backlog > 3 Months', _filter_long_backlog),
    }

    if card_id not in card_cfg:
        return empty

    title, filter_fn = card_cfg[card_id]
    subset = filter_fn(df)

    if subset.empty:
        return True, title, [], [{"name": "No issues found", "id": "msg"}], []

    # Build display rows
    jira_base = (Config.JIRA_URL or '').rstrip('/')

    rows = []
    for _, row in subset.iterrows():
        jira_link = f"{jira_base}/browse/{row['key']}" if jira_base else row['key']
        rows.append({
            'Key':      row['key'],
            'Summary':  row.get('summary', ''),
            'Reporter': row.get('reporter') or 'Unknown',
            'Assignee': row.get('assignee') or 'Unassigned',
            'Status':   row.get('status', ''),
            'Priority': row.get('priority', ''),
            'Due Date': row.get('due_date_str', 'N/A'),
            'JIRA Link': jira_link,
        })

    columns = [
        {'name': 'Key',      'id': 'Key'},
        {'name': 'Summary',  'id': 'Summary'},
        {'name': 'Reporter', 'id': 'Reporter'},
        {'name': 'Assignee', 'id': 'Assignee'},
        {'name': 'Status',   'id': 'Status'},
        {'name': 'Priority', 'id': 'Priority'},
        {'name': 'Due Date', 'id': 'Due Date'},
        {'name': 'JIRA Link','id': 'JIRA Link',
         'presentation': 'markdown'},
    ]

    # Convert link column to markdown hyperlinks
    for r in rows:
        if jira_base:
            r['JIRA Link'] = f"[{r['Key']}]({r['JIRA Link']})"

    # Tooltips for long Summary cells
    tooltip_data = [
        {'Summary': {'value': r['Summary'], 'type': 'markdown'}} for r in rows
    ]

    return True, title, rows, columns, tooltip_data


def _filter_long_backlog(df):
    """Return issues whose status contains 'backlog' and were created > 90 days ago."""
    if df.empty:
        return df
    df = df.copy()
    df['created'] = pd.to_datetime(df['created'], errors='coerce')
    cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=90)
    if df['created'].dt.tz is None:
        cutoff = cutoff.tz_localize(None)
    mask = (
        df['status'].str.lower().str.contains('backlog', na=False) &
        (df['created'] < cutoff)
    )
    return df[mask].copy()


# ── Urgency table ─────────────────────────────────────────────────────────────
@app.callback(
    [
        Output('urgency-table', 'data'),
        Output('urgency-table', 'columns')
    ],
    [
        Input('data-store', 'data'),
        Input('status-filter', 'value'),
        Input('priority-filter', 'value'),
        Input('assignee-filter', 'value'),
        Input('project-filter', 'value')
    ]
)
def update_urgency_table(data, status_filter, priority_filter, assignee_filter, project_filter):
    """Update urgency breakdown table."""
    if not data:
        return [], []

    df = pd.DataFrame(data)
    df = apply_filters(df, status_filter, priority_filter, assignee_filter, project_filter)

    df_with_due = df[df['has_due_date']].copy()
    if df_with_due.empty:
        return [], []

    urgency_cols = [
        'key', 'summary', 'priority', 'status',
        'assignee', 'due_date_str', 'days_past_due',
        'num_subtasks', 'urgency_score'
    ]
    df_display = df_with_due[urgency_cols].copy()
    df_display.columns = [
        'Key', 'Summary', 'Priority', 'Status',
        'Assignee', 'Due Date', 'Days Past Due',
        'Subtasks', 'Urgency Score'
    ]
    df_display['Urgency Score'] = df_display['Urgency Score'].round(1)
    df_display = df_display.sort_values('Urgency Score', ascending=False)

    columns = [{'name': col, 'id': col} for col in df_display.columns]
    return df_display.to_dict('records'), columns


@app.callback(
    [
        Output('issues-table', 'data'),
        Output('issues-table', 'columns')
    ],
    [
        Input('data-store', 'data'),
        Input('status-filter', 'value'),
        Input('priority-filter', 'value'),
        Input('assignee-filter', 'value'),
        Input('project-filter', 'value')
    ]
)
def update_table(data, status_filter, priority_filter, assignee_filter, project_filter):
    """Update issues table."""
    if not data:
        return [], []
    
    df = pd.DataFrame(data)
    df = apply_filters(df, status_filter, priority_filter, assignee_filter, project_filter)
    
    # Select columns for display
    display_columns = [
        'key', 'summary', 'issue_type', 'status', 'priority',
        'assignee', 'due_date_str', 'days_past_due', 'num_subtasks',
        'urgency_score'
    ]
    
    df_display = df[display_columns].copy()
    
    # Rename columns for better display
    df_display.columns = [
        'Key', 'Summary', 'Type', 'Status', 'Priority',
        'Assignee', 'Due Date', 'Days Past Due', 'Subtasks',
        'Urgency'
    ]
    
    # Sort by urgency (highest first)
    df_display = df_display.sort_values('Urgency', ascending=False)
    
    columns = [{"name": col, "id": col} for col in df_display.columns]
    
    return df_display.to_dict('records'), columns


def apply_filters(df, status_filter, priority_filter, assignee_filter, project_filter):
    """Apply filters to DataFrame."""
    if df.empty:
        return df
    
    filtered_df = df.copy()
    
    # Apply status filter
    if status_filter == 'overdue':
        filtered_df = DataProcessor.filter_overdue(filtered_df)
    elif status_filter == 'due_this_week':
        filtered_df = DataProcessor.filter_due_this_week(filtered_df)
    elif status_filter == 'upcoming':
        filtered_df = DataProcessor.filter_upcoming(filtered_df)
    
    # Apply priority filter
    if priority_filter:
        filtered_df = DataProcessor.filter_by_priority(filtered_df, priority_filter)
    
    # Apply assignee filter
    if assignee_filter:
        filtered_df = DataProcessor.filter_by_assignee(filtered_df, assignee_filter)
    
    # Apply project filter
    if project_filter:
        filtered_df = filtered_df[filtered_df['project'].isin(project_filter)]
    
    return filtered_df


if __name__ == '__main__':
    logger.info("Starting JIRA Dashboard...")
    
    # Initialize on startup
    if initialize_jira_client():
        logger.info("JIRA client ready")
    else:
        logger.warning("Starting without JIRA connection - configure .env file")
    
    app.run_server(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )
