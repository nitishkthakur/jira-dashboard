# Quick Start Guide

## Getting Started in 5 Minutes

### Step 1: Get Your JIRA API Token
1. Visit: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Name it "JIRA Dashboard"
4. Copy the token (you'll only see it once!)

### Step 2: Configure the Dashboard
```bash
# Copy the example configuration
cp .env.example .env

# Edit .env with your details
nano .env  # or use your preferred editor
```

Update these values:
```env
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your.email@company.com
JIRA_API_TOKEN=paste_your_token_here
JIRA_PROJECT_KEY=PROJ  # Your project key
```

### Step 3: Install and Run
```bash
# Install dependencies
pip install -r requirements.txt

# Start the dashboard
python app.py
```

### Step 4: Open Dashboard
Navigate to: http://localhost:8050

## What You'll See

### Metric Cards (Top)
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│   OVERDUE   │ DUE THIS    │  UPCOMING   │    HIGH     │
│     42      │    WEEK     │     56      │  PRIORITY   │
│             │     28      │             │     18      │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

### Urgency Timeline Chart
Interactive scatter plot showing:
- X-axis: Due dates
- Y-axis: Urgency score (0-100)
- Colors: Priority levels
- Size: Number of subtasks
- Red line: Today

### Issues Table
Sortable table with:
- Issue Key (clickable link to JIRA)
- Summary
- Type (Story, Bug, Task, etc.)
- Status
- Priority
- Assignee
- Due Date
- Days Past Due (highlighted if overdue)
- Number of Subtasks
- Urgency Score

## Common Use Cases

### 1. Morning Standup
1. Check overdue count
2. Review "Due This Week" items
3. Filter by team member to discuss individual tasks

### 2. Sprint Planning
1. Filter to "Upcoming" issues
2. Sort by urgency score
3. Review subtask counts to estimate effort

### 3. Manager Review
1. Check high priority count
2. Review urgency timeline for blockers
3. Export table to CSV for reporting

### 4. Individual Developer
1. Filter by your name in Assignee
2. Focus on overdue items first
3. Monitor subtask completion

## Data Refresh

- **Automatic**: Every 15 minutes (configurable)
- **Manual**: Click "Refresh Data" button
- **On Demand**: Restart the application

## Filters Explained

### Status Filter
- **All**: Show all issues with any status
- **Overdue**: Only issues past due date
- **Due This Week**: Issues due in next 7 days
- **Upcoming**: Issues due after 7 days

### Priority Filter
Multi-select from:
- Highest (🔴)
- High (🟠)
- Medium (🟡)
- Low (🟢)
- Lowest (⚪)

### Assignee Filter
Multi-select team members

### Project Filter
Multi-select if you configured multiple projects

## Understanding the Data

### Urgency Score Breakdown

The dashboard calculates urgency using this formula:

```
Urgency Score = (Priority × 0.4) + (Days Past Due × 0.4) + (Incomplete Subtasks × 0.2)
```

**Example 1: Critical Overdue**
- Priority: Highest (5/5 = 1.0)
- Days Past Due: 15 days (15/30 = 0.5)
- Subtask Completion: 30% (0.7 incomplete)

Urgency = (1.0 × 0.4) + (0.5 × 0.4) + (0.7 × 0.2) = 0.74 = **74/100** (Red - Critical!)

**Example 2: Upcoming Low Priority**
- Priority: Low (2/5 = 0.4)
- Days Past Due: Not overdue (0)
- Subtask Completion: 80% (0.2 incomplete)

Urgency = (0.4 × 0.4) + (0 × 0.4) + (0.2 × 0.2) = 0.2 = **20/100** (Green - No rush)

### Subtask Information

For **Story** type issues:
- Shows total number of subtasks
- Tracks completion percentage
- Incomplete subtasks increase urgency
- Helps estimate remaining work

### Days Past Due

- Calculated from due date to today
- Only shown if issue is overdue
- Key driver of urgency score
- Highlighted in red in table

## Troubleshooting

### "Configuration Error"
- Check .env file exists
- Verify all required variables are set
- Ensure no extra spaces in .env values

### "Connection Failed"
- Test JIRA URL in browser (should load your JIRA)
- Verify API token is correct
- Check email matches your JIRA account
- Ensure account has project access

### "No Issues Found"
- Verify project key is correct (case-sensitive!)
- Check you have read access to the project
- Try with different project if you have multiple

### Dashboard is Slow
- Reduce JIRA_MAX_RESULTS in .env (try 500)
- Increase CACHE_TIMEOUT (try 1800 for 30 min)
- Filter to specific project(s)

## Tips & Tricks

1. **Bookmark the URL**: Add http://localhost:8050 to favorites
2. **Multiple Projects**: Set `JIRA_PROJECT_KEYS=PROJ1,PROJ2,PROJ3` in .env
3. **Custom Port**: Change `PORT=8080` if 8050 is in use
4. **Dark Mode**: Coming in future update!
5. **Mobile Access**: Dashboard is responsive, works on tablets

## Next Steps

- Explore the detailed [dashboard-plan.md](dashboard-plan.md) for architecture
- Read full [README.md](README.md) for comprehensive guide
- Customize urgency weights in config.py if needed
- Share feedback and feature requests via GitHub issues

## Quick Command Reference

```bash
# Start dashboard
python app.py

# Install/update dependencies
pip install -r requirements.txt

# Test JIRA connection (in Python)
python -c "from data.jira_client import JiraClient; c = JiraClient(); print(c.test_connection())"

# Check configuration
cat .env

# View logs
python app.py 2>&1 | tee dashboard.log
```

---

**Happy Dashboard-ing! 🎯📊**
