"""
LLM service for interacting with Nvidia's LLM APIs.
Provides functionality for processing data, generating embeddings, and managing model configurations.
"""

import logging
import json
import uuid
import aiohttp
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from fastapi import Depends
from pydantic import BaseModel

from app.config import settings
from app.services.data_packaging import DataPackagingService, get_data_packaging_service
from app.services.prompt_service import PromptService, get_prompt_service

# Set up logging
log = logging.getLogger("app")

class LLMService:
    """Service for interacting with LLM APIs (Nvidia)"""
    
    def __init__(self, data_packaging_service: DataPackagingService, prompt_service: PromptService):
        """Initialize the LLM service with configuration."""
        self.data_packaging_service = data_packaging_service
        self.prompt_service = prompt_service
        
        # Get configuration from settings
        self.api_base_url = settings.NVIDIA_API_BASE_URL
        self.api_key = settings.NVIDIA_API_KEY
        self.default_model = settings.DEFAULT_LLM_MODEL
        self.embedding_model = settings.DEFAULT_EMBEDDING_MODEL
        
        # Cache for auth tokens and model information
        self._auth_token = None
        self._auth_token_expiry = 0
        self._models_cache = None
        self._models_cache_timestamp = 0
        
        log.info(f"LLM Service initialized with base URL: {self.api_base_url}")
    
    async def _ensure_auth_token(self) -> str:
        """
        Ensure we have a valid auth token for the Nvidia API.
        Refreshes the token if expired.
        
        Returns:
            str: Valid authentication token
        """
        # Check if token needs refresh (expired or not yet obtained)
        current_time = time.time()
        if not self._auth_token or current_time >= self._auth_token_expiry:
            log.info("Obtaining new Nvidia API auth token")
            
            # Implement Nvidia auth flow using their developer API
            async with aiohttp.ClientSession() as session:
                auth_url = f"{self.api_base_url}/auth/token"
                
                # This would be adjusted to use Nvidia's actual auth mechanism
                auth_data = {
                    "api_key": self.api_key
                }
                
                headers = {
                    "Content-Type": "application/json"
                }
                
                try:
                    async with session.post(auth_url, json=auth_data, headers=headers) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            log.error(f"Failed to obtain auth token: {error_text}")
                            raise Exception(f"Authentication failed: {error_text}")
                        
                        auth_response = await response.json()
                        self._auth_token = auth_response.get("access_token")
                        
                        # Calculate expiry (subtract 60 seconds for safety margin)
                        expires_in = auth_response.get("expires_in", 3600)  # Default to 1 hour
                        self._auth_token_expiry = current_time + expires_in - 60
                        
                        log.info(f"Successfully obtained auth token, expires in {expires_in} seconds")
                
                except Exception as e:
                    log.error(f"Error during authentication: {str(e)}", exc_info=True)
                    raise Exception(f"Authentication error: {str(e)}")
        
        return self._auth_token
    
    async def process_data(
        self,
        package_id: str,
        instructions: str,
        model_config: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process packaged data with the LLM.
        
        Args:
            package_id: ID of the data package to process
            instructions: Instructions for the LLM on how to process the data
            model_config: Optional configuration for the model
            max_tokens: Maximum tokens in the response
            
        Returns:
            Dict containing the LLM response and metadata
        """
        # Get the data package
        package_data, error = await self.data_packaging_service.get_package_by_id(package_id)
        if error:
            log.error(f"Error retrieving data package {package_id}: {error.get('reason')}")
            raise Exception(f"Failed to retrieve data package: {error.get('reason')}")
        
        # Prepare the data for LLM processing
        data_content = package_data.get("content", {})
        data_metadata = package_data.get("metadata", {})
        
        # Select the model to use
        model_name = model_config.get("model_name", self.default_model) if model_config else self.default_model
        
        # Create appropriate prompt using prompt service
        prompt = self.prompt_service.create_prompt(
            instructions=instructions,
            data_content=data_content,
            data_metadata=data_metadata,
            model_name=model_name,
            max_tokens=4000  # Reserve tokens for the response
        )
        
        # Configure request parameters
        request_params = {
            "model": model_name,
            "prompt": prompt,
            "max_tokens": max_tokens or 1024,
            "temperature": model_config.get("temperature", 0.7) if model_config else 0.7,
            "top_p": model_config.get("top_p", 0.95) if model_config else 0.95
        }
        
        # Make the API call to Nvidia's LLM
        result = await self._make_llm_api_call("/completion", request_params)
        
        # Process the result
        request_id = str(uuid.uuid4())
        processed_result = {
            "request_id": request_id,
            "model_used": model_name,
            "package_id": package_id,
            "result": result.get("choices", [{}])[0].get("text", ""),
            "usage": result.get("usage", {}),
            "timestamp": time.time()
        }
        
        return processed_result
    
    async def process_text(
        self,
        text: str,
        model_name: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Process raw text with the LLM.
        
        Args:
            text: Text prompt to process
            model_name: Name of the model to use
            max_tokens: Maximum tokens in the response
            temperature: Temperature parameter for generation
            top_p: Top-p parameter for generation
            
        Returns:
            Dict containing the LLM response and metadata
        """
        try:
            # Use specified model or default
            model_name = model_name or self.default_model
            
            # Configure request parameters
            request_params = {
                "model": model_name,
                "prompt": text,
                "max_tokens": max_tokens or 1024,
                "temperature": temperature or 0.7,
                "top_p": top_p or 0.95
            }
            
            # Make the API call to Nvidia's LLM
            result = await self._make_llm_api_call("/completion", request_params)
            
            # Process the result
            request_id = str(uuid.uuid4())
            processed_result = {
                "request_id": request_id,
                "model_used": model_name,
                "result": result.get("choices", [{}])[0].get("text", ""),
                "usage": result.get("usage", {}),
                "timestamp": time.time()
            }
            
            return processed_result
            
        except Exception as e:
            log.error(f"Error processing text with LLM: {str(e)}", exc_info=True)
            raise Exception(f"Failed to process text: {str(e)}")
    
    async def process_rag(
        self,
        query: str,
        context: str,
        instructions: str,
        model_name: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Process a retrieval augmented generation query.
        
        Args:
            query: User query
            context: Retrieved context from embeddings
            instructions: Instructions for the LLM
            model_name: Name of the model to use
            max_tokens: Maximum tokens in the response
            temperature: Temperature parameter for generation
            
        Returns:
            Dict containing the LLM response and metadata
        """
        try:
            # Use specified model or default
            model_name = model_name or self.default_model
            
            # Format the RAG prompt using prompt service
            # This handles different model-specific formats and context optimization
            rag_prompt = self.prompt_service.create_rag_prompt(
                query=query,
                instructions=instructions,
                context=context,
                model_name=model_name,
                max_tokens=4000  # Reserve tokens for the response
            )
            
            # Configure request parameters
            request_params = {
                "model": model_name,
                "prompt": rag_prompt,
                "max_tokens": max_tokens or 1024,
                "temperature": temperature or 0.7,
                "top_p": 0.95
            }
            
            # Make the API call to Nvidia's LLM
            result = await self._make_llm_api_call("/completion", request_params)
            
            # Process the result
            request_id = str(uuid.uuid4())
            processed_result = {
                "request_id": request_id,
                "model_used": model_name,
                "query": query,
                "result": result.get("choices", [{}])[0].get("text", ""),
                "usage": result.get("usage", {}),
                "timestamp": time.time()
            }
            
            return processed_result
            
        except Exception as e:
            log.error(f"Error processing RAG query: {str(e)}", exc_info=True)
            raise Exception(f"Failed to process RAG query: {str(e)}")
    
    async def generate_embedding(
        self,
        text: Optional[str] = None,
        package_id: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate embeddings for text or packaged data.
        
        Args:
            text: Text to generate embeddings for (if no package_id)
            package_id: ID of data package to generate embeddings for (prioritized over text)
            model_name: Name of embedding model to use
            
        Returns:
            Dict containing embedding vectors and metadata
        """
        # Determine the text to embed
        if package_id:
            # Get the data package
            package_data, error = await self.data_packaging_service.get_package_by_id(package_id)
            if error:
                log.error(f"Error retrieving data package {package_id}: {error.get('reason')}")
                raise Exception(f"Failed to retrieve data package: {error.get('reason')}")
            
            # Extract the text from the package
            data_content = package_data.get("content", {})
            # Convert content to a string representation for embedding
            if isinstance(data_content, dict):
                text_to_embed = json.dumps(data_content)
            else:
                text_to_embed = str(data_content)
        elif text:
            text_to_embed = text
        else:
            raise Exception("Either text or package_id must be provided")
        
        # Select the embedding model
        embedding_model = model_name or self.embedding_model
        
        # Configure request parameters
        request_params = {
            "model": embedding_model,
            "input": text_to_embed
        }
        
        # Make the API call to Nvidia's embedding model
        result = await self._make_llm_api_call("/embeddings", request_params)
        
        # Process the result
        request_id = str(uuid.uuid4())
        embedding_result = {
            "request_id": request_id,
            "model_used": embedding_model,
            "embedding": result.get("data", [{}])[0].get("embedding", []),
            "dimension": len(result.get("data", [{}])[0].get("embedding", [])),
            "usage": result.get("usage", {}),
            "timestamp": time.time()
        }
        
        if package_id:
            embedding_result["package_id"] = package_id
        
        return embedding_result
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available LLM models from Nvidia.
        
        Returns:
            List of model information dictionaries
        """
        # Check cache first
        current_time = time.time()
        cache_ttl = 300  # 5 minutes
        
        if self._models_cache and (current_time - self._models_cache_timestamp) < cache_ttl:
            log.info("Returning cached model list")
            return self._models_cache
        
        # Make API call to retrieve models
        models_result = await self._make_llm_api_call("/models", {})
        
        # Process and cache the results
        models_list = models_result.get("data", [])
        self._models_cache = models_list
        self._models_cache_timestamp = current_time
        
        return models_list
    
    async def check_connection(self) -> Dict[str, Any]:
        """
        Check connection status with the Nvidia API.
        
        Returns:
            Dict with connection status and details
        """
        try:
            # Try to get a token as a basic connectivity test
            token = await self._ensure_auth_token()
            
            # Try to list models as a functional test
            models = await self.list_models()
            
            return {
                "status": "connected",
                "api_url": self.api_base_url,
                "models_available": len(models),
                "default_model": self.default_model,
                "embedding_model": self.embedding_model
            }
        except Exception as e:
            log.error(f"Connection check failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "api_url": self.api_base_url,
                "error": str(e)
            }
    
    async def _make_llm_api_call(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make an authenticated API call to the Nvidia LLM API.
        
        Args:
            endpoint: API endpoint path
            params: Request parameters
            
        Returns:
            API response as dictionary
        """
        # Ensure we have a valid auth token
        auth_token = await self._ensure_auth_token()
        
        # Construct full URL
        url = f"{self.api_base_url}{endpoint}"
        
        # Make the API call
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_token}"
            }
            
            try:
                async with session.post(url, json=params, headers=headers) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        log.error(f"API call failed: {response.status} - {response_text}")
                        raise Exception(f"API call failed: {response.status} - {response_text}")
                    
                    # Parse the response
                    return json.loads(response_text)
            
            except Exception as e:
                log.error(f"Error during API call to {endpoint}: {str(e)}", exc_info=True)
                raise Exception(f"API call error: {str(e)}")


# Dependency for FastAPI
def get_llm_service(
    data_packaging_service: DataPackagingService = Depends(get_data_packaging_service),
    prompt_service: PromptService = Depends(get_prompt_service)
) -> LLMService:
    """
    Get LLM service instance for dependency injection.
    """
    return LLMService(data_packaging_service, prompt_service) 