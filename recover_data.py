"""
Emergency Data Recovery Script
Run this if your data gets wiped
"""

import os
import sys
from database import get_backup_list, restore_backup, verify_database_integrity

def emergency_recovery():
    print("🚨 EMERGENCY DATA RECOVERY")
    print("=" * 50)
    
    # List all backups
    backups = get_backup_list()
    
    if not backups:
        print("❌ No backups found!")
        return False
    
    print(f"\n📋 Found {len(backups)} backups:")
    for i, b in enumerate(backups):
        print(f"{i+1}. {b['filename']} - {b['date']} - {b['size']} bytes")
    
    print("\n" + "=" * 50)
    print("Recovering from latest backup...")
    
    # Try to recover
    if restore_backup(backups[0]['filename']):
        print("✅ Database restored from backup!")
        
        # Verify integrity
        if verify_database_integrity():
            print("✅ Database integrity verified!")
            return True
        else:
            print("⚠️ Database integrity check failed after recovery!")
            return False
    else:
        print("❌ Recovery failed!")
        return False

if __name__ == "__main__":
    emergency_recovery()
