#!/usr/bin/env python3
"""
Demo script for Enhanced Variable Substitution in PICARD.

This script demonstrates the new enhanced variable substitution capabilities
including semantic variables, numeric ranges, and enhanced entity pools.
"""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from template_processor import TemplateProcessor


def main():
    """Demonstrate enhanced variable substitution capabilities."""
    print("🚀 PICARD Enhanced Variable Substitution Demo")
    print("=" * 50)
    
    # Initialize template processor
    processor = TemplateProcessor()
    
    # Demo templates showcasing enhanced variables
    demo_templates = [
        {
            'name': 'Business Scenario',
            'template': 'Employee {{semantic1:person_name}} in {{semantic2:department}} department earns ${{number1:40000:120000:currency}} annually'
        },
        {
            'name': 'Project Management',
            'template': 'Assign {{semantic1:person_name}} to {{entity1:colors}} project with budget ${{number1:10000:50000:currency}} due in {{number2:30:180}} days'
        },
        {
            'name': 'System Configuration',
            'template': 'Deploy {{entity1:metals}} server for {{semantic1:company}} with {{number1:8:64}} GB RAM and timeout {{number2:30:300}} seconds'
        },
        {
            'name': 'Mixed Variables',
            'template': 'Archive {{entity1}} files and {{semantic1:person_name}} data to {{entity2:gems}} backup with {{number1:85:99:percentage}}% compression'
        },
        {
            'name': 'E-commerce Scenario',
            'template': 'Customer {{semantic1:person_name}} from {{semantic2:city}} purchased {{semantic3:product}} for ${{number1:25:500:decimal}} with {{number2:5:15}} day shipping'
        },
        {
            'name': 'Academic Records',
            'template': 'Student {{semantic1:person_name}} scored {{number1:60:100}}% in {{semantic2:course}} during {{semantic3:semester}}'
        }
    ]
    
    question_id = 1001
    sample_number = 1
    
    for i, demo in enumerate(demo_templates, 1):
        print(f"\n{i}. {demo['name']}")
        print("-" * 40)
        print(f"Template: {demo['template']}")
        
        try:
            result = processor.process_template(demo['template'], question_id, sample_number)
            print(f"Result:   {result['substituted']}")
            
            # Show variable breakdown
            if result.get('variables'):
                print("Variables:")
                for var_name, var_value in result['variables'].items():
                    print(f"  {var_name} → {var_value}")
            
        except Exception as e:
            print(f"ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Demo completed successfully!")
    print("\nKey Features Demonstrated:")
    print("• Semantic variables: {{semantic1:person_name}}, {{semantic2:department}}")
    print("• Numeric ranges: {{number1:10:100}}, {{number2:1000:5000:currency}}")
    print("• Enhanced entity pools: {{entity1:colors}}, {{entity2:metals}}")
    print("• Legacy compatibility: {{entity1}} still works")
    print("• Variable consistency: Same variable = same value throughout test")
    print("• Mixed usage: All variable types can be used together")


if __name__ == "__main__":
    main()