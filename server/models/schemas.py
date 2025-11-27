"""
Pydantic models for the claim assistance system
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum


class SessionStatus(str, Enum):
    AWAITING_POLICY = "awaiting_policy"
    AWAITING_DOCUMENT_CHOICE = "awaiting_document_choice"
    AWAITING_BILL = "awaiting_bill"
    AWAITING_PRESCRIPTION = "awaiting_prescription"
    AWAITING_BOTH_BILL = "awaiting_both_bill"
    AWAITING_BOTH_PRESCRIPTION = "awaiting_both_prescription"
    COMPLETED = "completed"


class DocumentChoice(str, Enum):
    BILL = "bill"
    PRESCRIPTION = "prescription"
    BOTH = "both"


class ChatOption(BaseModel):
    """Option for user to select"""
    value: str
    label: str


class ChatResponse(BaseModel):
    """Chat response with session tracking"""
    reply: str
    session_id: str
    status: SessionStatus
    options: Optional[List[ChatOption]] = None  # Clickable options for user
    input_type: str = "file"  # "file", "text", "options"


# --- Bill Extraction Models ---

class BillLineItem(BaseModel):
    """Single line item from hospital bill"""
    item_name: str
    amount: float
    per_day_rate: Optional[float] = None  # For room rent, ICU
    days: Optional[int] = None  # For room rent, ICU
    item_specific_copay: Optional[float] = None  # If this item has specific copay %


class BillExtraction(BaseModel):
    """Extracted data from hospital bill"""
    total_amount: float
    line_items: List[BillLineItem]
    discount: Optional[float] = 0.0


# --- Policy Bond Extraction Models ---

class BonusStructure(BaseModel):
    """NCB or Loyalty bonus structure"""
    bonus_type: str  # "ncb" or "loyalty"
    current_percentage: Optional[float] = None  # Current applicable %
    yearly_increase: Optional[List[float]] = None  # [20, 40, 60, 80, 100] progression
    max_percentage: Optional[float] = None  # Cap like 400%
    absolute_amount: Optional[float] = None  # If it's a fixed amount instead


class PolicyLimit(BaseModel):
    """Single coverage limit from policy bond"""
    coverage_name: str  # e.g., "Room Rent", "ICU Charges"
    limit_value: float  # The raw number
    limit_type: str  # "absolute", "percentage", "per_day"
    per_day_max: Optional[float] = None  # If per_day type


class BondExtraction(BaseModel):
    """Extracted data from policy bond"""
    sum_insured: float
    general_copay_percentage: Optional[float] = 0.0
    ncb_bonus: Optional[BonusStructure] = None
    loyalty_bonus: Optional[BonusStructure] = None
    coverage_limits: List[PolicyLimit]


# --- Calculation Models ---

class MatchedItem(BaseModel):
    """Bill item matched with policy limit"""
    bill_item: str
    bill_amount: float
    matched_coverage: Optional[str] = None
    policy_limit: Optional[float] = None  # Absolute limit after conversion
    limit_type: Optional[str] = None
    eligible_amount: float  # min(bill_amount, policy_limit)
    excess_amount: float  # bill_amount - eligible_amount (patient pays)
    copay_amount: float  # eligible_amount * copay%
    insurer_pays: float  # eligible_amount - copay_amount
    patient_pays: float  # excess_amount + copay_amount


class CalculationResult(BaseModel):
    """Final claim calculation result"""
    # Sum insured details
    base_sum_insured: float
    effective_sum_insured: float  # After NCB + Loyalty bonus
    ncb_bonus_applied: Optional[float] = 0.0
    loyalty_bonus_applied: Optional[float] = 0.0
    
    # Bill totals
    total_bill_amount: float
    total_discount: float
    net_bill_amount: float
    
    # Calculation breakdown
    matched_items: List[MatchedItem]
    
    # Final amounts
    total_eligible: float
    total_excess: float  # Non-payable due to limits
    total_copay: float
    general_copay_percentage: float
    insurer_pays: float
    patient_pays: float
