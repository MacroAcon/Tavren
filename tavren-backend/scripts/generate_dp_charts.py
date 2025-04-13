#!/usr/bin/env python3
"""
Generate visualizations for differential privacy analysis of retail store visits.
This creates charts showing privacy-utility tradeoffs for our DP implementation.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Set style
plt.style.use('ggplot')
sns.set_palette("colorblind")

def generate_comparison_chart():
    """Generate side-by-side comparison of raw vs DP results"""
    
    # Define the data
    categories = ['Grocery', 'Clothing', 'Electronics', 'Home Goods', 'Restaurant']
    raw_means = [0.48, 0.15, 0.09, 0.12, 0.16]
    
    # DP values at different epsilon levels
    dp_results = {
        0.1: [0.32, 0.09, 0.15, 0.08, 0.24],
        0.5: [0.46, 0.13, 0.11, 0.13, 0.18],
        1.0: [0.49, 0.16, 0.08, 0.11, 0.17],
        10.0: [0.48, 0.15, 0.09, 0.12, 0.16]
    }
    
    # Create the comparison chart
    plt.figure(figsize=(12, 8))
    
    # Set up the bar positions
    x = np.arange(len(categories))
    width = 0.15
    
    # Plot raw values
    plt.bar(x, raw_means, width, label='Raw Data')
    
    # Plot DP values
    for i, (epsilon, values) in enumerate(dp_results.items()):
        plt.bar(x + (i+1)*width, values, width, label=f'ε = {epsilon}')
    
    plt.xlabel('Store Category')
    plt.ylabel('Average Weekly Visits')
    plt.title('Raw vs. Differentially Private Store Visit Frequency')
    plt.xticks(x + width*2, categories)
    plt.legend(title='Privacy Level')
    plt.tight_layout()
    
    plt.savefig('dp_comparison_chart.png', dpi=300)
    print("Saved dp_comparison_chart.png")

def generate_error_chart():
    """Generate chart showing error rates across epsilon values"""
    
    # Define epsilon values and corresponding error rates
    epsilons = [0.01, 0.1, 0.5, 1.0, 5.0, 10.0]
    avg_errors = [76.2, 44.7, 12.1, 6.9, 1.4, 0.0]
    
    # Error rates by category
    errors_by_category = {
        'Grocery': [68.8, 33.3, 4.2, 2.1, 0.0, 0.0],
        'Clothing': [80.0, 40.0, 13.3, 6.7, 0.0, 0.0],
        'Electronics': [88.9, 66.7, 22.2, 11.1, 0.0, 0.0],
        'Home Goods': [75.0, 33.3, 8.3, 8.3, 0.0, 0.0],
        'Restaurant': [68.8, 50.0, 12.5, 6.3, 0.0, 0.0]
    }
    
    # Create the error chart
    plt.figure(figsize=(10, 6))
    
    # Plot average error curve
    plt.plot(epsilons, avg_errors, 'o-', linewidth=3, markersize=10, label='Average Error')
    
    # Plot error by category
    for category, errors in errors_by_category.items():
        plt.plot(epsilons, errors, '--', linewidth=1.5, alpha=0.7, label=category)
    
    plt.xscale('log')
    plt.xlabel('Epsilon (ε) Value - Log Scale')
    plt.ylabel('Error Rate (%)')
    plt.title('Privacy-Utility Tradeoff: Error vs. Privacy Level')
    plt.legend()
    plt.grid(True, which="both", ls="-", alpha=0.2)
    
    # Add reference lines for recommended thresholds
    plt.axvline(x=0.5, color='gray', linestyle='--', alpha=0.5)
    plt.axvline(x=1.0, color='gray', linestyle='--', alpha=0.5)
    plt.text(0.5, 50, 'ε = 0.5', rotation=90, verticalalignment='center')
    plt.text(1.0, 50, 'ε = 1.0', rotation=90, verticalalignment='center')
    
    # Add shaded regions for utility levels
    plt.axhspan(0, 10, alpha=0.2, color='green', label='Good Utility')
    plt.axhspan(10, 25, alpha=0.2, color='yellow', label='Moderate Utility')
    plt.axhspan(25, 100, alpha=0.2, color='red', label='Poor Utility')
    
    plt.tight_layout()
    plt.savefig('dp_analysis_chart.png', dpi=300)
    print("Saved dp_analysis_chart.png")

def generate_ranking_chart():
    """Generate chart showing ranking stability at different epsilon values"""
    
    # Define the data
    categories = ['Grocery', 'Restaurant', 'Clothing', 'Home Goods', 'Electronics']
    
    # True ranking (1 is highest)
    true_ranks = [1, 2, 3, 4, 5]
    
    # Rankings at different epsilon values
    rankings = {
        0.1: [1, 2, 4, 5, 3],
        0.5: [1, 2, 3, 4, 5],
        1.0: [1, 2, 3, 4, 5],
        10.0: [1, 2, 3, 4, 5]
    }
    
    # Convert rankings to colors (darker = higher rank)
    def rank_to_color(rank):
        return 1 - (rank - 1) / 5  # Normalize to [0, 1]
    
    # Create data for heatmap
    rankings_data = np.array([true_ranks] + [rankings[eps] for eps in [0.1, 0.5, 1.0, 10.0]])
    
    # Create heatmap
    plt.figure(figsize=(10, 4))
    ax = sns.heatmap(
        rankings_data, 
        annot=True, 
        cmap="YlGnBu_r",
        linewidths=.5, 
        yticklabels=['Raw Data', 'ε = 0.1', 'ε = 0.5', 'ε = 1.0', 'ε = 10.0'],
        xticklabels=categories,
        cbar_kws={'label': 'Rank (1 = Most Visited)'}
    )
    
    plt.title('Category Ranking Stability Across Privacy Levels')
    plt.tight_layout()
    plt.savefig('dp_ranking_chart.png', dpi=300)
    print("Saved dp_ranking_chart.png")

def main():
    """Generate all charts for the DP analysis"""
    print("Generating differential privacy analysis visualizations...")
    
    # Generate the three chart types
    generate_comparison_chart()
    generate_error_chart()
    generate_ranking_chart()
    
    print("All charts generated successfully.")

if __name__ == "__main__":
    main() 