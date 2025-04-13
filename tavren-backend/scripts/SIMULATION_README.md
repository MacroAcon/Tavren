# Tavren Buyer Query Simulation

This script simulates how buyer queries get processed through Tavren's privacy-enhancing technology (PET) stack. It demonstrates the privacy-utility tradeoff between different privacy methods (DP and SMPC) and parameter settings.

## Setup

Ensure you have the required dependencies:

```bash
pip install -r simulation_requirements.txt
```

## Running the Simulation

Basic usage:

```bash
python simulate_buyer_query.py
```

This will:
1. Generate a synthetic dataset of retail store visits
2. Process queries using raw (no privacy), DP (with multiple epsilon values), and SMPC methods
3. Display results and visualizations
4. Print performance metrics

### Command-line Options

- `--users N`: Number of users to generate in the mock dataset (default: 100)
- `--weeks N`: Number of weeks of data to generate (default: 4)
- `--seed N`: Random seed for reproducibility (default: 42)
- `--output DIR`: Directory to save output plots (default: display only)

Example with options:

```bash
python simulate_buyer_query.py --users 200 --weeks 8 --output ./simulation_results
```

## Understanding the Results

The simulation provides:

1. **Results Table**: Side-by-side comparison of average store visits by category across methods
2. **Error Metrics**: How much each privacy method deviates from the raw (true) values
3. **Performance Metrics**: Processing time for each method
4. **Visualizations**:
   - Bar chart comparing results across methods and categories
   - Privacy-utility tradeoff curve for DP with different epsilon values
   - Error rates by category and method

## Key Insights

- **DP with ε=0.1**: Highest privacy protection but largest error
- **DP with ε=1.0**: Good balance of privacy and utility (recommended for most use cases)
- **DP with ε=10.0**: High accuracy but reduced privacy protection
- **SMPC**: Exact computation (no noise) but requires coordination between parties

## Example Output

```
BUYER QUERY RESULTS: AVERAGE STORE VISITS
================================================================================

Results by Category:
--------------------------------------------------------------------------------
Category            raw     dp_epsilon_0.1  dp_epsilon_1.0  dp_epsilon_10.0        smpc
--------------------------------------------------------------------------------
clothing           2.35            2.93            2.28            2.38            2.35
electronics        1.98            6.14            2.65            2.05            1.98
grocery            4.05            7.26            3.77            4.04            4.05
home_goods         2.15            1.29            1.72            2.12            2.15
restaurant         2.27            0.78            1.45            2.41            2.27

Error Metrics:
--------------------------------------------------------------------------------
Mean Relative Error (%):
Category            raw     dp_epsilon_0.1  dp_epsilon_1.0  dp_epsilon_10.0        smpc
                             89.93           13.48            1.65            0.00

Performance Metrics:
--------------------------------------------------------------------------------
Processing Time (ms):
Category            raw     dp_epsilon_0.1  dp_epsilon_1.0  dp_epsilon_10.0        smpc
                    1.25          28.42           27.12           26.55         1245.67
```

## Next Steps

- Add more query types beyond average store visits
- Implement additional PET methods
- Create an interactive dashboard 