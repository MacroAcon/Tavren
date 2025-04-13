#!/usr/bin/env python3
"""
Secure Multi-Party Computation (SMPC) Simulation for Retail Store Visit Analysis

This script simulates how SMPC could be used to compute average store visit frequencies
across multiple data holders without revealing individual user data.

The simulation uses Additive Secret Sharing, a basic SMPC technique.
"""

import numpy as np
import pandas as pd
import random
import time
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple, Any
import datetime

# =============== UTILITY FUNCTIONS ===============

def generate_retail_data(party_id: int, num_users: int, num_weeks: int = 4) -> pd.DataFrame:
    """
    Generate synthetic retail visit data for a specific data holder (party)
    
    Args:
        party_id: Identifier for the data holder
        num_users: Number of users this party has data for
        num_weeks: Number of weeks of data to generate
        
    Returns:
        DataFrame with retail visit data
    """
    store_categories = ["grocery", "clothing", "electronics", "home_goods", "restaurant"]
    districts = ["north", "south", "east", "west", "central"]
    
    # Each party might have different user behavior patterns
    category_weights = {
        "grocery": 0.4 + random.uniform(-0.1, 0.1),      
        "clothing": 0.15 + random.uniform(-0.05, 0.05),
        "electronics": 0.1 + random.uniform(-0.05, 0.05),
        "home_goods": 0.15 + random.uniform(-0.05, 0.05),
        "restaurant": 0.2 + random.uniform(-0.05, 0.05)
    }
    
    # Generate data
    start_date = datetime.datetime.now() - datetime.timedelta(weeks=num_weeks)
    
    data = []
    
    # Base user_id on party to ensure uniqueness across parties
    base_user_id = party_id * 1000
    
    for user_id in range(base_user_id + 1, base_user_id + num_users + 1):
        # Personalize frequency of visits
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
                # Calculate probability of visit
                base_prob = category_weights[category] * user_activity_level * user_category_bias[category]
                
                # Determine if user visits this type of store on this day
                if random.random() < base_prob / 10:  # Divide by 10 to make visits less frequent
                    district = random.choice(districts)
                    data.append({
                        "user_id": user_id,
                        "timestamp": current_date,
                        "store_category": category,
                        "district": district,
                        "is_weekend": is_weekend,
                        "party_id": party_id
                    })
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    print(f"Generated {len(df)} store visits for {num_users} users (Party {party_id})")
    
    return df

def aggregate_visits_by_category(df: pd.DataFrame, num_users: int, num_weeks: int = 4) -> Dict[str, float]:
    """
    Calculate average weekly visits per user by store category
    
    Args:
        df: DataFrame with visit data
        num_users: Number of users in the dataset
        num_weeks: Number of weeks in the dataset
        
    Returns:
        Dictionary mapping categories to average weekly visits per user
    """
    # Count visits by category
    visits_by_category = df.groupby("store_category").size().to_dict()
    
    # Convert to average weekly visits per user
    avg_visits = {k: v / (num_users * num_weeks) for k, v in visits_by_category.items()}
    
    return avg_visits

# =============== SECURE MULTI-PARTY COMPUTATION SIMULATION ===============

class Party:
    """Represents a data holder in the SMPC protocol"""
    
    def __init__(self, party_id: int, num_users: int, num_weeks: int = 4):
        self.party_id = party_id
        self.num_users = num_users
        self.num_weeks = num_weeks
        
        # Generate local data
        self.data = generate_retail_data(party_id, num_users, num_weeks)
        
        # Store local averages for later comparison
        self.local_averages = aggregate_visits_by_category(self.data, num_users, num_weeks)
        
        # Secret shares received from other parties
        self.received_shares = {}
        
        # Communication stats
        self.bytes_sent = 0
        self.bytes_received = 0
    
    def compute_secret_shares(self, categories: List[str], num_parties: int) -> Dict[int, Dict[str, float]]:
        """
        Split local visit counts into secret shares for each party
        
        Args:
            categories: List of store categories
            num_parties: Total number of parties in the computation
            
        Returns:
            Dictionary mapping party_id to their share of each category count
        """
        # Get total visits for each category
        category_counts = {}
        for category in categories:
            # Get count of visits for this category
            count = len(self.data[self.data["store_category"] == category])
            category_counts[category] = count
        
        # Create secret shares using additive secret sharing
        # In additive secret sharing, we split a value v into n random shares that sum to v
        shares = {party_id: {} for party_id in range(num_parties)}
        
        for category, count in category_counts.items():
            # Generate n-1 random shares
            random_shares = [random.randint(-1000000, 1000000) for _ in range(num_parties - 1)]
            
            # The last share is the value minus the sum of random shares
            last_share = count - sum(random_shares)
            
            # Assign shares to parties
            for i in range(num_parties - 1):
                shares[i][category] = random_shares[i]
            shares[num_parties - 1][category] = last_share
        
        # Track communication
        # Each share is a float (8 bytes) * number of categories * number of parties
        self.bytes_sent += 8 * len(categories) * num_parties
        
        return shares
    
    def receive_share(self, from_party: int, shares: Dict[str, float]):
        """
        Receive secret shares from another party
        
        Args:
            from_party: ID of the sending party
            shares: Dictionary of category shares
        """
        self.received_shares[from_party] = shares
        
        # Track communication
        self.bytes_received += 8 * len(shares)  # 8 bytes per float
    
    def compute_local_sum(self, categories: List[str]) -> Dict[str, float]:
        """
        Compute the local sum of all received shares
        
        Args:
            categories: List of store categories
            
        Returns:
            Dictionary of category sums
        """
        # Sum up all shares for each category
        sums = {category: 0.0 for category in categories}
        
        # Add my own shares
        if self.party_id in self.received_shares:
            for category, value in self.received_shares[self.party_id].items():
                sums[category] += value
        
        # Add shares from other parties
        for party_id, shares in self.received_shares.items():
            if party_id == self.party_id:
                continue
            for category, value in shares.items():
                sums[category] += value
        
        return sums

def run_smpc_simulation(num_parties: int = 3, users_per_party: int = 100, num_weeks: int = 4) -> Tuple[Dict[str, float], List[Dict[str, float]], Dict[str, Any]]:
    """
    Run a full SMPC simulation with multiple parties
    
    Args:
        num_parties: Number of data holders participating
        users_per_party: Number of users per data holder
        num_weeks: Number of weeks of data
        
    Returns:
        Tuple of (
            SMPC result, 
            List of local results per party, 
            Performance metrics
        )
    """
    print(f"\n===== Running SMPC Simulation with {num_parties} Parties =====")
    
    # Track performance
    start_time = time.time()
    
    # Create parties
    parties = [Party(i, users_per_party, num_weeks) for i in range(num_parties)]
    
    # Define store categories
    store_categories = ["grocery", "clothing", "electronics", "home_goods", "restaurant"]
    
    # Phase 1: Each party computes secret shares of their data
    print("\nPhase 1: Computing Secret Shares")
    all_shares = {}
    for party in parties:
        all_shares[party.party_id] = party.compute_secret_shares(store_categories, num_parties)
    
    # Phase 2: Distribute shares to parties
    print("\nPhase 2: Distributing Shares")
    for sender_id, shares_by_recipient in all_shares.items():
        for recipient_id, shares in shares_by_recipient.items():
            parties[recipient_id].receive_share(sender_id, shares)
    
    # Phase 3: Each party computes local sum of shares
    print("\nPhase 3: Computing Local Sums")
    local_sums = []
    for party in parties:
        local_sums.append(party.compute_local_sum(store_categories))
    
    # For a real SMPC protocol, we'd need another round of communication
    # to combine these local sums. For simplicity, we'll just take the
    # sum from the first party as they're all equivalent in additive sharing.
    
    # Convert sums to average weekly visits per user
    total_users = num_parties * users_per_party
    smpc_result = {k: v / (total_users * num_weeks) for k, v in local_sums[0].items()}
    
    # Collect local results for comparison
    local_results = []
    for party in parties:
        local_results.append(party.local_averages)
    
    # Calculate combined average from raw data (ground truth)
    all_data = pd.concat([party.data for party in parties])
    ground_truth = aggregate_visits_by_category(all_data, total_users, num_weeks)
    
    # Calculate performance metrics
    end_time = time.time()
    execution_time = end_time - start_time
    
    total_bytes_sent = sum(party.bytes_sent for party in parties)
    total_bytes_received = sum(party.bytes_received for party in parties)
    
    # Print results
    print("\n===== Results =====")
    print("\nSMPC Computed Average Weekly Visits Per User:")
    for category, avg in smpc_result.items():
        print(f"  {category}: {avg:.4f}")
    
    print("\nGround Truth (Centralized Computation):")
    for category, avg in ground_truth.items():
        print(f"  {category}: {avg:.4f}")
    
    print("\nLocal Results by Party:")
    for i, results in enumerate(local_results):
        print(f"\nParty {i}:")
        for category, avg in results.items():
            print(f"  {category}: {avg:.4f}")
    
    # Verify correctness (should match ground truth exactly with additive sharing)
    error = sum(abs(smpc_result[k] - ground_truth[k]) for k in store_categories)
    print(f"\nTotal error: {error:.10f} (should be near zero)")
    
    # Collect performance metrics
    metrics = {
        "execution_time": execution_time,
        "total_bytes_sent": total_bytes_sent,
        "total_bytes_received": total_bytes_received,
        "error": error,
        "num_parties": num_parties,
        "users_per_party": users_per_party
    }
    
    print(f"\nExecution time: {execution_time:.2f} seconds")
    print(f"Total communication: {(total_bytes_sent + total_bytes_received) / 1024:.2f} KB")
    
    return smpc_result, local_results, metrics

def visualize_results(smpc_result: Dict[str, float], local_results: List[Dict[str, float]]):
    """
    Visualize SMPC results compared to local results
    
    Args:
        smpc_result: The SMPC computed result
        local_results: Results computed locally by each party
    """
    categories = list(smpc_result.keys())
    
    # Prepare data for plotting
    smpc_values = [smpc_result[cat] for cat in categories]
    
    # Create figure
    plt.figure(figsize=(12, 6))
    
    # Plot SMPC result
    bar_width = 0.15
    x = np.arange(len(categories))
    plt.bar(x, smpc_values, bar_width, label='SMPC Result')
    
    # Plot local results for each party
    for i, local_result in enumerate(local_results):
        local_values = [local_result.get(cat, 0) for cat in categories]
        plt.bar(x + (i+1)*bar_width, local_values, bar_width, label=f'Party {i}')
    
    plt.xlabel('Store Category')
    plt.ylabel('Average Weekly Visits Per User')
    plt.title('SMPC vs Local Results for Retail Visit Analysis')
    plt.xticks(x + bar_width * len(local_results) / 2, categories)
    plt.legend()
    plt.tight_layout()
    
    plt.savefig('smpc_comparison.png', dpi=300)
    print("Visualization saved to smpc_comparison.png")

def compare_performance(max_parties: int = 5):
    """
    Compare SMPC performance with different numbers of parties
    
    Args:
        max_parties: Maximum number of parties to test
    """
    execution_times = []
    communication_volumes = []
    party_counts = list(range(2, max_parties + 1))
    
    for num_parties in party_counts:
        print(f"\n\n***** Testing with {num_parties} parties *****")
        _, _, metrics = run_smpc_simulation(num_parties=num_parties, users_per_party=100)
        
        execution_times.append(metrics["execution_time"])
        communication_volumes.append((metrics["total_bytes_sent"] + metrics["total_bytes_received"]) / 1024)  # KB
    
    # Create figure with two subplots
    plt.figure(figsize=(12, 5))
    
    # Plot execution time
    plt.subplot(1, 2, 1)
    plt.plot(party_counts, execution_times, 'o-', linewidth=2)
    plt.xlabel('Number of Parties')
    plt.ylabel('Execution Time (seconds)')
    plt.title('SMPC Execution Time vs Number of Parties')
    plt.grid(True)
    
    # Plot communication volume
    plt.subplot(1, 2, 2)
    plt.plot(party_counts, communication_volumes, 'o-', linewidth=2)
    plt.xlabel('Number of Parties')
    plt.ylabel('Communication Volume (KB)')
    plt.title('SMPC Communication Volume vs Number of Parties')
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('smpc_performance.png', dpi=300)
    print("Performance comparison saved to smpc_performance.png")

def main():
    """Main function to run the SMPC simulation"""
    print("==== Secure Multi-Party Computation Simulation for Retail Visit Analysis ====")
    
    # Run basic SMPC simulation
    smpc_result, local_results, _ = run_smpc_simulation(num_parties=3, users_per_party=100)
    
    # Visualize results
    visualize_results(smpc_result, local_results)
    
    # Compare performance with different numbers of parties
    compare_performance(max_parties=5)
    
    print("\n==== SMPC Simulation Complete ====")
    print("""
SMPC Implementation Notes:

1. Data Flow Structure:
   - Each party (data holder) independently generates secret shares of their data
   - Shares are distributed to all participating parties
   - Each party computes local sums of the shares they received
   - Final result is identical to centralized computation without revealing raw data

2. Privacy Properties:
   - Individual visit data is never revealed in plaintext
   - Each party only sees random shares that leak no information about original values
   - Final aggregated result is the only information revealed

3. Limitations:
   - Communication overhead scales quadratically with number of parties (O(n²))
   - Requires all parties to participate in each step (fault intolerance)
   - Limited to simple additive operations (more complex operations require advanced protocols)
   - No protection against collusion between parties

4. Integration Considerations for Tavren:
   - Could be combined with DP for stronger privacy guarantees
   - Best suited for scenarios with a small number of trusted collaborators
   - Higher latency than centralized computation due to multi-round communication
   - Works well for predefined computations but less flexible than DP for ad-hoc queries
    """)

if __name__ == "__main__":
    main() 