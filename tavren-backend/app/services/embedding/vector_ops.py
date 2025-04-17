"""
Vector operations module.

This module handles fundamental vector operations needed for embedding service.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Union, Callable, Tuple, TypeVar
from .models import EmbeddingConfig, DistanceMetric

# Type variables for generic functions
T = TypeVar('T')
VectorType = Union[List[float], np.ndarray]

class VectorOperations:
    """Vector operations utility class."""
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """Initialize with optional configuration."""
        self.config = config or EmbeddingConfig()
        
        # Fast lookup for distance functions
        self._distance_functions = {
            DistanceMetric.COSINE: self.cosine_distance,
            DistanceMetric.EUCLIDEAN: self.euclidean_distance,
            DistanceMetric.DOT: self.dot_product,
            DistanceMetric.MANHATTAN: self.manhattan_distance
        }
    
    def get_distance_fn(self) -> Callable[[VectorType, VectorType], float]:
        """Get the configured distance function."""
        return self._distance_functions[self.config.distance_metric]
    
    @staticmethod
    def ensure_numpy(vector: VectorType) -> np.ndarray:
        """Convert a vector to numpy array if it's not already."""
        if isinstance(vector, np.ndarray):
            return vector
        return np.array(vector, dtype=np.float32)
    
    @staticmethod
    def normalize_vector(vector: VectorType) -> np.ndarray:
        """Normalize a vector to unit length."""
        vec = VectorOperations.ensure_numpy(vector)
        norm = np.linalg.norm(vec)
        if norm > 0:
            return vec / norm
        return vec
    
    @staticmethod
    def cosine_distance(vec1: VectorType, vec2: VectorType) -> float:
        """Calculate cosine distance between two vectors."""
        v1 = VectorOperations.ensure_numpy(vec1)
        v2 = VectorOperations.ensure_numpy(vec2)
        
        # Calculate dot product and norms
        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        # Avoid division by zero
        if norm1 == 0 or norm2 == 0:
            return 1.0  # Maximum distance
            
        # Return cosine similarity (1 - distance)
        return 1.0 - (dot / (norm1 * norm2))
    
    @staticmethod
    def euclidean_distance(vec1: VectorType, vec2: VectorType) -> float:
        """Calculate Euclidean distance between two vectors."""
        v1 = VectorOperations.ensure_numpy(vec1)
        v2 = VectorOperations.ensure_numpy(vec2)
        return float(np.linalg.norm(v1 - v2))
    
    @staticmethod
    def dot_product(vec1: VectorType, vec2: VectorType) -> float:
        """Calculate dot product between two vectors."""
        v1 = VectorOperations.ensure_numpy(vec1)
        v2 = VectorOperations.ensure_numpy(vec2)
        return float(np.dot(v1, v2))
    
    @staticmethod
    def manhattan_distance(vec1: VectorType, vec2: VectorType) -> float:
        """Calculate Manhattan distance between two vectors."""
        v1 = VectorOperations.ensure_numpy(vec1)
        v2 = VectorOperations.ensure_numpy(vec2)
        return float(np.sum(np.abs(v1 - v2)))
    
    def similarity_score(self, vec1: VectorType, vec2: VectorType) -> float:
        """
        Convert distance to similarity score (higher is more similar).
        
        Different metrics need different conversions:
        - Cosine: 1 - distance
        - Euclidean: 1 / (1 + distance)
        - Manhattan: 1 / (1 + distance)
        - Dot: raw value (already similarity)
        """
        distance_fn = self.get_distance_fn()
        
        # Special handling for dot product which is already a similarity
        if self.config.distance_metric == DistanceMetric.DOT:
            return self.dot_product(vec1, vec2)
            
        # For others, convert distance to similarity
        distance = distance_fn(vec1, vec2)
        
        if self.config.distance_metric == DistanceMetric.COSINE:
            return 1.0 - distance
        else:
            # For Euclidean and Manhattan
            return 1.0 / (1.0 + distance)
    
    def batch_similarity(
        self, 
        query_vec: VectorType, 
        vectors: List[VectorType]
    ) -> List[float]:
        """
        Calculate similarity between query vector and multiple vectors.
        
        This is optimized to avoid repeated calculations.
        """
        q_vec = self.ensure_numpy(query_vec)
        
        # Pre-normalize if using cosine and normalize is enabled
        if self.config.normalize and self.config.distance_metric == DistanceMetric.COSINE:
            q_vec = self.normalize_vector(q_vec)
            
        # Convert all vectors to numpy for vectorized operations
        vecs = np.array([self.ensure_numpy(v) for v in vectors], dtype=np.float32)
        
        # Handle different distance metrics with vectorized operations
        if self.config.distance_metric == DistanceMetric.COSINE:
            if self.config.normalize:
                # Normalize all vectors
                norms = np.linalg.norm(vecs, axis=1, keepdims=True)
                mask = norms > 0
                vecs[mask] = vecs[mask] / norms[mask]
                
            # Calculate dot products (vectorized)
            dots = np.dot(vecs, q_vec)
            
            # Convert to similarities
            return (dots + 1) / 2  # Scale from [-1, 1] to [0, 1]
            
        elif self.config.distance_metric == DistanceMetric.EUCLIDEAN:
            # Calculate Euclidean distances (vectorized)
            distances = np.linalg.norm(vecs - q_vec, axis=1)
            # Convert to similarities
            return 1.0 / (1.0 + distances)
            
        elif self.config.distance_metric == DistanceMetric.MANHATTAN:
            # Calculate Manhattan distances (vectorized)
            distances = np.sum(np.abs(vecs - q_vec), axis=1)
            # Convert to similarities
            return 1.0 / (1.0 + distances)
            
        elif self.config.distance_metric == DistanceMetric.DOT:
            # Just return dot products
            return np.dot(vecs, q_vec).tolist()
        
        # Fallback to non-vectorized approach
        return [self.similarity_score(q_vec, v) for v in vectors]

# Standalone functions for easy access
def normalize_vector(vector: VectorType) -> np.ndarray:
    """Standalone function to normalize a vector."""
    return VectorOperations.normalize_vector(vector)

def similarity_score(
    vec1: VectorType, 
    vec2: VectorType, 
    metric: DistanceMetric = DistanceMetric.COSINE
) -> float:
    """Standalone function to calculate similarity between two vectors."""
    ops = VectorOperations(EmbeddingConfig(distance_metric=metric))
    return ops.similarity_score(vec1, vec2) 