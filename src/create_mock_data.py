"""
Generate Mock LLM Responses for Testing

Creates a responses_TIMESTAMP.jsonl file with simple "Okie dokie" responses
and sets up one correct directory structure in test_artifacts for testing.
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent))


def create_mock_responses():
    """Create mock LLM responses from existing precheck file."""
    print("🤖 Creating Mock LLM Responses")
    print("=" * 40)
    
    # Find the most recent precheck file
    current_dir = Path(__file__).parent.parent
    results_dir = current_dir / "results"
    
    precheck_files = list(results_dir.glob("precheck_*.jsonl"))
    if not precheck_files:
        print("❌ No precheck files found! Run system_test.py first.")
        return None
    
    latest_precheck = sorted(precheck_files)[-1]
    print(f"📄 Using precheck file: {latest_precheck}")
    
    # Read precheck entries
    precheck_entries = []
    with open(latest_precheck, 'r', encoding='utf-8') as f:
        for line in f:
            precheck_entries.append(json.loads(line.strip()))
    
    print(f"📝 Found {len(precheck_entries)} precheck entries")
    
    # Create responses file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    responses_file = results_dir / f"responses_{timestamp}.jsonl"
    
    print(f"💾 Creating responses file: {responses_file}")
    
    with open(responses_file, 'w', encoding='utf-8') as f:
        for entry in precheck_entries:
            response = {
                "question_id": entry["question_id"],
                "sample_number": entry["sample_number"],
                "timestamp": datetime.now().isoformat(),
                "response_text": "Okie dokie",
                "execution_successful": True,
                "error_message": None
            }
            f.write(json.dumps(response) + '\n')
    
    print(f"✅ Created {len(precheck_entries)} mock responses")
    return responses_file, precheck_entries


def create_one_correct_directory_structure(precheck_entries):
    """Create exactly one correct directory structure in test_artifacts."""
    print("\n📁 Creating One Correct Directory Structure")
    print("=" * 45)
    
    # Find a directory structure entry
    dir_entry = None
    for entry in precheck_entries:
        if entry["scoring_type"] == "directory_structure":
            dir_entry = entry
            break
    
    if not dir_entry:
        print("❌ No directory structure entries found!")
        return
    
    print(f"🎯 Using Question {dir_entry['question_id']}, Sample {dir_entry['sample_number']}")
    print(f"   Entities: entity1={dir_entry.get('entity1')}, entity2={dir_entry.get('entity2')}, entity3={dir_entry.get('entity3')}, entity4={dir_entry.get('entity4')}")
    
    # Get the expected paths
    expected_paths = dir_entry["expected_paths"]
    print(f"📋 Creating paths: {expected_paths}")
    
    # Create the directory structure
    current_dir = Path(__file__).parent.parent
    test_artifacts_dir = current_dir / "test_artifacts"
    
    # Clean test_artifacts first (except .gitkeep)
    for item in test_artifacts_dir.iterdir():
        if item.name != ".gitkeep":
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                import shutil
                shutil.rmtree(item)
    
    print("🧹 Cleaned test_artifacts directory")
    
    # Create each path
    for path in expected_paths:
        full_path = test_artifacts_dir / path
        
        if path.endswith('/'):
            # It's a directory
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"📂 Created directory: {path}")
        else:
            # It's a file
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text("# This file was created by the mock setup\n")
            print(f"📄 Created file: {path}")
    
    print(f"✅ Successfully created directory structure for Question {dir_entry['question_id']}, Sample {dir_entry['sample_number']}")
    print(f"   This will be the ONLY correct answer when scoring!")
    
    return dir_entry


def show_test_artifacts_structure():
    """Show what's actually in test_artifacts now."""
    print("\n🗂️  Test Artifacts Directory Structure")
    print("=" * 40)
    
    current_dir = Path(__file__).parent.parent
    test_artifacts_dir = current_dir / "test_artifacts"
    
    def show_tree(directory, prefix=""):
        items = sorted(directory.iterdir())
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            
            if item.name == ".gitkeep":
                continue
                
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{item.name}{'/' if item.is_dir() else ''}")
            
            if item.is_dir():
                extension = "    " if is_last else "│   "
                show_tree(item, prefix + extension)
    
    if any(item.name != ".gitkeep" for item in test_artifacts_dir.iterdir()):
        show_tree(test_artifacts_dir)
    else:
        print("(Empty - only .gitkeep)")


def main():
    """Create mock responses and one correct directory structure."""
    try:
        # Create mock responses
        responses_file, precheck_entries = create_mock_responses()
        if not responses_file:
            return
        
        # Create one correct directory structure
        correct_entry = create_one_correct_directory_structure(precheck_entries)
        
        # Show what we created
        show_test_artifacts_structure()
        
        print(f"\n🎉 Mock Setup Complete!")
        print(f"📄 Responses file: {responses_file}")
        print(f"🏆 One correct answer: Question {correct_entry['question_id']}, Sample {correct_entry['sample_number']} (directory_structure)")
        print(f"📁 All other questions will score as incorrect (no files created)")
        print(f"\nReady for Phase 2: Scoring System! 🚀")
        
    except Exception as e:
        print(f"❌ Mock setup failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
