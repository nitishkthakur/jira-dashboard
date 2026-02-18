# JIRA Dashboard Plan

## Overview
This document outlines the design and implementation plan for a JIRA project management dashboard built using Plotly Dash. The dashboard is designed for project managers to track deadlines, subtasks, urgency, and overdue issues.

## Data Requirements

### Primary Data Points
1. **Issue Identification**
   - Issue Key (e.g., PROJ-123)
   - Issue Type (Story, Task, Bug, Epic, etc.)
   - Summary/Title
   - Status (To Do, In Progress, Done, etc.)

2. **Timeline Data**
   - Creation Date
   - Due Date (Deadline)
   - Last Updated Date
   - Resolution Date (if completed)
   - Days Past Due (calculated field)

3. **Subtask Information**
   - Number of Subtasks
   - List of Subtasks (for Stories)
   - Subtask Status
   - Subtask Completion Percentage

4. **Priority & Urgency**
   - Priority Level (Highest, High, Medium, Low, Lowest)
   - Urgency Score (custom calculated metric)
   - Assignee
   - Reporter

5. **Project Context**
   - Project Name
   - Sprint (if applicable)
   - Labels/Tags
   - Components

## Data Fetching Strategy

### JIRA API Integration
- **Authentication**: Use JIRA API token with email/username
- **API Endpoint**: REST API v3 (`/rest/api/3/search`)
- **Query Strategy**: JQL (JIRA Query Language) for flexible filtering

### Data Fetching Approach
```python
# Primary JQL query structure
jql = "project = {PROJECT_KEY} AND statusCategory != Done ORDER BY duedate ASC"

# Fields to retrieve
fields = [
    "summary",
    "status",
    "priority",
    "assignee",
    "reporter",
    "created",
    "duedate",
    "updated",
    "resolutiondate",
    "issuetype",
    "subtasks",
    "parent",
    "labels",
    "components",
    "sprint"
]
```

### Data Processing Pipeline
1. **Fetch**: Query JIRA API with pagination (100 issues per request)
2. **Transform**: Convert API response to structured DataFrame
3. **Enrich**: Calculate derived metrics:
   - Days past due = (Today - Due Date) if overdue
   - Urgency score = f(Priority, Days Past Due, Subtask Completion)
   - Subtask completion % = Completed Subtasks / Total Subtasks
4. **Cache**: Store processed data with timestamp (refresh every 15 minutes)
5. **Serve**: Provide data to dashboard components

### Urgency Calculation Formula
```python
urgency_score = (
    priority_weight * 0.4 +
    days_past_due_normalized * 0.4 +
    (1 - subtask_completion) * 0.2
)

# Priority weights
priority_weights = {
    "Highest": 5,
    "High": 4,
    "Medium": 3,
    "Low": 2,
    "Lowest": 1
}
```

## Dashboard Design

### Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│                    JIRA DASHBOARD                        │
│                   [Last Updated: ...]                    │
├─────────────────────────────────────────────────────────┤
│  Filters: [Project ▼] [Status ▼] [Assignee ▼] [Refresh] │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │   OVERDUE    │ │  DUE THIS    │ │   UPCOMING   │    │
│  │   ISSUES     │ │   WEEK       │ │   ISSUES     │    │
│  │     42       │ │     28       │ │     56       │    │
│  └──────────────┘ └──────────────┘ └──────────────┘    │
├─────────────────────────────────────────────────────────┤
│  HIGH PRIORITY OVERDUE ISSUES                           │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Urgency Timeline Chart                            │  │
│  │ (Scatter plot: Due Date vs Urgency Score)         │  │
│  └───────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│  DETAILED ISSUES TABLE                                  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Key │ Summary │ Status │ Due │ Days Past │ Priority│ │
│  │─────│─────────│────────│─────│───────────│─────────│ │
│  │ ... │ ...     │ ...    │ ... │    ...    │   ...   │ │
│  └───────────────────────────────────────────────────┘  │
│  [Expandable subtask details]                           │
└─────────────────────────────────────────────────────────┘
```

### Dashboard Components

#### 1. **Header Section**
- Dashboard title
- Last refresh timestamp
- Quick refresh button

#### 2. **Filter Bar**
- Project dropdown (multi-select)
- Status filter (Active, Overdue, All)
- Assignee filter (multi-select)
- Date range picker for due dates
- Clear filters button

#### 3. **Key Metrics Cards** (Top Row)
- **Overdue Issues**: Count with red background
- **Due This Week**: Count with yellow background
- **Upcoming Issues**: Count with blue background
- Click to filter table

#### 4. **Urgency Timeline Chart** (Visualization 1)
- **Type**: Scatter plot
- **X-axis**: Due Date
- **Y-axis**: Urgency Score (0-100)
- **Color**: Priority level
- **Size**: Number of subtasks
- **Hover Info**: Issue key, summary, assignee, days past due
- **Features**: 
  - Vertical line for "Today"
  - Shaded area for "Past Due" (red zone)
  - Clickable points to filter table

#### 5. **Priority Distribution** (Visualization 2)
- **Type**: Stacked bar chart or pie chart
- **Categories**: Overdue vs On-time
- **Segments**: Priority levels
- **Interactive**: Click to filter

#### 6. **Subtask Progress Gauge** (Visualization 3)
- **Type**: Progress bars or gauge charts
- **Display**: For each story with subtasks
- **Show**: Completion percentage
- **Color code**: 
  - Green: >80% complete
  - Yellow: 50-80%
  - Red: <50%

#### 7. **Detailed Issues Table** (Main Table)
- **Columns**:
  - Issue Key (link to JIRA)
  - Summary (truncated with hover)
  - Issue Type (icon)
  - Status
  - Assignee
  - Priority
  - Due Date
  - Days Past Due (highlighted if overdue)
  - Subtasks (count)
  - Urgency Score (color-coded)
- **Features**:
  - Sortable columns
  - Expandable rows for subtask details
  - Pagination (50 items per page)
  - Export to CSV button
  - Search/filter within table
- **Conditional Formatting**:
  - Overdue rows: Red background/text
  - Due soon (< 3 days): Yellow background
  - High urgency: Bold text

#### 8. **Expandable Subtask Section**
- **Trigger**: Click on row with subtasks
- **Display**:
  - Subtask key and summary
  - Subtask status
  - Subtask assignee
  - Completion indicator

### Color Scheme
- **Primary**: Dark blue (#1f77b4) for headers and primary actions
- **Success**: Green (#2ca02c) for on-track items
- **Warning**: Yellow/Orange (#ff7f0e) for items due soon
- **Danger**: Red (#d62728) for overdue items
- **Neutral**: Gray (#7f7f7f) for completed/neutral items

## Technical Implementation

### Technology Stack
- **Backend**: Python 3.9+
- **Dashboard**: Plotly Dash 2.x
- **Data Processing**: Pandas
- **API Client**: requests or jira-python library
- **Styling**: Dash Bootstrap Components
- **Caching**: Flask-Caching
- **Configuration**: python-dotenv

### Project Structure
```
jira-dashboard/
├── app.py                 # Main Dash application
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # Setup and usage instructions
├── dashboard-plan.md     # This document
├── data/
│   ├── __init__.py
│   ├── jira_client.py    # JIRA API client
│   ├── data_processor.py # Data transformation logic
│   └── models.py         # Data models
├── components/
│   ├── __init__.py
│   ├── filters.py        # Filter components
│   ├── metrics.py        # Metric cards
│   ├── charts.py         # Chart components
│   └── table.py          # Table component
└── utils/
    ├── __init__.py
    ├── calculations.py   # Urgency and metric calculations
    └── formatting.py     # Date and text formatting
```

### Implementation Phases

#### Phase 1: Data Layer (Week 1)
1. Set up JIRA API client with authentication
2. Implement data fetching with pagination
3. Create data models (Issue, Subtask classes)
4. Implement data transformation to DataFrame
5. Add caching mechanism

#### Phase 2: Core Dashboard (Week 2)
1. Set up Dash application structure
2. Implement basic layout with Bootstrap
3. Create filter components
4. Implement metric cards
5. Build detailed issues table

#### Phase 3: Visualizations (Week 3)
1. Implement urgency timeline scatter plot
2. Add priority distribution chart
3. Create subtask progress indicators
4. Add interactivity between charts and table

#### Phase 4: Polish & Optimization (Week 4)
1. Implement expandable subtask rows
2. Add export functionality
3. Optimize performance and caching
4. Add error handling and logging
5. Write documentation

### Configuration Requirements

#### Environment Variables (.env)
```
JIRA_URL=https://your-instance.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=PROJ
CACHE_TIMEOUT=900
DEBUG=False
```

#### Features Configuration
- Refresh interval: 15 minutes (configurable)
- Pagination size: 50 items per page
- Max issues to fetch: 1000 (with pagination)
- Date format: YYYY-MM-DD or configurable locale

## User Interactions

### Primary Workflows

1. **Daily Morning Check**
   - View overdue issues count
   - Check items due this week
   - Review urgency timeline for critical items

2. **Team Assignment Review**
   - Filter by assignee
   - Check individual workload
   - Identify blockers (low subtask completion)

3. **Sprint Planning**
   - Filter by status
   - Review upcoming deadlines
   - Assess capacity based on subtask counts

4. **Executive Reporting**
   - Export table to CSV
   - Screenshot urgency chart
   - Review priority distribution

### Interactive Features
- **Click on metric cards**: Filter table to show relevant issues
- **Click on chart points**: Highlight issue in table
- **Expand table rows**: View subtask details
- **Sort table columns**: Re-order by any field
- **Apply filters**: Narrow down view
- **Hover on chart**: See detailed tooltips

## Performance Considerations

### Optimization Strategies
1. **Lazy Loading**: Load data in chunks for large datasets
2. **Client-side Filtering**: Use Dash's built-in filtering when possible
3. **Caching**: Cache JIRA API responses for 15 minutes
4. **Pagination**: Server-side pagination for tables >100 rows
5. **Debouncing**: Debounce filter changes to reduce re-renders

### Scalability
- Support for multiple projects (up to 10)
- Handle up to 5,000 issues efficiently
- Refresh in background without blocking UI
- Responsive design for mobile/tablet viewing

## Future Enhancements

### Phase 2 Features (Future)
1. **Velocity Tracking**: Historical completion rates
2. **Burndown Charts**: Sprint progress visualization
3. **Team Workload**: Resource allocation heatmap
4. **Alerts & Notifications**: Email/Slack for critical deadlines
5. **Custom JQL**: Allow users to input custom queries
6. **Time Tracking**: Integrate time logs and estimates
7. **Dependency Visualization**: Show blocked/blocking relationships
8. **Historical Trends**: Track metrics over time
9. **Multi-tenant**: Support multiple JIRA instances
10. **User Preferences**: Save filter preferences per user

## Success Metrics

### Dashboard Effectiveness
- Reduce time to identify overdue issues from 15 min to <30 sec
- Improve deadline visibility by 80%
- Enable daily standup preparation in <5 minutes
- Provide actionable insights for 100% of active issues

## Maintenance & Updates

### Regular Updates
- Weekly: Review and update urgency calculation weights
- Monthly: Gather user feedback and iterate
- Quarterly: Audit API usage and optimize queries
- As needed: Update dependencies and security patches

## Conclusion

This dashboard will provide project managers with a comprehensive, real-time view of JIRA issues with emphasis on deadlines, urgency, and subtask tracking. The phased implementation approach ensures incremental value delivery while maintaining code quality and performance.
