"""
Prompt template service for managing LLM prompts.
Provides optimized templates for different data types, context truncation,
and privacy-aware instruction formatting.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple, Union
from fastapi import Depends

from app.config import settings

# Set up logging
log = logging.getLogger("app")

class PromptService:
    """Service for managing prompt templates and context window optimization"""
    
    def __init__(self):
        """Initialize the prompt template service."""
        # Default configuration
        self.max_content_tokens = 4000  # Default maximum tokens for data content
        self.truncation_message = "[Content truncated due to length]"
        
        # Data type specific templates
        self._templates = {
            "app_usage": self._app_usage_template,
            "location": self._location_template,
            "browsing_history": self._browsing_history_template,
            "health": self._health_template,
            "financial": self._financial_template,
            "unknown": self._default_template
        }
        
        log.info("Prompt Template Service initialized")
    
    def create_prompt(
        self,
        instructions: str,
        data_content: Dict[str, Any],
        data_metadata: Dict[str, Any],
        model_name: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Create a prompt for the LLM based on data type and metadata.
        
        Args:
            instructions: User instructions for the LLM
            data_content: The data content to process
            data_metadata: Metadata about the data
            model_name: Target LLM model name
            max_tokens: Maximum tokens for the prompt
            
        Returns:
            Formatted prompt string
        """
        # Extract data type from metadata
        data_type = data_metadata.get("data_type", "unknown")
        
        # Get the appropriate template function
        template_func = self._templates.get(data_type, self._default_template)
        
        # Apply the template
        return template_func(instructions, data_content, data_metadata, model_name, max_tokens)
    
    def create_rag_prompt(
        self,
        query: str,
        instructions: str,
        context: str,
        model_name: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Create a prompt for retrieval augmented generation.
        
        Args:
            query: User query
            instructions: Instructions for the LLM
            context: Retrieved context
            model_name: Target LLM model name
            max_tokens: Maximum tokens for the prompt
            
        Returns:
            Formatted RAG prompt
        """
        # Optimize context if max_tokens is specified
        if max_tokens:
            context = self._optimize_context(context, max_tokens)
        
        # Format based on model
        if model_name and "llama-3" in model_name.lower():
            return self._format_llama3_rag_prompt(query, instructions, context)
        else:
            return self._format_default_rag_prompt(query, instructions, context)
    
    def _format_llama3_rag_prompt(self, query: str, instructions: str, context: str) -> str:
        """Format RAG prompt specifically for Llama 3 models."""
        prompt = f"""<|begin_of_text|>
<|system|>
You are a helpful assistant that answers questions based solely on the provided context.
If you don't know the answer or can't find it in the context, say so clearly.
Always respect user privacy and data consent boundaries.
{instructions}
</|system|>

<|user|>
I need information about the following: {query}

Here is the relevant context to use for your answer:

{context}
</|user|>

<|assistant|>
"""
        return prompt
    
    def _format_default_rag_prompt(self, query: str, instructions: str, context: str) -> str:
        """Format RAG prompt for standard models."""
        prompt = f"""# Query
{query}

# Instructions
{instructions}

# Retrieved Context
{context}

Based on the above context and query only, please provide a well-informed response.
Do not include information not present in the context. If the context doesn't contain
the answer, please state that clearly instead of making up an answer.
"""
        return prompt
    
    def _optimize_context(self, context: str, max_tokens: int) -> str:
        """Optimize context to fit within token limit while preserving most relevant parts."""
        # First check if context already fits
        estimated_tokens = len(context.split()) * 1.3  # Rough estimate
        
        if estimated_tokens <= max_tokens:
            return context
            
        # Simple truncation approach - could be improved with more sophisticated chunking
        # For now, keep the first portion and add a truncation message
        max_chars = int(max_tokens / 1.3 * 4)  # Rough conversion back to characters
        
        # Try to break at a natural point
        truncated = context[:max_chars]
        last_paragraph = truncated.rfind("\n\n")
        
        if last_paragraph > max_chars * 0.7:  # Only use paragraph break if it's not too early
            truncated = context[:last_paragraph] + f"\n\n{self.truncation_message}"
        else:
            truncated = truncated + f"... {self.truncation_message}"
            
        return truncated
    
    def _app_usage_template(
        self, 
        instructions: str, 
        data_content: Dict[str, Any], 
        data_metadata: Dict[str, Any],
        model_name: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Template specifically optimized for app usage data."""
        # Format the data content as a string, handling potential token limits
        data_str = json.dumps(data_content, indent=2)
        
        if max_tokens:
            # Simple truncation for now, could be more sophisticated
            max_content_chars = max_tokens * 4  # Rough estimate
            if len(data_str) > max_content_chars:
                data_str = data_str[:max_content_chars] + f"... {self.truncation_message}"
        
        # Extract relevant metadata
        consent_purpose = data_metadata.get("purpose", "unspecified")
        anonymization = data_metadata.get("anonymization_level", "unknown")
        record_count = data_metadata.get("record_count", "unknown")
        
        # Add privacy reminders and data type specific instructions
        privacy_notes = f"""
Privacy Notes:
- This data was shared with purpose: "{consent_purpose}"
- Anonymization level: {anonymization}
- Representing {record_count} records of app usage data
- DO NOT attempt to re-identify users or extrapolate beyond the data
"""
        
        # App-usage specific guidance
        data_guidance = """
App Usage Data Guidelines:
- Focus on patterns and trends rather than individual sessions
- App usage timestamps may reveal daily routines - maintain privacy
- Interpret frequency and duration metrics with context
- Consider potential gaps in the data collection
"""
        
        # Construct the full prompt
        prompt = f"""# Instructions
{instructions}

{privacy_notes}

{data_guidance}

# App Usage Data
```json
{data_str}
```

Process the above app usage data according to the instructions, strictly respecting user consent and privacy boundaries.
Your analysis should remain within the specified purpose: "{consent_purpose}".
"""
        
        return prompt.strip()
    
    def _location_template(
        self, 
        instructions: str, 
        data_content: Dict[str, Any], 
        data_metadata: Dict[str, Any],
        model_name: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Template specifically optimized for location data."""
        # Format the data content as a string
        data_str = json.dumps(data_content, indent=2)
        
        if max_tokens:
            # Simple truncation for now
            max_content_chars = max_tokens * 4  # Rough estimate
            if len(data_str) > max_content_chars:
                data_str = data_str[:max_content_chars] + f"... {self.truncation_message}"
        
        # Extract relevant metadata
        consent_purpose = data_metadata.get("purpose", "unspecified")
        anonymization = data_metadata.get("anonymization_level", "unknown")
        record_count = data_metadata.get("record_count", "unknown")
        
        # Add strong privacy warnings for location data
        privacy_notes = f"""
IMPORTANT PRIVACY NOTES:
- This location data was shared ONLY for purpose: "{consent_purpose}"
- Anonymization level: {anonymization}
- Representing {record_count} location records
- Location data is highly sensitive and reveals personal patterns
- NEVER attempt to identify home/work locations or suggest surveillance
- DO NOT extrapolate beyond the data or make identity-related inferences
"""
        
        # Location-specific guidance
        data_guidance = """
Location Data Guidelines:
- Focus on patterns at area/region level rather than exact coordinates
- Avoid mentioning specific addresses even if they appear in the data
- Be cautious when discussing frequently visited locations
- Time patterns should be discussed in general terms (morning/evening)
- Always respect the boundaries of the stated purpose
"""
        
        # Construct the full prompt
        prompt = f"""# Instructions
{instructions}

{privacy_notes}

{data_guidance}

# Location Data
```json
{data_str}
```

Process the above location data according to the instructions, with strict respect for privacy boundaries.
Your analysis must remain within the specified purpose: "{consent_purpose}" and focus on aggregate patterns rather than individual movements.
"""
        
        return prompt.strip()
    
    def _browsing_history_template(
        self, 
        instructions: str, 
        data_content: Dict[str, Any], 
        data_metadata: Dict[str, Any],
        model_name: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Template specifically optimized for browsing history data."""
        # Format the data content as a string
        data_str = json.dumps(data_content, indent=2)
        
        if max_tokens:
            max_content_chars = max_tokens * 4
            if len(data_str) > max_content_chars:
                data_str = data_str[:max_content_chars] + f"... {self.truncation_message}"
        
        # Extract relevant metadata
        consent_purpose = data_metadata.get("purpose", "unspecified")
        anonymization = data_metadata.get("anonymization_level", "unknown")
        
        # Add strong privacy warnings for browsing history
        privacy_notes = f"""
IMPORTANT PRIVACY NOTES:
- This browsing history was shared ONLY for purpose: "{consent_purpose}"
- Anonymization level: {anonymization}
- Browsing data reveals personal interests and potentially sensitive information
- NEVER attempt to profile the user based on sensitive categories (health, politics, etc.)
- DO NOT extrapolate beyond the data or make identity-related inferences
"""
        
        # Browsing-specific guidance
        data_guidance = """
Browsing History Guidelines:
- Focus on general patterns and categories rather than specific URLs
- Avoid quoting exact search queries that could be personally identifying
- Be cautious with timestamps and patterns that might reveal personal routines
- Do not make assumptions about user intent based on visited sites
- Always respect the boundaries of the stated purpose
"""
        
        # Construct the full prompt
        prompt = f"""# Instructions
{instructions}

{privacy_notes}

{data_guidance}

# Browsing History Data
```json
{data_str}
```

Process the above browsing data according to the instructions, with strict respect for privacy boundaries.
Your analysis must remain within the specified purpose: "{consent_purpose}" and should avoid any judgments or inferences about the person.
"""
        
        return prompt.strip()
    
    def _health_template(
        self, 
        instructions: str, 
        data_content: Dict[str, Any], 
        data_metadata: Dict[str, Any],
        model_name: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Template specifically optimized for health data."""
        # Format the data content as a string
        data_str = json.dumps(data_content, indent=2)
        
        if max_tokens:
            max_content_chars = max_tokens * 4
            if len(data_str) > max_content_chars:
                data_str = data_str[:max_content_chars] + f"... {self.truncation_message}"
        
        # Extract relevant metadata
        consent_purpose = data_metadata.get("purpose", "unspecified")
        anonymization = data_metadata.get("anonymization_level", "unknown")
        
        # Add extremely strong privacy warnings for health data
        privacy_notes = f"""
CRITICAL PRIVACY NOTES:
- This health data was shared ONLY for purpose: "{consent_purpose}"
- Anonymization level: {anonymization}
- Health data is EXTREMELY sensitive and protected by special regulations
- NEVER attempt to identify the individual or link this data to other sources
- DO NOT make medical diagnoses or provide medical advice based on this data
- All analysis must strictly adhere to the consented purpose
"""
        
        # Health-specific guidance
        data_guidance = """
Health Data Guidelines:
- Focus only on the patterns and metrics relevant to the stated purpose
- Do not speculate about health conditions beyond what is explicitly in the data
- Avoid mentioning specific timestamps or patterns that could be identifying
- Be aware that health metrics should be interpreted by medical professionals
- Always note the limitations of the data for health interpretations
"""
        
        # Construct the full prompt
        prompt = f"""# Instructions
{instructions}

{privacy_notes}

{data_guidance}

# Health Data
```json
{data_str}
```

Process the above health data according to the instructions, with the highest level of privacy respect.
Your analysis must strictly remain within the specified purpose: "{consent_purpose}" and should include appropriate caveats about data interpretation.
"""
        
        return prompt.strip()
    
    def _financial_template(
        self, 
        instructions: str, 
        data_content: Dict[str, Any], 
        data_metadata: Dict[str, Any],
        model_name: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Template specifically optimized for financial data."""
        # Format the data content as a string
        data_str = json.dumps(data_content, indent=2)
        
        if max_tokens:
            max_content_chars = max_tokens * 4
            if len(data_str) > max_content_chars:
                data_str = data_str[:max_content_chars] + f"... {self.truncation_message}"
        
        # Extract relevant metadata
        consent_purpose = data_metadata.get("purpose", "unspecified")
        anonymization = data_metadata.get("anonymization_level", "unknown")
        
        # Add strong privacy warnings for financial data
        privacy_notes = f"""
CRITICAL PRIVACY NOTES:
- This financial data was shared ONLY for purpose: "{consent_purpose}"
- Anonymization level: {anonymization}
- Financial data is highly sensitive and protected by regulations
- NEVER attempt to identify the individual or link this data to other sources
- DO NOT provide financial advice or make predictions based on this data
- All analysis must strictly adhere to the consented purpose
"""
        
        # Financial-specific guidance
        data_guidance = """
Financial Data Guidelines:
- Focus only on the patterns and metrics relevant to the stated purpose
- Do not attempt to infer socioeconomic status or lifestyle from transactions
- Avoid mentioning specific merchants, locations, or transaction details that could be identifying
- Be aware that spending patterns reveal sensitive information about lifestyle and habits
- Always note the limitations of the data for financial interpretations
"""
        
        # Construct the full prompt
        prompt = f"""# Instructions
{instructions}

{privacy_notes}

{data_guidance}

# Financial Data
```json
{data_str}
```

Process the above financial data according to the instructions, with the highest level of privacy respect.
Your analysis must strictly remain within the specified purpose: "{consent_purpose}" and should avoid judgments about spending habits or financial status.
"""
        
        return prompt.strip()
    
    def _default_template(
        self, 
        instructions: str, 
        data_content: Dict[str, Any], 
        data_metadata: Dict[str, Any],
        model_name: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Default template for unknown data types."""
        # Format the data content as a string
        data_str = json.dumps(data_content, indent=2)
        
        if max_tokens:
            max_content_chars = max_tokens * 4
            if len(data_str) > max_content_chars:
                data_str = data_str[:max_content_chars] + f"... {self.truncation_message}"
        
        # Extract relevant metadata
        data_type = data_metadata.get("data_type", "unknown")
        consent_purpose = data_metadata.get("purpose", "unspecified")
        anonymization = data_metadata.get("anonymization_level", "unknown")
        
        # Add privacy warnings
        privacy_notes = f"""
PRIVACY NOTES:
- This data was shared ONLY for purpose: "{consent_purpose}"
- Anonymization level: {anonymization}
- Data type: {data_type}
- Always respect user privacy and consent boundaries
- Do not attempt to identify individuals or extract information beyond the stated purpose
"""
        
        # Construct the prompt
        prompt = f"""# Instructions
{instructions}

{privacy_notes}

# Data Content ({data_type})
```json
{data_str}
```

Process the above data according to the instructions, strictly respecting the user's consent purpose: "{consent_purpose}".
Do not draw conclusions beyond what is directly supported by the data.
"""
        
        return prompt.strip()


# Dependency for FastAPI
def get_prompt_service() -> PromptService:
    """
    Get prompt service instance for dependency injection.
    """
    return PromptService() 