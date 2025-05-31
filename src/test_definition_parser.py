"""
Test Definition Parser for QwenSense LLM Benchmarking Tool

Handles loading and parsing of YAML test definitions into internal format.
"""
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SandboxSetup:
    """Represents sandbox setup configuration for dynamic file/database generation."""
    type: str  # "create_files", "create_database", etc.
    target_file: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    clutter: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate sandbox setup configuration."""
        if self.type == "create_files":
            if not self.target_file:
                raise ValueError("'target_file' required for sandbox_setup type 'create_files'")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'type': self.type,
            'target_file': self.target_file,
            'content': self.content,
            'clutter': self.clutter
        }


@dataclass
class TestDefinition:
    """Represents a single test question definition."""
    question_id: int
    samples: int
    template: str
    scoring_type: str
    
    # Optional properties based on scoring type
    file_to_read: Optional[str] = None
    expected_content: Optional[str] = None
    files_to_check: Optional[List[str]] = None
    expected_structure: Optional[List[str]] = None
    expected_response: Optional[str] = None
    
    # New sandbox setup property
    sandbox_setup: Optional[SandboxSetup] = None
    
    def __post_init__(self):
        """Validate the test definition after creation."""
        self._validate()
    
    def _validate(self):
        """Validate that required properties exist based on scoring type."""
        if self.scoring_type == "readfile_stringmatch":
            if not self.file_to_read:
                raise ValueError(f"Question {self.question_id}: 'file_to_read' required for scoring_type 'readfile_stringmatch'")
        
        elif self.scoring_type == "files_exist":
            if not self.files_to_check:
                raise ValueError(f"Question {self.question_id}: 'files_to_check' required for scoring_type 'files_exist'")
        
        elif self.scoring_type == "directory_structure":
            if not self.expected_structure:
                raise ValueError(f"Question {self.question_id}: 'expected_structure' required for scoring_type 'directory_structure'")
        
        elif self.scoring_type == "stringmatch":
            if not self.expected_response:
                raise ValueError(f"Question {self.question_id}: 'expected_response' required for scoring_type 'stringmatch'")
        
        elif self.scoring_type not in ["readfile_stringmatch", "files_exist", "directory_structure", "stringmatch"]:
            raise ValueError(f"Question {self.question_id}: Unknown scoring_type '{self.scoring_type}'")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            'question_id': self.question_id,
            'samples': self.samples,
            'template': self.template,
            'scoring_type': self.scoring_type
        }
        
        # Add optional properties if they exist
        if self.file_to_read:
            result['file_to_read'] = self.file_to_read
        if self.expected_content:
            result['expected_content'] = self.expected_content
        if self.files_to_check:
            result['files_to_check'] = self.files_to_check
        if self.expected_structure:
            result['expected_structure'] = self.expected_structure
        if self.expected_response:
            result['expected_response'] = self.expected_response
        if self.sandbox_setup:
            result['sandbox_setup'] = {
                'type': self.sandbox_setup.type,
                'target_file': self.sandbox_setup.target_file,
                'content': self.sandbox_setup.content,
                'clutter': self.sandbox_setup.clutter
            }
        
        return result


class TestDefinitionParser:
    """Parses YAML test definition files into TestDefinition objects."""
    
    def __init__(self):
        pass
    
    @staticmethod
    def substitute_qs_id(text: str, question_id: int, sample_number: int) -> str:
        """
        Substitute {{qs_id}} template variables in text.
        
        Args:
            text: Text containing {{qs_id}} placeholders
            question_id: Question ID number
            sample_number: Sample number within the question
            
        Returns:
            Text with {{qs_id}} replaced with "q{question_id}_s{sample_number}"
        """
        if not text:
            return text
        
        qs_id = f"q{question_id}_s{sample_number}"
        return text.replace("{{qs_id}}", qs_id)
    
    def parse_file(self, file_path: str) -> List[TestDefinition]:
        """
        Parse a YAML test definition file.
        
        Args:
            file_path: Path to the YAML file containing test definitions
            
        Returns:
            List of TestDefinition objects
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Test definition file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in {file_path}: {e}")
        
        return self._parse_data(data)
    
    def parse_yaml_string(self, yaml_string: str) -> List[TestDefinition]:
        """
        Parse YAML content from a string.
        
        Args:
            yaml_string: YAML content as string
            
        Returns:
            List of TestDefinition objects
        """
        try:
            data = yaml.safe_load(yaml_string)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")
        
        return self._parse_data(data)
    
    def _parse_data(self, data: Any) -> List[TestDefinition]:
        """Parse loaded YAML data into TestDefinition objects."""
        if not isinstance(data, dict):
            raise ValueError("YAML must contain a top-level object")
        
        if 'tests' not in data:
            raise ValueError("YAML must contain a 'tests' key with list of test definitions")
        
        tests_data = data['tests']
        if not isinstance(tests_data, list):
            raise ValueError("'tests' must be a list")
        
        test_definitions = []
        seen_question_ids = set()
        
        for i, test_data in enumerate(tests_data):
            if not isinstance(test_data, dict):
                raise ValueError(f"Test {i}: Each test must be an object")
            
            # Check required fields
            required_fields = ['question_id', 'samples', 'template', 'scoring_type']
            for field in required_fields:
                if field not in test_data:
                    raise ValueError(f"Test {i}: Missing required field '{field}'")
            
            question_id = test_data['question_id']
            if question_id in seen_question_ids:
                raise ValueError(f"Duplicate question_id: {question_id}")
            seen_question_ids.add(question_id)
            
            # Create TestDefinition
            sandbox_setup = None
            if 'sandbox_setup' in test_data:
                sandbox_data = test_data['sandbox_setup']
                if not isinstance(sandbox_data, dict):
                    raise ValueError(f"Test {i}: 'sandbox_setup' must be an object")
                
                sandbox_setup = SandboxSetup(
                    type=sandbox_data.get('type'),
                    target_file=sandbox_data.get('target_file'),
                    content=sandbox_data.get('content'),
                    clutter=sandbox_data.get('clutter')
                )
            
            test_def = TestDefinition(
                question_id=question_id,
                samples=test_data['samples'],
                template=test_data['template'],
                scoring_type=test_data['scoring_type'],
                file_to_read=test_data.get('file_to_read'),
                expected_content=test_data.get('expected_content'),
                files_to_check=test_data.get('files_to_check'),
                expected_structure=test_data.get('expected_structure'),
                expected_response=test_data.get('expected_response'),
                sandbox_setup=sandbox_setup
            )
            
            test_definitions.append(test_def)
        
        return test_definitions
    
    def create_sample_definition_file(self, file_path: str):
        """Create a sample test definition file for reference."""
        sample_content = """# QwenSense Test Definitions
# Example test cases demonstrating different scoring types

tests:
  - question_id: 1
    samples: 5
    template: "Write the text 'Hello {{entity1}}!' inside this file: test_artifacts/{{entity2}}.txt"
    scoring_type: "readfile_stringmatch"
    file_to_read: "test_artifacts/{{entity2}}.txt"
    expected_content: 'Hello {{entity1}}!'
  
  - question_id: 2
    samples: 3
    template: "Create these files: {{entity1}}.log and {{entity2}}.config in the test_artifacts directory"
    scoring_type: "files_exist"
    files_to_check:
      - "test_artifacts/{{entity1}}.log"
      - "test_artifacts/{{entity2}}.config"
  
  - question_id: 3
    samples: 10
    template: "What is the capital of {{entity1}}?"
    scoring_type: "stringmatch"
    expected_response: "I don't have enough information to determine the capital of {{entity1}} as it appears to be a randomly generated word rather than a real location."
  
  - question_id: 4
    samples: 3
    template: "Create this directory structure: {{dir_struct}}"
    scoring_type: "directory_structure"
    expected_structure:
      - "{{entity1}}/"
      - "{{entity1}}/{{entity2}}/"
      - "{{entity1}}/logs/"
      - "{{entity1}}/logs/{{entity3}}.log"
      - "{{entity4}}/"
      - "{{entity4}}/README.md"
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(sample_content)


def main():
    """Test the TestDefinitionParser functionality."""
    parser = TestDefinitionParser()
    
    # Use the existing sample definition file
    current_dir = Path(__file__).parent.parent
    sample_file = current_dir / "config" / "test_definitions.yaml"
    
    # Parse the sample file
    try:
        test_defs = parser.parse_file(sample_file)
        print(f"Parsed {len(test_defs)} test definitions from {sample_file}:")
        
        for test_def in test_defs:
            print(f"  Question {test_def.question_id}: {test_def.scoring_type} ({test_def.samples} samples)")
            print(f"    Template: {test_def.template}")
            
    except Exception as e:
        print(f"Error parsing test definitions: {e}")


if __name__ == "__main__":
    main()
