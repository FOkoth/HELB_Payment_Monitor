import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st

DB_PATH = "helb_data.db"

def init_database():
    """Create all tables if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_number TEXT UNIQUE NOT NULL,
            request_type TEXT NOT NULL,
            department TEXT NOT NULL,
            submitted_by TEXT NOT NULL,
            submission_date TEXT NOT NULL,
            amount REAL NOT NULL,
            
            -- Payment specific
            imprest_no TEXT,
            batch_no TEXT,
            supplier_name TEXT,
            invoice_no TEXT,
            
            -- Surrender specific
            surrender_number TEXT,
            previous_imprest_no TEXT,
            
            -- Workflow
            status TEXT DEFAULT 'DRAFT',
            finance_comment TEXT,
            return_reason TEXT,
            finance_check_date TEXT,
            completion_date TEXT,
            
            -- Tracking
            last_updated TEXT
        )
    ''')
    
    # Users table (role-based)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT,
            full_name TEXT
        )
    ''')
    
    # Insert default users
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        default_users = [
            ('dept_user', 'dept123', 'DEPARTMENT', 'Academic Affairs', 'John Otieno'),
            ('finance_officer', 'fin123', 'FINANCE', 'Finance', 'Mary Wanjiku'),
            ('admin', 'admin123', 'ADMIN', 'ICT', 'Admin User'),
        ]
        cursor.executemany(
            "INSERT INTO users (username, password, role, department, full_name) VALUES (?, ?, ?, ?, ?)",
            default_users
        )
    
    # SLA Config table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sla_config (
            request_type TEXT PRIMARY KEY,
            sla_days INTEGER NOT NULL
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM sla_config")
    if cursor.fetchone()[0] == 0:
        sla_defaults = [
            ('Imprest', 5),
            ('Supplier', 7),
            ('Student Payment', 3),
            ('Surrender', 4),
        ]
        cursor.executemany(
            "INSERT INTO sla_config (request_type, sla_days) VALUES (?, ?)",
            sla_defaults
        )
    
    conn.commit()
    conn.close()

def get_requests(filters=None):
    """Fetch requests with optional filters"""
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM requests ORDER BY submission_date DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def save_request(data):
    """Save new request"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Generate request number
    cursor.execute("SELECT COUNT(*) FROM requests")
    count = cursor.fetchone()[0] + 1
    request_number = f"HELB-{datetime.now().strftime('%Y%m')}-{count:04d}"
    
    data['request_number'] = request_number
    data['submission_date'] = datetime.now().isoformat()
    data['last_updated'] = datetime.now().isoformat()
    
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data])
    
    cursor.execute(f"INSERT INTO requests ({columns}) VALUES ({placeholders})", list(data.values()))
    conn.commit()
    conn.close()
    return request_number

def update_request_status(request_id, status, finance_comment=None, return_reason=None):
    """Update workflow status"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updates = ["status = ?", "last_updated = ?"]
    params = [status, datetime.now().isoformat()]
    
    if status == 'FINANCE_CHECKING':
        updates.append("finance_check_date = ?")
        params.append(datetime.now().isoformat())
    elif status == 'COMPLETED':
        updates.append("completion_date = ?")
        params.append(datetime.now().isoformat())
    elif status == 'RETURNED' and return_reason:
        updates.append("return_reason = ?")
        params.append(return_reason)
    
    if finance_comment:
        updates.append("finance_comment = ?")
        params.append(finance_comment)
    
    params.append(request_id)
    cursor.execute(f"UPDATE requests SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()

def authenticate_user(username, password):
    """Verify login credentials"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, role, department, full_name FROM users WHERE username = ? AND password = ?",
        (username, password)
    )
    user = cursor.fetchone()
    conn.close()
    return user if user else None
