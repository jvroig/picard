"""
Template Functions for QwenSense LLM Benchmarking Tool

Handles template function evaluation for file and CSV content extraction.
Functions like {{file_line:3:path}}, {{csv_cell:row:column:path}}, etc.
"""
import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class TemplateFunctionError(Exception):
    """Raised when template function evaluation fails."""
    pass


class TemplateFunctions:
    """Handles evaluation of template functions for content extraction."""
    
    def __init__(self, base_dir: str = None):
        """
        Initialize template functions processor.
        
        Args:
            base_dir: Base directory for resolving relative file paths
        """
        if base_dir is None:
            base_dir = Path.cwd()
        self.base_dir = Path(base_dir)
    
    def evaluate_all_functions(self, text: str, target_file_path: str = None) -> str:
        """
        Evaluate all template functions in the given text.
        
        Args:
            text: Text containing template functions like {{file_line:3:path}}
            target_file_path: Path to substitute for TARGET_FILE keyword (optional)
            
        Returns:
            Text with all template functions replaced with their results
        """
        if not text:
            return text
        
        # Pattern to match template functions: {{function_name:args}}
        pattern = r'\{\{([^:]+):([^}]+)\}\}'
        
        def replace_function(match):
            function_name = match.group(1).strip()
            args_str = match.group(2).strip()
            args = [arg.strip() for arg in args_str.split(':')]
            
            try:
                return str(self.evaluate_function(function_name, args, target_file_path))
            except Exception as e:
                raise TemplateFunctionError(f"Error evaluating {{{{{function_name}:{args_str}}}}}: {e}")
        
        try:
            result = re.sub(pattern, replace_function, text)
            return result
        except TemplateFunctionError:
            raise
        except Exception as e:
            raise TemplateFunctionError(f"Error processing template functions in '{text}': {e}")
    
    def evaluate_function(self, function_name: str, args: List[str], target_file_path: str = None) -> Any:
        """
        Evaluate a single template function.
        
        Args:
            function_name: Name of the function (e.g., 'file_line', 'csv_cell')
            args: List of function arguments
            target_file_path: Path to substitute for TARGET_FILE keyword (optional)
            
        Returns:
            Result of the function evaluation
        """
        # Map function names to methods
        function_map = {
            'file_line': self._file_line,
            'file_word': self._file_word,
            'file_line_count': self._file_line_count,
            'file_word_count': self._file_word_count,
            'csv_cell': self._csv_cell,
            'csv_row': self._csv_row,
            'csv_column': self._csv_column,
            'csv_value': self._csv_value,
        }
        
        if function_name not in function_map:
            raise TemplateFunctionError(f"Unknown template function: {function_name}")
        
        return function_map[function_name](args, target_file_path)
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve a file path relative to base directory."""
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = self.base_dir / file_path
        return file_path
    
    def _resolve_target_file(self, path: str, target_file_path: str = None) -> str:
        """
        Resolve TARGET_FILE keyword to actual target file path.
        
        Args:
            path: Path that may contain TARGET_FILE keyword
            target_file_path: Actual target file path to substitute
            
        Returns:
            Resolved path with TARGET_FILE replaced if applicable
        """
        if path == "TARGET_FILE" and target_file_path:
            return target_file_path
        return path
    
    def _read_file_lines(self, path: str) -> List[str]:
        """Read file and return list of lines (without newlines)."""
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            raise TemplateFunctionError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [line.rstrip('\n\r') for line in f.readlines()]
        except Exception as e:
            raise TemplateFunctionError(f"Error reading file {file_path}: {e}")
    
    def _read_file_text(self, path: str) -> str:
        """Read entire file as text."""
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            raise TemplateFunctionError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise TemplateFunctionError(f"Error reading file {file_path}: {e}")
    
    # File content extraction functions
    
    def _file_line(self, args: List[str], target_file_path: str = None) -> str:
        """Get specific line number from file. Usage: {{file_line:N:path}}"""
        if len(args) != 2:
            raise TemplateFunctionError("file_line requires exactly 2 arguments: line_number, file_path")
        
        try:
            line_number = int(args[0])
        except ValueError:
            raise TemplateFunctionError(f"Invalid line number: {args[0]}")
        
        path = self._resolve_target_file(args[1], target_file_path)
        lines = self._read_file_lines(path)
        
        # Convert to 0-based indexing
        if line_number < 1 or line_number > len(lines):
            raise TemplateFunctionError(f"Line number {line_number} out of range (file has {len(lines)} lines)")
        
        return lines[line_number - 1]
    
    def _file_word(self, args: List[str], target_file_path: str = None) -> str:
        """Get Nth word from entire file. Usage: {{file_word:N:path}}"""
        if len(args) != 2:
            raise TemplateFunctionError("file_word requires exactly 2 arguments: word_number, file_path")
        
        try:
            word_number = int(args[0])
        except ValueError:
            raise TemplateFunctionError(f"Invalid word number: {args[0]}")
        
        path = self._resolve_target_file(args[1], target_file_path)
        text = self._read_file_text(path)
        words = text.split()
        
        # Convert to 0-based indexing
        if word_number < 1 or word_number > len(words):
            raise TemplateFunctionError(f"Word number {word_number} out of range (file has {len(words)} words)")
        
        return words[word_number - 1]
    
    def _file_line_count(self, args: List[str], target_file_path: str = None) -> int:
        """Count total lines in file. Usage: {{file_line_count:path}}"""
        if len(args) != 1:
            raise TemplateFunctionError("file_line_count requires exactly 1 argument: file_path")
        
        path = self._resolve_target_file(args[0], target_file_path)
        lines = self._read_file_lines(path)
        return len(lines)
    
    def _file_word_count(self, args: List[str], target_file_path: str = None) -> int:
        """Count total words in file. Usage: {{file_word_count:path}}"""
        if len(args) != 1:
            raise TemplateFunctionError("file_word_count requires exactly 1 argument: file_path")
        
        path = self._resolve_target_file(args[0], target_file_path)
        text = self._read_file_text(path)
        words = text.split()
        return len(words)
    
    # CSV-specific extraction functions
    
    def _read_csv_data(self, path: str) -> List[List[str]]:
        """Read CSV file and return list of rows."""
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            raise TemplateFunctionError(f"CSV file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                return list(reader)
        except Exception as e:
            raise TemplateFunctionError(f"Error reading CSV file {file_path}: {e}")
    
    def _csv_cell(self, args: List[str], target_file_path: str = None) -> str:
        """Get cell at row N, column M (0-indexed). Usage: {{csv_cell:row:column:path}}"""
        if len(args) != 3:
            raise TemplateFunctionError("csv_cell requires exactly 3 arguments: row, column, file_path")
        
        try:
            row = int(args[0])
            column = int(args[1])
        except ValueError:
            raise TemplateFunctionError(f"Invalid row/column numbers: {args[0]}, {args[1]}")
        
        path = self._resolve_target_file(args[2], target_file_path)
        data = self._read_csv_data(path)
        
        if row < 0 or row >= len(data):
            raise TemplateFunctionError(f"Row {row} out of range (CSV has {len(data)} rows)")
        
        if column < 0 or column >= len(data[row]):
            raise TemplateFunctionError(f"Column {column} out of range (row {row} has {len(data[row])} columns)")
        
        return data[row][column]
    
    def _csv_row(self, args: List[str], target_file_path: str = None) -> str:
        """Get entire row N as comma-separated string. Usage: {{csv_row:N:path}}"""
        if len(args) != 2:
            raise TemplateFunctionError("csv_row requires exactly 2 arguments: row_number, file_path")
        
        try:
            row = int(args[0])
        except ValueError:
            raise TemplateFunctionError(f"Invalid row number: {args[0]}")
        
        path = self._resolve_target_file(args[1], target_file_path)
        data = self._read_csv_data(path)
        
        if row < 0 or row >= len(data):
            raise TemplateFunctionError(f"Row {row} out of range (CSV has {len(data)} rows)")
        
        return ','.join(data[row])
    
    def _csv_column(self, args: List[str], target_file_path: str = None) -> str:
        """Get entire column by header name as comma-separated string. Usage: {{csv_column:header:path}}"""
        if len(args) != 2:
            raise TemplateFunctionError("csv_column requires exactly 2 arguments: header_name, file_path")
        
        header = args[0]
        path = self._resolve_target_file(args[1], target_file_path)
        data = self._read_csv_data(path)
        
        if len(data) == 0:
            raise TemplateFunctionError("CSV file is empty")
        
        headers = data[0]
        try:
            column_index = headers.index(header)
        except ValueError:
            raise TemplateFunctionError(f"Header '{header}' not found in CSV. Available headers: {headers}")
        
        # Extract column values (skip header row)
        column_values = []
        for row in data[1:]:
            if column_index < len(row):
                column_values.append(row[column_index])
            else:
                column_values.append('')  # Handle rows with missing columns
        
        return ','.join(column_values)
    
    def _csv_value(self, args: List[str], target_file_path: str = None) -> str:
        """Get cell by row number and column header. Usage: {{csv_value:row:header:path}}"""
        if len(args) != 3:
            raise TemplateFunctionError("csv_value requires exactly 3 arguments: row_number, header_name, file_path")
        
        try:
            row = int(args[0])
        except ValueError:
            raise TemplateFunctionError(f"Invalid row number: {args[0]}")
        
        header = args[1]
        path = self._resolve_target_file(args[2], target_file_path)
        data = self._read_csv_data(path)
        
        if len(data) == 0:
            raise TemplateFunctionError("CSV file is empty")
        
        headers = data[0]
        try:
            column_index = headers.index(header)
        except ValueError:
            raise TemplateFunctionError(f"Header '{header}' not found in CSV. Available headers: {headers}")
        
        # Row is relative to data rows (excluding header), so add 1
        data_row_index = row + 1
        if data_row_index < 1 or data_row_index >= len(data):
            raise TemplateFunctionError(f"Row {row} out of range (CSV has {len(data)-1} data rows)")
        
        if column_index >= len(data[data_row_index]):
            return ''  # Handle missing column
        
        return data[data_row_index][column_index]


def main():
    """Test the TemplateFunctions functionality."""
    import tempfile
    import os
    
    # Create temporary test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test text file
        test_file = temp_path / "test.txt"
        test_content = "Line 1\nLine 2\nLine 3 with words\nLine 4\nFinal line"
        test_file.write_text(test_content)
        
        # Create test CSV file
        csv_file = temp_path / "test.csv"
        csv_content = "name,age,city\nJohn,25,Boston\nAlice,30,Seattle\nBob,35,Denver"
        csv_file.write_text(csv_content)
        
        # Test template functions
        tf = TemplateFunctions(temp_dir)
        
        test_cases = [
            ("{{file_line:3:test.txt}}", "Line 3 with words"),
            ("{{file_word:4:test.txt}}", "2"),
            ("{{file_line_count:test.txt}}", "5"),
            ("{{file_word_count:test.txt}}", "12"),
            ("{{csv_cell:1:0:test.csv}}", "John"),
            ("{{csv_cell:2:2:test.csv}}", "Seattle"),
            ("{{csv_row:1:test.csv}}", "John,25,Boston"),
            ("{{csv_column:name:test.csv}}", "John,Alice,Bob"),
            ("{{csv_value:0:age:test.csv}}", "25"),
            ("{{csv_value:2:city:test.csv}}", "Denver"),
        ]
        
        print("Testing template functions:")
        for template, expected in test_cases:
            try:
                result = tf.evaluate_all_functions(template)
                status = "✅" if str(result) == expected else "❌"
                print(f"  {status} {template} → {result} (expected: {expected})")
            except Exception as e:
                print(f"  ❌ {template} → ERROR: {e}")


if __name__ == "__main__":
    main()
