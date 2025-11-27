"""
Calculation service - Matches bill items to policy limits and calculates claim
"""
from typing import Dict, Any, List, Optional


class CalculationService:
    """Handles claim calculation logic"""
    
    def calculate_new_sum_insured_with_bonus(
        self,
        base_sum_insured: float,
        ncb_bonus: Optional[Dict[str, Any]],
        loyalty_bonus: Optional[Dict[str, Any]],
        is_ncb_applied: bool = True  # Flag to control NCB application (hardcoded for now)
    ) -> Dict[str, Any]:
        """
        Calculate effective sum insured after applying NCB and Loyalty bonuses
        
        Args:
            base_sum_insured: Original sum insured from policy
            ncb_bonus: NCB bonus structure from extraction (simplified: just current_percentage)
            loyalty_bonus: Loyalty bonus structure from extraction (simplified: just current_percentage)
            is_ncb_applied: Whether to apply NCB bonus (True by default, can be made dynamic later)
        
        Returns:
            Dict with effective_sum_insured, ncb_applied, loyalty_applied
        """
        ncb_applied = 0.0
        ncb_percentage = 0.0
        loyalty_applied = 0.0
        loyalty_percentage = 0.0
        
        # Apply NCB bonus - only if flag is True
        if is_ncb_applied and ncb_bonus and ncb_bonus.get('current_percentage'):
            ncb_percentage = ncb_bonus['current_percentage']
            ncb_applied = base_sum_insured * (ncb_percentage / 100)
        
        # Apply Loyalty bonus - calculate amount from percentage
        if loyalty_bonus and loyalty_bonus.get('current_percentage'):
            loyalty_percentage = loyalty_bonus['current_percentage']
            loyalty_applied = base_sum_insured * (loyalty_percentage / 100)
        
        effective_sum_insured = base_sum_insured + ncb_applied + loyalty_applied
        
        return {
            "base_sum_insured": base_sum_insured,
            "is_ncb_applied": is_ncb_applied,
            "ncb_percentage": ncb_percentage,
            "ncb_bonus_applied": round(ncb_applied, 2),
            "loyalty_percentage": loyalty_percentage,
            "loyalty_bonus_applied": round(loyalty_applied, 2),
            "effective_sum_insured": round(effective_sum_insured, 2)
        }
    
    def _resolve_limit(
        self,
        limit_value: Optional[float],
        limit_type: Optional[str],
        per_day_max: Optional[float],
        days: Optional[int],
        sum_insured: float
    ) -> Optional[float]:
        """
        Convert any limit type to absolute amount
        
        Args:
            limit_value: Raw limit value
            limit_type: 'absolute', 'percentage', 'per_day', or 'sum_insured'
            per_day_max: Daily limit if per_day type
            days: Number of days from bill (for per_day calculation)
            sum_insured: Effective sum insured (for percentage/sum_insured calculation)
        
        Returns:
            Absolute limit amount, or None if not covered
        """
        # No coverage found = not covered, patient pays all
        if limit_value is None or limit_type is None:
            return None
        
        if limit_type == 'percentage':
            return sum_insured * (limit_value / 100)
        
        elif limit_type == 'per_day':
            daily_limit = per_day_max or limit_value
            num_days = days or 1
            return daily_limit * num_days
        
        elif limit_type == 'sum_insured':
            # Covered up to full sum insured
            return sum_insured
        
        else:  # absolute
            return limit_value
    
    def calculate_claim(
        self,
        bill_extraction: Dict[str, Any],
        bond_extraction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main calculation: match bill items to policy limits and compute payables
        
        Args:
            bill_extraction: Extracted bill data
            bond_extraction: Extracted policy bond data (with coverage_limits and exclusions)
        
        Returns:
            Complete calculation result with coverage status and exclusion reasons
        """
        # Step 1: Calculate effective sum insured with bonuses
        sum_insured_result = self.calculate_new_sum_insured_with_bonus(
            base_sum_insured=bond_extraction.get('sum_insured', 0),
            ncb_bonus=bond_extraction.get('ncb_bonus'),
            loyalty_bonus=bond_extraction.get('loyalty_bonus')
        )
        effective_sum_insured = sum_insured_result['effective_sum_insured']
        
        # Step 2: Get general copay
        general_copay_pct = bond_extraction.get('general_copay_percentage', 0) or 0
        
        # Step 3: Build lookup for coverage limits
        coverage_lookup = {}
        for limit in bond_extraction.get('coverage_limits', []):
            bill_item = limit.get('bill_item', '').lower().strip()
            if bill_item:
                coverage_lookup[bill_item] = limit
        
        # Step 4: Build lookup for exclusions
        exclusion_lookup = {}
        for exclusion in bond_extraction.get('exclusions', []):
            bill_item = exclusion.get('bill_item', '').lower().strip()
            if bill_item:
                exclusion_lookup[bill_item] = exclusion
        
        # Step 5: Process each bill item
        matched_items = []
        total_eligible = 0.0
        total_excess = 0.0
        total_copay = 0.0
        
        bill_items = bill_extraction.get('line_items', [])
        
        for item in bill_items:
            item_name = item.get('item_name', '')
            bill_amount = item.get('amount', 0) or 0
            days = item.get('days')
            item_copay_pct = item.get('item_specific_copay')
            
            # Find matching coverage and exclusion
            item_key = item_name.lower().strip()
            coverage = coverage_lookup.get(item_key, {})
            exclusion = exclusion_lookup.get(item_key, {})
            
            # Determine coverage status
            has_coverage = coverage.get('coverage_name') is not None
            is_excluded = exclusion.get('exclusion_reason') is not None
            
            # Resolve absolute limit
            absolute_limit = self._resolve_limit(
                limit_value=coverage.get('limit_value'),
                limit_type=coverage.get('limit_type'),
                per_day_max=coverage.get('per_day_max'),
                days=days,
                sum_insured=effective_sum_insured
            )
            
            # Check if item is covered
            is_covered = absolute_limit is not None and has_coverage
            
            if is_covered:
                # Item has specific coverage
                eligible_amount = min(bill_amount, absolute_limit)
                excess_amount = max(0, bill_amount - absolute_limit)
                
                # Apply copay: use the HIGHER of item-specific copay and general copay
                if item_copay_pct is not None:
                    copay_pct = max(item_copay_pct, general_copay_pct)
                else:
                    copay_pct = general_copay_pct
                copay_amount = eligible_amount * (copay_pct / 100)
                
                # Calculate final amounts
                insurer_pays = eligible_amount - copay_amount
                patient_pays = excess_amount + copay_amount
                coverage_status = "covered"
            else:
                # Item NOT covered - patient pays everything
                eligible_amount = 0.0
                excess_amount = bill_amount
                copay_pct = 0
                copay_amount = 0.0
                insurer_pays = 0.0
                patient_pays = bill_amount
                
                # Determine why not covered
                if is_excluded:
                    coverage_status = "excluded"
                else:
                    coverage_status = "not_mentioned"
            
            # Build result item
            result_item = {
                "bill_item": item_name,
                "bill_amount": round(bill_amount, 2),
                "is_covered": is_covered,
                "coverage_status": coverage_status,  # "covered", "excluded", or "not_mentioned"
                "matched_category": coverage.get('matched_category'),  # The policy category this item falls under
                "matched_coverage": coverage.get('coverage_name'),
                "policy_line": coverage.get('policy_line'),
                "page_number": coverage.get('page_number'),
                "policy_limit": round(absolute_limit, 2) if absolute_limit is not None else None,
                "limit_type": coverage.get('limit_type'),
                "eligible_amount": round(eligible_amount, 2),
                "excess_amount": round(excess_amount, 2),
                "copay_percentage": copay_pct,
                "copay_amount": round(copay_amount, 2),
                "insurer_pays": round(insurer_pays, 2),
                "patient_pays": round(patient_pays, 2)
            }
            
            # Add exclusion details if excluded
            if is_excluded:
                result_item["exclusion_reason"] = exclusion.get('exclusion_reason')
                result_item["exclusion_category"] = exclusion.get('exclusion_category')
                result_item["exclusion_policy_line"] = exclusion.get('policy_line')
                result_item["exclusion_page_number"] = exclusion.get('page_number')
            
            matched_items.append(result_item)
            
            total_eligible += eligible_amount
            total_excess += excess_amount
            total_copay += copay_amount
        
        # Step 6: Calculate totals
        total_bill = bill_extraction.get('total_amount', 0) or 0
        discount = bill_extraction.get('discount', 0) or 0
        net_bill = total_bill - discount
        
        total_insurer_pays = total_eligible - total_copay
        total_patient_pays = total_excess + total_copay
        
        # Cap insurer payment at effective sum insured
        if total_insurer_pays > effective_sum_insured:
            excess_over_si = total_insurer_pays - effective_sum_insured
            total_insurer_pays = effective_sum_insured
            total_patient_pays += excess_over_si
        
        # Validation: Check if extracted items match total bill
        sum_of_items = sum(item.get('amount', 0) for item in bill_items)
        
        # Calculate discrepancy percentage
        discrepancy = sum_of_items - net_bill
        discrepancy_pct = (abs(discrepancy) / net_bill * 100) if net_bill > 0 else 0
        
        # Determine extraction status
        extraction_status = "accurate"
        warning_message = None
        
        if discrepancy_pct <= 1:
            # Perfect extraction (within 1% - likely rounding)
            extraction_status = "accurate"
        elif discrepancy_pct <= 5:
            # Minor discrepancy
            extraction_status = "minor_discrepancy"
            if discrepancy > 0:
                warning_message = f"Minor over-extraction: Items total Rs.{sum_of_items:.2f} vs bill total Rs.{net_bill:.2f} ({discrepancy_pct:.1f}% over)"
            else:
                warning_message = f"Minor under-extraction: Items total Rs.{sum_of_items:.2f} vs bill total Rs.{net_bill:.2f} ({discrepancy_pct:.1f}% under)"
                total_patient_pays += abs(discrepancy)
        elif discrepancy > 0:
            # Over-extraction (double counting detected)
            extraction_status = "over_extracted"
            warning_message = f"Possible double-counting: Items total Rs.{sum_of_items:.2f} exceeds bill total Rs.{net_bill:.2f} by Rs.{discrepancy:.2f} ({discrepancy_pct:.1f}%)"
            # Scale down proportionally to match total
            scale_factor = net_bill / sum_of_items
            total_insurer_pays = total_insurer_pays * scale_factor
            total_patient_pays = net_bill - total_insurer_pays
            print(f"WARNING: Over-extraction detected. Scaling down by {scale_factor:.3f}")
        else:
            # Under-extraction (missing items)
            extraction_status = "under_extracted"
            missing_amount = abs(discrepancy)
            warning_message = f"Incomplete extraction: {len(bill_items)} items totaling Rs.{sum_of_items:.2f}, but bill total is Rs.{net_bill:.2f}. Missing Rs.{missing_amount:.2f} ({discrepancy_pct:.1f}%)"
            total_patient_pays += missing_amount
            print(f"WARNING: Under-extraction detected. Missing Rs.{missing_amount:.2f}")
        
        return {
            # Sum insured details
            "base_sum_insured": sum_insured_result['base_sum_insured'],
            "effective_sum_insured": effective_sum_insured,
            "ncb_bonus_applied": sum_insured_result['ncb_bonus_applied'],
            "loyalty_bonus_applied": sum_insured_result['loyalty_bonus_applied'],
            
            # Bill totals
            "total_bill_amount": round(total_bill, 2),
            "total_discount": round(discount, 2),
            "net_bill_amount": round(net_bill, 2),
            
            # Breakdown
            "matched_items": matched_items,
            
            # Final amounts
            "total_eligible": round(total_eligible, 2),
            "total_excess": round(total_excess, 2),
            "total_copay": round(total_copay, 2),
            "general_copay_percentage": general_copay_pct,
            "insurer_pays": round(total_insurer_pays, 2),
            "patient_pays": round(total_patient_pays, 2),
            
            # Validation info
            "extraction_status": extraction_status,
            "sum_of_extracted_items": round(sum_of_items, 2),
            "extraction_discrepancy": round(discrepancy, 2),
            "extraction_discrepancy_pct": round(discrepancy_pct, 1),
            "warning": warning_message
        }
