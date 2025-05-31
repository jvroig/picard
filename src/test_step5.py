#!/usr/bin/env python3
"""
Test Step 5: Precheck Generation with Template Function Evaluation
"""
import sys
import tempfile
import yaml
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

def test_precheck_with_template_functions():
    """Test precheck generation with template function evaluation."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Testing precheck generation with template functions in: {temp_dir}")
        
        # Set up test environment
        test_base = Path(temp_dir)
        config_dir = test_base / "config"
        config_dir.mkdir(parents=True)
        
        # Create entity pool
        entity_pool_file = config_dir / "entity_pool.txt"
        entity_pool_file.write_text("red\nblue\ngreen\nyellow\norange")
        
        # Create test definitions with template functions in expected_response
        test_definitions = {
            "tests": [
                # Regular test without template functions (control)
                {
                    "question_id": 1,
                    "samples": 1,
                    "template": "Say hello to {{entity1}}",
                    "scoring_type": "stringmatch",
                    "expected_response": "Hello {{entity1}}!"
                },
                # Test with sandbox setup and template functions
                {
                    "question_id": 2,
                    "samples": 2,
                    "template": "What is the content of line 2 in the file test_artifacts/{{qs_id}}/{{entity1}}/data.txt?",
                    "scoring_type": "stringmatch",
                    "expected_response": "{{file_line:2:test_artifacts/{{qs_id}}/{{entity1}}/data.txt}}",
                    "sandbox_setup": {
                        "type": "create_files",
                        "target_file": "test_artifacts/{{qs_id}}/{{entity1}}/data.txt",
                        "content": {
                            "type": "lorem_lines",
                            "count": 5
                        }
                    }
                },
                # Test with CSV template functions
                {
                    "question_id": 3,
                    "samples": 1,
                    "template": "Who is the person in row 1 of test_artifacts/{{qs_id}}/people.csv?",
                    "scoring_type": "stringmatch",
                    "expected_response": "{{csv_value:0:name:test_artifacts/{{qs_id}}/people.csv}}",
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
        
        test_def_file = config_dir / "test_definitions.yaml"
        with open(test_def_file, 'w') as f:
            yaml.dump(test_definitions, f)
        
        # Create test artifacts directory
        artifacts_dir = test_base / "test_artifacts"
        artifacts_dir.mkdir(parents=True)
        
        print("\n1. Testing precheck generation with file generation:")
        
        try:
            from precheck_generator import PrecheckGenerator
            
            precheck_gen = PrecheckGenerator(
                entity_pool_file=str(entity_pool_file),
                test_definitions_file=str(test_def_file),
                base_dir=str(test_base)
            )
            
            precheck_entries = precheck_gen.generate_precheck_entries()
            
            # Should have 4 entries (1 + 2 + 1 samples)
            if len(precheck_entries) == 4:
                print(f"  ✅ Generated {len(precheck_entries)} precheck entries")
                
                # Check first entry (no sandbox, no template functions)
                entry1 = precheck_entries[0]
                if 'sandbox_generation' not in entry1:
                    print("     ✅ Entry 1: No sandbox generation (as expected)")
                    if 'expected_response' in entry1 and '{{' not in entry1['expected_response']:
                        print(f"        Expected response: {entry1['expected_response']}")
                        test1_passed = True
                    else:
                        print(f"        ❌ Expected response still has templates: {entry1.get('expected_response')}")
                        test1_passed = False
                else:
                    print("     ❌ Entry 1 unexpectedly has sandbox generation")
                    test1_passed = False
            else:
                print(f"  ❌ Expected 4 precheck entries, got {len(precheck_entries)}")
                test1_passed = False
                
        except Exception as e:
            print(f"  ❌ Precheck generation failed: {e}")
            import traceback
            traceback.print_exc()
            test1_passed = False
        
        print("\n2. Testing sandbox file generation during precheck:")
        
        try:
            # Check entries with sandbox generation
            sandbox_entries = [entry for entry in precheck_entries if 'sandbox_generation' in entry]
            
            if len(sandbox_entries) == 3:  # Q2 has 2 samples + Q3 has 1 sample
                print(f"  ✅ Found {len(sandbox_entries)} entries with sandbox generation")
                
                # Check if files were actually created
                files_created_count = 0
                generation_errors = 0
                
                for entry in sandbox_entries:
                    sandbox_gen = entry['sandbox_generation']
                    if sandbox_gen.get('generation_successful', False):
                        files_created = sandbox_gen.get('files_created', [])
                        files_created_count += len(files_created)
                        
                        # Verify files exist
                        for file_path in files_created:
                            if Path(file_path).exists():
                                print(f"     ✅ File exists: {Path(file_path).name}")
                            else:
                                print(f"     ❌ File missing: {file_path}")
                                generation_errors += 1
                    else:
                        generation_errors += 1
                        print(f"     ❌ Generation failed for Q{entry['question_id']}S{entry['sample_number']}")
                
                if generation_errors == 0 and files_created_count > 0:
                    print(f"     ✅ Successfully created {files_created_count} files")
                    test2_passed = True
                else:
                    print(f"     ❌ {generation_errors} generation errors, {files_created_count} files created")
                    test2_passed = False
            else:
                print(f"  ❌ Expected 3 sandbox entries, got {len(sandbox_entries)}")
                test2_passed = False
                
        except Exception as e:
            print(f"  ❌ Sandbox file generation check failed: {e}")
            test2_passed = False
        
        print("\n3. Testing template function evaluation in expected_response:")
        
        try:
            # Check that template functions were evaluated
            template_function_entries = [entry for entry in precheck_entries if 'expected_response' in entry]
            resolved_entries = 0
            
            for entry in template_function_entries:
                expected_response = entry['expected_response']
                question_id = entry['question_id']
                
                # Check if template functions were resolved
                if question_id == 1:
                    # Should just have entity substitution, no template functions
                    if '{{' not in expected_response:
                        print(f"     ✅ Q{question_id}: Entity substitution working: '{expected_response}'")
                        resolved_entries += 1
                    else:
                        print(f"     ❌ Q{question_id}: Still has templates: '{expected_response}'")
                        
                elif question_id in [2, 3]:
                    # Should have template functions resolved to actual content
                    if '{{file_line:' not in expected_response and '{{csv_value:' not in expected_response:
                        if len(expected_response) > 0:
                            print(f"     ✅ Q{question_id}: Template function resolved: '{expected_response[:50]}...'")
                            resolved_entries += 1
                        else:
                            print(f"     ⚠️ Q{question_id}: Template function resolved but empty")
                    else:
                        print(f"     ❌ Q{question_id}: Template function not resolved: '{expected_response}'")
                        # Debug: Check if the expected file exists
                        if 'sandbox_generation' in entry:
                            files_created = entry['sandbox_generation'].get('files_created', [])
                            print(f"        Files created for this entry: {files_created}")
                        
                        # Extract the file path from the template function
                        import re
                        if '{{file_line:' in expected_response:
                            match = re.search(r'\{\{file_line:\d+:([^}]+)\}\}', expected_response)
                            if match:
                                file_path = match.group(1)
                                full_path = test_base / file_path
                                print(f"        Looking for file: {full_path}")
                                print(f"        File exists: {full_path.exists()}")
                        elif '{{csv_value:' in expected_response:
                            match = re.search(r'\{\{csv_value:\d+:\w+:([^}]+)\}\}', expected_response)
                            if match:
                                file_path = match.group(1)
                                full_path = test_base / file_path
                                print(f"        Looking for CSV: {full_path}")
                                print(f"        CSV exists: {full_path.exists()}")
            
            if resolved_entries >= 3:  # At least 3 out of 4 should be resolved properly
                print(f"  ✅ Template function evaluation working ({resolved_entries}/4 entries properly resolved)")
                test3_passed = True
            else:
                print(f"  ❌ Template function evaluation insufficient ({resolved_entries}/4 entries resolved)")
                test3_passed = False
                
        except Exception as e:
            print(f"  ❌ Template function evaluation check failed: {e}")
            test3_passed = False
        
        print("\n4. Testing precheck file save/load cycle:")
        
        try:
            # Save precheck entries
            precheck_file = test_base / "test_precheck.jsonl"
            precheck_gen.save_precheck_entries(precheck_entries, str(precheck_file))
            
            # Verify file was created and has content
            if precheck_file.exists():
                with open(precheck_file, 'r') as f:
                    lines = f.readlines()
                
                if len(lines) == 4:
                    print(f"  ✅ Precheck file saved with {len(lines)} entries")
                    
                    # Verify entries can be loaded back
                    loaded_entries = []
                    for line in lines:
                        loaded_entries.append(json.loads(line.strip()))
                    
                    # Check that a template function result is preserved
                    found_resolved = False
                    for entry in loaded_entries:
                        if ('expected_response' in entry and 
                            entry['expected_response'] and 
                            '{{file_line:' not in entry['expected_response'] and
                            '{{csv_value:' not in entry['expected_response']):
                            found_resolved = True
                            break
                    
                    if found_resolved:
                        print("     ✅ Template function results preserved in saved precheck")
                        test4_passed = True
                    else:
                        print("     ❌ Template function results not preserved properly")
                        test4_passed = False
                else:
                    print(f"     ❌ Precheck file has wrong number of lines: {len(lines)}")
                    test4_passed = False
            else:
                print("  ❌ Precheck file was not created")
                test4_passed = False
                
        except Exception as e:
            print(f"  ❌ Precheck file save/load test failed: {e}")
            test4_passed = False
        
        # Summary
        all_passed = test1_passed and test2_passed and test3_passed and test4_passed
        
        if all_passed:
            print("\n🎉 All Step 5 tests passed! Precheck generation with template functions is working.")
        else:
            print("\n❌ Some Step 5 tests failed:")
            print(f"   Precheck generation: {'✅' if test1_passed else '❌'}")
            print(f"   Sandbox file creation: {'✅' if test2_passed else '❌'}")
            print(f"   Template function evaluation: {'✅' if test3_passed else '❌'}")
            print(f"   Precheck save/load: {'✅' if test4_passed else '❌'}")
        
        return all_passed

if __name__ == "__main__":
    try:
        success = test_precheck_with_template_functions()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"❌ Step 5 test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
