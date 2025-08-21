"""
Data Generator - Generates realistic random data for PICARD framework.

Extracted from file_generators.py to avoid circular dependencies.
"""

import random


class LoremGenerator:
    """Generates lorem ipsum style content."""
    
    def __init__(self):
        #Our entity pool, for tag gibberish
        self.entity_pool = None
        
        # Extended lorem ipsum word pool
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
        """Generate multiple sentences connected naturally."""
        if count <= 0:
            return ""
        
        sentences = []
        for _ in range(count):
            sentences.append(self.generate_sentence())
        
        return ' '.join(sentences)
    
    def generate_paragraph(self, min_sentences: int = 4, max_sentences: int = 8) -> str:
        """Generate a paragraph with variable sentences."""
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
        # Import here to avoid circular dependency
        self.entity_pool = None
        
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

        elif field_type == 'entity_pool':
            # Import entity pool and pick random word
            if self.entity_pool is None:
                from entity_pool import EntityPool
                self.entity_pool = EntityPool()
            return self.entity_pool.get_random_entity()

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
        
        # New field types
        elif field_type == 'status':
            return random.choice(['active', 'inactive', 'completed', 'pending', 'cancelled', 'approved', 'rejected', 'processing'])
        
        elif field_type == 'department':
            return random.choice(['Engineering', 'Sales', 'Marketing', 'Finance', 'HR', 'Operations', 'IT', 'Legal', 'Customer Service', 'Research'])
        
        elif field_type == 'region':
            return random.choice(['North', 'South', 'East', 'West', 'Central', 'Northeast', 'Southeast', 'Southwest', 'Northwest', 'Midwest'])
        
        elif field_type == 'id':
            return str(random.randint(1, 9999))
        
        elif field_type == 'experience':
            return str(random.randint(0, 40))
        
        elif field_type == 'score':
            return str(random.randint(60, 100))
        
        elif field_type == 'course':
            courses = ['Math 101', 'Physics 201', 'Chemistry 301', 'Biology 101', 'Engineering 401', 
                      'Computer Science 202', 'Statistics 301', 'Calculus 401', 'Data Science 501', 
                      'Machine Learning 601', 'Economics 101', 'Psychology 201', 'History 101', 
                      'Literature 301', 'Art 201']
            return random.choice(courses)
        
        elif field_type == 'semester':
            seasons = ['Spring', 'Summer', 'Fall', 'Winter']
            years = ['2023', '2024', '2025']
            return f"{random.choice(seasons)} {random.choice(years)}"
        
        elif field_type == 'category':
            return random.choice(['Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports', 'Toys', 'Automotive', 'Health', 'Beauty', 'Food'])
        
        elif field_type == 'boolean':
            return random.choice(['true', 'false', 'yes', 'no', '1', '0'])
        
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
        elif header_lower in ['customer', 'customer_name', 'client', 'client_name']:
            return 'person_name'
        # New field types
        elif header_lower in ['status', 'state']:
            return 'status'
        elif header_lower in ['department', 'dept']:
            return 'department'
        elif header_lower in ['region', 'area', 'zone']:
            return 'region'
        elif header_lower.endswith('_id') or header_lower == 'id':
            return 'id'
        elif header_lower in ['experience', 'years_experience', 'years', 'exp']:
            return 'experience'
        elif header_lower in ['score', 'grade', 'rating', 'points']:
            return 'score'
        elif header_lower in ['course', 'subject', 'class']:
            return 'course'
        elif header_lower in ['semester', 'term', 'quarter']:
            return 'semester'
        elif header_lower in ['category', 'type', 'kind']:
            return 'category'
        elif header_lower in ['in_stock', 'available', 'active']:
            return 'boolean'
        elif header_lower in ['total', 'sum', 'revenue']:
            return 'currency'
        
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
        elif 'customer' in header_lower or 'client' in header_lower:
            return 'person_name'
        elif 'status' in header_lower:
            return 'status'
        elif 'department' in header_lower or 'dept' in header_lower:
            return 'department'
        elif 'region' in header_lower:
            return 'region'
        elif 'id' in header_lower:
            return 'id'
        elif 'experience' in header_lower or 'exp' in header_lower:
            return 'experience'
        elif 'score' in header_lower or 'grade' in header_lower:
            return 'score'
        elif 'course' in header_lower or 'subject' in header_lower:
            return 'course'
        elif 'category' in header_lower or 'type' in header_lower:
            return 'category'
        
        # Default
        return 'lorem_words'