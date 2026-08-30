# debug_connection.py
import psycopg2
import os

# YOUR DATABASE URL - COPY FROM database.py
DATABASE_URL = "postgresql://postgres:Helb%402025Secure%21@db.zbgkjyhootmctohnngiq.supabase.co:5432/postgres"

print("=" * 70)
print("🔍 DATABASE DEBUGGING TOOL")
print("=" * 70)

print("\n📡 Testing connection...")

try:
    # Test connection
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    print("✅ Connection successful!")

    # Check if users table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'users'
        )
    """)
    table_exists = cursor.fetchone()[0]
    print(f"📋 Users table exists: {table_exists}")

    if table_exists:
        # Count users
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        print(f"👥 Total users: {count}")
        
        if count > 0:
            # Show users
            cursor.execute("SELECT username, password, role FROM users")
            print("\n📋 Users in database:")
            for user in cursor.fetchall():
                print(f"   👤 {user[0]} | Password: {user[1]} | Role: {user[2]}")
            
            # Check admin specifically
            cursor.execute("SELECT * FROM users WHERE username = 'admin'")
            admin = cursor.fetchone()
            if admin:
                print("\n✅ Admin found!")
                print(f"   {admin}")
            else:
                print("\n❌ Admin NOT found!")
        else:
            print("❌ No users found!")
    else:
        print("❌ Users table does not exist!")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n💡 Possible issues:")
    print("   1. DATABASE_URL is wrong")
    print("   2. Supabase is paused (wake it up in dashboard)")
    print("   3. Password is incorrect")
    print("   4. Network issue (VPN/firewall blocking)")
    print("   5. SSL required - try adding sslmode=require")

print("\n" + "=" * 70)
