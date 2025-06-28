#!/usr/bin/env python3
"""
Results Processing Script for LLM Performance Analysis

Usage: python process_results.py <path_to_main_results_folder>

This script processes scores.json files from LLM result subdirectories and generates
consolidated CSV summaries for overall performance and performance by scoring type.
"""

import os
import sys
import json
import csv
from pathlib import Path


def load_scores_json(llm_folder_path):
    """Load and parse the scores.json file from an LLM folder."""
    scores_file = os.path.join(llm_folder_path, 'scores.json')
    
    if not os.path.exists(scores_file):
        print(f"Warning: scores.json not found in {llm_folder_path}")
        return None
    
    try:
        with open(scores_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing scores.json in {llm_folder_path}: {e}")
        return None
    except Exception as e:
        print(f"Error reading scores.json in {llm_folder_path}: {e}")
        return None


def create_consolidated_results_dir(main_results_folder):
    """Create the consolidated_results directory if it doesn't exist."""
    consolidated_dir = os.path.join(main_results_folder, 'consolidated_results')
    os.makedirs(consolidated_dir, exist_ok=True)
    return consolidated_dir


def generate_rounds_csv(all_llm_data, output_dir):
    """Generate a CSV showing inference rounds for each question/sample across all LLMs."""
    csv_path = os.path.join(output_dir, 'rounds.csv')
    
    # First, determine all unique question/sample combinations
    all_question_samples = set()
    for llm_data in all_llm_data:
        llm_folder_path = llm_data.get('llm_folder_path')
        conversations_dir = os.path.join(llm_folder_path, 'conversations')
        
        if os.path.exists(conversations_dir):
            for filename in os.listdir(conversations_dir):
                if filename.endswith('.json') and filename.startswith('q'):
                    # Extract question and sample from filename (e.g., q101_s1.json)
                    base_name = filename.replace('.json', '')
                    all_question_samples.add(base_name)
    
    # Sort the question/sample combinations for consistent ordering
    all_question_samples = sorted(list(all_question_samples))
    
    # Collect LLM names for column headers
    llm_names = [llm_data['llm_name'] for llm_data in all_llm_data]
    
    # Build the rounds data matrix
    rounds_data = {}
    
    for llm_data in all_llm_data:
        llm_name = llm_data['llm_name']
        llm_folder_path = llm_data.get('llm_folder_path')
        conversations_dir = os.path.join(llm_folder_path, 'conversations')
        
        rounds_data[llm_name] = {}
        
        # Initialize all question/sample combinations to 0
        for qs in all_question_samples:
            rounds_data[llm_name][qs] = 0
        
        # Load actual data from conversation files
        if os.path.exists(conversations_dir):
            for filename in os.listdir(conversations_dir):
                if filename.endswith('.json') and filename.startswith('q'):
                    base_name = filename.replace('.json', '')
                    file_path = os.path.join(conversations_dir, filename)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            conversation_data = json.load(f)
                            
                        # Extract inference rounds from statistics
                        statistics = conversation_data.get('statistics', {})
                        inference_rounds = statistics.get('inference_rounds', 0)
                        
                        rounds_data[llm_name][base_name] = inference_rounds
                        
                    except (json.JSONDecodeError, Exception) as e:
                        print(f"Warning: Could not read {file_path}: {e}")
                        # Keep the default value of 0
    
    # Calculate statistics for each question
    def calculate_mode(values):
        """Calculate mode (most frequent value) from a list of numbers."""
        from collections import Counter
        if not values:
            return 0
        counter = Counter(values)
        mode_count = max(counter.values())
        modes = [k for k, v in counter.items() if v == mode_count]
        return min(modes)  # Return smallest mode if there are ties
    
    # Group question/samples by question number
    questions_data = {}
    for qs in all_question_samples:
        # Extract question number (e.g., "101" from "q101_s1")
        question_num = qs.split('_')[0][1:]  # Remove 'q' prefix
        if question_num not in questions_data:
            questions_data[question_num] = []
        questions_data[question_num].append(qs)
    
    # Write the CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        header = ['Question_Sample'] + llm_names
        writer.writerow(header)
        
        # Write data rows
        for qs in all_question_samples:
            row = [qs]
            for llm_name in llm_names:
                rounds = rounds_data[llm_name].get(qs, 0)
                row.append(rounds)
            writer.writerow(row)
        
        # Add summary statistics for each question
        writer.writerow([])  # Empty row separator
        
        for question_num in sorted(questions_data.keys()):
            question_samples = questions_data[question_num]
            
            # Calculate statistics for each LLM for this question
            avg_row = [f'Average_q{question_num}']
            max_row = [f'Max_q{question_num}']
            min_row = [f'Min_q{question_num}']
            mode_row = [f'Mode_q{question_num}']
            
            for llm_name in llm_names:
                # Get all rounds for this question and LLM
                question_rounds = [rounds_data[llm_name].get(qs, 0) for qs in question_samples]
                
                # Calculate statistics
                avg_rounds = sum(question_rounds) / len(question_rounds) if question_rounds else 0
                max_rounds = max(question_rounds) if question_rounds else 0
                min_rounds = min(question_rounds) if question_rounds else 0
                mode_rounds = calculate_mode(question_rounds)
                
                avg_row.append(round(avg_rounds, 2))
                max_row.append(max_rounds)
                min_row.append(min_rounds)
                mode_row.append(mode_rounds)
            
            # Write the statistics rows
            writer.writerow(avg_row)
            writer.writerow(max_row)
            writer.writerow(min_row)
            writer.writerow(mode_row)
    
    print(f"✓ Generated rounds.csv")



def process_all_llm_folders(main_results_folder):
    """Process all LLM folders and collect their data."""
    all_llm_data = []
    
    # Get all subdirectories in the main results folder
    for item in os.listdir(main_results_folder):
        item_path = os.path.join(main_results_folder, item)
        
        # Skip if not a directory or if it's our consolidated_results folder
        if not os.path.isdir(item_path) or item == 'consolidated_results':
            continue
        
        llm_name = item
        print(f"Processing {llm_name}...")
        
        # Load scores data
        scores_data = load_scores_json(item_path)
        if scores_data is None:
            print(f"  ✗ Skipping {llm_name} - could not load scores.json")
            continue
        
        all_llm_data.append({
            'llm_name': llm_name,
            'llm_folder_path': item_path,  # Store the folder path for conversation access
            'scores_data': scores_data
        })
        print(f"  ✓ Loaded data for {llm_name}")
    
    return all_llm_data


def generate_overall_performance_csv(all_llm_data, output_dir):
    """Generate consolidated overall performance CSV for all LLMs."""
    csv_path = os.path.join(output_dir, 'overall_performance.csv')
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['LLM_Name', 'Test_ID', 'Timestamp', 'Total_Questions', 
                        'Correct_Answers', 'Accuracy_Percentage'])
        
        # Write data for each LLM
        for llm_data in all_llm_data:
            llm_name = llm_data['llm_name']
            metadata = llm_data['scores_data'].get('metadata', {})
            
            total_questions = metadata.get('total_questions', 0)
            correct_answers = metadata.get('correct_answers', 0)
            accuracy_percentage = metadata.get('accuracy_percentage', 0.0)
            test_id = metadata.get('test_id', 'N/A')
            timestamp = metadata.get('timestamp', 'N/A')
            
            writer.writerow([llm_name, test_id, timestamp, total_questions, 
                            correct_answers, accuracy_percentage])
    
    print(f"✓ Generated consolidated overall_performance.csv")


def generate_scoring_type_performance_csv(all_llm_data, output_dir):
    """Generate consolidated performance by scoring type CSV for all LLMs."""
    csv_path = os.path.join(output_dir, 'performance_by_scoring_type.csv')
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['LLM_Name', 'Scoring_Type', 'Correct', 'Total', 'Accuracy_Percentage'])
        
        # Write data for each LLM and scoring type
        for llm_data in all_llm_data:
            llm_name = llm_data['llm_name']
            by_scoring_type = llm_data['scores_data'].get('by_scoring_type', {})
            
            for scoring_type, stats in by_scoring_type.items():
                correct = stats.get('correct', 0)
                total = stats.get('total', 0)
                
                # Calculate accuracy percentage
                accuracy_pct = (correct / total * 100) if total > 0 else 0.0
                
                writer.writerow([llm_name, scoring_type, correct, total, round(accuracy_pct, 2)])
    
    print(f"✓ Generated consolidated performance_by_scoring_type.csv")


def generate_html_dashboard(all_llm_data, output_dir):
    """Generate an interactive HTML dashboard with charts."""
    html_path = os.path.join(output_dir, 'dashboard.html')
    
    # Prepare data for charts
    llm_names = []
    overall_accuracies = []
    
    # Collect all unique scoring types
    all_scoring_types = set()
    for llm_data in all_llm_data:
        by_scoring_type = llm_data['scores_data'].get('by_scoring_type', {})
        all_scoring_types.update(by_scoring_type.keys())
    
    all_scoring_types = sorted(list(all_scoring_types))
    
    # Prepare data for overall performance chart
    for llm_data in all_llm_data:
        llm_name = llm_data['llm_name']
        metadata = llm_data['scores_data'].get('metadata', {})
        accuracy = metadata.get('accuracy_percentage', 0.0)
        
        llm_names.append(llm_name)
        overall_accuracies.append(accuracy)
    
    # Prepare data for scoring type performance chart
    scoring_type_data = {}
    for scoring_type in all_scoring_types:
        scoring_type_data[scoring_type] = []
        for llm_data in all_llm_data:
            by_scoring_type = llm_data['scores_data'].get('by_scoring_type', {})
            if scoring_type in by_scoring_type:
                stats = by_scoring_type[scoring_type]
                correct = stats.get('correct', 0)
                total = stats.get('total', 0)
                accuracy = (correct / total * 100) if total > 0 else 0.0
                scoring_type_data[scoring_type].append(accuracy)
            else:
                scoring_type_data[scoring_type].append(0)
    
    # Generate HTML content
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Performance Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }}
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 5px;
        }}
        .chart-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #555;
        }}
        canvas {{
            max-height: 500px;
        }}
        .stats-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #e8f4fd;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 24px;
            font-weight: bold;
            color: #2196F3;
        }}
        .stat-label {{
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 LLM Performance Dashboard</h1>
        
        <div class="stats-summary">
            <div class="stat-card">
                <div class="stat-number">{len(all_llm_data)}</div>
                <div class="stat-label">Models Tested</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(all_scoring_types)}</div>
                <div class="stat-label">Scoring Types</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{max(overall_accuracies):.1f}%</div>
                <div class="stat-label">Best Performance</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{sum(overall_accuracies)/len(overall_accuracies):.1f}%</div>
                <div class="stat-label">Average Performance</div>
            </div>
        </div>

        <div class="chart-container">
            <div class="chart-title">📊 Overall Performance by Model</div>
            <canvas id="overallChart"></canvas>
        </div>

        <div class="chart-container">
            <div class="chart-title">🎯 Performance by Scoring Type</div>
            <canvas id="scoringTypeChart"></canvas>
        </div>
    </div>

    <script>
        // Overall Performance Chart
        const overallCtx = document.getElementById('overallChart').getContext('2d');
        new Chart(overallCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(llm_names)},
                datasets: [{{
                    label: 'Overall Accuracy (%)',
                    data: {json.dumps(overall_accuracies)},
                    backgroundColor: 'rgba(33, 150, 243, 0.8)',
                    borderColor: 'rgba(33, 150, 243, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        title: {{
                            display: true,
                            text: 'Accuracy (%)'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'LLM Models'
                        }}
                    }}
                }}
            }}
        }});

        // Scoring Type Performance Chart
        const scoringCtx = document.getElementById('scoringTypeChart').getContext('2d');
        const colors = [
            'rgba(255, 99, 132, 0.8)',
            'rgba(54, 162, 235, 0.8)',
            'rgba(255, 205, 86, 0.8)',
            'rgba(75, 192, 192, 0.8)',
            'rgba(153, 102, 255, 0.8)',
            'rgba(255, 159, 64, 0.8)'
        ];
        
        const datasets = [];
        {json.dumps(all_scoring_types)}.forEach((scoringType, index) => {{
            datasets.push({{
                label: scoringType,
                data: {json.dumps(scoring_type_data)}[scoringType],
                backgroundColor: colors[index % colors.length],
                borderColor: colors[index % colors.length].replace('0.8', '1'),
                borderWidth: 1
            }});
        }});

        new Chart(scoringCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(llm_names)},
                datasets: datasets
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'top'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        title: {{
                            display: true,
                            text: 'Accuracy (%)'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'LLM Models'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Generated interactive dashboard.html")


def main():
    """Main function to process all LLM folders and generate consolidated results."""
    if len(sys.argv) != 2:
        print("Usage: python process_results.py <path_to_main_results_folder>")
        sys.exit(1)
    
    main_results_folder = sys.argv[1]
    
    # Validate main results folder exists
    if not os.path.exists(main_results_folder):
        print(f"Error: Main results folder '{main_results_folder}' does not exist.")
        sys.exit(1)
    
    if not os.path.isdir(main_results_folder):
        print(f"Error: '{main_results_folder}' is not a directory.")
        sys.exit(1)
    
    print(f"Processing results from: {main_results_folder}")
    print("=" * 60)
    
    # Process all LLM folders
    all_llm_data = process_all_llm_folders(main_results_folder)
    
    if not all_llm_data:
        print("\nNo valid LLM data found. Exiting.")
        sys.exit(1)
    
    print(f"\nSuccessfully processed {len(all_llm_data)} LLM(s)")
    
    # Create consolidated results directory
    output_dir = create_consolidated_results_dir(main_results_folder)
    print(f"\nGenerating consolidated results in: {output_dir}")
    
    # Generate consolidated CSV files and dashboard
    try:
        generate_overall_performance_csv(all_llm_data, output_dir)
        generate_scoring_type_performance_csv(all_llm_data, output_dir)
        generate_rounds_csv(all_llm_data, output_dir)
        generate_html_dashboard(all_llm_data, output_dir)
        
        print(f"\n✅ Processing complete! Check the consolidated_results folder for:")
        print(f"   - overall_performance.csv")
        print(f"   - performance_by_scoring_type.csv")
        print(f"   - rounds.csv")
        print(f"   - dashboard.html (open this in your browser!)")
        
    except Exception as e:
        print(f"\n❌ Error generating consolidated CSV files: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()