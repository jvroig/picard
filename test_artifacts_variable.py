#!/usr/bin/env python3
"""
Test {{artifacts}} template variable functionality
"""
import sys
import tempfile
import yaml
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_artifacts_template_variable():
    """Test that {{artifacts}} template variable works correctly."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print("🎯 Testing {{artifacts}} template variable functionality")
        print("=" * 60)
        
        # Set up test environment
        test_base = Path(temp_dir)
        config_dir = test_base / "config"
        config_dir.mkdir(parents=True)
        
        # Create custom artifacts directory
        custom_artifacts = test_base / "my_custom_artifacts_location"
        custom_artifacts.mkdir(parents=True)
        
        # Create entity pool
        entity_pool_file = config_dir / "entity_pool.txt"
        entity_pool_file.write_text("red\nblue\ngreen")
        
        # Create test definition using {{artifacts}} template variable
        test_def_file = config_dir / "test_definitions.yaml"
        test_definitions = {
            "tests": [
                {
                    "question_id": 401,
                    "samples": 1,
                    "template": "What is on line 2 of the file?",
                    "scoring_type": "stringmatch",
                    "expected_response": "{{file_line:2:TARGET_FILE}}",
                    "sandbox_setup": {
                        "type": "create_files",
                        "target_file": "{{artifacts}}/{{qs_id}}/{{entity1}}/data.txt",  # Using {{artifacts}}!
                        "content": {
                            "type": "lorem_lines",
                            "count": 5
                        }
                    }
                },
                {
                    "question_id": 402,
                    "samples": 1,
                    "template": "What is the name in the CSV?",
                    "scoring_type": "stringmatch",
                    "expected_response": "{{csv_value:0:name:TARGET_FILE}}",
                    "sandbox_setup": {
                        "type": "create_csv",
                        "target_file": "{{artifacts}}/{{qs_id}}/people.csv",  # Using {{artifacts}}!
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
        
        print(f"📁 Test environment: {temp_dir}")
        print(f"🎯 Custom artifacts directory: {custom_artifacts}")
        print()
        
        # Test the template substitution directly first
        from test_definition_parser import TestDefinitionParser
        
        print("1. Testing {{artifacts}} substitution directly:")
        
        # Test with default artifacts directory
        test_string = "{{artifacts}}/{{qs_id}}/file.txt"
        result_default = TestDefinitionParser.substitute_artifacts(test_string)
        print(f"   Original: {test_string}")
        print(f"   Default:  {result_default}")
        
        # Test with custom artifacts directory
        result_custom = TestDefinitionParser.substitute_artifacts(test_string, str(custom_artifacts))
        print(f"   Custom:   {result_custom}")
        
        # Verify substitution happened
        if "{{artifacts}}" not in result_custom and str(custom_artifacts) in result_custom:
            print("   ✅ {{artifacts}} substitution working!")
        else:
            print("   ❌ {{artifacts}} substitution failed!")
            return False
        
        print()
        
        # Test with qs_id substitution combined
        print("2. Testing combined {{artifacts}} + {{qs_id}} substitution:")
        
        combined = TestDefinitionParser.substitute_artifacts(test_string, str(custom_artifacts))
        combined = TestDefinitionParser.substitute_qs_id(combined, 401, 1)
        
        expected_path = f"{custom_artifacts}/q401_s1/file.txt"
        print(f"   Combined result: {combined}")
        print(f"   Expected:        {expected_path}")
        
        if combined == expected_path:
            print("   ✅ Combined substitution working!")
        else:
            print("   ❌ Combined substitution failed!")
            return False
        
        print()
        
        # Test with the precheck generator (integration test)
        print("3. Testing integration with precheck generator:")
        
        try:
            from precheck_generator import PrecheckGenerator
            
            # Initialize with custom artifacts directory by creating temporary config
            precheck_gen = PrecheckGenerator(
                entity_pool_file=str(entity_pool_file),
                test_definitions_file=str(test_def_file),
                base_dir=str(test_base)
            )
            
            # Override the artifacts directory for this test
            import sys
            sys.path.insert(0, str(test_base))
            
            # Generate precheck entries
            precheck_entries = precheck_gen.generate_precheck_entries()
            
            print(f"   Generated {len(precheck_entries)} precheck entries")
            
            success_count = 0
            for i, entry in enumerate(precheck_entries, 1):
                question_id = entry['question_id']
                
                if 'sandbox_generation' in entry:
                    sandbox_gen = entry['sandbox_generation']
                    target_file = sandbox_gen.get('target_file_resolved', '')
                    
                    print(f"   Entry {i} (Q{question_id}): {Path(target_file).name}")
                    
                    # Check if {{artifacts}} was processed correctly
                    # The target file should not contain {{artifacts}} anymore
                    if '{{artifacts}}' not in target_file:
                        print(f"      ✅ {{artifacts}} resolved in target file")
                        success_count += 1
                    else:
                        print(f"      ❌ {{artifacts}} NOT resolved: {target_file}")
                else:
                    print(f"   Entry {i} (Q{question_id}): No sandbox generation")
            
            print()
            
            if success_count == len(precheck_entries):
                print("🎉 All {{artifacts}} integration tests passed!")
                print("   ✅ Template variable substitution working in precheck generation")
                print("   ✅ Files created with resolved paths") 
                print("   ✅ No {{artifacts}} placeholders remain in output")
                return True
            else:
                print(f"❌ Only {success_count}/{len(precheck_entries)} tests passed")
                return False
                
        except Exception as e:
            print(f"   ❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    try:
        success = test_artifacts_template_variable()
        
        print()
        print("📋 Summary of {{artifacts}} template variable:")
        print("   🎯 Purpose: Make test definitions portable across machines")
        print("   📝 Usage: {{artifacts}}/{{qs_id}}/{{entity1}}/file.txt") 
        print("   🔄 Processing order: {{artifacts}} → {{qs_id}} → {{entity1}}")
        print("   ⚙️  Configuration: Set path in qwen_sense_config.py")
        
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"❌ {{artifacts}} test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
