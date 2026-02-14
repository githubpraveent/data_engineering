#!/usr/bin/env python3
"""
Script to execute Dagster jobs
Handles the naming conflict by adjusting the import path
"""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Rename dagster_code back to dagster temporarily for imports
dagster_code_path = os.path.join(project_root, 'dagster_code')
if os.path.exists(dagster_code_path):
    # Import the dagster package first (the installed one)
    import dagster as dagster_pkg
    
    # Now import our local code using the renamed directory
    import importlib.util
    spec = importlib.util.spec_from_file_location("dagster_code.definitions", 
                                                   os.path.join(dagster_code_path, "definitions.py"))
    definitions_module = importlib.util.module_from_spec(spec)
    
    # Temporarily add dagster_code to sys.modules as 'dagster' for relative imports
    import dagster_code.assets as assets_module
    import dagster_code.jobs.ingestion_job as ingestion_job_module
    import dagster_code.jobs.transformation_job as transformation_job_module
    import dagster_code.jobs.data_quality_job as data_quality_job_module
    
    from dagster_code.definitions import defs
    
    # Execute jobs
    from dagster import DagsterInstance
    
    instance = DagsterInstance.ephemeral()
    
    print("Executing ingestion_job...")
    result1 = defs.get_job_def("ingestion_job").execute_in_process(instance=instance)
    print(f"Ingestion job result: {'SUCCESS' if result1.success else 'FAILED'}")
    
    print("\nExecuting transformation_job...")
    result2 = defs.get_job_def("transformation_job").execute_in_process(instance=instance)
    print(f"Transformation job result: {'SUCCESS' if result2.success else 'FAILED'}")
    
    print("\nExecuting data_quality_job...")
    result3 = defs.get_job_def("data_quality_job").execute_in_process(instance=instance)
    print(f"Data quality job result: {'SUCCESS' if result3.success else 'FAILED'}")
    
    print("\nAll jobs executed!")
else:
    print("Error: dagster_code directory not found")
    sys.exit(1)

