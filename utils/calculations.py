"""Utility functions for calculations and metrics."""

from typing import Optional
from config import Config


def calculate_urgency_score(
    priority: str,
    days_past_due: Optional[int],
    subtask_completion: float
) -> float:
    """
    Calculate urgency score for an issue.
    
    The urgency score is a weighted combination of:
    - Priority level (40%)
    - Days past due (40%)
    - Subtask completion (20%)
    
    Args:
        priority: Priority level (Highest, High, Medium, Low, Lowest)
        days_past_due: Number of days past due date (None if not overdue)
        subtask_completion: Subtask completion ratio (0.0 to 1.0)
        
    Returns:
        Urgency score from 0 to 100
    """
    # Priority weights (0-5)
    priority_weights = {
        'Highest': 5,
        'High': 4,
        'Medium': 3,
        'Low': 2,
        'Lowest': 1
    }
    
    # Get priority weight (default to medium if unknown)
    priority_value = priority_weights.get(priority, 3)
    priority_normalized = priority_value / 5.0  # Normalize to 0-1
    
    # Days past due normalized (capped at 30 days for normalization)
    if days_past_due is None or days_past_due <= 0:
        days_past_normalized = 0
    else:
        days_past_normalized = min(days_past_due / 30.0, 1.0)
    
    # Subtask incompletion (invert so incomplete = higher urgency)
    subtask_incompletion = 1.0 - subtask_completion
    
    # Calculate weighted score
    score = (
        priority_normalized * Config.PRIORITY_WEIGHT +
        days_past_normalized * Config.DAYS_PAST_DUE_WEIGHT +
        subtask_incompletion * Config.SUBTASK_COMPLETION_WEIGHT
    )
    
    # Scale to 0-100
    return round(score * 100, 2)


def get_urgency_color(urgency_score: float) -> str:
    """
    Get color code for urgency score.
    
    Args:
        urgency_score: Urgency score (0-100)
        
    Returns:
        Color code (red, orange, yellow, green)
    """
    if urgency_score >= 75:
        return 'red'
    elif urgency_score >= 50:
        return 'orange'
    elif urgency_score >= 25:
        return 'yellow'
    else:
        return 'green'


def get_priority_weight(priority: str) -> int:
    """
    Get numeric weight for priority level.
    
    Args:
        priority: Priority level string
        
    Returns:
        Priority weight (1-5)
    """
    weights = {
        'Highest': 5,
        'High': 4,
        'Medium': 3,
        'Low': 2,
        'Lowest': 1
    }
    return weights.get(priority, 3)


def calculate_team_capacity(
    num_issues: int,
    avg_subtasks_per_issue: float,
    team_size: int
) -> dict:
    """
    Calculate team capacity metrics.
    
    Args:
        num_issues: Total number of issues
        avg_subtasks_per_issue: Average subtasks per issue
        team_size: Number of team members
        
    Returns:
        Dictionary with capacity metrics
    """
    total_work_items = num_issues + (num_issues * avg_subtasks_per_issue)
    work_items_per_person = total_work_items / team_size if team_size > 0 else 0
    
    return {
        'total_work_items': total_work_items,
        'work_items_per_person': work_items_per_person,
        'team_size': team_size,
        'issues_per_person': num_issues / team_size if team_size > 0 else 0
    }
