"""
Template Functions for the PICARD framework

Handles template function evaluation for file, CSV, SQLite and JSON content extraction.
"""
import csv
import json
import re
import sqlite3
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
            'csv_sum': self._csv_sum,
            'csv_avg': self._csv_avg,
            'csv_count': self._csv_count,
            'csv_sum_where': self._csv_sum_where,
            'csv_avg_where': self._csv_avg_where,
            'csv_count_where': self._csv_count_where,
            'sqlite_query': self._sqlite_query,
            'sqlite_value': self._sqlite_value,
            'json_path': self._json_path,
            'json_value': self._json_value,
            'json_count': self._json_count,
            'json_keys': self._json_keys,
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
    
    # CSV Aggregation Functions
    
    def _csv_sum(self, args: List[str], target_file_path: str = None) -> float:
        """Sum all numeric values in a column. Usage: {{csv_sum:column:path}}"""
        if len(args) != 2:
            raise TemplateFunctionError("csv_sum requires exactly 2 arguments: column_name, file_path")
        
        column = args[0]
        path = self._resolve_target_file(args[1], target_file_path)
        data = self._read_csv_data(path)
        
        if len(data) == 0:
            raise TemplateFunctionError("CSV file is empty")
        
        headers = data[0]
        try:
            column_index = headers.index(column)
        except ValueError:
            raise TemplateFunctionError(f"Column '{column}' not found in CSV. Available headers: {headers}")
        
        total = 0
        count = 0
        for row in data[1:]:  # Skip header
            if column_index < len(row) and row[column_index].strip():
                try:
                    total += float(row[column_index])
                    count += 1
                except ValueError:
                    # Skip non-numeric values
                    continue
        
        return total
    
    def _csv_avg(self, args: List[str], target_file_path: str = None) -> float:
        """Average all numeric values in a column. Usage: {{csv_avg:column:path}}"""
        if len(args) != 2:
            raise TemplateFunctionError("csv_avg requires exactly 2 arguments: column_name, file_path")
        
        column = args[0]
        path = self._resolve_target_file(args[1], target_file_path)
        data = self._read_csv_data(path)
        
        if len(data) == 0:
            raise TemplateFunctionError("CSV file is empty")
        
        headers = data[0]
        try:
            column_index = headers.index(column)
        except ValueError:
            raise TemplateFunctionError(f"Column '{column}' not found in CSV. Available headers: {headers}")
        
        total = 0
        count = 0
        for row in data[1:]:  # Skip header
            if column_index < len(row) and row[column_index].strip():
                try:
                    total += float(row[column_index])
                    count += 1
                except ValueError:
                    # Skip non-numeric values
                    continue
        
        if count == 0:
            raise TemplateFunctionError(f"No numeric values found in column '{column}'")
        
        return total / count
    
    def _csv_count(self, args: List[str], target_file_path: str = None) -> int:
        """Count non-empty values in a column. Usage: {{csv_count:column:path}}"""
        if len(args) != 2:
            raise TemplateFunctionError("csv_count requires exactly 2 arguments: column_name, file_path")
        
        column = args[0]
        path = self._resolve_target_file(args[1], target_file_path)
        data = self._read_csv_data(path)
        
        if len(data) == 0:
            raise TemplateFunctionError("CSV file is empty")
        
        headers = data[0]
        try:
            column_index = headers.index(column)
        except ValueError:
            raise TemplateFunctionError(f"Column '{column}' not found in CSV. Available headers: {headers}")
        
        count = 0
        for row in data[1:]:  # Skip header
            if column_index < len(row) and row[column_index].strip():
                count += 1
        
        return count
    
    def _apply_filter(self, value: str, operator: str, filter_value: str) -> bool:
        """Apply filter operation to compare two values."""
        if not value.strip():
            return False
        
        # Try numeric comparison first
        try:
            num_value = float(value)
            num_filter = float(filter_value)
            
            if operator == '>':
                return num_value > num_filter
            elif operator == '<':
                return num_value < num_filter
            elif operator == '>=':
                return num_value >= num_filter
            elif operator == '<=':
                return num_value <= num_filter
            elif operator == '==':
                return num_value == num_filter
            elif operator == '!=':
                return num_value != num_filter
        except ValueError:
            # Fall back to string comparison
            pass
        
        # String operations
        if operator == '==':
            return value == filter_value
        elif operator == '!=':
            return value != filter_value
        elif operator == 'contains':
            return filter_value in value
        elif operator == 'startswith':
            return value.startswith(filter_value)
        elif operator == 'endswith':
            return value.endswith(filter_value)
        elif operator in ['>', '<', '>=', '<=']:
            # String comparison for non-numeric values
            if operator == '>':
                return value > filter_value
            elif operator == '<':
                return value < filter_value
            elif operator == '>=':
                return value >= filter_value
            elif operator == '<=':
                return value <= filter_value
        
        raise TemplateFunctionError(f"Unsupported operator: {operator}")
    
    def _csv_sum_where(self, args: List[str], target_file_path: str = None) -> float:
        """Sum values in column where filter condition is met. Usage: {{csv_sum_where:column:filter_column:operator:value:path}}"""
        if len(args) != 5:
            raise TemplateFunctionError("csv_sum_where requires exactly 5 arguments: column, filter_column, operator, value, file_path")
        
        column, filter_column, operator, filter_value, path = args
        path = self._resolve_target_file(path, target_file_path)
        data = self._read_csv_data(path)
        
        if len(data) == 0:
            raise TemplateFunctionError("CSV file is empty")
        
        headers = data[0]
        try:
            column_index = headers.index(column)
            filter_column_index = headers.index(filter_column)
        except ValueError as e:
            raise TemplateFunctionError(f"Column not found in CSV. Available headers: {headers}. Error: {e}")
        
        total = 0
        for row in data[1:]:  # Skip header
            if (column_index < len(row) and filter_column_index < len(row) and 
                row[column_index].strip() and row[filter_column_index].strip()):
                
                if self._apply_filter(row[filter_column_index], operator, filter_value):
                    try:
                        total += float(row[column_index])
                    except ValueError:
                        # Skip non-numeric values
                        continue
        
        return total
    
    def _csv_avg_where(self, args: List[str], target_file_path: str = None) -> float:
        """Average values in column where filter condition is met. Usage: {{csv_avg_where:column:filter_column:operator:value:path}}"""
        if len(args) != 5:
            raise TemplateFunctionError("csv_avg_where requires exactly 5 arguments: column, filter_column, operator, value, file_path")
        
        column, filter_column, operator, filter_value, path = args
        path = self._resolve_target_file(path, target_file_path)
        data = self._read_csv_data(path)
        
        if len(data) == 0:
            raise TemplateFunctionError("CSV file is empty")
        
        headers = data[0]
        try:
            column_index = headers.index(column)
            filter_column_index = headers.index(filter_column)
        except ValueError as e:
            raise TemplateFunctionError(f"Column not found in CSV. Available headers: {headers}. Error: {e}")
        
        total = 0
        count = 0
        for row in data[1:]:  # Skip header
            if (column_index < len(row) and filter_column_index < len(row) and 
                row[column_index].strip() and row[filter_column_index].strip()):
                
                if self._apply_filter(row[filter_column_index], operator, filter_value):
                    try:
                        total += float(row[column_index])
                        count += 1
                    except ValueError:
                        # Skip non-numeric values
                        continue
        
        if count == 0:
            raise TemplateFunctionError(f"No numeric values found in column '{column}' matching filter criteria")
        
        return total / count
    
    def _csv_count_where(self, args: List[str], target_file_path: str = None) -> int:
        """Count rows where filter condition is met. Usage: {{csv_count_where:column:filter_column:operator:value:path}}"""
        if len(args) != 5:
            raise TemplateFunctionError("csv_count_where requires exactly 5 arguments: column, filter_column, operator, value, file_path")
        
        column, filter_column, operator, filter_value, path = args
        path = self._resolve_target_file(path, target_file_path)
        data = self._read_csv_data(path)
        
        if len(data) == 0:
            raise TemplateFunctionError("CSV file is empty")
        
        headers = data[0]
        try:
            column_index = headers.index(column)
            filter_column_index = headers.index(filter_column)
        except ValueError as e:
            raise TemplateFunctionError(f"Column not found in CSV. Available headers: {headers}. Error: {e}")
        
        count = 0
        for row in data[1:]:  # Skip header
            if (column_index < len(row) and filter_column_index < len(row) and 
                row[column_index].strip() and row[filter_column_index].strip()):
                
                if self._apply_filter(row[filter_column_index], operator, filter_value):
                    count += 1
        
        return count
    
    # SQLite-specific extraction functions
    
    def _sqlite_query(self, args: List[str], target_file_path: str = None) -> str:
        """Execute arbitrary SQL query and return first result. Usage: {{sqlite_query:SELECT name FROM users:path}}"""
        if len(args) != 2:
            raise TemplateFunctionError("sqlite_query requires exactly 2 arguments: sql_query, file_path")
        
        sql_query = args[0]
        path = self._resolve_target_file(args[1], target_file_path)
        
        file_path = self._resolve_path(path)
        if not file_path.exists():
            raise TemplateFunctionError(f"SQLite file not found: {file_path}")
        
        try:
            conn = sqlite3.connect(str(file_path))
            try:
                cursor = conn.execute(sql_query)
                result = cursor.fetchone()
                
                if result is None:
                    raise TemplateFunctionError(f"SQL query returned no results: {sql_query}")
                
                # Return first column of first row
                return str(result[0]) if result[0] is not None else ""
                
            finally:
                conn.close()
                
        except sqlite3.Error as e:
            raise TemplateFunctionError(f"SQLite error executing '{sql_query}': {e}")
        except Exception as e:
            raise TemplateFunctionError(f"Error executing SQLite query '{sql_query}': {e}")
    
    def _sqlite_value(self, args: List[str], target_file_path: str = None) -> str:
        """Get value by row and column from first table. Usage: {{sqlite_value:row:column:path}} or {{sqlite_value:row:column:table:path}}"""
        if len(args) not in [3, 4]:
            raise TemplateFunctionError("sqlite_value requires 3 or 4 arguments: row, column, [table], file_path")
        
        try:
            row = int(args[0])
            column = args[1]  # Can be column name or index
        except ValueError:
            raise TemplateFunctionError(f"Invalid row number: {args[0]}")
        
        if len(args) == 4:
            table_name = args[2]
            path = self._resolve_target_file(args[3], target_file_path)
        else:
            table_name = None
            path = self._resolve_target_file(args[2], target_file_path)
        
        file_path = self._resolve_path(path)
        if not file_path.exists():
            raise TemplateFunctionError(f"SQLite file not found: {file_path}")
        
        try:
            conn = sqlite3.connect(str(file_path))
            try:
                # If no table specified, get the first table
                if table_name is None:
                    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    if not tables:
                        raise TemplateFunctionError("No tables found in SQLite database")
                    table_name = tables[0][0]
                
                # Try to parse column as integer index first
                try:
                    column_index = int(column)
                    # Get column names to validate index
                    cursor = conn.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    if column_index < 0 or column_index >= len(columns):
                        raise TemplateFunctionError(f"Column index {column_index} out of range (table has {len(columns)} columns)")
                    column_name = columns[column_index][1]  # Column name is at index 1
                except ValueError:
                    # Column is a name, not an index
                    column_name = column
                
                # Execute query to get the value
                sql_query = f"SELECT {column_name} FROM {table_name} LIMIT 1 OFFSET {row}"
                cursor = conn.execute(sql_query)
                result = cursor.fetchone()
                
                if result is None:
                    raise TemplateFunctionError(f"Row {row} not found in table {table_name}")
                
                return str(result[0]) if result[0] is not None else ""
                
            finally:
                conn.close()
                
        except sqlite3.Error as e:
            raise TemplateFunctionError(f"SQLite error: {e}")
        except Exception as e:
            raise TemplateFunctionError(f"Error accessing SQLite database: {e}")
    
    # JSON-specific extraction functions
    
    def _read_json_data(self, path: str) -> Any:
        """Read JSON file and return parsed data."""
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            raise TemplateFunctionError(f"JSON file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise TemplateFunctionError(f"Invalid JSON in file {file_path}: {e}")
        except Exception as e:
            raise TemplateFunctionError(f"Error reading JSON file {file_path}: {e}")
    
    def _json_path(self, args: List[str], target_file_path: str = None) -> str:
        """Extract value using JSONPath-like syntax. Usage: {{json_path:$.users[0].name:path}}"""
        if len(args) != 2:
            raise TemplateFunctionError("json_path requires exactly 2 arguments: path_expression, file_path")
        
        path_expr = args[0]
        file_path = self._resolve_target_file(args[1], target_file_path)
        data = self._read_json_data(file_path)
        
        try:
            result = self._evaluate_json_path(data, path_expr)
            return str(result) if result is not None else ""
        except Exception as e:
            raise TemplateFunctionError(f"Error evaluating JSONPath '{path_expr}': {e}")
    
    def _json_value(self, args: List[str], target_file_path: str = None) -> str:
        """Get value by simple key path. Usage: {{json_value:key1.key2[0]:path}}"""
        if len(args) != 2:
            raise TemplateFunctionError("json_value requires exactly 2 arguments: key_path, file_path")
        
        key_path = args[0]
        file_path = self._resolve_target_file(args[1], target_file_path)
        data = self._read_json_data(file_path)
        
        try:
            result = self._navigate_json_keys(data, key_path)
            return str(result) if result is not None else ""
        except Exception as e:
            raise TemplateFunctionError(f"Error accessing JSON key '{key_path}': {e}")
    
    def _json_count(self, args: List[str], target_file_path: str = None) -> int:
        """Count elements in JSON array or object keys. Usage: {{json_count:$.users:path}}"""
        if len(args) not in [1, 2]:
            raise TemplateFunctionError("json_count requires 1 or 2 arguments: [path_expression], file_path")
        
        if len(args) == 1:
            # Count root level
            path_expr = "$"
            file_path = self._resolve_target_file(args[0], target_file_path)
        else:
            path_expr = args[0]
            file_path = self._resolve_target_file(args[1], target_file_path)
        
        data = self._read_json_data(file_path)
        
        try:
            if path_expr == "$":
                target = data
            else:
                target = self._evaluate_json_path(data, path_expr)
            
            if isinstance(target, list):
                return len(target)
            elif isinstance(target, dict):
                return len(target.keys())
            else:
                raise TemplateFunctionError(f"Cannot count non-array/non-object value: {type(target)}")
        except Exception as e:
            raise TemplateFunctionError(f"Error counting JSON elements at '{path_expr}': {e}")
    
    def _json_keys(self, args: List[str], target_file_path: str = None) -> str:
        """Get object keys as comma-separated string. Usage: {{json_keys:$.user:path}}"""
        if len(args) not in [1, 2]:
            raise TemplateFunctionError("json_keys requires 1 or 2 arguments: [path_expression], file_path")
        
        if len(args) == 1:
            # Get root level keys
            path_expr = "$"
            file_path = self._resolve_target_file(args[0], target_file_path)
        else:
            path_expr = args[0]
            file_path = self._resolve_target_file(args[1], target_file_path)
        
        data = self._read_json_data(file_path)
        
        try:
            if path_expr == "$":
                target = data
            else:
                target = self._evaluate_json_path(data, path_expr)
            
            if isinstance(target, dict):
                return ','.join(target.keys())
            else:
                raise TemplateFunctionError(f"Cannot get keys from non-object value: {type(target)}")
        except Exception as e:
            raise TemplateFunctionError(f"Error getting JSON keys at '{path_expr}': {e}")
    
    def _evaluate_json_path(self, data: Any, path_expr: str) -> Any:
        """Evaluate simple JSONPath-like expressions."""
        # Remove leading $ if present
        if path_expr.startswith('$'):
            path_expr = path_expr[1:]
        
        if not path_expr or path_expr == '.':
            return data
        
        # Split path and navigate
        if path_expr.startswith('.'):
            path_expr = path_expr[1:]
        
        return self._navigate_json_keys(data, path_expr)
    
    def _navigate_json_keys(self, data: Any, key_path: str) -> Any:
        """Navigate JSON data using dot notation and array indices."""
        if not key_path:
            return data
        
        current = data
        
        # Split path by dots, but handle array indices
        parts = []
        current_part = ""
        bracket_depth = 0
        
        for char in key_path:
            if char == '[':
                bracket_depth += 1
                current_part += char
            elif char == ']':
                bracket_depth -= 1
                current_part += char
            elif char == '.' and bracket_depth == 0:
                if current_part:
                    parts.append(current_part)
                current_part = ""
            else:
                current_part += char
        
        if current_part:
            parts.append(current_part)
        
        # Navigate through each part
        for part in parts:
            # Check for array index notation
            if '[' in part and ']' in part:
                # Extract key and index
                key_part = part[:part.index('[')]
                index_part = part[part.index('[') + 1:part.rindex(']')]
                
                # Navigate to the key first (if not empty)
                if key_part:
                    if not isinstance(current, dict) or key_part not in current:
                        raise TemplateFunctionError(f"Key '{key_part}' not found in JSON object")
                    current = current[key_part]
                
                # Then navigate to the array index
                try:
                    index = int(index_part)
                    if not isinstance(current, list):
                        raise TemplateFunctionError(f"Cannot index non-array value: {type(current)}")
                    if index < 0 or index >= len(current):
                        raise TemplateFunctionError(f"Array index {index} out of range (length: {len(current)})")
                    current = current[index]
                except ValueError:
                    raise TemplateFunctionError(f"Invalid array index: {index_part}")
            else:
                # Simple key navigation
                if not isinstance(current, dict):
                    raise TemplateFunctionError(f"Cannot access key '{part}' on non-object value: {type(current)}")
                if part not in current:
                    raise TemplateFunctionError(f"Key '{part}' not found in JSON object")
                current = current[part]
        
        return current


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
        csv_content = "name,age,salary,department,status\nJohn,25,50000,Engineering,active\nAlice,30,60000,Engineering,active\nBob,35,70000,Sales,inactive\nCarol,28,55000,Marketing,active"
        csv_file.write_text(csv_content)
        
        # Test template functions
        tf = TemplateFunctions(temp_dir)
        
        test_cases = [
            ("{{file_line:3:test.txt}}", "Line 3 with words"),
            ("{{file_word:4:test.txt}}", "2"),
            ("{{file_line_count:test.txt}}", "5"),
            ("{{file_word_count:test.txt}}", "12"),
            ("{{csv_cell:1:0:test.csv}}", "John"),
            ("{{csv_cell:3:4:test.csv}}", "inactive"),
            ("{{csv_row:1:test.csv}}", "John,25,50000,Engineering,active"),
            ("{{csv_column:name:test.csv}}", "John,Alice,Bob,Carol"),
            ("{{csv_value:0:age:test.csv}}", "25"),
            ("{{csv_value:2:department:test.csv}}", "Sales"),
            # New aggregation functions
            ("{{csv_sum:age:test.csv}}", "118.0"),
            ("{{csv_avg:salary:test.csv}}", "58750.0"),
            ("{{csv_count:name:test.csv}}", "4"),
            # New filtered aggregation functions
            ("{{csv_sum_where:salary:department:==:Engineering:test.csv}}", "110000.0"),
            ("{{csv_avg_where:age:status:==:active:test.csv}}", "27.666666666666668"),
            ("{{csv_count_where:name:department:contains:ing:test.csv}}", "3"),
            ("{{csv_sum_where:salary:age:>:30:test.csv}}", "70000.0"),
        ]
        
        # Create test JSON file for JSON function testing
        json_file = temp_path / "test.json"
        json_data = {
            "users": [
                {"id": 1, "name": "John", "age": 25, "active": True},
                {"id": 2, "name": "Alice", "age": 30, "active": False},
                {"id": 3, "name": "Bob", "age": 35, "active": True}
            ],
            "metadata": {
                "total": 3,
                "version": "1.0"
            },
            "config": {
                "settings": {
                    "debug": True,
                    "timeout": 30
                }
            }
        }
        json_file.write_text(json.dumps(json_data, indent=2))
        
        # JSON function test cases
        json_test_cases = [
            ("{{json_path:$.users[0].name:test.json}}", "John"),
            ("{{json_path:$.users[1].age:test.json}}", "30"),
            ("{{json_value:metadata.total:test.json}}", "3"),
            ("{{json_value:config.settings.debug:test.json}}", "True"),
            ("{{json_count:$.users:test.json}}", "3"),
            ("{{json_count:$.metadata:test.json}}", "2"),
            ("{{json_keys:$.metadata:test.json}}", "total,version"),
            ("{{json_keys:$.config.settings:test.json}}", "debug,timeout"),
        ]
        
        print("\nTesting JSON template functions:")
        for template, expected in json_test_cases:
            try:
                result = tf.evaluate_all_functions(template)
                status = "✅" if str(result) == expected else "❌"
                print(f"  {status} {template} → {result} (expected: {expected})")
            except Exception as e:
                print(f"  ❌ {template} → ERROR: {e}")
        
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
