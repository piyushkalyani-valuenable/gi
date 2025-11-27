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
        
        # Check if response is plain text (not JSON)
        if not cleaned.startswith('{') and not cleaned.startswith('['):
            print(f"ERROR: Gemini returned plain text instead of JSON")
            print(f"Response: {cleaned[:200]}")
            raise ValueError(f"Gemini returned plain text instead of JSON. Response: {cleaned[:200]}")
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Response was: {cleaned[:500]}")
            raise ValueError(f"Failed to parse Gemini response as JSON: {e}")
    
    def extract_bill(self, file_data: bytes, filename: str, max_retries: int = 2) -> Dict[str, Any]:
        """
        Extract line items from hospital bill with retry logic
        
        Args:
            file_data: Bill file bytes
            filename: Bill filename
            max_retries: Maximum number of retry attempts
        
        Returns dict with:
        - total_amount: float
        - discount: float
        - line_items: list of {item_name, amount, per_day_rate?, days?}
        """
        prompt = """Extract charges from this hospital bill.

**CRITICAL: Many bills have TWO sections:**
1. **SUMMARY** section (e.g., "Room & Nursing Charges: 2350", "Professional Fees: 1200")
2. **DETAILED BREAKUP** section (e.g., "Bed Charges - PRIVATE: 1250", "Dr. Shaunak Sule: 500")

**YOU MUST EXTRACT FROM ONLY ONE SECTION:**
- If you see BOTH summary AND detailed sections → extract ONLY from the DETAILED section
- If you see ONLY summary → extract from summary
- If you see ONLY detailed → extract from detailed
- NEVER extract from both sections - this causes double-counting!

Return JSON:
{
    "total_amount": <total bill amount>,
    "discount": <discount amount, 0 if none>,
    "line_items": [
        {
            "item_name": "<charge name>",
            "amount": <amount as number>,
            "per_day_rate": <daily rate if applicable, null otherwise>,
            "days": <number of days if applicable, null otherwise>,
            "item_specific_copay": <copay % if mentioned, null otherwise>
        }
    ]
}

**MANDATORY VERIFICATION:**
1. Add up all your line_item amounts
2. They MUST equal total_amount (minus discount)
3. If sum > total → you extracted from BOTH sections (WRONG!)
4. If sum < total → you missed items
5. Fix it before responding

Return ONLY valid JSON. Do NOT return explanatory text."""
        
        # Retry logic
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    print(f"Retry attempt {attempt}/{max_retries} for bill extraction...")
                
                response = self.gemini.chat_with_file(prompt, file_data, filename)
                extracted_data = self._parse_json_response(response)
                
                # Deduplicate line items
                extracted_data = self._deduplicate_bill_items(extracted_data)
                
                return extracted_data
                
            except ValueError as e:
                last_error = e
                error_msg = str(e)
                
                if "plain text instead of JSON" in error_msg:
                    print(f"Attempt {attempt + 1} failed: Gemini returned plain text")
                    if attempt < max_retries:
                        # Add stronger instruction for retry
                        prompt = prompt.replace(
                            "Return ONLY valid JSON.",
                            "Return ONLY valid JSON. NO explanations, NO apologies, ONLY JSON starting with { and ending with }."
                        )
                        continue
                else:
                    print(f"Attempt {attempt + 1} failed: {error_msg}")
                    if attempt < max_retries:
                        continue
                
                # If last attempt, raise the error
                if attempt == max_retries:
                    raise ValueError(f"Failed to extract bill after {max_retries + 1} attempts. Last error: {error_msg}")
            
            except Exception as e:
                last_error = e
                print(f"Attempt {attempt + 1} failed with unexpected error: {e}")
                if attempt == max_retries:
                    raise
        
        # Should never reach here, but just in case
        raise last_error if last_error else Exception("Unknown error in bill extraction")
    
    def _deduplicate_bill_items(self, bill_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove duplicate bill items (same item_name appearing multiple times)
        
        Strategy: Keep the first occurrence of each unique item name
        """
        line_items = bill_data.get('line_items', [])
        
        if not line_items:
            return bill_data
        
        seen_items = {}
        deduplicated_items = []
        duplicates_removed = []
        
        for item in line_items:
            item_name = item.get('item_name', '').strip().upper()
            
            if not item_name:
                continue
            
            if item_name not in seen_items:
                # First occurrence - keep it
                seen_items[item_name] = item
                deduplicated_items.append(item)
            else:
                # Duplicate found - skip it
                duplicates_removed.append({
                    'item_name': item.get('item_name'),
                    'amount': item.get('amount'),
                    'reason': f"Duplicate of existing item"
                })
        
        # Log duplicates if any were found
        if duplicates_removed:
            print(f"⚠️ Removed {len(duplicates_removed)} duplicate items:")
            for dup in duplicates_removed[:5]:  # Show first 5
                print(f"  - {dup['item_name']}: ₹{dup['amount']}")
            if len(duplicates_removed) > 5:
                print(f"  ... and {len(duplicates_removed) - 5} more")
        
        bill_data['line_items'] = deduplicated_items
        bill_data['duplicates_removed'] = len(duplicates_removed)
        
        return bill_data
    
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
        - coverage_limits: list of matched limits with page numbers
        - exclusions: list of explicitly excluded items with reasons and page numbers
        """
        keywords_str = ", ".join([f'"{k}"' for k in bill_keywords])
        
        prompt = f"""Analyze this insurance policy bond document.

I need to find coverage information for these items from a hospital bill: {keywords_str}

**IMPORTANT: USE CATEGORY-BASED MATCHING**

Hospital bills have specific item names (like "GLUCOSE TEST", "ELECTROLYTES", "X-RAY CHEST"), but insurance policies use CATEGORY names (like "investigation and diagnostics procedures", "Medicines and drugs", "Room rent").

Your job is to:
1. Identify which CATEGORY each bill item belongs to
2. Find the coverage limit for that CATEGORY in the policy
3. Apply that category's limit to the bill item

**COMMON CATEGORY MAPPINGS:**
- Lab tests (blood tests, glucose, electrolytes, ABG, COVID test, etc.) → "investigation and diagnostics procedures" or "Diagnostics"
- X-rays, CT scans, MRI, ultrasound → "investigation and diagnostics procedures" or "Diagnostics"
- Medicines, tablets, injections → "Medicines, drugs and consumables" or "Pharmacy"
- Room charges, bed charges → "Room rent"
- ICU, CCU, HDU charges → "Intensive Care Unit charges"
- Doctor fees, consultation → "Medical Practitioners' fees"
- Nursing charges → "Nursing charges"
- OT charges, surgery → "Operation theatre charges"
- Oxygen, nebulization → Check if covered under consumables or explicitly excluded

For EACH bill item, determine ONE of three states:
1. **COVERED** - Item falls under a covered category in the policy
2. **EXPLICITLY EXCLUDED** - Item is mentioned in exclusions/non-payable items
3. **NOT MENTIONED** - Item doesn't fit any category and isn't excluded

Return a JSON object with this EXACT structure:
{{
    "sum_insured": <base sum insured amount as number>,
    "general_copay_percentage": <general co-payment percentage as number, 0 if none>,
    "ncb_bonus": {{
        "bonus_type": "ncb",
        "current_percentage": <current applicable NCB percentage as number (e.g., 20 for 20%), null if not found>
    }},
    "loyalty_bonus": {{
        "bonus_type": "loyalty",
        "current_percentage": <current applicable loyalty bonus percentage as number, null if not found>
    }},
    "coverage_limits": [
        {{
            "bill_item": "<exact item name from the bill>",
            "matched_category": "<the policy category this item falls under>",
            "coverage_name": "<matching coverage name in policy>",
            "policy_line": "<exact text/clause from the policy document>",
            "page_number": <page number where this coverage is mentioned, null if not found>,
            "limit_value": <the limit number, use sum_insured if "covered up to Sum Insured">,
            "limit_type": "<one of: absolute, percentage, per_day, sum_insured>",
            "per_day_max": <if per_day type, the daily limit, null otherwise>
        }}
    ],
    "exclusions": [
        {{
            "bill_item": "<exact item name from the bill>",
            "exclusion_reason": "<exact text from policy explaining why this is excluded>",
            "exclusion_category": "<category like 'Non-Payable Items', 'Exclusions', 'Not Covered', etc.>",
            "policy_line": "<exact clause text from exclusions section>",
            "page_number": <page number where this exclusion is mentioned>
        }}
    ]
}}

CRITICAL RULES:

1. **EXCLUSIONS TAKE PRIORITY** (CHECK FIRST!):
   - BEFORE matching to any category, CHECK if the item is in the exclusions/non-payable list
   - If an item is SPECIFICALLY mentioned in exclusions → add to exclusions array, NOT coverage_limits
   - Example: "Oxygen cylinder" or "Oxygen" in exclusions → excluded, even if "consumables" are covered
   - Example: "Vitamins" in exclusions → excluded, even if "medicines" are covered
   - Specific exclusions OVERRIDE general category coverage

2. **CATEGORY-BASED MATCHING** (for items NOT excluded):
   - Only match to categories if item is NOT in exclusions
   - DO match bill items to their logical CATEGORY in the policy
   - Example: "GLUCOSE TEST" → matches "investigation and diagnostics procedures"
   - Example: "ELECTROLYTES" → matches "investigation and diagnostics procedures"
   - Example: "ABG (ARTERIAL BLOOD GAS)" → matches "investigation and diagnostics procedures"
   - Example: "COVID-19 TEST" → matches "investigation and diagnostics procedures"
   - Example: "PARACETAMOL" → matches "Medicines, drugs and consumables"
   - If policy says category is "Covered up to Sum Insured", use sum_insured as limit_value and limit_type as "sum_insured"

3. **COVERAGE DETECTION** (for coverage_limits array):
   - Match bill items to their CATEGORY, not exact keyword
   - limit_type detection:
     * "per_day": if limit mentions "per day", "/day", "daily"
     * "percentage": if limit is a % of sum insured
     * "absolute": if it's a fixed rupee amount
     * "sum_insured": if covered up to full sum insured
   - Include page_number where coverage is found

4. **EXCLUSION DETECTION** (for exclusions array):
   - Check exclusions section, non-payable items, limitations, "Items Not Payable" tables
   - Look for specific mentions like "Oxygen cylinder", "Oxygen (for usage outside)", "Vitamins", etc.
   - Only add if EXPLICITLY mentioned as excluded/non-payable
   - MUST include exclusion_reason and policy_line
   - Include partial matches (e.g., "OXYGEN PER HOUR" matches "Oxygen cylinder" exclusion)

5. **NOT MENTIONED** (absent from both arrays):
   - Only if item doesn't fit ANY category AND isn't excluded
   - This should be RARE - most hospital items fit a category

6. **PAGE NUMBERS**:
   - Include page numbers where coverage/exclusion is found
   - Set to null if not visible in document

7. Return ONLY the JSON, no explanations.
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
