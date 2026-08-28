# test_connection.py
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

print("Testing connection to Supabase...")
print(f"Connection string: {DATABASE_URL[:30]}...")  # Only show first 30 chars for security

try:
    conn = psycopg2.connect(DATABASE_URL)
    print("✅ SUCCESS! Connected to Supabase!")
    
    # Test query
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"📊 PostgreSQL Version: {version[0]}")
    
    # Close connection
    cursor.close()
    conn.close()
    print("✅ Connection test complete!")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\nPlease check:")
    print("1. Your password is correct")
    print("2. Special characters in password are URL-encoded")
    print("3. Your .env file is in the same folder")
