# PICARD File Generation Capabilities Expansion Plan

## 🎯 Executive Summary

This plan outlines a comprehensive expansion of PICARD's file generation capabilities to support a broader range of file formats, data types, and testing scenarios. The goal is to increase PICARD's utility for testing agentic AI systems across diverse domains while maintaining the framework's core anti-memorization principles.

## 📊 Current State Analysis

### Implemented File Generators
- ✅ **TextFileGenerator** (`create_files`) - Lorem ipsum content with placeholders
- ✅ **CSVFileGenerator** (`create_csv`) - Business data with 40+ semantic types
- ✅ **SQLiteFileGenerator** (`create_sqlite`) - Relational databases with foreign keys
- ✅ **JSONFileGenerator** (`create_json`) - Schema-driven JSON generation

### Implemented Template Functions
- ✅ **File Functions**: `file_line`, `file_word`, `file_line_count`, `file_word_count`
- ✅ **CSV Functions**: `csv_cell`, `csv_value`, `csv_count`, `csv_sum`, `csv_avg`, `csv_*_where`
- ✅ **SQLite Functions**: `sqlite_query`, `sqlite_value`
- ✅ **JSON Functions**: `json_path`, `json_value`, `json_count`, `json_keys` (UNDOCUMENTED)

### Current Semantic Data Types (40+)
- **People**: `person_name`, `first_name`, `last_name`, `email`
- **Business**: `company`, `department`, `salary`, `currency`, `price`, `product`
- **Location**: `city`, `region`, `phone`
- **Time**: `date`, `age`, `experience`, `semester`
- **Status**: `status`, `boolean`, `category`, `course`, `score`
- **Content**: `entity_pool`, `lorem_word`, `lorem_words`

## 🎯 Expansion Goals

### Primary Objectives
1. **Format Diversity**: Support 15+ additional file formats
2. **Domain Coverage**: Add specialized data types for technical, scientific, and creative domains
3. **Real-world Realism**: Generate files that mirror actual enterprise and development environments
4. **Advanced Scenarios**: Support complex multi-file and multi-format workflows

### Success Metrics
- Support 20+ file formats by end of implementation
- 100+ semantic data types across 10+ domains
- 50+ new template functions for diverse data extraction
- Capability to simulate realistic development/ops environments

## 🚀 Phase 1: Critical Documentation & Foundation (Week 1-2)

### 1.1 Documentation Gap Fixes
**Priority: HIGH** - Fix immediate inconsistencies

#### JSON Functions Documentation
- **Issue**: JSON template functions are implemented and tested but not documented in REFERENCE.md
- **Action**: Add comprehensive JSON functions section to REFERENCE.md
- **Functions to Document**:
  - `json_path` - JSONPath-like extraction
  - `json_value` - Dot notation value access  
  - `json_count` - Count arrays/objects
  - `json_keys` - Extract object keys

#### Missing Generator Documentation
- **Issue**: `create_json` mentioned in tests but not in REFERENCE.md overview
- **Action**: Add JSON generation section to REFERENCE.md sandbox setup
- **Include**: Schema examples, data type mappings, nested structure support

### 1.2 Core Infrastructure Enhancements

#### Enhanced Data Generator
```python
# Extend DataGenerator with new domains
class EnhancedDataGenerator(DataGenerator):
    def __init__(self):
        super().__init__()
        self.technical_data = TechnicalDataProvider()
        self.scientific_data = ScientificDataProvider() 
        self.creative_data = CreativeDataProvider()
        self.business_data = BusinessDataProvider()
```

#### Configurable Generation Patterns
```yaml
# Support custom data generation patterns
content:
  type: "create_structured"
  template: "enterprise_config"
  domain: "technical"
  complexity: "high"
```

## 🏗️ Phase 2: New File Format Generators (Week 3-6)

### 2.1 Configuration & Markup Formats

#### YAMLFileGenerator (`create_yaml`)
```python
class YAMLFileGenerator(BaseFileGenerator):
    """Generate YAML files with hierarchical configuration data."""
```

**Use Cases**:
- Kubernetes configurations
- CI/CD pipeline definitions  
- Application config files
- Docker Compose files

**Features**:
- Schema-driven generation
- Realistic cloud-native configs
- Multi-document YAML support
- Anchor/reference relationships

#### XMLFileGenerator (`create_xml`)
**Use Cases**:
- SOAP API responses
- Configuration files
- Legacy enterprise data
- RSS/Atom feeds

#### TOMLFileGenerator (`create_toml`)
**Use Cases**:
- Python project configurations
- Rust Cargo.toml files
- Application settings

#### INIFileGenerator (`create_ini`)
**Use Cases**:
- Legacy Windows configs
- Database connection strings
- Application settings

### 2.2 Data & Analytics Formats

#### ParquetFileGenerator (`create_parquet`)
```python
class ParquetFileGenerator(BaseFileGenerator):
    """Generate Parquet files for big data scenarios."""
```

**Use Cases**:
- Data lake testing
- Analytics pipeline validation
- Large dataset processing

**Features**:
- Columnar data generation
- Compression options
- Partition simulation
- Schema evolution

#### ExcelFileGenerator (`create_excel`)
**Use Cases**:
- Business reporting
- Financial data
- Multi-sheet workbooks

**Features**:
- Multiple worksheets
- Formulas and calculations
- Charts and formatting
- Named ranges

### 2.3 Development & Operations Formats

#### LogFileGenerator (`create_logs`)
```python
class LogFileGenerator(BaseFileGenerator):
    """Generate realistic application and system logs."""
```

**Log Formats**:
- **Apache/Nginx**: Web server logs
- **Application**: JSON structured logs
- **System**: Syslog format
- **Container**: Docker/Kubernetes logs

**Features**:
- Realistic timestamp progression
- Error rate patterns
- IP address generation
- Request/response patterns

#### DockerfileGenerator (`create_dockerfile`)
**Use Cases**:
- Container build testing
- DevOps pipeline validation

#### KubernetesManifestGenerator (`create_k8s`)
**Use Cases**:
- K8s deployment testing
- YAML manifest generation

### 2.4 Archive & Binary Formats

#### ArchiveFileGenerator (`create_archive`)
**Formats**: ZIP, TAR, TAR.GZ

**Use Cases**:
- Backup testing
- Distribution packages
- Multi-file scenarios

#### BinaryFileGenerator (`create_binary`)
**Types**:
- Images (PNG, JPEG placeholders)
- Documents (PDF structure)
- Executables (mock headers)

## 🧠 Phase 3: Enhanced Data Generation (Week 7-10)

### 3.1 Technical Domain Data Types

#### Software Development
```python
TECHNICAL_TYPES = {
    'git_commit_hash': lambda: secrets.token_hex(20),
    'semantic_version': lambda: f"{random.randint(1,10)}.{random.randint(0,20)}.{random.randint(0,50)}",
    'docker_image': lambda: f"{random.choice(registries)}/{random.choice(repos)}:{random.choice(tags)}",
    'kubernetes_resource': lambda: random.choice(['Pod', 'Service', 'Deployment', 'ConfigMap']),
    'http_status_code': lambda: random.choice([200, 201, 400, 401, 403, 404, 500, 502, 503]),
    'ip_address': lambda: f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
    'mac_address': lambda: ':'.join([f"{random.randint(0,255):02x}" for _ in range(6)]),
    'uuid': lambda: str(uuid.uuid4()),
    'api_endpoint': lambda: f"/api/v{random.randint(1,3)}/{random.choice(['users', 'orders', 'products'])}",
    'log_level': lambda: random.choice(['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']),
    'mime_type': lambda: random.choice(['application/json', 'text/plain', 'image/png', 'video/mp4']),
    'file_extension': lambda: random.choice(['.txt', '.json', '.csv', '.log', '.yaml', '.xml']),
    'database_url': lambda: f"postgresql://user:pass@{random.choice(hosts)}:5432/{random.choice(dbs)}",
    'redis_key': lambda: f"{random.choice(['user', 'session', 'cache'])}:{random.randint(1,10000)}",
    'aws_region': lambda: random.choice(['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']),
    'programming_language': lambda: random.choice(['Python', 'JavaScript', 'Java', 'Go', 'Rust', 'C++'])
}
```

#### DevOps & Cloud
```python
DEVOPS_TYPES = {
    'cloud_provider': lambda: random.choice(['AWS', 'GCP', 'Azure', 'DigitalOcean']),
    'instance_type': lambda: random.choice(['t3.micro', 'm5.large', 'n1-standard-1', 'Standard_B2s']),
    'availability_zone': lambda: f"{random.choice(['us-east-1', 'us-west-2'])}{'abc'[random.randint(0,2)]}",
    'cidr_block': lambda: f"10.{random.randint(0,255)}.{random.randint(0,255)}.0/24",
    'load_balancer_algorithm': lambda: random.choice(['round_robin', 'least_connections', 'ip_hash']),
    'container_port': lambda: random.choice([80, 443, 3000, 8080, 5432, 6379, 27017]),
    'environment': lambda: random.choice(['development', 'staging', 'production', 'test'])
}
```

### 3.2 Scientific & Research Data Types

#### Life Sciences
```python
SCIENTIFIC_TYPES = {
    'gene_symbol': lambda: f"{random.choice(['BRCA', 'TP53', 'EGFR', 'KRAS'])}{random.randint(1,9)}",
    'protein_sequence': lambda: ''.join(random.choices('ACDEFGHIKLMNPQRSTVWY', k=random.randint(50,200))),
    'amino_acid': lambda: random.choice(['Ala', 'Arg', 'Asn', 'Asp', 'Cys', 'Glu', 'Gln']),
    'chemical_formula': lambda: f"C{random.randint(1,20)}H{random.randint(1,40)}O{random.randint(1,10)}",
    'molecular_weight': lambda: f"{random.uniform(100, 1000):.2f}",
    'ph_value': lambda: f"{random.uniform(0, 14):.1f}",
    'temperature_celsius': lambda: f"{random.uniform(-273, 1000):.1f}",
    'lab_instrument': lambda: random.choice(['PCR', 'HPLC', 'Mass Spectrometer', 'Centrifuge']),
    'research_field': lambda: random.choice(['Genomics', 'Proteomics', 'Bioinformatics', 'Pharmacology'])
}
```

### 3.3 Creative & Media Data Types

#### Creative Content
```python
CREATIVE_TYPES = {
    'color_hex': lambda: f"#{random.randint(0,16777215):06x}",
    'font_family': lambda: random.choice(['Arial', 'Helvetica', 'Times New Roman', 'Georgia']),
    'image_resolution': lambda: f"{random.choice([1920, 1280, 800])}x{random.choice([1080, 720, 600])}",
    'video_codec': lambda: random.choice(['H.264', 'H.265', 'VP9', 'AV1']),
    'audio_format': lambda: random.choice(['MP3', 'WAV', 'FLAC', 'AAC']),
    'music_genre': lambda: random.choice(['Rock', 'Jazz', 'Classical', 'Electronic', 'Hip Hop']),
    'art_medium': lambda: random.choice(['Oil Paint', 'Watercolor', 'Digital', 'Pencil', 'Acrylic']),
    'photography_setting': lambda: f"f/{random.uniform(1.4, 16):.1f} ISO{random.choice([100, 200, 400, 800, 1600])}"
}
```

### 3.4 Financial & Legal Data Types

#### Financial
```python
FINANCIAL_TYPES = {
    'currency_code': lambda: random.choice(['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD']),
    'stock_symbol': lambda: ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=random.randint(2,5))),
    'bank_routing': lambda: ''.join([str(random.randint(0,9)) for _ in range(9)]),
    'credit_score': lambda: random.randint(300, 850),
    'tax_rate': lambda: f"{random.uniform(0, 50):.2f}%",
    'market_cap': lambda: f"${random.uniform(1, 1000):.1f}B",
    'financial_ratio': lambda: f"{random.uniform(0.1, 10):.2f}",
    'fiscal_quarter': lambda: f"Q{random.randint(1,4)} {random.randint(2020,2025)}"
}
```

## 🔧 Phase 4: Advanced Template Functions (Week 11-14)

### 4.1 Cross-Format Functions

#### Universal Functions
```python
# File system operations
'file_size': lambda path: os.path.getsize(path),
'file_extension': lambda path: Path(path).suffix,
'file_modified': lambda path: datetime.fromtimestamp(os.path.getmtime(path)),

# Content analysis
'line_contains': lambda pattern, file: [i for i, line in enumerate(open(file)) if pattern in line],
'word_frequency': lambda word, file: content.count(word),
'char_count': lambda file: len(open(file).read()),

# Data conversion  
'csv_to_json': lambda csv_file: convert_csv_to_json(csv_file),
'json_to_yaml': lambda json_file: convert_json_to_yaml(json_file),
```

### 4.2 Advanced Analysis Functions

#### Log Analysis Functions
```python
LOG_FUNCTIONS = {
    'log_error_count': lambda file: count_log_level(file, 'ERROR'),
    'log_ip_unique': lambda file: len(extract_unique_ips(file)),
    'log_time_range': lambda file: get_time_range(file),
    'log_status_codes': lambda file: extract_status_codes(file),
    'log_user_agents': lambda file: extract_user_agents(file)
}
```

#### YAML/Config Functions
```python
YAML_FUNCTIONS = {
    'yaml_value': lambda path, file: extract_yaml_path(file, path),
    'yaml_keys': lambda path, file: list_yaml_keys(file, path),
    'yaml_validate': lambda schema, file: validate_yaml_schema(file, schema)
}
```

#### Archive Functions
```python
ARCHIVE_FUNCTIONS = {
    'zip_file_count': lambda zip_file: count_files_in_zip(zip_file),
    'zip_file_list': lambda zip_file: list_files_in_zip(zip_file),
    'zip_extract_text': lambda file, zip_file: extract_text_from_zip(zip_file, file)
}
```

### 4.3 Complex Data Processing Functions

#### Statistical Functions
```python
STATS_FUNCTIONS = {
    'data_median': lambda column, file: calculate_median(file, column),
    'data_std_dev': lambda column, file: calculate_std_dev(file, column),
    'data_percentile': lambda p, column, file: calculate_percentile(file, column, p),
    'data_correlation': lambda col1, col2, file: calculate_correlation(file, col1, col2)
}
```

## 🌟 Phase 5: Advanced Scenarios & Use Cases (Week 15-18)

### 5.1 Multi-File Scenarios

#### Enterprise Development Environment
```yaml
sandbox_setup:
  type: "create_enterprise_env"
  structure:
    - name: "microservices"
      files:
        - type: "create_dockerfile"
          target: "services/api/Dockerfile"
        - type: "create_yaml" 
          target: "k8s/deployment.yaml"
          template: "kubernetes_deployment"
        - type: "create_json"
          target: "package.json"
          template: "node_package"
```

#### Data Pipeline Simulation
```yaml
sandbox_setup:
  type: "create_data_pipeline"
  stages:
    - type: "create_csv"
      target: "raw_data/orders.csv"
      rows: 1000
    - type: "create_parquet"
      target: "processed/orders_clean.parquet"
      source: "raw_data/orders.csv"
    - type: "create_json"
      target: "config/pipeline_config.json"
      schema: "etl_config"
```

### 5.2 Domain-Specific Templates

#### Healthcare System
```yaml
content:
  type: "create_healthcare_data"
  formats: ["csv", "json", "xml"]
  compliance: "HIPAA"
  data_types: ["patient_id", "diagnosis_code", "treatment_protocol"]
```

#### Financial Trading System  
```yaml
content:
  type: "create_trading_data"
  formats: ["csv", "json", "binary"]
  market_data: true
  real_time_simulation: true
```

#### IoT Sensor Network
```yaml
content:
  type: "create_iot_data" 
  formats: ["json", "csv", "binary"]
  sensor_types: ["temperature", "humidity", "pressure", "motion"]
  time_series: true
```

## 📈 Phase 6: Performance & Scale (Week 19-20)

### 6.1 Large Data Generation

#### Streaming Data Generation
```python
class StreamingDataGenerator:
    """Generate large datasets without memory constraints."""
    
    def generate_streaming_csv(self, target_file, schema, row_count):
        """Generate CSV files with millions of rows using streaming."""
        
    def generate_partitioned_data(self, target_dir, schema, partitions):
        """Generate partitioned datasets for big data scenarios."""
```

#### Parallel Generation
```python
class ParallelFileGenerator:
    """Generate multiple files concurrently."""
    
    def generate_concurrent(self, file_specs, max_workers=4):
        """Generate multiple files in parallel using ThreadPoolExecutor."""
```

### 6.2 Advanced Caching & Optimization

#### Template Function Caching
```python
@lru_cache(maxsize=128)
def cached_file_operation(operation, file_path, *args):
    """Cache expensive file operations for repeated use."""
```

#### Lazy Evaluation
```python
class LazyTemplateFunction:
    """Defer expensive operations until actually needed."""
```

## 🎯 Implementation Priority Matrix

### High Priority (Weeks 1-8)
1. **Fix JSON documentation gap** - Critical for current users
2. **YAML/XML generators** - High demand formats
3. **Log file generation** - Essential for DevOps testing
4. **Enhanced data types** - Technical domains
5. **Archive support** - Common use case

### Medium Priority (Weeks 9-16)  
1. **Parquet/Excel generators** - Analytics use cases
2. **Advanced template functions** - Power user features
3. **Multi-file scenarios** - Complex testing
4. **Performance optimizations** - Scale requirements

### Lower Priority (Weeks 17-20)
1. **Binary format support** - Specialized use cases
2. **Streaming generation** - Large scale scenarios
3. **Domain-specific templates** - Niche applications

## 📋 Testing Strategy

### Unit Testing Expansion
```python
# Each new generator gets comprehensive unit tests
class TestYAMLFileGenerator:
    def test_basic_yaml_generation(self):
    def test_nested_structure_generation(self):
    def test_kubernetes_manifest_generation(self):
    def test_anchor_reference_generation(self):
```

### Integration Testing
```python
# Cross-format workflow tests
class TestMultiFormatWorkflows:
    def test_json_to_yaml_conversion(self):
    def test_csv_to_parquet_pipeline(self):
    def test_log_analysis_workflow(self):
```

### Performance Testing
```python
# Large data generation tests
class TestLargeDataGeneration:
    def test_million_row_csv_generation(self):
    def test_concurrent_file_generation(self):
    def test_memory_usage_streaming(self):
```

## 🚀 Success Metrics & Validation

### Quantitative Goals
- **File Format Support**: 20+ formats (currently 4)
- **Data Types**: 100+ semantic types (currently 40+)  
- **Template Functions**: 80+ functions (currently 30+)
- **Performance**: Generate 1M+ rows without memory issues
- **Concurrency**: Support 10+ files generated simultaneously

### Qualitative Goals
- **Enterprise Realism**: Generated environments mirror real development setups
- **Domain Coverage**: Support testing across 10+ professional domains
- **Workflow Complexity**: Enable multi-step, cross-format testing scenarios
- **User Experience**: Intuitive YAML configuration for complex scenarios

### Validation Approach
1. **Real-world scenarios**: Test with actual enterprise use cases
2. **Performance benchmarks**: Measure generation speed and memory usage
3. **User feedback**: Gather input from framework users
4. **Anti-memorization validation**: Ensure combinatorial explosion is maintained

## 📖 Documentation Plan

### Updated Reference Documentation
1. **REFERENCE.md updates** - Add all new generators and functions
2. **DATA_GENERATION.md expansion** - Document all new data types
3. **Advanced Scenarios Guide** - Multi-file and cross-format examples
4. **Performance Guide** - Large data and optimization techniques

### New Documentation
1. **Domain-Specific Guides** - Technical, scientific, creative use cases
2. **Migration Guide** - Upgrading existing tests to use new capabilities
3. **Best Practices** - Recommendations for complex scenario design

## 🔄 Risk Mitigation

### Technical Risks
- **Memory usage** with large files → Streaming generation
- **Generation speed** → Parallel processing and caching
- **Format complexity** → Incremental implementation with testing

### Compatibility Risks  
- **Breaking changes** → Maintain backward compatibility
- **Documentation drift** → Automated documentation validation
- **Test maintenance** → Modular test design

### Adoption Risks
- **Learning curve** → Comprehensive examples and tutorials
- **Migration effort** → Automated migration tools where possible

## 🎉 Conclusion

This expansion plan will transform PICARD from a capable but limited file generation framework into a comprehensive testing platform that supports virtually any file format and data scenario. The phased approach ensures we can deliver value incrementally while maintaining quality and backward compatibility.

The resulting framework will be uniquely positioned to test modern agentic AI systems across the full spectrum of real-world data and file formats, from simple CSV processing to complex multi-service architectures with diverse data sources.

**Next Steps**: Begin with Phase 1 documentation fixes and foundation work, then proceed systematically through the phases based on user feedback and priority adjustments.