#!/usr/bin/env python3
"""
Test Step 3: File Generator Infrastructure Implementation
"""
import sys
import tempfile
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from file_generators import (
    LoremGenerator, DataGenerator, TextFileGenerator, CSVFileGenerator, 
    FileGeneratorFactory, FileGeneratorError
)

def test_lorem_generator():
    """Test lorem ipsum generation functionality."""
    lorem = LoremGenerator()
    
    tests = [
        ('generate_words', 5, lambda x: len(x.split()) == 5),
        ('generate_sentence', None, lambda x: x.endswith('.') and x[0].isupper()),
        ('generate_sentences', 3, lambda x: x.count('.') == 3),
        ('generate_paragraph', None, lambda x: len(x.split('.')) >= 4),
        ('generate_lines', 4, lambda x: len(x.split('\n')) == 4),
        ('generate_paragraphs', 2, lambda x: '\n\n' in x),
    ]
    
    passed = 0
    print("Testing LoremGenerator:")
    
    for method_name, arg, validator in tests:
        try:
            method = getattr(lorem, method_name)
            if arg is not None:
                result = method(arg)
            else:
                result = method()
            
            if validator(result):
                print(f"  ✅ {method_name}() → Valid output")
                passed += 1
            else:
                print(f"  ❌ {method_name}() → Invalid output: {result[:50]}...")
        except Exception as e:
            print(f"  ❌ {method_name}() → Error: {e}")
    
    print(f"LoremGenerator: {passed}/{len(tests)} tests passed")
    return passed == len(tests)

def test_data_generator():
    """Test CSV data generation functionality."""
    data_gen = DataGenerator()
    
    # Test field type generation
    field_tests = [
        ('person_name', lambda x: ' ' in x and len(x.split()) == 2),
        ('email', lambda x: '@' in x and '.' in x),
        ('age', lambda x: x.isdigit() and 18 <= int(x) <= 70),
        ('city', lambda x: len(x) > 0 and x.isalpha() or ' ' in x),
        ('phone', lambda x: '(' in x and ')' in x and '-' in x),
        ('price', lambda x: '.' in x and x.replace('.', '').isdigit()),
    ]
    
    passed = 0
    print("\nTesting DataGenerator:")
    
    for field_type, validator in field_tests:
        try:
            result = data_gen.generate_field(field_type)
            if validator(result):
                print(f"  ✅ {field_type} → {result}")
                passed += 1
            else:
                print(f"  ❌ {field_type} → Invalid: {result}")
        except Exception as e:
            print(f"  ❌ {field_type} → Error: {e}")
    
    # Test auto-detection
    auto_tests = [
        ('name', 'person_name'),
        ('email', 'email'),
        ('age', 'age'),
        ('random_field', 'lorem_words'),
    ]
    
    for header, expected_type in auto_tests:
        detected = data_gen.auto_detect_field_type(header)
        if detected == expected_type:
            print(f"  ✅ Auto-detect '{header}' → {detected}")
            passed += 1
        else:
            print(f"  ❌ Auto-detect '{header}' → {detected} (expected {expected_type})")
    
    total_tests = len(field_tests) + len(auto_tests)
    print(f"DataGenerator: {passed}/{total_tests} tests passed")
    return passed == total_tests

def test_text_file_generator():
    """Test text file generation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        text_gen = TextFileGenerator(temp_dir)
        
        test_cases = [
            {
                'name': 'Basic lorem lines',
                'content_spec': {'type': 'lorem_lines', 'count': 5},
                'validator': lambda content: len(content.split('\n')) == 5
            },
            {
                'name': 'Lorem sentences',
                'content_spec': {'type': 'lorem_sentences', 'count': 3},
                'validator': lambda content: content.count('.') == 3
            },
            {
                'name': 'Custom content with lorem',
                'content_spec': {'type': 'custom', 'content': 'Start\n{{lorem:2l}}\nEnd'},
                'validator': lambda content: 'Start' in content and 'End' in content
            }
        ]
        
        passed = 0
        print("\nTesting TextFileGenerator:")
        
        for test_case in test_cases:
            try:
                result = text_gen.generate(
                    target_file=f"test_{test_case['name'].replace(' ', '_')}.txt",
                    content_spec=test_case['content_spec']
                )
                
                # Check if file was created
                if len(result['files_created']) > 0:
                    content = result['content_generated'][result['files_created'][0]]
                    if test_case['validator'](content):
                        print(f"  ✅ {test_case['name']}")
                        passed += 1
                    else:
                        print(f"  ❌ {test_case['name']} → Content validation failed")
                else:
                    print(f"  ❌ {test_case['name']} → No files created")
                    
            except Exception as e:
                print(f"  ❌ {test_case['name']} → Error: {e}")
        
        print(f"TextFileGenerator: {passed}/{len(test_cases)} tests passed")
        return passed == len(test_cases)

def test_csv_file_generator():
    """Test CSV file generation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_gen = CSVFileGenerator(temp_dir)
        
        test_cases = [
            {
                'name': 'Basic CSV with headers',
                'content_spec': {'headers': ['name', 'email', 'age'], 'rows': 3},
                'validator': lambda data: len(data) == 4 and data[0] == ['name', 'email', 'age']
            },
            {
                'name': 'CSV with auto-detected types',
                'content_spec': {'headers': ['company', 'phone', 'city'], 'rows': 2},
                'validator': lambda data: len(data) == 3 and len(data[1]) == 3
            }
        ]
        
        passed = 0
        print("\nTesting CSVFileGenerator:")
        
        for test_case in test_cases:
            try:
                result = csv_gen.generate(
                    target_file=f"test_{test_case['name'].replace(' ', '_')}.csv",
                    content_spec=test_case['content_spec']
                )
                
                # Check CSV data
                if len(result['files_created']) > 0:
                    csv_data = result['csv_data'][result['files_created'][0]]
                    if test_case['validator'](csv_data):
                        print(f"  ✅ {test_case['name']}")
                        passed += 1
                    else:
                        print(f"  ❌ {test_case['name']} → CSV validation failed")
                else:
                    print(f"  ❌ {test_case['name']} → No files created")
                    
            except Exception as e:
                print(f"  ❌ {test_case['name']} → Error: {e}")
        
        print(f"CSVFileGenerator: {passed}/{len(test_cases)} tests passed")
        return passed == len(test_cases)

def test_lorem_substitution():
    """Test {{lorem:...}} substitution in content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        text_gen = TextFileGenerator(temp_dir)
        
        test_cases = [
            ('{{lorem:3l}}', lambda x: len(x.split('\n')) == 3),
            ('{{lorem:2s}}', lambda x: x.count('.') == 2),
            ('{{lorem:1p}}', lambda x: len(x.split()) > 10),
            ('Header\n{{lorem:2l}}\nFooter', lambda x: 'Header' in x and 'Footer' in x),
        ]
        
        passed = 0
        print("\nTesting Lorem Substitution:")
        
        for template, validator in test_cases:
            try:
                result = text_gen._process_lorem_content(template)
                if validator(result):
                    print(f"  ✅ '{template}' → Valid substitution")
                    passed += 1
                else:
                    print(f"  ❌ '{template}' → Invalid result: {result[:50]}...")
            except Exception as e:
                print(f"  ❌ '{template}' → Error: {e}")
        
        print(f"Lorem Substitution: {passed}/{len(test_cases)} tests passed")
        return passed == len(test_cases)

def test_clutter_generation():
    """Test clutter file generation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        text_gen = TextFileGenerator(temp_dir)
        
        print("\nTesting Clutter Generation:")
        
        try:
            result = text_gen.generate(
                target_file="main/data.txt",
                content_spec={'type': 'lorem_lines', 'count': 3},
                clutter_spec={'count': 5}
            )
            
            # Should have main file + clutter files
            total_files = len(result['files_created'])
            if total_files >= 5:  # At least 5 files (1 main + clutter)
                print(f"  ✅ Generated {total_files} files (including clutter)")
                return True
            else:
                print(f"  ❌ Only generated {total_files} files, expected at least 5")
                return False
                
        except Exception as e:
            print(f"  ❌ Clutter generation failed: {e}")
            return False

def test_factory():
    """Test file generator factory."""
    print("\nTesting FileGeneratorFactory:")
    
    try:
        # Test valid generator types
        text_gen = FileGeneratorFactory.create_generator('create_files')
        csv_gen = FileGeneratorFactory.create_generator('create_csv')
        
        if isinstance(text_gen, TextFileGenerator) and isinstance(csv_gen, CSVFileGenerator):
            print("  ✅ Factory creates correct generator types")
            
            # Test invalid generator type
            try:
                FileGeneratorFactory.create_generator('invalid_type')
                print("  ❌ Factory should have raised error for invalid type")
                return False
            except FileGeneratorError:
                print("  ✅ Factory correctly handles invalid types")
                return True
        else:
            print("  ❌ Factory created wrong generator types")
            return False
            
    except Exception as e:
        print(f"  ❌ Factory test failed: {e}")
        return False

if __name__ == "__main__":
    try:
        test1 = test_lorem_generator()
        test2 = test_data_generator()
        test3 = test_text_file_generator()
        test4 = test_csv_file_generator()
        test5 = test_lorem_substitution()
        test6 = test_clutter_generation()
        test7 = test_factory()
        
        all_passed = all([test1, test2, test3, test4, test5, test6, test7])
        
        if all_passed:
            print("\n🎉 All Step 3 tests passed! File Generator Infrastructure is working correctly.")
        else:
            print("\n❌ Some Step 3 tests failed.")
            
    except Exception as e:
        print(f"❌ Step 3 test failed with error: {e}")
        import traceback
        traceback.print_exc()
