#!/usr/bin/env python3
"""
Retail Store Visit Frequency Analysis with Differential Privacy

This script implements differential privacy for analyzing average store visit
frequency across retail categories. It demonstrates how different epsilon
values affect the privacy-utility tradeoff.

Use case: Calculate average weekly store visits per user across retail categories
and time segments (weekday vs weekend) with added noise for privacy protection.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import random
from typing import Dict, List, Tuple
import seaborn as sns

# New imports for OpenDP
import opendp.prelude as dp
from opendp.measurements import make_base_laplace

# Try to enable features if available in current version
try:
    from opendp.mod import enable_features
    enable_features("contrib")
except (ImportError, AttributeError):
    print("Note: Running without OpenDP contrib features - using core functionality")


def generate_mock_data(num_users: int = 100, num_weeks: int = 4) -> pd.DataFrame:
    """
    Generate mock data for retail store visits
    
    Args:
        num_users: Number of users to simulate
        num_weeks: Number of weeks of data to generate
        
    Returns:
        DataFrame with columns: user_id, timestamp, store_category, district, is_weekend
    """
    print(f"Generating mock data for {num_users} users over {num_weeks} weeks...")
    
    # Define parameters
    store_categories = ["grocery", "clothing", "electronics", "home_goods", "restaurant"]
    districts = ["north", "south", "east", "west", "central"]
    
    # Probability of visit by store category (some stores are visited more frequently)
    category_weights = {
        "grocery": 0.5,      # People visit grocery stores most often
        "clothing": 0.15,
        "electronics": 0.1,
        "home_goods": 0.1,
        "restaurant": 0.15
    }
    
    # Weekend vs weekday visit probability
    weekend_bias = {
        "grocery": 1.2,      # 20% more grocery visits on weekends
        "clothing": 2.0,     # Twice as many clothing visits on weekends
        "electronics": 1.5,  
        "home_goods": 1.8,
        "restaurant": 1.3
    }
    
    # Generate data
    start_date = datetime.datetime.now() - datetime.timedelta(weeks=num_weeks)
    
    data = []
    
    # Each user has their own visiting patterns
    for user_id in range(1, num_users + 1):
        # Personalize frequency of visits (some users shop more than others)
        user_activity_level = random.uniform(0.5, 2.0)
        
        # Each user has category preferences
        user_category_bias = {
            cat: random.uniform(0.7, 1.3) for cat in store_categories
        }
        
        # For each day in the time period
        for day in range(num_weeks * 7):
            current_date = start_date + datetime.timedelta(days=day)
            is_weekend = 1 if current_date.weekday() >= 5 else 0
            
            # For each store category
            for category in store_categories:
                # Calculate probability of visit based on all factors
                base_prob = category_weights[category] * user_activity_level * user_category_bias[category]
                
                # Adjust for weekend
                if is_weekend:
                    base_prob *= weekend_bias[category]
                
                # Determine if user visits this type of store on this day
                if random.random() < base_prob / 10:  # Divide by 10 to make visits less frequent
                    # User might visit multiple times in a day
                    num_visits = np.random.poisson(1.2)  # Poisson distribution with mean 1.2
                    
                    for _ in range(num_visits):
                        district = random.choice(districts)
                        data.append({
                            "user_id": user_id,
                            "timestamp": current_date,
                            "store_category": category,
                            "district": district,
                            "is_weekend": is_weekend
                        })
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    print(f"Generated {len(df)} store visits for {num_users} users")
    
    return df


def aggregate_visits(df: pd.DataFrame) -> Tuple[Dict, Dict, Dict]:
    """
    Aggregate visits by category and weekend/weekday
    
    Args:
        df: DataFrame with visit data
        
    Returns:
        Tuple of dictionaries with aggregated data:
        (visits_by_category, visits_by_category_weekend, visits_by_user_category)
    """
    # Get number of unique users
    num_users = df["user_id"].nunique()
    
    # Calculate total visits by category
    visits_by_category = df.groupby("store_category").size().to_dict()
    visits_by_category = {k: v / (num_users * 4) for k, v in visits_by_category.items()}  # 4 weeks
    
    # Calculate weekend visits by category
    weekend_df = df[df["is_weekend"] == 1]
    visits_by_category_weekend = weekend_df.groupby("store_category").size().to_dict()
    weekend_users = num_users  # All users potentially available on weekends
    weekend_days = 8  # 8 weekend days in 4 weeks
    visits_by_category_weekend = {
        k: v / (weekend_users * weekend_days / 7) for k, v in visits_by_category_weekend.items()
    }
    
    # Calculate visits by user and category (for user-level DP)
    visits_by_user_category = df.groupby(["user_id", "store_category"]).size().reset_index()
    visits_by_user_category.columns = ["user_id", "store_category", "visit_count"]
    
    # Convert to dictionary for easier access
    user_category_dict = {}
    for _, row in visits_by_user_category.iterrows():
        if row["store_category"] not in user_category_dict:
            user_category_dict[row["store_category"]] = []
        user_category_dict[row["store_category"]].append(row["visit_count"] / 4)  # 4 weeks
    
    return visits_by_category, visits_by_category_weekend, user_category_dict


def apply_dp_to_visits(user_category_dict: Dict, epsilon_values: List[float]) -> Dict:
    """
    Apply differential privacy to visit counts with various epsilon values
    
    Args:
        user_category_dict: Dictionary of visit counts by category and user
        epsilon_values: List of epsilon values to test
        
    Returns:
        Dictionary with DP results for each epsilon
    """
    results = {}
    
    # Get true means for comparison
    true_means = {
        category: np.mean(counts) 
        for category, counts in user_category_dict.items()
    }
    
    for epsilon in epsilon_values:
        dp_means = {}
        errors = {}
        
        for category, counts in user_category_dict.items():
            # Get bounds for the data
            lower = 0
            upper = max(counts) * 1.1  # Set upper bound slightly higher than observed
            
            # Calculate sensitivity for the mean
            sensitivity = (upper - lower) / len(counts)
            
            # Calculate scale parameter for Laplace noise
            scale = sensitivity / epsilon
            
            # Calculate true mean
            true_mean = np.mean(counts)
            
            # Add Laplace noise to the mean using OpenDP
            noise = make_base_laplace().eval(scale=scale, location=0.0)
            dp_mean = true_mean + noise
            
            # Clamp the result to the valid range
            dp_mean = max(lower, min(dp_mean, upper))
            
            # Store result and calculate error
            dp_means[category] = dp_mean
            errors[category] = abs(dp_mean - true_means[category]) / true_means[category] * 100  # Percent error
        
        results[epsilon] = {
            "dp_means": dp_means,
            "errors": errors,
            "avg_error": np.mean(list(errors.values()))
        }
    
    return results


def analyze_dp_results(results: Dict, true_means: Dict) -> None:
    """
    Analyze and visualize DP results
    
    Args:
        results: Dictionary with DP results
        true_means: True means for comparison
    """
    # Prepare data for visualization
    epsilons = list(results.keys())
    avg_errors = [results[eps]["avg_error"] for eps in epsilons]
    
    # Create a figure with two subplots
    plt.figure(figsize=(15, 10))
    
    # Plot 1: Average error vs epsilon
    plt.subplot(2, 1, 1)
    plt.plot(epsilons, avg_errors, 'o-', linewidth=2)
    plt.title("Privacy-Utility Tradeoff: Error vs. Epsilon")
    plt.xlabel("Epsilon (ε)")
    plt.ylabel("Average Percent Error")
    plt.grid(True)
    plt.xscale('log')
    
    # Plot 2: True vs DP means for each category
    plt.subplot(2, 1, 2)
    
    # Set up the bar chart
    categories = list(true_means.keys())
    x = np.arange(len(categories))
    width = 0.15  # Width of bars
    
    # Plot true means
    plt.bar(x - 2*width, [true_means[cat] for cat in categories], width, label='True Mean')
    
    # Plot DP means for each epsilon
    for i, eps in enumerate(epsilons):
        dp_means = results[eps]["dp_means"]
        plt.bar(x + (i-1)*width, [dp_means[cat] for cat in categories], width, label=f'ε = {eps}')
    
    plt.title("Effect of Different Epsilon Values on Store Visit Estimates")
    plt.xlabel("Store Category")
    plt.ylabel("Average Weekly Visits")
    plt.xticks(x, categories, rotation=45)
    plt.legend()
    plt.grid(True, axis='y')
    
    plt.tight_layout()
    plt.savefig("dp_analysis_results.png")
    print("Analysis charts saved to dp_analysis_results.png")


def print_dp_insights(results: Dict, true_means: Dict) -> None:
    """
    Print insights about the DP results
    
    Args:
        results: Dictionary with DP results
        true_means: True means for comparison
    """
    print("\n===== DIFFERENTIAL PRIVACY ANALYSIS RESULTS =====")
    print("\nTrue average weekly visits per user:")
    for category, mean in true_means.items():
        print(f"  {category}: {mean:.2f}")
    
    print("\nDifferential Privacy Results:")
    for epsilon, result in sorted(results.items()):
        print(f"\nEpsilon (ε) = {epsilon}:")
        print(f"  Average error: {result['avg_error']:.2f}%")
        
        # Show individual category results
        for category in true_means.keys():
            dp_mean = result["dp_means"][category]
            error = result["errors"][category]
            print(f"  {category}: {dp_mean:.2f} (error: {error:.2f}%)")
    
    # Print insights about the privacy-utility tradeoff
    print("\n===== INSIGHTS =====")
    
    # Sort epsilons for analysis
    sorted_epsilons = sorted(results.keys())
    lowest_eps = sorted_epsilons[0]
    highest_eps = sorted_epsilons[-1]
    
    # Compare highest privacy (lowest epsilon) to lowest privacy (highest epsilon)
    high_privacy_error = results[lowest_eps]["avg_error"]
    low_privacy_error = results[highest_eps]["avg_error"]
    error_reduction = high_privacy_error - low_privacy_error
    
    print(f"1. Increasing epsilon from {lowest_eps} to {highest_eps} reduces average error by {error_reduction:.2f}%")
    
    # Identify which categories are most affected by DP
    category_sensitivity = {}
    for category in true_means.keys():
        sensitivity = np.std([results[eps]["dp_means"][category] for eps in results.keys()])
        category_sensitivity[category] = sensitivity
    
    most_sensitive = max(category_sensitivity.items(), key=lambda x: x[1])[0]
    least_sensitive = min(category_sensitivity.items(), key=lambda x: x[1])[0]
    
    print(f"2. '{most_sensitive}' is most sensitive to privacy parameters (highest variance in estimates)")
    print(f"3. '{least_sensitive}' is least sensitive to privacy parameters (most stable across epsilon values)")
    
    # Estimate a reasonable epsilon for this use case
    reasonable_errors = [eps for eps, res in results.items() if res["avg_error"] < 10]
    if reasonable_errors:
        recommended_epsilon = min(reasonable_errors)
        print(f"4. Recommended epsilon: {recommended_epsilon} (achieves <10% average error)")
    else:
        print("4. No tested epsilon values achieve <10% average error, consider testing higher values")
    
    print("\n5. Key biases introduced by DP:")
    # Check for bias (are certain categories systematically over or underestimated?)
    bias_pattern = {}
    for category in true_means.keys():
        estimates = [results[eps]["dp_means"][category] for eps in results.keys()]
        avg_estimate = np.mean(estimates)
        true_value = true_means[category]
        bias = (avg_estimate - true_value) / true_value * 100
        bias_pattern[category] = bias
        
        if bias > 5:
            print(f"  - '{category}' is systematically OVERESTIMATED by {bias:.1f}%")
        elif bias < -5:
            print(f"  - '{category}' is systematically UNDERESTIMATED by {abs(bias):.1f}%")
    
    # Check for tail impact (high or low values more affected)
    high_freq_categories = sorted(true_means.items(), key=lambda x: x[1], reverse=True)[:2]
    low_freq_categories = sorted(true_means.items(), key=lambda x: x[1])[:2]
    
    high_freq_avg_error = np.mean([
        results[highest_eps]["errors"][cat] for cat, _ in high_freq_categories
    ])
    low_freq_avg_error = np.mean([
        results[highest_eps]["errors"][cat] for cat, _ in low_freq_categories
    ])
    
    print("\n6. Tail impact analysis:")
    if high_freq_avg_error > low_freq_avg_error * 1.2:
        print("  - High-frequency categories are more affected by noise (>20% higher error)")
    elif low_freq_avg_error > high_freq_avg_error * 1.2:
        print("  - Low-frequency categories are more affected by noise (>20% higher error)")
    else:
        print("  - Both high and low-frequency categories are similarly affected by noise")


def main():
    """Main function to run the analysis"""
    print("==== Retail Store Visit Frequency Analysis with Differential Privacy ====")
    
    # Generate mock data
    df = generate_mock_data(num_users=200, num_weeks=4)
    
    # Aggregate data
    visits_by_category, visits_by_category_weekend, user_category_dict = aggregate_visits(df)
    
    # Print original aggregated data
    print("\n=== Original Aggregated Data (without DP) ===")
    print("\nAverage Weekly Visits per User by Category:")
    for category, avg_visits in visits_by_category.items():
        print(f"  {category}: {avg_visits:.2f}")
    
    print("\nAverage Weekend Visits per User by Category (per weekend day):")
    for category, avg_visits in visits_by_category_weekend.items():
        print(f"  {category}: {avg_visits:.2f}")
    
    # Apply DP with various epsilon values
    epsilon_values = [0.01, 0.1, 0.5, 1.0, 10.0]
    results = apply_dp_to_visits(user_category_dict, epsilon_values)
    
    # Get true means for comparison
    true_means = {
        category: np.mean(counts) 
        for category, counts in user_category_dict.items()
    }
    
    # Print and visualize results
    print_dp_insights(results, true_means)
    analyze_dp_results(results, true_means)
    
    print("\n==== Analysis Complete ====")
    print("This implementation demonstrates differential privacy applied to retail visit frequency analysis.")
    print("The results show how different epsilon values affect the privacy-utility tradeoff.")


if __name__ == "__main__":
    main() 