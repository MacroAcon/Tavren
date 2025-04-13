#!/usr/bin/env python3
"""
Buyer Query Simulation Script

This script demonstrates how buyer queries get processed through Tavren's 
privacy-enhancing technology (PET) stack. It simulates a buyer requesting 
store visit frequency analysis and shows the results with different 
privacy protections applied.

The script:
1. Generates a sample user dataset
2. Processes the query with raw (no privacy), DP, and SMPC methods
3. Displays a side-by-side comparison of results
4. Visualizes privacy-utility tradeoffs
5. Reports performance metrics
"""

import sys
import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Tuple
import random
import datetime
import argparse

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.utils.insight_processor import process_insight, QueryType, PrivacyMethod

# Set style for plots
sns.set_style("whitegrid")
plt.rcParams.update({'font.size': 12})

def generate_mock_data(num_users: int = 100, num_weeks: int = 4) -> pd.DataFrame:
    """
    Generate a synthetic dataset of store visits for demo purposes
    
    Args:
        num_users: Number of users to simulate
        num_weeks: Number of weeks of data to generate
        
    Returns:
        DataFrame with user store visit data
    """
    print(f"Generating mock data for {num_users} users over {num_weeks} weeks...")
    
    # Define parameters for the dataset
    store_categories = ["grocery", "clothing", "electronics", "home_goods", "restaurant"]
    districts = ["north", "south", "east", "west", "central"]
    
    # Probability of visit by store category
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
                    
                    for _ in range(max(1, num_visits)):  # Ensure at least one visit
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

def split_for_smpc(df: pd.DataFrame, num_parties: int = 3) -> List[Dict]:
    """
    Split a dataset into multiple parties for SMPC simulation
    
    Args:
        df: Input DataFrame with user visit data
        num_parties: Number of parties to split data between
        
    Returns:
        List of dictionaries representing different data parties
    """
    # Get unique users
    users = df["user_id"].unique()
    
    # Shuffle users
    np.random.shuffle(users)
    
    # Split users among parties
    users_per_party = len(users) // num_parties
    party_user_lists = [users[i*users_per_party:(i+1)*users_per_party] for i in range(num_parties)]
    
    # If there are leftover users, distribute them
    leftover = len(users) % num_parties
    for i in range(leftover):
        party_user_lists[i] = np.append(party_user_lists[i], users[-(i+1)])
    
    # Create party data
    party_data = []
    for i, party_users in enumerate(party_user_lists):
        # Filter data for this party's users
        party_df = df[df["user_id"].isin(party_users)].copy()
        
        # Add party_id column
        party_df["party_id"] = i
        
        # Create party data dictionary
        party_data.append({
            "party_id": i,
            "users": party_users.tolist(),
            "data": party_df
        })
    
    return party_data

def get_raw_results(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate raw (non-private) results for average store visits
    
    Args:
        df: DataFrame with store visit data
        
    Returns:
        Dictionary mapping categories to average visits
    """
    # Group by user_id and store_category to get visit counts
    visit_counts = df.groupby(["user_id", "store_category"]).size().reset_index()
    visit_counts.columns = ["user_id", "store_category", "visit_count"]
    
    # Calculate average by category
    avg_visits = visit_counts.groupby("store_category")["visit_count"].mean().to_dict()
    
    return avg_visits

def run_queries(df: pd.DataFrame, epsilon_values: List[float]) -> Dict[str, Any]:
    """
    Run queries with different privacy methods and parameters
    
    Args:
        df: Input DataFrame with store visit data
        epsilon_values: List of epsilon values to test for DP
        
    Returns:
        Dictionary with results and performance metrics
    """
    results = {}
    metrics = {}
    
    # Get raw results (no privacy)
    start_time = time.time()
    raw_results = get_raw_results(df)
    raw_time = time.time() - start_time
    
    results["raw"] = raw_results
    metrics["raw"] = {
        "processing_time_ms": round(raw_time * 1000, 2)
    }
    
    # Run DP queries with different epsilon values
    for epsilon in epsilon_values:
        start_time = time.time()
        dp_result = process_insight(
            data=df,
            query_type=QueryType.AVERAGE_STORE_VISITS,
            pet_method=PrivacyMethod.DP,
            epsilon=epsilon
        )
        dp_time = time.time() - start_time
        
        key = f"dp_epsilon_{epsilon}"
        results[key] = dp_result["result"]
        metrics[key] = {
            "processing_time_ms": round(dp_time * 1000, 2),
            "epsilon": epsilon
        }
    
    # Run SMPC query
    try:
        # Split data for SMPC
        party_data = split_for_smpc(df)
        
        start_time = time.time()
        smpc_result = process_insight(
            data=party_data,
            query_type=QueryType.AVERAGE_STORE_VISITS,
            pet_method=PrivacyMethod.SMPC
        )
        smpc_time = time.time() - start_time
        
        results["smpc"] = smpc_result["result"]
        metrics["smpc"] = {
            "processing_time_ms": round(smpc_time * 1000, 2),
            "num_parties": len(party_data)
        }
    except Exception as e:
        print(f"Error running SMPC query: {str(e)}")
        print("SMPC results will not be included in the comparison.")
        results["smpc"] = None
        metrics["smpc"] = {
            "error": str(e)
        }
    
    return {
        "results": results,
        "metrics": metrics
    }

def calculate_errors(result_dict: Dict[str, Dict[str, float]], raw_results: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    """
    Calculate error metrics for each privacy method compared to raw results
    
    Args:
        result_dict: Dictionary of results from different methods
        raw_results: Raw (non-private) results for comparison
        
    Returns:
        Dictionary with error metrics for each method
    """
    errors = {}
    
    for method, results in result_dict.items():
        if method == "raw" or results is None:
            continue
        
        # Calculate absolute errors
        abs_errors = {}
        rel_errors = {}
        
        for category, raw_value in raw_results.items():
            if category in results:
                abs_errors[category] = abs(results[category] - raw_value)
                rel_errors[category] = abs_errors[category] / raw_value * 100 if raw_value > 0 else 0
        
        # Calculate mean errors
        mean_abs_error = sum(abs_errors.values()) / len(abs_errors) if abs_errors else 0
        mean_rel_error = sum(rel_errors.values()) / len(rel_errors) if rel_errors else 0
        
        errors[method] = {
            "absolute_errors": abs_errors,
            "relative_errors": rel_errors,
            "mean_absolute_error": mean_abs_error,
            "mean_relative_error": mean_rel_error
        }
    
    return errors

def print_results_table(results: Dict[str, Dict[str, float]], metrics: Dict[str, Dict[str, Any]], errors: Dict[str, Dict[str, float]]):
    """
    Print a formatted table of results and metrics
    
    Args:
        results: Results from different privacy methods
        metrics: Performance metrics for each method
        errors: Error metrics for each method
    """
    # Extract methods and categories
    methods = list(results.keys())
    if "raw" in methods:
        # Ensure raw comes first
        methods.remove("raw")
        methods = ["raw"] + methods
    
    categories = set()
    for method_results in results.values():
        if method_results:
            categories.update(method_results.keys())
    categories = sorted(categories)
    
    # Print header
    print("\n" + "="*80)
    print("BUYER QUERY RESULTS: AVERAGE STORE VISITS".center(80))
    print("="*80)
    
    # Print results table
    print("\nResults by Category:")
    print("-" * 80)
    
    # Header row
    row_format = "{:<15}" + "{:>12}" * len(methods)
    header = ["Category"] + methods
    print(row_format.format(*header))
    print("-" * 80)
    
    # Data rows
    for category in categories:
        row = [category]
        for method in methods:
            if results[method] and category in results[method]:
                row.append(f"{results[method][category]:.2f}")
            else:
                row.append("N/A")
        print(row_format.format(*row))
    
    # Print error metrics
    print("\nError Metrics:")
    print("-" * 80)
    
    print("Mean Relative Error (%):")
    row = [""]
    for method in methods:
        if method == "raw":
            row.append("0.00")
        elif method in errors and "mean_relative_error" in errors[method]:
            row.append(f"{errors[method]['mean_relative_error']:.2f}")
        else:
            row.append("N/A")
    print(row_format.format(*header))
    print(row_format.format(*row))
    
    # Print performance metrics
    print("\nPerformance Metrics:")
    print("-" * 80)
    
    print("Processing Time (ms):")
    row = [""]
    for method in methods:
        if method in metrics and "processing_time_ms" in metrics[method]:
            row.append(f"{metrics[method]['processing_time_ms']:.2f}")
        else:
            row.append("N/A")
    print(row_format.format(*header))
    print(row_format.format(*row))
    
    # Print additional metrics
    print("\nAdditional Parameters:")
    print("-" * 80)
    
    for method in methods:
        if method.startswith("dp_epsilon_"):
            epsilon = metrics[method].get("epsilon", "N/A")
            print(f"{method}: epsilon = {epsilon}")
        elif method == "smpc":
            if "num_parties" in metrics[method]:
                num_parties = metrics[method]["num_parties"]
                print(f"{method}: num_parties = {num_parties}")
            elif "error" in metrics[method]:
                print(f"{method}: Error - {metrics[method]['error']}")
    
    print("\n" + "="*80)

def plot_results(results: Dict[str, Dict[str, float]], errors: Dict[str, Dict[str, float]], output_dir: str = None):
    """
    Generate visualizations of the results and privacy-utility tradeoff
    
    Args:
        results: Results from different privacy methods
        errors: Error metrics for each method
        output_dir: Directory to save plot images (if None, will display instead)
    """
    # Extract categories and methods
    categories = set()
    methods = []
    
    for method, method_results in results.items():
        if method_results:
            methods.append(method)
            categories.update(method_results.keys())
    
    categories = sorted(categories)
    
    # Filter out None results
    valid_results = {k: v for k, v in results.items() if v is not None}
    
    # Create a DataFrame for easier plotting
    plot_data = pd.DataFrame(columns=["Category", "Method", "Value"])
    for method, method_results in valid_results.items():
        for category, value in method_results.items():
            plot_data = plot_data.append({
                "Category": category,
                "Method": method,
                "Value": value
            }, ignore_index=True)
    
    # Ensure raw is first in the order
    method_order = ["raw"] + [m for m in methods if m != "raw"]
    
    # Plot results comparison
    plt.figure(figsize=(12, 8))
    g = sns.barplot(x="Category", y="Value", hue="Method", data=plot_data, order=categories, hue_order=method_order)
    plt.title("Average Store Visits by Category and Privacy Method", fontsize=16)
    plt.xlabel("Store Category", fontsize=14)
    plt.ylabel("Average Visits", fontsize=14)
    plt.legend(title="Method", fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        plt.savefig(os.path.join(output_dir, "results_comparison.png"), dpi=300)
    else:
        plt.show()
    
    # Plot error rates
    if errors:
        error_data = pd.DataFrame(columns=["Method", "Category", "Error (%)"])
        for method, error_dict in errors.items():
            if "relative_errors" in error_dict:
                for category, error in error_dict["relative_errors"].items():
                    error_data = error_data.append({
                        "Method": method,
                        "Category": category,
                        "Error (%)": error
                    }, ignore_index=True)
        
        # Only include DP methods in the privacy-utility plot
        dp_methods = [m for m in method_order if m.startswith("dp_epsilon_")]
        dp_epsilons = [float(m.split("_")[-1]) for m in dp_methods]
        
        if dp_methods and len(dp_methods) > 1:
            # Plot privacy-utility tradeoff
            plt.figure(figsize=(10, 6))
            
            # Extract mean error for each epsilon
            mean_errors = [errors[m]["mean_relative_error"] for m in dp_methods]
            
            plt.plot(dp_epsilons, mean_errors, 'o-', linewidth=2, markersize=10)
            plt.title("Privacy-Utility Tradeoff", fontsize=16)
            plt.xlabel("Epsilon (Privacy Parameter)", fontsize=14)
            plt.ylabel("Mean Relative Error (%)", fontsize=14)
            plt.xscale("log")
            plt.grid(True, alpha=0.3)
            
            # Add annotations
            for i, eps in enumerate(dp_epsilons):
                plt.annotate(f"ε={eps}", 
                           xy=(eps, mean_errors[i]),
                           xytext=(10, 0), 
                           textcoords="offset points",
                           fontsize=12)
            
            plt.tight_layout()
            
            if output_dir:
                plt.savefig(os.path.join(output_dir, "privacy_utility_tradeoff.png"), dpi=300)
            else:
                plt.show()
        
        # Plot error by category and method
        plt.figure(figsize=(12, 8))
        g = sns.barplot(x="Category", y="Error (%)", hue="Method", data=error_data, order=categories)
        plt.title("Error Rate by Category and Privacy Method", fontsize=16)
        plt.xlabel("Store Category", fontsize=14)
        plt.ylabel("Relative Error (%)", fontsize=14)
        plt.legend(title="Method", fontsize=12)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if output_dir:
            plt.savefig(os.path.join(output_dir, "error_by_category.png"), dpi=300)
        else:
            plt.show()

def main():
    """Main function to run the simulation"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Simulate buyer queries with privacy-enhancing technologies")
    parser.add_argument("--users", type=int, default=100, help="Number of users to generate in the mock dataset")
    parser.add_argument("--weeks", type=int, default=4, help="Number of weeks of data to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, default=None, help="Directory to save output plots")
    args = parser.parse_args()
    
    # Set random seed for reproducibility
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    print("\nTavren Buyer Query Simulation")
    print("-" * 40)
    
    # Generate mock data
    df = generate_mock_data(num_users=args.users, num_weeks=args.weeks)
    
    # Run queries with different privacy methods
    epsilon_values = [0.1, 1.0, 10.0]  # Low, medium, high privacy
    print(f"\nRunning queries with epsilon values: {epsilon_values}")
    
    query_results = run_queries(df, epsilon_values)
    results = query_results["results"]
    metrics = query_results["metrics"]
    
    # Calculate errors
    errors = calculate_errors(results, results["raw"])
    
    # Print results table
    print_results_table(results, metrics, errors)
    
    # Plot results
    plot_results(results, errors, args.output)
    
    if args.output:
        print(f"\nPlots saved to: {args.output}")
    else:
        print("\nPlots displayed. Close the plot windows to exit.")
    
    print("\nSimulation complete!")

if __name__ == "__main__":
    main() 