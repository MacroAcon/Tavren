# Secure Multi-Party Computation Simulation: Usage Guide

This guide explains how to run and use the SMPC simulation for retail store visit analysis in Tavren.

## Overview

The `retail_visit_smpc_simulation.py` script demonstrates how Secure Multi-Party Computation (SMPC) can be used to compute aggregated statistics across multiple data holders without revealing individual data. It simulates multiple parties each with their own user data, using additive secret sharing to compute average store visit frequencies.

## Prerequisites

1. Make sure you have Python 3.7+ installed
2. Install the required Python packages:

```bash
pip install numpy pandas matplotlib
```

No specialized SMPC libraries are required for this simulation, as it implements additive secret sharing from scratch.

## Running the Simulation

To run the basic simulation:

```bash
python retail_visit_smpc_simulation.py
```

This will:
1. Generate synthetic data for multiple parties (data holders)
2. Run the SMPC protocol to compute average visit frequencies
3. Compare results with local computation by each party
4. Generate visualizations of the results
5. Provide performance metrics

## Simulation Components

### Data Generation

Each simulated party generates synthetic retail store visit data for their users. The data includes:
- User IDs
- Store categories visited (grocery, clothing, electronics, etc.)
- Visit timestamps
- Districts (locations)
- Weekend/weekday flags

### SMPC Protocol Steps

The simulation implements a basic additive secret sharing protocol:

1. **Secret Sharing**: Each party splits their data into random shares that sum to the original value
2. **Distribution**: Shares are distributed to all participating parties
3. **Local Computation**: Each party computes the sum of all shares they received
4. **Result Aggregation**: The final result is calculated without revealing individual inputs

### Performance Analysis

The script measures:
- Execution time for different numbers of parties
- Communication volume (in KB)
- Scaling characteristics as more parties are added

## Customizing the Simulation

You can modify the main function to customize the simulation:

```python
# Run with 5 parties instead of 3
smpc_result, local_results, _ = run_smpc_simulation(num_parties=5, users_per_party=100)

# Use more users per party
smpc_result, local_results, _ = run_smpc_simulation(num_parties=3, users_per_party=500)

# Test with different numbers of parties up to 10
compare_performance(max_parties=10)
```

## Output Files

The simulation generates the following files:

- `smpc_comparison.png`: Bar chart comparing SMPC results with each party's local results
- `smpc_performance.png`: Charts showing execution time and communication volume by number of parties

## Integration with Tavren

This simulation provides a foundation for understanding how SMPC could be integrated with Tavren:

1. **Potential Use Cases**:
   - Collaborations with external data partners (e.g., retailers)
   - Cross-organization analytics
   - Privacy-preserving model training

2. **Implementation Considerations**:
   - Real implementation would require a proper SMPC framework (e.g., PySyft, MP-SPDZ)
   - Additional security mechanisms needed for production use
   - Network communication would need optimization

3. **Hybrid Approach**:
   - Consider combining with differential privacy for stronger guarantees
   - See `docs/tavren-smpc-dp-comparison.md` for a detailed comparison

## Next Steps

After running this simulation:

1. Review the performance characteristics to understand scaling limitations
2. Consider which specific Tavren use cases might benefit from SMPC
3. Explore more advanced SMPC libraries for production implementation
4. Evaluate the privacy-performance tradeoffs compared to DP

For a comparison of SMPC and Differential Privacy approaches for Tavren, see the analysis document at `docs/tavren-smpc-dp-comparison.md`. 