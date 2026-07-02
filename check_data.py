"""
Check database status and data
"""

import os
from database import get_all_users, get_requests, get_database_health

def check_data():
    print("📊 DATABASE STATUS CHECK")
    print("=" * 50)
    
    health = get_database_health()
    print(f"Database Size: {health['db_size_mb']:.2f} MB")
    print(f"Total Requests: {health['total_requests']:,}")
    print(f"Total Users: {health['total_users']:,}")
    print(f"Status: {health['status']}")
    
    if health['total_users'] > 0:
        users = get_all_users()
        print(f"\n📋 Users ({len(users)}):")
        for _, user in users.iterrows():
            print(f"  - {user['username']} ({user['role']}) - {user['department']}")
    
    if health['total_requests'] > 0:
        requests = get_requests()
        print(f"\n📋 Latest Requests (last 5):")
        for _, req in requests.head(5).iterrows():
            print(f"  - {req['request_number']} | {req['request_type']} | {req['status']} | KES {req['amount']:,.2f}")

if __name__ == "__main__":
    check_data()
