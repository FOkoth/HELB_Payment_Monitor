import os
import sqlite3

# Delete the existing database
db_path = "helb_data.db"
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✅ Deleted old database: {db_path}")
else:
    print(f"ℹ️ No existing database found at {db_path}")

print("✅ Database reset complete. Restart your app to recreate the database.")
