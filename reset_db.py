import os
import sqlite3

DB_PATH = "helb_data.db"

# Delete the existing database
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("✅ Old database deleted successfully!")
else:
    print("ℹ️ No existing database found.")

print("✅ Database reset complete. The app will create a fresh database on next run.")
