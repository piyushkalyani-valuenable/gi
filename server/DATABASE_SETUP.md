# Database Configuration

The application now supports environment-based database configuration.

## 🔄 How It Works

The database connection automatically switches based on the `ENVIRONMENT` variable in `.env`:

- **`ENVIRONMENT=development`** → Connects to **Local MySQL**
- **`ENVIRONMENT=production`** → Connects to **AWS RDS** (via Secrets Manager)

## 📝 Configuration

### Development (Local MySQL)

Edit `.env`:
```env
ENVIRONMENT=development

LOCAL_DB_HOST=localhost
LOCAL_DB_PORT=3306
LOCAL_DB_USER=root
LOCAL_DB_PASSWORD=piyupiyu
LOCAL_DB_NAME=mydb
```

### Production (AWS RDS)

Edit `.env`:
```env
ENVIRONMENT=production

AWS_REGION=ap-south-1
AWS_SECRET_NAME=DB_SECRET
```

Make sure AWS credentials are configured:
```bash
aws configure
```

## ✅ Testing Connection

Run the test script:
```bash
python test_db.py
```

Expected output:
```
💻 Using DEVELOPMENT database (Local MySQL)
✅ Database connection pool created: localhost/mydb
✅ Connected to database: {'DATABASE()': 'mydb'}
✅ Found 8 tables:
   - abha_database
   - claim_sequence
   - discharge_summary_extracted_data
   - extraction_logs
   - internal_database
   - policy_bond_extracted_data
   - prescriptions_database
   - vitals_database
```

## 📊 Current Tables

Your local database (`mydb`) has these tables:
- `abha_database` - ABHA procedure prices
- `internal_database` - Internal procedure prices
- `prescriptions_database` - Prescription data
- `discharge_summary_extracted_data` - Discharge summaries
- `policy_bond_extracted_data` - Policy bond data
- `vitals_database` - Patient vitals
- `extraction_logs` - Extraction history
- `claim_sequence` - Claim sequences

## 🔧 Usage in Code

The connection is automatic. Just use:

```python
from database.connection import DatabaseConnection

# Get cursor
with DatabaseConnection.get_cursor() as cursor:
    cursor.execute("SELECT * FROM abha_database LIMIT 5")
    results = cursor.fetchall()

# Get connection
with DatabaseConnection.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM internal_database")
```

## 🚀 Switching Environments

### To Development:
```env
ENVIRONMENT=development
```

### To Production:
```env
ENVIRONMENT=production
```

Restart the server after changing the environment.

## 🔐 Security Notes

- Never commit `.env` file
- Keep production credentials in AWS Secrets Manager
- Use different API keys for dev/prod
- Local database is for development only
