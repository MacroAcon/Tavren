#!/usr/bin/env python3
"""
Insight Processor Module

This module serves as a centralized processor for data insight requests,
applying either Differential Privacy (DP) or Secure Multi-Party Computation (SMPC)
to protect user privacy while providing valuable insights.

The processor acts as a bridge between raw data and privacy-preserving insights,
choosing the appropriate privacy-enhancing technology based on configuration.
"""

from __future__ import annotations

import logging
import numpy as np
from typing import Dict, List, Any, Union, Optional, Tuple, TYPE_CHECKING
import pandas as pd
import time
import importlib.util
import os
import sys
from enum import Enum
import json
from datetime import datetime
import random
import math

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logger = logging.getLogger(__name__)

# Define enums for supported query types and privacy methods
# These are duplicated from app.schemas.insight to avoid circular imports
class QueryType(str, Enum):
    AVERAGE_STORE_VISITS = "average_store_visits"

class PrivacyMethod(str, Enum):
    DP = "dp"
    SMPC = "smpc"

# Move imports inside functions to avoid circular imports
# from app.utils.consent_validator import validate_user_consent
# from app.services.consent_ledger import ConsentLedgerService
from app.utils.rate_limit import RateLimiter

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

async def process_insight(
    data: List[Dict[str, Any]],
    query_type: QueryType,
    privacy_method: PrivacyMethod,
    privacy_params: Optional[Dict[str, Any]] = None,
    custom_query: Optional[Dict[str, Any]] = None,
    validate_consent: bool = True,
    user_id_field: str = "user_id",
    db: Optional["AsyncSession"] = None
) -> Dict[str, Any]:
    """
    Process an insight request with the specified privacy-enhancing technology.
    
    This is the main entry point for insight processing. It:
    1. Validates the input data and parameters
    2. Checks user consent and DSR restrictions if requested
    3. Applies the appropriate privacy-enhancing technology
    4. Returns the processed result with metadata
    
    Args:
        data: Input dataset as a list of dictionaries
        query_type: Type of query to process
        privacy_method: Privacy-enhancing technology to use
        privacy_params: Additional parameters for the privacy method
        custom_query: Optional custom query parameters
        validate_consent: Whether to validate user consent
        user_id_field: Field name for user IDs in the data
        db: Optional database session for consent validation
        
    Returns:
        Dictionary with processed result and metadata
    """
    start_time = time.time()
    process_id = os.getpid()
    
    # Initialize results dictionary
    results = {
        "success": False,
        "query_type": query_type.value,
        "privacy_method": privacy_method.value,
        "timestamp": datetime.now().isoformat(),
        "result": None,
        "error": None,
        "metadata": {
            "process_id": process_id,
            "processing_time_ms": 0
        }
    }
    
    try:
        # Validate inputs
        is_valid, error_msg = validate_query_input(data, query_type)
        if not is_valid:
            results["error"] = f"Input validation failed: {error_msg}"
            logger.error(f"Input validation failed: {error_msg}")
            return results
            
        if privacy_method != PrivacyMethod.DP:
            is_valid, error_msg = validate_privacy_params(privacy_method, privacy_params)
            if not is_valid:
                results["error"] = f"Privacy parameters validation failed: {error_msg}"
                logger.error(f"Privacy validation failed: {error_msg}")
                return results
        
        # If consent validation is enabled, extract user IDs and validate
        if validate_consent and db:
            # Extract all user IDs from the data
            user_ids = list(set(item.get(user_id_field) for item in data if user_id_field in item))
            
            # Check for DSR restrictions
            can_process, restricted_users, restriction_msg = await check_dsr_restrictions(db, user_ids)
            if not can_process:
                results["error"] = f"Processing restricted due to DSR: {restriction_msg}"
                results["metadata"]["restricted_users"] = restricted_users
                logger.warning(f"Processing restricted due to DSR for users: {restricted_users}")
                return results
        
        # Process query based on type
        if query_type == QueryType.AVERAGE_STORE_VISITS:
            result = apply_dp_to_average(data, privacy_params.get("epsilon", 1.0))
            
        elif query_type == QueryType.AVERAGE_STORE_VISITS:
            # Identify numeric fields
            numeric_keys = set()
            for item in data:
                for key, value in item.items():
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        numeric_keys.add(key)
            
            # Calculate averages for each numeric field
            averages = {}
            for key in numeric_keys:
                values = [item.get(key) for item in data if key in item and 
                          isinstance(item.get(key), (int, float)) and not isinstance(item.get(key), bool)]
                if values:
                    averages[key] = sum(values) / len(values)
            
            result = {"averages": averages}
            
        elif query_type == QueryType.AVERAGE_STORE_VISITS:
            # Identify numeric fields
            numeric_keys = set()
            for item in data:
                for key, value in item.items():
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        numeric_keys.add(key)
            
            # Calculate sums for each numeric field
            sums = {}
            for key in numeric_keys:
                values = [item.get(key) for item in data if key in item and 
                          isinstance(item.get(key), (int, float)) and not isinstance(item.get(key), bool)]
                if values:
                    sums[key] = sum(values)
            
            result = {"sums": sums}
            
        elif query_type == QueryType.AVERAGE_STORE_VISITS:
            # Identify common fields across records
            keys_sets = [set(item.keys()) for item in data]
            common_keys = set.intersection(*keys_sets) if keys_sets else set()
            
            # Calculate distributions for each common field
            distributions = {}
            for key in common_keys:
                value_counts = {}
                for item in data:
                    value = item.get(key)
                    # Convert complex values to strings for counting
                    if not isinstance(value, (str, int, float, bool)):
                        value = str(value)
                    
                    if value in value_counts:
                        value_counts[value] += 1
                    else:
                        value_counts[value] = 1
                
                distributions[key] = value_counts
            
            result = {"distributions": distributions}
            
        elif query_type == QueryType.AVERAGE_STORE_VISITS:
            # To be implemented - would calculate correlation between numeric fields
            result = {"correlation": "Not implemented yet"}
            
        elif query_type == QueryType.AVERAGE_STORE_VISITS:
            # To be implemented - would analyze trends over time
            result = {"trend": "Not implemented yet"}
            
        elif query_type == QueryType.AVERAGE_STORE_VISITS:
            # Custom query handling
            if not custom_query:
                results["error"] = "Custom query parameters required for custom query type"
                return results
                
            # Process custom query (example implementation)
            result = {"custom": "Custom query implementation example"}
        
        else:
            results["error"] = f"Unsupported query type: {query_type.value}"
            return results
        
        # Apply privacy method if specified
        if privacy_method == PrivacyMethod.DP:
            epsilon = privacy_params.get("epsilon", 1.0)
            delta = privacy_params.get("delta", 1e-5)
            result = apply_differential_privacy(result, epsilon, delta)
            
        elif privacy_method == PrivacyMethod.SMPC:
            # Placeholder for SMPC implementation
            result = result
            results["metadata"]["privacy"] = {
                "method": "secure_multiparty_computation",
                "min_parties": privacy_params.get("min_parties", 3)
            }
            
        else:
            # Other privacy methods would be implemented here
            result = result
            results["metadata"]["privacy"] = {
                "method": privacy_method.value,
                "applied": False,
                "reason": "Method not implemented"
            }
        
        # Update results
        results["result"] = result
        results["success"] = True
        
    except Exception as e:
        logger.exception(f"Error processing insight: {str(e)}")
        results["error"] = f"Processing error: {str(e)}"
        
    finally:
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        results["metadata"]["processing_time_ms"] = round(processing_time, 2)
        
    return results 