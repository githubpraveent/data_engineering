from ingestion.batch.extract_files import extract_files
from ingestion.batch.extract_sqlserver import extract_sqlserver
from ingestion.batch.load_snowflake import load_to_snowflake


def run_batch_pipeline():
    file_payloads = extract_files()
    sql_payloads = extract_sqlserver()
    load_to_snowflake(file_payloads, sql_payloads)
