"""Data models for JIRA issues and related entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Subtask:
    """Represents a JIRA subtask."""
    key: str
    summary: str
    status: str
    assignee: Optional[str] = None
    is_done: bool = False
    
    @classmethod
    def from_jira_dict(cls, data: dict) -> 'Subtask':
        """Create Subtask from JIRA API response."""
        fields = data.get('fields', {})
        status = fields.get('status', {}).get('name', 'Unknown')
        assignee_data = fields.get('assignee')
        assignee = assignee_data.get('displayName') if assignee_data else None
        
        # Check if status indicates completion
        status_category = fields.get('status', {}).get('statusCategory', {}).get('key', '')
        is_done = status_category == 'done'
        
        return cls(
            key=data.get('key', ''),
            summary=fields.get('summary', ''),
            status=status,
            assignee=assignee,
            is_done=is_done
        )


@dataclass
class Issue:
    """Represents a JIRA issue with all required fields for dashboard."""
    key: str
    summary: str
    issue_type: str
    status: str
    priority: str
    assignee: Optional[str]
    reporter: Optional[str]
    created: datetime
    due_date: Optional[datetime]
    updated: datetime
    resolution_date: Optional[datetime]
    subtasks: List[Subtask] = field(default_factory=list)
    parent_key: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    components: List[str] = field(default_factory=list)
    project: str = ''
    
    @property
    def num_subtasks(self) -> int:
        """Get number of subtasks."""
        return len(self.subtasks)
    
    @property
    def subtask_completion(self) -> float:
        """Calculate subtask completion percentage (0.0 to 1.0)."""
        if not self.subtasks:
            return 1.0  # No subtasks means fully complete in terms of breakdown
        
        completed = sum(1 for st in self.subtasks if st.is_done)
        return completed / len(self.subtasks)
    
    @property
    def days_past_due(self) -> Optional[int]:
        """Calculate days past due date. Returns None if not past due or no due date."""
        if not self.due_date:
            return None
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        due = self.due_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if today > due:
            return (today - due).days
        return None
    
    @property
    def is_overdue(self) -> bool:
        """Check if issue is overdue."""
        days_past = self.days_past_due
        return days_past is not None and days_past > 0
    
    @property
    def days_until_due(self) -> Optional[int]:
        """Calculate days until due date. Negative if overdue."""
        if not self.due_date:
            return None
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        due = self.due_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return (due - today).days
    
    @classmethod
    def from_jira_dict(cls, data: dict) -> 'Issue':
        """Create Issue from JIRA API response."""
        fields = data.get('fields', {})
        
        # Extract assignee and reporter
        assignee_data = fields.get('assignee')
        reporter_data = fields.get('reporter')
        assignee = assignee_data.get('displayName') if assignee_data else None
        reporter = reporter_data.get('displayName') if reporter_data else None
        
        # Parse dates
        def parse_date(date_str: Optional[str]) -> Optional[datetime]:
            if not date_str:
                return None
            try:
                # Handle both datetime and date formats
                if 'T' in date_str:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    return datetime.strptime(date_str, '%Y-%m-%d')
            except (ValueError, AttributeError):
                return None
        
        created = parse_date(fields.get('created'))
        due_date = parse_date(fields.get('duedate'))
        updated = parse_date(fields.get('updated'))
        resolution_date = parse_date(fields.get('resolutiondate'))
        
        # Extract subtasks
        subtasks_data = fields.get('subtasks', [])
        subtasks = [Subtask.from_jira_dict(st) for st in subtasks_data]
        
        # Extract parent (if this is a subtask)
        parent_data = fields.get('parent')
        parent_key = parent_data.get('key') if parent_data else None
        
        # Extract labels and components
        labels = fields.get('labels', [])
        components = [c.get('name', '') for c in fields.get('components', [])]
        
        # Extract project
        project_data = fields.get('project', {})
        project = project_data.get('key', '')
        
        return cls(
            key=data.get('key', ''),
            summary=fields.get('summary', ''),
            issue_type=fields.get('issuetype', {}).get('name', 'Unknown'),
            status=fields.get('status', {}).get('name', 'Unknown'),
            priority=fields.get('priority', {}).get('name', 'Medium'),
            assignee=assignee,
            reporter=reporter,
            created=created or datetime.now(),
            due_date=due_date,
            updated=updated or datetime.now(),
            resolution_date=resolution_date,
            subtasks=subtasks,
            parent_key=parent_key,
            labels=labels,
            components=components,
            project=project
        )
    
    def to_dict(self) -> dict:
        """Convert Issue to dictionary for DataFrame."""
        return {
            'key': self.key,
            'summary': self.summary,
            'issue_type': self.issue_type,
            'status': self.status,
            'priority': self.priority,
            'assignee': self.assignee or 'Unassigned',
            'reporter': self.reporter,
            'created': self.created,
            'due_date': self.due_date,
            'updated': self.updated,
            'resolution_date': self.resolution_date,
            'num_subtasks': self.num_subtasks,
            'subtask_completion': self.subtask_completion,
            'days_past_due': self.days_past_due,
            'days_until_due': self.days_until_due,
            'is_overdue': self.is_overdue,
            'parent_key': self.parent_key,
            'labels': ','.join(self.labels),
            'components': ','.join(self.components),
            'project': self.project
        }
