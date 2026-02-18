# JIRA Data Download & Structure Plan

## Executive Summary

This document outlines the comprehensive data collection, processing, and storage strategy for the JIRA Dashboard. It details what data to download from JIRA, how to structure it, and how to calculate derived metrics.

## Data Sources

### Primary Source: JIRA REST API v3
- **Endpoint**: `/rest/api/3/search`
- **Authentication**: Basic Auth (Email + API Token)
- **Protocol**: HTTPS
- **Rate Limits**: Respect JIRA Cloud rate limits (varies by plan)

## Data to Download

### 1. Core Issue Fields

#### Essential Fields (Always Retrieved)
```python
CORE_FIELDS = [
    'summary',           # Issue title/description
    'status',            # Current status (To Do, In Progress, Done, etc.)
    'priority',          # Priority level (Highest, High, Medium, Low, Lowest)
    'assignee',          # Person assigned to the issue
    'reporter',          # Person who created the issue
    'created',           # Creation timestamp
    'duedate',           # Deadline/due date
    'updated',           # Last update timestamp
    'resolutiondate',    # When issue was resolved (if completed)
    'issuetype',         # Type (Story, Bug, Task, Epic, Subtask)
    'project'            # Project information
]
```

#### Relationship Fields
```python
RELATIONSHIP_FIELDS = [
    'subtasks',          # List of subtask issues
    'parent',            # Parent issue (if this is a subtask)
]
```

#### Classification Fields
```python
CLASSIFICATION_FIELDS = [
    'labels',            # Tags/labels on the issue
    'components',        # Component categorization
]
```

### 2. Subtask Details (Nested)

For each subtask in the `subtasks` field:
```python
SUBTASK_FIELDS = {
    'key': 'PROJ-124',                    # Subtask key
    'summary': 'Implement login form',    # Subtask title
    'status': 'In Progress',              # Current status
    'assignee': 'John Doe',               # Who's working on it
    'statusCategory': 'indeterminate'     # done/indeterminate/new
}
```

### 3. Calculated/Derived Fields

These are computed after downloading:

```python
DERIVED_FIELDS = {
    'num_subtasks': 5,              # Count of subtasks
    'subtask_completion': 0.6,      # 60% complete (3/5 done)
    'days_past_due': 7,             # 7 days overdue
    'days_until_due': -7,           # Negative if overdue
    'is_overdue': True,             # Boolean flag
    'urgency_score': 72.5,          # Custom urgency calculation
    'has_due_date': True,           # Has a deadline
    'is_story': True,               # Is issue type Story?
    'has_subtasks': True            # Has subtasks?
}
```

## Data Download Strategy

### JQL (JIRA Query Language) Approach

#### Base Query Structure
```jql
project = PROJ 
AND statusCategory != Done 
ORDER BY duedate ASC
```

#### Multi-Project Query
```jql
(project = PROJ1 OR project = PROJ2 OR project = PROJ3)
AND statusCategory != Done
ORDER BY duedate ASC
```

#### Advanced Filtering (Optional)
```jql
project = PROJ
AND statusCategory != Done
AND (priority = High OR priority = Highest)
AND duedate <= endOfWeek()
ORDER BY duedate ASC
```

### Pagination Strategy

JIRA API limits results per request to 100 issues.

```python
# Pagination algorithm
start_at = 0
batch_size = 100
all_issues = []

while True:
    batch = jira.search_issues(
        jql_query,
        startAt=start_at,
        maxResults=batch_size,
        fields=CORE_FIELDS + RELATIONSHIP_FIELDS + CLASSIFICATION_FIELDS
    )
    
    if not batch:
        break
    
    all_issues.extend(batch)
    
    if len(batch) < batch_size:
        break  # Last page
    
    start_at += batch_size
```

### Error Handling

```python
try:
    issues = jira_client.fetch_issues()
except JIRAError as e:
    if e.status_code == 401:
        # Authentication failed
        log_error("Invalid credentials")
    elif e.status_code == 403:
        # Permission denied
        log_error("Insufficient permissions")
    elif e.status_code == 429:
        # Rate limit exceeded
        wait_and_retry()
    else:
        # Other error
        log_error(f"API error: {e}")
```

## Data Structure & Models

### Object-Oriented Approach

#### Issue Class
```python
@dataclass
class Issue:
    # Identity
    key: str                          # "PROJ-123"
    summary: str                      # "Implement user login"
    
    # Classification
    issue_type: str                   # "Story"
    status: str                       # "In Progress"
    priority: str                     # "High"
    project: str                      # "PROJ"
    
    # People
    assignee: Optional[str]           # "John Doe"
    reporter: Optional[str]           # "Jane Smith"
    
    # Timeline
    created: datetime                 # When created
    due_date: Optional[datetime]      # Deadline
    updated: datetime                 # Last modified
    resolution_date: Optional[datetime]  # When completed
    
    # Relationships
    subtasks: List[Subtask]           # List of subtasks
    parent_key: Optional[str]         # Parent issue key
    
    # Classification
    labels: List[str]                 # ["backend", "critical"]
    components: List[str]             # ["API", "Authentication"]
    
    # Computed Properties (not stored, calculated on access)
    @property
    def num_subtasks(self) -> int
    
    @property
    def subtask_completion(self) -> float
    
    @property
    def days_past_due(self) -> Optional[int]
    
    @property
    def is_overdue(self) -> bool
```

#### Subtask Class
```python
@dataclass
class Subtask:
    key: str                          # "PROJ-124"
    summary: str                      # "Create login form"
    status: str                       # "Done"
    assignee: Optional[str]           # "John Doe"
    is_done: bool                     # True
```

### DataFrame Structure

After processing, data is stored in a pandas DataFrame:

```python
# Column structure
DATAFRAME_COLUMNS = {
    # Identity
    'key': 'object',                  # PROJ-123
    'summary': 'object',              # Issue title
    
    # Classification
    'issue_type': 'object',           # Story, Bug, Task
    'status': 'object',               # To Do, In Progress, Done
    'priority': 'object',             # Highest, High, Medium, Low, Lowest
    'project': 'object',              # PROJ
    
    # People
    'assignee': 'object',             # John Doe
    'reporter': 'object',             # Jane Smith
    
    # Timeline
    'created': 'datetime64[ns]',     # 2024-01-15 10:30:00
    'due_date': 'datetime64[ns]',    # 2024-02-01 00:00:00
    'updated': 'datetime64[ns]',     # 2024-01-20 14:22:00
    'resolution_date': 'datetime64[ns]',  # null or datetime
    
    # Subtasks
    'num_subtasks': 'int64',         # 5
    'subtask_completion': 'float64', # 0.6 (60%)
    
    # Derived Metrics
    'days_past_due': 'float64',      # 7.0 or NaN
    'days_until_due': 'float64',     # -7.0 (negative if overdue)
    'is_overdue': 'bool',            # True
    'urgency_score': 'float64',      # 72.5
    
    # Flags
    'has_due_date': 'bool',          # True
    'is_story': 'bool',              # True
    'has_subtasks': 'bool',          # True
    
    # Display Strings
    'created_str': 'object',         # "2024-01-15"
    'due_date_str': 'object',        # "2024-02-01"
    'updated_str': 'object',         # "2024-01-20"
    
    # Lists as strings
    'labels': 'object',              # "backend,critical"
    'components': 'object'           # "API,Authentication"
}
```

## Calculation Details

### 1. Days Past Due Calculation

```python
def calculate_days_past_due(due_date: datetime) -> Optional[int]:
    """
    Calculate how many days past the due date.
    Returns None if not overdue or no due date.
    """
    if due_date is None:
        return None
    
    # Normalize to midnight for date comparison
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    due = due_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if today > due:
        return (today - due).days
    
    return None  # Not overdue
```

**Example**:
- Due Date: February 1, 2024
- Today: February 8, 2024
- Days Past Due: 7 days

### 2. Subtask Completion Calculation

```python
def calculate_subtask_completion(subtasks: List[Subtask]) -> float:
    """
    Calculate percentage of subtasks completed.
    Returns 1.0 if no subtasks (nothing to break down).
    """
    if not subtasks:
        return 1.0
    
    completed = sum(1 for st in subtasks if st.is_done)
    return completed / len(subtasks)
```

**Example**:
- Total Subtasks: 5
- Completed Subtasks: 3
- Completion: 3/5 = 0.6 = 60%

### 3. Urgency Score Calculation

```python
def calculate_urgency_score(
    priority: str,
    days_past_due: Optional[int],
    subtask_completion: float
) -> float:
    """
    Calculate urgency score (0-100) using weighted formula.
    
    Formula:
    Urgency = (Priority × 0.4) + (Days Past Due × 0.4) + (Incomplete × 0.2)
    """
    # Priority weights (normalized to 0-1)
    priority_map = {
        'Highest': 1.0,
        'High': 0.8,
        'Medium': 0.6,
        'Low': 0.4,
        'Lowest': 0.2
    }
    priority_normalized = priority_map.get(priority, 0.6)
    
    # Days past due (capped at 30 days, normalized to 0-1)
    if days_past_due is None or days_past_due <= 0:
        days_normalized = 0.0
    else:
        days_normalized = min(days_past_due / 30.0, 1.0)
    
    # Subtask incompletion (invert so incomplete = higher urgency)
    incomplete = 1.0 - subtask_completion
    
    # Weighted sum
    urgency = (
        priority_normalized * 0.4 +
        days_normalized * 0.4 +
        incomplete * 0.2
    )
    
    # Scale to 0-100
    return round(urgency * 100, 2)
```

**Example 1: High Urgency**
- Priority: Highest (1.0)
- Days Past Due: 15 days (0.5 normalized)
- Subtask Completion: 30% (0.7 incomplete)

```
Urgency = (1.0 × 0.4) + (0.5 × 0.4) + (0.7 × 0.2)
        = 0.4 + 0.2 + 0.14
        = 0.74
        = 74/100
```

**Example 2: Low Urgency**
- Priority: Low (0.4)
- Days Past Due: 0 (not overdue)
- Subtask Completion: 80% (0.2 incomplete)

```
Urgency = (0.4 × 0.4) + (0.0 × 0.4) + (0.2 × 0.2)
        = 0.16 + 0.0 + 0.04
        = 0.20
        = 20/100
```

## Data Caching Strategy

### Cache Configuration
```python
CACHE_CONFIG = {
    'type': 'simple',              # In-memory cache
    'timeout': 900,                # 15 minutes
    'threshold': 100               # Max cached items
}
```

### Cache Keys
```python
cache_key = f"issues_{project_keys}_{jql_hash}"
```

### Cache Invalidation
- **Time-based**: Automatic after 15 minutes
- **Manual**: "Refresh Data" button clears cache
- **Startup**: Cache cleared on application restart

### Benefits
- Reduces API calls to JIRA
- Improves dashboard responsiveness
- Respects rate limits
- Supports offline viewing (for cache duration)

## Data Flow Diagram

```
┌─────────────┐
│ JIRA Cloud  │
│   REST API  │
└──────┬──────┘
       │ HTTP/HTTPS
       │ Authentication: Email + API Token
       │ JQL Query
       │
       ▼
┌─────────────────┐
│  JiraClient     │
│  - fetch_issues │
│  - pagination   │
│  - error handle │
└──────┬──────────┘
       │ Raw JSON
       │
       ▼
┌─────────────────┐
│  Issue Models   │
│  - Issue class  │
│  - Subtask class│
│  - from_jira_dict│
└──────┬──────────┘
       │ Python Objects
       │
       ▼
┌─────────────────┐
│ DataProcessor   │
│  - to_dataframe │
│  - calculations │
│  - enrichment   │
└──────┬──────────┘
       │ pandas DataFrame
       │
       ▼
┌─────────────────┐
│  Cache Layer    │
│  - 15 min TTL   │
│  - memoization  │
└──────┬──────────┘
       │ Cached DataFrame
       │
       ▼
┌─────────────────┐
│ Dash Dashboard  │
│  - Tables       │
│  - Charts       │
│  - Filters      │
└─────────────────┘
```

## Performance Considerations

### Optimization Strategies

1. **Pagination**: Fetch in batches of 100
2. **Field Selection**: Only request needed fields
3. **Caching**: 15-minute cache reduces API calls
4. **Lazy Loading**: Load subtask details on demand (future)
5. **Indexing**: Use DataFrame indexes for fast filtering

### Expected Performance

| Metric | Value |
|--------|-------|
| Fetch Time (100 issues) | ~2-3 seconds |
| Fetch Time (1000 issues) | ~15-20 seconds |
| DataFrame Processing | <1 second |
| Cache Hit Response | <100ms |
| Dashboard Render | <500ms |

### Scalability Limits

- **Recommended**: Up to 1,000 issues
- **Maximum**: 5,000 issues (with pagination)
- **Concurrent Users**: 10-20 (single instance)
- **Projects**: 1-10 projects

## Data Quality & Validation

### Validation Rules

1. **Required Fields**: key, summary, status must exist
2. **Date Parsing**: Handle various date formats
3. **Missing Data**: Gracefully handle null values
4. **Type Safety**: Validate data types
5. **Boundary Checks**: Urgency score 0-100

### Error Handling

```python
# Robust date parsing
def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    
    try:
        # Try ISO format first
        if 'T' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        # Try date-only format
        return datetime.strptime(date_str, '%Y-%m-%d')
    except (ValueError, AttributeError):
        logger.warning(f"Failed to parse date: {date_str}")
        return None
```

## Security Considerations

### API Token Storage
- Store in `.env` file (gitignored)
- Never commit to version control
- Rotate tokens regularly
- Use environment-specific tokens

### Data Access
- Read-only access to JIRA
- No write operations
- Respect project permissions
- Log access attempts

### Network Security
- HTTPS for all API calls
- Validate SSL certificates
- Timeout on slow connections
- Retry with exponential backoff

## Monitoring & Logging

### Key Metrics to Log

```python
METRICS = {
    'fetch_duration': 'Time to fetch issues',
    'issue_count': 'Number of issues retrieved',
    'error_count': 'Number of errors',
    'cache_hit_rate': 'Cache effectiveness',
    'api_calls': 'Number of API requests'
}
```

### Log Levels

- **INFO**: Successful operations, counts
- **WARNING**: Missing data, fallbacks
- **ERROR**: API failures, parsing errors
- **DEBUG**: Detailed flow, raw responses

## Future Enhancements

### Phase 2 Data Additions

1. **Time Tracking**
   - Original estimate
   - Time spent
   - Remaining estimate

2. **Comments & Activity**
   - Comment count
   - Recent activity log
   - User mentions

3. **Dependencies**
   - Blocked by
   - Blocks
   - Related issues

4. **Custom Fields**
   - Story points
   - Sprint information
   - Custom priorities

5. **Historical Data**
   - Status change history
   - Velocity metrics
   - Trend analysis

## Conclusion

This data plan provides a comprehensive strategy for downloading, structuring, and processing JIRA data for dashboard consumption. The approach balances completeness with performance, ensuring the dashboard delivers value while respecting API limits and user experience requirements.
