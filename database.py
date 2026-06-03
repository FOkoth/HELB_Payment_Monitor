import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st

DB_PATH = "helb_data.db"

def init_database():
    """Create all tables if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Departments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            can_submit_imprest INTEGER DEFAULT 1,
            can_submit_petty_cash INTEGER DEFAULT 1,
            can_submit_supplier INTEGER DEFAULT 0,
            can_submit_student_payment INTEGER DEFAULT 0,
            can_submit_surrender INTEGER DEFAULT 1,
            can_submit_refund INTEGER DEFAULT 0,
            requires_product_type INTEGER DEFAULT 0,
            requires_funder INTEGER DEFAULT 0,
            is_finance_dept INTEGER DEFAULT 0
        )
    ''')
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT,
            has_payment_type INTEGER DEFAULT 0,
            has_semester INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Funders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS funders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Financial Years table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_years (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Semesters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS semesters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            department_id INTEGER,
            full_name TEXT,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    ''')
    
    # Requests table with new columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_number TEXT UNIQUE NOT NULL,
            request_type TEXT NOT NULL,
            department_id INTEGER,
            department_name TEXT,
            submitted_by TEXT NOT NULL,
            submission_date TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_description TEXT,
            imprest_no TEXT,
            batch_no TEXT,
            supplier_name TEXT,
            invoice_no TEXT,
            lpo_no TEXT,
            product_type TEXT,
            payment_type TEXT,
            funder_name TEXT,
            financial_year TEXT,
            semester TEXT,
            refund_reason TEXT,
            original_payment_ref TEXT,
            surrender_number TEXT,
            previous_imprest_no TEXT,
            status TEXT DEFAULT 'SUBMITTED',
            finance_comment TEXT,
            return_reason TEXT,
            finance_check_date TEXT,
            completion_date TEXT,
            last_updated TEXT
        )
    ''')
    
    # SLA Config table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sla_config (
            request_type TEXT PRIMARY KEY,
            sla_days INTEGER NOT NULL
        )
    ''')
    
    # Insert default departments (alphabetically)
    cursor.execute("SELECT COUNT(*) FROM departments")
    if cursor.fetchone()[0] == 0:
        default_depts = [
            ('CEO\'s Office', 1, 1, 0, 0, 1, 0, 0, 0, 0),
            ('Corporate Communication', 1, 1, 0, 0, 1, 0, 0, 0, 0),
            ('Debt Management', 0, 0, 0, 0, 0, 1, 0, 0, 0),
            ('External Resource Mobilization', 1, 0, 0, 1, 1, 0, 0, 1, 0),
            ('Field Services', 1, 1, 0, 0, 1, 0, 0, 0, 0),
            ('Finance', 1, 1, 0, 0, 0, 0, 0, 0, 1),
            ('Human Resource', 1, 1, 0, 0, 1, 0, 0, 0, 0),
            ('ICT', 1, 1, 0, 0, 1, 0, 0, 0, 0),
            ('Internal Audit', 0, 0, 0, 0, 0, 0, 0, 0, 0),
            ('Legal Services', 0, 0, 0, 0, 0, 0, 0, 0, 0),
            ('Lending', 1, 0, 0, 1, 1, 0, 1, 0, 0),
            ('Strategy', 1, 1, 0, 0, 1, 0, 0, 0, 0),
            ('Supply Chain Management', 0, 0, 1, 0, 0, 0, 0, 0, 0),
        ]
        for dept in default_depts:
            cursor.execute('''
                INSERT INTO departments (
                    name, can_submit_imprest, can_submit_petty_cash, 
                    can_submit_supplier, can_submit_student_payment, 
                    can_submit_surrender, can_submit_refund, 
                    requires_product_type, requires_funder, is_finance_dept
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', dept)
    
    # Insert default products
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        default_products = [
            ('Undergraduate', 'LOAN', 1, 1, 1),
            ('TVET', 'LOAN', 1, 1, 1),
            ('Jielimishe', 'SCHOLARSHIP', 0, 0, 1),
        ]
        cursor.executemany(
            "INSERT INTO products (name, category, has_payment_type, has_semester, is_active) VALUES (?, ?, ?, ?, ?)",
            default_products
        )
    
    # Insert default funders
    cursor.execute("SELECT COUNT(*) FROM funders")
    if cursor.fetchone()[0] == 0:
        default_funders = [
            ('KMTC',), ('World Bank',), ('AfDB',), ('UNESCO',), 
            ('Mastercard Foundation',), ('KOICA',), ('JICA',), ('USAID',), ('GIZ',)
        ]
        cursor.executemany("INSERT INTO funders (name) VALUES (?)", default_funders)
    
    # Insert financial years
    cursor.execute("SELECT COUNT(*) FROM financial_years")
    if cursor.fetchone()[0] == 0:
        default_years = [
            ('2025/2026', 1),
            ('2026/2027', 1),
        ]
        cursor.executemany("INSERT INTO financial_years (name, is_active) VALUES (?, ?)", default_years)
    
    # Insert semesters
    cursor.execute("SELECT COUNT(*) FROM semesters")
    if cursor.fetchone()[0] == 0:
        default_semesters = [
            ('Semester 1',),
            ('Semester 2',),
        ]
        cursor.executemany("INSERT INTO semesters (name) VALUES (?)", default_semesters)
    
    # Insert SLA defaults
    cursor.execute("SELECT COUNT(*) FROM sla_config")
    if cursor.fetchone()[0] == 0:
        sla_defaults = [
            ('Imprest', 5),
            ('Supplier', 7),
            ('Student Payment', 3),
            ('Surrender', 4),
            ('Petty Cash', 3),
            ('Refund', 10),
        ]
        cursor.executemany(
            "INSERT INTO sla_config (request_type, sla_days) VALUES (?, ?)",
            sla_defaults
        )
    
    conn.commit()
    conn.close()
    
    # Insert default users AFTER departments exist
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get department IDs
    cursor.execute("SELECT id, name FROM departments")
    dept_map = {name: id for id, name in cursor.fetchall()}
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        default_users = [
            ('admin', 'admin123', 'ADMIN', None, 'System Administrator'),
            ('finance_user', 'fin123', 'FINANCE', dept_map.get('Finance'), 'Finance Officer'),
            ('lending_user', 'lend123', 'DEPARTMENT', dept_map.get('Lending'), 'Lending Officer'),
            ('erm_user', 'erm123', 'DEPARTMENT', dept_map.get('External Resource Mobilization'), 'ERM Officer'),
            ('debt_user', 'debt123', 'DEPARTMENT', dept_map.get('Debt Management'), 'Debt Officer'),
            ('scm_user', 'scm123', 'DEPARTMENT', dept_map.get('Supply Chain Management'), 'SCM Officer'),
            ('internal_audit_user', 'audit123', 'DEPARTMENT', dept_map.get('Internal Audit'), 'Audit Officer'),
            ('legal_user', 'legal123', 'DEPARTMENT', dept_map.get('Legal Services'), 'Legal Officer'),
            ('hr_user', 'hr123', 'DEPARTMENT', dept_map.get('Human Resource'), 'HR Officer'),
            ('ict_user', 'ict123', 'DEPARTMENT', dept_map.get('ICT'), 'ICT Officer'),
            ('corpcomm_user', 'corp123', 'DEPARTMENT', dept_map.get('Corporate Communication'), 'Comm Officer'),
            ('strategy_user', 'strat123', 'DEPARTMENT', dept_map.get('Strategy'), 'Strategy Officer'),
            ('ceo_user', 'ceo123', 'DEPARTMENT', dept_map.get('CEO\'s Office'), 'CEO Office'),
            ('field_user', 'field123', 'DEPARTMENT', dept_map.get('Field Services'), 'Field Officer'),
        ]
        cursor.executemany(
            "INSERT INTO users (username, password, role, department_id, full_name) VALUES (?, ?, ?, ?, ?)",
            default_users
        )
    
    conn.commit()
    conn.close()

def get_departments():
    """Get all departments"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT id, name FROM departments ORDER BY name", conn)
    conn.close()
    return df

def get_products():
    """Get all active products"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT name, category, has_payment_type, has_semester FROM products WHERE is_active = 1 ORDER BY name", conn)
    conn.close()
    return df

def add_product(name, category, has_payment_type, has_semester):
    """Add a new product"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO products (name, category, has_payment_type, has_semester, is_active) VALUES (?, ?, ?, ?, 1)",
            (name, category, has_payment_type, has_semester)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_financial_years():
    """Get all active financial years"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT name FROM financial_years WHERE is_active = 1 ORDER BY name DESC", conn)
    conn.close()
    return df['name'].tolist() if not df.empty else []

def get_semesters():
    """Get all semesters"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT name FROM semesters ORDER BY name", conn)
    conn.close()
    return df['name'].tolist() if not df.empty else []

def get_funders():
    """Get all funders"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT name FROM funders ORDER BY name", conn)
    conn.close()
    return df['name'].tolist() if not df.empty else []

def get_user_department(username):
    """Get user's department details"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.* FROM users u
        JOIN departments d ON u.department_id = d.id
        WHERE u.username = ?
    ''', (username,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_all_users():
    """Get all users with department names"""
    conn = sqlite3.connect(DB_PATH)
    query = '''
        SELECT u.username, u.role, d.name as department, u.full_name 
        FROM users u
        LEFT JOIN departments d ON u.department_id = d.id
        ORDER BY u.username
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def create_user(username, password, role, department_id, full_name):
    """Create a new user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, role, department_id, full_name) VALUES (?, ?, ?, ?, ?)",
            (username, password, role, department_id, full_name)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def create_department(name, permissions):
    """Create a new department with permissions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO departments (
                name, can_submit_imprest, can_submit_petty_cash, 
                can_submit_supplier, can_submit_student_payment, 
                can_submit_surrender, can_submit_refund, 
                requires_product_type, requires_funder, is_finance_dept
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, *permissions))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_department_permissions(dept_id):
    """Get department permissions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM departments WHERE id = ?', (dept_id,))
    result = cursor.fetchone()
    conn.close()
    return result

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
    data['submission_date'] = datetime.now().strftime('%Y-%m-%d')
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
    try:
        cursor.execute('''
            SELECT u.username, u.role, d.name as department_name, u.full_name, u.department_id, COALESCE(d.is_finance_dept, 0) as is_finance_dept
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.id
            WHERE u.username = ? AND u.password = ?
        ''', (username, password))
        user = cursor.fetchone()
        conn.close()
        return user if user else None
    except Exception as e:
        conn.close()
        return None
