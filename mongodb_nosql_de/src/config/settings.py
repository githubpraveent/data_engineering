"""
Configuration Settings

Loads configuration from environment variables and config files.
"""

import os
import yaml
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings"""

    # Environment
    environment: str = Field(default="staging", env="ENVIRONMENT")

    # MongoDB Configuration
    mongodb_uri: str = Field(..., env="MONGODB_URI")
    mongodb_database: str = Field(default="data_pipeline", env="MONGODB_DATABASE")
    
    # Collections
    collection_facts: str = Field(default="transactions_fact", env="COLLECTION_FACTS")
    collection_dimensions: str = Field(default="products_dim", env="COLLECTION_DIMENSIONS")
    collection_aggregates: str = Field(default="daily_aggregates", env="COLLECTION_AGGREGATES")

    # Pipeline Configuration
    batch_size: int = Field(default=1000, env="PIPELINE_BATCH_SIZE")
    workers: int = Field(default=2, env="PIPELINE_WORKERS")
    
    # Source Configuration
    source_type: str = Field(default="csv", env="SOURCE_TYPE")
    source_path: str = Field(default="/opt/data-pipeline/data/source", env="SOURCE_PATH")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Data Quality
    dq_enabled: bool = Field(default=True, env="DQ_ENABLED")
    dq_strict_mode: bool = Field(default=False, env="DQ_STRICT_MODE")
    dq_completeness_threshold: float = Field(default=0.95, env="DQ_COMPLETENESS_THRESHOLD")
    dq_accuracy_threshold: float = Field(default=0.90, env="DQ_ACCURACY_THRESHOLD")
    dq_uniqueness_threshold: float = Field(default=0.99, env="DQ_UNIQUENESS_THRESHOLD")

    @classmethod
    def from_config_file(cls, config_path: Optional[str] = None) -> "Settings":
        """Load settings from YAML config file if available"""
        if config_path is None:
            config_path = os.getenv("CONFIG_PATH", "/opt/data-pipeline/config.yml")

        settings_dict = {}
        
        # Try to load from config file
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, "r") as f:
                config_data = yaml.safe_load(f)
                
                # Flatten nested structure
                if "mongodb" in config_data:
                    settings_dict["mongodb_uri"] = config_data["mongodb"].get("uri")
                    settings_dict["mongodb_database"] = config_data["mongodb"].get("database", "data_pipeline")
                    
                    if "collections" in config_data["mongodb"]:
                        collections = config_data["mongodb"]["collections"]
                        settings_dict["collection_facts"] = collections.get("facts", "transactions_fact")
                        settings_dict["collection_dimensions"] = collections.get("dimensions", "products_dim")
                        settings_dict["collection_aggregates"] = collections.get("aggregates", "daily_aggregates")
                
                if "pipeline" in config_data:
                    pipeline_config = config_data["pipeline"]
                    settings_dict["batch_size"] = pipeline_config.get("batch_size", 1000)
                    settings_dict["workers"] = pipeline_config.get("workers", 2)
                    
                    if "source" in pipeline_config:
                        source_config = pipeline_config["source"]
                        settings_dict["source_type"] = source_config.get("type", "csv")
                        settings_dict["source_path"] = source_config.get("path", "/opt/data-pipeline/data/source")
                
                if "data_quality" in config_data:
                    dq_config = config_data["data_quality"]
                    settings_dict["dq_enabled"] = dq_config.get("enabled", True)
                    settings_dict["dq_strict_mode"] = dq_config.get("strict_mode", False)
                    
                    if "thresholds" in dq_config:
                        thresholds = dq_config["thresholds"]
                        settings_dict["dq_completeness_threshold"] = thresholds.get("completeness", 0.95)
                        settings_dict["dq_accuracy_threshold"] = thresholds.get("accuracy", 0.90)
                        settings_dict["dq_uniqueness_threshold"] = thresholds.get("uniqueness", 0.99)
                
                settings_dict["environment"] = config_data.get("environment", os.getenv("ENVIRONMENT", "staging"))

        # Environment variables override config file
        return cls(**settings_dict)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


# Global settings instance
settings = Settings.from_config_file()
