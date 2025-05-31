#!/usr/bin/env python3
"""
Test Step 4: Sandbox Setup Integration into Test Runner
"""
import sys
import tempfile
import json
import yaml
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from test_runner import TestRunner
from test_definition_parser import TestDefinitionParser

def test_sandbox_integration():
    """Test end-to-end sandbox integration."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Testing sandbox integration in: {temp_dir}")
        
        # Create test environment
        test_base = Path(temp_dir)
        config_dir = test_base / "config"
        config_dir.mkdir(parents=True)
        
        # Create entity pool
        entity_pool_file = config_dir / "entity_pool.txt"
        entity_pool_file.write_text("red\nblue\ngreen\nyellow\norange")
        
        # Create test definitions with sandbox setup
        test_definitions = {
            "tests": [
                {
                    "question_id": 1,
                    "samples": 2,
                    "template": "Read line 2 from file test_artifacts/{{qs_id}}/{{entity1}}/data.txt and tell me what it says.",
                    "scoring_type": "stringmatch",
                    "expected_response": "{{file_line:2:test_artifacts/{{qs_id}}/{{entity1}}/data.txt}}",
                    "sandbox_setup": {
                        "type": "create_files",
                        "target_file": "test_artifacts/{{qs_id}}/{{entity1}}/data.txt",
                        "content": {
                            "type": "lorem_lines",
                            "count": 5
                        },
                        "clutter": {
                            "count": 3
                        }
                    }
                },
                {
                    "question_id": 2,
                    "samples": 1,
                    "template": "What is the name in row 1 of test_artifacts/{{qs_id}}/people.csv?",
                    "scoring_type": "stringmatch", 
                    "expected_response": "{{csv_value:0:name:test_artifacts/{{qs_id}}/people.csv}}",
                    "sandbox_setup": {
                        "type": "create_files",
                        "target_file": "test_artifacts/{{qs_id}}/people.csv",
                        "content": {
                            "type": "csv",
                            "headers": ["name", "age", "city"],
                            "rows": 3
                        }
                    }
                }
            ]
        }
        
        test_def_file = config_dir / "test_definitions.yaml"
        with open(test_def_file, 'w') as f:
            yaml.dump(test_definitions, f)
        
        # Create test artifacts directory structure
        artifacts_dir = test_base / "test_artifacts"
        artifacts_dir.mkdir(parents=True)
        gitkeep = artifacts_dir / ".gitkeep"
        gitkeep.write_text("")
        
        # Create template zip
        templates_dir = test_base / "test_artifacts_templates"
        templates_dir.mkdir(parents=True)
        
        print("\n1. Testing test definition parsing with sandbox_setup:")
        
        try:
            parser = TestDefinitionParser()
            test_defs = parser.parse_file(str(test_def_file))
            
            # Check that sandbox_setup was parsed
            sandbox_questions = [td for td in test_defs if td.sandbox_setup is not None]
            if len(sandbox_questions) == 2:
                print("  ✅ Test definitions with sandbox_setup parsed correctly")
                print(f"     Question 1 sandbox type: {sandbox_questions[0].sandbox_setup.type}")
                print(f"     Question 2 sandbox type: {sandbox_questions[1].sandbox_setup.type}")
                test1_passed = True
            else:
                print(f"  ❌ Expected 2 questions with sandbox_setup, got {len(sandbox_questions)}")
                test1_passed = False
                
        except Exception as e:
            print(f"  ❌ Test definition parsing failed: {e}")
            test1_passed = False
        
        print("\n2. Testing precheck generation with sandbox_setup:")
        
        try:
            from precheck_generator import PrecheckGenerator
            
            precheck_gen = PrecheckGenerator(
                entity_pool_file=str(entity_pool_file),
                test_definitions_file=str(test_def_file)
            )
            
            precheck_entries = precheck_gen.generate_precheck_entries()
            
            # Check that sandbox_setup info is in precheck entries
            sandbox_entries = [entry for entry in precheck_entries if 'sandbox_setup' in entry]
            if len(sandbox_entries) == 3:  # 2 + 1 samples = 3 total entries
                print(f"  ✅ Generated {len(sandbox_entries)} precheck entries with sandbox_setup")
                
                # Check specific fields
                first_entry = sandbox_entries[0]
                if 'target_file' in first_entry['sandbox_setup']:
                    print("     Sandbox setup includes target_file")
                    test2_passed = True
                else:
                    print("     ❌ Sandbox setup missing target_file")
                    test2_passed = False
            else:
                print(f"  ❌ Expected 3 precheck entries with sandbox_setup, got {len(sandbox_entries)}")
                test2_passed = False
                
        except Exception as e:
            print(f"  ❌ Precheck generation failed: {e}")
            test2_passed = False
        
        print("\n3. Testing TestRunner sandbox method:")
        
        try:
            # Initialize test runner
            test_runner = TestRunner(str(test_base))
            
            # Create a sample precheck entry with sandbox setup
            sample_entry = {
                'question_id': 1,
                'sample_number': 1,
                'entity1': 'blue',
                'sandbox_setup': {
                    'type': 'create_files',
                    'target_file': 'test_artifacts/{{qs_id}}/{{entity1}}/test.txt',
                    'content': {'type': 'lorem_lines', 'count': 3}
                }
            }
            
            # Test sandbox setup method
            result = test_runner._setup_question_sandbox(sample_entry)
            
            if result['has_sandbox_setup'] and len(result['files_created']) > 0:
                print(f"  ✅ Sandbox setup created {len(result['files_created'])} files")
                print(f"     Files created: {result['files_created']}")
                
                # Check if file actually exists and has content
                target_file = Path(temp_dir) / "test_artifacts" / "q1_s1" / "blue" / "test.txt"
                print(f"     Looking for file at: {target_file}")
                
                # Also check the actual created file
                if result['files_created']:
                    actual_file = Path(result['files_created'][0])
                    print(f"     Actual file created: {actual_file}")
                    if actual_file.exists():
                        content = actual_file.read_text()
                        if len(content.split('\n')) >= 3:
                            print("     ✅ Generated file has expected content structure")
                            test3_passed = True
                        else:
                            print(f"     ❌ Generated file has wrong content: {content[:50]}")
                            test3_passed = False
                    else:
                        print(f"     ❌ Actual file does not exist: {actual_file}")
                        test3_passed = False
                else:
                    test3_passed = False
            else:
                print("  ❌ Sandbox setup did not create expected files")
                test3_passed = False
                
        except Exception as e:
            print(f"  ❌ TestRunner sandbox method failed: {e}")
            import traceback
            traceback.print_exc()
            test3_passed = False
        
        # Summary
        all_passed = test1_passed and test2_passed and test3_passed
        
        if all_passed:
            print("\n🎉 All Step 4 tests passed! Sandbox setup integration is working.")
        else:
            print("\n❌ Some Step 4 tests failed.")
            print(f"   Test 1 (parsing): {'✅' if test1_passed else '❌'}")
            print(f"   Test 2 (precheck): {'✅' if test2_passed else '❌'}")
            print(f"   Test 3 (runner): {'✅' if test3_passed else '❌'}")
        
        return all_passed

if __name__ == "__main__":
    try:
        success = test_sandbox_integration()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"❌ Step 4 test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
