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
import plotly.graph_objs as go
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

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="JIRA Dashboard",
    suppress_callback_exceptions=True
)

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
                html.H1("JIRA Dashboard", className="text-primary mb-2"),
                html.P(
                    "Project Management Overview",
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


def create_metric_cards():
    """Create metric cards for key statistics."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Overdue", className="card-title text-danger"),
                        html.H2(id="overdue-count", className="text-danger"),
                        html.P("Issues past due date", className="text-muted")
                    ])
                ], className="text-center")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Due This Week", className="card-title text-warning"),
                        html.H2(id="due-week-count", className="text-warning"),
                        html.P("Issues due in 7 days", className="text-muted")
                    ])
                ], className="text-center")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Upcoming", className="card-title text-info"),
                        html.H2(id="upcoming-count", className="text-info"),
                        html.P("Issues due later", className="text-muted")
                    ])
                ], className="text-center")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("High Priority", className="card-title text-primary"),
                        html.H2(id="high-priority-count", className="text-primary"),
                        html.P("High/Highest priority", className="text-muted")
                    ])
                ], className="text-center")
            ], md=3)
        ], className="mb-4")
    ], fluid=True)


def create_urgency_chart():
    """Create urgency timeline scatter plot."""
    return dbc.Container([
        dbc.Card([
            dbc.CardHeader(html.H5("Urgency Timeline")),
            dbc.CardBody([
                dcc.Graph(id="urgency-timeline")
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
    dcc.Interval(
        id='interval-component',
        interval=Config.CACHE_TIMEOUT * 1000,  # in milliseconds
        n_intervals=0
    ),
    create_header(),
    create_filters(),
    create_metric_cards(),
    create_urgency_chart(),
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
        Output('high-priority-count', 'children')
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
        return "0", "0", "0", "0"
    
    df = pd.DataFrame(data)
    df = apply_filters(df, status_filter, priority_filter, assignee_filter, project_filter)
    
    stats = DataProcessor.get_summary_stats(df)
    
    return (
        str(stats['overdue_count']),
        str(stats['due_this_week_count']),
        str(stats['upcoming_count']),
        str(stats['high_priority_count'])
    )


@app.callback(
    Output('urgency-timeline', 'figure'),
    [
        Input('data-store', 'data'),
        Input('status-filter', 'value'),
        Input('priority-filter', 'value'),
        Input('assignee-filter', 'value'),
        Input('project-filter', 'value')
    ]
)
def update_urgency_chart(data, status_filter, priority_filter, assignee_filter, project_filter):
    """Update urgency timeline scatter plot."""
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data)
    df = apply_filters(df, status_filter, priority_filter, assignee_filter, project_filter)
    
    # Filter to issues with due dates
    df_with_due = df[df['has_due_date']].copy()
    
    if df_with_due.empty:
        return go.Figure()
    
    # Create scatter plot
    fig = go.Figure()
    
    priority_colors = {
        'Highest': '#d62728',
        'High': '#ff7f0e',
        'Medium': '#2ca02c',
        'Low': '#1f77b4',
        'Lowest': '#7f7f7f'
    }
    
    for priority in df_with_due['priority'].unique():
        df_priority = df_with_due[df_with_due['priority'] == priority]
        
        fig.add_trace(go.Scatter(
            x=df_priority['due_date'],
            y=df_priority['urgency_score'],
            mode='markers',
            name=priority,
            marker=dict(
                size=df_priority['num_subtasks'].apply(lambda x: max(8, x * 3)),
                color=priority_colors.get(priority, '#1f77b4'),
                line=dict(width=1, color='white')
            ),
            text=df_priority.apply(
                lambda row: f"<b>{row['key']}</b><br>" +
                           f"{row['summary'][:50]}<br>" +
                           f"Assignee: {row['assignee']}<br>" +
                           f"Days Past Due: {row['days_past_due'] or 'N/A'}<br>" +
                           f"Urgency: {row['urgency_score']:.1f}",
                axis=1
            ),
            hovertemplate='%{text}<extra></extra>'
        ))
    
    # Add vertical line for today
    today = datetime.now()
    fig.add_vline(
        x=today,
        line_dash="dash",
        line_color="red",
        annotation_text="Today"
    )
    
    fig.update_layout(
        title="Issue Urgency vs Due Date",
        xaxis_title="Due Date",
        yaxis_title="Urgency Score",
        hovermode='closest',
        height=500
    )
    
    return fig


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
