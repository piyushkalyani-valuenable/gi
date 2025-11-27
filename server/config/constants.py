"""
Application constants and configuration values
"""

# Gemini AI Configuration
GEMINI_MODEL = "gemini-2.5-pro"
GEMINI_FILE_POLL_INTERVAL = 3  # seconds
GEMINI_FILE_MAX_WAIT_TIME = 60  # seconds
GEMINI_REQUEST_TIMEOUT = 180  # 3 minutes timeout for Gemini API calls

# File Upload Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max file size

# Extraction Turn Configuration
TURN_PRESCRIPTION = 1
TURN_DISCHARGE = 2
TURN_BOND = 3

# Keyword Files
KEYWORD_FILES = {
    TURN_PRESCRIPTION: "keywords/prescription.txt",
    TURN_DISCHARGE: "keywords/discharge.txt",
    TURN_BOND: "keywords/bond.txt",
}

# Database Tables
TABLE_ABHA = "abha_database"
TABLE_INTERNAL = "internal_database"

# Non-Payable Ratios (defaults)
CONSUMABLES_NONPAYABLE_RATIO = 1.0
PHARMACY_NONPAYABLE_RATIO = 1.0

# Fuzzy Matching
FUZZY_MATCH_CUTOFF = 0.7

# Supported MIME Types
SUPPORTED_MIME_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "application/pdf",
]
