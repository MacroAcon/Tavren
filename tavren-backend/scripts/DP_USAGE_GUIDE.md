# Differential Privacy Scripts Usage Guide

This guide explains how to run and use the differential privacy (DP) scripts for analyzing the retail store visit frequency use case in Tavren.

## Prerequisites

1. Make sure you have Python 3.7+ installed
2. Install the required Python packages:

```bash
pip install opendp matplotlib numpy pandas seaborn
```

## Available Scripts

### 1. Retail Visit DP Analysis (`retail_visit_dp_analysis.py`)

This script implements differential privacy for retail store visit frequency analysis. It:
- Generates mock retail store visit data
- Applies differential privacy with various epsilon values
- Shows how privacy levels affect result accuracy
- Provides insights on bias, variance, and pattern degradation

**Usage:**
```bash
python retail_visit_dp_analysis.py
```

**Output:**
- Terminal output showing raw vs. DP-protected statistics
- Analysis of error rates at different epsilon values
- Insights about which data categories are most affected by DP noise
- Visualization saved to `dp_analysis_results.png`

### 2. DP Charts Generator (`generate_dp_charts.py`)

This script generates visualizations comparing raw vs. DP-protected results:
- Side-by-side comparison of raw vs. DP results for different categories
- Error rates across various epsilon values
- Ranking stability chart showing how privacy affects the relative ordering of categories

**Usage:**
```bash
python generate_dp_charts.py
```

**Output:**
- `dp_comparison_chart.png`: Bar chart comparing raw vs. DP values
- `dp_analysis_chart.png`: Line chart showing error rates across epsilon values
- `dp_ranking_chart.png`: Heatmap showing ranking stability

## Integration with Tavren

These scripts provide the foundation for implementing differential privacy in Tavren's data packaging layer. To integrate with the full platform:

1. The DP implementation logic in `retail_visit_dp_analysis.py` should be refactored into service modules
2. The epsilon configuration should be parameterized based on user preferences and query type
3. Privacy budget management should be added to track and limit total privacy exposure

See the full implementation recommendations in `docs/tavren-dp-implementation-recommendation.md`.

## Troubleshooting

**Missing packages error:**
If you see `ModuleNotFoundError: No module named 'X'`, install the required package:
```bash
pip install X
```

**OpenDP version compatibility:**
If you encounter OpenDP API compatibility issues, update the script or install a compatible version:
```bash
pip install opendp==0.12.1
```

## Next Steps

After reviewing these scripts and analysis results:

1. Install required dependencies
2. Run both scripts to see the DP analysis in action
3. Review the implementation recommendation document
4. Integrate the DP approach into the data packaging layer according to the roadmap 