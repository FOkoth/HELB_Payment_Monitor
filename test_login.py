# test_login.py
from database import authenticate_user, get_all_users

print("=" * 50)
print("Testing Database Connection")
print("=" * 50)

# Test 1: Get all users
try:
    users = get_all_users()
    print(f"✅ Connected to database. Found {len(users)} users.")
    print("Users:")
    for idx, row in users.iterrows():
        print(f"  - {row['username']} ({row['role']})")
except Exception as e:
    print(f"❌ Error getting users: {e}")

print("\n" + "=" * 50)
print("Testing Authentication")
print("=" * 50)

# Test 2: Try to authenticate admin
try:
    user = authenticate_user('admin', 'admin123')
    if user:
        print("✅ Authentication successful!")
        print(f"  Username: {user[0]}")
        print(f"  Role: {user[1]}")
        print(f"  Department: {user[2]}")
        print(f"  Full Name: {user[3]}")
    else:
        print("❌ Authentication failed - invalid credentials")
except Exception as e:
    print(f"❌ Authentication error: {e}")

print("\n" + "=" * 50)
print("Test 3: Try other credentials")
print("=" * 50)

# Test 3: Try other users
test_users = [
    ('finance_receiver', 'receiver123'),
    ('finance_processor', 'processor123'),
    ('finance_admin', 'finadmin123'),
]

for username, password in test_users:
    try:
        user = authenticate_user(username, password)
        if user:
            print(f"✅ {username} - Authentication successful!")
        else:
            print(f"❌ {username} - Authentication failed")
    except Exception as e:
        print(f"❌ {username} - Error: {e}")
