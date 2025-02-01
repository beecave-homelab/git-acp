"""Configuration loader module for git_acp package."""
from git_acp.config.env_config import load_env_config

def load_config() -> None:
    """
    Load and validate configuration.
    
    Currently, this loads environment variables.
    Future versions may merge configurations from multiple sources.
    """
    load_env_config() 