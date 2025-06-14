#!/usr/bin/env python3
"""
Test script for SQLite support in QwenSense
"""
import sys
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from file_generators import SQLiteFileGenerator
from template_functions import TemplateFunctions

def test_sqlite_generation():
    """Test SQLite file generation."""
    print("🧪 Testing SQLite file generation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        generator = SQLiteFileGenerator(temp_dir)
        
        # Test single table format
        single_table_spec = {
            'table_name': 'employees',
            'columns': [
                {'name': 'id', 'type': 'auto_id'},
                {'name': 'name', 'type': 'TEXT'},
                {'name': 'age', 'type': 'INTEGER'},
                {'name': 'salary', 'type': 'INTEGER'}
            ],
            'rows': 5
        }
        
        result = generator.generate('test_single.db', single_table_spec)
        print(f"✅ Single table: Created {len(result['files_created'])} files")
        print(f"   Content summary: {result['content_generated'][result['files_created'][0]][:200]}...")
        
        # Test multi-table format
        multi_table_spec = {
            'tables': [
                {
                    'name': 'users',
                    'columns': [
                        {'name': 'id', 'type': 'auto_id'},
                        {'name': 'name', 'type': 'TEXT'},
                        {'name': 'email', 'type': 'TEXT'}
                    ],
                    'rows': 3
                },
                {
                    'name': 'orders',
                    'columns': [
                        {'name': 'id', 'type': 'auto_id'},
                        {'name': 'user_id', 'type': 'INTEGER'},
                        {'name': 'amount', 'type': 'INTEGER'},
                        {'name': 'date', 'type': 'DATE'}
                    ],
                    'rows': 5
                }
            ]
        }
        
        result = generator.generate('test_multi.db', multi_table_spec)
        print(f"✅ Multi table: Created {len(result['files_created'])} files")
        print(f"   Content summary: {result['content_generated'][result['files_created'][0]][:300]}...")

def test_sqlite_template_functions():
    """Test SQLite template functions."""
    print("\n🧪 Testing SQLite template functions...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test database
        generator = SQLiteFileGenerator(temp_dir)
        db_spec = {
            'tables': [
                {
                    'name': 'customers',
                    'columns': [
                        {'name': 'id', 'type': 'auto_id'},
                        {'name': 'name', 'type': 'TEXT'},
                        {'name': 'city', 'type': 'TEXT'},
                        {'name': 'age', 'type': 'INTEGER'}
                    ],
                    'rows': 4
                },
                {
                    'name': 'products',
                    'columns': [
                        {'name': 'id', 'type': 'auto_id'},
                        {'name': 'title', 'type': 'TEXT'},
                        {'name': 'price', 'type': 'INTEGER'}
                    ],
                    'rows': 3
                }
            ]
        }
        
        result = generator.generate('test_functions.db', db_spec)
        db_file = result['files_created'][0]
        
        # Test template functions
        tf = TemplateFunctions(temp_dir)
        
        test_cases = [
            "{{sqlite_query:SELECT COUNT(*) FROM customers:test_functions.db}}",
            "{{sqlite_query:SELECT name FROM customers LIMIT 1:test_functions.db}}",
            "{{sqlite_query:SELECT SUM(price) FROM products:test_functions.db}}",
            "{{sqlite_value:0:name:customers:test_functions.db}}",
            "{{sqlite_value:1:age:customers:test_functions.db}}",
        ]
        
        print("   Template function tests:")
        for template in test_cases:
            try:
                result = tf.evaluate_all_functions(template)
                print(f"   ✅ {template} → {result}")
            except Exception as e:
                print(f"   ❌ {template} → ERROR: {e}")

def main():
    """Run all tests."""
    print("🚀 Testing QwenSense SQLite Support")
    print("=" * 50)
    
    try:
        test_sqlite_generation()
        test_sqlite_template_functions()
        print("\n🎉 All tests completed!")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
