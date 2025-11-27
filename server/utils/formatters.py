"""
Output formatting utilities
"""
from typing import List, Dict


def format_extracted_data_for_display(extracted_data: List[Dict[str, str]]) -> str:
    """
    Format extracted data for display
    
    Args:
        extracted_data: List of extracted data dicts
    
    Returns:
        Formatted string
    """
    output_lines = []
    header = ["Field", "Value", "Units"]
    
    output_lines.append(f"{header[0].ljust(25)}{header[1].ljust(25)}{header[2].ljust(10)}")
    output_lines.append("-" * 60)
    
    for row in extracted_data:
        field = row.get('Field', '').strip()
        value = row.get('Value', '').strip().replace('"', '')
        units = row.get('Units', '').strip()
        
        line = f"{field.ljust(25)}{value.ljust(25)}{units.ljust(10)}"
        output_lines.append(line)
    
    return "\n".join(output_lines)


def format_df_list_for_display(df_list: List[Dict[str, str]], df_name: str) -> str:
    """
    Format dataframe list for display
    
    Args:
        df_list: List of keyword-value dicts
        df_name: Name of the dataframe
    
    Returns:
        Formatted string with markdown code block
    """
    if not df_list:
        return f"\n**{df_name}** is currently empty.\n"
    
    output_lines = []
    output_lines.append(f"### Data Extracted into {df_name}\n")
    output_lines.append(f"{'KEYWORD'.ljust(30)}{'VALUE'.ljust(30)}")
    output_lines.append("-" * 60)
    
    for row in df_list:
        keyword = row.get('keyword', '').strip()
        value = row.get('value', '').strip()
        line = f"{keyword.ljust(30)}{value.ljust(30)}"
        output_lines.append(line)
    
    return f"```text\n{output_lines[0]}\n{output_lines[1]}\n{output_lines[2]}\n{'\n'.join(output_lines[3:])}\n```\n"
