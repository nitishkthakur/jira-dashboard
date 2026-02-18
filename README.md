# JIRA Dashboard

A comprehensive Dash-based dashboard for project managers to track JIRA issues, deadlines, subtasks, urgency, and project health metrics.

## Features

### 📊 Key Metrics
- **Overdue Issues**: Real-time count of issues past their due date
- **Due This Week**: Issues requiring immediate attention (next 7 days)
- **Upcoming Issues**: Future deadlines beyond the current week
- **High Priority Items**: Track critical issues (High/Highest priority)

### 🎯 Urgency Tracking
- **Intelligent Urgency Score**: Weighted algorithm considering:
  - Priority level (40%)
  - Days past due (40%)
  - Subtask completion (20%)
- **Visual Timeline**: Interactive scatter plot showing urgency vs. due date
- **Color-coded Priorities**: Quick visual identification of critical items

### 📋 Comprehensive Issue Details
- **Issue Key and Summary**: Direct links to JIRA
- **Timeline Information**:
  - Creation date
  - Due date (deadline)
  - Last updated
  - Days past due (calculated)
- **Subtask Tracking**:
  - Number of subtasks
  - Subtask details (for Stories)
  - Completion percentage
- **Assignment Information**: Assignee and reporter tracking
- **Project Context**: Labels, components, and project classification

### 🔍 Advanced Filtering
- **Status Filter**: All, Overdue, Due This Week, Upcoming
- **Priority Filter**: Multi-select priority levels
- **Assignee Filter**: Filter by team member
- **Project Filter**: Multi-project support

### 📈 Data Visualization
- **Urgency Timeline Chart**: Scatter plot with:
  - X-axis: Due Date
  - Y-axis: Urgency Score (0-100)
  - Color: Priority level
  - Size: Number of subtasks
  - Interactive hover information
- **Detailed Issues Table**: Sortable, filterable, paginated table
- **Export Capability**: Export filtered data to CSV

## Installation

### Prerequisites
- Python 3.9 or higher
- JIRA account with API access
- JIRA API token ([Generate here](https://id.atlassian.com/manage-profile/security/api-tokens))

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/nitishkthakur/jira-dashboard.git
cd jira-dashboard
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your JIRA credentials:
```env
JIRA_URL=https://your-instance.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token-here
JIRA_PROJECT_KEY=PROJ
```

4. **Run the dashboard**
```bash
python app.py
```

5. **Access the dashboard**
Open your browser and navigate to: `http://localhost:8050`

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `JIRA_URL` | Your JIRA instance URL | Yes | - |
| `JIRA_EMAIL` | Your JIRA email/username | Yes | - |
| `JIRA_API_TOKEN` | JIRA API token | Yes | - |
| `JIRA_PROJECT_KEY` | Primary project key | Yes | PROJ |
| `JIRA_PROJECT_KEYS` | Comma-separated project keys | No | JIRA_PROJECT_KEY |
| `JIRA_MAX_RESULTS` | Max issues to fetch | No | 1000 |
| `CACHE_TIMEOUT` | Cache duration in seconds | No | 900 (15 min) |
| `DEBUG` | Enable debug mode | No | False |
| `PORT` | Dashboard port | No | 8050 |
| `HOST` | Dashboard host | No | 0.0.0.0 |

### Generating JIRA API Token

1. Go to [Atlassian Account Security](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a label (e.g., "JIRA Dashboard")
4. Copy the token and add it to your `.env` file

**Important**: API tokens are displayed only once. Save it securely!

## Usage

### Dashboard Navigation

1. **Header Section**
   - View last update time
   - Click "Refresh Data" to manually update

2. **Filters**
   - Select status type (All, Overdue, Due This Week, Upcoming)
   - Choose specific priorities, assignees, or projects
   - Filters apply to all visualizations

3. **Metric Cards**
   - Quick overview of key statistics
   - Click cards to filter table (future enhancement)

4. **Urgency Timeline**
   - Interactive scatter plot
   - Hover over points for details
   - Red vertical line shows "Today"
   - Past due issues shown in red zone

5. **Issues Table**
   - Sort by clicking column headers
   - Filter using column search boxes
   - Navigate pages for large datasets
   - Export to CSV for reporting

### Understanding Urgency Score

The urgency score (0-100) helps prioritize work:

```
Urgency = (Priority × 0.4) + (Days Past Due × 0.4) + (Incomplete Subtasks × 0.2)
```

- **0-25 (Green)**: Low urgency
- **25-50 (Yellow)**: Medium urgency
- **50-75 (Orange)**: High urgency
- **75-100 (Red)**: Critical urgency

### Best Practices

1. **Daily Morning Check**
   - Review overdue issues count
   - Check items due this week
   - Prioritize based on urgency timeline

2. **Team Stand-ups**
   - Filter by assignee
   - Review individual workload
   - Identify blockers (low subtask completion)

3. **Sprint Planning**
   - Filter by upcoming due dates
   - Assess capacity based on subtask counts
   - Balance high-priority items

4. **Executive Reporting**
   - Export table to CSV
   - Screenshot urgency chart
   - Share key metrics

## Project Structure

```
jira-dashboard/
├── app.py                 # Main Dash application
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # This file
├── dashboard-plan.md     # Detailed implementation plan
├── data/
│   ├── __init__.py
│   ├── jira_client.py    # JIRA API client
│   ├── data_processor.py # Data transformation logic
│   └── models.py         # Data models (Issue, Subtask)
├── components/           # Dashboard components (future)
└── utils/
    ├── __init__.py
    ├── calculations.py   # Urgency and metric calculations
    └── formatting.py     # Date and text formatting
```

## Data Flow

```
JIRA API → JiraClient → Issue Models → DataProcessor → DataFrame → Dash Components
```

1. **JiraClient**: Fetches issues via JIRA REST API
2. **Issue Models**: Structures data with calculated fields
3. **DataProcessor**: Transforms to pandas DataFrame
4. **DataFrame**: Cached for performance
5. **Dash Components**: Render interactive visualizations

## Troubleshooting

### Connection Issues

**Problem**: "Failed to connect to JIRA"
- Verify `JIRA_URL` is correct (e.g., `https://yourcompany.atlassian.net`)
- Check `JIRA_EMAIL` matches your JIRA account
- Ensure `JIRA_API_TOKEN` is valid (not expired)
- Test connection: Visit JIRA_URL in browser

### No Data Displayed

**Problem**: Dashboard shows "0" issues
- Check `JIRA_PROJECT_KEY` matches your project
- Verify project permissions (can you access in JIRA?)
- Review logs for API errors
- Try with `DEBUG=True` in `.env`

### Performance Issues

**Problem**: Dashboard is slow
- Reduce `JIRA_MAX_RESULTS` (default: 1000)
- Increase `CACHE_TIMEOUT` (default: 900 seconds)
- Filter by specific project(s)
- Check network latency to JIRA instance

### API Rate Limiting

**Problem**: "API rate limit exceeded"
- Increase `CACHE_TIMEOUT` to reduce API calls
- Avoid clicking "Refresh" repeatedly
- Consider upgrading JIRA plan for higher limits

## Development

### Running in Development Mode

```bash
# Enable debug mode
export DEBUG=True

# Run with hot reload
python app.py
```

### Running Tests

```bash
# Install development dependencies
pip install pytest black flake8

# Run tests
pytest

# Format code
black .

# Lint code
flake8 .
```

## Future Enhancements

See [dashboard-plan.md](dashboard-plan.md) for detailed roadmap, including:

- Velocity tracking and burndown charts
- Team workload heatmaps
- Email/Slack notifications
- Custom JQL queries
- Time tracking integration
- Dependency visualization
- Historical trend analysis
- Multi-tenant support

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check [dashboard-plan.md](dashboard-plan.md) for implementation details
- Review JIRA API documentation: https://developer.atlassian.com/cloud/jira/platform/rest/v3/

## Acknowledgments

Built with:
- [Plotly Dash](https://dash.plotly.com/) - Interactive dashboards
- [jira-python](https://github.com/pycontribs/jira) - JIRA API client
- [Pandas](https://pandas.pydata.org/) - Data processing
- [Bootstrap](https://getbootstrap.com/) - UI components

---

**Note**: This dashboard provides read-only access to JIRA data. No modifications are made to your JIRA instance.