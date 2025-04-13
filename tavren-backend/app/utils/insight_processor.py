#!/usr/bin/env python3
"""
Insight Processor Module

This module serves as a centralized processor for data insight requests,
applying either Differential Privacy (DP) or Secure Multi-Party Computation (SMPC)
to protect user privacy while providing valuable insights.

The processor acts as a bridge between raw data and privacy-preserving insights,
choosing the appropriate privacy-enhancing technology based on configuration.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Union, Optional
import pandas as pd
import time
import importlib.util
import os
import sys
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

# Define enums for supported query types and privacy methods
class QueryType(str, Enum):
    AVERAGE_STORE_VISITS = "average_store_visits"

class PrivacyMethod(str, Enum):
    DP = "dp"
    SMPC = "smpc"

def validate_input(data: Any, query_type: str, pet_method: str, epsilon: Optional[float] = None) -> bool:
    """
    Validate input parameters for the insight processor
    
    Args:
        data: Input data (DataFrame or dictionary)
        query_type: Type of query to process
        pet_method: Privacy-enhancing technology method to use
        epsilon: Privacy parameter for differential privacy (if applicable)
        
    Returns:
        bool: True if input is valid, False otherwise
        
    Raises:
        ValueError: If input validation fails
    """
    # Check data type
    if not isinstance(data, (pd.DataFrame, dict, list)):
        raise ValueError("Data must be a pandas DataFrame, dictionary, or list")
    
    # Check query type
    if query_type not in [qt.value for qt in QueryType]:
        valid_types = [qt.value for qt in QueryType]
        raise ValueError(f"Query type '{query_type}' not supported. Valid types: {valid_types}")
    
    # Check PET method
    if pet_method not in [pm.value for pm in PrivacyMethod]:
        valid_methods = [pm.value for pm in PrivacyMethod]
        raise ValueError(f"Privacy method '{pet_method}' not supported. Valid methods: {valid_methods}")
    
    # Check epsilon for DP
    if pet_method == PrivacyMethod.DP:
        if epsilon is None:
            raise ValueError("Epsilon parameter is required for differential privacy")
        if not isinstance(epsilon, (int, float)) or epsilon <= 0:
            raise ValueError("Epsilon must be a positive number")
    
    return True

def apply_dp_to_average(data: pd.DataFrame, epsilon: float) -> Dict[str, float]:
    """
    Apply differential privacy to average store visits calculation
    
    Args:
        data: DataFrame with store visit data
        epsilon: Privacy parameter (higher = more accuracy, less privacy)
        
    Returns:
        Dictionary mapping categories to privacy-protected average visits
    """
    logger.info(f"Applying DP with epsilon {epsilon} to average store visits")
    
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

def apply_smpc_to_average(data: List[Dict]) -> Dict[str, float]:
    """
    Apply SMPC simulation to average store visits calculation
    
    This function imports and uses logic from the retail_visit_smpc_simulation.py
    script to simulate a secure multi-party computation.
    
    Args:
        data: List of dictionaries representing different data parties
        
    Returns:
        Dictionary mapping categories to secure computed average visits
    """
    logger.info("Applying SMPC to average store visits")
    
    # Import the SMPC simulation module dynamically
    scripts_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scripts')
    smpc_file = os.path.join(scripts_path, 'retail_visit_smpc_simulation.py')
    
    if not os.path.exists(smpc_file):
        raise ImportError(f"SMPC simulation file not found at {smpc_file}")
    
    # Create a spec for the module
    spec = importlib.util.spec_from_file_location("smpc_simulation", smpc_file)
    smpc_module = importlib.util.module_from_spec(spec)
    sys.modules["smpc_simulation"] = smpc_module
    spec.loader.exec_module(smpc_module)
    
    # Extract the necessary functions
    Party = smpc_module.Party
    
    # Convert input data to Party objects
    parties = []
    for i, party_data in enumerate(data):
        # Create a Party object with the party's data
        party = Party(i, len(party_data.get('users', [])))
        # Override the generated data with provided data
        if isinstance(party_data.get('data'), pd.DataFrame):
            party.data = party_data['data']
        parties.append(party)
    
    # Simulate the SMPC protocol
    num_parties = len(parties)
    categories = set()
    for party in parties:
        if isinstance(party.data, pd.DataFrame) and 'store_category' in party.data.columns:
            categories.update(party.data['store_category'].unique())
    categories = list(categories)
    
    # Compute and exchange secret shares
    for i, sender in enumerate(parties):
        shares = sender.compute_secret_shares(categories, num_parties)
        for j, receiver in enumerate(parties):
            if i != j:
                receiver.receive_share(i, shares[j])
    
    # Compute local sums
    local_sums = [party.compute_local_sum(categories) for party in parties]
    
    # Final result is any party's local sum (they should all be the same)
    result = local_sums[0]
    
    return result

def process_insight(data: Any, query_type: str, pet_method: str, epsilon: Optional[float] = None) -> Dict[str, Any]:
    """
    Process an insight request with the specified privacy-enhancing technology
    
    Args:
        data: Input data (format depends on query_type and pet_method)
        query_type: Type of query to process
        pet_method: Privacy-enhancing technology method to use
        epsilon: Privacy parameter for differential privacy (if applicable)
        
    Returns:
        Dictionary containing the privacy-protected insight result
        
    Raises:
        ValueError: If input validation fails
        NotImplementedError: If query type or PET method is valid but not implemented
    """
    start_time = time.time()
    logger.info(f"Processing insight request: query_type={query_type}, pet_method={pet_method}")
    
    try:
        # Validate input
        validate_input(data, query_type, pet_method, epsilon)
        
        result = {}
        
        # Process based on query type and PET method
        if query_type == QueryType.AVERAGE_STORE_VISITS:
            if pet_method == PrivacyMethod.DP:
                if not isinstance(data, pd.DataFrame):
                    raise ValueError("DP method requires data as a pandas DataFrame")
                result = apply_dp_to_average(data, epsilon)
            elif pet_method == PrivacyMethod.SMPC:
                if not isinstance(data, list):
                    raise ValueError("SMPC method requires data as a list of party data")
                result = apply_smpc_to_average(data)
            else:
                # This shouldn't happen due to validation, but just in case
                raise NotImplementedError(f"PET method {pet_method} not implemented for {query_type}")
        else:
            # This shouldn't happen due to validation, but just in case
            raise NotImplementedError(f"Query type {query_type} not implemented")
        
        # Add metadata to result
        processing_time = time.time() - start_time
        metadata = {
            "query_type": query_type,
            "pet_method": pet_method,
            "processing_time_ms": round(processing_time * 1000, 2)
        }
        
        if pet_method == PrivacyMethod.DP:
            metadata["epsilon"] = epsilon
        
        return {
            "result": result,
            "metadata": metadata
        }
    
    except Exception as e:
        logger.error(f"Error processing insight: {str(e)}", exc_info=True)
        raise 