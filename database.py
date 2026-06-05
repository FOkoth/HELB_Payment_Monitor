import sqlite3
import pandas as pd
from datetime import datetime, date
import os
import json
import shutil

DB_PATH = "helb_data.db"
BACKUP_DIR = "backups"

# ================================================================
# BACKUP FUNCTIONS
# ================================================================
def ensure_backup_dir():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)


def create_backup():
    ensure_backup_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"helb_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, backup_path)
        metadata = {
            'backup_date': datetime.now().isoformat(),
            'original_db': DB_PATH,
            'file_size': os.path.getsize(DB_PATH)
        }
        meta_path = os.path.join(BACKUP_DIR, f"helb_backup_{timestamp}.json")
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        return backup_filename, backup_path
    return None, None


def get_backup_list():
    ensure_backup_dir()
    backups = []
    for file in os.listdir(BACKUP_DIR):
        if file.endswith('.db'):
            backup_path = os.path.join(BACKUP_DIR, file)
            meta_path = backup_path.replace('.db', '.json')
            metadata = {}
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {
                    'backup_date': datetime.fromtimestamp(os.path.getmtime(backup_path)).isoformat(),
                    'file_size': os.path.getsize(backup_path)
                }
            backups.append({
                'filename': file,
                'path': backup_path,
                'date': metadata.get('backup_date', 'Unknown'),
                'size': metadata.get('file_size', 0)
            })
    backups.sort(key=lambda x: x['date'], reverse=True)
    return backups


def restore_backup(backup_filename):
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    if os.path.exists(backup_path):
        if os.path.exists(DB_PATH):
            emergency_backup = f"helb_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(DB_PATH, os.path.join(BACKUP_DIR, emergency_backup))
        shutil.copy2(backup_path, DB_PATH)
        return True
    return False


def auto_backup_scheduler():
    ensure_backup_dir()
    backups = get_backup_list()
    if backups:
        last_backup_date = datetime.fromisoformat(backups[0]['date']).date()
        today = date.today()
        if last_backup_date != today:
            create_backup()
            return True
    else:
        create_backup()
        return True
    return False


def export_data_to_csv():
    df_requests = get_requests()
    df_users = get_all_users()
    df_departments = get_departments()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_dir = os.path.join(BACKUP_DIR, f"csv_export_{timestamp}")
    os.makedirs(export_dir, exist_ok=True)
    df_requests.to_csv(os.path.join(export_dir, "requests.csv"), index=False)
    df_users.to_csv(os.path.join(export_dir, "users.csv"), index=False)
    df_departments.to_csv(os.path.join(export_dir, "departments.csv"), index=False)
    return export_dir


# ================================================================
# LOGS TABLE
# ================================================================
def create_logs_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER,
            request_number TEXT,
            action TEXT NOT NULL,
            status_from TEXT,
            status_to TEXT,
            comment TEXT,
            performed_by TEXT,
            performed_by_role TEXT,
            performed_by_dept TEXT,
            timestamp TEXT,
            details TEXT
        )
    ''')
    conn.commit()
    conn.close()


def add_request_log(request_id, request_number, action, status_from, status_to, 
                    comment, performed_by, performed_by_role, performed_by_dept, details=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO request_logs (
                request_id, request_number, action, status_from, status_to,
                comment, performed_by, performed_by_role, performed_by_dept,
                timestamp, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request_id, request_number, action, status_from, status_to,
            comment, performed_by, performed_by_role, performed_by_dept,
            datetime.now().isoformat(), details
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error adding log: {e}")


def get_request_logs(request_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM request_logs 
            WHERE request_id = ? 
            ORDER BY timestamp ASC
        ''', (request_id,))
        logs = cursor.fetchall()
        conn.close()
        if logs:
            columns = ['id', 'request_id', 'request_number', 'action', 'status_from', 
                       'status_to', 'comment', 'performed_by', 'performed_by_role', 
                       'performed_by_dept', 'timestamp', 'details']
            return [dict(zip(columns, log)) for log in logs]
        return []
    except Exception as e:
        print(f"Error getting logs: {e}")
        return []


# ================================================================
# BASIC REQUEST FUNCTIONS
# ================================================================
def get_returned_requests(department_name):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM requests WHERE status = 'RETURNED' AND department_name = ? ORDER BY date_returned DESC",
        conn, params=(department_name,)
    )
    conn.close()
    return df


def resubmit_request(request_id, updated_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    set_clause = ', '.join([f"{k} = ?" for k in updated_data.keys()])
    values = list(updated_data.values())
    values.append(request_id)
    cursor.execute(f"UPDATE requests SET {set_clause}, last_updated = ? WHERE id = ?", 
                   values + [datetime.now().isoformat()])
    conn.commit()
    conn.close()


def get_request_by_id(request_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
    row = cursor.fetchone()
    if row:
        columns = [description[0] for description in cursor.description]
        result = dict(zip(columns, row))
        conn.close()
        return result
    conn.close()
    return None


def get_column_names(table_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    conn.close()
    return columns


def calculate_tat(submission_date, payment_date=None):
    from utils.holidays_ke import working_days_between
    sub_date = datetime.strptime(submission_date, '%Y-%m-%d').date()
    if payment_date:
        pay_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
        return working_days_between(sub_date, pay_date)
    else:
        today = date.today()
        return working_days_between(sub_date, today)


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
    
    # Users table with finance permissions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            department_id INTEGER,
            full_name TEXT,
            can_receive_requests INTEGER DEFAULT 0,
            can_process_stages INTEGER DEFAULT 0,
            can_release_payments INTEGER DEFAULT 0,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    ''')
    
    # Requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_number TEXT UNIQUE NOT NULL,
            request_type TEXT NOT NULL,
            main_category TEXT,
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
            last_updated TEXT,
            finance_checklist_approvals INTEGER DEFAULT 0,
            finance_checklist_documents INTEGER DEFAULT 0,
            finance_checklist_comments TEXT,
            date_confirmed_by_finance TEXT,
            mileage_claim_details TEXT,
            training_details TEXT,
            professional_body TEXT,
            direct_payment_details TEXT
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
        default_years = [('2024/2025', 0), ('2025/2026', 1), ('2026/2027', 1)]
        cursor.executemany("INSERT INTO financial_years (name, is_active) VALUES (?, ?)", default_years)
    
    # Insert semesters
    cursor.execute("SELECT COUNT(*) FROM semesters")
    if cursor.fetchone()[0] == 0:
        default_semesters = [('Semester 1',), ('Semester 2',)]
        cursor.executemany("INSERT INTO semesters (name) VALUES (?)", default_semesters)
    
    # Insert SLA defaults
    cursor.execute("SELECT COUNT(*) FROM sla_config")
    if cursor.fetchone()[0] == 0:
        sla_defaults = [
            ('Student Payment', 3), ('Imprest', 5), ('Petty Cash', 3),
            ('Supplier Payment', 7), ('Salary Payment', 5), ('Refund Payment', 10),
            ('Surrender', 4), ('Mileage Claim', 3), ('Staff Training', 5),
            ('Professional Body', 5), ('Direct Payment', 3)
        ]
        cursor.executemany("INSERT INTO sla_config (request_type, sla_days) VALUES (?, ?)", sla_defaults)
    
    conn.commit()
    conn.close()
    
    create_logs_table()
    
    # Insert default users
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM departments")
    dept_map = {name: id for id, name in cursor.fetchall()}
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        default_users = [
            ('admin', 'admin123', 'ADMIN', None, 'System Administrator', 0, 0, 0),
            ('finance_receiver', 'receiver123', 'FINANCE_RECEIVER', dept_map.get('Finance'), 'Finance Receiver', 1, 0, 0),
            ('finance_processor', 'processor123', 'FINANCE_PROCESSOR', dept_map.get('Finance'), 'Finance Processor', 0, 1, 0),
            ('finance_releaser', 'releaser123', 'FINANCE_RELEASER', dept_map.get('Finance'), 'Finance Releaser', 0, 0, 1),
            ('finance_admin', 'finadmin123', 'FINANCE_ADMIN', dept_map.get('Finance'), 'Finance Admin', 1, 1, 1),
            ('management_user', 'management123', 'MANAGEMENT', None, 'Management User', 0, 0, 0),
            ('lending_user', 'lend123', 'DEPARTMENT', dept_map.get('Lending'), 'Lending Officer', 0, 0, 0),
            ('erm_user', 'erm123', 'DEPARTMENT', dept_map.get('External Resource Mobilization'), 'ERM Officer', 0, 0, 0),
            ('debt_user', 'debt123', 'DEPARTMENT', dept_map.get('Debt Management'), 'Debt Officer', 0, 0, 0),
            ('scm_user', 'scm123', 'DEPARTMENT', dept_map.get('Supply Chain Management'), 'SCM Officer', 0, 0, 0),
            ('hr_user', 'hr123', 'DEPARTMENT', dept_map.get('Human Resource'), 'HR Officer', 0, 0, 0),
            ('ceo_user', 'ceo123', 'DEPARTMENT', dept_map.get('CEO\'s Office'), 'CEO Office', 0, 0, 0),
            ('corpcomm_user', 'corp123', 'DEPARTMENT', dept_map.get('Corporate Communication'), 'Comm Officer', 0, 0, 0),
            ('field_user', 'field123', 'DEPARTMENT', dept_map.get('Field Services'), 'Field Officer', 0, 0, 0),
            ('ict_user', 'ict123', 'DEPARTMENT', dept_map.get('ICT'), 'ICT Officer', 0, 0, 0),
            ('internal_audit_user', 'audit123', 'DEPARTMENT', dept_map.get('Internal Audit'), 'Audit Officer', 0, 0, 0),
            ('legal_user', 'legal123', 'DEPARTMENT', dept_map.get('Legal Services'), 'Legal Officer', 0, 0, 0),
            ('strategy_user', 'strat123', 'DEPARTMENT', dept_map.get('Strategy'), 'Strategy Officer', 0, 0, 0),
        ]
        cursor.executemany(
            "INSERT INTO users (username, password, role, department_id, full_name, can_receive_requests, can_process_stages, can_release_payments) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            default_users
        )
    
    # Insert finance settings
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='finance_settings'")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS finance_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE,
                setting_value TEXT
            )
        ''')
        cursor.execute("INSERT INTO finance_settings (setting_key, setting_value) VALUES (?, ?)", 
                       ('finance_password', 'finance123'))
    
    conn.commit()
    conn.close()


# ================================================================
# FINANCE PASSWORD FUNCTIONS
# ================================================================
def verify_finance_password(password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT setting_value FROM finance_settings WHERE setting_key = 'finance_password'")
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == password


def update_finance_password(new_password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE finance_settings SET setting_value = ? WHERE setting_key = 'finance_password'", (new_password,))
    conn.commit()
    conn.close()
    return True


def get_finance_password():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT setting_value FROM finance_settings WHERE setting_key = 'finance_password'")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 'finance123'


# ================================================================
# ENHANCED USER FUNCTIONS
# ================================================================
def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    query = '''
        SELECT u.username, u.role, d.name as department, u.full_name,
               u.can_receive_requests, u.can_process_stages, u.can_release_payments
        FROM users u
        LEFT JOIN departments d ON u.department_id = d.id
        ORDER BY u.username
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def create_user(username, password, role, department_id, full_name, 
                can_receive_requests=0, can_process_stages=0, can_release_payments=0):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, role, department_id, full_name, can_receive_requests, can_process_stages, can_release_payments) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (username, password, role, department_id, full_name, can_receive_requests, can_process_stages, can_release_payments)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False
    finally:
        conn.close()


def update_user_permissions(username, can_receive, can_process, can_release):
    """Update finance user permissions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE users 
            SET can_receive_requests = ?, can_process_stages = ?, can_release_payments = ?
            WHERE username = ?
        ''', (can_receive, can_process, can_release, username))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating permissions: {e}")
        return False
    finally:
        conn.close()


def get_user_permissions(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT can_receive_requests, can_process_stages, can_release_payments, role
        FROM users WHERE username = ?
    ''', (username,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            'can_receive': result[0] == 1,
            'can_process': result[1] == 1,
            'can_release': result[2] == 1,
            'role': result[3]
        }
    return {'can_receive': False, 'can_process': False, 'can_release': False, 'role': 'DEPARTMENT'}


def delete_user(username):
    """Delete a user by username"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False
    finally:
        conn.close()


# ================================================================
# DEPARTMENT FUNCTIONS
# ================================================================
def create_department(name, permissions):
    """Create a new department with permissions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        can_imprest, can_petty, can_supplier, can_student, can_surrender, can_refund, requires_product, requires_funder, is_finance = permissions
        cursor.execute('''
            INSERT INTO departments (
                name, can_submit_imprest, can_submit_petty_cash, 
                can_submit_supplier, can_submit_student_payment, 
                can_submit_surrender, can_submit_refund, 
                requires_product_type, requires_funder, is_finance_dept
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, can_imprest, can_petty, can_supplier, can_student, can_surrender, can_refund, requires_product, requires_funder, is_finance))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating department: {e}")
        return False
    finally:
        conn.close()


def delete_department(dept_id):
    """Delete a department by ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM departments WHERE id = ?", (dept_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting department: {e}")
        return False
    finally:
        conn.close()


# ================================================================
# SEARCH FUNCTIONS
# ================================================================
def search_payment_records(search_term, search_type="all"):
    """Search payment records by various criteria"""
    conn = sqlite3.connect(DB_PATH)
    
    if search_type == "batch_no":
        query = "SELECT * FROM requests WHERE batch_no LIKE ? ORDER BY submission_date DESC"
        params = (f"%{search_term}%",)
    elif search_type == "request_number":
        query = "SELECT * FROM requests WHERE request_number LIKE ? ORDER BY submission_date DESC"
        params = (f"%{search_term}%",)
    elif search_type == "invoice_no":
        query = "SELECT * FROM requests WHERE invoice_no LIKE ? ORDER BY submission_date DESC"
        params = (f"%{search_term}%",)
    elif search_type == "imprest_no":
        query = "SELECT * FROM requests WHERE imprest_no LIKE ? ORDER BY submission_date DESC"
        params = (f"%{search_term}%",)
    elif search_type == "surrender_number":
        query = "SELECT * FROM requests WHERE surrender_number LIKE ? ORDER BY submission_date DESC"
        params = (f"%{search_term}%",)
    else:
        query = '''
            SELECT * FROM requests 
            WHERE request_number LIKE ? 
               OR batch_no LIKE ? 
               OR invoice_no LIKE ? 
               OR imprest_no LIKE ? 
               OR surrender_number LIKE ?
               OR customer_name LIKE ?
               OR supplier_name LIKE ?
               OR staff_name LIKE ?
               OR payment_reference LIKE ?
            ORDER BY submission_date DESC
        '''
        params = (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", 
                  f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", 
                  f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_departments():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT id, name FROM departments ORDER BY name", conn)
    conn.close()
    return df


def get_products():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT id, name, category, has_payment_type, has_semester FROM products WHERE is_active = 1 ORDER BY name", conn)
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
    except:
        return False
    finally:
        conn.close()


def delete_product(product_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


def get_financial_years():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT id, name FROM financial_years WHERE is_active = 1 ORDER BY name DESC", conn)
    conn.close()
    return df['name'].tolist() if not df.empty else []


def add_financial_year(year_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO financial_years (name, is_active) VALUES (?, 1)", (year_name,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


def delete_financial_year(year_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM financial_years WHERE id = ?", (year_id,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


def get_semesters():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT id, name FROM semesters ORDER BY name", conn)
    conn.close()
    return df['name'].tolist() if not df.empty else []


def add_semester(semester_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO semesters (name) VALUES (?)", (semester_name,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


def delete_semester(semester_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM semesters WHERE id = ?", (semester_id,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


def get_funders():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT id, name FROM funders ORDER BY name", conn)
    conn.close()
    return df


def add_funder(funder_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO funders (name) VALUES (?)", (funder_name,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


def delete_funder(funder_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM funders WHERE id = ?", (funder_id,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


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


def get_requests():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM requests ORDER BY submission_date DESC", conn)
    conn.close()
    return df


def get_pending_confirmation_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'SUBMITTED'")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_pending_completion_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM requests WHERE status NOT IN ('PAID', 'CLEARED', 'RETURNED')")
    count = cursor.fetchone()[0]
    conn.close()
    return count


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
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    try:
        add_request_log(request_id, request_number, "SUBMITTED", None, "SUBMITTED",
                       "Request submitted", data.get('submitted_by'), "DEPARTMENT", data.get('department_name'))
    except:
        pass
    return request_number


def update_request_status(request_id, status, finance_comment=None, return_reason=None, 
                          performed_by=None, performed_by_role=None, performed_by_dept=None,
                          checklist_approvals=None, checklist_documents=None, checklist_comments=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT status, request_number, main_category FROM requests WHERE id = ?", (request_id,))
    current = cursor.fetchone()
    old_status = current[0] if current else None
    request_number = current[1] if current else None
    
    cursor.execute("PRAGMA table_info(requests)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    updates = ["status = ?", "last_updated = ?"]
    params = [status, datetime.now().isoformat()]
    action = ""
    comment = finance_comment or return_reason
    
    if status == 'RECEIVED_BY_FINANCE':
        if 'date_received' in existing_columns:
            updates.append("date_received = ?")
            params.append(datetime.now().strftime('%Y-%m-%d'))
        if 'date_confirmed_by_finance' in existing_columns:
            updates.append("date_confirmed_by_finance = ?")
            params.append(datetime.now().strftime('%Y-%m-%d'))
        if checklist_approvals is not None and 'finance_checklist_approvals' in existing_columns:
            updates.append("finance_checklist_approvals = ?")
            params.append(1 if checklist_approvals else 0)
        if checklist_documents is not None and 'finance_checklist_documents' in existing_columns:
            updates.append("finance_checklist_documents = ?")
            params.append(1 if checklist_documents else 0)
        if checklist_comments and 'finance_checklist_comments' in existing_columns:
            updates.append("finance_checklist_comments = ?")
            params.append(checklist_comments)
        action = "RECEIVED"
    
    elif status == 'RETURNED':
        if 'date_returned' in existing_columns:
            updates.append("date_returned = ?")
            params.append(datetime.now().strftime('%Y-%m-%d'))
        if return_reason and 'return_reason' in existing_columns:
            updates.append("return_reason = ?")
            params.append(return_reason)
        action = "RETURNED"
    
    elif status == 'SUBMITTED':
        if 'submission_date' in existing_columns:
            updates.append("submission_date = ?")
            params.append(datetime.now().strftime('%Y-%m-%d'))
        if 'date_returned' in existing_columns:
            updates.append("date_returned = ?")
            params.append(None)
        if 'return_reason' in existing_columns:
            updates.append("return_reason = ?")
            params.append(None)
        action = "RESUBMITTED"
    
    # Payment statuses
    elif status == 'PAYMENT_PREPARED':
        action = "Payment Prepared"
    
    elif status == 'PAYMENT_VERIFIED':
        action = "Payment Verified"
    
    elif status == 'PAYMENT_APPROVED':
        action = "Payment Approved"
    
    elif status == 'PAYMENT_AUTHORIZED':
        action = "Payment Authorized"
    
    # Surrender statuses
    elif status == 'SURRENDER_FIRST_VERIFICATION':
        action = "First Verification"
    
    elif status == 'SURRENDER_SECOND_VERIFICATION':
        action = "Second Verification"
    
    elif status == 'SURRENDER_APPROVAL':
        action = "Surrender Approval"
    
    elif status == 'SURRENDER_POSTING':
        action = "Surrender Posting"
    
    elif status == 'PAID':
        if 'payment_date' in existing_columns:
            updates.append("payment_date = ?")
            params.append(datetime.now().strftime('%Y-%m-%d'))
        if 'completion_date' in existing_columns:
            updates.append("completion_date = ?")
            params.append(datetime.now().strftime('%Y-%m-%d'))
        action = "PAID"
    
    elif status == 'CLEARED':
        if 'payment_date' in existing_columns:
            updates.append("payment_date = ?")
            params.append(datetime.now().strftime('%Y-%m-%d'))
        if 'completion_date' in existing_columns:
            updates.append("completion_date = ?")
            params.append(datetime.now().strftime('%Y-%m-%d'))
        action = "CLEARED"
    
    if finance_comment and 'finance_comment' in existing_columns:
        updates.append("finance_comment = ?")
        params.append(finance_comment)
    
    params.append(request_id)
    cursor.execute(f"UPDATE requests SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    
    if action:
        try:
            add_request_log(request_id, request_number, action, old_status, status,
                           comment, performed_by, performed_by_role, performed_by_dept)
        except:
            pass


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
            SELECT u.username, u.role, d.name as department_name, u.full_name, u.department_id, 
                   COALESCE(d.is_finance_dept, 0) as is_finance_dept,
                   u.can_receive_requests, u.can_process_stages, u.can_release_payments
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.id
            WHERE u.username = ? AND u.password = ?
        ''', (username, password))
        user = cursor.fetchone()
        conn.close()
        return user if user else None
    except:
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
        SELECT u.username, u.role, d.name as department_name, u.full_name, u.department_id,
               u.can_receive_requests, u.can_process_stages, u.can_release_payments
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


def get_time_lapsed_from_confirmation(request_id):
    from utils.holidays_ke import working_days_between
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT date_confirmed_by_finance, payment_date, completion_date FROM requests WHERE id = ?", (request_id,))
        result = cursor.fetchone()
        conn.close()
        if result and result[0]:
            confirmed_date = datetime.strptime(result[0], '%Y-%m-%d').date()
            if result[1]:
                completion_date = datetime.strptime(result[1], '%Y-%m-%d').date()
                return working_days_between(confirmed_date, completion_date)
            elif result[2]:
                completion_date = datetime.strptime(result[2], '%Y-%m-%d').date()
                return working_days_between(confirmed_date, completion_date)
            else:
                return working_days_between(confirmed_date, date.today())
        return None
    except:
        return None


def get_department_requests(department_name):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM requests WHERE department_name = ? ORDER BY submission_date DESC",
        conn, params=(department_name,)
    )
    conn.close()
    return df


def get_management_dashboard_stats(financial_year=None, quarter=None):
    from utils.holidays_ke import working_days_between
    df = get_requests()
    if df.empty:
        return {'total_requests': 0, 'total_received': 0, 'total_returned': 0,
                'total_paid': 0, 'total_amount': 0, 'avg_completion_time': 0,
                'total_breaches': 0, 'breach_rate': 0, 'completed_count': 0}
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
    total_received = len(df[df['date_received'].notna()])
    total_returned = len(df[df['date_returned'].notna()])
    total_paid = len(df[df['status'].isin(['PAID', 'CLEARED'])])
    total_amount = df['amount'].sum()
    breaches = 0
    completion_times = []
    for _, row in df.iterrows():
        if row['status'] in ['PAID', 'CLEARED'] and row['payment_date']:
            try:
                submitted = datetime.strptime(row['submission_date'], '%Y-%m-%d').date()
                paid = datetime.strptime(row['payment_date'], '%Y-%m-%d').date()
                days = working_days_between(submitted, paid)
                completion_times.append(days)
                sla_map = {'Student Payment': 3, 'Imprest': 5, 'Petty Cash': 3, 
                           'Supplier Payment': 7, 'Salary Payment': 5, 'Refund Payment': 10,
                           'Surrender': 4, 'Mileage Claim': 3, 'Staff Training': 5,
                           'Professional Body': 5, 'Direct Payment': 3}
                sla_days = sla_map.get(row['request_type'], 5)
                if days > sla_days:
                    breaches += 1
            except:
                pass
    avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
    breach_rate = (breaches / total_paid * 100) if total_paid > 0 else 0
    return {'total_requests': total_requests, 'total_received': total_received,
            'total_returned': total_returned, 'total_paid': total_paid,
            'total_amount': total_amount, 'avg_completion_time': avg_completion_time,
            'total_breaches': breaches, 'breach_rate': breach_rate, 'completed_count': total_paid}


def get_trend_data(financial_year=None):
    df = get_requests()
    if df.empty:
        return pd.DataFrame()
    if financial_year and financial_year != "All":
        df = df[df['financial_year'] == financial_year]
    df['submission_date_dt'] = pd.to_datetime(df['submission_date'])
    df['month'] = df['submission_date_dt'].dt.strftime('%b %Y')
    monthly = df.groupby('month').agg({'amount': 'sum', 'request_number': 'count'}).reset_index()
    monthly.columns = ['month', 'total_amount', 'request_count']
    return monthly.sort_values('month')


def get_all_departments_summary():
    conn = sqlite3.connect(DB_PATH)
    query = '''
        SELECT department_name, COUNT(*) as total_requests,
               SUM(CASE WHEN status IN ('PAID', 'CLEARED') THEN 1 ELSE 0 END) as completed,
               SUM(CASE WHEN status = 'RETURNED' THEN 1 ELSE 0 END) as returned,
               SUM(amount) as total_amount
        FROM requests GROUP BY department_name ORDER BY total_requests DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def search_by_batch_number(batch_no):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT request_number, main_category, amount, status, payment_date, 
               payment_reference, department_name, submission_date
        FROM requests WHERE batch_no = ? AND main_category = 'Submit Payment Request'
        ORDER BY submission_date DESC
    ''', (batch_no,))
    results = cursor.fetchall()
    conn.close()
    if results:
        return [{'request_number': r[0], 'main_category': r[1], 'amount': r[2],
                 'status': r[3], 'payment_date': r[4], 'payment_reference': r[5],
                 'department': r[6], 'submission_date': r[7]} for r in results]
    return []


def get_all_batch_numbers():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT batch_no FROM requests 
        WHERE main_category = 'Submit Payment Request' AND batch_no IS NOT NULL
        ORDER BY batch_no DESC
    ''')
    results = cursor.fetchall()
    conn.close()
    return [r[0] for r in results if r[0]]


def get_allowed_main_categories(user_role, user_dept):
    finance_roles = ["FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER", "FINANCE_ADMIN"]
    if user_role in ["MANAGEMENT"] + finance_roles:
        return []
    return ["Submit Payment Request", "Submit Surrender"]


def get_allowed_request_types(user_role, user_dept, main_category):
    if user_role == "ADMIN":
        if main_category == "Submit Payment Request":
            return ["Student Payment", "Imprest", "Petty Cash", "Supplier Payment", 
                    "Salary Payment", "Refund Payment", "Mileage Claim", "Staff Training", 
                    "Professional Body", "Direct Payment"]
        else:
            return ["Surrender"]
    
    finance_roles = ["FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER", "FINANCE_ADMIN"]
    if user_role in finance_roles:
        return []
    
    if user_role == "MANAGEMENT":
        return []
    
    if main_category == "Submit Payment Request":
        allowed = ["Imprest", "Petty Cash", "Direct Payment"]
        if user_dept in ["Lending", "External Resource Mobilization"]:
            allowed.append("Student Payment")
        if user_dept == "Supply Chain Management":
            allowed.append("Supplier Payment")
        if user_dept == "Human Resource":
            allowed.append("Salary Payment")
            allowed.append("Mileage Claim")
            allowed.append("Staff Training")
            allowed.append("Professional Body")
        if user_dept == "Debt Management":
            allowed.append("Refund Payment")
        return allowed
    else:
        return ["Surrender"]


def get_reports_data(user_role, user_dept):
    df = get_requests()
    if df.empty:
        return df
    finance_roles = ["FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER", "FINANCE_ADMIN"]
    if user_role in ["ADMIN", "MANAGEMENT"] + finance_roles:
        return df
    else:
        return df[df['department_name'] == user_dept]


# ================================================================
# WORKFLOW MANAGEMENT FUNCTIONS
# ================================================================
def get_workflow_stages(request_type):
    """Get workflow stages for a request type"""
    if request_type == "Surrender":
        return [
            {'stage': 'RECEIVED_BY_FINANCE', 'name': 'Received', 'order': 1},
            {'stage': 'SURRENDER_FIRST_VERIFICATION', 'name': 'First Verification', 'order': 2},
            {'stage': 'SURRENDER_SECOND_VERIFICATION', 'name': 'Second Verification', 'order': 3},
            {'stage': 'SURRENDER_APPROVAL', 'name': 'Approval', 'order': 4},
            {'stage': 'SURRENDER_POSTING', 'name': 'Posting', 'order': 5},
            {'stage': 'CLEARED', 'name': 'Cleared', 'order': 6}
        ]
    else:
        return [
            {'stage': 'RECEIVED_BY_FINANCE', 'name': 'Received', 'order': 1},
            {'stage': 'PAYMENT_PREPARED', 'name': 'Prepared', 'order': 2},
            {'stage': 'PAYMENT_VERIFIED', 'name': 'Verified', 'order': 3},
            {'stage': 'PAYMENT_APPROVED', 'name': 'Approved', 'order': 4},
            {'stage': 'PAYMENT_AUTHORIZED', 'name': 'Authorized', 'order': 5},
            {'stage': 'PAID', 'name': 'Paid', 'order': 6}
        ]


def can_user_perform_action(user_role, user_permissions, current_status, target_status):
    """Check if user can perform a workflow action"""
    # Admin can do anything
    if user_role == "ADMIN":
        return True
    
    # Finance Admin can do everything
    if user_role == "FINANCE_ADMIN":
        return True
    
    # Permission-based checks
    if target_status == 'RECEIVED_BY_FINANCE':
        return user_permissions.get('can_receive', False)
    elif target_status in ['PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED',
                           'SURRENDER_FIRST_VERIFICATION', 'SURRENDER_SECOND_VERIFICATION', 'SURRENDER_APPROVAL', 'SURRENDER_POSTING']:
        return user_permissions.get('can_process', False)
    elif target_status in ['PAID', 'CLEARED']:
        return user_permissions.get('can_release', False)
    
    return False
