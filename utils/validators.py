"""
Validation utilities for the AI Language Tutor application.
"""

from typing import Any, Dict, Optional


def validate_input(text: str, max_length: int = 1000) -> bool:
    """Validate user input text."""
    if not text or not isinstance(text, str):
        return False
    
    if len(text.strip()) == 0:
        return False
    
    if len(text) > max_length:
        return False
    
    return True


def validate_api_response(response: Dict[str, Any]) -> bool:
    """Validate API response structure."""
    if not isinstance(response, dict):
        return False
    
    # Add specific validation logic as needed
    return True


