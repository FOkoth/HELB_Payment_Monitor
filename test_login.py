# test_login.py
from database import authenticate_user, get_all_users

print("=" * 60)
print("TESTING DATABASE CONNECTION AND LOGIN")
print("=" * 60)

# Test 1: Get all users
print("\n📋 Test 1: Get all users from database")
try:
    users = get_all_users()
    print(f"✅ Found {len(users)} users in database")
    print("\nUsers list:")
    for idx, row in users.iterrows():
        print(f"  - {row['username']} (Role: {row['role']})")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Try admin login
print("\n" + "=" * 60)
print("🔐 Test 2: Try admin login")
print("=" * 60)

try:
    user = authenticate_user('admin', 'admin123')
    if user:
        print("✅ SUCCESS! admin logged in successfully!")
        print(f"  Username: {user[0]}")
        print(f"  Role: {user[1]}")
        print(f"  Department: {user[2]}")
        print(f"  Full Name: {user[3]}")
    else:
        print("❌ FAILED: admin login failed - invalid credentials")
        print("This means the username/password in the database don't match what you're typing.")
except Exception as e:
    print(f"❌ ERROR: {e}")
