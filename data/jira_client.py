"""JIRA API client for fetching issue data."""

import logging
from typing import List, Optional
from jira import JIRA
from jira.exceptions import JIRAError

from config import Config
from data.models import Issue

logger = logging.getLogger(__name__)


class JiraClient:
    """Client for interacting with JIRA API."""
    
    def __init__(self):
        """Initialize JIRA client with configuration."""
        self.jira = None
        self._connect()
    
    def _connect(self):
        """Establish connection to JIRA."""
        try:
            Config.validate()
            
            # Create JIRA client with basic auth (email + API token)
            self.jira = JIRA(
                server=Config.JIRA_URL,
                basic_auth=(Config.JIRA_EMAIL, Config.JIRA_API_TOKEN)
            )
            
            logger.info(f"Connected to JIRA: {Config.JIRA_URL}")
            
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise
        except JIRAError as e:
            logger.error(f"Failed to connect to JIRA: {e}")
            raise
    
    def fetch_issues(
        self,
        project_keys: Optional[List[str]] = None,
        jql_filter: Optional[str] = None,
        max_results: int = None
    ) -> List[Issue]:
        """
        Fetch issues from JIRA.
        
        Args:
            project_keys: List of project keys to fetch. Defaults to configured projects.
            jql_filter: Additional JQL filter to apply
            max_results: Maximum number of results to fetch
            
        Returns:
            List of Issue objects
        """
        if not self.jira:
            raise RuntimeError("JIRA client not connected")
        
        # Use configured projects if not specified
        if not project_keys:
            project_keys = Config.JIRA_PROJECT_KEYS
        
        # Build JQL query
        project_clause = " OR ".join([f"project = {pk}" for pk in project_keys])
        jql = f"({project_clause})"
        
        # Add custom filter if provided
        if jql_filter:
            jql = f"{jql} AND ({jql_filter})"
        
        # Order by due date (nulls last)
        jql = f"{jql} ORDER BY duedate ASC"
        
        # Fields to retrieve
        fields = [
            'summary',
            'status',
            'priority',
            'assignee',
            'reporter',
            'created',
            'duedate',
            'updated',
            'resolutiondate',
            'issuetype',
            'subtasks',
            'parent',
            'labels',
            'components',
            'project'
        ]
        
        max_results = max_results or Config.JIRA_MAX_RESULTS
        
        logger.info(f"Fetching issues with JQL: {jql}")
        
        try:
            # Fetch issues with pagination
            issues = []
            start_at = 0
            batch_size = 100  # JIRA API limit per request
            
            while len(issues) < max_results:
                batch = self.jira.search_issues(
                    jql,
                    startAt=start_at,
                    maxResults=batch_size,
                    fields=fields
                )
                
                if not batch:
                    break
                
                # Convert to Issue objects
                for jira_issue in batch:
                    try:
                        issue_dict = {
                            'key': jira_issue.key,
                            'fields': {
                                field: getattr(jira_issue.fields, field, None)
                                for field in fields
                            }
                        }
                        
                        # Special handling for nested objects
                        for field in fields:
                            value = getattr(jira_issue.fields, field, None)
                            if value is not None:
                                if hasattr(value, 'raw'):
                                    issue_dict['fields'][field] = value.raw
                                elif hasattr(value, '__dict__'):
                                    issue_dict['fields'][field] = {
                                        k: v for k, v in value.__dict__.items()
                                        if not k.startswith('_')
                                    }
                        
                        issue = Issue.from_jira_dict(issue_dict)
                        issues.append(issue)
                        
                    except Exception as e:
                        logger.error(f"Error parsing issue {jira_issue.key}: {e}")
                        continue
                
                # Check if we got all results
                if len(batch) < batch_size:
                    break
                
                start_at += batch_size
            
            logger.info(f"Fetched {len(issues)} issues")
            return issues
            
        except JIRAError as e:
            logger.error(f"Error fetching issues: {e}")
            raise
    
    def get_issue(self, issue_key: str) -> Optional[Issue]:
        """
        Fetch a single issue by key.
        
        Args:
            issue_key: JIRA issue key (e.g., 'PROJ-123')
            
        Returns:
            Issue object or None if not found
        """
        if not self.jira:
            raise RuntimeError("JIRA client not connected")
        
        try:
            jira_issue = self.jira.issue(issue_key)
            issue_dict = {
                'key': jira_issue.key,
                'fields': {
                    k: getattr(jira_issue.fields, k, None)
                    for k in dir(jira_issue.fields)
                    if not k.startswith('_')
                }
            }
            return Issue.from_jira_dict(issue_dict)
            
        except JIRAError as e:
            logger.error(f"Error fetching issue {issue_key}: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test JIRA connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self.jira:
                return False
            
            # Try to fetch server info
            server_info = self.jira.server_info()
            logger.info(f"Connected to JIRA {server_info.get('version')}")
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
