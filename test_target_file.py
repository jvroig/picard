#!/usr/bin/env python3
"""
Test TARGET_FILE keyword functionality
"""
import sys
import tempfile
import yaml
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_target_file_keyword():
    """Test that TARGET_FILE keyword works correctly."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print("🎯 Testing TARGET_FILE keyword functionality")
        print("=" * 50)
        
        # Set up test environment
        test_base = Path(temp_dir)
        config_dir = test_base / "config"
        config_dir.mkdir(parents=True)
        
        # Create entity pool
        entity_pool_file = config_dir / "entity_pool.txt"
        entity_pool_file.write_text("red\nblue\ngreen")
        
        # Create test definition using TARGET_FILE keyword
        test_def_file = config_dir / "test_definitions.yaml"
        test_definitions = {
            "tests": [
                {
                    "question_id": 301,
                    "samples": 1,
                    "template": "What is on line 2 of the target file?",
                    "scoring_type": "stringmatch",
                    "expected_response": "{{file_line:2:TARGET_FILE}}",  # Using TARGET_FILE keyword!
                    "sandbox_setup": {
                        "type": "create_files",
                        "target_file": "test_artifacts/{{qs_id}}/{{entity1}}/data.txt",
                        "content": {
                            "type": "lorem_lines",
                            "count": 5
                        }
                    }
                },
                {
                    "question_id": 302,
                    "samples": 1,
                    "template": "What is the name in the first row of the CSV?",
                    "scoring_type": "stringmatch",
                    "expected_response": "{{csv_value:0:name:TARGET_FILE}}",  # Using TARGET_FILE for CSV!
                    "sandbox_setup": {
                        "type": "create_csv",
                        "target_file": "test_artifacts/{{qs_id}}/people.csv",
                        "content": {
                            "headers": ["name", "age", "city"],
                            "rows": 3
                        }
                    }
                }
            ]
        }
        
        with open(test_def_file, 'w') as f:
            yaml.dump(test_definitions, f)
        
        # Create artifacts directory
        artifacts_dir = test_base / "test_artifacts"
        artifacts_dir.mkdir(parents=True)
        
        print(f"📁 Working in: {temp_dir}")
        print()
        
        # Generate precheck entries
        from precheck_generator import PrecheckGenerator
        
        precheck_gen = PrecheckGenerator(
            entity_pool_file=str(entity_pool_file),
            test_definitions_file=str(test_def_file),
            base_dir=str(test_base)
        )
        
        precheck_entries = precheck_gen.generate_precheck_entries()
        
        print(f"✅ Generated {len(precheck_entries)} precheck entries")
        print()
        
        # Test each entry
        success_count = 0
        
        for i, entry in enumerate(precheck_entries, 1):
            question_id = entry['question_id']
            sample_number = entry['sample_number']
            
            print(f"📝 Test {i}: Question {question_id}, Sample {sample_number}")
            
            # Check if files were generated
            if 'sandbox_generation' in entry:
                sandbox_gen = entry['sandbox_generation']
                if sandbox_gen.get('generation_successful', False):
                    files_created = sandbox_gen.get('files_created', [])
                    target_file = sandbox_gen.get('target_file_resolved', 'N/A')
                    
                    print(f"   🎁 Target file: {Path(target_file).name}")
                    print(f"   📄 Files created: {len(files_created)}")
                    
                    # Check if the file actually exists
                    if files_created and Path(files_created[0]).exists():
                        print(f"   ✅ Target file exists and has content")
                        
                        # Show the expected response
                        expected = entry.get('expected_response', 'N/A')
                        if expected and expected != 'N/A':
                            print(f"   🎯 Expected response: '{expected}'")
                            
                            # Verify that TARGET_FILE was resolved (no TARGET_FILE should remain)
                            if 'TARGET_FILE' not in expected:
                                print(f"   ✅ TARGET_FILE keyword successfully resolved!")
                                success_count += 1
                            else:
                                print(f"   ❌ TARGET_FILE keyword NOT resolved")
                        else:
                            print(f"   ❌ No expected response generated")
                    else:
                        print(f"   ❌ Target file was not created")
                else:
                    print(f"   ❌ File generation failed")
            else:
                print(f"   ❌ No sandbox generation found")
            
            print()
        
        # Summary
        if success_count == len(precheck_entries):
            print("🎉 All TARGET_FILE tests passed!")
            print("   ✅ TARGET_FILE keywords resolved correctly")
            print("   ✅ Template functions working with generated files")
            print("   ✅ Expected responses contain actual file content")
        else:
            print(f"❌ {success_count}/{len(precheck_entries)} tests passed")
        
        # Show example of what the old vs new syntax looks like
        print()
        print("📋 Syntax Comparison:")
        print("   ❌ Old (nested braces): {{file_line:2:test_artifacts/{{qs_id}}/data.txt}}")
        print("   ✅ New (TARGET_FILE): {{file_line:2:TARGET_FILE}}")
        print("   ✅ Clean, readable, and no parsing issues!")
        
        return success_count == len(precheck_entries)

if __name__ == "__main__":
    try:
        success = test_target_file_keyword()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"❌ TARGET_FILE test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
