"""
Integration tests for complete pipeline
"""

import pytest
from pathlib import Path
from pipeline.orchestrator import PipelineOrchestrator
from config.settings import Settings


@pytest.mark.integration
def test_end_to_end_pipeline(mongodb_uri="mongodb://localhost:27017/test_integration"):
    """Test complete ETL pipeline"""
    settings = Settings(
        environment="test",
        mongodb_uri=mongodb_uri,
        mongodb_database="test_integration",
        source_type="csv",
        source_path=str(Path(__file__).parent.parent.parent / "data" / "sample" / "transactions_sample.csv"),
        batch_size=10,
        dq_enabled=True,
        dq_strict_mode=False
    )
    
    orchestrator = PipelineOrchestrator(settings)
    result = orchestrator.run()
    
    assert result.success is True
    assert result.records_processed > 0
    assert result.records_loaded > 0
