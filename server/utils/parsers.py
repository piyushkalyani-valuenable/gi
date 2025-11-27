"""
Data parsing utilities
"""
import csv
import io
import re
from typing import List, Dict


def parse_currency_to_float(currency_str: str) -> float:
    """
    Clean currency string and convert to float
    
    Args:
        currency_str: Currency string (e.g., "1,85,000" or "₹10,000")
    
    Returns:
        Float value or 0.0 if parsing fails
    """
    if not currency_str or str(currency_str).upper() in ('N/A', 'NOT FOUND', 'NONE', 'NIL'):
        return 0.0
    
    try:
        clean_str = str(currency_str).replace('"', '').replace(',', '').replace('₹', '').replace('INR', '').replace('$', '').replace('%', '').strip()
        return float(clean_str)
    except (ValueError, TypeError):
        print(f"Warning: Failed to parse '{currency_str}' to float. Defaulting to 0.0.")
        return 0.0


def parse_csv_output(csv_data: str) -> List[Dict[str, str]]:
    """
    Parse CSV output from AI model
    
    Args:
        csv_data: Raw CSV string from AI
    
    Returns:
        List of dictionaries with extracted data
    """
    try:
        csv_file = io.StringIO(csv_data)
        lines = csv_file.readlines()
        
        # Find header line
        header_index = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("Extraction_ID") or line.strip().startswith("Field"):
                header_index = i
                break
        
        if header_index == -1:
            print("Warning: Could not find expected CSV header in response.")
            return []
        
        clean_csv_string = "".join(lines[header_index:])
        clean_csv_file = io.StringIO(clean_csv_string)
        reader = csv.DictReader(clean_csv_file)
        
        return list(reader)
    except Exception as e:
        print(f"CSV Parsing Error: {e}")
        return []


def create_dataframe_list(extracted_data: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Convert extracted data to dataframe-like list
    
    Args:
        extracted_data: Raw extracted data
    
    Returns:
        List of dicts with 'keyword' and 'value' keys
    """
    df_list = []
    for row in extracted_data:
        field = row.get('Field', '').strip()
        value = row.get('Value', '').strip().replace('"', '')
        units = row.get('Units', '').strip()
        
        if value.upper() in ('N/A', 'NOT FOUND', 'NONE') and units.upper() in ('N/A', 'NOT FOUND', 'NONE'):
            continue
        
        if units and units.upper() != 'N/A':
            formatted_value = f"{value} {units}"
        else:
            formatted_value = value
        
        df_list.append({
            'keyword': field,
            'value': formatted_value
        })
    return df_list


def clean_numeric_values(df_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Clean mixed alphanumeric values to extract only numbers
    
    Args:
        df_list: List of keyword-value dicts
    
    Returns:
        Cleaned list with numeric values extracted
    """
    cleaned_df = []
    for row in df_list:
        value = str(row.get('value', ''))
        numeric_part = re.findall(r"\d+(?:\.\d+)?", value.replace(',', ''))
        if numeric_part:
            row['value'] = numeric_part[0]
        cleaned_df.append(row)
    return cleaned_df


def clean_ncb_value(value: str) -> str:
    """
    Clean NCB-related field values
    
    Args:
        value: Raw value string
    
    Returns:
        Cleaned value
    """
    value = str(value).strip()
    
    # If has number and %, extract "number%"
    if re.search(r'\d+', value) and '%' in value:
        match = re.search(r'\d+\s*%', value)
        if match:
            return match.group(0).replace(" ", "")
    
    # If has number but no %, extract just the number
    elif re.search(r'\d+', value) and '%' not in value:
        match = re.search(r'\d+(?:\.\d+)?', value)
        if match:
            return match.group(0)
    
    return value
