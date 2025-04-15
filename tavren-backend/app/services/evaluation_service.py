"""
Evaluation service for measuring and improving the quality of RAG (Retrieval Augmented Generation).
Provides metrics, feedback mechanisms, and A/B testing capabilities.
"""

import logging
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from fastapi import Depends
from sqlalchemy import select, func, desc, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import RetrievalMetric, RetrievalFeedback, ABTestConfig, EmbeddingParameter
from app.config import settings
from app.services.embedding_service import EmbeddingService, get_embedding_service

# Set up logging
log = logging.getLogger("app")

class EvaluationService:
    """Service for evaluating and improving RAG performance"""
    
    def __init__(
        self, 
        db: AsyncSession,
        embedding_service: EmbeddingService
    ):
        """Initialize the evaluation service with database session."""
        self.db = db
        self.embedding_service = embedding_service
        
        # Default configuration
        self.default_metrics = [
            "mrr",  # Mean Reciprocal Rank
            "precision",
            "recall", 
            "latency",
            "user_rating"
        ]
        
        # Initialize metric names from settings or use defaults
        self.enabled_metrics = getattr(settings, 'ENABLED_METRICS', self.default_metrics)
        
        log.info(f"Evaluation Service initialized with metrics: {', '.join(self.enabled_metrics)}")
    
    async def log_retrieval_metrics(
        self,
        query_text: str,
        results: List[Dict[str, Any]],
        latency_ms: float,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        relevant_package_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log metrics for a retrieval operation.
        
        Args:
            query_text: The query text used for retrieval
            results: List of retrieval results
            latency_ms: Query latency in milliseconds
            user_id: Optional user ID
            session_id: Optional session ID for grouping related queries
            relevant_package_ids: Optional list of package IDs known to be relevant (for precision/recall)
            metadata: Additional metadata about the query
            
        Returns:
            Dict with recorded metrics and metric_id
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
                
            # Create metric record
            metric_record = RetrievalMetric(
                query_text=query_text,
                result_count=len(results),
                latency_ms=latency_ms,
                user_id=user_id,
                session_id=session_id,
                timestamp=datetime.utcnow(),
                result_package_ids=[r.get("package_id") for r in results if r.get("package_id")],
                relevant_package_ids=relevant_package_ids,
                retrieval_metadata=metadata or {}
            )
            
            # Calculate metrics if we have relevance information
            if relevant_package_ids and len(relevant_package_ids) > 0:
                metrics = self._calculate_retrieval_metrics(
                    results=[r.get("package_id") for r in results if r.get("package_id")], 
                    relevant_ids=relevant_package_ids
                )
                
                # Update the metric record with calculated values
                metric_record.precision = metrics.get("precision")
                metric_record.recall = metrics.get("recall")
                metric_record.mrr = metrics.get("mrr")
                metric_record.ndcg = metrics.get("ndcg")
                
                # Store the full metrics dictionary in retrieval_metadata
                if "metrics" not in metric_record.retrieval_metadata:
                    metric_record.retrieval_metadata["metrics"] = {}
                metric_record.retrieval_metadata["metrics"].update(metrics)
            
            # Save to database
            self.db.add(metric_record)
            await self.db.commit()
            await self.db.refresh(metric_record)
            
            # Prepare response
            response = {
                "metric_id": metric_record.id,
                "timestamp": metric_record.timestamp.isoformat(),
                "query_text": query_text,
                "result_count": len(results),
                "latency_ms": latency_ms,
                "session_id": session_id
            }
            
            # Add calculated metrics if available
            if relevant_package_ids and len(relevant_package_ids) > 0:
                response.update({
                    "precision": metric_record.precision,
                    "recall": metric_record.recall,
                    "mrr": metric_record.mrr,
                    "ndcg": metric_record.ndcg
                })
                
            log.info(f"Logged retrieval metrics for query: {query_text[:30]}...")
            return response
        
        except Exception as e:
            await self.db.rollback()
            log.error(f"Error logging retrieval metrics: {str(e)}", exc_info=True)
            raise Exception(f"Failed to log retrieval metrics: {str(e)}")
    
    async def record_user_feedback(
        self,
        metric_id: int,
        rating: int,
        user_id: Optional[str] = None,
        feedback_text: Optional[str] = None,
        helpful_result_ids: Optional[List[str]] = None,
        unhelpful_result_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record user feedback for a retrieval operation.
        
        Args:
            metric_id: ID of the associated metric record
            rating: User rating (1-5)
            user_id: Optional user ID
            feedback_text: Optional text feedback
            helpful_result_ids: Optional list of helpful result IDs
            unhelpful_result_ids: Optional list of unhelpful result IDs
            metadata: Additional metadata
            
        Returns:
            Dict with feedback information
        """
        try:
            # Validate rating
            if rating < 1 or rating > 5:
                raise ValueError("Rating must be between 1 and 5")
                
            # Get the associated metric record first to ensure it exists
            query = select(RetrievalMetric).where(RetrievalMetric.id == metric_id)
            result = await self.db.execute(query)
            metric_record = result.scalars().first()
            
            if not metric_record:
                raise ValueError(f"Metric record with ID {metric_id} not found")
            
            # Create feedback record
            feedback_record = RetrievalFeedback(
                metric_id=metric_id,
                user_id=user_id or metric_record.user_id,
                rating=rating,
                feedback_text=feedback_text,
                helpful_result_ids=helpful_result_ids or [],
                unhelpful_result_ids=unhelpful_result_ids or [],
                timestamp=datetime.utcnow(),
                retrieval_metadata=metadata or {}
            )
            
            # Save to database
            self.db.add(feedback_record)
            
            # Update the metric record with the user rating
            metric_record.user_rating = rating
            
            await self.db.commit()
            await self.db.refresh(feedback_record)
            
            # Return feedback information
            log.info(f"Recorded user feedback for query: {metric_record.query_text[:30]}... | Rating: {rating}")
            
            return {
                "feedback_id": feedback_record.id,
                "metric_id": metric_id,
                "rating": rating,
                "timestamp": feedback_record.timestamp.isoformat(),
                "query_text": metric_record.query_text
            }
        
        except Exception as e:
            await self.db.rollback()
            log.error(f"Error recording user feedback: {str(e)}", exc_info=True)
            raise Exception(f"Failed to record user feedback: {str(e)}")
    
    async def get_retrieval_metrics(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        include_feedback: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get retrieval metrics, optionally filtered by parameters.
        
        Args:
            user_id: Optional user ID filter
            session_id: Optional session ID filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of records to return
            include_feedback: Whether to include feedback data
            
        Returns:
            List of metric records
        """
        try:
            # Build the query with filters
            query = select(RetrievalMetric)
            
            if user_id:
                query = query.where(RetrievalMetric.user_id == user_id)
                
            if session_id:
                query = query.where(RetrievalMetric.session_id == session_id)
                
            if start_date:
                query = query.where(RetrievalMetric.timestamp >= start_date)
                
            if end_date:
                query = query.where(RetrievalMetric.timestamp <= end_date)
                
            # Order by timestamp (newest first) and limit results
            query = query.order_by(desc(RetrievalMetric.timestamp)).limit(limit)
            
            # Execute the query
            result = await self.db.execute(query)
            metric_records = result.scalars().all()
            
            # Format the response
            metrics_data = []
            for record in metric_records:
                metric_data = {
                    "id": record.id,
                    "query_text": record.query_text,
                    "result_count": record.result_count,
                    "latency_ms": record.latency_ms,
                    "user_id": record.user_id,
                    "session_id": record.session_id,
                    "timestamp": record.timestamp.isoformat(),
                    "precision": record.precision,
                    "recall": record.recall,
                    "mrr": record.mrr,
                    "ndcg": record.ndcg,
                    "user_rating": record.user_rating,
                    "result_package_ids": record.result_package_ids,
                    "relevant_package_ids": record.relevant_package_ids
                }
                
                # Include feedback if requested
                if include_feedback:
                    # Query feedback for this metric
                    feedback_query = select(RetrievalFeedback).where(
                        RetrievalFeedback.metric_id == record.id
                    ).order_by(RetrievalFeedback.timestamp)
                    
                    feedback_result = await self.db.execute(feedback_query)
                    feedback_records = feedback_result.scalars().all()
                    
                    # Format feedback data
                    feedback_data = []
                    for feedback in feedback_records:
                        feedback_data.append({
                            "id": feedback.id,
                            "rating": feedback.rating,
                            "user_id": feedback.user_id,
                            "timestamp": feedback.timestamp.isoformat(),
                            "feedback_text": feedback.feedback_text,
                            "helpful_result_ids": feedback.helpful_result_ids,
                            "unhelpful_result_ids": feedback.unhelpful_result_ids
                        })
                    
                    metric_data["feedback"] = feedback_data
                
                metrics_data.append(metric_data)
            
            return metrics_data
        
        except Exception as e:
            log.error(f"Error retrieving metrics: {str(e)}", exc_info=True)
            raise Exception(f"Failed to retrieve metrics: {str(e)}")

    async def create_ab_test(
        self,
        name: str,
        description: str,
        variants: Dict[str, Any],
        active: bool = True,
        traffic_allocation: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an A/B test configuration for different strategies.
        
        Args:
            name: Name of the A/B test
            description: Description of what is being tested
            variants: Dictionary of test variants and their parameters
            active: Whether the test is currently active
            traffic_allocation: Optional dictionary mapping variant names to traffic percentage (0-1)
            metadata: Additional metadata
            
        Returns:
            Dict with A/B test information
        """
        try:
            # Validate variants
            if not variants or len(variants) < 2:
                raise ValueError("At least two variants are required for an A/B test")
                
            # Set default traffic allocation if not provided
            if not traffic_allocation:
                # Equal distribution among variants
                even_split = 1.0 / len(variants)
                traffic_allocation = {variant: even_split for variant in variants}
            
            # Validate traffic allocation sums to approximately 1.0
            total_allocation = sum(traffic_allocation.values())
            if not (0.99 <= total_allocation <= 1.01):  # Allow small floating-point errors
                raise ValueError(f"Traffic allocation must sum to 1.0, got {total_allocation}")
            
            # Create A/B test record
            ab_test = ABTestConfig(
                name=name,
                description=description,
                variants=variants,
                traffic_allocation=traffic_allocation,
                active=active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                test_metadata=metadata or {}
            )
            
            # Save to database
            self.db.add(ab_test)
            await self.db.commit()
            await self.db.refresh(ab_test)
            
            # Return A/B test information
            log.info(f"Created A/B test: {name} with {len(variants)} variants")
            
            return {
                "id": ab_test.id,
                "name": ab_test.name,
                "description": ab_test.description,
                "variants": ab_test.variants,
                "traffic_allocation": ab_test.traffic_allocation,
                "active": ab_test.active,
                "created_at": ab_test.created_at.isoformat(),
                "updated_at": ab_test.updated_at.isoformat()
            }
        
        except Exception as e:
            await self.db.rollback()
            log.error(f"Error creating A/B test: {str(e)}", exc_info=True)
            raise Exception(f"Failed to create A/B test: {str(e)}")
    
    async def get_active_ab_test_variant(
        self,
        test_name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get an active A/B test variant for a user or session.
        
        Args:
            test_name: Name of the A/B test
            user_id: Optional user ID for consistent variant assignment
            session_id: Optional session ID if user is anonymous
            
        Returns:
            Dict with selected variant or None if no active test
        """
        try:
            # Query the active A/B test by name
            query = select(ABTestConfig).where(
                ABTestConfig.name == test_name,
                ABTestConfig.active == True
            )
            
            result = await self.db.execute(query)
            ab_test = result.scalars().first()
            
            if not ab_test:
                log.info(f"No active A/B test found with name: {test_name}")
                return None
            
            # Use user_id or session_id for deterministic variant selection
            # This ensures the same user always gets the same variant
            seed = user_id or session_id or str(uuid.uuid4())
            
            # Simple deterministic hash-based allocation
            import hashlib
            hash_value = int(hashlib.md5(seed.encode()).hexdigest(), 16)
            hash_pct = (hash_value % 1000) / 1000.0  # Value between 0 and 1
            
            # Select variant based on traffic allocation
            cumulative = 0.0
            selected_variant = None
            
            for variant, allocation in ab_test.traffic_allocation.items():
                cumulative += allocation
                if hash_pct <= cumulative:
                    selected_variant = variant
                    break
            
            # If no variant was selected (shouldn't happen with proper allocations),
            # choose the first one as fallback
            if not selected_variant and ab_test.variants:
                selected_variant = list(ab_test.variants.keys())[0]
            
            # Return the selected variant and its parameters
            variant_params = ab_test.variants.get(selected_variant, {})
            
            log.info(f"Selected variant '{selected_variant}' for test '{test_name}' and user/session '{seed[:8]}...'")
            
            return {
                "test_id": ab_test.id,
                "test_name": ab_test.name,
                "variant": selected_variant,
                "parameters": variant_params,
                "metadata": ab_test.test_metadata
            }
        
        except Exception as e:
            log.error(f"Error getting A/B test variant: {str(e)}", exc_info=True)
            raise Exception(f"Failed to get A/B test variant: {str(e)}")
    
    async def log_ab_test_result(
        self,
        test_id: int,
        variant: str,
        metric_id: int,
        outcome: str,
        score: Optional[float] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log the result of an A/B test for a specific user interaction.
        
        Args:
            test_id: ID of the A/B test
            variant: Variant name
            metric_id: Associated metric ID
            outcome: Result outcome (e.g., 'conversion', 'engagement')
            score: Optional numeric score or value
            user_id: Optional user ID
            session_id: Optional session ID
            metadata: Additional metadata
            
        Returns:
            Dict with result information
        """
        try:
            # Validate that the test and variant exist
            query = select(ABTestConfig).where(ABTestConfig.id == test_id)
            result = await self.db.execute(query)
            ab_test = result.scalars().first()
            
            if not ab_test:
                raise ValueError(f"A/B test with ID {test_id} not found")
            
            if variant not in ab_test.variants:
                raise ValueError(f"Variant '{variant}' not found in test {ab_test.name}")
            
            # Update the metric record with A/B test information
            metric_query = select(RetrievalMetric).where(RetrievalMetric.id == metric_id)
            metric_result = await self.db.execute(metric_query)
            metric = metric_result.scalars().first()
            
            if not metric:
                raise ValueError(f"Metric with ID {metric_id} not found")
            
            # Update metric with A/B test data
            if "ab_tests" not in metric.retrieval_metadata:
                metric.retrieval_metadata["ab_tests"] = []
                
            metric.retrieval_metadata["ab_tests"].append({
                "test_id": test_id,
                "test_name": ab_test.name,
                "variant": variant,
                "outcome": outcome,
                "score": score,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Add any additional metadata
            if metadata:
                if "ab_test_metadata" not in metric.retrieval_metadata:
                    metric.retrieval_metadata["ab_test_metadata"] = {}
                metric.retrieval_metadata["ab_test_metadata"].update(metadata)
            
            await self.db.commit()
            
            log.info(f"Logged A/B test result for '{ab_test.name}', variant '{variant}', outcome: {outcome}")
            
            return {
                "test_id": test_id,
                "test_name": ab_test.name,
                "variant": variant,
                "metric_id": metric_id,
                "outcome": outcome,
                "score": score,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            await self.db.rollback()
            log.error(f"Error logging A/B test result: {str(e)}", exc_info=True)
            raise Exception(f"Failed to log A/B test result: {str(e)}")
    
    async def get_ab_test_results(
        self,
        test_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated results for an A/B test.
        
        Args:
            test_id: ID of the A/B test
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dict with test results by variant
        """
        try:
            # Query the A/B test
            query = select(ABTestConfig).where(ABTestConfig.id == test_id)
            result = await self.db.execute(query)
            ab_test = result.scalars().first()
            
            if not ab_test:
                raise ValueError(f"A/B test with ID {test_id} not found")
            
            # Find all metrics with this test ID in their retrieval_metadata
            metrics_query = select(RetrievalMetric).where(
                RetrievalMetric.retrieval_metadata["ab_tests"].contains([{"test_id": test_id}])
            )
            
            # Apply date filters if provided
            if start_date:
                metrics_query = metrics_query.where(RetrievalMetric.timestamp >= start_date)
            if end_date:
                metrics_query = metrics_query.where(RetrievalMetric.timestamp <= end_date)
            
            metrics_result = await self.db.execute(metrics_query)
            metrics = metrics_result.scalars().all()
            
            # Group metrics by variant and calculate statistics
            results_by_variant = {}
            
            for metric in metrics:
                # Find the specific A/B test entry for this metric
                for test_entry in metric.retrieval_metadata.get("ab_tests", []):
                    if test_entry.get("test_id") == test_id:
                        variant = test_entry.get("variant")
                        outcome = test_entry.get("outcome")
                        score = test_entry.get("score")
                        
                        # Initialize variant entry if not exists
                        if variant not in results_by_variant:
                            results_by_variant[variant] = {
                                "count": 0,
                                "outcomes": {},
                                "metrics": {
                                    "precision": [],
                                    "recall": [],
                                    "mrr": [],
                                    "ndcg": [],
                                    "user_rating": [],
                                    "latency_ms": []
                                }
                            }
                        
                        # Update variant statistics
                        results_by_variant[variant]["count"] += 1
                        
                        # Update outcome counts
                        if outcome:
                            if outcome not in results_by_variant[variant]["outcomes"]:
                                results_by_variant[variant]["outcomes"][outcome] = {
                                    "count": 0,
                                    "scores": []
                                }
                            
                            results_by_variant[variant]["outcomes"][outcome]["count"] += 1
                            
                            if score is not None:
                                results_by_variant[variant]["outcomes"][outcome]["scores"].append(score)
                        
                        # Add metrics if available
                        for metric_name in ["precision", "recall", "mrr", "ndcg"]:
                            if getattr(metric, metric_name) is not None:
                                results_by_variant[variant]["metrics"][metric_name].append(
                                    getattr(metric, metric_name)
                                )
                        
                        if metric.user_rating is not None:
                            results_by_variant[variant]["metrics"]["user_rating"].append(metric.user_rating)
                            
                        if metric.latency_ms is not None:
                            results_by_variant[variant]["metrics"]["latency_ms"].append(metric.latency_ms)
            
            # Calculate averages for each metric and variant
            for variant, data in results_by_variant.items():
                for metric_name, values in data["metrics"].items():
                    if values:
                        data["metrics"][f"avg_{metric_name}"] = sum(values) / len(values)
                    else:
                        data["metrics"][f"avg_{metric_name}"] = None
                
                # Calculate average scores for outcomes
                for outcome, outcome_data in data["outcomes"].items():
                    scores = outcome_data.get("scores", [])
                    if scores:
                        outcome_data["avg_score"] = sum(scores) / len(scores)
            
            # Compile results
            return {
                "test_id": ab_test.id,
                "test_name": ab_test.name,
                "description": ab_test.description,
                "active": ab_test.active,
                "total_data_points": sum(data["count"] for data in results_by_variant.values()),
                "variants": results_by_variant,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        
        except Exception as e:
            log.error(f"Error getting A/B test results: {str(e)}", exc_info=True)
            raise Exception(f"Failed to get A/B test results: {str(e)}")
    
    async def register_embedding_parameters(
        self,
        name: str,
        parameters: Dict[str, Any],
        model_name: str,
        description: Optional[str] = None,
        active: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a set of embedding parameters for fine-tuning.
        
        Args:
            name: Name of the parameter set
            parameters: Dictionary of embedding parameters
            model_name: Name of the embedding model
            description: Optional description
            active: Whether this is the active parameter set
            metadata: Additional metadata
            
        Returns:
            Dict with parameter information
        """
        try:
            # Create parameter record
            param_record = EmbeddingParameter(
                name=name,
                parameters=parameters,
                model_name=model_name,
                description=description,
                active=active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                parameter_metadata=metadata or {}
            )
            
            # If this is active, deactivate other parameter sets for the same model
            if active:
                # Find other active parameter sets for this model
                query = select(EmbeddingParameter).where(
                    EmbeddingParameter.model_name == model_name,
                    EmbeddingParameter.active == True
                )
                
                result = await self.db.execute(query)
                active_params = result.scalars().all()
                
                # Deactivate them
                for param in active_params:
                    param.active = False
                    param.updated_at = datetime.utcnow()
            
            # Save to database
            self.db.add(param_record)
            await self.db.commit()
            await self.db.refresh(param_record)
            
            log.info(f"Registered embedding parameters '{name}' for model '{model_name}'")
            
            return {
                "id": param_record.id,
                "name": param_record.name,
                "model_name": param_record.model_name,
                "parameters": param_record.parameters,
                "active": param_record.active,
                "created_at": param_record.created_at.isoformat()
            }
        
        except Exception as e:
            await self.db.rollback()
            log.error(f"Error registering embedding parameters: {str(e)}", exc_info=True)
            raise Exception(f"Failed to register embedding parameters: {str(e)}")
    
    async def get_active_embedding_parameters(
        self,
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get the active embedding parameters for a model.
        
        Args:
            model_name: Optional model name filter
            
        Returns:
            Dict with active parameter sets by model
        """
        try:
            # Query for active parameter sets
            query = select(EmbeddingParameter).where(EmbeddingParameter.active == True)
            
            if model_name:
                query = query.where(EmbeddingParameter.model_name == model_name)
                
            result = await self.db.execute(query)
            parameter_records = result.scalars().all()
            
            # Group by model name
            parameters_by_model = {}
            
            for record in parameter_records:
                parameters_by_model[record.model_name] = {
                    "id": record.id,
                    "name": record.name,
                    "parameters": record.parameters,
                    "description": record.description,
                    "created_at": record.created_at.isoformat(),
                    "updated_at": record.updated_at.isoformat()
                }
            
            return parameters_by_model
        
        except Exception as e:
            log.error(f"Error getting active embedding parameters: {str(e)}", exc_info=True)
            raise Exception(f"Failed to get active embedding parameters: {str(e)}")
    
    def _calculate_retrieval_metrics(self, results: List[str], relevant_ids: List[str]) -> Dict[str, float]:
        """
        Calculate common retrieval metrics.
        
        Args:
            results: List of retrieved item IDs in rank order
            relevant_ids: List of known relevant item IDs
            
        Returns:
            Dict with calculated metrics
        """
        metrics = {}
        
        # Ensure we have items to evaluate
        if not results or not relevant_ids:
            return {
                "precision": 0.0,
                "recall": 0.0,
                "mrr": 0.0,
                "ndcg": 0.0
            }
        
        # Set of relevant IDs for faster lookups
        relevant_set = set(relevant_ids)
        
        # Calculate precision (relevant / retrieved)
        relevant_retrieved = [item for item in results if item in relevant_set]
        metrics["precision"] = len(relevant_retrieved) / len(results) if results else 0.0
        
        # Calculate recall (relevant retrieved / total relevant)
        metrics["recall"] = len(relevant_retrieved) / len(relevant_set) if relevant_set else 0.0
        
        # Calculate MRR (Mean Reciprocal Rank)
        # Find the rank of the first relevant item
        mrr = 0.0
        for i, item in enumerate(results):
            if item in relevant_set:
                # Rank is 1-indexed
                mrr = 1.0 / (i + 1)
                break
        metrics["mrr"] = mrr
        
        # Calculate NDCG (Normalized Discounted Cumulative Gain)
        # DCG = sum(rel_i / log2(i + 1)) where rel_i is the relevance of item i
        # For binary relevance, rel_i is 1 if relevant, 0 otherwise
        dcg = 0.0
        for i, item in enumerate(results):
            if item in relevant_set:
                # For binary relevance, rel_i is 1 if relevant
                dcg += 1.0 / (np.log2(i + 2))  # i+2 because log2(1) = 0
                
        # Calculate Ideal DCG (items sorted by relevance)
        # For binary relevance, this is simply the DCG if all relevant items
        # were returned in the top positions
        idcg = 0.0
        for i in range(min(len(relevant_set), len(results))):
            idcg += 1.0 / (np.log2(i + 2))
            
        # Calculate NDCG
        metrics["ndcg"] = dcg / idcg if idcg > 0 else 0.0
        
        return metrics

# Dependency for FastAPI
async def get_evaluation_service(
    db = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> EvaluationService:
    """
    Get evaluation service instance for dependency injection.
    """
    return EvaluationService(db, embedding_service) 