"""
Test database connection
"""
from database.connection import DatabaseConnection

print("Testing database connection...")

try:
    with DatabaseConnection.get_cursor() as cursor:
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()
        print(f"✅ Connected to database: {db_name}")
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"✅ Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {list(table.values())[0]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
