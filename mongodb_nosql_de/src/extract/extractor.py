"""
Data Extractor

Handles extraction of data from various sources (CSV, API, database).
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

from config.settings import Settings


class DataExtractor:
    """Extracts data from configured source"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.source_type = settings.source_type
        self.source_path = settings.source_path

    def extract(self) -> List[Dict[str, Any]]:
        """Extract data from source"""
        logger.info(f"Extracting data from {self.source_type} source: {self.source_path}")

        if self.source_type == "csv":
            return self._extract_csv()
        elif self.source_type == "json":
            return self._extract_json()
        elif self.source_type == "api":
            return self._extract_api()
        else:
            raise ValueError(f"Unsupported source type: {self.source_type}")

    def _extract_csv(self) -> List[Dict[str, Any]]:
        """Extract data from CSV file"""
        source_file = Path(self.source_path)
        
        if not source_file.exists():
            # Try to find any CSV file in the directory
            source_dir = Path(self.source_path)
            if source_dir.is_dir():
                csv_files = list(source_dir.glob("*.csv"))
                if csv_files:
                    source_file = csv_files[0]
                    logger.info(f"Using CSV file: {source_file}")
                else:
                    raise FileNotFoundError(f"No CSV files found in {self.source_path}")
            else:
                raise FileNotFoundError(f"Source file not found: {self.source_path}")

        data = []
        with open(source_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean up empty values
                cleaned_row = {k: (v.strip() if v else None) for k, v in row.items()}
                data.append(cleaned_row)

        logger.info(f"Extracted {len(data)} records from CSV file")
        return data

    def _extract_json(self) -> List[Dict[str, Any]]:
        """Extract data from JSON file"""
        source_file = Path(self.source_path)
        
        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {self.source_path}")

        with open(source_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both list and single object
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise ValueError(f"JSON file must contain a list or object, got {type(data)}")

        logger.info(f"Extracted {len(data)} records from JSON file")
        return data

    def _extract_api(self) -> List[Dict[str, Any]]:
        """Extract data from API endpoint"""
        import requests
        
        try:
            response = requests.get(self.source_path, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle both list and single object
            if isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                raise ValueError(f"API must return a list or object, got {type(data)}")

            logger.info(f"Extracted {len(data)} records from API")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to extract data from API: {str(e)}")
            raise
