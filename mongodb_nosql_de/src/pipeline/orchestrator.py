"""
Pipeline Orchestrator

Coordinates the ETL process across extract, transform, validate, and load stages.
"""

from dataclasses import dataclass
from typing import Optional
from loguru import logger

from extract.extractor import DataExtractor
from transform.transformer import DataTransformer
from quality.validator import DataQualityValidator
from load.loader import DataLoader
from config.settings import Settings


@dataclass
class PipelineResult:
    """Pipeline execution result"""
    success: bool
    records_processed: int = 0
    records_failed: int = 0
    records_loaded: int = 0
    error_message: Optional[str] = None
    data_quality_score: float = 0.0


class PipelineOrchestrator:
    """Orchestrates the data pipeline execution"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.extractor = DataExtractor(settings)
        self.transformer = DataTransformer(settings)
        self.validator = DataQualityValidator(settings)
        self.loader = DataLoader(settings)

    def run(self) -> PipelineResult:
        """Execute the complete ETL pipeline"""
        logger.info("Starting pipeline orchestration")

        try:
            # Extract phase
            logger.info("Phase 1: Extracting data from source")
            raw_data = self.extractor.extract()
            
            if not raw_data or len(raw_data) == 0:
                logger.warning("No data extracted from source")
                return PipelineResult(success=False, error_message="No data extracted")

            logger.info(f"Extracted {len(raw_data)} records from source")

            # Transform phase
            logger.info("Phase 2: Transforming data")
            transformed_data = self.transformer.transform(raw_data)
            
            if not transformed_data:
                logger.error("Transformation produced no data")
                return PipelineResult(success=False, error_message="Transformation failed")

            logger.info(f"Transformed {len(transformed_data)} records")

            # Validation phase
            validation_result = None
            if self.settings.dq_enabled:
                logger.info("Phase 3: Validating data quality")
                validation_result = self.validator.validate(transformed_data)
                
                if not validation_result.passed:
                    error_msg = f"Data quality validation failed: {validation_result.error_message}"
                    logger.error(error_msg)
                    
                    if self.settings.dq_strict_mode:
                        return PipelineResult(
                            success=False,
                            error_message=error_msg,
                            data_quality_score=validation_result.quality_score
                        )
                    else:
                        logger.warning(f"Data quality issues detected but continuing: {validation_result.error_message}")

                logger.info(f"Data quality score: {validation_result.quality_score:.2%}")
                
                # Filter out invalid records if needed
                if validation_result.invalid_records:
                    logger.warning(f"Filtering {len(validation_result.invalid_records)} invalid records")
                    transformed_data = [
                        record for record in transformed_data 
                        if record.get("_id") not in validation_result.invalid_records
                    ]

            # Load phase
            logger.info("Phase 4: Loading data to MongoDB")
            load_result = self.loader.load(transformed_data)

            if not load_result.success:
                logger.error(f"Load phase failed: {load_result.error_message}")
                return PipelineResult(
                    success=False,
                    error_message=load_result.error_message,
                    records_processed=len(raw_data)
                )

            logger.info(f"Successfully loaded {load_result.records_loaded} records")

            # Build aggregates
            logger.info("Phase 5: Building aggregate collections")
            self.transformer.build_aggregates(self.loader.db)

            # Return success result
            return PipelineResult(
                success=True,
                records_processed=len(raw_data),
                records_loaded=load_result.records_loaded,
                records_failed=len(raw_data) - load_result.records_loaded,
                data_quality_score=validation_result.quality_score if validation_result else 1.0
            )

        except Exception as e:
            logger.exception(f"Pipeline execution failed: {str(e)}")
            return PipelineResult(
                success=False,
                error_message=str(e)
            )
