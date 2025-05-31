#!/usr/bin/env python3
"""
Test the extended TestDefinitionParser with sandbox_setup support
"""
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from test_definition_parser import TestDefinitionParser, SandboxSetup

def test_sandbox_setup_parsing():
    """Test parsing YAML with sandbox_setup."""
    
    test_yaml = """
tests:
  - question_id: 5
    samples: 3
    template: "Read the file test_artifacts/{{qs_id}}/{{entity1}}/data.txt and tell me what's on line 3, verbatim."
    scoring_type: "stringmatch"
    expected_response: "{{file_line:3:test_artifacts/{{qs_id}}/{{entity1}}/data.txt}}"
    sandbox_setup:
      type: "create_files"
      target_file: "test_artifacts/{{qs_id}}/{{entity1}}/data.txt"
      content:
        type: "lorem_lines"
        count: 10
      clutter:
        count: 5
        pattern: "test_artifacts/{{qs_id}}/{{entity1}}/**/*.{txt,log}"
"""
    
    parser = TestDefinitionParser()
    test_defs = parser.parse_yaml_string(test_yaml)
    
    assert len(test_defs) == 1
    test_def = test_defs[0]
    
    # Check basic properties
    assert test_def.question_id == 5
    assert test_def.samples == 3
    assert test_def.scoring_type == "stringmatch"
    
    # Check sandbox_setup
    assert test_def.sandbox_setup is not None
    assert test_def.sandbox_setup.type == "create_files"
    assert test_def.sandbox_setup.target_file == "test_artifacts/{{qs_id}}/{{entity1}}/data.txt"
    assert test_def.sandbox_setup.content["type"] == "lorem_lines"
    assert test_def.sandbox_setup.content["count"] == 10
    assert test_def.sandbox_setup.clutter["count"] == 5
    
    print("✅ Sandbox setup parsing works correctly!")

def test_qs_id_substitution():
    """Test {{qs_id}} substitution."""
    
    test_cases = [
        ("test_artifacts/{{qs_id}}/data.txt", 5, 2, "test_artifacts/q5_s2/data.txt"),
        ("{{qs_id}}_backup.log", 1, 10, "q1_s10_backup.log"),
        ("no substitution needed", 3, 4, "no substitution needed"),
        ("", 1, 1, ""),
        (None, 1, 1, None)
    ]
    
    for input_text, question_id, sample_number, expected in test_cases:
        result = TestDefinitionParser.substitute_qs_id(input_text, question_id, sample_number)
        assert result == expected, f"Expected {expected}, got {result}"
    
    print("✅ {{qs_id}} substitution works correctly!")

def test_to_dict_with_sandbox():
    """Test dictionary conversion includes sandbox_setup."""
    
    test_yaml = """
tests:
  - question_id: 5
    samples: 3
    template: "Read file"
    scoring_type: "stringmatch"
    expected_response: "test"
    sandbox_setup:
      type: "create_files"
      target_file: "test.txt"
      content:
        type: "lorem_lines"
        count: 5
"""
    
    parser = TestDefinitionParser()
    test_defs = parser.parse_yaml_string(test_yaml)
    test_dict = test_defs[0].to_dict()
    
    assert "sandbox_setup" in test_dict
    assert test_dict["sandbox_setup"]["type"] == "create_files"
    assert test_dict["sandbox_setup"]["target_file"] == "test.txt"
    assert test_dict["sandbox_setup"]["content"]["type"] == "lorem_lines"
    
    print("✅ Dictionary conversion includes sandbox_setup!")

if __name__ == "__main__":
    try:
        test_sandbox_setup_parsing()
        test_qs_id_substitution()
        test_to_dict_with_sandbox()
        print("\n🎉 All tests passed! Step 1 implementation is working.")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
