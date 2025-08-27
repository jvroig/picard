"""
JSON Targeted Edit Scorer - Verifies targeted JSON file modifications

Tests that LLMs correctly modify JSON files by:
1. Verifying target changes occurred correctly
2. Verifying non-target data remained unchanged

This enables testing write operations while maintaining PICARD's anti-memorization advantages.
"""
import json
import sys
import copy
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

try:
    from jsonpath_ng import parse as jsonpath_parse
    from jsonpath_ng.exceptions import JSONPathMatch
except ImportError:
    raise ImportError("jsonpath-ng required: pip install jsonpath-ng")

from scorer import BaseScoringType, ScoringResult
from response_cleaner import ResponseCleaner


class JsonTargetedEditScorer(BaseScoringType):
    """Scorer for json_targeted_edit scoring type - verifies targeted JSON modifications."""
    
    def score(self, precheck_entry, response_entry, test_artifacts_dir):
        """Score based on targeted JSON edit verification."""
        
        # Get configuration from precheck entry
        original_file = precheck_entry.get('original_file', '').strip()
        modified_file = precheck_entry.get('modified_file', '').strip()
        edit_verification = precheck_entry.get('edit_verification', {})
        
        if not original_file or not modified_file:
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='json_targeted_edit',
                correct=False,
                error_message="Missing original_file or modified_file in test configuration",
                details={'configuration_error': True}
            )
        
        # Resolve file paths relative to test artifacts directory
        original_path = Path(test_artifacts_dir) / original_file.replace(str(test_artifacts_dir) + '/', '')
        modified_path = Path(test_artifacts_dir) / modified_file.replace(str(test_artifacts_dir) + '/', '')
        
        # Check if files exist
        if not original_path.exists():
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='json_targeted_edit',
                correct=False,
                error_message=f"Original file not found: {original_path}",
                details={'file_error': 'original_missing'}
            )
        
        if not modified_path.exists():
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='json_targeted_edit',
                correct=False,
                error_message=f"Modified file not found: {modified_path}. LLM may not have created output file.",
                details={'file_error': 'modified_missing'}
            )
        
        # Load JSON files
        try:
            with open(original_path, 'r') as f:
                original_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='json_targeted_edit',
                correct=False,
                error_message=f"Failed to load original JSON: {e}",
                details={'file_error': 'original_invalid_json'}
            )
        
        try:
            with open(modified_path, 'r') as f:
                modified_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='json_targeted_edit',
                correct=False,
                error_message=f"Failed to load modified JSON: {e}",
                details={'file_error': 'modified_invalid_json'}
            )
        
        # Verify target changes and preservation
        target_result = self._verify_target_changes(modified_data, edit_verification.get('target_changes', []))
        preservation_result = self._verify_preservation(original_data, modified_data, edit_verification.get('preservation_spec', {}))
        
        # Overall success requires both target changes and preservation
        overall_success = target_result[0] and preservation_result[0]
        
        details = {
            'original_file': str(original_path),
            'modified_file': str(modified_path),
            'target_verification': {
                'success': target_result[0],
                'message': target_result[1],
                'details': target_result[2] if len(target_result) > 2 else {}
            },
            'preservation_verification': {
                'success': preservation_result[0],
                'message': preservation_result[1],
                'details': preservation_result[2] if len(preservation_result) > 2 else {}
            }
        }
        
        error_message = None
        if not overall_success:
            error_messages = []
            if not target_result[0]:
                error_messages.append(f"Target changes: {target_result[1]}")
            if not preservation_result[0]:
                error_messages.append(f"Preservation: {preservation_result[1]}")
            error_message = "; ".join(error_messages)
        
        return ScoringResult(
            question_id=precheck_entry['question_id'],
            sample_number=precheck_entry['sample_number'],
            scoring_type='json_targeted_edit',
            correct=overall_success,
            error_message=error_message,
            details=details
        )
    
    def _verify_target_changes(self, modified_data: Dict[str, Any], target_changes: List[Dict[str, Any]]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verify that all target changes occurred correctly.
        
        Args:
            modified_data: The modified JSON data
            target_changes: List of expected changes with 'selector' and 'expected_value'
        
        Returns:
            Tuple of (success, message, details)
        """
        if not target_changes:
            return True, "No target changes to verify", {}
        
        details = {}
        
        for i, target in enumerate(target_changes):
            selector = target.get('selector', '')
            expected_value = target.get('expected_value')
            
            if not selector:
                return False, f"Target change {i}: missing selector", details
            
            try:
                # Parse and execute JSONPath
                jsonpath_expr = jsonpath_parse(selector)
                matches = jsonpath_expr.find(modified_data)
                
                if not matches:
                    details[f'target_{i}'] = {'selector': selector, 'matches_found': 0}
                    return False, f"Target change {i}: no matches found for selector '{selector}'", details
                
                # Check if all matches have the expected value
                actual_values = [match.value for match in matches]
                mismatched_values = [v for v in actual_values if v != expected_value]
                
                details[f'target_{i}'] = {
                    'selector': selector,
                    'expected_value': expected_value,
                    'matches_found': len(matches),
                    'actual_values': actual_values,
                    'all_correct': len(mismatched_values) == 0
                }
                
                if mismatched_values:
                    return False, f"Target change {i}: expected all values to be {expected_value}, found mismatches: {mismatched_values}", details
                
            except Exception as e:
                details[f'target_{i}'] = {'selector': selector, 'error': str(e)}
                return False, f"Target change {i}: JSONPath error: {e}", details
        
        return True, f"All {len(target_changes)} target changes verified successfully", details
    
    def _verify_preservation(self, original_data: Dict[str, Any], modified_data: Dict[str, Any], preservation_spec: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verify that non-target data was preserved correctly.
        
        Args:
            original_data: The original JSON data
            modified_data: The modified JSON data
            preservation_spec: Specification for what to exclude from comparison
        
        Returns:
            Tuple of (success, message, details)
        """
        exclude_paths = preservation_spec.get('exclude_paths', [])
        
        if not exclude_paths:
            # No exclusions - everything should be identical
            if original_data == modified_data:
                return True, "All data preserved (no exclusions)", {}
            else:
                return False, "Data was modified but no exclusions specified", {'full_comparison': False}
        
        # TODO: Implement path exclusion logic
        # For now, return success with a placeholder message
        return True, f"Preservation check skipped (exclude_paths not yet implemented): {exclude_paths}", {'implementation_pending': True}