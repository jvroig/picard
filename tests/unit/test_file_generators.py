"""
Unit tests for all file generators.

Migrated from the main() functions in src/file_generators.py
"""
import pytest
import json
import csv
import sqlite3
import sys
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from file_generators import (
    TextFileGenerator, CSVFileGenerator, SQLiteFileGenerator, 
    JSONFileGenerator, FileGeneratorFactory, FileGeneratorError
)


@pytest.mark.unit
@pytest.mark.file_generation
class TestTextFileGenerator:
    """Test text file generation functionality."""
    
    def test_lorem_lines_generation(self, text_generator, temp_workspace):
        """Test lorem ipsum lines generation."""
        result = text_generator.generate(
            target_file="test_data/sample.txt",
            content_spec={'type': 'lorem_lines', 'count': 5},
            clutter_spec={'count': 3}
        )
        
        assert len(result['files_created']) >= 4  # Main file + 3 clutter files
        assert result['errors'] == []
        
        # Verify main file
        target_file = temp_workspace / "test_data/sample.txt"
        assert target_file.exists()
        
        content = target_file.read_text()
        lines = content.strip().split('\n')
        assert len(lines) == 5
        
        # Each line should have content
        for line in lines:
            assert len(line.strip()) > 0
    
    def test_lorem_sentences_generation(self, text_generator, temp_workspace):
        """Test lorem ipsum sentences generation."""
        result = text_generator.generate(
            target_file="sentences.txt",
            content_spec={'type': 'lorem_sentences', 'count': 3}
        )
        
        assert result['errors'] == []
        target_file = temp_workspace / "sentences.txt"
        content = target_file.read_text()
        
        # Should contain multiple sentences (periods)
        assert content.count('.') >= 3
    
    def test_custom_content_with_placeholders(self, text_generator, temp_workspace):
        """Test custom content with {{lorem:...}} placeholders."""
        custom_content = "Header\n{{lorem:3l}}\nFooter"
        
        result = text_generator.generate(
            target_file="custom.txt",
            content_spec={'type': 'custom', 'content': custom_content}
        )
        
        assert result['errors'] == []
        target_file = temp_workspace / "custom.txt"
        content = target_file.read_text()
        
        assert content.startswith("Header\n")
        assert content.endswith("\nFooter")
        # Should have 3 lines between Header and Footer
        lines = content.split('\n')
        assert len(lines) == 5  # Header + 3 lorem lines + Footer


@pytest.mark.unit
@pytest.mark.file_generation
class TestCSVFileGenerator:
    """Test CSV file generation functionality."""
    
    def test_basic_csv_generation(self, csv_generator, temp_workspace):
        """Test basic CSV generation with auto-detected field types."""
        result = csv_generator.generate(
            target_file="test_data/basic.csv",
            content_spec={
                'headers': ['id', 'name', 'age', 'city', 'status'], 
                'rows': 5
            },
            clutter_spec={'count': 2}
        )
        
        assert len(result['files_created']) >= 3  # Main + 2 clutter
        assert result['errors'] == []
        
        # Verify CSV structure
        target_file = temp_workspace / "test_data/basic.csv"
        assert target_file.exists()
        
        csv_data = result['csv_data'][str(target_file)]
        assert len(csv_data) == 6  # Header + 5 rows
        assert csv_data[0] == ['id', 'name', 'age', 'city', 'status']
        
        # Verify data types were generated appropriately
        for row in csv_data[1:]:
            assert len(row) == 5
            # ID should be numeric string
            assert row[0].isdigit()
            # Name should be non-empty string
            assert len(row[1]) > 0
            # Age should be numeric
            assert row[2].isdigit()
    
    def test_explicit_header_types(self, csv_generator, temp_workspace):
        """Test CSV generation with explicit header types."""
        result = csv_generator.generate(
            target_file="explicit.csv",
            content_spec={
                'headers': ['CUST_ID', 'CUST_NM', 'ORD_AMT', 'STAT_CD'],
                'header_types': ['id', 'person_name', 'price', 'status'],
                'rows': 3
            }
        )
        
        assert result['errors'] == []
        csv_data = result['csv_data'][str(temp_workspace / "explicit.csv")]
        
        assert len(csv_data) == 4  # Header + 3 rows
        
        # Verify explicit types were used
        for row in csv_data[1:]:
            # ID (first column)
            assert row[0].isdigit()
            # Name (second column) - should have space for person_name
            assert ' ' in row[1]
            # Price (third column) - should have decimal
            assert '.' in row[2]
            # Status (fourth column) - should be valid status
            assert row[3] in ['active', 'inactive', 'completed', 'pending', 'cancelled', 'approved', 'rejected', 'processing']
    
    def test_field_type_auto_detection(self, csv_generator):
        """Test automatic field type detection."""
        from file_generators import DataGenerator
        data_gen = DataGenerator()
        
        test_cases = [
            ('name', 'person_name'),
            ('email', 'email'),
            ('age', 'age'),
            ('status', 'status'),
            ('department', 'department'),
            ('order_id', 'id'),
            ('years_experience', 'experience')
        ]
        
        for header, expected_type in test_cases:
            detected_type = data_gen.auto_detect_field_type(header)
            assert detected_type == expected_type


@pytest.mark.unit
@pytest.mark.file_generation
class TestSQLiteFileGenerator:
    """Test SQLite database generation functionality."""
    
    def test_simple_table_creation(self, sqlite_generator, temp_workspace):
        """Test basic SQLite table creation."""
        result = sqlite_generator.generate(
            target_file="simple.db",
            content_spec={
                'table_name': 'users',
                'columns': [
                    {'name': 'id', 'type': 'INTEGER'},
                    {'name': 'name', 'type': 'TEXT'},
                    {'name': 'age', 'type': 'INTEGER'}
                ],
                'rows': 3
            }
        )
        
        assert result['errors'] == []
        db_file = temp_workspace / "simple.db"
        assert db_file.exists()
        
        # Verify database content
        sqlite_data = result['sqlite_data'][str(db_file)]
        assert 'users' in sqlite_data
        
        table_data = sqlite_data['users']
        assert len(table_data['rows']) == 3
        assert len(table_data['columns']) == 3
        
        # Verify we can actually query the database
        conn = sqlite3.connect(str(db_file))
        try:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            assert ('users',) in tables
            
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            assert count == 3
        finally:
            conn.close()
    
    def test_multi_table_database(self, sqlite_generator, temp_workspace):
        """Test multi-table database generation."""
        result = sqlite_generator.generate(
            target_file="multi.db",
            content_spec={
                'tables': [
                    {
                        'name': 'customers',
                        'columns': [
                            {'name': 'id', 'type': 'auto_id'},
                            {'name': 'name', 'type': 'TEXT', 'data_type': 'person_name'},
                            {'name': 'email', 'type': 'TEXT', 'data_type': 'email'}
                        ],
                        'rows': 2
                    },
                    {
                        'name': 'orders',
                        'columns': [
                            {'name': 'id', 'type': 'auto_id'},
                            {'name': 'customer_id', 'type': 'INTEGER', 'foreign_key': 'customers.id'},
                            {'name': 'amount', 'type': 'REAL'}
                        ],
                        'rows': 3
                    }
                ]
            }
        )
        
        assert result['errors'] == []
        db_file = temp_workspace / "multi.db"
        
        sqlite_data = result['sqlite_data'][str(db_file)]
        assert 'customers' in sqlite_data
        assert 'orders' in sqlite_data
        
        # Verify foreign key relationships work
        conn = sqlite3.connect(str(db_file))
        try:
            # Should have 2 customers
            cursor = conn.execute("SELECT COUNT(*) FROM customers")
            assert cursor.fetchone()[0] == 2
            
            # Should have 3 orders
            cursor = conn.execute("SELECT COUNT(*) FROM orders")
            assert cursor.fetchone()[0] == 3
            
            # Foreign keys should reference valid customer IDs
            cursor = conn.execute("SELECT DISTINCT customer_id FROM orders")
            foreign_keys = [row[0] for row in cursor.fetchall()]
            for fk in foreign_keys:
                assert fk in [1, 2]  # Should reference customer IDs 1 or 2
        finally:
            conn.close()
    
    def test_data_type_integration(self, sqlite_generator, temp_workspace):
        """Test integration with DataGenerator field types."""
        result = sqlite_generator.generate(
            target_file="datatypes.db",
            content_spec={
                'table_name': 'employees',
                'columns': [
                    {'name': 'id', 'type': 'INTEGER', 'data_type': 'id'},
                    {'name': 'name', 'type': 'TEXT', 'data_type': 'person_name'},
                    {'name': 'department', 'type': 'TEXT', 'data_type': 'department'},
                    {'name': 'salary', 'type': 'INTEGER', 'data_type': 'salary'}
                ],
                'rows': 2
            }
        )
        
        assert result['errors'] == []
        sqlite_data = result['sqlite_data'][str(temp_workspace / "datatypes.db")]
        
        table_data = sqlite_data['employees']
        for row in table_data['rows']:
            # Verify data types make sense
            assert isinstance(row[0], str) and row[0].isdigit()  # ID
            assert isinstance(row[1], str) and ' ' in row[1]     # person_name has space
            assert isinstance(row[2], str)                       # department
            assert isinstance(row[3], str) and row[3].isdigit()  # salary


@pytest.mark.unit
@pytest.mark.file_generation
class TestFileGeneratorFactory:
    """Test the FileGeneratorFactory."""
    
    @pytest.mark.parametrize("generator_type,expected_class", [
        ('create_files', TextFileGenerator),
        ('create_csv', CSVFileGenerator),
        ('create_sqlite', SQLiteFileGenerator),
        ('create_json', JSONFileGenerator),
    ])
    def test_factory_creates_correct_generators(self, temp_workspace, generator_type, expected_class):
        """Test factory creates the correct generator types."""
        generator = FileGeneratorFactory.create_generator(generator_type, str(temp_workspace))
        assert isinstance(generator, expected_class)
    
    def test_factory_unknown_type_raises_error(self, temp_workspace):
        """Test factory raises error for unknown generator types."""
        with pytest.raises(FileGeneratorError, match="Unknown generator type"):
            FileGeneratorFactory.create_generator('create_unknown', str(temp_workspace))


@pytest.mark.unit
@pytest.mark.file_generation
class TestErrorHandling:
    """Test error handling across file generators."""
    
    def test_csv_header_types_length_mismatch(self, csv_generator):
        """Test CSV generator handles header_types length mismatch."""
        with pytest.raises(FileGeneratorError, match="header_types length.*must match headers length"):
            csv_generator.generate(
                target_file="error.csv",
                content_spec={
                    'headers': ['a', 'b'],
                    'header_types': ['id'],  # Length mismatch
                    'rows': 1
                }
            )
    
    def test_invalid_sqlite_foreign_key(self, sqlite_generator):
        """Test SQLite generator handles invalid foreign key references."""
        with pytest.raises(FileGeneratorError, match="Referenced table.*not found"):
            sqlite_generator.generate(
                target_file="error.db",
                content_spec={
                    'table_name': 'orders',
                    'columns': [
                        {'name': 'customer_id', 'type': 'INTEGER', 'foreign_key': 'nonexistent.id'}
                    ],
                    'rows': 1
                }
            )