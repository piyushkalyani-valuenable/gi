# GI Claim Assistance - Server

Refactored FastAPI backend for health insurance claim assessment.

## 🏗️ Project Structure

```
server/
├── config/              # Configuration and settings
│   ├── settings.py      # Environment-based settings
│   ├── constants.py     # Application constants
│   ├── prompts.py       # AI prompt templates
│   └── aws_config.py    # AWS Secrets Manager config
├── database/            # Database connection management
│   └── connection.py    # Connection pool
├── models/              # Pydantic models
│   └── schemas.py       # Request/response schemas
├── routes/              # API routes (controllers)
│   ├── chat.py          # Main chat/extraction endpoint
│   └── health.py        # Health check endpoints
├── services/            # Business logic layer
│   ├── gemini_service.py           # Gemini AI integration
│   ├── database_service.py         # Database operations
│   ├── session_service.py          # Session management
│   ├── data_extraction_service.py  # Field extraction
│   ├── calculation_service.py      # Calculation helpers
│   ├── policy_factors.py           # Policy factor calculations
│   └── claim_calculation_service.py # Main claim calculation
├── utils/               # Utility functions
│   ├── parsers.py       # Data parsing utilities
│   ├── fuzzy_match.py   # Fuzzy matching logic
│   ├── formatters.py    # Output formatting
│   └── keyword_loader.py # Keyword file loader
├── keywords/            # Keyword files for extraction
│   ├── prescription.txt
│   ├── discharge.txt
│   └── bond.txt
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variables template
```

## 🚀 Setup

### 1. Create Virtual Environment

```bash
cd server
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
AWS_REGION=ap-south-1
AWS_SECRET_NAME=DB_SECRET
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 4. AWS Credentials

Ensure AWS credentials are configured:

**Option 1: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

**Option 2: AWS CLI Config**
```bash
aws configure
```

### 5. Run Server

```bash
# Development (with auto-reload)
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📡 API Endpoints

### Health Check
- `GET /api/health` - Service health status
- `GET /api/db-check` - Database connectivity check

### Chat/Extraction
- `POST /api/chat` - Main endpoint for document extraction and claim calculation

**Request:**
```
Content-Type: multipart/form-data

session_id: string (required)
user_input: string (optional)
file: file (optional)
```

**Response:**
```json
{
  "reply": "string",
  "extraction_count": 1,
  "calculation_result": {
    "total_billed": 100000.0,
    "insurer_payable": 80000.0,
    "patient_payable": 20000.0,
    ...
  }
}
```

## 🔄 Workflow

1. **Turn 1 - Prescription**: Upload prescription → Extract procedure → Lookup price
2. **Turn 2 - Discharge Summary**: Upload discharge → Extract billing details
3. **Turn 3 - Policy Bond**: Upload policy → Extract coverage → Calculate claim

## 🧪 Testing

```bash
# Test database connection
python -c "from database import DatabaseConnection; print('DB OK' if DatabaseConnection.get_pool() else 'DB FAIL')"

# Test API
curl http://localhost:8000/api/health
```

## 📝 Key Improvements

- ✅ **No global state** - Session-based architecture
- ✅ **Proper separation of concerns** - Routes, services, models
- ✅ **Connection pooling** - Efficient database usage
- ✅ **Type safety** - Pydantic models throughout
- ✅ **Environment-based config** - No hardcoded credentials
- ✅ **Clean code structure** - Easy to maintain and extend

## 🔐 Security Notes

- Never commit `.env` file
- Use AWS Secrets Manager for sensitive data
- Rotate API keys regularly
- Use HTTPS in production
