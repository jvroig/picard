# PICARD: Probing Intelligent Capabilities via Artificial Randomized Data

> Testing what models **can do** — not what they've *seen*.

PICARD is a framework for evaluating agentic AI capabilities while preventing memorization through systematic multi-layered randomization. 

This project is the reference implementation of the PICARD framework, as described in the PICARD paper [arXiv link here when available]

## 🎯 Why PICARD?

As LLM training datasets grow, popular benchmarks inevitably appear in training data, leading to inflated performance that measures memorization rather than genuine capability.

PICARD creates combinatorially vast question spaces (>10^80 unique configurations - more than all the atoms in the universe) through:
- **Entity substitution**: Random replacement of variables (names, objects, etc) in question templates.
- **Dynamic data generation**: Unique CSV data, databases, and file structures per test
- **Agentic evaluation**: Multi-step workflows with real tool use, not single-shot Q&A

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/jvroig/picard.git
cd picard
pip install -r requirements.txt
```

### Configuration

1. Copy the configuration template:
```bash
cp picard_config.py.template picard_config.py
```

2. Edit `picard_config.py` to set your sandbox directory:
```python
ARTIFACTS_DIR = "/path/to/your/sandbox/folder"
```
### Agentic Server
PICARD requires an agentic server that provides *"LLM with tools in a loop"* functionality. 

An implementation of an agentic server is available at https://github.com/jvroig/qwen-agentic-server

### Running Tests
Once the agentic server is up, you can run tests


```bash
# Run the default sample test
python src/test_runner.py

# Run tests using your own PICARD-based test
python src/test_runner.py --definitions "configs/your-test-definition.yml"

# Score a successful test run (e.g., "test_20250529")
python src/scorer.py --test-dir results/test_20250529 
python src/scorer.py #No params = just score the latest test result
```

## 📝 Creating Tests

Tests are defined in YAML with powerful templating:

```yaml
- question_id: 301
  samples: 20
  template: "Create a JSON summary of {{artifacts}}/{{qs_id}}/{{entity1}}/data.csv 
             showing total customers and average age."
  scoring_type: "readfile_jsonmatch"
  file_to_read: "{{artifacts}}/{{qs_id}}/summary.json"
  expected_content: '{"total": {{csv_count:ID:TARGET_FILE}}, 
                      "avg_age": {{csv_avg:AGE:TARGET_FILE}}}'
  sandbox_setup:
    type: "create_csv"
    target_file: "{{artifacts}}/{{qs_id}}/{{entity1}}/data.csv"
    content:
      headers: ["ID", "NAME", "AGE", "CITY"] 
      rows: 50
```

This creates 20 unique test instances with:
- Random entity substitution (`{{entity1}}` → "crimson", "harbor", etc.)
- Dynamically generated CSV files with 50 random rows
- Deterministic answer keys computed from the generated data

## 🎲 Anti-Memorization Mathematics

PICARD's combinatorial explosion makes memorization impossible:

- **Single question**: 154^4 = 560M+ combinations (4 variables)
- **Test suite**: (154^2)^50 = 6.4×10^32 combinations (modest 50-item test)
- **Reality**: Far exceeds atoms in observable universe (≈10^80)

## 🔧 Scoring Systems

**Deterministic Scoring**: No "LLM-as-judge" uncertainty
- `stringmatch`: Exact text comparison
- `jsonmatch`: Structured data validation
- `files_exist`: File system verification  
- `directory_structure`: Hierarchy validation
- `readfile_*`: Content verification

## 📈 Statistical Analysis

PICARD provides comprehensive performance analysis:

```bash
# Analyze group results (multiple tests in the `results/` folder) 
# This assumes individual result subfolders have been renamed to indicate LLM
# For example:
#   "test_20250614_173738" -> "llama33-70b"
#   "test_20250614_174716" -> "llama33-8b" 
# This command will then produce grouped stats for llama33-70b and llama33-8b
python process_results.py results/

# Outputs:
# - overall_performance.csv: Accuracy by model
# - performance_by_scoring_type.csv: Scores per unique scoring type (jsonmatch, stringmatch, readfile_jsonmatch, readfile_stringmatch)  
# - rounds.csv: Inference efficiency analysis - how many rounds the LLM takes per question
```

## 🔍 Example Results

Real insights from PICARD evaluation:

| Model | Overall | File Ops | Database | Efficiency |
|-------|---------|----------|----------|------------|
| LLM1 | 89.0% | 95% | 85% | 4.2 rounds avg |
| LLM2 | 40.0% | 100% | 12% | 5.1 rounds avg |

*LLM2: Perfect at file operations, struggles with direct responses*

## 🛠️ Extending PICARD

### Adding New Scoring Types

```python
# src/scoring_types/custom_scorer.py
class CustomScorer(BaseScoringType):
    def score(self, precheck_entry, response_entry, test_artifacts_dir):
        # Your scoring logic here
        return ScoringResult(...)
```

### Creating Domain-Specific Tests

```yaml
# Customize for your use case
tests:
  - question_id: 1001
    template: "Your domain-specific task with {{entity1}}"
    # Add sandbox_setup for specialized data generation
```

### Expanding Entity Pools

```python
# Future: Semantic entity pools
# {{medical_term1}}, {{legal_concept1}}, {{business_metric1}}
```

## 🤝 Contributing

PICARD is designed for community extension:

1. **New scoring types**: Add evaluation methods for your domain
2. **Data generators**: Create specialized content generators  
3. **Agentic servers**: Implement integrations for different agentic servers
4. **Entity pools**: Contribute domain-specific entity collections

## 📚 Citation

```bibtex
@article{roig2025picard,
  title={Testing What Models Can Do, Not What They've Seen: PICARD: Probing Intelligent Capabilities via Artificial Randomized Data},
  author={Roig, JV},
  journal={arXiv preprint arXiv:XXXX.XXXXX},
  year={2025}
}
```

## 🔗 Links

- **Paper**: [arXiv link upon publication]
- **Documentation**: [Wiki with detailed guides]
- **Community**: [Discussion forum/Discord]

---

*PICARD: Making agentic AI evaluation trustworthy.*
