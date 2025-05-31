"""
File Generator Infrastructure for QwenSense LLM Benchmarking Tool

Handles dynamic file generation including lorem ipsum content and CSV data.
Supports {{lorem:20l}}, {{lorem:5p}}, {{lorem:10s}} style content generation.
"""
import csv
import random
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod


class FileGeneratorError(Exception):
    """Raised when file generation fails."""
    pass


class LoremGenerator:
    """Generates lorem ipsum style content."""
    
    def __init__(self):
        # Lorem ipsum word pool - mix of classic and modern words
        self.words = [
            'lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 'adipiscing', 'elit',
            'sed', 'do', 'eiusmod', 'tempor', 'incididunt', 'ut', 'labore', 'et', 'dolore',
            'magna', 'aliqua', 'enim', 'ad', 'minim', 'veniam', 'quis', 'nostrud',
            'exercitation', 'ullamco', 'laboris', 'nisi', 'aliquip', 'ex', 'ea', 'commodo',
            'consequat', 'duis', 'aute', 'irure', 'in', 'reprehenderit', 'voluptate',
            'velit', 'esse', 'cillum', 'fugiat', 'nulla', 'pariatur', 'excepteur', 'sint',
            'occaecat', 'cupidatat', 'non', 'proident', 'sunt', 'culpa', 'qui', 'officia',
            'deserunt', 'mollit', 'anim', 'id', 'est', 'laborum', 'at', 'vero', 'eos',
            'accusamus', 'accusantium', 'doloremque', 'laudantium', 'totam', 'rem',
            'aperiam', 'eaque', 'ipsa', 'quae', 'ab', 'illo', 'inventore', 'veritatis',
            'quasi', 'architecto', 'beatae', 'vitae', 'dicta', 'explicabo', 'nemo',
            'ipsam', 'quia', 'voluptas', 'aspernatur', 'odit', 'aut', 'fugit', 'sequi',
            'nesciunt', 'neque', 'porro', 'quisquam', 'dolorem', 'magnam', 'numquam'
        ]
        
        # Sentence connectors and punctuation
        self.connectors = [', ', '. ', ', and ', ', but ', ', or ', '. Furthermore, ', 
                          '. However, ', '. Moreover, ', '. Additionally, ']
    
    def generate_words(self, count: int) -> str:
        """Generate a sequence of random words."""
        if count <= 0:
            return ""
        return ' '.join(random.choices(self.words, k=count))
    
    def generate_sentence(self, min_words: int = 8, max_words: int = 15) -> str:
        """Generate a single sentence."""
        word_count = random.randint(min_words, max_words)
        words = random.choices(self.words, k=word_count)
        
        # Capitalize first word
        if words:
            words[0] = words[0].capitalize()
        
        sentence = ' '.join(words)
        return sentence + '.'
    
    def generate_sentences(self, count: int) -> str:
        """Generate multiple sentences."""
        if count <= 0:
            return ""
        
        sentences = []
        for _ in range(count):
            sentences.append(self.generate_sentence())
        
        return ' '.join(sentences)
    
    def generate_paragraph(self, min_sentences: int = 4, max_sentences: int = 8) -> str:
        """Generate a paragraph with multiple sentences."""
        sentence_count = random.randint(min_sentences, max_sentences)
        return self.generate_sentences(sentence_count)
    
    def generate_lines(self, count: int) -> str:
        """Generate content as distinct lines."""
        if count <= 0:
            return ""
        
        lines = []
        for _ in range(count):
            # Each line is a sentence
            lines.append(self.generate_sentence())
        
        return '\n'.join(lines)
    
    def generate_paragraphs(self, count: int) -> str:
        """Generate multiple paragraphs."""
        if count <= 0:
            return ""
        
        paragraphs = []
        for _ in range(count):
            paragraphs.append(self.generate_paragraph())
        
        return '\n\n'.join(paragraphs)


class DataGenerator:
    """Generates realistic random data for CSV files."""
    
    def __init__(self):
        # Data pools for different field types
        self.first_names = [
            'John', 'Jane', 'Michael', 'Sarah', 'David', 'Lisa', 'Robert', 'Emily',
            'James', 'Amanda', 'Christopher', 'Jessica', 'Daniel', 'Ashley', 'Matthew',
            'Jennifer', 'Anthony', 'Elizabeth', 'Mark', 'Deborah', 'Donald', 'Dorothy',
            'Steven', 'Lisa', 'Paul', 'Nancy', 'Andrew', 'Karen', 'Joshua', 'Betty'
        ]
        
        self.last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
            'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
            'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
            'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark',
            'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young', 'Allen', 'King'
        ]
        
        self.cities = [
            'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia',
            'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville',
            'Fort Worth', 'Columbus', 'Charlotte', 'San Francisco', 'Indianapolis',
            'Seattle', 'Denver', 'Washington', 'Boston', 'Nashville', 'Baltimore',
            'Louisville', 'Portland', 'Oklahoma City', 'Milwaukee', 'Las Vegas',
            'Albuquerque', 'Tucson', 'Fresno', 'Sacramento', 'Kansas City', 'Mesa'
        ]
        
        self.companies = [
            'Acme Corp', 'Global Industries', 'Tech Solutions', 'Dynamic Systems',
            'Innovation Labs', 'Premier Group', 'Elite Services', 'Advanced Tech',
            'Modern Solutions', 'Future Corp', 'Digital Dynamics', 'Smart Systems',
            'Optimal Solutions', 'Peak Performance', 'Alpha Industries', 'Beta Corp',
            'Gamma Systems', 'Delta Tech', 'Epsilon Group', 'Zeta Solutions'
        ]
        
        self.products = [
            'Widget Pro', 'Super Gadget', 'Ultra Tool', 'Mega Device', 'Power Unit',
            'Smart Sensor', 'Digital Display', 'Advanced Controller', 'Precision Meter',
            'Compact Module', 'Premium Kit', 'Professional Set', 'Enterprise Solution',
            'Standard Package', 'Deluxe Edition', 'Basic Model', 'Enhanced Version',
            'Ultimate Bundle', 'Complete System', 'Essential Package'
        ]
    
    def generate_field(self, field_type: str) -> str:
        """Generate data for a specific field type."""
        if field_type == 'person_name':
            first = random.choice(self.first_names)
            last = random.choice(self.last_names)
            return f"{first} {last}"
        
        elif field_type == 'first_name':
            return random.choice(self.first_names)
        
        elif field_type == 'last_name':
            return random.choice(self.last_names)
        
        elif field_type == 'email':
            first = random.choice(self.first_names).lower()
            last = random.choice(self.last_names).lower()
            domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'company.com', 'email.com']
            domain = random.choice(domains)
            return f"{first}.{last}@{domain}"
        
        elif field_type == 'age':
            return str(random.randint(18, 70))
        
        elif field_type == 'city':
            return random.choice(self.cities)
        
        elif field_type == 'city_name':
            return random.choice(self.cities)
        
        elif field_type == 'company':
            return random.choice(self.companies)
        
        elif field_type == 'company_name':
            return random.choice(self.companies)
        
        elif field_type == 'product':
            return random.choice(self.products)
        
        elif field_type == 'product_name':
            return random.choice(self.products)
        
        elif field_type == 'currency':
            return str(random.randint(1000, 100000))
        
        elif field_type == 'salary':
            return str(random.randint(30000, 150000))
        
        elif field_type == 'price':
            return f"{random.randint(10, 500)}.{random.randint(0, 99):02d}"
        
        elif field_type == 'phone':
            area = random.randint(200, 999)
            exchange = random.randint(200, 999)
            number = random.randint(1000, 9999)
            return f"({area}) {exchange}-{number}"
        
        elif field_type == 'date':
            year = random.randint(2020, 2025)
            month = random.randint(1, 12)
            day = random.randint(1, 28)  # Safe day range
            return f"{year}-{month:02d}-{day:02d}"
        
        elif field_type == 'lorem_word':
            lorem = LoremGenerator()
            return lorem.generate_words(1)
        
        elif field_type == 'lorem_words':
            lorem = LoremGenerator()
            return lorem.generate_words(random.randint(2, 5))
        
        else:
            # Default: generate lorem words
            lorem = LoremGenerator()
            return lorem.generate_words(random.randint(1, 3))
    
    def auto_detect_field_type(self, header: str) -> str:
        """Auto-detect field type from header name."""
        header_lower = header.lower()
        
        # Direct matches
        if header_lower in ['name', 'full_name', 'fullname']:
            return 'person_name'
        elif header_lower in ['first_name', 'firstname', 'first']:
            return 'first_name'
        elif header_lower in ['last_name', 'lastname', 'last', 'surname']:
            return 'last_name'
        elif header_lower in ['email', 'email_address']:
            return 'email'
        elif header_lower in ['age']:
            return 'age'
        elif header_lower in ['city', 'location']:
            return 'city'
        elif header_lower in ['company', 'employer']:
            return 'company'
        elif header_lower in ['product', 'item']:
            return 'product'
        elif header_lower in ['salary', 'income']:
            return 'salary'
        elif header_lower in ['price', 'cost', 'amount']:
            return 'price'
        elif header_lower in ['phone', 'telephone', 'phone_number']:
            return 'phone'
        elif header_lower in ['date', 'created_date', 'updated_date']:
            return 'date'
        
        # Partial matches
        elif 'name' in header_lower:
            return 'person_name'
        elif 'email' in header_lower:
            return 'email'
        elif 'city' in header_lower:
            return 'city'
        elif 'company' in header_lower:
            return 'company'
        elif 'price' in header_lower or 'cost' in header_lower:
            return 'price'
        elif 'phone' in header_lower:
            return 'phone'
        elif 'date' in header_lower:
            return 'date'
        
        # Default
        return 'lorem_words'


class BaseFileGenerator(ABC):
    """Abstract base class for file generators."""
    
    def __init__(self, base_dir: str = None):
        """
        Initialize file generator.
        
        Args:
            base_dir: Base directory for file operations
        """
        if base_dir is None:
            base_dir = Path.cwd()
        self.base_dir = Path(base_dir)
        self.lorem_generator = LoremGenerator()
        self.data_generator = DataGenerator()
    
    @abstractmethod
    def generate(self, target_file: str, content_spec: Dict[str, Any], 
                 clutter_spec: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate files according to specifications.
        
        Args:
            target_file: Path to the main target file
            content_spec: Content specification dictionary
            clutter_spec: Clutter file specification (optional)
            
        Returns:
            Dictionary with generation results and metadata
        """
        pass
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve file path relative to base directory."""
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = self.base_dir / file_path
        return file_path
    
    def _ensure_directory(self, file_path: Path):
        """Ensure the directory for a file path exists."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _process_lorem_content(self, content: str) -> str:
        """Process {{lorem:...}} placeholders in content."""
        if not content:
            return content
        
        # Pattern to match {{lorem:counttype}} where type is l/s/p
        lorem_pattern = r'\{\{lorem:(\d+)([lsp])\}\}'
        
        def replace_lorem(match):
            count = int(match.group(1))
            lorem_type = match.group(2)
            
            if lorem_type == 'l':  # lines
                return self.lorem_generator.generate_lines(count)
            elif lorem_type == 's':  # sentences
                return self.lorem_generator.generate_sentences(count)
            elif lorem_type == 'p':  # paragraphs
                return self.lorem_generator.generate_paragraphs(count)
            else:
                return self.lorem_generator.generate_words(count)
        
        return re.sub(lorem_pattern, replace_lorem, content)


class TextFileGenerator(BaseFileGenerator):
    """Generates text files with lorem ipsum content."""
    
    def generate(self, target_file: str, content_spec: Dict[str, Any], 
                 clutter_spec: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate text file with specified content.
        
        Args:
            target_file: Path to target text file
            content_spec: Content specification like {'type': 'lorem_lines', 'count': 10}
            clutter_spec: Clutter specification (optional)
            
        Returns:
            Generation results with file content and metadata
        """
        result = {
            'target_file': target_file,
            'files_created': [],
            'content_generated': {},
            'errors': []
        }
        
        try:
            # Generate main file content
            content = self._generate_text_content(content_spec)
            
            # Write main file
            target_path = self._resolve_path(target_file)
            self._ensure_directory(target_path)
            
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            result['files_created'].append(str(target_path))
            result['content_generated'][str(target_path)] = content
            
            # Generate clutter files if specified
            if clutter_spec:
                clutter_result = self._generate_clutter_files(target_file, clutter_spec)
                result['files_created'].extend(clutter_result['files_created'])
                result['content_generated'].update(clutter_result['content_generated'])
                result['errors'].extend(clutter_result['errors'])
            
        except Exception as e:
            result['errors'].append(f"Error generating text file {target_file}: {e}")
            raise FileGeneratorError(f"Failed to generate text file {target_file}: {e}")
        
        return result
    
    def _generate_text_content(self, content_spec: Dict[str, Any]) -> str:
        """Generate text content based on specification."""
        content_type = content_spec.get('type', 'lorem_lines')
        count = content_spec.get('count', 10)
        
        if content_type == 'lorem_lines':
            return self.lorem_generator.generate_lines(count)
        elif content_type == 'lorem_sentences':
            return self.lorem_generator.generate_sentences(count)
        elif content_type == 'lorem_paragraphs':
            return self.lorem_generator.generate_paragraphs(count)
        elif content_type == 'lorem_words':
            return self.lorem_generator.generate_words(count)
        elif content_type == 'custom':
            # Handle custom content with {{lorem:...}} placeholders
            custom_content = content_spec.get('content', '')
            return self._process_lorem_content(custom_content)
        else:
            # Default to lorem lines
            return self.lorem_generator.generate_lines(count)
    
    def _generate_clutter_files(self, base_file: str, clutter_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate clutter files around the main file."""
        result = {
            'files_created': [],
            'content_generated': {},
            'errors': []
        }
        
        try:
            count = clutter_spec.get('count', 5)
            pattern = clutter_spec.get('pattern', '**/*.txt')
            
            # Extract base directory from target file
            base_path = self._resolve_path(base_file).parent
            
            # Generate random files
            for i in range(count):
                # Generate random filename and subdirectory
                subdir_depth = random.randint(0, 2)
                subdirs = []
                for _ in range(subdir_depth):
                    subdirs.append(f"dir_{random.randint(1, 100)}")
                
                filename = f"file_{random.randint(1, 1000)}.txt"
                if subdirs:
                    clutter_path = base_path / '/'.join(subdirs) / filename
                else:
                    clutter_path = base_path / filename
                
                # Generate random content
                content = self.lorem_generator.generate_lines(random.randint(3, 10))
                
                # Write clutter file
                self._ensure_directory(clutter_path)
                with open(clutter_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                result['files_created'].append(str(clutter_path))
                result['content_generated'][str(clutter_path)] = content
                
        except Exception as e:
            result['errors'].append(f"Error generating clutter files: {e}")
        
        return result


class CSVFileGenerator(BaseFileGenerator):
    """Generates CSV files with realistic random data."""
    
    def generate(self, target_file: str, content_spec: Dict[str, Any], 
                 clutter_spec: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate CSV file with specified structure and data.
        
        Args:
            target_file: Path to target CSV file
            content_spec: Content specification like {'headers': [...], 'rows': 50}
            clutter_spec: Clutter specification (optional)
            
        Returns:
            Generation results with CSV data and metadata
        """
        result = {
            'target_file': target_file,
            'files_created': [],
            'content_generated': {},
            'csv_data': {},
            'errors': []
        }
        
        try:
            # Generate CSV content
            csv_data = self._generate_csv_content(content_spec)
            
            # Write CSV file
            target_path = self._resolve_path(target_file)
            self._ensure_directory(target_path)
            
            with open(target_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(csv_data)
            
            result['files_created'].append(str(target_path))
            result['csv_data'][str(target_path)] = csv_data
            
            # Store content as string for compatibility
            csv_content = '\n'.join([','.join(row) for row in csv_data])
            result['content_generated'][str(target_path)] = csv_content
            
            # Generate clutter files if specified
            if clutter_spec:
                clutter_result = self._generate_clutter_files(target_file, clutter_spec)
                result['files_created'].extend(clutter_result['files_created'])
                result['content_generated'].update(clutter_result['content_generated'])
                result['errors'].extend(clutter_result['errors'])
            
        except Exception as e:
            result['errors'].append(f"Error generating CSV file {target_file}: {e}")
            raise FileGeneratorError(f"Failed to generate CSV file {target_file}: {e}")
        
        return result
    
    def _generate_csv_content(self, content_spec: Dict[str, Any]) -> List[List[str]]:
        """Generate CSV content based on specification."""
        headers = content_spec.get('headers', ['name', 'email', 'age'])
        row_count = content_spec.get('rows', 10)
        
        # Start with headers
        csv_data = [headers]
        
        # Auto-detect field types from headers
        field_types = []
        for header in headers:
            field_types.append(self.data_generator.auto_detect_field_type(header))
        
        # Generate data rows
        for _ in range(row_count):
            row = []
            for field_type in field_types:
                row.append(self.data_generator.generate_field(field_type))
            csv_data.append(row)
        
        return csv_data
    
    def _generate_clutter_files(self, base_file: str, clutter_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate clutter CSV and text files."""
        result = {
            'files_created': [],
            'content_generated': {},
            'errors': []
        }
        
        try:
            count = clutter_spec.get('count', 3)
            base_path = self._resolve_path(base_file).parent
            
            for i in range(count):
                # Random file type and location
                file_type = random.choice(['csv', 'txt', 'log'])
                subdir_depth = random.randint(0, 1)
                
                if subdir_depth > 0:
                    subdir = f"subdir_{random.randint(1, 50)}"
                    clutter_path = base_path / subdir / f"clutter_{random.randint(1, 100)}.{file_type}"
                else:
                    clutter_path = base_path / f"clutter_{random.randint(1, 100)}.{file_type}"
                
                self._ensure_directory(clutter_path)
                
                if file_type == 'csv':
                    # Generate small random CSV
                    headers = random.sample(['id', 'name', 'value', 'status', 'date'], 3)
                    csv_data = [headers]
                    for _ in range(random.randint(2, 5)):
                        row = [self.data_generator.generate_field('lorem_words') for _ in headers]
                        csv_data.append(row)
                    
                    with open(clutter_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerows(csv_data)
                    
                    content = '\n'.join([','.join(row) for row in csv_data])
                else:
                    # Generate text content
                    content = self.lorem_generator.generate_lines(random.randint(2, 8))
                    with open(clutter_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                result['files_created'].append(str(clutter_path))
                result['content_generated'][str(clutter_path)] = content
                
        except Exception as e:
            result['errors'].append(f"Error generating CSV clutter files: {e}")
        
        return result


class FileGeneratorFactory:
    """Factory for creating file generators."""
    
    @staticmethod
    def create_generator(generator_type: str, base_dir: str = None) -> BaseFileGenerator:
        """
        Create a file generator of the specified type.
        
        Args:
            generator_type: Type of generator ('create_files', 'create_csv', etc.)
            base_dir: Base directory for file operations
            
        Returns:
            File generator instance
        """
        if generator_type == 'create_files':
            return TextFileGenerator(base_dir)
        elif generator_type == 'create_csv':
            return CSVFileGenerator(base_dir)
        else:
            raise FileGeneratorError(f"Unknown generator type: {generator_type}")


def main():
    """Test the file generator infrastructure."""
    import tempfile
    import json
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Testing file generators in: {temp_dir}")
        
        # Test text file generation
        print("\n1. Testing text file generation:")
        text_gen = TextFileGenerator(temp_dir)
        
        text_result = text_gen.generate(
            target_file="test_data/sample.txt",
            content_spec={'type': 'lorem_lines', 'count': 5},
            clutter_spec={'count': 3}
        )
        
        print(f"   Created files: {len(text_result['files_created'])}")
        print(f"   Target content preview: {text_result['content_generated'][list(text_result['content_generated'].keys())[0]][:100]}...")
        
        # Test CSV file generation
        print("\n2. Testing CSV file generation:")
        csv_gen = CSVFileGenerator(temp_dir)
        
        csv_result = csv_gen.generate(
            target_file="test_data/people.csv",
            content_spec={'headers': ['name', 'email', 'age', 'city'], 'rows': 5},
            clutter_spec={'count': 2}
        )
        
        print(f"   Created files: {len(csv_result['files_created'])}")
        print(f"   CSV data rows: {len(csv_result['csv_data'][list(csv_result['csv_data'].keys())[0]])}")
        
        # Test lorem content processing
        print("\n3. Testing lorem content processing:")
        custom_content = "Header\n{{lorem:3l}}\nFooter"
        processed = text_gen._process_lorem_content(custom_content)
        print(f"   Original: {custom_content}")
        print(f"   Processed: {processed[:100]}...")
        
        # Test factory
        print("\n4. Testing factory:")
        factory_gen = FileGeneratorFactory.create_generator('create_files', temp_dir)
        print(f"   Factory created: {type(factory_gen).__name__}")
        
        print("\n✅ All file generator tests completed!")


if __name__ == "__main__":
    main()
