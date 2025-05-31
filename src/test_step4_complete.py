#!/usr/bin/env python3
"""
Test Step 4: Complete End-to-End Integration Test
"""
import sys
import tempfile
import yaml
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

def test_complete_integration():
    """Test complete integration with a realistic test scenario."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Testing complete integration in: {temp_dir}")
        
        # Set up test environment
        test_base = Path(temp_dir)
        config_dir = test_base / "config"
        config_dir.mkdir(parents=True)
        
        # Create entity pool
        entity_pool_file = config_dir / "entity_pool.txt"
        entity_pool_file.write_text("red\nblue\ngreen\nyellow\norange\npurple")
        
        # Create realistic test definitions with sandbox setup
        test_definitions = {
            "tests": [
                # Test without sandbox setup (control)
                {
                    "question_id": 1,
                    "samples": 1,
                    "template": "Say hello to {{entity1}}",
                    "scoring_type": "stringmatch",
                    "expected_response": "Hello {{entity1}}!"
                },
                # Test with text file generation
                {
                    "question_id": 2,
                    "samples": 1,
                    "template": "Read the file test_artifacts/{{qs_id}}/data/{{entity1}}.txt and tell me the content of line 3.",
                    "scoring_type": "stringmatch",
                    "expected_response": "{{file_line:3:test_artifacts/{{qs_id}}/data/{{entity1}}.txt}}",
                    "sandbox_setup": {
                        "type": "create_files",
                        "target_file": "test_artifacts/{{qs_id}}/data/{{entity1}}.txt",
                        "content": {
                            "type": "lorem_lines",
                            "count": 5
                        },
                        "clutter": {
                            "count": 2
                        }
                    }
                }
            ]
        }
        
        test_def_file = config_dir / "test_definitions.yaml"
        with open(test_def_file, 'w') as f:
            yaml.dump(test_definitions, f)
        
        # Create test artifacts directory
        artifacts_dir = test_base / "test_artifacts"
        artifacts_dir.mkdir(parents=True)
        gitkeep = artifacts_dir / ".gitkeep"
        gitkeep.write_text("")
        
        # Create templates directory (needed for sandbox manager)
        templates_dir = test_base / "test_artifacts_templates"
        templates_dir.mkdir(parents=True)
        
        print("\n1. Testing precheck generation with mixed question types:")
        
        try:
            from precheck_generator import PrecheckGenerator
            
            precheck_gen = PrecheckGenerator(
                entity_pool_file=str(entity_pool_file),
                test_definitions_file=str(test_def_file)
            )
            
            precheck_entries = precheck_gen.generate_precheck_entries()
            
            # Should have 2 entries total (1 sample each)
            if len(precheck_entries) == 2:
                print(f"  ✅ Generated {len(precheck_entries)} precheck entries")
                
                # Check first entry (no sandbox)
                entry1 = precheck_entries[0]
                if 'sandbox_setup' not in entry1:
                    print("     ✅ Entry 1 has no sandbox setup (as expected)")
                else:
                    print("     ❌ Entry 1 unexpectedly has sandbox setup")
                    return False
                
                # Check second entry (with sandbox)
                entry2 = precheck_entries[1]
                if 'sandbox_setup' in entry2:
                    print("     ✅ Entry 2 has sandbox setup")
                    print(f"        Target file template: {entry2['sandbox_setup']['target_file']}")
                    test1_passed = True
                else:
                    print("     ❌ Entry 2 missing sandbox setup")
                    test1_passed = False
            else:
                print(f"  ❌ Expected 2 precheck entries, got {len(precheck_entries)}")
                test1_passed = False
                
        except Exception as e:
            print(f"  ❌ Precheck generation failed: {e}")
            import traceback
            traceback.print_exc()
            test1_passed = False
        
        print("\n2. Testing individual sandbox setup execution:")
        
        try:
            from test_runner import TestRunner
            
            test_runner = TestRunner(str(test_base))
            
            # Get the entry with sandbox setup
            sandbox_entry = precheck_entries[1]
            
            # Execute sandbox setup
            result = test_runner._setup_question_sandbox(sandbox_entry)
            
            if result['has_sandbox_setup']:
                print(f"  ✅ Sandbox setup executed successfully")
                print(f"     Files created: {len(result['files_created'])}")
                print(f"     Errors: {len(result['errors'])}")
                
                # Verify files exist and have content
                files_valid = True
                for file_path in result['files_created']:
                    file_obj = Path(file_path)
                    if file_obj.exists():
                        content = file_obj.read_text()
                        if len(content.strip()) > 0:
                            print(f"     ✅ File {file_obj.name} exists with content")
                        else:
                            print(f"     ❌ File {file_obj.name} exists but is empty")
                            files_valid = False
                    else:
                        print(f"     ❌ File {file_path} does not exist")
                        files_valid = False
                
                test2_passed = files_valid
            else:
                print("  ❌ Sandbox setup was not executed")
                test2_passed = False
                
        except Exception as e:
            print(f"  ❌ Sandbox setup execution failed: {e}")
            import traceback
            traceback.print_exc()
            test2_passed = False
        
        print("\n3. Testing template function integration:")
        
        try:
            from template_processor import TemplateProcessor
            
            processor = TemplateProcessor(base_dir=str(test_base))
            
            # Use the generated file to test template function
            if result['files_created']:
                target_file = result['files_created'][0]  # Main file should be first
                
                # Create a template that reads from the generated file
                template = f"The third line says: {{{{file_line:3:{target_file}}}}}"
                
                processed = processor.process_template(template, question_id=2, sample_number=1)
                
                if 'file_line:3:' in str(processed['template_function_results']):
                    print("  ✅ Template function integration working")
                    print(f"     Template: {template}")
                    print(f"     Result: {processed['substituted'][:100]}...")
                    test3_passed = True
                else:
                    print("  ❌ Template function not properly executed")
                    print(f"     Results: {processed}")
                    test3_passed = False
            else:
                print("  ❌ No files were generated to test template functions")
                test3_passed = False
                
        except Exception as e:
            print(f"  ❌ Template function integration failed: {e}")
            import traceback
            traceback.print_exc()
            test3_passed = False
        
        # Summary
        all_passed = test1_passed and test2_passed and test3_passed
        
        if all_passed:
            print("\n🎉 Complete Step 4 integration test passed!")
            print("   ✅ Precheck generation handles mixed question types")
            print("   ✅ Sandbox setup creates files dynamically")
            print("   ✅ Template functions work with generated files")
        else:
            print("\n❌ Step 4 integration test failed:")
            print(f"   Precheck generation: {'✅' if test1_passed else '❌'}")
            print(f"   Sandbox execution: {'✅' if test2_passed else '❌'}")
            print(f"   Template integration: {'✅' if test3_passed else '❌'}")
        
        return all_passed

if __name__ == "__main__":
    try:
        success = test_complete_integration()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"❌ Complete integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
