#!/usr/bin/env python3
"""
Test fix for template variable substitution in questions
"""
import sys
import tempfile
import yaml
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_question_substitution_fix():
    """Test that template variables are properly substituted in questions."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print("🔧 Testing template variable substitution fix")
        print("=" * 50)
        
        # Set up test environment
        test_base = Path(temp_dir)
        config_dir = test_base / "config"
        config_dir.mkdir(parents=True)
        
        # Create entity pool
        entity_pool_file = config_dir / "entity_pool.txt"
        entity_pool_file.write_text("bear\nwolf\neagle")
        
        # Create test definition with template variables in question
        test_def_file = config_dir / "test_definitions.yaml"
        test_definitions = {
            "tests": [
                {
                    "question_id": 6,
                    "samples": 1,
                    "template": "What is the name of the first person in {{artifacts}}/{{qs_id}}/{{entity1}}/people.csv?",
                    "scoring_type": "stringmatch",
                    "expected_response": "{{csv_value:0:name:TARGET_FILE}}",
                    "sandbox_setup": {
                        "type": "create_csv",
                        "target_file": "{{artifacts}}/{{qs_id}}/{{entity1}}/people.csv",
                        "content": {
                            "headers": ["name", "age", "city"],
                            "rows": 5
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
        
        print(f"📁 Test environment: {temp_dir}")
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
        
        # Check the first entry
        entry = precheck_entries[0]
        
        print("🔍 Analyzing precheck entry:")
        print(f"   Original template: {entry['template']}")
        print(f"   Substituted question: {entry['substituted_question']}")
        print()
        
        # Check if template variables were properly resolved
        substituted_question = entry['substituted_question']
        
        issues = []
        
        if '{{artifacts}}' in substituted_question:
            issues.append("{{artifacts}} not resolved in question")
        
        if '{{qs_id}}' in substituted_question:
            issues.append("{{qs_id}} not resolved in question")
        
        if '{{entity1}}' in substituted_question:
            issues.append("{{entity1}} not resolved in question")
        
        # Should contain actual values
        expected_patterns = [
            "test_artifacts",  # Should contain some artifacts directory
            "q6_s1",  # qs_id should be resolved
            entry['entity1']  # entity should be resolved
        ]
        
        for pattern in expected_patterns:
            if str(pattern) not in substituted_question:
                issues.append(f"Expected pattern '{pattern}' not found in question")
        
        if issues:
            print("❌ Template substitution issues found:")
            for issue in issues:
                print(f"   - {issue}")
            print()
            print(f"Expected something like: What is the name of the first person in [some_path]/test_artifacts/q6_s1/{entry['entity1']}/people.csv?")
            return False
        else:
            print("✅ All template variables properly resolved!")
            print("   ✅ {{artifacts}} resolved to actual path")
            print("   ✅ {{qs_id}} resolved to q6_s1")
            print(f"   ✅ {{{{entity1}}}} resolved to {entry['entity1']}")
            print()
            
            # Also check that sandbox generation worked
            if 'sandbox_generation' in entry:
                sandbox_gen = entry['sandbox_generation']
                if sandbox_gen.get('generation_successful', False):
                    target_file = sandbox_gen.get('target_file_resolved', '')
                    print(f"✅ Sandbox file created: {Path(target_file).name}")
                    
                    # Check that the file path in question matches the generated file path
                    if target_file in substituted_question:
                        print("✅ Question path matches generated file path")
                        return True
                    else:
                        print("❌ Question path does not match generated file path")
                        print(f"   Question contains: {substituted_question}")
                        print(f"   Generated file: {target_file}")
                        return False
                else:
                    print("❌ Sandbox generation failed")
                    return False
            else:
                print("❌ No sandbox generation found")
                return False

if __name__ == "__main__":
    try:
        success = test_question_substitution_fix()
        
        print()
        if success:
            print("🎉 Template variable substitution fix is working!")
            print("   ✅ LLM will now see fully resolved file paths")
            print("   ✅ No more {{artifacts}} or {{qs_id}} in questions")
        else:
            print("❌ Template variable substitution fix failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
