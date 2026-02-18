"""Data processing and transformation for JIRA issues."""

import logging
from typing import List
import pandas as pd

from data.models import Issue
from utils.calculations import calculate_urgency_score

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and transform JIRA issue data for dashboard consumption."""
    
    @staticmethod
    def issues_to_dataframe(issues: List[Issue]) -> pd.DataFrame:
        """
        Convert list of Issues to pandas DataFrame.
        
        Args:
            issues: List of Issue objects
            
        Returns:
            DataFrame with issue data
        """
        if not issues:
            logger.warning("No issues to process")
            return pd.DataFrame()
        
        # Convert issues to dictionaries
        issue_dicts = [issue.to_dict() for issue in issues]
        
        # Create DataFrame
        df = pd.DataFrame(issue_dicts)
        
        # Calculate urgency scores
        df['urgency_score'] = df.apply(
            lambda row: calculate_urgency_score(
                priority=row['priority'],
                days_past_due=row['days_past_due'],
                subtask_completion=row['subtask_completion']
            ),
            axis=1
        )
        
        # Add additional derived columns
        df['has_due_date'] = df['due_date'].notna()
        df['is_story'] = df['issue_type'] == 'Story'
        df['has_subtasks'] = df['num_subtasks'] > 0
        
        # Format dates for display
        df['created_str'] = df['created'].dt.strftime('%Y-%m-%d')
        df['due_date_str'] = df['due_date'].dt.strftime('%Y-%m-%d').fillna('No due date')
        df['updated_str'] = df['updated'].dt.strftime('%Y-%m-%d')
        
        logger.info(f"Processed {len(df)} issues into DataFrame")
        
        return df
    
    @staticmethod
    def filter_overdue(df: pd.DataFrame) -> pd.DataFrame:
        """Filter DataFrame to only overdue issues."""
        return df[df['is_overdue'] == True].copy()
    
    @staticmethod
    def filter_due_this_week(df: pd.DataFrame) -> pd.DataFrame:
        """Filter DataFrame to issues due within 7 days."""
        return df[
            (df['days_until_due'].notna()) &
            (df['days_until_due'] >= 0) &
            (df['days_until_due'] <= 7)
        ].copy()
    
    @staticmethod
    def filter_upcoming(df: pd.DataFrame) -> pd.DataFrame:
        """Filter DataFrame to issues due more than 7 days from now."""
        return df[
            (df['days_until_due'].notna()) &
            (df['days_until_due'] > 7)
        ].copy()
    
    @staticmethod
    def filter_by_priority(df: pd.DataFrame, priorities: List[str]) -> pd.DataFrame:
        """Filter DataFrame by priority levels."""
        return df[df['priority'].isin(priorities)].copy()
    
    @staticmethod
    def filter_by_status(df: pd.DataFrame, statuses: List[str]) -> pd.DataFrame:
        """Filter DataFrame by status values."""
        return df[df['status'].isin(statuses)].copy()
    
    @staticmethod
    def filter_by_assignee(df: pd.DataFrame, assignees: List[str]) -> pd.DataFrame:
        """Filter DataFrame by assignee names."""
        return df[df['assignee'].isin(assignees)].copy()
    
    @staticmethod
    def get_summary_stats(df: pd.DataFrame) -> dict:
        """
        Calculate summary statistics for the dashboard.
        
        Args:
            df: DataFrame with issue data
            
        Returns:
            Dictionary with summary statistics
        """
        if df.empty:
            return {
                'total_issues': 0,
                'overdue_count': 0,
                'due_this_week_count': 0,
                'upcoming_count': 0,
                'no_due_date_count': 0,
                'avg_urgency': 0,
                'high_priority_count': 0,
                'with_subtasks_count': 0
            }
        
        return {
            'total_issues': len(df),
            'overdue_count': df['is_overdue'].sum(),
            'due_this_week_count': len(DataProcessor.filter_due_this_week(df)),
            'upcoming_count': len(DataProcessor.filter_upcoming(df)),
            'no_due_date_count': (~df['has_due_date']).sum(),
            'avg_urgency': df['urgency_score'].mean(),
            'high_priority_count': df[df['priority'].isin(['Highest', 'High'])].shape[0],
            'with_subtasks_count': df['has_subtasks'].sum()
        }
    
    @staticmethod
    def get_unique_values(df: pd.DataFrame, column: str) -> List[str]:
        """Get unique values from a column, sorted."""
        if df.empty or column not in df.columns:
            return []
        
        values = df[column].dropna().unique().tolist()
        return sorted(values)
    
    @staticmethod
    def sort_by_urgency(df: pd.DataFrame, ascending: bool = False) -> pd.DataFrame:
        """Sort DataFrame by urgency score."""
        return df.sort_values('urgency_score', ascending=ascending).copy()
    
    @staticmethod
    def get_top_urgent_issues(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """Get top N most urgent issues."""
        return DataProcessor.sort_by_urgency(df, ascending=False).head(n)
