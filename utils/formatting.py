"""Utility functions for formatting data for display."""

from datetime import datetime
from typing import Optional


def format_date(date: Optional[datetime], format_str: str = '%Y-%m-%d') -> str:
    """
    Format datetime object to string.
    
    Args:
        date: Datetime object to format
        format_str: Format string (default: YYYY-MM-DD)
        
    Returns:
        Formatted date string or 'N/A' if None
    """
    if date is None:
        return 'N/A'
    
    try:
        return date.strftime(format_str)
    except (AttributeError, ValueError):
        return 'N/A'


def format_days_past_due(days: Optional[int]) -> str:
    """
    Format days past due for display.
    
    Args:
        days: Number of days past due
        
    Returns:
        Formatted string
    """
    if days is None or days <= 0:
        return '-'
    
    if days == 1:
        return '1 day'
    
    return f'{days} days'


def format_subtask_count(count: int, completion: float) -> str:
    """
    Format subtask count with completion percentage.
    
    Args:
        count: Total number of subtasks
        completion: Completion ratio (0.0 to 1.0)
        
    Returns:
        Formatted string (e.g., "5 (80%)")
    """
    if count == 0:
        return '0'
    
    percentage = int(completion * 100)
    return f'{count} ({percentage}%)'


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Truncate text to maximum length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + '...'


def format_priority(priority: str) -> str:
    """
    Format priority for display with icon.
    
    Args:
        priority: Priority level
        
    Returns:
        Formatted priority string
    """
    icons = {
        'Highest': '🔴',
        'High': '🟠',
        'Medium': '🟡',
        'Low': '🟢',
        'Lowest': '⚪'
    }
    
    icon = icons.get(priority, '⚪')
    return f'{icon} {priority}'


def format_urgency_score(score: float) -> str:
    """
    Format urgency score with color indicator.
    
    Args:
        score: Urgency score (0-100)
        
    Returns:
        Formatted score string
    """
    if score >= 75:
        indicator = '🔴'
    elif score >= 50:
        indicator = '🟠'
    elif score >= 25:
        indicator = '🟡'
    else:
        indicator = '🟢'
    
    return f'{indicator} {score:.1f}'


def format_issue_link(jira_url: str, issue_key: str) -> str:
    """
    Format JIRA issue link.
    
    Args:
        jira_url: Base JIRA URL
        issue_key: Issue key
        
    Returns:
        Full URL to issue
    """
    return f'{jira_url}/browse/{issue_key}'


def format_list(items: list, max_items: int = 3) -> str:
    """
    Format list of items for display.
    
    Args:
        items: List of items
        max_items: Maximum items to show
        
    Returns:
        Formatted string
    """
    if not items:
        return '-'
    
    if len(items) <= max_items:
        return ', '.join(items)
    
    shown = ', '.join(items[:max_items])
    remaining = len(items) - max_items
    return f'{shown} +{remaining} more'
