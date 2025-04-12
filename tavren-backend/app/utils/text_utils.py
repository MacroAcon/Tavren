"""
Text processing utilities for tokenization, chunking, and formatting.
"""

import re
from typing import List, Optional
import tiktoken

# Default tokenizer model
DEFAULT_TOKENIZER = "cl100k_base"  # Used by GPT-4, GPT-3.5-Turbo

def get_tokenizer(model: Optional[str] = None):
    """Get a tokenizer for the specified model or the default."""
    try:
        if model:
            return tiktoken.encoding_for_model(model)
        return tiktoken.get_encoding(DEFAULT_TOKENIZER)
    except KeyError:
        # Fallback to default if model not found
        return tiktoken.get_encoding(DEFAULT_TOKENIZER)

def count_tokens(text: str, model: Optional[str] = None) -> int:
    """
    Count the number of tokens in a text string.
    
    Args:
        text: The text to count tokens for
        model: Optional model name to use specific tokenizer
        
    Returns:
        Number of tokens
    """
    if not text:
        return 0
        
    tokenizer = get_tokenizer(model)
    tokens = tokenizer.encode(text)
    return len(tokens)

def truncate_text_to_token_limit(text: str, max_tokens: int, model: Optional[str] = None) -> str:
    """
    Truncate text to a maximum token count.
    
    Args:
        text: The text to truncate
        max_tokens: Maximum number of tokens
        model: Optional model name for tokenizer
        
    Returns:
        Truncated text
    """
    if not text:
        return ""
        
    tokenizer = get_tokenizer(model)
    tokens = tokenizer.encode(text)
    
    if len(tokens) <= max_tokens:
        return text
        
    truncated_tokens = tokens[:max_tokens]
    return tokenizer.decode(truncated_tokens)

def chunk_text(
    text: str, 
    max_tokens: int = 512, 
    overlap_tokens: int = 50,
    respect_boundaries: bool = True,
    model: Optional[str] = None
) -> List[str]:
    """
    Split text into chunks with a maximum token count and optional overlap.
    
    Args:
        text: Text to split into chunks
        max_tokens: Maximum tokens per chunk
        overlap_tokens: Number of tokens to overlap between chunks
        respect_boundaries: Try to split at paragraph/sentence boundaries
        model: Optional model name for tokenizer
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
        
    # Get tokens for the full text
    tokenizer = get_tokenizer(model)
    tokens = tokenizer.encode(text)
    
    # If text is already small enough, return as single chunk
    if len(tokens) <= max_tokens:
        return [text]
    
    # Prepare to store chunks
    chunks = []
    
    # Find semantic boundaries (paragraphs, sentences)
    if respect_boundaries:
        # Get paragraph boundaries
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk_tokens = []
        current_paragraphs = []
        
        for paragraph in paragraphs:
            paragraph_tokens = tokenizer.encode(paragraph)
            
            # If adding this paragraph would exceed max_tokens, store the chunk and start a new one
            if len(current_chunk_tokens) + len(paragraph_tokens) > max_tokens:
                # If we have content for a chunk, add it
                if current_chunk_tokens:
                    chunk_text = '\n\n'.join(current_paragraphs)
                    chunks.append(chunk_text)
                    
                    # Start new chunk with overlap
                    if overlap_tokens > 0 and len(current_chunk_tokens) > overlap_tokens:
                        # Find the starting point for overlap
                        overlap_start = len(current_chunk_tokens) - overlap_tokens
                        overlap_text = tokenizer.decode(current_chunk_tokens[overlap_start:])
                        
                        # Find paragraph boundary within overlap if possible
                        overlap_paragraphs = re.split(r'\n\s*\n', overlap_text)
                        if len(overlap_paragraphs) > 1:
                            # Use the last complete paragraph from overlap
                            current_paragraphs = [overlap_paragraphs[-1]]
                            current_chunk_tokens = tokenizer.encode(current_paragraphs[0])
                        else:
                            current_paragraphs = []
                            current_chunk_tokens = []
                    else:
                        current_paragraphs = []
                        current_chunk_tokens = []
                
                # If paragraph is too long for a single chunk, we need to split it
                if len(paragraph_tokens) > max_tokens:
                    # Split paragraph into sentences
                    sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                    
                    temp_tokens = []
                    temp_sentences = []
                    
                    for sentence in sentences:
                        sentence_tokens = tokenizer.encode(sentence)
                        
                        # If adding this sentence exceeds max_tokens, store chunk and start new one
                        if len(temp_tokens) + len(sentence_tokens) > max_tokens:
                            if temp_tokens:
                                chunk_text = ' '.join(temp_sentences)
                                chunks.append(chunk_text)
                                
                                # Start new chunk with overlap
                                if overlap_tokens > 0 and len(temp_tokens) > overlap_tokens:
                                    overlap_start = len(temp_tokens) - overlap_tokens
                                    temp_tokens = temp_tokens[overlap_start:]
                                    overlap_text = tokenizer.decode(temp_tokens)
                                    
                                    # Try to find sentence boundary in overlap
                                    overlap_sentences = re.split(r'(?<=[.!?])\s+', overlap_text)
                                    if len(overlap_sentences) > 1:
                                        temp_sentences = [overlap_sentences[-1]]
                                        temp_tokens = tokenizer.encode(temp_sentences[0])
                                    else:
                                        temp_sentences = []
                                        temp_tokens = []
                                else:
                                    temp_sentences = []
                                    temp_tokens = []
                            
                            # If sentence is too long, we need to force-split it
                            if len(sentence_tokens) > max_tokens:
                                # Force split by tokens
                                for i in range(0, len(sentence_tokens), max_tokens - overlap_tokens):
                                    if i > 0:
                                        # Include overlap from previous chunk
                                        start_idx = max(0, i - overlap_tokens)
                                    else:
                                        start_idx = 0
                                        
                                    end_idx = min(len(sentence_tokens), i + max_tokens)
                                    chunk_tokens = sentence_tokens[start_idx:end_idx]
                                    chunk_text = tokenizer.decode(chunk_tokens)
                                    chunks.append(chunk_text)
                            else:
                                temp_tokens = sentence_tokens
                                temp_sentences = [sentence]
                        else:
                            temp_tokens.extend(sentence_tokens)
                            temp_sentences.append(sentence)
                    
                    # Add any remaining content from this paragraph
                    if temp_tokens:
                        chunk_text = ' '.join(temp_sentences)
                        chunks.append(chunk_text)
                else:
                    # Start new chunk with this paragraph
                    current_paragraphs = [paragraph]
                    current_chunk_tokens = paragraph_tokens
            else:
                # Add paragraph to current chunk
                current_chunk_tokens.extend(paragraph_tokens)
                current_paragraphs.append(paragraph)
        
        # Add final chunk if there's any content left
        if current_paragraphs:
            chunk_text = '\n\n'.join(current_paragraphs)
            chunks.append(chunk_text)
    else:
        # Simple token-based chunking without respecting boundaries
        chunk_size = max_tokens - overlap_tokens
        
        for i in range(0, len(tokens), chunk_size):
            # Include overlap from previous chunk
            if i > 0:
                start_idx = i - overlap_tokens
            else:
                start_idx = 0
                
            end_idx = min(len(tokens), i + max_tokens)
            chunk_tokens = tokens[start_idx:end_idx]
            chunk_text = tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
    
    return chunks

def format_context(results: List[dict], max_tokens: int = 2000, model: Optional[str] = None) -> str:
    """
    Format search results into a context string for RAG, respecting token limits.
    
    Args:
        results: List of search results with text and metadata
        max_tokens: Maximum tokens for the formatted context
        model: Optional model name for tokenizer
        
    Returns:
        Formatted context string
    """
    if not results:
        return ""
        
    context_parts = []
    total_tokens = 0
    tokenizer = get_tokenizer(model)
    
    for i, result in enumerate(results):
        # Format this chunk with source information
        source_info = f"[Source {i+1}"
        if result.get("package_name"):
            source_info += f": {result['package_name']}"
        source_info += "]"
        
        chunk_text = f"{source_info}:\n{result['text']}"
        chunk_tokens = len(tokenizer.encode(chunk_text))
        
        # Check if adding this would exceed our token limit
        if total_tokens + chunk_tokens > max_tokens:
            # If this is the first chunk, truncate it to fit
            if i == 0:
                truncated_text = truncate_text_to_token_limit(chunk_text, max_tokens, model)
                context_parts.append(truncated_text)
                total_tokens = max_tokens
                break
            else:
                # Skip this chunk as we've reached the token limit
                break
                
        # Add this chunk to our context
        context_parts.append(chunk_text)
        total_tokens += chunk_tokens
    
    # Join all context parts with clear separation
    return "\n\n".join(context_parts) 