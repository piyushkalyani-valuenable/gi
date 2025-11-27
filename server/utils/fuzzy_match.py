"""
Fuzzy matching utilities
"""
import difflib
from typing import List, Dict, Optional
from config.constants import FUZZY_MATCH_CUTOFF


def find_nearest_keyword_in_df(df_list: List[Dict[str, str]], target_keyword: str, cutoff: float = FUZZY_MATCH_CUTOFF) -> Optional[str]:
    """
    Find nearest matching keyword in dataframe list
    
    Args:
        df_list: List of dicts with 'keyword' key
        target_keyword: Keyword to search for
        cutoff: Similarity threshold (0.0 to 1.0)
    
    Returns:
        Matched keyword or None
    """
    if not df_list:
        return None
    
    keywords = [row.get('keyword', '').strip() for row in df_list if row.get('keyword')]
    if not keywords:
        return None
    
    normalized_to_original = {k.lower(): k for k in keywords}
    matches = difflib.get_close_matches(
        target_keyword.strip().lower(),
        list(normalized_to_original.keys()),
        n=1,
        cutoff=cutoff
    )
    
    if matches:
        return normalized_to_original.get(matches[0])
    return None


def find_nearest_field_in_extracted(extracted_rows: List[Dict[str, str]], target_field: str, cutoff: float = FUZZY_MATCH_CUTOFF) -> Optional[str]:
    """
    Find nearest matching field in extracted data
    
    Args:
        extracted_rows: List of extracted data dicts
        target_field: Field name to search for
        cutoff: Similarity threshold
    
    Returns:
        Matched field name or None
    """
    if not extracted_rows:
        return None
    
    fields = [row.get('Field', '').strip() for row in extracted_rows if row.get('Field')]
    if not fields:
        return None
    
    normalized_to_original = {f.lower(): f for f in fields}
    matches = difflib.get_close_matches(
        target_field.strip().lower(),
        list(normalized_to_original.keys()),
        n=1,
        cutoff=cutoff
    )
    
    if matches:
        return normalized_to_original[matches[0]]
    return None
