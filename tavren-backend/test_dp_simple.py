import pandas as pd
import numpy as np
from app.utils.insight_processor import apply_dp_to_average

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