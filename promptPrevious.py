"""
Extraction service - Uses Gemini to extract data from documents
"""
import json
import re
from typing import Dict, Any, List
from services.gemini_service import GeminiService


class ExtractionService:
    """Handles document extraction using Gemini AI"""
    
    def __init__(self):
        self.gemini = GeminiService()
    
    def _clean_json_response(self, response: str) -> str:
        """Remove markdown code blocks from response"""
        # Remove ```json and ``` markers
        cleaned = re.sub(r'^```json\s*', '', response.strip())
        cleaned = re.sub(r'^```\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        return cleaned.strip()
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from Gemini response"""
        cleaned = self._clean_json_response(response)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Response was: {cleaned[:500]}")
            raise ValueError(f"Failed to parse Gemini response as JSON: {e}")
    
    def extract_bill(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract line items from hospital bill
        
        Returns dict with:
        - total_amount: float
        - discount: float
        - line_items: list of {item_name, amount, per_day_rate?, days?}
        """
        prompt = """Analyze this hospital bill document and extract all billing information.

Return a JSON object with this EXACT structure:
{
    "total_amount": <total bill amount as number>,
    "discount": <any discount amount as number, 0 if none>,
    "line_items": [
        {
            "item_name": "<name of the charge/procedure>",
            "amount": <total amount for this item as number>,
            "per_day_rate": <per day rate if applicable, null otherwise>,
            "days": <number of days if applicable, null otherwise>,
            "item_specific_copay": <copay percentage for this specific item if mentioned, null otherwise>
        }
    ]
}

IMPORTANT RULES:
1. **CRITICAL - NO DOUBLE COUNTING**: Extract EITHER summary categories OR individual line items, NOT BOTH.
   - If the bill has summary categories like "Room & Nursing Charges: 2350" that include sub-items, extract ONLY the summary.
   - If the bill has only individual items without summaries, extract those individual items.
   - The SUM of all line_items amounts should EQUAL the total_amount (minus discount).
   - NEVER include both a category total AND its component items.

2. For Room Rent and ICU charges: ALWAYS try to extract per_day_rate and days. Calculate from total if needed.

3. All amounts should be numbers, not strings.

4. item_specific_copay should be a percentage number (e.g., 20 for 20%), null if not specified.

5. VERIFY: Add up all your line_item amounts - they should match total_amount. If they don't, you have duplicates.

6. Return ONLY the JSON, no explanations.
"""
        
        response = self.gemini.chat_with_file(prompt, file_data, filename)
        return self._parse_json_response(response)
    
    def extract_bond_for_keywords(
        self, 
        file_data: bytes, 
        filename: str, 
        bill_keywords: List[str]
    ) -> Dict[str, Any]:
        """
        Extract policy bond data for specific keywords from bill
        
        Args:
            file_data: Policy bond file bytes
            filename: Policy bond filename
            bill_keywords: List of item names from the bill to match
        
        Returns dict with:
        - sum_insured: float
        - general_copay_percentage: float
        - ncb_bonus: bonus structure
        - loyalty_bonus: bonus structure  
        - coverage_limits: list of matched limits
        """
        keywords_str = ", ".join([f'"{k}"' for k in bill_keywords])
        
        prompt = f"""Analyze this insurance policy bond document.

I need to find coverage limits for these items from a hospital bill: {keywords_str}

Return a JSON object with this EXACT structure:
{{
    "sum_insured": <base sum insured amount as number>,
    "general_copay_percentage": <general co-payment percentage as number, 0 if none>,
    "ncb_bonus": {{
        "bonus_type": "ncb",
        "current_percentage": <current applicable NCB percentage, null if not found>,
        "yearly_increase": [<array of yearly increase percentages like [20, 40, 60, 80, 100]>],
        "max_percentage": <maximum NCB percentage cap, null if not found>,
        "absolute_amount": <fixed bonus amount if not percentage based, null otherwise>
    }},
    "loyalty_bonus": {{
        "bonus_type": "loyalty",
        "current_percentage": <current applicable loyalty bonus percentage, null if not found>,
        "yearly_increase": [<array of yearly increase percentages>],
        "max_percentage": <maximum loyalty bonus percentage cap, null if not found>,
        "absolute_amount": <fixed bonus amount if not percentage based, null otherwise>
    }},
    "coverage_limits": [
        {{
            "bill_item": "<exact item name from the bill>",
            "coverage_name": "<matching coverage name in policy>",
            "policy_line": "<exact text/clause from the policy document where this limit is mentioned>",
            "limit_value": <the limit number>,
            "limit_type": "<one of: absolute, percentage, per_day>",
            "per_day_max": <if per_day type, the daily limit, null otherwise>
        }}
    ]
}}

IMPORTANT RULES:
1. For each bill item, find a SPECIFIC matching coverage in the policy. Only match if there is a clear, direct coverage for that item.
2. limit_type detection:
   - "per_day": if limit mentions "per day", "/day", "daily"
   - "percentage": if limit is a % of sum insured OR if the number is less than 100 without currency
   - "absolute": if it's a fixed rupee amount
3. **CRITICAL**: If a bill item has NO SPECIFIC matching coverage in the policy, set ALL coverage fields to null:
   - coverage_name: null
   - policy_line: null
   - limit_value: null
   - limit_type: null
   - per_day_max: null
   DO NOT fall back to general "Inpatient Care" or "Hospitalization" coverage. Only match specific limits.
4. For NCB/Loyalty bonus: extract the progression structure if available (e.g., "20% first year, 40% second year" = [20, 40]).
5. Set bonus fields to null if not found in the policy.
6. Return ONLY the JSON, no explanations.
"""
        
        response = self.gemini.chat_with_file(prompt, file_data, filename)
        return self._parse_json_response(response)


    def extract_prescription(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract procedure and hospital information from prescription
        
        Returns dict with:
        - procedure_name: str
        - hospital_name: str (if available)
        - doctor_name: str (if available)
        - diagnosis: str (if available)
        - additional_info: dict (any other relevant info)
        
        This format is compatible with internal_database for price storage
        """
        prompt = """Analyze this medical prescription/document and extract the procedure and hospital information.

Return a JSON object with this EXACT structure:
{
    "procedure_name": "<name of the medical procedure/treatment recommended>",
    "hospital_name": "<name of the hospital if mentioned, null otherwise>",
    "doctor_name": "<name of the prescribing doctor if mentioned, null otherwise>",
    "diagnosis": "<diagnosis or condition if mentioned, null otherwise>",
    "patient_name": "<patient name if mentioned, null otherwise>",
    "date": "<date of prescription if mentioned, null otherwise>",
    "additional_procedures": [
        "<any additional procedures mentioned>"
    ],
    "notes": "<any other relevant notes>"
}

IMPORTANT RULES:
1. procedure_name should be the PRIMARY procedure or treatment being recommended.
2. If multiple procedures are mentioned, put the main one in procedure_name and others in additional_procedures.
3. Extract hospital_name if the prescription is from a hospital or mentions one.
4. All fields except procedure_name can be null if not found.
5. Return ONLY the JSON, no explanations.
"""
        
        response = self.gemini.chat_with_file(prompt, file_data, filename)
        return self._parse_json_response(response)
