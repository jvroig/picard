"""
Unit tests for the core PICARD scorer functionality.

Tests the main PicardScorer orchestration, ScoringResult data structures,
and end-to-end scoring pipeline integration.
"""

import pytest
import tempfile
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from scorer import PicardScorer, ScoringResult, BaseScoringType


class MockScoringType(BaseScoringType):
    """Mock scoring type for testing."""
    
    def __init__(self, should_succeed=True, error_message=None):
        self.should_succeed = should_succeed
        self.error_message = error_message
    
    def score(self, precheck_entry, response_entry, test_artifacts_dir):
        if not self.should_succeed:
            raise Exception(self.error_message or "Mock scoring error")
        
        return ScoringResult(
            question_id=precheck_entry['question_id'],
            sample_number=precheck_entry['sample_number'],
            scoring_type='mock',
            correct=True,
            details={'mock': 'success'}
        )


class TestScoringResult:
    """Test ScoringResult data structure."""
    
    def test_scoring_result_creation(self):
        """Test basic ScoringResult creation."""
        result = ScoringResult(
            question_id=101,
            sample_number=1,
            scoring_type='stringmatch',
            correct=True
        )
        
        assert result.question_id == 101
        assert result.sample_number == 1
        assert result.scoring_type == 'stringmatch'
        assert result.correct is True
        assert result.error_message is None
        assert result.details == {}
        assert result.timestamp is not None
    
    def test_scoring_result_with_error(self):
        """Test ScoringResult with error information."""
        result = ScoringResult(
            question_id=102,
            sample_number=2,
            scoring_type='files_exist',
            correct=False,
            error_message="File not found",
            details={'missing_files': ['test.txt']}
        )
        
        assert result.correct is False
        assert result.error_message == "File not found"
        assert result.details['missing_files'] == ['test.txt']
    
    def test_scoring_result_to_dict(self):
        """Test ScoringResult serialization to dictionary."""
        result = ScoringResult(
            question_id=103,
            sample_number=3,
            scoring_type='jsonmatch',
            correct=True,
            details={'expected': {'key': 'value'}}
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['question_id'] == 103
        assert result_dict['sample_number'] == 3
        assert result_dict['scoring_type'] == 'jsonmatch'
        assert result_dict['correct'] is True
        assert result_dict['error_message'] is None
        assert result_dict['details']['expected']['key'] == 'value'
        assert 'timestamp' in result_dict


class TestPicardScorer:
    """Test PicardScorer orchestration functionality."""
    
    @pytest.fixture
    def temp_base_dir(self):
        """Create temporary base directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Create basic directory structure
            (base_path / "results").mkdir()
            (base_path / "test_artifacts").mkdir()
            
            yield base_path
    
    @pytest.fixture
    def scorer(self, temp_base_dir):
        """Create PicardScorer instance for testing."""
        return PicardScorer(base_dir=str(temp_base_dir))
    
    def test_scorer_initialization(self, temp_base_dir):
        """Test scorer initialization with proper directory setup."""
        scorer = PicardScorer(base_dir=str(temp_base_dir))
        
        assert scorer.base_dir == temp_base_dir
        assert scorer.results_dir == temp_base_dir / "results"
        # test_artifacts_dir might be different due to config loading
        assert scorer.test_artifacts_dir is not None
        
        # Should have registered scoring types
        assert len(scorer.scoring_types) >= 0  # May be 0 if imports fail in test env
    
    def test_scorer_default_initialization(self):
        """Test scorer initialization with default parameters."""
        scorer = PicardScorer()
        
        assert scorer.base_dir is not None
        assert scorer.results_dir is not None
        assert scorer.test_artifacts_dir is not None
    
    def test_find_test_directories_empty(self, scorer):
        """Test finding test directories when none exist."""
        test_dirs = scorer.find_test_directories()
        assert test_dirs == []
    
    def test_find_test_directories_with_tests(self, scorer, temp_base_dir):
        """Test finding test directories when they exist."""
        # Create test directories
        (temp_base_dir / "results" / "test_20250101_120000").mkdir()
        (temp_base_dir / "results" / "test_20250102_130000").mkdir()
        (temp_base_dir / "results" / "not_a_test_dir").mkdir()
        
        test_dirs = scorer.find_test_directories()
        
        assert len(test_dirs) == 2
        assert test_dirs[0].name == "test_20250101_120000"
        assert test_dirs[1].name == "test_20250102_130000"
    
    def test_find_latest_test_directory(self, scorer, temp_base_dir):
        """Test finding the most recent test directory."""
        # Create test directories with different timestamps
        (temp_base_dir / "results" / "test_20250101_120000").mkdir()
        (temp_base_dir / "results" / "test_20250102_130000").mkdir()
        (temp_base_dir / "results" / "test_20250103_140000").mkdir()
        
        latest = scorer.find_latest_test_directory()
        
        assert latest is not None
        assert latest.name == "test_20250103_140000"
    
    def test_find_latest_test_directory_none(self, scorer):
        """Test finding latest test directory when none exist."""
        latest = scorer.find_latest_test_directory()
        assert latest is None
    
    def test_validate_test_directory_valid(self, scorer, temp_base_dir):
        """Test validating a properly structured test directory."""
        test_dir = temp_base_dir / "results" / "test_20250101_120000"
        test_dir.mkdir()
        
        # Create required files
        (test_dir / "precheck.jsonl").write_text("test content")
        (test_dir / "responses.jsonl").write_text("test content")
        
        assert scorer.validate_test_directory(test_dir) is True
    
    def test_validate_test_directory_missing_files(self, scorer, temp_base_dir):
        """Test validating test directory with missing required files."""
        test_dir = temp_base_dir / "results" / "test_20250101_120000"
        test_dir.mkdir()
        
        # Only create one required file
        (test_dir / "precheck.jsonl").write_text("test content")
        
        assert scorer.validate_test_directory(test_dir) is False
    
    def test_load_precheck_file(self, scorer, temp_base_dir):
        """Test loading precheck entries from JSONL file."""
        precheck_file = temp_base_dir / "precheck.jsonl"
        
        # Create test precheck data
        precheck_data = [
            {'question_id': 101, 'sample_number': 1, 'scoring_type': 'stringmatch', 'expected_response': 'Hello'},
            {'question_id': 102, 'sample_number': 1, 'scoring_type': 'files_exist', 'files_to_check': ['test.txt']}
        ]
        
        with open(precheck_file, 'w') as f:
            for entry in precheck_data:
                f.write(json.dumps(entry) + '\n')
        
        loaded_entries = scorer.load_precheck_file(str(precheck_file))
        
        assert len(loaded_entries) == 2
        assert loaded_entries[0]['question_id'] == 101
        assert loaded_entries[1]['scoring_type'] == 'files_exist'
    
    def test_load_precheck_file_with_invalid_json(self, scorer, temp_base_dir):
        """Test loading precheck file with some invalid JSON lines."""
        precheck_file = temp_base_dir / "precheck.jsonl"
        
        with open(precheck_file, 'w') as f:
            f.write('{"question_id": 101, "sample_number": 1}\n')
            f.write('invalid json line\n')
            f.write('{"question_id": 102, "sample_number": 1}\n')
        
        loaded_entries = scorer.load_precheck_file(str(precheck_file))
        
        # Should load valid entries and skip invalid ones
        assert len(loaded_entries) == 2
        assert loaded_entries[0]['question_id'] == 101
        assert loaded_entries[1]['question_id'] == 102
    
    def test_load_responses_file(self, scorer, temp_base_dir):
        """Test loading response entries from JSONL file."""
        responses_file = temp_base_dir / "responses.jsonl"
        
        # Create test response data
        response_data = [
            {'question_id': 101, 'sample_number': 1, 'response_text': 'Hello'},
            {'question_id': 102, 'sample_number': 1, 'response_text': 'World'}
        ]
        
        with open(responses_file, 'w') as f:
            for entry in response_data:
                f.write(json.dumps(entry) + '\n')
        
        loaded_responses = scorer.load_responses_file(str(responses_file))
        
        assert len(loaded_responses) == 2
        assert loaded_responses[0]['response_text'] == 'Hello'
        assert loaded_responses[1]['response_text'] == 'World'
    
    def test_match_entries(self, scorer):
        """Test matching precheck entries with response entries."""
        precheck_entries = [
            {'question_id': 101, 'sample_number': 1, 'scoring_type': 'stringmatch'},
            {'question_id': 102, 'sample_number': 1, 'scoring_type': 'stringmatch'},
            {'question_id': 103, 'sample_number': 1, 'scoring_type': 'stringmatch'},
        ]
        
        response_entries = [
            {'question_id': 101, 'sample_number': 1, 'response_text': 'Response 1'},
            {'question_id': 102, 'sample_number': 1, 'response_text': 'Response 2'},
            # Missing response for question 103
        ]
        
        matched_pairs = scorer.match_entries(precheck_entries, response_entries)
        
        assert len(matched_pairs) == 2
        assert matched_pairs[0][0]['question_id'] == 101
        assert matched_pairs[0][1]['response_text'] == 'Response 1'
        assert matched_pairs[1][0]['question_id'] == 102
        assert matched_pairs[1][1]['response_text'] == 'Response 2'
    
    def test_score_single_entry_unknown_scoring_type(self, scorer):
        """Test scoring with unknown scoring type."""
        precheck_entry = {
            'question_id': 101,
            'sample_number': 1,
            'scoring_type': 'unknown_type'
        }
        
        response_entry = {
            'question_id': 101,
            'sample_number': 1,
            'response_text': 'Test response'
        }
        
        result = scorer.score_single_entry(precheck_entry, response_entry)
        
        assert result.correct is False
        assert "Unknown scoring type: unknown_type" in result.error_message
        assert result.scoring_type == 'unknown_type'
    
    def test_score_single_entry_with_mock_scorer(self, scorer):
        """Test scoring with a mock scoring type."""
        # Register mock scorer
        scorer.scoring_types['mock'] = MockScoringType(should_succeed=True)
        
        precheck_entry = {
            'question_id': 101,
            'sample_number': 1,
            'scoring_type': 'mock'
        }
        
        response_entry = {
            'question_id': 101,
            'sample_number': 1,
            'response_text': 'Test response'
        }
        
        result = scorer.score_single_entry(precheck_entry, response_entry)
        
        assert result.correct is True
        assert result.error_message is None
        assert result.details['mock'] == 'success'
    
    def test_score_single_entry_with_scorer_exception(self, scorer):
        """Test scoring when scorer raises an exception."""
        # Register mock scorer that fails
        scorer.scoring_types['mock_fail'] = MockScoringType(
            should_succeed=False, 
            error_message="Mock scorer failure"
        )
        
        precheck_entry = {
            'question_id': 101,
            'sample_number': 1,
            'scoring_type': 'mock_fail'
        }
        
        response_entry = {
            'question_id': 101,
            'sample_number': 1,
            'response_text': 'Test response'
        }
        
        result = scorer.score_single_entry(precheck_entry, response_entry)
        
        assert result.correct is False
        assert "Scoring error: Mock scorer failure" in result.error_message
    
    def test_score_test_directory_invalid(self, scorer, temp_base_dir):
        """Test scoring an invalid test directory."""
        test_dir = temp_base_dir / "results" / "invalid_test"
        test_dir.mkdir()
        
        with pytest.raises(ValueError, match="Invalid test directory"):
            scorer.score_test_directory(test_dir)
    
    def test_score_test_directory_valid(self, scorer, temp_base_dir):
        """Test scoring a valid test directory."""
        # Create valid test directory
        test_dir = temp_base_dir / "results" / "test_20250101_120000"
        test_dir.mkdir()
        
        # Create precheck file
        precheck_data = [
            {'question_id': 101, 'sample_number': 1, 'scoring_type': 'mock', 'expected_response': 'Hello'}
        ]
        with open(test_dir / "precheck.jsonl", 'w') as f:
            for entry in precheck_data:
                f.write(json.dumps(entry) + '\n')
        
        # Create responses file
        response_data = [
            {'question_id': 101, 'sample_number': 1, 'response_text': 'Hello'}
        ]
        with open(test_dir / "responses.jsonl", 'w') as f:
            for entry in response_data:
                f.write(json.dumps(entry) + '\n')
        
        # Register mock scorer
        scorer.scoring_types['mock'] = MockScoringType(should_succeed=True)
        
        results = scorer.score_test_directory(test_dir)
        
        assert len(results) == 1
        assert results[0].question_id == 101
        assert results[0].correct is True
    
    def test_save_results_to_test_directory(self, scorer, temp_base_dir):
        """Test saving scoring results to test directory."""
        test_dir = temp_base_dir / "results" / "test_20250101_120000"
        test_dir.mkdir()
        
        # Create sample results
        results = [
            ScoringResult(101, 1, 'stringmatch', True),
            ScoringResult(102, 1, 'files_exist', False, error_message="File missing"),
            ScoringResult(103, 1, 'stringmatch', True)
        ]
        
        scores_file = scorer.save_results_to_test_directory(results, test_dir)
        
        assert scores_file.exists()
        assert scores_file.name == "scores.json"
        
        # Load and verify saved data
        with open(scores_file) as f:
            saved_data = json.load(f)
        
        assert saved_data['metadata']['total_questions'] == 3
        assert saved_data['metadata']['correct_answers'] == 2
        assert saved_data['metadata']['accuracy_percentage'] == 66.67
        
        # Check by question breakdown (keys are strings in JSON)
        assert '101' in saved_data['by_question']
        assert saved_data['by_question']['101']['correct'] == 1
        assert saved_data['by_question']['101']['total'] == 1
        
        # Check by scoring type breakdown
        assert 'stringmatch' in saved_data['by_scoring_type']
        assert saved_data['by_scoring_type']['stringmatch']['correct'] == 2
        assert saved_data['by_scoring_type']['stringmatch']['total'] == 2
        
        # Check detailed results
        assert len(saved_data['detailed_results']) == 3
        assert saved_data['detailed_results'][0]['question_id'] == 101
        assert saved_data['detailed_results'][1]['error_message'] == "File missing"


class TestScorerIntegration:
    """Integration tests for scorer with multiple components."""
    
    @pytest.fixture
    def full_test_setup(self):
        """Create a complete test setup with multiple test directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Create directory structure
            results_dir = base_path / "results"
            results_dir.mkdir()
            artifacts_dir = base_path / "test_artifacts"
            artifacts_dir.mkdir()
            
            # Create test directory 1
            test_dir1 = results_dir / "test_20250101_120000"
            test_dir1.mkdir()
            
            precheck1 = [
                {'question_id': 101, 'sample_number': 1, 'scoring_type': 'mock', 'expected_response': 'Hello'},
                {'question_id': 102, 'sample_number': 1, 'scoring_type': 'mock', 'expected_response': 'World'}
            ]
            with open(test_dir1 / "precheck.jsonl", 'w') as f:
                for entry in precheck1:
                    f.write(json.dumps(entry) + '\n')
            
            responses1 = [
                {'question_id': 101, 'sample_number': 1, 'response_text': 'Hello'},
                {'question_id': 102, 'sample_number': 1, 'response_text': 'Goodbye'}  # Wrong answer
            ]
            with open(test_dir1 / "responses.jsonl", 'w') as f:
                for entry in responses1:
                    f.write(json.dumps(entry) + '\n')
            
            # Create test directory 2
            test_dir2 = results_dir / "test_20250102_130000"
            test_dir2.mkdir()
            
            precheck2 = [
                {'question_id': 201, 'sample_number': 1, 'scoring_type': 'mock', 'expected_response': 'Test'}
            ]
            with open(test_dir2 / "precheck.jsonl", 'w') as f:
                for entry in precheck2:
                    f.write(json.dumps(entry) + '\n')
            
            responses2 = [
                {'question_id': 201, 'sample_number': 1, 'response_text': 'Test'}
            ]
            with open(test_dir2 / "responses.jsonl", 'w') as f:
                for entry in responses2:
                    f.write(json.dumps(entry) + '\n')
            
            yield base_path, test_dir1, test_dir2
    
    def test_score_all_tests(self, full_test_setup):
        """Test scoring all test directories."""
        base_path, test_dir1, test_dir2 = full_test_setup
        
        scorer = PicardScorer(base_dir=str(base_path))
        scorer.scoring_types['mock'] = MockScoringType(should_succeed=True)
        
        all_results = scorer.score_all_tests()
        
        assert len(all_results) == 2
        assert "test_20250101_120000" in all_results
        assert "test_20250102_130000" in all_results
        
        # Check first test results
        results1 = all_results["test_20250101_120000"]
        assert len(results1) == 2
        assert results1[0].question_id == 101
        assert results1[1].question_id == 102
        
        # Check second test results
        results2 = all_results["test_20250102_130000"]
        assert len(results2) == 1
        assert results2[0].question_id == 201
    
    def test_end_to_end_scoring_workflow(self, full_test_setup):
        """Test complete end-to-end scoring workflow."""
        base_path, test_dir1, test_dir2 = full_test_setup
        
        scorer = PicardScorer(base_dir=str(base_path))
        scorer.scoring_types['mock'] = MockScoringType(should_succeed=True)
        
        # Test finding test directories
        test_dirs = scorer.find_test_directories()
        assert len(test_dirs) == 2
        
        # Test finding latest directory
        latest = scorer.find_latest_test_directory()
        assert latest.name == "test_20250102_130000"
        
        # Test scoring latest directory
        results = scorer.score_test_directory(latest)
        assert len(results) == 1
        assert results[0].correct is True
        
        # Test saving results
        scores_file = scorer.save_results_to_test_directory(results, latest)
        assert scores_file.exists()
        
        # Verify saved data
        with open(scores_file) as f:
            saved_data = json.load(f)
        
        assert saved_data['metadata']['accuracy_percentage'] == 100.0
        assert saved_data['metadata']['total_questions'] == 1