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
from typing import Dict, List, Any, Union, Optional, Tuple
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

# Configure logging
logger = logging.getLogger(__name__)

# Define enums for supported query types and privacy methods
class QueryType(str, Enum):
    AVERAGE_STORE_VISITS = "average_store_visits"

class PrivacyMethod(str, Enum):
    DP = "dp"
    SMPC = "smpc"

# Import consent validation utilities
from app.utils.consent_validator import validate_user_consent
from app.services.consent_ledger import ConsentLedgerService
from app.utils.rate_limit import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

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
    data: Any, 
    query_type: str, 
    pet_method: str, 
    epsilon: Optional[float] = None,
    user_id: Optional[str] = None,
    data_scope: Optional[str] = None,
    purpose: Optional[str] = "insight_generation",
    consent_validator = None
) -> Dict[str, Any]:
    """
    Process an insight request with the specified privacy-enhancing technology
    
    Args:
        data: Input data (DataFrame, dictionary, or list)
        query_type: Type of query to process
        pet_method: Privacy-enhancing technology method to use
        epsilon: Privacy parameter for differential privacy (if applicable)
        user_id: Optional ID of the user whose data is being processed
        data_scope: Optional scope of the data being processed (e.g., "location")
        purpose: Optional purpose of processing (default: "insight_generation")
        consent_validator: Optional consent validator instance for checking consent
        
    Returns:
        Dictionary containing processed result and metadata
        
    Raises:
        ValueError: If input validation fails
        PermissionError: If consent validation fails
    """
    start_time = time.time()
    process_id = str(int(start_time * 1000))  # Generate a unique process ID
    
    logger.info(f"Processing insight {process_id} using {pet_method} for query type {query_type}")
    
    # Check consent if validator and user_id are provided
    if consent_validator and user_id and data_scope:
        logger.info(f"Validating consent for user {user_id}, scope '{data_scope}', purpose '{purpose}'")
        try:
            is_allowed, details = await consent_validator.is_processing_allowed(
                user_id=user_id,
                data_scope=data_scope,
                purpose=purpose
            )
            
            if not is_allowed:
                logger.warning(f"Consent validation failed for user {user_id}: {details['reason']}")
                return {
                    "result": None,
                    "metadata": {
                        "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                        "process_id": process_id,
                        "error": "Consent validation failed",
                        "error_details": details,
                        "status": "rejected"
                    }
                }
            
            logger.info(f"Consent validated successfully for user {user_id}, scope '{data_scope}', purpose '{purpose}'")
            
        except Exception as e:
            logger.error(f"Error during consent validation: {str(e)}", exc_info=True)
            return {
                "result": None,
                "metadata": {
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                    "process_id": process_id,
                    "error": "Consent validation error",
                    "error_details": {"message": str(e)},
                    "status": "error"
                }
            }
    
    # Check if user_id, data_scope, and purpose are provided but no validator
    elif user_id and data_scope and not consent_validator:
        logger.warning("User data being processed without consent validation")
    
    # Validate input
    try:
        validate_input(data, query_type, pet_method, epsilon)
    except ValueError as e:
        logger.error(f"Input validation error: {str(e)}")
        return {
            "result": None,
            "metadata": {
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "process_id": process_id,
                "error": "Input validation failed",
                "error_details": {"message": str(e)},
                "status": "error"
            }
        }
    
    # Process based on query type and PET method
    try:
        result = None
        
        if query_type == QueryType.AVERAGE_STORE_VISITS:
            if pet_method == PrivacyMethod.DP:
                result = apply_dp_to_average(data, epsilon)
            elif pet_method == PrivacyMethod.SMPC:
                result = apply_smpc_to_average(data)
        
        if result is None:
            raise NotImplementedError(f"Query type {query_type} with {pet_method} not implemented yet")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Prepare metadata
        metadata = {
            "processing_time_ms": round(processing_time * 1000, 2),
            "process_id": process_id,
            "query_type": query_type,
            "pet_method": pet_method,
            "status": "success"
        }
        
        # Include consent information if available
        if consent_validator and user_id and data_scope:
            metadata["consent_validated"] = True
            metadata["user_id"] = user_id
            metadata["data_scope"] = data_scope
            metadata["purpose"] = purpose
        
        # Include DP specific metadata
        if pet_method == PrivacyMethod.DP and epsilon:
            metadata["epsilon"] = epsilon
            metadata["estimated_error"] = 1.0 / epsilon * 100  # Rough error estimate in percentage
        
        return {
            "result": result,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Error processing insight: {str(e)}", exc_info=True)
        return {
            "result": None,
            "metadata": {
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "process_id": process_id,
                "error": "Processing error",
                "error_details": {"message": str(e)},
                "status": "error"
            }
        }

# Input validation functions
def validate_query_input(data: List[Dict[str, Any]], query_type: QueryType) -> Tuple[bool, str]:
    """
    Validate the input data based on the query type.
    
    Args:
        data: Input data as a list of dictionaries
        query_type: Type of query to run
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not data:
        return False, "Input data is empty"
    
    if not isinstance(data, list):
        return False, "Input data must be a list"
    
    if query_type == QueryType.AVERAGE_STORE_VISITS:
        # Count just needs a list of records
        return True, ""
        
    elif query_type == QueryType.AVERAGE_STORE_VISITS:
        # Check if data contains numeric values to average
        numeric_keys = set()
        for item in data:
            for key, value in item.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    numeric_keys.add(key)
        
        if not numeric_keys:
            return False, "No numeric fields found for averaging"
        return True, ""
        
    elif query_type == QueryType.AVERAGE_STORE_VISITS:
        # Check if data contains numeric values to sum
        numeric_keys = set()
        for item in data:
            for key, value in item.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    numeric_keys.add(key)
        
        if not numeric_keys:
            return False, "No numeric fields found for summing"
        return True, ""
        
    elif query_type == QueryType.AVERAGE_STORE_VISITS:
        # For distribution, all items should have at least one common field
        if not data:
            return False, "Input data is empty"
            
        keys_sets = [set(item.keys()) for item in data]
        common_keys = set.intersection(*keys_sets) if keys_sets else set()
        
        if not common_keys:
            return False, "No common fields across data points for distribution analysis"
        return True, ""
        
    elif query_type == QueryType.AVERAGE_STORE_VISITS:
        # For correlation, need at least two numeric fields
        numeric_keys = set()
        for item in data:
            for key, value in item.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    numeric_keys.add(key)
        
        if len(numeric_keys) < 2:
            return False, "Need at least two numeric fields for correlation analysis"
        return True, ""
        
    elif query_type == QueryType.AVERAGE_STORE_VISITS:
        # For trend analysis, need time field and at least one numeric field
        time_fields = set()
        numeric_fields = set()
        
        for item in data:
            for key, value in item.items():
                if key.lower() in ["time", "date", "timestamp"]:
                    time_fields.add(key)
                elif isinstance(value, (int, float)) and not isinstance(value, bool):
                    numeric_fields.add(key)
        
        if not time_fields:
            return False, "No time/date fields found for trend analysis"
        if not numeric_fields:
            return False, "No numeric fields found for trend analysis"
        return True, ""
        
    return True, ""  # Default case or CUSTOM type

def validate_privacy_params(privacy_method: PrivacyMethod, privacy_params: Optional[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Validate privacy method parameters.
    
    Args:
        privacy_method: The privacy method to use
        privacy_params: Parameters for the privacy method
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if privacy_method == PrivacyMethod.DP:
        if "epsilon" not in privacy_params:
            return False, "Epsilon parameter is required for differential privacy"
        
        epsilon = privacy_params.get("epsilon")
        if not isinstance(epsilon, (int, float)) or epsilon <= 0:
            return False, "Epsilon must be a positive number"
            
        delta = privacy_params.get("delta", 0)
        if not isinstance(delta, (int, float)) or delta < 0 or delta >= 1:
            return False, "Delta must be between 0 and 1"
            
        return True, ""
        
    elif privacy_method == PrivacyMethod.SMPC:
        if "min_parties" not in privacy_params:
            return False, "min_parties parameter is required for SMPC"
            
        min_parties = privacy_params.get("min_parties")
        if not isinstance(min_parties, int) or min_parties < 2:
            return False, "min_parties must be an integer greater than 1"
            
        return True, ""
    
    return True, ""

# Check user DSR restrictions
async def check_dsr_restrictions(db: AsyncSession, user_ids: List[str]) -> Tuple[bool, List[str], str]:
    """
    Check if any users in the dataset have processing restrictions from DSR requests.
    
    Args:
        db: Database session
        user_ids: List of user IDs to check for restrictions
        
    Returns:
        Tuple of (can_process, restricted_users, error_message)
    """
    if not user_ids:
        return True, [], ""
    
    # Setup consent ledger service
    consent_service = ConsentLedgerService(db)
    
    restricted_users = []
    for user_id in user_ids:
        # Get user consent history
        user_history = await consent_service.get_user_history(user_id)
        
        # Check for DSR restriction events
        for event in user_history:
            # Look for system restriction events in metadata
            metadata = event.consent_metadata or {}
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            # Check for restriction requests in the event metadata
            if metadata.get("dsr_type") == "processing_restriction" and event.action == "dsr_request":
                restricted_users.append(user_id)
                break
                
            # Also check for global opt-outs with system_restriction offer_id
            if event.offer_id == "system_restriction" and event.action == "opt_out":
                restricted_users.append(user_id)
                break
    
    if restricted_users:
        return False, restricted_users, "Some users have requested processing restrictions"
    
    return True, [], ""

# Apply privacy methods to results
def apply_differential_privacy(
    data: Dict[str, Any],
    epsilon: float,
    delta: float = 1e-5
) -> Dict[str, Any]:
    """
    Apply differential privacy to query results.
    
    Args:
        data: Query results to privatize
        epsilon: Privacy parameter (smaller = more privacy)
        delta: Probability of privacy failure
        
    Returns:
        Privatized results
    """
    # This is a simplified implementation for demonstration
    # A production system would use a proper DP library like IBM's diffprivlib or Google's dp-accounting
    
    # Calculate sensitivity based on the query type and data
    sensitivity = 1.0  # Simplified assumption
    
    # Add noise to the results
    noise_scale = sensitivity / epsilon
    
    # Apply noise to numeric values
    private_data = data.copy()
    for key, value in data.items():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            # Add Laplace noise
            noise = np.random.laplace(0, noise_scale)
            
            # For counts, round to nearest integer
            if key == "count" or key.endswith("_count"):
                private_data[key] = max(0, int(round(value + noise)))
            else:
                private_data[key] = value + noise
                
    # Add privacy metadata
    private_data["privacy_metadata"] = {
        "method": "differential_privacy",
        "epsilon": epsilon,
        "delta": delta,
        "estimated_error_pct": round(noise_scale / max(1, abs(data.get("result", 1))) * 100, 2)
    }
    
    return private_data

async def process_insight(
    data: List[Dict[str, Any]],
    query_type: QueryType,
    privacy_method: PrivacyMethod,
    privacy_params: Optional[Dict[str, Any]] = None,
    custom_query: Optional[Dict[str, Any]] = None,
    validate_consent: bool = True,
    user_id_field: str = "user_id",
    db: Optional[AsyncSession] = None
) -> Dict[str, Any]:
    """
    Process an insight request with privacy protection.
    
    Args:
        data: Input data as a list of dictionaries
        query_type: Type of query to run
        privacy_method: Privacy method to apply
        privacy_params: Parameters for the privacy method
        custom_query: Custom query parameters (for QueryType.CUSTOM)
        validate_consent: Whether to validate user consent
        user_id_field: Field name containing user IDs
        db: Database session for consent checking
        
    Returns:
        Results with privacy applied
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