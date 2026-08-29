# test_connection.py
import psycopg2
import pandas as pd

# Your actual connection string
DATABASE_URL = "postgresql://postgres.zbgkjyhootmctohnngiq:Helb%402025Secure%21@db.zbgkjyhootmctohnngiq.supabase.co:5432/postgres"

print("=" * 60)
print("🔍 TESTING DATABASE CONNECTION")
print("=" * 60)

try:
    print("\n📡 Connecting to Supabase...")
    conn = psycopg2.connect(DATABASE_URL)
    print("✅ Connected!")
    
    cursor = conn.cursor()
    
    # Check tables
    print("\n📋 Checking tables...")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    print(f"   Found {len(tables)} tables:")
    for table in tables:
        print(f"      - {table[0]}")
    
    # Check users
    print("\n👥 Checking users...")
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    print(f"   Users count: {count}")
    
    if count > 0:
        cursor.execute("SELECT username, role FROM users LIMIT 5")
        for user in cursor.fetchall():
            print(f"      👤 {user[0]} ({user[1]})")
    else:
        print("   ⚠️ No users found in the database!")
        
        # Try to insert a test user
        print("\n🔧 Attempting to insert test user...")
        try:
            cursor.execute("""
                INSERT INTO users (username, password, role, full_name, created_at, is_active)
                VALUES ('test_login', 'test123', 'DEPARTMENT', 'Test Login', CURRENT_TIMESTAMP, 1)
                ON CONFLICT (username) DO NOTHING
                RETURNING username
            """)
            result = cursor.fetchone()
            conn.commit()
            if result:
                print(f"   ✅ Test user inserted: {result[0]}")
            else:
                print("   ⚠️ Test user already exists or insert failed")
        except Exception as e:
            print(f"   ❌ Failed to insert test user: {e}")
            conn.rollback()
    
    # Check departments
    print("\n🏢 Checking departments...")
    cursor.execute("SELECT COUNT(*) FROM departments")
    dept_count = cursor.fetchone()[0]
    print(f"   Departments count: {dept_count}")
    
    if dept_count > 0:
        cursor.execute("SELECT name FROM departments LIMIT 5")
        for dept in cursor.fetchall():
            print(f"      📁 {dept[0]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("🔍 TEST COMPLETE")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
