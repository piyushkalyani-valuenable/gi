"""
Chat routes - Handles the claim assessment flow
"""
import json
from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from typing import Optional

from services.gemini_service import GeminiService
from services.storage_service import StorageService
from services.session_service import SessionService
from services.extraction_service import ExtractionService
from services.calculation_service import CalculationService
from services.price_lookup_service import PriceLookupService
from models.schemas import ChatResponse, ChatOption, SessionStatus
from config.constants import MAX_FILE_SIZE

router = APIRouter(prefix="/api", tags=["chat"])

# Initialize services
gemini_service = GeminiService()
extraction_service = ExtractionService()
calculation_service = CalculationService()
price_lookup_service = PriceLookupService()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    user_input: str = Form(default=""),
    session_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """
    Main chat endpoint - handles the claim assessment flow

    Flow:
    1. awaiting_policy: Upload policy bond
    2. awaiting_document_choice: Choose bill/prescription/both
    3. awaiting_bill: Upload bill -> calculate claim
    4. awaiting_prescription: Upload prescription -> price lookup
    5. awaiting_both_bill: Upload bill (when both selected)
    6. awaiting_both_prescription: Upload prescription (when both selected)
    7. completed: Show results
    """
    try:
        # Get or create session
        if session_id:
            session = SessionService.get_session(session_id)
            if not session:
                session_id = SessionService.create_session()
                session = SessionService.get_session(session_id)
        else:
            session_id = SessionService.create_session()
            session = SessionService.get_session(session_id)

        status = session["status"]

        # Route to appropriate handler
        handlers = {
            "awaiting_policy": _handle_awaiting_policy,
            "awaiting_document_choice": _handle_document_choice,
            "awaiting_bill": _handle_awaiting_bill,
            "awaiting_prescription": _handle_awaiting_prescription,
            "awaiting_both_bill": _handle_awaiting_both_bill,
            "awaiting_both_prescription": _handle_awaiting_both_prescription,
            "completed": _handle_completed,
        }

        handler = handlers.get(status)
        if not handler:
            raise HTTPException(status_code=500, detail=f"Unknown session status: {status}")

        return await handler(session_id, session, file, user_input)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _handle_awaiting_policy(
    session_id: str, session: dict, file: Optional[UploadFile], user_input: str
) -> ChatResponse:
    """Step 1: Upload policy bond"""
    if not file or not file.filename:
        return ChatResponse(
            reply="Welcome! Please upload your insurance policy bond document to begin.",
            session_id=session_id,
            status=SessionStatus.AWAITING_POLICY,
            input_type="file",
        )

    file_data = await file.read()
    filename = file.filename

    # Validate file size
    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024):.0f}MB."
        )

    if not _is_valid_file(filename):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload PDF or image.")

    StorageService.store_file(session_id, "policy_bond", file_data, filename)
    SessionService.update_status(session_id, "awaiting_document_choice")

    return ChatResponse(
        reply=f"Policy bond '{filename}' received. What would you like to process?",
        session_id=session_id,
        status=SessionStatus.AWAITING_DOCUMENT_CHOICE,
        input_type="options",
        options=[
            ChatOption(value="bill", label="🧾 Hospital Bill (Claim Calculation)"),
            ChatOption(value="prescription", label="💊 Prescription (Price Lookup)"),
            ChatOption(value="both", label="📋 Both Documents"),
        ],
    )


async def _handle_document_choice(
    session_id: str, session: dict, file: Optional[UploadFile], user_input: str
) -> ChatResponse:
    """Step 2: Choose document type"""
    choice = user_input.strip().lower()

    if choice == "bill":
        SessionService.set_document_choice(session_id, "bill")
        SessionService.update_status(session_id, "awaiting_bill")
        return ChatResponse(
            reply="Please upload your hospital bill for claim calculation.",
            session_id=session_id,
            status=SessionStatus.AWAITING_BILL,
            input_type="file",
        )

    elif choice == "prescription":
        SessionService.set_document_choice(session_id, "prescription")
        SessionService.update_status(session_id, "awaiting_prescription")
        return ChatResponse(
            reply="Please upload your prescription for price lookup.",
            session_id=session_id,
            status=SessionStatus.AWAITING_PRESCRIPTION,
            input_type="file",
        )

    elif choice == "both":
        SessionService.set_document_choice(session_id, "both")
        SessionService.update_status(session_id, "awaiting_both_bill")
        return ChatResponse(
            reply="Please upload your hospital bill first (for claim calculation).",
            session_id=session_id,
            status=SessionStatus.AWAITING_BOTH_BILL,
            input_type="file",
        )

    else:
        return ChatResponse(
            reply="Please select an option:",
            session_id=session_id,
            status=SessionStatus.AWAITING_DOCUMENT_CHOICE,
            input_type="options",
            options=[
                ChatOption(value="bill", label="🧾 Hospital Bill"),
                ChatOption(value="prescription", label="💊 Prescription"),
                ChatOption(value="both", label="📋 Both"),
            ],
        )


async def _handle_awaiting_bill(
    session_id: str, session: dict, file: Optional[UploadFile], user_input: str
) -> ChatResponse:
    """Process bill only - full claim calculation"""
    if not file or not file.filename:
        return ChatResponse(
            reply="Please upload the hospital bill document.",
            session_id=session_id,
            status=SessionStatus.AWAITING_BILL,
        )

    return await _process_bill_and_calculate(session_id, file)


async def _handle_awaiting_prescription(
    session_id: str, session: dict, file: Optional[UploadFile], user_input: str
) -> ChatResponse:
    """Process prescription only - price lookup"""
    if not file or not file.filename:
        return ChatResponse(
            reply="Please upload the prescription document.",
            session_id=session_id,
            status=SessionStatus.AWAITING_PRESCRIPTION,
        )

    return await _process_prescription(session_id, file, is_final=True)


async def _handle_awaiting_both_bill(
    session_id: str, session: dict, file: Optional[UploadFile], user_input: str
) -> ChatResponse:
    """Process bill when both selected"""
    if not file or not file.filename:
        return ChatResponse(
            reply="Please upload the hospital bill document.",
            session_id=session_id,
            status=SessionStatus.AWAITING_BOTH_BILL,
        )

    # Process bill and calculate
    result = await _process_bill_and_calculate(session_id, file, is_final=False)

    # Update status to await prescription
    SessionService.update_status(session_id, "awaiting_both_prescription")

    return ChatResponse(
        reply=result.reply + "\n\n---\nNow please upload your prescription for price lookup.",
        session_id=session_id,
        status=SessionStatus.AWAITING_BOTH_PRESCRIPTION,
    )


async def _handle_awaiting_both_prescription(
    session_id: str, session: dict, file: Optional[UploadFile], user_input: str
) -> ChatResponse:
    """Process prescription when both selected (final step)"""
    if not file or not file.filename:
        return ChatResponse(
            reply="Please upload the prescription document.",
            session_id=session_id,
            status=SessionStatus.AWAITING_BOTH_PRESCRIPTION,
        )

    return await _process_prescription(session_id, file, is_final=True)


async def _handle_completed(
    session_id: str, session: dict, file: Optional[UploadFile], user_input: str
) -> ChatResponse:
    """Assessment completed"""
    if user_input.strip().lower() in ["reset", "new", "start over"]:
        new_session_id = SessionService.create_session()
        return ChatResponse(
            reply="Starting new assessment. Please upload your insurance policy bond.",
            session_id=new_session_id,
            status=SessionStatus.AWAITING_POLICY,
            input_type="file",
        )

    calculation_result = SessionService.get_extraction(session_id, "calculation_result")
    result_json = json.dumps(calculation_result, indent=2) if calculation_result else "No results found."

    return ChatResponse(
        reply=f"Assessment complete.\n\n{result_json}",
        session_id=session_id,
        status=SessionStatus.COMPLETED,
        input_type="options",
        options=[
            ChatOption(value="reset", label="🔄 Start New Assessment"),
        ],
    )


# --- Helper Functions ---


async def _process_bill_and_calculate(
    session_id: str, file: UploadFile, is_final: bool = True
) -> ChatResponse:
    """Process bill file and run claim calculation"""
    file_data = await file.read()
    filename = file.filename

    # Validate file size
    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024):.0f}MB."
        )

    if not _is_valid_file(filename):
        raise HTTPException(status_code=400, detail="Invalid file type.")

    StorageService.store_file(session_id, "bill", file_data, filename)

    # Extract bill
    print(f"[{session_id}] Extracting bill...")
    bill_extraction = extraction_service.extract_bill(file_data, filename)
    SessionService.save_extraction(session_id, "bill_extraction", bill_extraction)

    # Get keywords
    bill_keywords = [item["item_name"] for item in bill_extraction.get("line_items", [])]
    print(f"[{session_id}] Keywords: {bill_keywords}")

    # Get policy bond
    policy_file = StorageService.get_file(session_id, "policy_bond")
    if not policy_file:
        raise HTTPException(status_code=500, detail="Policy bond not found")

    policy_data, policy_filename = policy_file

    # Extract bond limits
    print(f"[{session_id}] Extracting bond limits...")
    bond_extraction = extraction_service.extract_bond_for_keywords(
        policy_data, policy_filename, bill_keywords
    )
    SessionService.save_extraction(session_id, "bond_extraction", bond_extraction)

    # Calculate
    print(f"[{session_id}] Calculating claim...")
    calculation_result = calculation_service.calculate_claim(bill_extraction, bond_extraction)
    SessionService.save_extraction(session_id, "calculation_result", calculation_result)

    if is_final:
        SessionService.update_status(session_id, "completed")

    result_json = json.dumps(calculation_result, indent=2)

    return ChatResponse(
        reply=f"Claim Calculation Result:\n\n{result_json}",
        session_id=session_id,
        status=SessionStatus.COMPLETED if is_final else SessionStatus.AWAITING_BOTH_PRESCRIPTION,
    )


async def _process_prescription(session_id: str, file: UploadFile, is_final: bool = True) -> ChatResponse:
    """Process prescription file and do price lookup"""
    file_data = await file.read()
    filename = file.filename

    # Validate file size
    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024):.0f}MB."
        )

    if not _is_valid_file(filename):
        raise HTTPException(status_code=400, detail="Invalid file type.")

    StorageService.store_file(session_id, "prescription", file_data, filename)

    # Extract prescription
    print(f"[{session_id}] Extracting prescription...")
    prescription_extraction = extraction_service.extract_prescription(file_data, filename)
    SessionService.save_extraction(session_id, "prescription_extraction", prescription_extraction)

    procedure_name = prescription_extraction.get("procedure_name")
    hospital_name = prescription_extraction.get("hospital_name")

    # Price lookup
    print(f"[{session_id}] Looking up price for: {procedure_name}")
    price_result = price_lookup_service.lookup_price(procedure_name, hospital_name)

    # Save to internal DB if found via Gemini (for future lookups)
    if price_result.get("source") == "Gemini" and price_result.get("price"):
        price_lookup_service.save_to_internal_db(
            procedure_name=procedure_name,
            price=price_result["price"],
            source="Gemini",
            hospital_name=hospital_name,
        )

    if is_final:
        SessionService.update_status(session_id, "completed")

    result = {
        "prescription_data": prescription_extraction,
        "price_lookup": price_result,
    }
    result_json = json.dumps(result, indent=2)

    return ChatResponse(
        reply=f"Prescription Analysis & Price Lookup:\n\n{result_json}",
        session_id=session_id,
        status=SessionStatus.COMPLETED,
    )


def _is_valid_file(filename: str) -> bool:
    """Check if file type is supported"""
    return filename.lower().endswith((".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif"))
