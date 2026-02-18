"""
Configuration management for JIRA Dashboard.
Loads environment variables and provides configuration access.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for JIRA Dashboard."""
    
    # JIRA API Configuration
    JIRA_URL = os.getenv('JIRA_URL')
    JIRA_USERNAME = os.getenv('JIRA_USERNAME')
    JIRA_PASSWORD = os.getenv('JIRA_PASSWORD')

    # Optional: restrict to specific projects (comma-separated, e.g. PROJ1,PROJ2).
    # If unset, all projects accessible to the user are fetched.
    _raw_project_keys = os.getenv('JIRA_PROJECT_KEYS', '').strip()
    JIRA_PROJECT_KEYS = [k.strip() for k in _raw_project_keys.split(',') if k.strip()]

    JIRA_MAX_RESULTS = int(os.getenv('JIRA_MAX_RESULTS', '1000'))
    
    # Dashboard Configuration
    CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', '900'))  # 15 minutes
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', '8050'))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # Pagination
    TABLE_PAGE_SIZE = 50
    
    # Urgency Calculation Weights
    PRIORITY_WEIGHT = 0.4
    DAYS_PAST_DUE_WEIGHT = 0.4
    SUBTASK_COMPLETION_WEIGHT = 0.2
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        required = ['JIRA_URL', 'JIRA_USERNAME', 'JIRA_PASSWORD']
        missing = [key for key in required if not getattr(cls, key)]
        
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}. "
                "Please set these in your .env file."
            )
        
        return True


# Validate configuration on import
if __name__ != '__main__':
    try:
        Config.validate()
    except ValueError:
        # Don't fail on import, allow app to show error message
        pass
