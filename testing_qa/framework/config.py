"""
Environment configuration management
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dynaconf import Dynaconf


class EnvironmentConfig:
    """Manages environment-specific configuration"""
    
    def __init__(self, env_name: str = None):
        self.env_name = env_name or os.getenv("TEST_ENV", "dev")
        self.config_path = Path(__file__).parent.parent / "config" / "environments"
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from JSON file"""
        config_file = self.config_path / f"{self.env_name}.json"
        
        if not config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_file}. "
                f"Please copy from {self.env_name}.example.json and configure."
            )
        
        with open(config_file, 'r') as f:
            self._config = json.load(f)
        
        # Resolve environment variables
        self._resolve_env_vars(self._config)
    
    def _resolve_env_vars(self, obj: Any) -> Any:
        """Recursively resolve environment variables in config"""
        if isinstance(obj, dict):
            return {k: self._resolve_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)
        return obj
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    @property
    def api_gateway(self) -> Dict[str, Any]:
        """Get API Gateway configuration"""
        return self._config.get("api_gateway", {})
    
    @property
    def lambda_config(self) -> Dict[str, Any]:
        """Get Lambda configuration"""
        return self._config.get("lambda", {})
    
    @property
    def queues(self) -> Dict[str, str]:
        """Get queue configurations"""
        return self._config.get("queues", {})
    
    @property
    def async_config(self) -> Dict[str, Any]:
        """Get async testing configuration"""
        return self._config.get("async", {})
    
    @property
    def downstream_services(self) -> Dict[str, Any]:
        """Get downstream service configurations"""
        return self._config.get("downstream_services", {})
    
    @property
    def aws_config(self) -> Dict[str, Any]:
        """Get AWS configuration"""
        return self._config.get("aws", {})


# Global config instance
_config_instance: Optional[EnvironmentConfig] = None


def get_config(env_name: str = None) -> EnvironmentConfig:
    """Get or create configuration instance"""
    global _config_instance
    if _config_instance is None or (env_name and _config_instance.env_name != env_name):
        _config_instance = EnvironmentConfig(env_name)
    return _config_instance

