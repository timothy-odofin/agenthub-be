"""
Command-line interface utilities for AgentHub.

Provides professional argument parsing for application configuration,
including environment file selection for multi-environment deployments.
"""
import argparse
import sys
from pathlib import Path
from typing import Optional, List


class AgentHubCLI:
    """Command-line interface for AgentHub application."""
    
    def __init__(self):
        """Initialize CLI parser."""
        self.parser = argparse.ArgumentParser(
            prog='agenthub',
            description='AgentHub - AI-powered agent hub with multi-provider LLM support',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Use default .env file
  python -m uvicorn app.main:app
  
  # Use development environment
  python -m uvicorn app.main:app --env .env.dev
  
  # Use staging environment  
  python -m uvicorn app.main:app --env .env.staging
  
  # Use production environment with mounted secrets
  python -m uvicorn app.main:app --env /secrets/.env.production

Environment Variables:
  The application loads environment variables in this order:
  1. System environment variables (highest priority)
  2. Environment file specified by --env argument
  3. Default .env file (if --env not specified)
  
  System environment variables always take precedence over file variables.

For more information, visit: https://github.com/timothy-odofin/agenthub-be
            """
        )
        
        self._setup_arguments()
    
    def _setup_arguments(self) -> None:
        """Setup command-line arguments."""
        # Environment configuration
        env_group = self.parser.add_argument_group('Environment Configuration')
        env_group.add_argument(
            '--env',
            type=str,
            default='.env',
            metavar='PATH',
            help='Path to environment file (default: .env). '
                 'Use different files for dev/staging/production deployments.'
        )
        
        env_group.add_argument(
            '--env-required',
            action='store_true',
            help='Exit with error if environment file is not found (default: warn and continue)'
        )
        
        # Application configuration
        app_group = self.parser.add_argument_group('Application Configuration')
        app_group.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug mode (overrides DEBUG environment variable)'
        )
        
        app_group.add_argument(
            '--log-level',
            type=str,
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            metavar='LEVEL',
            help='Set logging level (overrides LOG_LEVEL environment variable)'
        )
        
        # Version
        self.parser.add_argument(
            '--version',
            action='version',
            version='AgentHub 1.0.0'
        )
    
    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """Parse command-line arguments.
        
        Args:
            args: List of arguments to parse. If None, uses sys.argv
            
        Returns:
            Parsed arguments namespace
        """
        # Use parse_known_args to allow uvicorn/gunicorn args to pass through
        parsed_args, unknown = self.parser.parse_known_args(args)
        
        # Validate environment file path
        env_path = Path(parsed_args.env)
        
        if not env_path.exists():
            if parsed_args.env_required:
                self.parser.error(f"Environment file not found: {env_path}")
            # Otherwise, just a warning (handled in EnvironmentManager)
        
        return parsed_args
    
    def get_env_file(self, args: Optional[argparse.Namespace] = None) -> Optional[str]:
        """Get environment file path from arguments.
        
        Args:
            args: Parsed arguments. If None, parses from sys.argv
            
        Returns:
            Path to environment file, or None if not specified
        """
        if args is None:
            args = self.parse_args()
        
        return args.env if args.env else None


# Global CLI instance
cli = AgentHubCLI()


def parse_cli_args() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Convenience function for quick access to CLI parsing.
    
    Returns:
        Parsed arguments namespace
    """
    return cli.parse_args()


def get_env_file_from_cli() -> Optional[str]:
    """Get environment file path from CLI arguments.
    
    Convenience function for quick access to env file path.
    
    Returns:
        Path to environment file specified in CLI arguments
    """
    return cli.get_env_file()
