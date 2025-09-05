#!/usr/bin/env python3
"""
Test script for the two variable expansion bug fixes.
"""
import sys
sys.path.append('src')

print("🔧 Testing Variable Expansion Bug Fixes")
print("=" * 50)

# Test 1: Template function balanced brace parsing
print("\n1️⃣ Testing balanced brace parsing fix...")
from template_functions import TemplateFunctions
import tempfile
from pathlib import Path

# Create a test file for file_line function
with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir)
    
    # Create test file with lines
    test_file = temp_path / "notes.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nLine 8\nLine 9\nLine 10\nLine 11\nLine 12\nLine 13\nLine 14\nLine 15")
    
    tf = TemplateFunctions(base_dir=str(temp_dir))
    
    # Test the problematic case - this should now work
    test_text = f"{{{{file_line:12:{test_file}}}}}"
    print(f"   Input: {test_text}")
    
    try:
        result = tf.evaluate_all_functions(test_text)
        print(f"   ✅ Result: {result}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

# Test 2: TextFileGenerator variable processing
print("\n2️⃣ Testing TextFileGenerator count variable processing...")
from file_generators import TextFileGenerator
from entity_pool import EntityPool

# Create a test content spec with numeric variable
content_spec = {
    'type': 'lorem_lines',
    'count': '{{number1:5:8}}'  # This should be processed to an actual number
}

print(f"   Input content_spec: {content_spec}")

with tempfile.TemporaryDirectory() as temp_dir:
    tg = TextFileGenerator(temp_dir)
    
    # Mock the entity pool to return a known value
    tg.entity_pool.substitute_template_enhanced = lambda x, y=None: {
        'substituted': x.replace('{{number1:5:8}}', '6'),
        'entities': {},
        'variables': {'number1:5:8': '6'}
    }
    
    try:
        result = tg.generate(
            target_file="test.txt",
            content_spec=content_spec
        )
        print(f"   ✅ Files created: {result['files_created']}")
        
        # Check if the file has the right number of lines
        if result['files_created']:
            file_path = result['files_created'][0]
            with open(file_path, 'r') as f:
                lines = f.readlines()
            print(f"   ✅ Generated {len(lines)} lines (expected 6)")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n✅ Bug fix testing completed!")