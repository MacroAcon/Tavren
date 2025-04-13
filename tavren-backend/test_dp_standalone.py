import pandas as pd
import numpy as np

def apply_dp_to_average(data: pd.DataFrame, epsilon: float) -> dict:
    """
    Apply differential privacy to average store visits calculation
    
    Args:
        data: DataFrame with store visit data
        epsilon: Privacy parameter (higher = more accuracy, less privacy)
        
    Returns:
        Dictionary mapping categories to privacy-protected average visits
    """
    print(f"Applying DP with epsilon {epsilon} to average store visits")
    
    # Get unique categories
    if 'store_category' not in data.columns:
        raise ValueError("Data must contain 'store_category' column")
    
    categories = data['store_category'].unique()
    num_users = data['user_id'].nunique()
    
    # Create a dictionary to store counts per user and category
    user_category_dict = {}
    
    # Group by user_id and store_category to get visit counts
    visit_counts = data.groupby(['user_id', 'store_category']).size().reset_index()
    visit_counts.columns = ['user_id', 'store_category', 'visit_count']
    
    # Convert to dictionary for easier access
    for _, row in visit_counts.iterrows():
        category = row['store_category']
        if category not in user_category_dict:
            user_category_dict[category] = []
        # Normalize by number of time periods if needed
        user_category_dict[category].append(row['visit_count'])
    
    # Apply DP to each category
    dp_results = {}
    
    for category, counts in user_category_dict.items():
        # Calculate sensitivity (assuming bounded contribution)
        lower_bound = 0
        upper_bound = max(counts) * 1.1  # Set upper bound slightly higher than observed max
        sensitivity = (upper_bound - lower_bound) / len(counts)
        
        # Calculate true mean
        true_mean = np.mean(counts)
        
        # Add calibrated Laplace noise
        scale = sensitivity / epsilon
        noise = np.random.laplace(0, scale)
        dp_mean = true_mean + noise
        
        # Clamp to valid range (non-negative)
        dp_mean = max(0, dp_mean)
        
        dp_results[category] = dp_mean
    
    return dp_results

# Set random seed for reproducible results
np.random.seed(42)

# Create sample data with 3 users visiting 3 store categories
data = []
users = [1, 2, 3]
categories = ["grocery", "clothing", "electronics"]

for user_id in users:
    for category in categories:
        # Each user has different visit patterns
        if category == "grocery":
            visits = 5 if user_id == 1 else (3 if user_id == 2 else 4)
        elif category == "clothing":
            visits = 2 if user_id == 1 else (4 if user_id == 2 else 1)
        else:  # electronics
            visits = 1 if user_id == 1 else (2 if user_id == 2 else 3)
        
        # Add visits to data
        for _ in range(visits):
            data.append({
                "user_id": user_id,
                "store_category": category,
                "district": "test",
                "is_weekend": 0
            })

# Convert to DataFrame
df = pd.DataFrame(data)

# Process with high epsilon (10.0) - high accuracy
high_accuracy = apply_dp_to_average(df, 10.0)
print("High accuracy results (ε=10.0):", high_accuracy)

# Process with low epsilon (0.1) - high privacy
high_privacy = apply_dp_to_average(df, 0.1)
print("High privacy results (ε=0.1):", high_privacy)

# Calculate average error for both results
true_values = {
    "grocery": 4.0,       # (5+3+4)/3
    "clothing": 2.33,     # (2+4+1)/3
    "electronics": 2.0    # (1+2+3)/3
}

high_accuracy_error = sum(abs(high_accuracy[k] - v) for k, v in true_values.items()) / 3
high_privacy_error = sum(abs(high_privacy[k] - v) for k, v in true_values.items()) / 3

# Print results
print(f"High accuracy error (ε=10.0): {high_accuracy_error:.2f}")
print(f"High privacy error (ε=0.1): {high_privacy_error:.2f}")
print("High accuracy results:", high_accuracy)
print("High privacy results:", high_privacy)

# Verify high privacy has higher error
assert high_privacy_error > high_accuracy_error
print("Test passed!") 