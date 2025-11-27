"""
Keyword file loading utilities
"""
from typing import List
from pathlib import Path
from fastapi import HTTPException
from config.constants import KEYWORD_FILES


def load_keywords_for_turn(turn_number: int) -> List[str]:
    """
    Load keywords from file based on turn number
    
    Args:
        turn_number: Extraction turn (1, 2, or 3)
    
    Returns:
        List of keywords
    
    Raises:
        HTTPException: If file not found or invalid turn number
    """
    if turn_number not in KEYWORD_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid turn number: {turn_number}. Only turns 1, 2, and 3 are configured."
        )
    
    filename = KEYWORD_FILES[turn_number]
    filepath = Path(__file__).parent.parent / filename
    
    try:
        with open(filepath, 'r') as f:
            keywords = [line.strip() for line in f if line.strip()]
        
        if not keywords:
            raise ValueError(f"'{filename}' found but is empty.")
        
        print(f"Loaded {len(keywords)} keywords from {filename}.")
        return keywords
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail=f"Configuration Error: The required file '{filename}' was not found."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Configuration Error: {e}")
