"""
Test data management
"""
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from faker import Faker
import logging

logger = logging.getLogger(__name__)


class TestDataManager:
    """Manages test data and parameterization"""
    
    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "test_data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.faker = Faker()
        self._cache: Dict[str, Any] = {}
    
    def load_json(self, filename: str) -> Dict[str, Any]:
        """Load test data from JSON file"""
        file_path = self.data_dir / filename
        if not file_path.exists():
            logger.warning(f"Test data file not found: {file_path}")
            return {}
        
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load test data from YAML file"""
        file_path = self.data_dir / filename
        if not file_path.exists():
            logger.warning(f"Test data file not found: {file_path}")
            return {}
        
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    
    def generate_fake_data(self, schema: Dict[str, str]) -> Dict[str, Any]:
        """Generate fake data based on schema"""
        data = {}
        for key, data_type in schema.items():
            if data_type == "email":
                data[key] = self.faker.email()
            elif data_type == "name":
                data[key] = self.faker.name()
            elif data_type == "uuid":
                data[key] = self.faker.uuid4()
            elif data_type == "date":
                data[key] = self.faker.date()
            elif data_type == "text":
                data[key] = self.faker.text()
            elif data_type == "int":
                data[key] = self.faker.random_int()
            elif data_type == "float":
                data[key] = self.faker.pyfloat()
            else:
                data[key] = self.faker.word()
        return data
    
    def get_template(self, template_name: str, **kwargs) -> Dict[str, Any]:
        """Get test data template with substitutions"""
        template = self.load_json(f"{template_name}.json")
        
        # Substitute variables
        def substitute(obj):
            if isinstance(obj, dict):
                return {k: substitute(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [substitute(item) for item in obj]
            elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
                var_name = obj[2:-1]
                return kwargs.get(var_name, obj)
            return obj
        
        return substitute(template)
    
    def save_data(self, filename: str, data: Dict[str, Any]):
        """Save test data to file"""
        file_path = self.data_dir / filename
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved test data to {file_path}")

