#!/usr/bin/env python3
"""
Test Results Visualizer
A CLI tool to visualize test results from JSON score files.

Usage: python visualize_cli_score.py <score_file.json> [--failures-only] [--no-color]
"""

import json
import sys
import argparse
from typing import Dict, Any

# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def colorize(text: str, color: str, use_color: bool = True) -> str:
    """Apply color to text if use_color is True."""
    if not use_color:
        return text
    return f"{color}{text}{Colors.RESET}"

def truncate_with_ellipsis(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis if longer than max_length."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_json_content(content: str, max_length: int = 200) -> str:
    """Format JSON content for display, with truncation."""
    try:
        # Try to parse and pretty-print JSON
        parsed = json.loads(content)
        formatted = json.dumps(parsed, separators=(',', ':'))
        return truncate_with_ellipsis(formatted, max_length)
    except:
        # If not valid JSON, just truncate the raw content
        return truncate_with_ellipsis(content, max_length)

def print_summary(data: Dict[str, Any], use_color: bool = True):
    """Print test results summary."""
    metadata = data.get('metadata', {})
    
    print(colorize("=== Test Results Summary ===", Colors.BOLD, use_color))
    print(f"Test ID: {metadata.get('test_id', 'Unknown')}")
    print(f"Timestamp: {metadata.get('timestamp', 'Unknown')}")
    
    total = metadata.get('total_questions', 0)
    correct = metadata.get('correct_answers', 0)
    accuracy = metadata.get('accuracy_percentage', 0)
    
    accuracy_color = Colors.GREEN if accuracy >= 80 else Colors.YELLOW if accuracy >= 60 else Colors.RED
    print(f"Total: {total} questions | Correct: {correct} | Accuracy: {colorize(f'{accuracy}%', accuracy_color, use_color)}")
    print()

def print_by_scoring_type(data: Dict[str, Any], use_color: bool = True):
    """Print results grouped by scoring type."""
    by_scoring = data.get('by_scoring_type', {})
    if not by_scoring:
        return
        
    print(colorize("=== By Question Type ===", Colors.BOLD, use_color))
    
    for scoring_type, results in by_scoring.items():
        correct = results.get('correct', 0)
        total = results.get('total', 0)
        percentage = (correct / total * 100) if total > 0 else 0
        
        percentage_color = Colors.GREEN if percentage == 100 else Colors.YELLOW if percentage >= 50 else Colors.RED
        status = colorize(f"{correct}/{total} ({percentage:.1f}%)", percentage_color, use_color)
        print(f"{scoring_type}: {status}")
    print()

def print_detailed_results(data: Dict[str, Any], failures_only: bool = False, use_color: bool = True):
    """Print detailed results for each test case."""
    detailed_results = data.get('detailed_results', [])
    if not detailed_results:
        return
        
    print(colorize("=== Detailed Results ===", Colors.BOLD, use_color))
    
    for result in detailed_results:
        question_id = result.get('question_id', 'Unknown')
        sample_number = result.get('sample_number', 'Unknown')
        scoring_type = result.get('scoring_type', 'Unknown')
        is_correct = result.get('correct', False)
        error_message = result.get('error_message')
        details = result.get('details', {})
        
        # Skip correct results if failures_only is True
        if failures_only and is_correct:
            continue
            
        # Format question identifier
        question_label = f"Q{question_id}.{sample_number} ({scoring_type})"
        
        # Status indicator
        if is_correct:
            status = colorize("✅ CORRECT", Colors.GREEN, use_color)
        else:
            status = colorize("❌ INCORRECT", Colors.RED, use_color)
            
        print(f"{question_label}: {status}")
        
        # Show error message if present
        if error_message:
            print(f"   Error: {colorize(error_message, Colors.RED, use_color)}")
        
        # Show expected vs actual for incorrect results
        if not is_correct and details:
            # Handle different detail formats
            expected = None
            actual = None
            
            if 'expected_content' in details:
                expected = details['expected_content']
            elif 'expected_raw' in details:
                expected = details['expected_raw']
            elif 'expected' in details:
                expected = details['expected']
                
            if 'actual_content' in details:
                actual = details['actual_content']
            elif 'actual_raw' in details:
                actual = details['actual_raw']
            elif 'actual' in details:
                actual = details['actual']
            elif 'actual_cleaned' in details:
                actual = details['actual_cleaned']
                
            if expected is not None:
                expected_formatted = format_json_content(str(expected))
                print(f"   Expected: {expected_formatted}")
                
            if actual is not None:
                actual_formatted = format_json_content(str(actual))
                print(f"   Actual: {actual_formatted}")
                
        print()  # Empty line between results

def main():
    parser = argparse.ArgumentParser(description='Visualize test results from JSON score files')
    parser.add_argument('score_file', help='Path to the JSON score file')
    parser.add_argument('--failures-only', '-f', action='store_true', 
                       help='Show only failed test cases')
    parser.add_argument('--no-color', action='store_true',
                       help='Disable colored output')
    
    args = parser.parse_args()
    
    # Read and parse the JSON file
    try:
        with open(args.score_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{args.score_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{args.score_file}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{args.score_file}': {e}", file=sys.stderr)
        sys.exit(1)
    
    use_color = not args.no_color and sys.stdout.isatty()
    
    # Print the visualized results
    print_summary(data, use_color)
    print_by_scoring_type(data, use_color)
    print_detailed_results(data, args.failures_only, use_color)

if __name__ == '__main__':
    main()