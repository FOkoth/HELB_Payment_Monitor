import sqlite3
import pandas as pd
from datetime import datetime, date
import streamlit as st

DB_PATH = "helb_data.db"

def migrate_database():
    """Add missing columns to existing tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get existing columns in requests table
    cursor.execute("PRAGMA table_info(requests)")
    existing_columns = [column[1] for column in cursor.fetchall()]
    
    # Define all columns that should exist
    required_columns = {
        'payment_description': 'TEXT',
        'financial_year': 'TEXT',
        'batch_no': 'TEXT',
        'product_type': 'TEXT',
        'semester': 'TEXT',
        'payment_type': 'TEXT',
        'imprest_no': 'TEXT',
        'supplier_name': 'TEXT',
        'invoice_no': 'TEXT',
        'lpo_no': 'TEXT',
        'salary_month': 'TEXT',
        'salary_year': 'INTEGER',
        'customer_name': 'TEXT',
        'customer_id': 'TEXT',
        'surrender_number': 'TEXT',
        'staff_name': 'TEXT',
        'funder_name': 'TEXT',
        'refund_reason': 'TEXT',
        'original_payment_ref': 'TEXT',
        'previous_imprest_no': 'TEXT',
        'date_received': 'TEXT',
        'date_returned': 'TEXT',
        'payment_date': 'TEXT',
        'payment_reference': 'TEXT',
        'completed_by': 'TEXT',
        'completion_notes': 'TEXT'
    }
    
    # Add missing columns
    for col_name, col_type in required_columns.items():
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE requests ADD COLUMN {col_name} {col_type}")
                print(f"Added column: {col_name}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
    
    # Check and add full_name column to users table
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [column[1] for column in cursor.fetchall()]
    if 'full_name' not in user_columns:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
            print("Added column: full_name to users")
        except Exception as e:
            print(f"Error adding full_name: {e}")
    
    conn.commit()
    conn.close()
    print("Database migration completed!")


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
    
    # Requests table
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
            financial_year TEXT,
            batch_no TEXT,
            product_type TEXT,
            semester TEXT,
            payment_type TEXT,
            imprest_no TEXT,
            supplier_name TEXT,
            invoice_no TEXT,
            lpo_no TEXT,
            salary_month TEXT,
            salary_year INTEGER,
            customer_name TEXT,
            customer_id TEXT,
            surrender_number TEXT,
            staff_name TEXT,
            funder_name TEXT,
            refund_reason TEXT,
            original_payment_ref TEXT,
            previous_imprest_no TEXT,
            status TEXT DEFAULT 'SUBMITTED',
            finance_comment TEXT,
            return_reason TEXT,
            date_received TEXT,
            date_returned TEXT,
            finance_check_date TEXT,
            payment_date TEXT,
            payment_reference TEXT,
            completed_by TEXT,
            completion_notes TEXT,
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
    
    # Insert default departments
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
            ('2024/2025', 0),
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
            ('Student Payment', 3),
            ('Imprest Payment', 5),
            ('Petty Cash Payment', 3),
            ('Supplier Payment', 7),
            ('Salary Payment', 5),
            ('Refund Payment', 10),
            ('Surrender', 4),
        ]
        cursor.executemany(
            "INSERT INTO sla_config (request_type, sla_days) VALUES (?, ?)",
            sla_defaults
        )
    
    conn.commit()
    conn.close()
    
    # Run migration to add missing columns to existing database
    migrate_database()
    
    # Insert default users
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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
            ('hr_user', 'hr123', 'DEPARTMENT', dept_map.get('Human Resource'), 'HR Officer'),
        ]
        cursor.executemany(
            "INSERT INTO users (username, password, role, department_id, full_name) VALUES (?, ?, ?, ?, ?)",
            default_users
        )
    
    conn.commit()
    conn.close()


def get_departments():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT id, name FROM departments ORDER BY name", conn)
    conn.close()
    return df


def get_products():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT name, category, has_payment_type, has_semester FROM products WHERE is_active = 1 ORDER BY name", conn)
    conn.close()
    return df


def add_product(name, category, has_payment_type, has_semester):
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
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT name FROM financial_years WHERE is_active = 1 ORDER BY name DESC", conn)
    conn.close()
    return df['name'].tolist() if not df.empty else []


def get_semesters():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT name FROM semesters ORDER BY name", conn)
    conn.close()
    return df['name'].tolist() if not df.empty else []


def get_funders():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT name FROM funders ORDER BY name", conn)
    conn.close()
    return df['name'].tolist() if not df.empty else []


def get_user_department(username):
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


def get_requests(filters=None):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM requests ORDER BY submission_date DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def save_request(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updates = ["status = ?", "last_updated = ?"]
    params = [status, datetime.now().isoformat()]
    
    if status == 'RECEIVED_BY_FINANCE':
        updates.append("date_received = ?")
        params.append(datetime.now().strftime('%Y-%m-%d'))
        updates.append("finance_check_date = ?")
        params.append(datetime.now().isoformat())
    elif status == 'RETURNED':
        updates.append("date_returned = ?")
        params.append(datetime.now().strftime('%Y-%m-%d'))
        if return_reason:
            updates.append("return_reason = ?")
            params.append(return_reason)
    elif status == 'PAID':
        updates.append("payment_date = ?")
        params.append(datetime.now().strftime('%Y-%m-%d'))
        updates.append("completion_date = ?")
        params.append(datetime.now().strftime('%Y-%m-%d'))
    elif status == 'CLEARED':
        updates.append("payment_date = ?")
        params.append(datetime.now().strftime('%Y-%m-%d'))
        updates.append("completion_date = ?")
        params.append(datetime.now().strftime('%Y-%m-%d'))
    
    if finance_comment:
        updates.append("finance_comment = ?")
        params.append(finance_comment)
    
    params.append(request_id)
    cursor.execute(f"UPDATE requests SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()


def update_payment_details(request_id, payment_reference):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE requests SET payment_reference = ?, payment_date = ?, last_updated = ? WHERE id = ?",
        (payment_reference, datetime.now().strftime('%Y-%m-%d'), datetime.now().isoformat(), request_id)
    )
    conn.commit()
    conn.close()


def authenticate_user(username, password):
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


def update_user_password(username, new_password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
    conn.commit()
    conn.close()
    return True


def get_user_by_username(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.username, u.role, d.name as department_name, u.full_name, u.department_id
        FROM users u
        LEFT JOIN departments d ON u.department_id = d.id
        WHERE u.username = ?
    ''', (username,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_pending_duration(request_date):
    from utils.holidays_ke import working_days_between
    today = date.today()
    submitted_date = datetime.strptime(request_date, '%Y-%m-%d').date()
    return working_days_between(submitted_date, today)


def get_working_days_between(start_date, end_date):
    from utils.holidays_ke import working_days_between
    return working_days_between(start_date, end_date)


def get_dashboard_stats(financial_year=None, quarter=None):
    from utils.holidays_ke import working_days_between
    
    df = get_requests()
    
    # Handle empty dataframe
    if df.empty:
        return {
            'total_requests': 0,
            'total_received': 0,
            'total_returned': 0,
            'total_paid': 0,
            'total_amount': 0,
            'avg_completion_time': 0,
            'total_breaches': 0,
            'breach_rate': 0,
            'completed_count': 0
        }
    
    # Make a copy to avoid warnings
    df = df.copy()
    
    if financial_year and financial_year != "All":
        df = df[df['financial_year'] == financial_year]
    
    if quarter and quarter != "All":
        df['submission_date_dt'] = pd.to_datetime(df['submission_date'])
        if quarter == "Q1 (Jul-Sep)":
            df = df[df['submission_date_dt'].dt.month.isin([7, 8, 9])]
        elif quarter == "Q2 (Oct-Dec)":
            df = df[df['submission_date_dt'].dt.month.isin([10, 11, 12])]
        elif quarter == "Q3 (Jan-Mar)":
            df = df[df['submission_date_dt'].dt.month.isin([1, 2, 3])]
        elif quarter == "Q4 (Apr-Jun)":
            df = df[df['submission_date_dt'].dt.month.isin([4, 5, 6])]
    
    total_requests = len(df)
    
    # Safely check for column existence
    total_received = len(df[df['date_received'].notna()]) if 'date_received' in df.columns else 0
    total_returned = len(df[df['date_returned'].notna()]) if 'date_returned' in df.columns else 0
    total_paid = len(df[df['status'].isin(['PAID', 'CLEARED'])]) if 'status' in df.columns else 0
    total_amount = df['amount'].sum() if 'amount' in df.columns else 0
    
    # Calculate breaches
    breaches = 0
    completion_times = []
    
    if 'status' in df.columns and 'payment_date' in df.columns and 'submission_date' in df.columns:
        for _, row in df.iterrows():
            if row['status'] in ['PAID', 'CLEARED'] and row['payment_date']:
                try:
                    submitted = datetime.strptime(row['submission_date'], '%Y-%m-%d').date()
                    paid = datetime.strptime(row['payment_date'], '%Y-%m-%d').date()
                    days = working_days_between(submitted, paid)
                    completion_times.append(days)
                    
                    sla_map = {'Student Payment': 3, 'Imprest Payment': 5, 'Petty Cash Payment': 3, 
                               'Supplier Payment': 7, 'Salary Payment': 5, 'Refund Payment': 10, 'Surrender': 4}
                    sla_days = sla_map.get(row['request_type'], 5)
                    if days > sla_days:
                        breaches += 1
                except:
                    pass
    
    avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
    breach_rate = (breaches / total_paid * 100) if total_paid > 0 else 0
    
    return {
        'total_requests': total_requests,
        'total_received': total_received,
        'total_returned': total_returned,
        'total_paid': total_paid,
        'total_amount': total_amount,
        'avg_completion_time': avg_completion_time,
        'total_breaches': breaches,
        'breach_rate': breach_rate,
        'completed_count': total_paid
    }


def get_department_performance(financial_year=None):
    from utils.holidays_ke import working_days_between
    
    df = get_requests()
    if df.empty:
        return pd.DataFrame()
    
    if financial_year and financial_year != "All":
        df = df[df['financial_year'] == financial_year]
    
    performance = []
    for dept in df['department_name'].unique():
        dept_df = df[df['department_name'] == dept]
        total = len(dept_df)
        paid = len(dept_df[dept_df['status'].isin(['PAID', 'CLEARED'])])
        
        breaches = 0
        for _, row in dept_df.iterrows():
            if row['status'] in ['PAID', 'CLEARED'] and row['payment_date']:
                try:
                    submitted = datetime.strptime(row['submission_date'], '%Y-%m-%d').date()
                    paid_date = datetime.strptime(row['payment_date'], '%Y-%m-%d').date()
                    days = working_days_between(submitted, paid_date)
                    sla_map = {'Student Payment': 3, 'Imprest Payment': 5, 'Petty Cash Payment': 3, 
                               'Supplier Payment': 7, 'Salary Payment': 5, 'Refund Payment': 10, 'Surrender': 4}
                    sla_days = sla_map.get(row['request_type'], 5)
                    if days > sla_days:
                        breaches += 1
                except:
                    pass
        
        performance.append({
            'department': dept,
            'total_requests': total,
            'completed': paid,
            'completion_rate': (paid / total * 100) if total > 0 else 0,
            'breaches': breaches
        })
    
    return pd.DataFrame(performance)


def get_trend_data(financial_year=None):
    df = get_requests()
    if df.empty:
        return pd.DataFrame()
    
    if financial_year and financial_year != "All":
        df = df[df['financial_year'] == financial_year]
    
    df['submission_date_dt'] = pd.to_datetime(df['submission_date'])
    df['month'] = df['submission_date_dt'].dt.strftime('%b %Y')
    
    monthly = df.groupby('month').agg({
        'amount': 'sum',
        'request_number': 'count'
    }).reset_index()
    monthly.columns = ['month', 'total_amount', 'request_count']
    
    return monthly.sort_values('month')


def get_breach_analysis(financial_year=None):
    from utils.holidays_ke import working_days_between
    
    df = get_requests()
    if df.empty:
        return pd.DataFrame()
    
    if financial_year and financial_year != "All":
        df = df[df['financial_year'] == financial_year]
    
    breach_data = []
    for _, row in df.iterrows():
        if row['status'] in ['PAID', 'CLEARED'] and row['payment_date']:
            try:
                submitted = datetime.strptime(row['submission_date'], '%Y-%m-%d').date()
                paid = datetime.strptime(row['payment_date'], '%Y-%m-%d').date()
                days = working_days_between(submitted, paid)
                
                sla_map = {'Student Payment': 3, 'Imprest Payment': 5, 'Petty Cash Payment': 3, 
                           'Supplier Payment': 7, 'Salary Payment': 5, 'Refund Payment': 10, 'Surrender': 4}
                sla_days = sla_map.get(row['request_type'], 5)
                
                breach_data.append({
                    'request_number': row['request_number'],
                    'request_type': row['request_type'],
                    'department': row['department_name'],
                    'submission_date': row['submission_date'],
                    'payment_date': row['payment_date'],
                    'days_taken': days,
                    'sla_days': sla_days,
                    'status': 'Breached' if days > sla_days else 'Within SLA'
                })
            except:
                pass
    
    return pd.DataFrame(breach_data)
