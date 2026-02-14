#!/usr/bin/env python3
"""
Main Data Pipeline Entry Point

Orchestrates the ETL process: Extract, Validate, Transform, Load
"""

import sys
import os
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.orchestrator import PipelineOrchestrator
from config.settings import Settings


def main():
    """Main pipeline execution"""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "/var/log/pipeline/pipeline.log",
        rotation="10 MB",
        retention="30 days",
        level="DEBUG"
    )

    try:
        # Load configuration
        settings = Settings()
        logger.info(f"Starting pipeline in {settings.environment} environment")

        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(settings)

        # Execute pipeline
        result = orchestrator.run()

        if result.success:
            logger.info(f"Pipeline completed successfully. Processed {result.records_processed} records")
            sys.exit(0)
        else:
            logger.error(f"Pipeline failed: {result.error_message}")
            sys.exit(1)

    except Exception as e:
        logger.exception(f"Fatal error in pipeline: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
