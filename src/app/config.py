import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, cast
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key"
    DATABASE_URL = os.environ.get("DATABASE_URL") or "sqlite:///instance/aipackager.db"
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or "instance/uploads"
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 209715200))
    AI_MODEL = os.environ.get(
        "AI_MODEL", "gpt-4o-mini"
    )  # Default to gpt-4o-mini if not set


class ProductionConfig(Config):
    """Production specific configuration."""

    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Development specific configuration."""

    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing specific configuration."""

    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"


class MCPConfigLoader:
    """Configuration loader for MCP servers."""

    def __init__(self, config_path: str = "mcp_config.json"):
        """Initialize the MCP configuration loader.

        Args:
            config_path: Path to the MCP configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load and parse the MCP configuration file.

        Returns:
            Dictionary containing the parsed configuration

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            json.JSONDecodeError: If the configuration file is invalid JSON
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"MCP config file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            config = json.load(f)

        # Environment variable substitution
        return cast(Dict[str, Any], self._substitute_env_vars(config))

    def _substitute_env_vars(self, obj: Any) -> Any:
        """Recursively substitute ${VAR} with environment variables.

        Args:
            obj: Object to process (dict, list, str, etc.)

        Returns:
            Object with environment variables substituted
        """
        if isinstance(obj, dict):
            return cast(
                Dict[str, Any],
                {key: self._substitute_env_vars(value) for key, value in obj.items()},
            )
        elif isinstance(obj, list):
            return cast(List[Any], [self._substitute_env_vars(item) for item in obj])
        elif isinstance(obj, str):
            # Replace ${VAR} with environment variable value
            pattern = re.compile(r"\$\{([^}]+)\}")

            def replace_var(match: re.Match[str]) -> str:
                var_name = match.group(1)
                return os.environ.get(
                    var_name, match.group(0)
                )  # Return original if not found

            return pattern.sub(replace_var, obj)
        else:
            return obj

    def get_server_config(self, server_name: str) -> Dict[str, Any]:
        """Get configuration for a specific MCP server.

        Args:
            server_name: Name of the MCP server

        Returns:
            Dictionary containing the server configuration
        """
        return cast(
            Dict[str, Any], self.config.get("mcpServers", {}).get(server_name, {})
        )

    def is_server_enabled(self, server_name: str) -> bool:
        """Check if a specific MCP server is enabled.

        Args:
            server_name: Name of the MCP server

        Returns:
            True if the server is enabled, False otherwise
        """
        server_config = self.get_server_config(server_name)
        return cast(bool, server_config.get("enabled", False))

    def get_server_url(self, server_name: str) -> str:
        """Get the URL for a specific MCP server.

        Args:
            server_name: Name of the MCP server

        Returns:
            URL string for the server

        Raises:
            KeyError: If the server is not configured or URL is missing
        """
        server_config = self.get_server_config(server_name)
        if not server_config:
            raise KeyError(f"MCP server '{server_name}' not found in configuration")

        url = server_config.get("url")
        if not url:
            raise KeyError(f"URL not configured for MCP server '{server_name}'")

        return cast(str, url)

    def get_server_env(self, server_name: str) -> Dict[str, str]:
        """Get environment variables for a specific MCP server.

        Args:
            server_name: Name of the MCP server

        Returns:
            Dictionary of environment variables
        """
        server_config = self.get_server_config(server_name)
        return cast(Dict[str, str], server_config.get("env", {}))
