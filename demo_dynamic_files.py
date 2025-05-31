#!/usr/bin/env python3
"""
Example demonstrating QwenSense dynamic file generation
Run this to see how the new template function system works
"""
import sys
import tempfile
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from precheck_generator import PrecheckGenerator

def demonstrate_dynamic_file_generation():
    """Show how dynamic file generation works with a concrete example."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print("🎯 QwenSense Dynamic File Generation Demo")
        print("=" * 50)
        
        # Set up test environment
        test_base = Path(temp_dir)
        config_dir = test_base / "config"
        config_dir.mkdir(parents=True)
        
        # Create entity pool
        entity_pool_file = config_dir / "entity_pool.txt"
        entity_pool_file.write_text("red\nblue\ngreen\nyellow\norange\npurple")
        
        # Create a simple test definition directly
        test_def_file = config_dir / "test_definitions.yaml"
        test_definitions = {
            "tests": [
                {
                    "question_id": 101,
                    "samples": 2,
                    "template": "Please read the file test_artifacts/{{qs_id}}/{{entity1}}/notes.txt and tell me exactly what line 3 says.",
                    "scoring_type": "stringmatch",
                    "expected_response": "{{file_line:3:test_artifacts/{{qs_id}}/{{entity1}}/notes.txt}}",
                    "sandbox_setup": {
                        "type": "create_files",
                        "target_file": "test_artifacts/{{qs_id}}/{{entity1}}/notes.txt",
                        "content": {
                            "type": "lorem_lines",
                            "count": 7
                        },
                        "clutter": {
                            "count": 3
                        }
                    }
                },
                {
                    "question_id": 102,
                    "samples": 1,
                    "template": "Look at the CSV file test_artifacts/{{qs_id}}/employees.csv. What is the name of the person in the first data row?",
                    "scoring_type": "stringmatch",
                    "expected_response": "{{csv_value:0:name:test_artifacts/{{qs_id}}/employees.csv}}",
                    "sandbox_setup": {
                        "type": "create_csv",
                        "target_file": "test_artifacts/{{qs_id}}/employees.csv",
                        "content": {
                            "headers": ["name", "age", "department", "salary"],
                            "rows": 4
                        }
                    }
                },
                {
                    "question_id": 103,
                    "samples": 1,
                    "template": "Say hello to {{entity1}} in a friendly way.",
                    "scoring_type": "stringmatch",
                    "expected_response": "Hello {{entity1}}!"
                }
            ]
        }
        
        import yaml
        with open(test_def_file, 'w') as f:
            yaml.dump(test_definitions, f)
        
        # Create artifacts directory
        artifacts_dir = test_base / "test_artifacts"
        artifacts_dir.mkdir(parents=True)
        
        print(f"📁 Working directory: {temp_dir}")
        print()
        
        # Generate precheck entries
        print("🔄 Generating precheck entries with dynamic files...")
        
        precheck_gen = PrecheckGenerator(
            entity_pool_file=str(entity_pool_file),
            test_definitions_file=str(test_def_file),
            base_dir=str(test_base)
        )
        
        precheck_entries = precheck_gen.generate_precheck_entries()
        
        print(f"✅ Generated {len(precheck_entries)} precheck entries")
        print()
        
        # Show examples of what was generated
        for i, entry in enumerate(precheck_entries[:3], 1):  # Show first 3 examples
            question_id = entry['question_id']
            sample_number = entry['sample_number']
            
            print(f"📝 Example {i}: Question {question_id}, Sample {sample_number}")
            print(f"   Template: {entry['template']}")
            print(f"   Substituted Question: {entry['substituted_question']}")
            
            if 'sandbox_generation' in entry:
                sandbox_gen = entry['sandbox_generation']
                if sandbox_gen.get('generation_successful', False):
                    files_created = sandbox_gen.get('files_created', [])
                    print(f"   🎁 Generated Files: {len(files_created)}")
                    for file_path in files_created:
                        file_obj = Path(file_path)
                        if file_obj.exists():
                            print(f"      📄 {file_obj.name} ({file_obj.stat().st_size} bytes)")
                            # Show content preview for small files
                            if file_obj.suffix == '.txt' and file_obj.stat().st_size < 500:
                                content = file_obj.read_text()
                                lines = content.split('\n')[:3]
                                print(f"         Preview: {lines[0][:50]}...")
                            elif file_obj.suffix == '.csv':
                                content = file_obj.read_text()
                                lines = content.split('\n')[:2]
                                print(f"         Headers: {lines[0]}")
                                if len(lines) > 1:
                                    print(f"         Data: {lines[1]}")
                else:
                    print(f"   ❌ File generation failed: {sandbox_gen.get('errors', [])}")
            
            if 'expected_response' in entry:
                expected = entry['expected_response']
                if len(expected) > 100:
                    print(f"   🎯 Expected Response: {expected[:100]}...")
                else:
                    print(f"   🎯 Expected Response: {expected}")
                
                # Check if template functions were resolved
                if '{{file_line:' not in expected and '{{csv_value:' not in expected:
                    print("      ✅ Template functions successfully resolved!")
                else:
                    print("      ⚠️ Template functions still present")
            
            print()
        
        # Show the difference between questions with and without sandbox
        sandbox_questions = [e for e in precheck_entries if 'sandbox_generation' in e]
        regular_questions = [e for e in precheck_entries if 'sandbox_generation' not in e]
        
        print(f"📊 Summary:")
        print(f"   Total questions: {len(precheck_entries)}")
        print(f"   With dynamic files: {len(sandbox_questions)}")
        print(f"   Traditional questions: {len(regular_questions)}")
        
        if sandbox_questions:
            total_files = sum(len(e['sandbox_generation'].get('files_created', [])) 
                            for e in sandbox_questions)
            print(f"   Total files generated: {total_files}")
        
        print()
        
        # Save precheck for inspection
        precheck_file = test_base / "precheck.jsonl"
        precheck_gen.save_precheck_entries(precheck_entries, str(precheck_file))
        print(f"💾 Precheck saved to: {precheck_file}")
        
        # Show what a real test run would look like
        print()
        print("🚀 Simulated Test Execution:")
        print("   (In a real test run, the LLM would be given these questions)")
        print()
        
        for entry in precheck_entries[:2]:  # Show 2 examples
            question = entry['substituted_question']
            expected = entry.get('expected_response', 'N/A')
            
            print(f"   🤖 LLM Question: {question}")
            print(f"   ✅ Expected Answer: {expected}")
            print(f"   📋 Scoring: Compare LLM response to expected answer")
            print()
        
        print("🎉 Demo completed! The system:")
        print("   1. ✅ Generated random files with lorem ipsum content")
        print("   2. ✅ Resolved template functions to actual file content") 
        print("   3. ✅ Created deterministic expected answers")
        print("   4. ✅ Ready for LLM testing with anti-memorization protection")

if __name__ == "__main__":
    try:
        demonstrate_dynamic_file_generation()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
