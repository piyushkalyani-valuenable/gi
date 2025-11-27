"""
Price lookup service - Searches ABHA DB, Internal DB, then falls back to Gemini
Using SQLAlchemy
"""
import json
import re
from typing import Dict, Any, Optional
from sqlalchemy import func
from database.connection import Database
from database.models import InternalDatabase, AbhaDatabase
from services.gemini_service import GeminiService


class PriceLookupService:
    """
    Handles price lookup hierarchy:
    1. ABHA Database (external reference)
    2. Internal Database (our stored prices)
    3. Gemini AI (web search fallback)
    """

    def __init__(self):
        self.gemini = GeminiService()

    def lookup_price(
        self, procedure_name: str, hospital_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Look up price for a procedure using the hierarchy:
        ABHA DB -> Internal DB -> Gemini
        """
        if not procedure_name or procedure_name.upper() in ("N/A", "NONE", ""):
            return {
                "status": "error",
                "message": "No valid procedure name provided",
                "price": None,
                "source": None,
            }

        # Step 1: Try ABHA Database
        abha_result = self._lookup_abha(procedure_name)
        if abha_result.get("price") is not None:
            return abha_result

        # Step 2: Try Internal Database
        internal_result = self._lookup_internal(procedure_name, hospital_name)
        if internal_result.get("price") is not None:
            return internal_result

        # Step 3: Fall back to Gemini AI
        gemini_result = self._lookup_gemini(procedure_name)
        return gemini_result

    def _lookup_abha(self, procedure_name: str) -> Dict[str, Any]:
        """Search ABHA database for procedure price"""
        try:
            with Database.get_session() as db:
                result = (
                    db.query(AbhaDatabase)
                    .filter(
                        func.lower(func.trim(AbhaDatabase.package_name))
                        == func.lower(procedure_name.strip())
                    )
                    .first()
                )

                if result and result.total_package_price:
                    return {
                        "status": "found",
                        "message": "Price found in ABHA database",
                        "price": float(result.total_package_price),
                        "source": "ABHA",
                        "procedure_name": result.package_name or procedure_name,
                    }

            return {
                "status": "not_found",
                "message": f"No match in ABHA database for '{procedure_name}'",
                "price": None,
                "source": None,
            }

        except Exception as e:
            print(f"ABHA lookup error: {e}")
            return {
                "status": "error",
                "message": f"ABHA database error: {type(e).__name__}",
                "price": None,
                "source": None,
            }

    def _lookup_internal(
        self, procedure_name: str, hospital_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search internal database for procedure price"""
        try:
            with Database.get_session() as db:
                query = db.query(InternalDatabase).filter(
                    func.lower(func.trim(InternalDatabase.procedure_name))
                    == func.lower(procedure_name.strip())
                )

                if hospital_name:
                    query = query.filter(
                        func.lower(func.trim(InternalDatabase.hospital_name))
                        == func.lower(hospital_name.strip())
                    )

                result = query.order_by(InternalDatabase.id.desc()).first()

                if result and result.price:
                    return {
                        "status": "found",
                        "message": "Price found in internal database",
                        "price": float(result.price),
                        "source": result.source or "Internal",
                        "procedure_name": result.procedure_name,
                        "hospital_name": result.hospital_name,
                    }

            return {
                "status": "not_found",
                "message": f"No match in internal database for '{procedure_name}'",
                "price": None,
                "source": None,
            }

        except Exception as e:
            print(f"Internal DB lookup error: {e}")
            return {
                "status": "error",
                "message": f"Internal database error: {type(e).__name__}",
                "price": None,
                "source": None,
            }

    def _lookup_gemini(self, procedure_name: str) -> Dict[str, Any]:
        """Use Gemini AI to search for procedure price"""
        prompt = f"""Find the current market price for the medical procedure '{procedure_name}' in India.

Return ONLY a JSON object with this structure:
{{
    "price": <estimated price in INR as a number>,
    "price_range_low": <lower estimate if available, null otherwise>,
    "price_range_high": <upper estimate if available, null otherwise>,
    "currency": "INR",
    "notes": "<any relevant notes about the price>"
}}

If you cannot find a reliable price, return:
{{
    "price": null,
    "notes": "Price not found"
}}

Return ONLY the JSON, no explanations."""

        try:
            response = self.gemini.chat(prompt)

            # Clean and parse response
            cleaned = re.sub(r"^```json\s*", "", response.strip())
            cleaned = re.sub(r"^```\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

            data = json.loads(cleaned)

            if data.get("price"):
                return {
                    "status": "found",
                    "message": "Price found via Gemini AI search",
                    "price": float(data["price"]),
                    "price_range_low": data.get("price_range_low"),
                    "price_range_high": data.get("price_range_high"),
                    "source": "Gemini",
                    "notes": data.get("notes"),
                }

            return {
                "status": "not_found",
                "message": f"Gemini could not find price for '{procedure_name}'",
                "price": None,
                "source": None,
                "notes": data.get("notes"),
            }

        except Exception as e:
            print(f"Gemini lookup error: {e}")
            return {
                "status": "error",
                "message": f"Gemini search error: {type(e).__name__}",
                "price": None,
                "source": None,
            }

    def save_to_internal_db(
        self,
        procedure_name: str,
        price: float,
        source: str,
        hospital_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save a price lookup result to internal database for future use"""
        try:
            with Database.get_session() as db:
                record = InternalDatabase(
                    procedure_name=procedure_name,
                    price=price,
                    source=source,
                    hospital_name=hospital_name,
                )
                db.add(record)

            return {"status": "success", "message": "Price saved to internal database"}

        except Exception as e:
            print(f"Save to internal DB error: {e}")
            return {"status": "error", "message": f"Failed to save: {type(e).__name__}"}

    # TODO: In future, process bills to extract procedure prices and save to internal_database
    # This will help build up our price database over time
    # def extract_prices_from_bill(self, bill_extraction: Dict[str, Any]) -> None:
    #     """Extract procedure prices from processed bills and save to internal DB"""
    #     pass
