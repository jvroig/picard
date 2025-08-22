"""
Unit tests for the FilesExist scoring type.

Tests file existence checking functionality including path resolution,
multiple file handling, and various path formats.
"""

import pytest
import tempfile
import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "scoring_types"))

from scoring_types.files_exist import FilesExistScorer
from scorer import ScoringResult


class TestFilesExistScorer:
    """Test the FilesExistScorer implementation."""
    
    @pytest.fixture
    def scorer(self):
        """Create FilesExistScorer instance for testing."""
        return FilesExistScorer()
    
    @pytest.fixture
    def test_artifacts_dir(self, tmp_path):
        """Create temporary test artifacts directory with test files."""
        artifacts_dir = tmp_path / "test_artifacts"
        artifacts_dir.mkdir()
        
        # Create some test files
        (artifacts_dir / "file1.txt").write_text("Test content 1")
        (artifacts_dir / "file2.csv").write_text("header1,header2\nvalue1,value2")
        (artifacts_dir / "subdir").mkdir()
        (artifacts_dir / "subdir" / "nested_file.json").write_text('{"key": "value"}')
        
        return artifacts_dir
    
    def test_single_file_exists_success(self, scorer, test_artifacts_dir):
        """Test successful scoring when single file exists."""
        precheck_entry = {
            'question_id': 101,
            'sample_number': 1,
            'files_to_check': ['file1.txt']
        }
        
        response_entry = {
            'question_id': 101,
            'sample_number': 1,
            'response_text': 'Some response'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert isinstance(result, ScoringResult)
        assert result.question_id == 101
        assert result.sample_number == 1
        assert result.scoring_type == 'files_exist'
        assert result.correct is True
        assert result.error_message is None
        
        # Check details
        assert result.details['all_files_exist'] is True
        assert result.details['missing_files'] == []
        assert result.details['files_to_check'] == ['file1.txt']
        
        # Check individual file status
        file_status = result.details['file_status']['file1.txt']
        assert file_status['exists'] is True
        assert file_status['is_file'] is True
        assert 'file1.txt' in file_status['expected_path']
    
    def test_single_file_missing_failure(self, scorer, test_artifacts_dir):
        """Test failure when single file is missing."""
        precheck_entry = {
            'question_id': 102,
            'sample_number': 1,
            'files_to_check': ['missing_file.txt']
        }
        
        response_entry = {
            'question_id': 102,
            'sample_number': 1,
            'response_text': 'Some response'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is False
        assert result.error_message == "Missing files: ['missing_file.txt']"
        
        # Check details
        assert result.details['all_files_exist'] is False
        assert result.details['missing_files'] == ['missing_file.txt']
        
        # Check individual file status
        file_status = result.details['file_status']['missing_file.txt']
        assert file_status['exists'] is False
        assert file_status['is_file'] is False
    
    def test_multiple_files_all_exist_success(self, scorer, test_artifacts_dir):
        """Test successful scoring when all multiple files exist."""
        precheck_entry = {
            'question_id': 103,
            'sample_number': 1,
            'files_to_check': ['file1.txt', 'file2.csv', 'subdir/nested_file.json']
        }
        
        response_entry = {
            'question_id': 103,
            'sample_number': 1,
            'response_text': 'Some response'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        assert result.details['all_files_exist'] is True
        assert result.details['missing_files'] == []
        
        # Check all files are marked as existing
        for file_path in ['file1.txt', 'file2.csv', 'subdir/nested_file.json']:
            file_status = result.details['file_status'][file_path]
            assert file_status['exists'] is True
            assert file_status['is_file'] is True
    
    def test_multiple_files_some_missing_failure(self, scorer, test_artifacts_dir):
        """Test failure when some files are missing."""
        precheck_entry = {
            'question_id': 104,
            'sample_number': 1,
            'files_to_check': ['file1.txt', 'missing1.txt', 'file2.csv', 'missing2.txt']
        }
        
        response_entry = {
            'question_id': 104,
            'sample_number': 1,
            'response_text': 'Some response'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is False
        assert result.error_message == "Missing files: ['missing1.txt', 'missing2.txt']"
        
        # Check details
        assert result.details['all_files_exist'] is False
        assert set(result.details['missing_files']) == {'missing1.txt', 'missing2.txt'}
        
        # Check existing files are marked correctly
        assert result.details['file_status']['file1.txt']['exists'] is True
        assert result.details['file_status']['file2.csv']['exists'] is True
        
        # Check missing files are marked correctly
        assert result.details['file_status']['missing1.txt']['exists'] is False
        assert result.details['file_status']['missing2.txt']['exists'] is False
    
    def test_no_files_to_check_error(self, scorer, test_artifacts_dir):
        """Test error when no files_to_check are specified."""
        precheck_entry = {
            'question_id': 105,
            'sample_number': 1,
            'files_to_check': []
        }
        
        response_entry = {
            'question_id': 105,
            'sample_number': 1,
            'response_text': 'Some response'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is False
        assert result.error_message == "No files_to_check specified in precheck entry"
    
    def test_missing_files_to_check_field_error(self, scorer, test_artifacts_dir):
        """Test error when files_to_check field is missing entirely."""
        precheck_entry = {
            'question_id': 106,
            'sample_number': 1
            # missing files_to_check field
        }
        
        response_entry = {
            'question_id': 106,
            'sample_number': 1,
            'response_text': 'Some response'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is False
        assert result.error_message == "No files_to_check specified in precheck entry"
    
    def test_absolute_path_resolution(self, scorer, test_artifacts_dir):
        """Test that absolute paths are used directly."""
        # Create a file at an absolute path
        absolute_file = test_artifacts_dir / "absolute_test.txt"
        absolute_file.write_text("absolute content")
        
        precheck_entry = {
            'question_id': 107,
            'sample_number': 1,
            'files_to_check': [str(absolute_file)]  # Absolute path
        }
        
        response_entry = {
            'question_id': 107,
            'sample_number': 1,
            'response_text': 'Some response'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        
        # Check that the absolute path was used
        file_status = result.details['file_status'][str(absolute_file)]
        assert file_status['expected_path'] == str(absolute_file)
        assert file_status['exists'] is True
    
    def test_test_artifacts_prefix_removal(self, scorer, test_artifacts_dir):
        """Test that 'test_artifacts/' prefix is properly handled."""
        precheck_entry = {
            'question_id': 108,
            'sample_number': 1,
            'files_to_check': ['test_artifacts/file1.txt']  # With prefix
        }
        
        response_entry = {
            'question_id': 108,
            'sample_number': 1,
            'response_text': 'Some response'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        
        # Check that the prefix was removed and path resolved correctly
        file_status = result.details['file_status']['test_artifacts/file1.txt']
        expected_path = str(test_artifacts_dir / 'file1.txt')
        assert file_status['expected_path'] == expected_path
        assert file_status['exists'] is True
    
    def test_relative_path_resolution(self, scorer, test_artifacts_dir):
        """Test that relative paths are resolved against test_artifacts_dir."""
        precheck_entry = {
            'question_id': 109,
            'sample_number': 1,
            'files_to_check': ['subdir/nested_file.json']  # Relative path
        }
        
        response_entry = {
            'question_id': 109,
            'sample_number': 1,
            'response_text': 'Some response'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        
        # Check that relative path was resolved correctly
        file_status = result.details['file_status']['subdir/nested_file.json']
        expected_path = str(test_artifacts_dir / 'subdir' / 'nested_file.json')
        assert file_status['expected_path'] == expected_path
        assert file_status['exists'] is True
    
    def test_directory_vs_file_detection(self, scorer, test_artifacts_dir):
        """Test that directories are detected correctly (exists=True, is_file=False)."""
        precheck_entry = {
            'question_id': 110,
            'sample_number': 1,
            'files_to_check': ['subdir']  # Directory, not file
        }
        
        response_entry = {
            'question_id': 110,
            'sample_number': 1,
            'response_text': 'Some response'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True  # Directory exists
        
        # Check that it's detected as existing but not a file
        file_status = result.details['file_status']['subdir']
        assert file_status['exists'] is True
        assert file_status['is_file'] is False  # It's a directory
    
    def test_mixed_file_types_and_paths(self, scorer, test_artifacts_dir):
        """Test scoring with mixed file types and path formats."""
        # Create additional test files
        (test_artifacts_dir / "mixed_test.log").write_text("log content")
        
        precheck_entry = {
            'question_id': 111,
            'sample_number': 1,
            'files_to_check': [
                'file1.txt',                           # Simple relative
                'test_artifacts/file2.csv',            # With prefix
                'subdir/nested_file.json',             # Nested relative
                str(test_artifacts_dir / 'mixed_test.log'),  # Absolute
                'subdir',                              # Directory
                'missing.txt'                          # Missing file
            ]
        }
        
        response_entry = {
            'question_id': 111,
            'sample_number': 1,
            'response_text': 'Some response'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is False  # Because missing.txt doesn't exist
        assert result.details['missing_files'] == ['missing.txt']
        
        # Check that existing files are marked correctly
        existing_files = [
            'file1.txt', 'test_artifacts/file2.csv', 
            'subdir/nested_file.json', str(test_artifacts_dir / 'mixed_test.log'), 'subdir'
        ]
        
        for file_path in existing_files:
            file_status = result.details['file_status'][file_path]
            assert file_status['exists'] is True, f"File {file_path} should exist"
    
    def test_empty_files_are_detected(self, scorer, test_artifacts_dir):
        """Test that empty files are still detected as existing."""
        # Create empty file
        empty_file = test_artifacts_dir / "empty.txt"
        empty_file.touch()
        
        precheck_entry = {
            'question_id': 112,
            'sample_number': 1,
            'files_to_check': ['empty.txt']
        }
        
        response_entry = {
            'question_id': 112,
            'sample_number': 1,
            'response_text': 'Some response'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        
        # Check that empty file is detected
        file_status = result.details['file_status']['empty.txt']
        assert file_status['exists'] is True
        assert file_status['is_file'] is True
    
    def test_special_characters_in_filenames(self, scorer, test_artifacts_dir):
        """Test files with special characters in names."""
        # Create files with special characters
        special_files = [
            "file with spaces.txt",
            "file-with-dashes.txt", 
            "file_with_underscores.txt",
            "file.with.dots.txt"
        ]
        
        for filename in special_files:
            (test_artifacts_dir / filename).write_text("content")
        
        precheck_entry = {
            'question_id': 113,
            'sample_number': 1,
            'files_to_check': special_files
        }
        
        response_entry = {
            'question_id': 113,
            'sample_number': 1,
            'response_text': 'Some response'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        
        # Check all special files are detected
        for filename in special_files:
            file_status = result.details['file_status'][filename]
            assert file_status['exists'] is True
            assert file_status['is_file'] is True


class TestFilesExistScorerPathResolution:
    """Test the path resolution logic in FilesExistScorer."""
    
    @pytest.fixture
    def scorer(self):
        """Create FilesExistScorer instance for testing."""
        return FilesExistScorer()
    
    def test_resolve_file_path_absolute(self, scorer, tmp_path):
        """Test _resolve_file_path with absolute paths."""
        test_artifacts_dir = tmp_path / "artifacts"
        absolute_path = tmp_path / "some_file.txt"
        
        resolved = scorer._resolve_file_path(str(absolute_path), test_artifacts_dir)
        
        assert resolved == absolute_path
    
    def test_resolve_file_path_with_test_artifacts_prefix(self, scorer, tmp_path):
        """Test _resolve_file_path with test_artifacts/ prefix."""
        test_artifacts_dir = tmp_path / "artifacts"
        file_path_str = "test_artifacts/subdir/file.txt"
        
        resolved = scorer._resolve_file_path(file_path_str, test_artifacts_dir)
        
        expected = test_artifacts_dir / "subdir" / "file.txt"
        assert resolved == expected
    
    def test_resolve_file_path_relative(self, scorer, tmp_path):
        """Test _resolve_file_path with simple relative paths."""
        test_artifacts_dir = tmp_path / "artifacts"
        file_path_str = "simple_file.txt"
        
        resolved = scorer._resolve_file_path(file_path_str, test_artifacts_dir)
        
        expected = test_artifacts_dir / "simple_file.txt"
        assert resolved == expected
    
    def test_resolve_file_path_nested_relative(self, scorer, tmp_path):
        """Test _resolve_file_path with nested relative paths."""
        test_artifacts_dir = tmp_path / "artifacts"
        file_path_str = "dir1/dir2/nested_file.txt"
        
        resolved = scorer._resolve_file_path(file_path_str, test_artifacts_dir)
        
        expected = test_artifacts_dir / "dir1" / "dir2" / "nested_file.txt"
        assert resolved == expected


class TestFilesExistScorerIntegration:
    """Integration tests for FilesExistScorer with realistic scenarios."""
    
    @pytest.fixture
    def scorer(self):
        """Create FilesExistScorer instance for testing."""
        return FilesExistScorer()
    
    @pytest.fixture
    def realistic_test_setup(self, tmp_path):
        """Create a realistic test directory structure."""
        artifacts_dir = tmp_path / "test_artifacts"
        artifacts_dir.mkdir()
        
        # Create typical PICARD test output structure
        q101_dir = artifacts_dir / "q101_s1"
        q101_dir.mkdir()
        
        # Create various file types that might be generated
        (q101_dir / "output.txt").write_text("Generated output")
        (q101_dir / "data.csv").write_text("id,name\n1,test")
        (q101_dir / "config.json").write_text('{"setting": "value"}')
        (q101_dir / "logs").mkdir()
        (q101_dir / "logs" / "process.log").write_text("Process log")
        
        return artifacts_dir
    
    def test_typical_picard_file_check(self, scorer, realistic_test_setup):
        """Test typical PICARD file existence check scenario."""
        precheck_entry = {
            'question_id': 201,
            'sample_number': 1,
            'files_to_check': [
                'q101_s1/output.txt',
                'q101_s1/data.csv',
                'q101_s1/config.json',
                'q101_s1/logs/process.log'
            ]
        }
        
        response_entry = {
            'question_id': 201,
            'sample_number': 1,
            'response_text': 'Task completed successfully'
        }
        
        result = scorer.score(precheck_entry, response_entry, realistic_test_setup)
        
        assert result.correct is True
        assert result.details['all_files_exist'] is True
        assert result.details['missing_files'] == []
        
        # Verify all files are detected
        for file_path in precheck_entry['files_to_check']:
            file_status = result.details['file_status'][file_path]
            assert file_status['exists'] is True
            assert file_status['is_file'] is True
    
    def test_partial_task_completion(self, scorer, realistic_test_setup):
        """Test scenario where task was only partially completed."""
        precheck_entry = {
            'question_id': 202,
            'sample_number': 1,
            'files_to_check': [
                'q101_s1/output.txt',       # Exists
                'q101_s1/data.csv',         # Exists  
                'q101_s1/summary.txt',      # Missing
                'q101_s1/analysis.pdf'      # Missing
            ]
        }
        
        response_entry = {
            'question_id': 202,
            'sample_number': 1,
            'response_text': 'Partial completion'
        }
        
        result = scorer.score(precheck_entry, response_entry, realistic_test_setup)
        
        assert result.correct is False
        assert result.details['all_files_exist'] is False
        assert set(result.details['missing_files']) == {'q101_s1/summary.txt', 'q101_s1/analysis.pdf'}
        
        # Verify existing files are still detected
        assert result.details['file_status']['q101_s1/output.txt']['exists'] is True
        assert result.details['file_status']['q101_s1/data.csv']['exists'] is True
    
    def test_directory_structure_check(self, scorer, realistic_test_setup):
        """Test checking for directory structure creation."""
        precheck_entry = {
            'question_id': 203,
            'sample_number': 1,
            'files_to_check': [
                'q101_s1',           # Directory should exist
                'q101_s1/logs',      # Subdirectory should exist
                'q101_s1/output.txt' # File should exist
            ]
        }
        
        response_entry = {
            'question_id': 203,
            'sample_number': 1,
            'response_text': 'Structure created'
        }
        
        result = scorer.score(precheck_entry, response_entry, realistic_test_setup)
        
        assert result.correct is True
        
        # Check directory detection
        assert result.details['file_status']['q101_s1']['exists'] is True
        assert result.details['file_status']['q101_s1']['is_file'] is False  # It's a directory
        
        assert result.details['file_status']['q101_s1/logs']['exists'] is True
        assert result.details['file_status']['q101_s1/logs']['is_file'] is False  # It's a directory
        
        assert result.details['file_status']['q101_s1/output.txt']['exists'] is True
        assert result.details['file_status']['q101_s1/output.txt']['is_file'] is True  # It's a file
    
    def test_edge_case_empty_file_list_in_real_scenario(self, scorer, realistic_test_setup):
        """Test edge case with empty file list in realistic scenario."""
        precheck_entry = {
            'question_id': 204,
            'sample_number': 1,
            'files_to_check': []  # No files to check
        }
        
        response_entry = {
            'question_id': 204,
            'sample_number': 1,
            'response_text': 'No file output expected'
        }
        
        result = scorer.score(precheck_entry, response_entry, realistic_test_setup)
        
        assert result.correct is False
        assert result.error_message == "No files_to_check specified in precheck entry"