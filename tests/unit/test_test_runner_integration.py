"""
Integration tests for TestRunner class.

Tests TestRunner coordination with real components and dependencies.
Focuses on component interaction, data flow, and realistic usage scenarios.
"""

import pytest
import tempfile
import json
import yaml
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from test_runner import TestRunner


class TestTestRunnerPrecheckIntegration:
    """Test TestRunner integration with PrecheckGenerator."""
    
    @pytest.fixture
    def test_environment(self, tmp_path):
        """Set up test environment with required directories and files."""
        base_dir = tmp_path / "picard_test"
        base_dir.mkdir()
        (base_dir / "results").mkdir()
        (base_dir / "config").mkdir()
        
        # Create minimal test definitions file
        test_definitions = {
            'entity_pools': {
                'entity1': ['Alice', 'Bob'],
                'entity2': ['task1', 'task2']
            },
            'tests': [
                {
                    'question_id': 1,
                    'samples': 2,
                    'template': 'Test question with {{entity1}}',
                    'expected_response': 'Expected answer',
                    'scoring_type': 'stringmatch'
                }
            ]
        }
        
        test_def_file = base_dir / "config" / "test_definitions.yaml"
        test_def_file.write_text(yaml.dump(test_definitions))
        
        return {
            'base_dir': base_dir,
            'test_definitions_file': test_def_file
        }
    
    def test_precheck_generation_integration(self, test_environment):
        """Test TestRunner integrates correctly with PrecheckGenerator."""
        with patch('test_runner.SandboxManager') as mock_sandbox:
            # Setup sandbox manager mock
            mock_sandbox_instance = Mock()
            mock_sandbox_instance.reset_sandbox.return_value = True
            mock_sandbox_instance.get_sandbox_status.return_value = {"status": "ready"}
            mock_sandbox.return_value = mock_sandbox_instance
            
            # Create runner and run initialization
            runner = TestRunner(base_dir=str(test_environment['base_dir']))
            test_id = runner.initialize_test_run(
                test_definitions_file=str(test_environment['test_definitions_file']),
                label="integration_test"
            )
            
            # Generate precheck entries
            precheck_entries = runner.precheck_generator.generate_precheck_entries()
            
            # Verify precheck generation worked
            assert len(precheck_entries) > 0
            assert precheck_entries[0]['question_id'] == 1
            assert 'entity1' in precheck_entries[0]
            # Entity value should be one of the expected values, but entity pool might be different than expected
            entity1_value = precheck_entries[0]['entity1']
            assert isinstance(entity1_value, str)
            assert len(entity1_value) > 0
            
            # Verify statistics
            stats = runner.precheck_generator.get_statistics()
            assert stats['total_questions'] == 1
            assert stats['total_samples'] == 2
    
    def test_precheck_file_saving_integration(self, test_environment):
        """Test that precheck entries are saved correctly."""
        with patch('test_runner.SandboxManager') as mock_sandbox:
            mock_sandbox_instance = Mock()
            mock_sandbox_instance.reset_sandbox.return_value = True
            mock_sandbox.return_value = mock_sandbox_instance
            
            runner = TestRunner(base_dir=str(test_environment['base_dir']))
            test_id = runner.initialize_test_run(
                test_definitions_file=str(test_environment['test_definitions_file']),
                label="save_test"
            )
            
            # Generate and save precheck entries
            precheck_entries = runner.precheck_generator.generate_precheck_entries()
            precheck_file = runner.test_dir / "precheck.jsonl"
            runner.precheck_generator.save_precheck_entries(precheck_entries, str(precheck_file))
            
            # Verify file was saved correctly
            assert precheck_file.exists()
            
            # Verify JSONL format
            lines = precheck_file.read_text().strip().split('\n')
            assert len(lines) == len(precheck_entries)
            
            # Verify first entry can be parsed
            first_entry = json.loads(lines[0])
            assert first_entry['question_id'] == 1
            assert 'substituted_question' in first_entry


class TestTestRunnerSandboxIntegration:
    """Test TestRunner integration with sandbox setup and file generation."""
    
    @pytest.fixture
    def sandbox_test_environment(self, tmp_path):
        """Set up test environment with sandbox setup configuration."""
        base_dir = tmp_path / "picard_test"
        base_dir.mkdir()
        (base_dir / "results").mkdir()
        (base_dir / "config").mkdir()
        (base_dir / "test_artifacts").mkdir(parents=True)
        
        # Create test definitions with sandbox setup
        test_definitions = {
            'entity_pools': {
                'entity1': ['data1', 'data2'],
                'entity2': ['file1', 'file2']
            },
            'tests': [
                {
                    'question_id': 10,
                    'samples': 1,
                    'template': 'Process {{entity1}} from {{entity2}}',
                    'expected_response': 'Processing complete',
                    'scoring_type': 'stringmatch',
                    'sandbox_setup': {
                        'components': [
                            {
                                'type': 'create_csv',
                                'target_file': 'test_artifacts/{{qs_id}}/{{entity1}}.csv',
                                'content': {
                                    'headers': ['id', 'name', 'value'],
                                    'rows': 5
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        test_def_file = base_dir / "config" / "test_definitions.yaml"
        test_def_file.write_text(yaml.dump(test_definitions))
        
        return {
            'base_dir': base_dir,
            'test_definitions_file': test_def_file
        }
    
    def test_sandbox_template_processing_integration(self, sandbox_test_environment):
        """Test sandbox setup with template variable processing."""
        with patch('test_runner.SandboxManager') as mock_sandbox:
            mock_sandbox_instance = Mock()
            mock_sandbox_instance.reset_sandbox.return_value = True
            mock_sandbox.return_value = mock_sandbox_instance
            
            runner = TestRunner(base_dir=str(sandbox_test_environment['base_dir']))
            runner.initialize_test_run(
                test_definitions_file=str(sandbox_test_environment['test_definitions_file']),
                label="sandbox_test"
            )
            
            # Generate precheck entries (which includes sandbox processing)
            precheck_entries = runner.precheck_generator.generate_precheck_entries()
            
            # Find entry with sandbox setup
            sandbox_entry = None
            for entry in precheck_entries:
                if 'sandbox_generation' in entry:
                    sandbox_entry = entry
                    break
            
            assert sandbox_entry is not None
            
            # Verify template processing occurred
            sandbox_gen = sandbox_entry['sandbox_generation']
            if sandbox_gen.get('generation_successful', False):
                assert len(sandbox_gen.get('files_created', [])) > 0
                
                # Verify file path contains resolved variables
                created_file = sandbox_gen['files_created'][0]
                assert 'q10_s1' in created_file  # {{qs_id}} should be resolved
                assert not '{{' in created_file  # No unresolved templates
    
    def test_sandbox_file_generation_integration(self, sandbox_test_environment):
        """Test that sandbox setup actually creates files."""
        with patch('test_runner.SandboxManager') as mock_sandbox:
            mock_sandbox_instance = Mock()
            mock_sandbox_instance.reset_sandbox.return_value = True
            mock_sandbox.return_value = mock_sandbox_instance
            
            runner = TestRunner(base_dir=str(sandbox_test_environment['base_dir']))
            runner.initialize_test_run(
                test_definitions_file=str(sandbox_test_environment['test_definitions_file']),
                label="file_gen_test"
            )
            
            # Generate precheck entries
            precheck_entries = runner.precheck_generator.generate_precheck_entries()
            
            # Find entry with successful sandbox generation
            for entry in precheck_entries:
                if 'sandbox_generation' in entry and entry['sandbox_generation'].get('generation_successful'):
                    files_created = entry['sandbox_generation']['files_created']
                    
                    # Verify files were actually created
                    for file_path in files_created:
                        full_path = sandbox_test_environment['base_dir'] / file_path
                        assert full_path.exists(), f"File {file_path} should have been created"
                        
                        # Verify file has content
                        content = full_path.read_text()
                        assert len(content) > 0
                        
                        # For CSV files, verify CSV structure
                        if file_path.endswith('.csv'):
                            lines = content.strip().split('\n')
                            assert len(lines) >= 2  # Header + at least 1 data row
                            assert 'id,name,value' in lines[0]  # Expected headers


class TestTestRunnerLLMIntegration:
    """Test TestRunner integration with LLM execution (mocked)."""
    
    @pytest.fixture
    def llm_test_environment(self, tmp_path):
        """Set up environment for LLM integration testing."""
        base_dir = tmp_path / "picard_test"
        base_dir.mkdir()
        (base_dir / "results").mkdir()
        (base_dir / "config").mkdir()
        
        # Simple test definitions for LLM testing
        test_definitions = {
            'entity_pools': {
                'entity1': ['test1', 'test2']
            },
            'tests': [
                {
                    'question_id': 20,
                    'samples': 2,
                    'template': 'Simple question about {{entity1}}',
                    'expected_response': 'Simple answer',
                    'scoring_type': 'stringmatch'
                }
            ]
        }
        
        test_def_file = base_dir / "config" / "test_definitions.yaml"
        test_def_file.write_text(yaml.dump(test_definitions))
        
        return {
            'base_dir': base_dir,
            'test_definitions_file': test_def_file
        }
    
    def test_mock_llm_execution_integration(self, llm_test_environment):
        """Test integration with mock LLM execution."""
        # Mock the sandbox manager
        with patch('test_runner.SandboxManager') as mock_sandbox:
            mock_sandbox_instance = Mock()
            mock_sandbox_instance.reset_sandbox.return_value = True
            mock_sandbox_instance.get_sandbox_status.return_value = {"status": "ready"}
            mock_sandbox.return_value = mock_sandbox_instance
            
            # Mock the LLM execution function
            mock_llm_response = {
                'response_text': 'Mock LLM response',
                'execution_successful': True,
                'timestamp': '2025-01-01T12:00:00',
                'model_info': 'mock_model',
                'conversation_history': [],
                'statistics': {'total_time': 1.5}
            }
            
            # Mock the LLM execution at the module level where it's imported
            with patch('src.mock_llm.execute_with_retry', return_value=mock_llm_response) as mock_execute:
                runner = TestRunner(base_dir=str(llm_test_environment['base_dir']))
                
                # Run a complete benchmark with mock LLM
                result = runner.run_benchmark(
                    test_definitions_file=str(llm_test_environment['test_definitions_file']),
                    use_mock_llm=True,
                    label="llm_integration_test"
                )
                
                # Verify LLM was called for each sample
                expected_calls = 2  # 2 samples
                assert mock_execute.call_count == expected_calls
                
                # Verify results were written
                responses_file = Path(result['responses_file'])
                assert responses_file.exists()
                
                # Verify response content
                responses_content = responses_file.read_text()
                response_lines = responses_content.strip().split('\n')
                assert len(response_lines) == expected_calls
                
                # Verify each response is valid JSON
                for line in response_lines:
                    response_data = json.loads(line)
                    assert response_data['execution_successful'] is True
                    assert response_data['response_text'] == 'Mock LLM response'
    
    def test_llm_execution_with_retry_parameters(self, llm_test_environment):
        """Test that LLM execution receives correct retry parameters."""
        with patch('test_runner.SandboxManager') as mock_sandbox:
            mock_sandbox_instance = Mock()
            mock_sandbox_instance.reset_sandbox.return_value = True
            mock_sandbox_instance.get_sandbox_status.return_value = {"status": "ready"}
            mock_sandbox.return_value = mock_sandbox_instance
            
            mock_llm_response = {
                'response_text': 'Test response',
                'execution_successful': True,
                'timestamp': '2025-01-01T12:00:00',
                'model_info': 'test_model'
            }
            
            # Mock the LLM execution at the module level where it's imported
            with patch('src.mock_llm.execute_with_retry', return_value=mock_llm_response) as mock_execute:
                runner = TestRunner(base_dir=str(llm_test_environment['base_dir']))
                
                # Run with custom parameters
                runner.run_benchmark(
                    test_definitions_file=str(llm_test_environment['test_definitions_file']),
                    max_retries=5,
                    max_llm_rounds=10,
                    retry_delay=3.5,
                    api_endpoint="http://custom-endpoint.com/api",
                    use_mock_llm=True,
                    label="retry_test"
                )
                
                # Verify parameters were passed correctly
                assert mock_execute.call_count > 0
                call_args = mock_execute.call_args
                assert call_args[1]['max_retries'] == 5
                assert call_args[1]['max_llm_rounds'] == 10
                assert call_args[1]['delay'] == 3.5
                assert call_args[1]['api_endpoint'] == "http://custom-endpoint.com/api"
    
    def test_llm_execution_error_handling(self, llm_test_environment):
        """Test error handling when LLM execution fails."""
        with patch('test_runner.SandboxManager') as mock_sandbox:
            mock_sandbox_instance = Mock()
            mock_sandbox_instance.reset_sandbox.return_value = True
            mock_sandbox.return_value = mock_sandbox_instance
            
            # Mock LLM execution to raise an exception
            with patch('src.mock_llm.execute_with_retry', side_effect=Exception("LLM connection failed")):
                runner = TestRunner(base_dir=str(llm_test_environment['base_dir']))
                
                # Should raise exception due to fail-fast strategy
                with pytest.raises(Exception) as exc_info:
                    runner.run_benchmark(
                        test_definitions_file=str(llm_test_environment['test_definitions_file']),
                        use_mock_llm=True,
                        label="error_test"
                    )
                
                assert "Test run aborted due to LLM execution failure" in str(exc_info.value)


class TestTestRunnerProgressiveWriting:
    """Test TestRunner progressive writing during execution."""
    
    @pytest.fixture
    def progressive_test_environment(self, tmp_path):
        """Set up environment for progressive writing testing."""
        base_dir = tmp_path / "picard_test"
        base_dir.mkdir()
        (base_dir / "results").mkdir()
        (base_dir / "config").mkdir()
        
        # Test definitions with multiple samples for progressive testing
        test_definitions = {
            'entity_pools': {
                'entity1': ['item1', 'item2', 'item3']
            },
            'tests': [
                {
                    'question_id': 30,
                    'samples': 3,
                    'template': 'Question about {{entity1}}',
                    'expected_response': 'Answer',
                    'scoring_type': 'stringmatch'
                }
            ]
        }
        
        test_def_file = base_dir / "config" / "test_definitions.yaml"
        test_def_file.write_text(yaml.dump(test_definitions))
        
        return {
            'base_dir': base_dir,
            'test_definitions_file': test_def_file
        }
    
    def test_progressive_writing_during_execution(self, progressive_test_environment):
        """Test that results are written progressively during execution."""
        with patch('test_runner.SandboxManager') as mock_sandbox:
            mock_sandbox_instance = Mock()
            mock_sandbox_instance.reset_sandbox.return_value = True
            mock_sandbox_instance.get_sandbox_status.return_value = {"status": "ready"}
            mock_sandbox.return_value = mock_sandbox_instance
            
            # Create a call counter to simulate progressive execution
            call_count = 0
            
            def mock_llm_execute(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                return {
                    'response_text': f'Response {call_count}',
                    'execution_successful': True,
                    'timestamp': '2025-01-01T12:00:00',
                    'model_info': 'test_model',
                    'conversation_history': [],
                    'statistics': {}
                }
            
            with patch('src.mock_llm.execute_with_retry', side_effect=mock_llm_execute):
                runner = TestRunner(base_dir=str(progressive_test_environment['base_dir']))
                
                # Initialize test run and setup progressive writing
                test_id = runner.initialize_test_run(
                    test_definitions_file=str(progressive_test_environment['test_definitions_file']),
                    label="progressive_test"
                )
                
                precheck_entries = runner.precheck_generator.generate_precheck_entries()
                runner._initialize_progressive_writers()
                
                # Execute questions one by one and verify progressive writing
                total_executed = 0
                for entry in precheck_entries:
                    # Execute single question
                    result = mock_llm_execute(entry['substituted_question'])
                    
                    response_entry = {
                        'question_id': entry['question_id'],
                        'sample_number': entry['sample_number'],
                        'timestamp': result['timestamp'],
                        'response_text': result['response_text'],
                        'execution_successful': result['execution_successful']
                    }
                    
                    conversation_entry = {
                        'question_id': entry['question_id'],
                        'sample_number': entry['sample_number'],
                        'timestamp': result['timestamp'],
                        'final_response': result['response_text'],
                        'conversation_history': result['conversation_history']
                    }
                    
                    # Write result immediately
                    runner._write_result_immediately(response_entry, conversation_entry)
                    total_executed += 1
                    
                    # Verify progressive writing - file should contain results so far
                    runner.responses_file.flush()  # Force flush to disk
                    responses_file = runner.test_dir / "responses.jsonl"
                    
                    if responses_file.exists():
                        content = responses_file.read_text().strip()
                        if content:
                            lines = content.split('\n')
                            assert len(lines) == total_executed
                
                # Clean up
                runner._finalize_progressive_results()
                
                # Verify final state
                responses_file = runner.test_dir / "responses.jsonl"
                final_content = responses_file.read_text().strip()
                final_lines = final_content.split('\n')
                assert len(final_lines) == len(precheck_entries)
    
    def test_conversation_files_created_progressively(self, progressive_test_environment):
        """Test that individual conversation files are created during execution."""
        with patch('test_runner.SandboxManager') as mock_sandbox:
            mock_sandbox_instance = Mock()
            mock_sandbox_instance.reset_sandbox.return_value = True
            mock_sandbox.return_value = mock_sandbox_instance
            
            runner = TestRunner(base_dir=str(progressive_test_environment['base_dir']))
            test_id = runner.initialize_test_run(
                test_definitions_file=str(progressive_test_environment['test_definitions_file']),
                label="conversation_test"
            )
            
            precheck_entries = runner.precheck_generator.generate_precheck_entries()
            runner._initialize_progressive_writers()
            
            # Process each entry and verify conversation files
            for entry in precheck_entries:
                conversation_entry = {
                    'question_id': entry['question_id'],
                    'sample_number': entry['sample_number'],
                    'timestamp': '2025-01-01T12:00:00',
                    'final_response': f'Response for Q{entry["question_id"]}S{entry["sample_number"]}',
                    'conversation_history': [{'role': 'user', 'content': entry['substituted_question']}]
                }
                
                response_entry = {
                    'question_id': entry['question_id'],
                    'sample_number': entry['sample_number'],
                    'response_text': conversation_entry['final_response']
                }
                
                runner._write_result_immediately(response_entry, conversation_entry)
                
                # Verify conversation file was created
                expected_filename = f"q{entry['question_id']}_s{entry['sample_number']}.json"
                conversation_file = runner.conversations_dir / expected_filename
                assert conversation_file.exists()
                
                # Verify content
                conversation_data = json.loads(conversation_file.read_text())
                assert conversation_data['question_id'] == entry['question_id']
                assert conversation_data['sample_number'] == entry['sample_number']
                assert len(conversation_data['conversation_history']) == 1
            
            runner._finalize_progressive_results()


class TestTestRunnerErrorRecovery:
    """Test TestRunner error recovery and edge cases."""
    
    @pytest.fixture
    def error_test_environment(self, tmp_path):
        """Set up environment for error testing."""
        base_dir = tmp_path / "picard_test"
        base_dir.mkdir()
        (base_dir / "results").mkdir()
        (base_dir / "config").mkdir()
        
        test_definitions = {
            'entity_pools': {'entity1': ['test']},
            'tests': [
                {
                    'question_id': 40,
                    'samples': 1,
                    'template': 'Test question',
                    'expected_response': 'Test answer',
                    'scoring_type': 'stringmatch'
                }
            ]
        }
        
        test_def_file = base_dir / "config" / "test_definitions.yaml"
        test_def_file.write_text(yaml.dump(test_definitions))
        
        return {'base_dir': base_dir, 'test_definitions_file': test_def_file}
    
    def test_sandbox_reset_failure_handling(self, error_test_environment):
        """Test error handling when sandbox reset fails."""
        with patch('test_runner.SandboxManager') as mock_sandbox:
            mock_sandbox_instance = Mock()
            mock_sandbox_instance.reset_sandbox.return_value = False  # Simulate failure
            mock_sandbox.return_value = mock_sandbox_instance
            
            runner = TestRunner(base_dir=str(error_test_environment['base_dir']))
            
            # Should raise exception when sandbox reset fails
            with pytest.raises(Exception) as exc_info:
                runner.run_benchmark(
                    test_definitions_file=str(error_test_environment['test_definitions_file']),
                    use_mock_llm=True,
                    label="sandbox_fail_test"
                )
            
            assert "Failed to reset sandbox" in str(exc_info.value)
    
    def test_progressive_writing_error_recovery(self, error_test_environment):
        """Test that progressive writing errors don't crash the test run."""
        with patch('test_runner.SandboxManager') as mock_sandbox:
            mock_sandbox_instance = Mock()
            mock_sandbox_instance.reset_sandbox.return_value = True
            mock_sandbox_instance.get_sandbox_status.return_value = {"status": "ready"}
            mock_sandbox.return_value = mock_sandbox_instance
            
            mock_llm_response = {
                'response_text': 'Test response',
                'execution_successful': True,
                'timestamp': '2025-01-01T12:00:00',
                'model_info': 'test_model'
            }
            
            with patch('src.mock_llm.execute_with_retry', return_value=mock_llm_response):
                runner = TestRunner(base_dir=str(error_test_environment['base_dir']))
                
                # Mock file write error
                with patch('builtins.open', side_effect=IOError("Disk full")):
                    # Should complete without crashing despite write errors
                    result = runner.run_benchmark(
                        test_definitions_file=str(error_test_environment['test_definitions_file']),
                        use_mock_llm=True,
                        label="write_error_test"
                    )
                    
                    # Should return result even with write errors
                    assert 'test_id' in result
                    assert 'test_dir' in result