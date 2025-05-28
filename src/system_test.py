"""
QwenSense System Test - Generate Precheck Files and Show Entity Substitutions

This script demonstrates the full Phase 1 system by:
1. Loading test definitions and entity pool
2. Generating actual precheck files with random entity substitutions
3. Showing detailed view of what's happening behind the scenes
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent))

from entity_pool import EntityPool
from test_definition_parser import TestDefinitionParser


def generate_precheck_files():
    """Generate actual precheck files and show the process."""
    print("🚀 QwenSense System Test - Precheck File Generation")
    print("=" * 60)
    
    # Initialize components
    pool = EntityPool()
    parser = TestDefinitionParser()
    
    # Load test definitions
    current_dir = Path(__file__).parent.parent
    test_file = current_dir / "config" / "test_definitions.yaml"
    test_definitions = parser.parse_file(test_file)
    
    print(f"📚 Loaded {pool.count_entities()} entities from entity pool")
    print(f"📋 Loaded {len(test_definitions)} test definitions")
    print()
    
    # Create timestamp for this test run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = current_dir / "results"
    results_dir.mkdir(exist_ok=True)
    
    precheck_file = results_dir / f"precheck_{timestamp}.jsonl"
    
    print(f"📁 Writing precheck file to: {precheck_file}")
    print()
    
    # Generate precheck entries for each test definition
    total_samples = 0
    
    with open(precheck_file, 'w', encoding='utf-8') as f:
        for test_def in test_definitions:
            print(f"🎯 Processing Question {test_def.question_id} ({test_def.scoring_type})")
            print(f"   Template: {test_def.template}")
            print(f"   Generating {test_def.samples} samples...")
            print()
            
            for sample_num in range(1, test_def.samples + 1):
                # Generate random entities for this sample
                result = pool.substitute_template(test_def.template, test_def.expected_structure)
                
                # Build precheck entry
                precheck_entry = {
                    'scoring_type': test_def.scoring_type,
                    'question_id': test_def.question_id,
                    'sample_number': sample_num,
                    'template': test_def.template,
                    'substituted_question': result['substituted'],
                    **result['entities']  # Add all entity mappings
                }
                
                # Add scoring-specific properties
                if test_def.file_to_read:
                    substituted_file = pool.substitute_with_entities(test_def.file_to_read, result['entities'])
                    precheck_entry['file_to_read'] = substituted_file
                    precheck_entry['expected_content'] = pool.substitute_with_entities(
                        f"Hello {result['entities'].get('entity1', '')}" if 'entity1' in result['entities'] else "Hello!", 
                        result['entities']
                    )
                
                if test_def.files_to_check:
                    substituted_files = [
                        pool.substitute_with_entities(file_path, result['entities'])
                        for file_path in test_def.files_to_check
                    ]
                    precheck_entry['files_to_check'] = substituted_files
                
                if test_def.expected_structure:
                    substituted_structure = [
                        pool.substitute_with_entities(path, result['entities'])
                        for path in test_def.expected_structure
                    ]
                    precheck_entry['expected_paths'] = substituted_structure
                
                if test_def.expected_response:
                    substituted_response = pool.substitute_with_entities(test_def.expected_response, result['entities'])
                    precheck_entry['expected_response'] = substituted_response
                
                # Write to file
                f.write(json.dumps(precheck_entry) + '\n')
                
                # Show first few samples in detail
                if sample_num <= 3:
                    print(f"   📝 Sample {sample_num}:")
                    print(f"      Entities: {result['entities']}")
                    print(f"      Question: {result['substituted'][:100]}{'...' if len(result['substituted']) > 100 else ''}")
                    
                    if test_def.scoring_type == "readfile_stringmatch":
                        print(f"      Expected file: {precheck_entry['file_to_read']}")
                        print(f"      Expected content: {precheck_entry['expected_content']}")
                    elif test_def.scoring_type == "files_exist":
                        print(f"      Files to check: {precheck_entry['files_to_check']}")
                    elif test_def.scoring_type == "directory_structure":
                        print(f"      Expected paths: {precheck_entry['expected_paths']}")
                    elif test_def.scoring_type == "stringmatch":
                        print(f"      Expected response: {precheck_entry['expected_response']}")
                    print()
                
                total_samples += 1
            
            if test_def.samples > 3:
                print(f"   ... and {test_def.samples - 3} more samples")
            print(f"   ✅ Completed {test_def.samples} samples for Question {test_def.question_id}")
            print()
    
    print(f"🎉 Successfully generated {total_samples} total samples!")
    print(f"📄 Precheck file written to: {precheck_file}")
    return precheck_file


def analyze_precheck_file(precheck_file):
    """Analyze the generated precheck file and show statistics."""
    print("\n" + "=" * 60)
    print("📊 PRECHECK FILE ANALYSIS")
    print("=" * 60)
    
    entries = []
    with open(precheck_file, 'r', encoding='utf-8') as f:
        for line in f:
            entries.append(json.loads(line.strip()))
    
    print(f"📁 File: {precheck_file}")
    print(f"📝 Total entries: {len(entries)}")
    print()
    
    # Group by question
    by_question = {}
    entity_usage = {}
    
    for entry in entries:
        qid = entry['question_id']
        if qid not in by_question:
            by_question[qid] = []
        by_question[qid].append(entry)
        
        # Track entity usage
        for key, value in entry.items():
            if key.startswith('entity'):
                if value not in entity_usage:
                    entity_usage[value] = 0
                entity_usage[value] += 1
    
    # Show question breakdown
    print("📋 Questions breakdown:")
    for qid in sorted(by_question.keys()):
        question_entries = by_question[qid]
        scoring_type = question_entries[0]['scoring_type']
        print(f"   Question {qid} ({scoring_type}): {len(question_entries)} samples")
    print()
    
    # Show most/least used entities
    sorted_entities = sorted(entity_usage.items(), key=lambda x: x[1], reverse=True)
    print("🎲 Entity usage statistics:")
    print(f"   Most used: {sorted_entities[0][0]} ({sorted_entities[0][1]} times)")
    print(f"   Least used: {sorted_entities[-1][0]} ({sorted_entities[-1][1]} times)")
    print(f"   Unique entities used: {len(entity_usage)} out of {EntityPool().count_entities()}")
    print()
    
    # Show sample entries
    print("📄 Sample precheck entries:")
    for qid in sorted(by_question.keys())[:2]:  # Show first 2 questions
        entry = by_question[qid][0]  # First sample
        print(f"   Question {qid} Sample 1:")
        print(f"   {json.dumps(entry, indent=6)}")
        print()


def show_entity_substitution_details():
    """Show detailed view of entity substitution process."""
    print("\n" + "=" * 60)
    print("🔍 ENTITY SUBSTITUTION DEEP DIVE")
    print("=" * 60)
    
    pool = EntityPool()
    
    # Test different templates
    test_templates = [
        "Write 'Hello {{entity1}}!' in {{entity2}}.txt",
        "Create files: {{entity1}}.log and {{entity2}}.config",
        "What is the capital of {{entity1}}?",
        "Create this directory structure: {{expected_structure}}"
    ]
    
    expected_structure = [
        "{{entity1}}/",
        "{{entity1}}/{{entity2}}/", 
        "{{entity1}}/logs/{{entity3}}.log",
        "{{entity4}}/README.md"
    ]
    
    for i, template in enumerate(test_templates, 1):
        print(f"🧪 Test {i}: Template Analysis")
        print(f"   Original: {template}")
        
        # Show what entities are found
        import re
        entity_pattern = r'\{\{(entity\d+)\}\}'
        found_entities = re.findall(entity_pattern, template)
        print(f"   Found entities: {found_entities}")
        
        # Generate substitution
        if i == 4:  # Directory structure
            result = pool.substitute_template(template, expected_structure)
            print(f"   Directory paths: {expected_structure}")
        else:
            result = pool.substitute_template(template)
        
        print(f"   Random values: {result['entities']}")
        print(f"   Final result: {result['substituted']}")
        print()


def main():
    """Run the complete system test."""
    try:
        # Generate precheck files
        precheck_file = generate_precheck_files()
        
        # Analyze the generated file
        analyze_precheck_file(precheck_file)
        
        # Show detailed substitution process
        show_entity_substitution_details()
        
        print("✅ System test completed successfully!")
        print(f"\nTo view your precheck file: cat {precheck_file}")
        print(f"To view formatted JSON: cat {precheck_file} | jq .")
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
