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
    
    # Generate consolidated CSV files
    try:
        generate_overall_performance_csv(all_llm_data, output_dir)
        generate_scoring_type_performance_csv(all_llm_data, output_dir)
        
        print(f"\n✅ Processing complete! Check the consolidated_results folder for:")
        print(f"   - overall_performance.csv")
        print(f"   - performance_by_scoring_type.csv")
        
    except Exception as e:
        print(f"\n❌ Error generating consolidated CSV files: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
