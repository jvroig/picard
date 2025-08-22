"""
Unit tests for TestRunner class.

Tests individual methods of TestRunner in isolation with mocked dependencies.
Focuses on core logic like label sanitization, directory management, 
and individual method functionality.
"""

import pytest
import tempfile
import json
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, mock_open
from io import StringIO

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from test_runner import TestRunner


class TestTestRunnerInitialization:
    """Test TestRunner initialization and setup."""
    
    def test_initialization_default_base_dir(self):
        """Test TestRunner initializes with default base directory."""
        with patch('test_runner.SandboxManager'), \
             patch('test_runner.TemplateProcessor'):
            runner = TestRunner()
            
            assert runner.base_dir is not None
            assert runner.results_dir.name == "results"
            assert runner.config_dir.name == "config"
            assert runner.test_id is None
            assert runner.test_dir is None
            assert runner.responses_file is None
            assert runner.conversations_dir is None
    
    def test_initialization_custom_base_dir(self, tmp_path):
        """Test TestRunner initializes with custom base directory."""
        with patch('test_runner.SandboxManager'), \
             patch('test_runner.TemplateProcessor'):
            runner = TestRunner(base_dir=str(tmp_path))
            
            assert runner.base_dir == tmp_path
            assert runner.results_dir == tmp_path / "results"
            assert runner.config_dir == tmp_path / "config"
    
    def test_components_initialized(self, tmp_path):
        """Test that required components are initialized."""
        with patch('test_runner.SandboxManager') as mock_sandbox, \
             patch('test_runner.TemplateProcessor') as mock_template:
            runner = TestRunner(base_dir=str(tmp_path))
            
            # Verify components were created
            mock_sandbox.assert_called_once_with(str(tmp_path))
            mock_template.assert_called_once_with(base_dir=str(tmp_path))
            assert runner.sandbox_manager is not None
            assert runner.template_processor is not None


class TestLabelSanitization:
    """Test label sanitization functionality."""
    
    @pytest.fixture
    def runner(self):
        """Create TestRunner instance for testing."""
        with patch('test_runner.SandboxManager'), \
             patch('test_runner.TemplateProcessor'):
            return TestRunner()
    
    def test_basic_label_sanitization(self, runner):
        """Test basic label sanitization."""
        result = runner.sanitize_label("My Test Run")
        assert result == "my_test_run"
    
    def test_special_characters_removed(self, runner):
        """Test that special characters are removed."""
        result = runner.sanitize_label("Test@#$%^&*()Run!")
        assert result == "testrun"
    
    def test_hyphens_and_periods_converted(self, runner):
        """Test that hyphens and periods become underscores."""
        result = runner.sanitize_label("test-run.v1")
        assert result == "test_run_v1"
    
    def test_multiple_underscores_collapsed(self, runner):
        """Test that multiple consecutive underscores are collapsed."""
        result = runner.sanitize_label("test___run____final")
        assert result == "test_run_final"
    
    def test_leading_trailing_underscores_removed(self, runner):
        """Test that leading and trailing underscores are removed."""
        result = runner.sanitize_label("_test_run_")
        assert result == "test_run"
    
    def test_length_limit_enforced(self, runner):
        """Test that very long labels are truncated."""
        long_label = "a" * 100
        result = runner.sanitize_label(long_label)
        assert len(result) <= 50
        assert result == "a" * 50
    
    def test_length_limit_with_trailing_underscore_cleanup(self, runner):
        """Test length limit with trailing underscore cleanup."""
        # Create a label that will have underscore at position 50
        label = "test_" + "a" * 50 + "_more"  
        result = runner.sanitize_label(label)
        assert len(result) <= 50
        assert not result.endswith('_')
    
    def test_empty_label_returns_default(self, runner):
        """Test that empty label returns 'test'."""
        assert runner.sanitize_label("") == "test"
        assert runner.sanitize_label("   ") == "test"
        assert runner.sanitize_label(None) == "test"
    
    def test_whitespace_only_label(self, runner):
        """Test that whitespace-only label returns 'test'."""
        assert runner.sanitize_label("\n\t  \r") == "test"
    
    def test_all_special_characters_label(self, runner):
        """Test label with only special characters returns 'test'."""
        assert runner.sanitize_label("@#$%^&*()!") == "test"
    
    def test_unicode_characters_removed(self, runner):
        """Test that Unicode characters are removed."""
        result = runner.sanitize_label("test_αβγ_run_🎉")
        assert result == "test_run"
    
    def test_numbers_preserved(self, runner):
        """Test that numbers are preserved."""
        result = runner.sanitize_label("test123_run456")
        assert result == "test123_run456"


class TestTestRunInitialization:
    """Test test run initialization functionality."""
    
    @pytest.fixture
    def runner(self, tmp_path):
        """Create TestRunner with temporary directory."""
        with patch('test_runner.SandboxManager'), \
             patch('test_runner.TemplateProcessor'):
            runner = TestRunner(base_dir=str(tmp_path))
            # Create required directories
            runner.results_dir.mkdir(exist_ok=True)
            runner.config_dir.mkdir(exist_ok=True)
            return runner
    
    def test_initialize_test_run_creates_directory(self, runner):
        """Test that test run initialization creates directory."""
        with patch('test_runner.PrecheckGenerator') as mock_precheck:
            test_id = runner.initialize_test_run(label="test_run")
            
            # Verify directory was created
            assert runner.test_dir.exists()
            assert runner.test_dir.name == test_id
            assert test_id.startswith("test_run_")
            # Check date format is present (timestamp precision may vary)
            current_date = datetime.now().strftime('%Y%m%d')
            assert current_date in test_id
    
    def test_initialize_test_run_sets_attributes(self, runner):
        """Test that initialization sets runner attributes correctly."""
        with patch('test_runner.PrecheckGenerator') as mock_precheck:
            test_id = runner.initialize_test_run(label="custom")
            
            assert runner.test_id == test_id
            assert runner.test_dir == runner.results_dir / test_id
            assert runner.precheck_generator is not None
    
    def test_initialize_test_run_creates_precheck_generator(self, runner):
        """Test that PrecheckGenerator is created with correct parameters."""
        with patch('test_runner.PrecheckGenerator') as mock_precheck:
            test_definitions_file = "custom_test.yaml"
            runner.initialize_test_run(
                test_definitions_file=test_definitions_file,
                label="test"
            )
            
            mock_precheck.assert_called_once_with(
                test_definitions_file=test_definitions_file,
                base_dir=str(runner.base_dir)
            )
    
    def test_initialize_test_run_default_test_definitions(self, runner):
        """Test that default test definitions file is used when none provided."""
        with patch('test_runner.PrecheckGenerator') as mock_precheck:
            runner.initialize_test_run(label="test")
            
            expected_file = str(runner.config_dir / "test_definitions.yaml")
            mock_precheck.assert_called_once_with(
                test_definitions_file=expected_file,
                base_dir=str(runner.base_dir)
            )
    
    def test_unique_test_ids_generated(self, runner):
        """Test that multiple initializations generate unique test IDs."""
        with patch('test_runner.PrecheckGenerator'):
            # Mock datetime to return different timestamps
            with patch('test_runner.datetime') as mock_datetime:
                # First call returns one timestamp
                mock_datetime.now.return_value.strftime.return_value = "20250822_120000"
                test_id1 = runner.initialize_test_run(label="test")
                
                # Reset for second run
                runner.test_id = None
                runner.test_dir = None
                runner.precheck_generator = None
                
                # Second call returns different timestamp
                mock_datetime.now.return_value.strftime.return_value = "20250822_120001"
                test_id2 = runner.initialize_test_run(label="test")
                
                assert test_id1 != test_id2
                assert "120000" in test_id1
                assert "120001" in test_id2
    
    def test_label_sanitization_in_test_id(self, runner):
        """Test that labels are sanitized in test ID generation."""
        with patch('test_runner.PrecheckGenerator'):
            test_id = runner.initialize_test_run(label="Test Run!")
            
            assert "test_run_" in test_id
            assert "Test Run!" not in test_id
            assert "!" not in test_id


class TestProgressiveWriting:
    """Test progressive result writing functionality."""
    
    @pytest.fixture
    def runner(self, tmp_path):
        """Create TestRunner with initialized test run."""
        with patch('test_runner.SandboxManager'), \
             patch('test_runner.TemplateProcessor'), \
             patch('test_runner.PrecheckGenerator'):
            runner = TestRunner(base_dir=str(tmp_path))
            runner.results_dir.mkdir(exist_ok=True)
            runner.test_id = "test_123"
            runner.test_dir = runner.results_dir / runner.test_id
            runner.test_dir.mkdir(exist_ok=True)
            return runner
    
    def test_initialize_progressive_writers_creates_files(self, runner):
        """Test that progressive writers create necessary files and directories."""
        runner._initialize_progressive_writers()
        
        # Verify responses file is created and opened
        responses_file = runner.test_dir / "responses.jsonl"
        assert responses_file.exists()
        assert runner.responses_file is not None
        
        # Verify conversations directory is created
        assert runner.conversations_dir.exists()
        assert runner.conversations_dir.is_dir()
        
        # Cleanup
        runner.responses_file.close()
    
    def test_write_result_immediately_creates_jsonl_entry(self, runner):
        """Test that individual results are written to JSONL immediately."""
        runner._initialize_progressive_writers()
        
        response_entry = {
            'question_id': 101,
            'sample_number': 1,
            'response_text': 'Test response',
            'timestamp': '2025-01-01T12:00:00'
        }
        
        conversation_entry = {
            'question_id': 101,
            'sample_number': 1,
            'conversation_history': [],
            'final_response': 'Test response'
        }
        
        runner._write_result_immediately(response_entry, conversation_entry)
        
        # Verify JSONL entry was written
        runner.responses_file.close()  # Close to flush
        responses_file = runner.test_dir / "responses.jsonl"
        content = responses_file.read_text()
        
        assert '{"question_id": 101' in content
        assert '"response_text": "Test response"' in content
        assert content.endswith('\n')  # JSONL format
    
    def test_write_result_immediately_creates_conversation_file(self, runner):
        """Test that individual conversation files are created."""
        runner._initialize_progressive_writers()
        
        response_entry = {
            'question_id': 102,
            'sample_number': 3,
            'response_text': 'Test response'
        }
        
        conversation_entry = {
            'question_id': 102,
            'sample_number': 3,
            'conversation_history': [{'role': 'user', 'content': 'test'}],
            'final_response': 'Test response'
        }
        
        runner._write_result_immediately(response_entry, conversation_entry)
        
        # Verify individual conversation file was created
        conversation_file = runner.conversations_dir / "q102_s3.json"
        assert conversation_file.exists()
        
        # Verify content
        conversation_data = json.loads(conversation_file.read_text())
        assert conversation_data['question_id'] == 102
        assert conversation_data['sample_number'] == 3
        assert len(conversation_data['conversation_history']) == 1
        
        # Cleanup
        runner.responses_file.close()
    
    def test_write_result_immediately_handles_file_errors(self, runner, capfd):
        """Test that file write errors don't crash the test run."""
        runner._initialize_progressive_writers()
        
        # Close the file to simulate error condition
        runner.responses_file.close()
        
        response_entry = {'question_id': 103, 'sample_number': 1}
        conversation_entry = {'question_id': 103, 'sample_number': 1}
        
        # Should not raise exception
        runner._write_result_immediately(response_entry, conversation_entry)
        
        # Check that warning was printed
        captured = capfd.readouterr()
        assert "Failed to write response to JSONL" in captured.out or "Failed to write response to JSONL" in captured.err
    
    def test_finalize_progressive_results_closes_files(self, runner):
        """Test that progressive writing finalization closes file handles."""
        runner._initialize_progressive_writers()
        
        # Mock the summary generation since it has dependencies
        with patch.object(runner, '_generate_test_summary'):
            runner._finalize_progressive_results()
        
        # Verify file handle was closed
        assert runner.responses_file is None


class TestSandboxSetup:
    """Test sandbox setup functionality."""
    
    @pytest.fixture
    def runner(self, tmp_path):
        """Create TestRunner with mocked template processor."""
        mock_template_processor = Mock()
        with patch('test_runner.SandboxManager'), \
             patch('test_runner.TemplateProcessor', return_value=mock_template_processor):
            runner = TestRunner(base_dir=str(tmp_path))
            runner.template_processor = mock_template_processor
            return runner
    
    def test_setup_question_sandbox_no_sandbox_setup(self, runner):
        """Test behavior when precheck entry has no sandbox setup."""
        precheck_entry = {
            'question_id': 1,
            'sample_number': 1,
            'substituted_question': 'Test question'
        }
        
        result = runner._setup_question_sandbox(precheck_entry)
        
        assert result['has_sandbox_setup'] is False
        assert result['files_created'] == []
        assert result['content_generated'] == {}
        assert result['errors'] == []
    
    def test_setup_question_sandbox_with_sandbox_setup(self, runner):
        """Test sandbox setup processing with template variables."""
        precheck_entry = {
            'question_id': 2,
            'sample_number': 1,
            'sandbox_setup': {
                'type': 'create_csv',
                'target_file': 'test_{{qs_id}}.csv',
                'content': {'rows': 5, 'headers': ['id', 'name']},
                'clutter': {}
            },
            'entity1': 'Alice',
            'entity2': 'Bob'
        }
        
        # Mock template processor
        runner.template_processor.process_multiple_fields.return_value = {
            'target_file': {'substituted': 'test_q2_s1.csv'},
            'content': {'substituted': "{'rows': 5, 'headers': ['id', 'name']}"},
            'clutter': {'substituted': '{}'}
        }
        
        # Mock file generator
        mock_generator = Mock()
        mock_generator.generate.return_value = {
            'files_created': ['test_q2_s1.csv'],
            'content_generated': {'test_q2_s1.csv': 'id,name\n1,Alice\n2,Bob'},
            'errors': []
        }
        
        with patch('test_runner.FileGeneratorFactory') as mock_factory:
            mock_factory.create_generator.return_value = mock_generator
            
            result = runner._setup_question_sandbox(precheck_entry)
        
        assert result['has_sandbox_setup'] is True
        assert result['files_created'] == ['test_q2_s1.csv']
        assert 'test_q2_s1.csv' in result['content_generated']
        assert result['errors'] == []
        
        # Verify template processor was called correctly
        runner.template_processor.process_multiple_fields.assert_called_once()
        call_args = runner.template_processor.process_multiple_fields.call_args
        assert call_args[0][1] == 2  # question_id
        assert call_args[0][2] == 1  # sample_number
    
    def test_setup_question_sandbox_error_handling(self, runner, capfd):
        """Test error handling when sandbox setup fails."""
        precheck_entry = {
            'question_id': 3,
            'sample_number': 1,
            'sandbox_setup': {
                'type': 'invalid_type',
                'target_file': 'test.csv'
            }
        }
        
        # Mock template processor to raise exception
        runner.template_processor.process_multiple_fields.side_effect = Exception("Template processing failed")
        
        result = runner._setup_question_sandbox(precheck_entry)
        
        assert result['has_sandbox_setup'] is True
        assert len(result['errors']) == 1
        assert "Sandbox setup failed for Q3S1" in result['errors'][0]
        assert "Template processing failed" in result['errors'][0]
        
        # Check that warning was printed
        captured = capfd.readouterr()
        assert "Sandbox setup failed" in captured.out
    
    def test_setup_question_sandbox_updates_precheck_entry(self, runner):
        """Test that sandbox setup updates the precheck entry with execution info."""
        precheck_entry = {
            'question_id': 4,
            'sample_number': 2,
            'sandbox_setup': {
                'type': 'create_text',
                'target_file': 'output.txt',
                'content': {'type': 'lorem_lines', 'count': 3}
            }
        }
        
        # Mock template processor
        runner.template_processor.process_multiple_fields.return_value = {
            'target_file': {'substituted': 'output.txt'},
            'content': {'substituted': "{'type': 'lorem_lines', 'count': 3}"},
            'clutter': {'substituted': '{}'}
        }
        
        # Mock file generator
        mock_generator = Mock()
        mock_generator.generate.return_value = {
            'files_created': ['output.txt'],
            'content_generated': {},
            'errors': []
        }
        
        with patch('test_runner.FileGeneratorFactory') as mock_factory:
            mock_factory.create_generator.return_value = mock_generator
            
            runner._setup_question_sandbox(precheck_entry)
        
        # Verify precheck entry was updated with execution info
        assert 'sandbox_execution' in precheck_entry
        execution_info = precheck_entry['sandbox_execution']
        assert execution_info['target_file'] == 'output.txt'
        assert execution_info['files_created'] == ['output.txt']
        assert 'generation_timestamp' in execution_info


class TestTestSummaryGeneration:
    """Test test summary generation functionality."""
    
    @pytest.fixture
    def runner(self, tmp_path):
        """Create TestRunner with test run initialized."""
        with patch('test_runner.SandboxManager') as mock_sandbox, \
             patch('test_runner.TemplateProcessor'), \
             patch('test_runner.PrecheckGenerator') as mock_precheck:
            
            # Setup mocks
            mock_sandbox_instance = Mock()
            mock_sandbox_instance.get_sandbox_status.return_value = {"status": "ready", "files": 10}
            mock_sandbox.return_value = mock_sandbox_instance
            
            mock_precheck_instance = Mock()
            mock_precheck_instance.get_statistics.return_value = {
                "total_questions": 5,
                "total_samples": 15,
                "entity_pool_size": 100
            }
            mock_precheck.return_value = mock_precheck_instance
            
            runner = TestRunner(base_dir=str(tmp_path))
            runner.test_id = "test_summary_123"
            runner.test_dir = tmp_path / "results" / runner.test_id
            runner.test_dir.mkdir(parents=True)
            runner.precheck_generator = mock_precheck_instance
            
            return runner
    
    def test_generate_test_summary_creates_file(self, runner):
        """Test that test summary file is created with correct structure."""
        runner._generate_test_summary()
        
        summary_file = runner.test_dir / 'test_summary.json'
        assert summary_file.exists()
        
        # Verify content structure
        summary_data = json.loads(summary_file.read_text())
        
        expected_keys = [
            'test_id', 'timestamp', 'test_directory',
            'sandbox_status', 'statistics', 'files_generated'
        ]
        
        for key in expected_keys:
            assert key in summary_data, f"Missing key: {key}"
    
    def test_generate_test_summary_content(self, runner):
        """Test that test summary contains correct information."""
        runner._generate_test_summary()
        
        summary_file = runner.test_dir / 'test_summary.json'
        summary_data = json.loads(summary_file.read_text())
        
        # Verify specific content
        assert summary_data['test_id'] == "test_summary_123"
        assert summary_data['test_directory'] == str(runner.test_dir)
        assert summary_data['sandbox_status']['status'] == "ready"
        assert summary_data['statistics']['total_questions'] == 5
        assert 'precheck' in summary_data['files_generated']
        assert 'responses' in summary_data['files_generated']
    
    def test_generate_test_summary_handles_missing_precheck_generator(self, runner):
        """Test summary generation when precheck generator is None."""
        runner.precheck_generator = None
        
        runner._generate_test_summary()
        
        summary_file = runner.test_dir / 'test_summary.json'
        summary_data = json.loads(summary_file.read_text())
        
        # Should use empty dict for statistics
        assert summary_data['statistics'] == {}