#!/usr/bin/env python3
"""
Test Step 2: Template Function System Implementation
"""
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from template_functions import TemplateFunctions, TemplateFunctionError
from template_processor import TemplateProcessor

def test_template_functions():
    """Test individual template functions."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files
        text_file = temp_path / "test.txt"
        text_file.write_text("Line one\nLine two\nLine three here\nLine four\nLast line")
        
        csv_file = temp_path / "data.csv"
        csv_file.write_text("name,age,city\nJohn,25,Boston\nAlice,30,Seattle\nBob,35,Denver")
        
        tf = TemplateFunctions(temp_dir)
        
        # Test all file functions
        file_tests = [
            ("{{file_line:3:test.txt}}", "Line three here"),
            ("{{file_word:5:test.txt}}", "Line"),
            ("{{file_line_count:test.txt}}", "5"),
            ("{{file_word_count:test.txt}}", "11"),
        ]
        
        # Test all CSV functions
        csv_tests = [
            ("{{csv_cell:1:0:data.csv}}", "John"),
            ("{{csv_cell:2:2:data.csv}}", "Seattle"),
            ("{{csv_row:1:data.csv}}", "John,25,Boston"),
            ("{{csv_column:name:data.csv}}", "John,Alice,Bob"),
            ("{{csv_value:0:age:data.csv}}", "25"),
            ("{{csv_value:2:city:data.csv}}", "Denver"),
        ]
        
        all_tests = file_tests + csv_tests
        passed = 0
        
        print("Testing individual template functions:")
        for template, expected in all_tests:
            try:
                result = tf.evaluate_all_functions(template)
                if str(result) == expected:
                    print(f"  ✅ {template} → {result}")
                    passed += 1
                else:
                    print(f"  ❌ {template} → {result} (expected: {expected})")
            except Exception as e:
                print(f"  ❌ {template} → ERROR: {e}")
        
        print(f"\nTemplate Functions: {passed}/{len(all_tests)} tests passed")
        return passed == len(all_tests)

def test_template_processor_integration():
    """Test the full template processor integration."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test environment
        test_dir = temp_path / "q5_s2"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        data_file = test_dir / "data.txt"
        data_file.write_text("First\nSecond\nThird content\nFourth")
        
        csv_file = test_dir / "info.csv"
        csv_file.write_text("product,price,stock\nWidget,99.99,50\nGadget,149.99,25")
        
        processor = TemplateProcessor(base_dir=temp_dir)
        
        # Test integrated processing
        test_cases = [
            {
                'template': 'Read {{qs_id}}/data.txt line {{file_line:3:{{qs_id}}/data.txt}}',
                'should_contain': ['q5_s2', 'Third content'],
                'description': 'qs_id + file_line integration'
            },
            {
                'template': 'Product {{entity1}} costs {{csv_value:0:price:{{qs_id}}/info.csv}}',
                'should_contain': ['99.99'],  # Just check for the price, entity names are random
                'description': 'entity + qs_id + csv_value integration'
            },
            {
                'template': 'File has {{file_line_count:{{qs_id}}/data.txt}} lines total',
                'should_contain': ['4 lines'],
                'description': 'qs_id + file_line_count integration'
            }
        ]
        
        passed = 0
        print("\nTesting template processor integration:")
        
        for test_case in test_cases:
            try:
                result = processor.process_template(test_case['template'], question_id=5, sample_number=2)
                output = result['substituted']
                
                # Check if all required content is present
                all_present = all(content in output for content in test_case['should_contain'])
                
                if all_present:
                    print(f"  ✅ {test_case['description']}")
                    print(f"     {test_case['template']} → {output}")
                    passed += 1
                else:
                    print(f"  ❌ {test_case['description']}")
                    print(f"     Expected content: {test_case['should_contain']}")
                    print(f"     Got: {output}")
                    
            except Exception as e:
                print(f"  ❌ {test_case['description']} → ERROR: {e}")
        
        print(f"\nIntegration Tests: {passed}/{len(test_cases)} tests passed")
        return passed == len(test_cases)

def test_error_handling():
    """Test error handling for invalid template functions."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        tf = TemplateFunctions(temp_dir)
        
        error_tests = [
            "{{file_line:999:nonexistent.txt}}",  # File doesn't exist
            "{{csv_cell:0:999:nonexistent.csv}}",  # File doesn't exist
            "{{unknown_function:arg1:arg2}}",  # Unknown function
            "{{file_line:invalid:test.txt}}",  # Invalid line number
        ]
        
        passed = 0
        print("\nTesting error handling:")
        
        for template in error_tests:
            try:
                result = tf.evaluate_all_functions(template)
                print(f"  ❌ {template} → Should have failed but got: {result}")
            except TemplateFunctionError:
                print(f"  ✅ {template} → Correctly raised TemplateFunctionError")
                passed += 1
            except Exception as e:
                print(f"  ❌ {template} → Wrong exception type: {e}")
        
        print(f"\nError Handling: {passed}/{len(error_tests)} tests passed")
        return passed == len(error_tests)

if __name__ == "__main__":
    try:
        test1 = test_template_functions()
        test2 = test_template_processor_integration()
        test3 = test_error_handling()
        
        if test1 and test2 and test3:
            print("\n🎉 All Step 2 tests passed! Template Function System is working correctly.")
        else:
            print("\n❌ Some Step 2 tests failed.")
            
    except Exception as e:
        print(f"❌ Step 2 test failed with error: {e}")
        import traceback
        traceback.print_exc()
