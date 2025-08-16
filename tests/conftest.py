"""
Shared pytest fixtures for PICARD tests.
"""
import pytest
import tempfile
import json
import csv
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from file_generators import (
    TextFileGenerator, CSVFileGenerator, 
    SQLiteFileGenerator, JSONFileGenerator,
    FileGeneratorFactory
)
from template_functions import TemplateFunctions


@pytest.fixture
def temp_workspace():
    """Provide a temporary directory for file operations."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def template_functions(temp_workspace):
    """Pre-configured TemplateFunctions instance."""
    return TemplateFunctions(str(temp_workspace))


@pytest.fixture
def sample_csv_data():
    """Standard CSV test data for consistent testing."""
    return {
        'headers': ['id', 'name', 'age', 'city', 'status'],
        'rows': [
            ['1', 'John Doe', '25', 'New York', 'active'],
            ['2', 'Jane Smith', '30', 'Los Angeles', 'inactive'],
            ['3', 'Bob Johnson', '35', 'Chicago', 'active'],
            ['4', 'Alice Brown', '28', 'Boston', 'active']
        ]
    }


@pytest.fixture
def sample_json_data():
    """Standard JSON test data for consistent testing."""
    return {
        "users": [
            {"id": 1, "name": "John", "age": 25, "active": True, "city": "New York"},
            {"id": 2, "name": "Alice", "age": 30, "active": False, "city": "Los Angeles"},
            {"id": 3, "name": "Bob", "age": 35, "active": True, "city": "Chicago"}
        ],
        "metadata": {
            "total": 3,
            "version": "1.0",
            "created": "2025-01-01"
        },
        "config": {
            "settings": {
                "debug": True,
                "timeout": 30,
                "max_retries": 5
            }
        }
    }


@pytest.fixture
def create_csv_file(temp_workspace, sample_csv_data):
    """Create a sample CSV file for testing."""
    def _create_csv(filename="test.csv", data=None):
        if data is None:
            data = sample_csv_data
        
        csv_file = temp_workspace / filename
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(data['headers'])
            writer.writerows(data['rows'])
        
        return str(csv_file)
    
    return _create_csv


@pytest.fixture
def create_json_file(temp_workspace, sample_json_data):
    """Create a sample JSON file for testing."""
    def _create_json(filename="test.json", data=None):
        if data is None:
            data = sample_json_data
        
        json_file = temp_workspace / filename
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return str(json_file)
    
    return _create_json


@pytest.fixture
def create_text_file(temp_workspace):
    """Create a sample text file for testing."""
    def _create_text(filename="test.txt", lines=None):
        if lines is None:
            lines = [
                "Line 1 with some words",
                "Line 2 has different content", 
                "Line 3 contains special data",
                "Line 4 is the penultimate line",
                "Line 5 is the final line"
            ]
        
        text_file = temp_workspace / filename
        text_file.write_text('\n'.join(lines))
        
        return str(text_file)
    
    return _create_text


# File Generator Fixtures

@pytest.fixture
def text_generator(temp_workspace):
    """Pre-configured TextFileGenerator."""
    return TextFileGenerator(str(temp_workspace))


@pytest.fixture
def csv_generator(temp_workspace):
    """Pre-configured CSVFileGenerator."""
    return CSVFileGenerator(str(temp_workspace))


@pytest.fixture
def sqlite_generator(temp_workspace):
    """Pre-configured SQLiteFileGenerator."""
    return SQLiteFileGenerator(str(temp_workspace))


@pytest.fixture
def json_generator(temp_workspace):
    """Pre-configured JSONFileGenerator."""
    return JSONFileGenerator(str(temp_workspace))


@pytest.fixture
def file_generator_factory(temp_workspace):
    """FileGeneratorFactory for testing factory patterns."""
    def _create_generator(generator_type):
        return FileGeneratorFactory.create_generator(generator_type, str(temp_workspace))
    
    return _create_generator