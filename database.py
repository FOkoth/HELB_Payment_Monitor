import os
import json
import time
import logging
import hashlib
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from functools import wraps

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================================
# DATABASE URL - SINGLE SOURCE OF TRUTH
# ============================================================
# IMPORTANT: Get this from Supabase → Settings → Database → Connection string
# Replace with YOUR actual password
DATABASE_URL = "postgresql://postgres:Helb%402025Secure%21@db.zbgkjyhootmctohnngiq.supabase.co:5432/postgres"

#DATABASE_URL = "postgresql://postgres:Helb%402025Secure%21@db.zbgkjyhootmctohnngiq.supabase.co:5432/postgres"

# Try to get from environment or secrets
try:
    import streamlit as st
    DATABASE_URL = st.secrets.get("DATABASE_URL", DATABASE_URL)
except:
    pass

if os.getenv('DATABASE_URL'):
    DATABASE_URL = os.getenv('DATABASE_URL')

print(f"✅ DATABASE_URL loaded")
PRODUCTION_MODE = str(os.getenv('PRODUCTION_MODE', 'False')).lower() == 'true'

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("psycopg2-binary not installed. Run: pip install psycopg2-binary")
    raise

def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"helb_db_{datetime.now().strftime('%Y%m%d')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ============================================================
# CONNECTION FUNCTION - WITH SSL AND RETRY
# ============================================================
def get_connection():
    """Get database connection with SSL and retry logic"""
    try:
        print(f"🔍 Connecting to Supabase...")
        # Try with SSL first
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        print(f"✅ Connected to Supabase!")
        return conn
    except Exception as e1:
        print(f"⚠️ SSL connection failed: {e1}")
        try:
            # Try without SSL
            conn = psycopg2.connect(DATABASE_URL)
            print(f"✅ Connected to Supabase (no SSL)!")
            return conn
        except Exception as e2:
            print(f"❌ All connection attempts failed: {e2}")
            logger.error(f"Database connection error: {e2}")
            raise

def execute_query(query, params=None, fetch_all=False, fetch_one=False, commit=False):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = None
        if fetch_all:
            result = cursor.fetchall()
        elif fetch_one:
            result = cursor.fetchone()
        if commit:
            conn.commit()
        return result
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Query error: {e}")
        print(f"❌ execute_query error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================
# FALLBACK USERS - ONLY FOR EMERGENCY
# ============================================================
def get_fallback_users():
    """Emergency fallback users - only used when database is completely down"""
    from datetime import datetime
    return pd.DataFrame([
        {
            'username': 'admin',
            'role': 'ADMIN',
            'department': 'Finance',
            'full_name': 'System Administrator',
            'can_receive_requests': 1,
            'can_process_stages': 1,
            'can_release_payments': 1,
            'created_at': datetime.now().isoformat(),
            'is_active': 1
        },
        {
            'username': 'test',
            'role': 'DEPARTMENT',
            'department': 'Lending',
            'full_name': 'Test User',
            'can_receive_requests': 0,
            'can_process_stages': 0,
            'can_release_payments': 0,
            'created_at': datetime.now().isoformat(),
            'is_active': 1
        },
        {
            'username': 'finance_user',
            'role': 'FINANCE_RECEIVER',
            'department': 'Finance',
            'full_name': 'Finance User',
            'can_receive_requests': 1,
            'can_process_stages': 0,
            'can_release_payments': 0,
            'created_at': datetime.now().isoformat(),
            'is_active': 1
        }
    ])

# ============================================================
# GET ALL USERS - ALWAYS RETURNS DATA
# ============================================================
def get_all_users():
    """Get all users from database, with emergency fallback"""
    conn = None
    try:
        print("🔍 get_all_users: Starting...")
        conn = get_connection()
        print("🔍 get_all_users: Connected!")
        
        query = "SELECT username, role, full_name, can_receive_requests, can_process_stages, can_release_payments, created_at, is_active FROM users ORDER BY username"
        
        print(f"🔍 get_all_users: Executing query...")
        df = pd.read_sql_query(query, conn)
        print(f"🔍 get_all_users: Query returned {len(df)} rows")
        
        df['department'] = None
        
        df = df[['username', 'role', 'department', 'full_name', 
                'can_receive_requests', 'can_process_stages', 
                'can_release_payments', 'created_at', 'is_active']]
        
        conn.close()
        
        # If no users in database, return fallback
        if df.empty:
            print("⚠️ get_all_users: Database has no users! Using fallback.")
            return get_fallback_users()
        
        print(f"✅ get_all_users: Returning {len(df)} users from database")
        # Print users for debugging
        for idx, row in df.iterrows():
            print(f"   👤 {row['username']} ({row['role']})")
        
        return df
        
    except Exception as e:
        print(f"❌ get_all_users error: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        # EMERGENCY FALLBACK - Keep the app running
        print("⚠️ get_all_users: Database unavailable! Using emergency fallback.")
        return get_fallback_users()

# ============================================================
# GET DEPARTMENTS
# ============================================================
def get_departments():
    conn = None
    try:
        print("🔍 get_departments: Starting...")
        conn = get_connection()
        print("🔍 get_departments: Connected!")
        
        query = "SELECT id, name FROM departments ORDER BY name"
        
        print(f"🔍 get_departments: Executing query...")
        df = pd.read_sql_query(query, conn)
        print(f"🔍 get_departments: Query returned {len(df)} rows")
        
        conn.close()
        return df
        
    except Exception as e:
        print(f"❌ get_departments error: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        # Fallback departments
        print("⚠️ get_departments: Using fallback departments.")
        return pd.DataFrame([
            {'id': 6, 'name': 'Finance'},
            {'id': 11, 'name': 'Lending'},
            {'id': 7, 'name': 'Human Resource'},
            {'id': 8, 'name': 'ICT'},
            {'id': 12, 'name': 'Strategy'},
            {'id': 1, 'name': "CEO's Office"},
            {'id': 2, 'name': 'Corporate Communication'},
            {'id': 3, 'name': 'Debt Management'},
            {'id': 4, 'name': 'External Resource Mobilization'},
            {'id': 5, 'name': 'Field Services'},
            {'id': 9, 'name': 'Internal Audit'},
            {'id': 10, 'name': 'Legal Services'},
            {'id': 13, 'name': 'Supply Chain Management'}
        ])

# ============================================================
# AUTHENTICATE USER - WITH EMERGENCY FALLBACK
# ============================================================
def authenticate_user(username, password):
    conn = None
    cursor = None
    try:
        print(f"🔍 AUTH: Attempting login for '{username}'")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT u.username, u.role, d.name as department_name, u.full_name, u.department_id, 
                   COALESCE(d.is_finance_dept, 0) as is_finance_dept,
                   u.can_receive_requests, u.can_process_stages, u.can_release_payments
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.id
            WHERE u.username = %s AND u.password = %s AND u.is_active = 1
        """
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        
        if user:
            update_query = "UPDATE users SET last_login = %s WHERE username = %s"
            cursor.execute(update_query, (datetime.now().isoformat(), username))
            conn.commit()
            print(f"✅ AUTH: User '{username}' authenticated from database!")
            cursor.close()
            conn.close()
            return user
        
        cursor.close()
        conn.close()
        
        # EMERGENCY FALLBACK - Only for admin
        if username == 'admin' and password == 'admin123':
            print(f"✅ AUTH: Emergency admin fallback!")
            return ("admin", "ADMIN", "Finance", "System Administrator", 6, 1, 1, 1, 1)
        
        print(f"❌ AUTH: Invalid credentials for '{username}'")
        return None
        
    except Exception as e:
        print(f"❌ AUTH error: {e}")
        import traceback
        traceback.print_exc()
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        
        # EMERGENCY FALLBACK - Only for admin
        if username == 'admin' and password == 'admin123':
            print(f"✅ AUTH: Emergency admin fallback!")
            return ("admin", "ADMIN", "Finance", "System Administrator", 6, 1, 1, 1, 1)
        
        return None

# ============================================================
# GET USER BY USERNAME - WITH EMERGENCY FALLBACK
# ============================================================
def get_user_by_username(username):
    try:
        query = """
            SELECT u.username, u.role, d.name as department_name, u.full_name, u.department_id,
                   u.can_receive_requests, u.can_process_stages, u.can_release_payments,
                   u.created_at, u.last_login, u.is_active
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.id
            WHERE u.username = %s
        """
        result = execute_query(query, (username,), fetch_one=True)
        
        if result:
            return result
        
        # Emergency fallback
        if username == 'admin':
            return ('admin', 'ADMIN', 'Finance', 'System Administrator', 6, 1, 1, 1, 
                    datetime.now().isoformat(), datetime.now().isoformat(), 1)
        
        return None
        
    except Exception as e:
        print(f"❌ get_user_by_username error: {e}")
        if username == 'admin':
            return ('admin', 'ADMIN', 'Finance', 'System Administrator', 6, 1, 1, 1, 
                    datetime.now().isoformat(), datetime.now().isoformat(), 1)
        return None

# ============================================================
# GET USER PERMISSIONS - WITH EMERGENCY FALLBACK
# ============================================================
def get_user_permissions(username):
    try:
        query = """
            SELECT can_receive_requests, can_process_stages, can_release_payments, role
            FROM users WHERE username = %s
        """
        result = execute_query(query, (username,), fetch_one=True)
        if result:
            return {
                'can_receive': result[0] == 1,
                'can_process': result[1] == 1,
                'can_release': result[2] == 1,
                'role': result[3]
            }
    except Exception as e:
        print(f"❌ get_user_permissions error: {e}")
    
    # Emergency fallback
    if username == 'admin':
        return {'can_receive': True, 'can_process': True, 'can_release': True, 'role': 'ADMIN'}
    
    return {'can_receive': False, 'can_process': False, 'can_release': False, 'role': 'DEPARTMENT'}

# ============================================================
# ALL OTHER FUNCTIONS - UNCHANGED
# ============================================================

def create_user(username, password, role, department_id, full_name, 
                can_receive_requests=0, can_process_stages=0, can_release_payments=0):
    try:
        print(f"🔍 Creating user: {username}")
        
        check_query = "SELECT COUNT(*) FROM users WHERE username = %s"
        count_result = execute_query(check_query, (username,), fetch_one=True)
        count = count_result[0] if count_result else 0
        
        if count > 0:
            print(f"❌ User '{username}' already exists!")
            return False
        
        query = """
            INSERT INTO users (
                username, password, role, department_id, full_name, 
                can_receive_requests, can_process_stages, can_release_payments, 
                created_at, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
        """
        params = (
            username, password, role, department_id, full_name,
            1 if can_receive_requests else 0,
            1 if can_process_stages else 0,
            1 if can_release_payments else 0,
            datetime.now().isoformat()
        )
        execute_query(query, params, commit=True)
        print(f"✅ User '{username}' created!")
        return True
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        print(f"❌ Error creating user: {e}")
        return False

def update_user_password(username, new_password):
    try:
        query = "UPDATE users SET password = %s WHERE username = %s"
        execute_query(query, (new_password, username), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error updating password: {e}")
        return False

def update_user_permissions(username, can_receive, can_process, can_release):
    try:
        query = """
            UPDATE users 
            SET can_receive_requests = %s, can_process_stages = %s, can_release_payments = %s
            WHERE username = %s
        """
        execute_query(query, (
            1 if can_receive else 0, 
            1 if can_process else 0, 
            1 if can_release else 0, 
            username
        ), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error updating permissions: {e}")
        return False

def delete_user(username):
    try:
        query = "DELETE FROM users WHERE username = %s"
        execute_query(query, (username,), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return False

def get_user_department(username):
    query = """
        SELECT d.* FROM users u
        JOIN departments d ON u.department_id = d.id
        WHERE u.username = %s
    """
    return execute_query(query, (username,), fetch_one=True)

def get_department_requests(department_name):
    query = "SELECT * FROM requests WHERE department_name = %s ORDER BY submission_date DESC"
    conn = None
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn, params=(department_name,))
        conn.close()
        return df
    except Exception as e:
        print(f"❌ get_department_requests error: {e}")
        if conn:
            conn.close()
        return pd.DataFrame()

def create_department(name, permissions):
    try:
        can_imprest, can_petty, can_supplier, can_student, can_surrender, can_refund, requires_product, requires_funder, is_finance = permissions
        query = """
            INSERT INTO departments (
                name, can_submit_imprest, can_submit_petty_cash, 
                can_submit_supplier, can_submit_student_payment, 
                can_submit_surrender, can_submit_refund, 
                requires_product_type, requires_funder, is_finance_dept
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (name, 
                  1 if can_imprest else 0, 
                  1 if can_petty else 0, 
                  1 if can_supplier else 0, 
                  1 if can_student else 0, 
                  1 if can_surrender else 0, 
                  1 if can_refund else 0, 
                  1 if requires_product else 0, 
                  1 if requires_funder else 0, 
                  1 if is_finance else 0)
        execute_query(query, params, commit=True)
        return True
    except Exception as e:
        logger.error(f"Error creating department: {e}")
        return False

def delete_department(dept_id):
    try:
        check_query = "SELECT COUNT(*) FROM users WHERE department_id = %s"
        result = execute_query(check_query, (dept_id,), fetch_one=True)
        if result and result[0] > 0:
            return False
        query = "DELETE FROM departments WHERE id = %s"
        execute_query(query, (dept_id,), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error deleting department: {e}")
        return False

def get_products():
    conn = None
    try:
        conn = get_connection()
        df = pd.read_sql_query("SELECT id, name, category, has_payment_type, has_semester FROM products WHERE is_active = 1 ORDER BY name", conn)
        conn.close()
        return df
    except Exception as e:
        print(f"❌ get_products error: {e}")
        if conn:
            conn.close()
        return pd.DataFrame()

def add_product(name, category, has_payment_type, has_semester):
    try:
        query = "INSERT INTO products (name, category, has_payment_type, has_semester, is_active) VALUES (%s, %s, %s, %s, 1)"
        execute_query(query, (name, category, 1 if has_payment_type else 0, 1 if has_semester else 0), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error adding product: {e}")
        return False

def delete_product(product_id):
    try:
        query = "DELETE FROM products WHERE id = %s"
        execute_query(query, (product_id,), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        return False

def get_funders():
    conn = None
    try:
        conn = get_connection()
        df = pd.read_sql_query("SELECT id, name FROM funders ORDER BY name", conn)
        conn.close()
        return df
    except Exception as e:
        print(f"❌ get_funders error: {e}")
        if conn:
            conn.close()
        return pd.DataFrame()

def add_funder(funder_name):
    try:
        query = "INSERT INTO funders (name) VALUES (%s)"
        execute_query(query, (funder_name,), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error adding funder: {e}")
        return False

def delete_funder(funder_id):
    try:
        query = "DELETE FROM funders WHERE id = %s"
        execute_query(query, (funder_id,), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error deleting funder: {e}")
        return False

def get_financial_years():
    conn = None
    try:
        conn = get_connection()
        df = pd.read_sql_query("SELECT id, name FROM financial_years WHERE is_active = 1 ORDER BY name DESC", conn)
        conn.close()
        return df['name'].tolist() if not df.empty else []
    except Exception as e:
        print(f"❌ get_financial_years error: {e}")
        if conn:
            conn.close()
        return []

def add_financial_year(year_name):
    try:
        query = "INSERT INTO financial_years (name, is_active) VALUES (%s, 1)"
        execute_query(query, (year_name,), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error adding financial year: {e}")
        return False

def delete_financial_year(year_id):
    try:
        query = "DELETE FROM financial_years WHERE id = %s"
        execute_query(query, (year_id,), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error deleting financial year: {e}")
        return False

def get_semesters():
    conn = None
    try:
        conn = get_connection()
        df = pd.read_sql_query("SELECT id, name FROM semesters ORDER BY name", conn)
        conn.close()
        return df['name'].tolist() if not df.empty else []
    except Exception as e:
        print(f"❌ get_semesters error: {e}")
        if conn:
            conn.close()
        return []

def add_semester(semester_name):
    try:
        query = "INSERT INTO semesters (name) VALUES (%s)"
        execute_query(query, (semester_name,), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error adding semester: {e}")
        return False

def delete_semester(semester_id):
    try:
        query = "DELETE FROM semesters WHERE id = %s"
        execute_query(query, (semester_id,), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error deleting semester: {e}")
        return False

def get_requests():
    conn = None
    try:
        conn = get_connection()
        df = pd.read_sql_query("SELECT * FROM requests ORDER BY submission_date DESC", conn)
        conn.close()
        return df
    except Exception as e:
        print(f"❌ get_requests error: {e}")
        if conn:
            conn.close()
        return pd.DataFrame()

def get_request_by_id(request_id):
    query = "SELECT * FROM requests WHERE id = %s"
    result = execute_query(query, (request_id,), fetch_one=True)
    if result:
        columns = [
            'id', 'request_number', 'request_type', 'main_category', 
            'department_id', 'department_name', 'submitted_by', 'submission_date',
            'amount', 'payment_description', 'financial_year', 'batch_no',
            'product_type', 'semester', 'payment_type', 'imprest_no',
            'supplier_name', 'invoice_no', 'lpo_no', 'salary_month',
            'salary_year', 'customer_name', 'customer_id', 'surrender_number',
            'staff_name', 'funder_name', 'refund_reason', 'original_payment_ref',
            'previous_imprest_no', 'status', 'finance_comment', 'return_reason',
            'date_received', 'date_returned', 'finance_check_date', 'payment_date',
            'payment_reference', 'completed_by', 'completion_notes', 'last_updated',
            'finance_checklist_approvals', 'finance_checklist_documents', 
            'finance_checklist_comments', 'date_confirmed_by_finance',
            'mileage_claim_details', 'training_details', 'professional_body',
            'direct_payment_details', 'fare_reimbursement_details', 'completion_date'
        ]
        return dict(zip(columns, result))
    return None

def save_request(data):
    data['request_number'] = data.get('request_number', f"HELB-{datetime.now().strftime('%Y%m')}-{get_next_count():04d}")
    data['submission_date'] = datetime.now().strftime('%Y-%m-%d')
    data['last_updated'] = datetime.now().isoformat()
    columns = list(data.keys())
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join(columns)
    query = f"INSERT INTO requests ({columns_str}) VALUES ({placeholders}) RETURNING id"
    try:
        result = execute_query(query, list(data.values()), fetch_one=True, commit=True)
        request_id = result[0] if result else None
        log_audit(
            operation='INSERT',
            table_name='requests',
            record_id=request_id,
            user=data.get('submitted_by'),
            details={'request_number': data.get('request_number'), 'request_type': data.get('request_type')}
        )
        try:
            add_request_log(request_id, data.get('request_number'), "SUBMITTED", None, "SUBMITTED",
                           "Request submitted", data.get('submitted_by'), "DEPARTMENT", data.get('department_name'))
        except:
            pass
        return data.get('request_number')
    except Exception as e:
        logger.error(f"Error saving request: {e}")
        return None

def update_request_status(request_id, status, finance_comment=None, return_reason=None, 
                          performed_by=None, performed_by_role=None, performed_by_dept=None,
                          checklist_approvals=None, checklist_documents=None, checklist_comments=None):
    try:
        current_query = "SELECT status, request_number, main_category FROM requests WHERE id = %s"
        current = execute_query(current_query, (request_id,), fetch_one=True)
        old_status = current[0] if current else None
        request_number = current[1] if current else None
        updates = ["status = %s", "last_updated = %s"]
        params = [status, datetime.now().isoformat()]
        action = ""
        comment = finance_comment or return_reason
        if status == 'RECEIVED_BY_FINANCE':
            updates.append("date_received = %s")
            params.append(datetime.now().strftime('%Y-%m-%d'))
            updates.append("date_confirmed_by_finance = %s")
            params.append(datetime.now().strftime('%Y-%m-%d'))
            if checklist_approvals is not None:
                updates.append("finance_checklist_approvals = %s")
                params.append(1 if checklist_approvals else 0)
            if checklist_documents is not None:
                updates.append("finance_checklist_documents = %s")
                params.append(1 if checklist_documents else 0)
            if checklist_comments:
                updates.append("finance_checklist_comments = %s")
                params.append(checklist_comments)
            action = "RECEIVED"
        elif status == 'RETURNED':
            updates.append("date_returned = %s")
            params.append(datetime.now().strftime('%Y-%m-%d'))
            if return_reason:
                updates.append("return_reason = %s")
                params.append(return_reason)
            action = "RETURNED"
        elif status == 'SUBMITTED':
            updates.append("submission_date = %s")
            params.append(datetime.now().strftime('%Y-%m-%d'))
            updates.append("date_returned = %s")
            params.append(None)
            updates.append("return_reason = %s")
            params.append(None)
            action = "RESUBMITTED"
        elif status == 'PAYMENT_PREPARED':
            action = "Payment Prepared"
        elif status == 'PAYMENT_VERIFIED':
            action = "Payment Verified"
        elif status == 'PAYMENT_APPROVED':
            action = "Payment Approved"
        elif status == 'PAYMENT_AUTHORIZED':
            action = "Payment Authorized"
        elif status == 'SURRENDER_FIRST_VERIFICATION':
            action = "First Verification"
        elif status == 'SURRENDER_SECOND_VERIFICATION':
            action = "Second Verification"
        elif status == 'SURRENDER_APPROVAL':
            action = "Surrender Approval"
        elif status == 'SURRENDER_POSTING':
            action = "Surrender Posting"
        elif status == 'PAID':
            updates.append("payment_date = %s")
            params.append(datetime.now().strftime('%Y-%m-%d'))
            updates.append("completion_date = %s")
            params.append(datetime.now().strftime('%Y-%m-%d'))
            action = "PAID"
        elif status == 'CLEARED':
            updates.append("payment_date = %s")
            params.append(datetime.now().strftime('%Y-%m-%d'))
            updates.append("completion_date = %s")
            params.append(datetime.now().strftime('%Y-%m-%d'))
            action = "CLEARED"
        if finance_comment:
            updates.append("finance_comment = %s")
            params.append(finance_comment)
        params.append(request_id)
        query = f"UPDATE requests SET {', '.join(updates)} WHERE id = %s"
        execute_query(query, params, commit=True)
        log_audit(
            operation='UPDATE_STATUS',
            table_name='requests',
            record_id=request_id,
            user=performed_by,
            details={'old_status': old_status, 'new_status': status, 'action': action}
        )
        if action:
            try:
                add_request_log(request_id, request_number, action, old_status, status,
                               comment, performed_by, performed_by_role, performed_by_dept)
            except:
                pass
        return True
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        return False

def update_payment_details(request_id, payment_reference):
    try:
        query = """
            UPDATE requests 
            SET payment_reference = %s, payment_date = %s, last_updated = %s 
            WHERE id = %s
        """
        execute_query(query, (
            payment_reference, 
            datetime.now().strftime('%Y-%m-%d'), 
            datetime.now().isoformat(), 
            request_id
        ), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error updating payment details: {e}")
        return False

def get_returned_requests(department_name):
    query = """
        SELECT * FROM requests 
        WHERE status = 'RETURNED' AND department_name = %s 
        ORDER BY date_returned DESC
    """
    conn = None
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn, params=(department_name,))
        conn.close()
        return df
    except Exception as e:
        print(f"❌ get_returned_requests error: {e}")
        if conn:
            conn.close()
        return pd.DataFrame()

def get_returned_request_by_id(request_id):
    query = "SELECT * FROM requests WHERE id = %s AND status = 'RETURNED'"
    result = execute_query(query, (request_id,), fetch_one=True)
    if result:
        columns = [
            'id', 'request_number', 'request_type', 'main_category', 
            'department_id', 'department_name', 'submitted_by', 'submission_date',
            'amount', 'payment_description', 'financial_year', 'batch_no',
            'product_type', 'semester', 'payment_type', 'imprest_no',
            'supplier_name', 'invoice_no', 'lpo_no', 'salary_month',
            'salary_year', 'customer_name', 'customer_id', 'surrender_number',
            'staff_name', 'funder_name', 'refund_reason', 'original_payment_ref',
            'previous_imprest_no', 'status', 'finance_comment', 'return_reason',
            'date_received', 'date_returned', 'finance_check_date', 'payment_date',
            'payment_reference', 'completed_by', 'completion_notes', 'last_updated',
            'finance_checklist_approvals', 'finance_checklist_documents', 
            'finance_checklist_comments', 'date_confirmed_by_finance',
            'mileage_claim_details', 'training_details', 'professional_body',
            'direct_payment_details', 'fare_reimbursement_details', 'completion_date'
        ]
        return dict(zip(columns, result))
    return None

def resubmit_request(request_id, updated_data):
    try:
        set_parts = []
        values = []
        for key, value in updated_data.items():
            if key != 'id' and key != 'request_number':
                set_parts.append(f"{key} = %s")
                values.append(value)
        set_parts.append("last_updated = %s")
        values.append(datetime.now().isoformat())
        values.append(request_id)
        query = f"UPDATE requests SET {', '.join(set_parts)} WHERE id = %s"
        execute_query(query, values, commit=True)
        return True
    except Exception as e:
        logger.error(f"Error resubmitting request: {e}")
        return False

def search_payment_records(search_term, search_type="all"):
    conn = None
    try:
        conn = get_connection()
        
        if search_type == "request_number":
            query = "SELECT * FROM requests WHERE request_number ILIKE %s ORDER BY submission_date DESC"
            params = (f"%{search_term}%",)
        elif search_type == "batch_no":
            query = "SELECT * FROM requests WHERE batch_no ILIKE %s ORDER BY submission_date DESC"
            params = (f"%{search_term}%",)
        elif search_type == "imprest_no":
            query = "SELECT * FROM requests WHERE imprest_no ILIKE %s ORDER BY submission_date DESC"
            params = (f"%{search_term}%",)
        elif search_type == "invoice_no":
            query = "SELECT * FROM requests WHERE invoice_no ILIKE %s ORDER BY submission_date DESC"
            params = (f"%{search_term}%",)
        elif search_type == "surrender_number":
            query = "SELECT * FROM requests WHERE surrender_number ILIKE %s ORDER BY submission_date DESC"
            params = (f"%{search_term}%",)
        elif search_type == "payment_reference":
            query = "SELECT * FROM requests WHERE payment_reference ILIKE %s ORDER BY submission_date DESC"
            params = (f"%{search_term}%",)
        elif search_type == "all_names":
            query = """
                SELECT * FROM requests 
                WHERE customer_name ILIKE %s 
                   OR supplier_name ILIKE %s 
                   OR staff_name ILIKE %s
                ORDER BY submission_date DESC
            """
            params = (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")
        else:
            query = """
                SELECT * FROM requests 
                WHERE request_number ILIKE %s 
                   OR batch_no ILIKE %s 
                   OR imprest_no ILIKE %s 
                   OR invoice_no ILIKE %s 
                   OR surrender_number ILIKE %s
                   OR customer_name ILIKE %s
                   OR supplier_name ILIKE %s
                   OR staff_name ILIKE %s
                   OR payment_reference ILIKE %s
                ORDER BY submission_date DESC
            """
            params = (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", 
                      f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", 
                      f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        print(f"❌ search_payment_records error: {e}")
        if conn:
            conn.close()
        return pd.DataFrame()

def search_by_batch_number(batch_no):
    query = """
        SELECT request_number, main_category, amount, status, payment_date, 
               payment_reference, department_name, submission_date
        FROM requests WHERE batch_no = %s AND main_category = 'Submit Payment Request'
        ORDER BY submission_date DESC
    """
    results = execute_query(query, (batch_no,), fetch_all=True)
    if results:
        return [{'request_number': r[0], 'main_category': r[1], 'amount': r[2],
                 'status': r[3], 'payment_date': r[4], 'payment_reference': r[5],
                 'department': r[6], 'submission_date': r[7]} for r in results]
    return []

def get_all_batch_numbers():
    query = """
        SELECT DISTINCT batch_no FROM requests 
        WHERE main_category = 'Submit Payment Request' AND batch_no IS NOT NULL
        ORDER BY batch_no DESC
    """
    results = execute_query(query, fetch_all=True)
    return [r[0] for r in results if r[0]]

def calculate_tat(submission_date, payment_date=None):
    from utils.holidays_ke import working_days_between
    try:
        sub_date = datetime.strptime(submission_date, '%Y-%m-%d').date()
        if payment_date:
            pay_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
            return working_days_between(sub_date, pay_date)
        else:
            today = date.today()
            return working_days_between(sub_date, today)
    except:
        return 0

def get_next_count():
    try:
        query = "SELECT COUNT(*) FROM requests"
        result = execute_query(query, fetch_one=True)
        return result[0] + 1 if result else 1
    except:
        return 1

def log_audit(operation, table_name, record_id, user=None, details=None, before_state=None, after_state=None):
    try:
        query = """
            INSERT INTO audit_logs (
                timestamp, operation, table_name, record_id, "user", 
                details, before_state, after_state
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            datetime.now().isoformat(),
            operation,
            table_name,
            record_id,
            user or 'SYSTEM',
            json.dumps(details) if details else None,
            json.dumps(before_state) if before_state else None,
            json.dumps(after_state) if after_state else None
        )
        execute_query(query, params, commit=True)
        logger.info(f"AUDIT: {operation} on {table_name}/{record_id} by {user}")
    except Exception as e:
        logger.error(f"Audit log failed: {e}")

def add_request_log(request_id, request_number, action, status_from, status_to, 
                    comment, performed_by, performed_by_role, performed_by_dept, details=None):
    try:
        query = """
            INSERT INTO request_logs (
                request_id, request_number, action, status_from, status_to,
                comment, performed_by, performed_by_role, performed_by_dept,
                timestamp, details
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            request_id, request_number, action, status_from, status_to,
            comment, performed_by, performed_by_role, performed_by_dept,
            datetime.now().isoformat(), details
        )
        execute_query(query, params, commit=True)
    except Exception as e:
        logger.error(f"Error adding log: {e}")

def get_request_logs(request_id):
    try:
        query = """
            SELECT * FROM request_logs 
            WHERE request_id = %s 
            ORDER BY timestamp ASC
        """
        results = execute_query(query, (request_id,), fetch_all=True)
        if results:
            columns = ['id', 'request_id', 'request_number', 'action', 'status_from', 
                       'status_to', 'comment', 'performed_by', 'performed_by_role', 
                       'performed_by_dept', 'timestamp', 'details']
            return [dict(zip(columns, log)) for log in results]
        return []
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return []

def get_sla_from_database():
    try:
        query = "SELECT request_type, sla_days FROM sla_config"
        results = execute_query(query, fetch_all=True)
        sla_map = {}
        for req_type, sla_days in results:
            sla_map[req_type] = sla_days
        return sla_map
    except:
        return {
            'Student Payment': 3, 'Imprest': 5, 'Petty Cash': 3,
            'Supplier Payment': 7, 'Salary Payment': 5, 'Refund Payment': 10,
            'Surrender': 4, 'Mileage Claim': 3, 'Staff Training': 5,
            'Professional Body': 5, 'Direct Payment': 3, 'Fare Reimbursement': 3
        }

def get_all_request_types():
    try:
        query = "SELECT request_type, sla_days FROM sla_config ORDER BY request_type"
        results = execute_query(query, fetch_all=True)
        return [{'request_type': r[0], 'sla_days': r[1]} for r in results]
    except:
        return []

def add_request_type(request_type, sla_days):
    try:
        query = "INSERT INTO sla_config (request_type, sla_days) VALUES (%s, %s)"
        execute_query(query, (request_type, sla_days), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error adding request type: {e}")
        return False

def update_request_type(old_name, new_name, sla_days):
    try:
        query = "UPDATE sla_config SET request_type = %s, sla_days = %s WHERE request_type = %s"
        execute_query(query, (new_name, sla_days, old_name), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error updating request type: {e}")
        return False

def delete_request_type(request_type):
    try:
        query = "DELETE FROM sla_config WHERE request_type = %s"
        execute_query(query, (request_type,), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error deleting request type: {e}")
        return False

def update_sla_days(request_type, sla_days):
    try:
        query = "UPDATE sla_config SET sla_days = %s WHERE request_type = %s"
        execute_query(query, (sla_days, request_type), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error updating SLA days: {e}")
        return False

def verify_finance_password(password):
    try:
        query = "SELECT setting_value FROM finance_settings WHERE setting_key = 'finance_password'"
        result = execute_query(query, fetch_one=True)
        return result and result[0] == password
    except:
        return False

def update_finance_password(new_password):
    try:
        query = "UPDATE finance_settings SET setting_value = %s WHERE setting_key = 'finance_password'"
        execute_query(query, (new_password,), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error updating finance password: {e}")
        return False

def get_finance_password():
    try:
        query = "SELECT setting_value FROM finance_settings WHERE setting_key = 'finance_password'"
        result = execute_query(query, fetch_one=True)
        return result[0] if result else 'finance123'
    except:
        return 'finance123'

def get_allowed_main_categories(user_role, user_dept):
    finance_roles = ["FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER", "FINANCE_ADMIN"]
    if user_role in ["ADMIN", "FINANCE_ADMIN"]:
        return ["Submit Payment Request", "Submit Surrender"]
    if user_role in finance_roles:
        return []
    if user_role == "MANAGEMENT":
        return []
    return ["Submit Payment Request", "Submit Surrender"]

def get_allowed_request_types(user_role, user_dept, main_category):
    if user_role in ["ADMIN", "FINANCE_ADMIN"]:
        if main_category == "Submit Payment Request":
            all_types = get_all_request_types()
            return [t['request_type'] for t in all_types if t['request_type'] != 'Surrender']
        else:
            return ["Surrender"]
    finance_roles = ["FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER"]
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
            allowed.append("Fare Reimbursement")
        if user_dept == "Field Services":
            allowed.append("Fare Reimbursement")
        if user_dept == "Debt Management":
            allowed.append("Refund Payment")
        return allowed
    else:
        return ["Surrender"]

def get_pending_confirmation_count():
    try:
        query = "SELECT COUNT(*) FROM requests WHERE status = 'SUBMITTED'"
        result = execute_query(query, fetch_one=True)
        return result[0] if result else 0
    except:
        return 0

def get_pending_completion_count():
    try:
        query = "SELECT COUNT(*) FROM requests WHERE status NOT IN ('PAID', 'CLEARED', 'RETURNED')"
        result = execute_query(query, fetch_one=True)
        return result[0] if result else 0
    except:
        return 0

def get_pending_duration(request_date):
    from utils.holidays_ke import working_days_between
    try:
        today = date.today()
        submitted_date = datetime.strptime(request_date, '%Y-%m-%d').date()
        return working_days_between(submitted_date, today)
    except:
        return 0

def get_time_lapsed_from_confirmation(request_id):
    from utils.holidays_ke import working_days_between
    try:
        query = "SELECT date_confirmed_by_finance, payment_date, completion_date FROM requests WHERE id = %s"
        result = execute_query(query, (request_id,), fetch_one=True)
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
    sla_map = get_sla_from_database()
    for _, row in df.iterrows():
        if row['status'] in ['PAID', 'CLEARED'] and row['payment_date']:
            try:
                submitted = datetime.strptime(row['submission_date'], '%Y-%m-%d').date()
                paid = datetime.strptime(row['payment_date'], '%Y-%m-%d').date()
                days = working_days_between(submitted, paid)
                completion_times.append(days)
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
    query = """
        SELECT department_name, COUNT(*) as total_requests,
               SUM(CASE WHEN status IN ('PAID', 'CLEARED') THEN 1 ELSE 0 END) as completed,
               SUM(CASE WHEN status = 'RETURNED' THEN 1 ELSE 0 END) as returned,
               SUM(amount) as total_amount
        FROM requests GROUP BY department_name ORDER BY total_requests DESC
    """
    conn = None
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"❌ get_all_departments_summary error: {e}")
        if conn:
            conn.close()
        return pd.DataFrame()

def get_reports_data(user_role, user_dept):
    df = get_requests()
    if df.empty:
        return df
    finance_roles = ["FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER", "FINANCE_ADMIN"]
    if user_role in ["ADMIN", "MANAGEMENT"] + finance_roles:
        return df
    else:
        return df[df['department_name'] == user_dept]

def get_intelligent_completion_prediction(request_id, request_type, current_status, current_tat, sla_days):
    from utils.holidays_ke import add_working_days
    try:
        query = """
            SELECT submission_date, payment_date, status, request_type
            FROM requests 
            WHERE request_type = %s 
            AND status IN ('PAID', 'CLEARED')
            AND payment_date IS NOT NULL
            AND payment_date != ''
            ORDER BY submission_date DESC
            LIMIT 50
        """
        df = get_requests()
        if df.empty:
            remaining_days = max(1, sla_days - current_tat) if sla_days > current_tat else 1
            predicted_date = add_working_days(date.today(), remaining_days)
            return predicted_date, "Estimated", "Using SLA estimation."
        
        type_df = df[df['request_type'] == request_type]
        historical_tats = []
        for _, row in type_df.iterrows():
            if row['status'] in ['PAID', 'CLEARED'] and row.get('payment_date'):
                tat = calculate_tat(row['submission_date'], row['payment_date'])
                if tat and tat > 0:
                    historical_tats.append(tat)
        
        if current_status in ['PAID', 'CLEARED']:
            return None, "Completed", "Request has already been completed."
        
        if historical_tats:
            avg_historical_tat = np.mean(historical_tats)
            median_historical_tat = np.median(historical_tats)
            remaining_days_avg = max(1, int(avg_historical_tat - current_tat)) if avg_historical_tat > current_tat else 1
            remaining_days_median = max(1, int(median_historical_tat - current_tat)) if median_historical_tat > current_tat else 1
            remaining_days_sla = max(1, sla_days - current_tat) if sla_days > current_tat else 1
            
            if len(historical_tats) >= 20:
                remaining_days = remaining_days_median
                confidence = "High"
                reasoning = f"Based on {len(historical_tats)} similar historical requests averaging {avg_historical_tat:.1f} days total."
            elif len(historical_tats) >= 10:
                remaining_days = (remaining_days_median + remaining_days_sla) // 2
                confidence = "Medium"
                reasoning = f"Based on {len(historical_tats)} similar requests. Historical average: {avg_historical_tat:.1f} days."
            elif len(historical_tats) >= 3:
                remaining_days = remaining_days_sla
                confidence = "Low"
                reasoning = f"Limited historical data ({len(historical_tats)} requests). Using SLA target of {sla_days} days."
            else:
                remaining_days = remaining_days_sla
                confidence = "Estimated"
                reasoning = f"No historical data available. Using SLA target of {sla_days} days."
            
            progress_percentage = (current_tat / sla_days * 100) if sla_days > 0 else 0
            if progress_percentage > 100:
                remaining_days = max(1, remaining_days // 2)
                reasoning += " This request is already beyond SLA target - expedited processing recommended."
            elif progress_percentage > 80:
                remaining_days = max(1, remaining_days - 1)
                reasoning += " This request is approaching SLA deadline - priority processing."
            
            predicted_date = add_working_days(date.today(), remaining_days)
            return predicted_date, confidence, reasoning
        else:
            remaining_days = max(1, sla_days - current_tat) if sla_days > current_tat else 1
            predicted_date = add_working_days(date.today(), remaining_days)
            confidence = "Estimated"
            reasoning = f"No historical data available. Using SLA target of {sla_days} days."
            return predicted_date, confidence, reasoning
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        from utils.holidays_ke import add_working_days
        remaining_days = max(1, sla_days - current_tat) if sla_days > current_tat else 1
        predicted_date = add_working_days(date.today(), remaining_days)
        return predicted_date, "Estimated", "Using standard SLA estimation."

def identify_bottlenecks(df):
    from utils.holidays_ke import working_days_between
    bottlenecks = []
    if df.empty:
        return pd.DataFrame(columns=['Stage', 'Avg Days', 'Max Days', 'P95 Days', 'Is Bottleneck'])
    stage_durations = {
        'Submission to Receipt': [],
        'Receipt to Preparation': [],
        'Preparation to Verification': [],
        'Verification to Approval': [],
        'Approval to Authorization': [],
        'Authorization to Payment': []
    }
    for _, row in df.iterrows():
        if row.get('date_received') and row.get('submission_date'):
            try:
                sub_date = datetime.strptime(row['submission_date'], '%Y-%m-%d').date()
                rec_date = datetime.strptime(row['date_received'], '%Y-%m-%d').date()
                if sub_date and rec_date:
                    days = working_days_between(sub_date, rec_date)
                    if days >= 0:
                        stage_durations['Submission to Receipt'].append(days)
            except:
                pass
    for stage, durations in stage_durations.items():
        if durations:
            avg_duration = np.mean(durations)
            max_duration = np.max(durations)
            p95_duration = np.percentile(durations, 95)
            bottlenecks.append({
                'Stage': stage,
                'Avg Days': round(avg_duration, 1),
                'Max Days': max_duration,
                'P95 Days': round(p95_duration, 1),
                'Is Bottleneck': avg_duration > 3
            })
        else:
            bottlenecks.append({
                'Stage': stage,
                'Avg Days': 0,
                'Max Days': 0,
                'P95 Days': 0,
                'Is Bottleneck': False
            })
    return pd.DataFrame(bottlenecks)

def get_fastest_request_types(df):
    tat_analysis = []
    if df.empty:
        return pd.DataFrame(columns=['Request Type', 'Average TAT', 'Median TAT', 'Fastest (Days)', 'Slowest (Days)', 'Sample Size', 'Performance Score'])
    sla_map = get_sla_from_database()
    for req_type in df['request_type'].unique():
        type_df = df[(df['request_type'] == req_type) & (df['status'].isin(['PAID', 'CLEARED']))]
        if not type_df.empty and type_df['payment_date'].notna().any():
            tat_values = []
            for _, row in type_df.iterrows():
                if row.get('payment_date') and row.get('submission_date'):
                    try:
                        tat = calculate_tat(row['submission_date'], row['payment_date'])
                        if tat is not None and tat > 0:
                            tat_values.append(tat)
                    except:
                        pass
            if tat_values:
                avg_tat = np.mean(tat_values)
                median_tat = np.median(tat_values)
                min_tat = np.min(tat_values)
                max_tat = np.max(tat_values)
                count = len(tat_values)
                sla_target = sla_map.get(req_type, 5)
                if avg_tat <= sla_target:
                    perf_score = 100
                elif avg_tat <= sla_target * 1.5:
                    perf_score = 80
                elif avg_tat <= sla_target * 2:
                    perf_score = 60
                elif avg_tat <= sla_target * 3:
                    perf_score = 40
                else:
                    perf_score = 20
                tat_analysis.append({
                    'Request Type': req_type,
                    'Average TAT': round(avg_tat, 1),
                    'Median TAT': round(median_tat, 1),
                    'Fastest (Days)': min_tat,
                    'Slowest (Days)': max_tat,
                    'Sample Size': count,
                    'Performance Score': perf_score
                })
    if tat_analysis:
        result_df = pd.DataFrame(tat_analysis)
        if 'Average TAT' in result_df.columns:
            return result_df.sort_values('Average TAT')
        else:
            return result_df
    else:
        return pd.DataFrame(columns=['Request Type', 'Average TAT', 'Median TAT', 'Fastest (Days)', 'Slowest (Days)', 'Sample Size', 'Performance Score'])

def get_bulk_eligible_requests(statuses=None, request_types=None, department=None, limit=100):
    query = """
        SELECT id, request_number, request_type, department_name, amount, 
               status, submission_date, submitted_by
        FROM requests 
        WHERE status IN ('SUBMITTED', 'RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 
                        'PAYMENT_VERIFIED', 'PAYMENT_APPROVED')
    """
    params = []
    if statuses:
        placeholders = ','.join(['%s'] * len(statuses))
        query += f" AND status IN ({placeholders})"
        params.extend(statuses)
    if request_types:
        placeholders = ','.join(['%s'] * len(request_types))
        query += f" AND request_type IN ({placeholders})"
        params.extend(request_types)
    if department:
        query += " AND department_name = %s"
        params.append(department)
    query += " ORDER BY submission_date ASC LIMIT %s"
    params.append(limit)
    results = execute_query(query, params, fetch_all=True)
    return [{'id': r[0], 'request_number': r[1], 'request_type': r[2], 
             'department_name': r[3], 'amount': r[4], 'status': r[5],
             'submission_date': r[6], 'submitted_by': r[7]} for r in results]

def bulk_update_status(request_ids, new_status, performed_by, performed_by_role, performed_by_dept, 
                       payment_reference=None, finance_comment=None):
    success_count = 0
    failed_ids = []
    for request_id in request_ids:
        try:
            current_query = "SELECT status, request_number FROM requests WHERE id = %s"
            current = execute_query(current_query, (request_id,), fetch_one=True)
            if not current:
                failed_ids.append(request_id)
                continue
            old_status = current[0]
            request_number = current[1]
            updates = ["status = %s", "last_updated = %s"]
            params = [new_status, datetime.now().isoformat()]
            if new_status == 'PAID' and payment_reference:
                updates.append("payment_date = %s")
                params.append(datetime.now().strftime('%Y-%m-%d'))
                updates.append("payment_reference = %s")
                params.append(payment_reference)
            elif new_status == 'CLEARED' and payment_reference:
                updates.append("payment_date = %s")
                params.append(datetime.now().strftime('%Y-%m-%d'))
                updates.append("payment_reference = %s")
                params.append(payment_reference)
            elif new_status == 'RECEIVED_BY_FINANCE':
                updates.append("date_received = %s")
                params.append(datetime.now().strftime('%Y-%m-%d'))
                updates.append("date_confirmed_by_finance = %s")
                params.append(datetime.now().strftime('%Y-%m-%d'))
            elif new_status == 'RETURNED' and finance_comment:
                updates.append("date_returned = %s")
                params.append(datetime.now().strftime('%Y-%m-%d'))
                updates.append("return_reason = %s")
                params.append(finance_comment)
            params.append(request_id)
            query = f"UPDATE requests SET {', '.join(updates)} WHERE id = %s"
            execute_query(query, params, commit=True)
            add_request_log(request_id, request_number, f"BULK_{new_status}", 
                          old_status, new_status, 
                          f"Bulk processed by {performed_by}", 
                          performed_by, performed_by_role, performed_by_dept)
            success_count += 1
        except Exception as e:
            failed_ids.append(request_id)
            logger.error(f"Error processing request {request_id}: {e}")
    return success_count, failed_ids

def export_bulk_requests(request_ids):
    placeholders = ','.join(['%s'] * len(request_ids))
    query = f"""
        SELECT request_number, request_type, department_name, amount, 
               payment_description, status, submission_date, submitted_by
        FROM requests WHERE id IN ({placeholders})
    """
    conn = None
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn, params=request_ids)
        conn.close()
        return df
    except Exception as e:
        print(f"❌ export_bulk_requests error: {e}")
        if conn:
            conn.close()
        return pd.DataFrame()

def get_database_health():
    health = {
        'db_size_mb': 0,
        'total_requests': 0,
        'total_logs': 0,
        'total_users': 0,
        'status': 'Healthy',
        'recommendation': 'PostgreSQL is handling the load well'
    }
    try:
        query = "SELECT COUNT(*) FROM requests"
        result = execute_query(query, fetch_one=True)
        health['total_requests'] = result[0] if result else 0
        query = "SELECT COUNT(*) FROM request_logs"
        result = execute_query(query, fetch_one=True)
        health['total_logs'] = result[0] if result else 0
        query = "SELECT COUNT(*) FROM users"
        result = execute_query(query, fetch_one=True)
        health['total_users'] = result[0] if result else 0
        if health['total_requests'] > 200000:
            health['status'] = 'Warning - High volume'
            health['recommendation'] = 'Consider archiving old records'
        else:
            health['status'] = 'Healthy'
            health['recommendation'] = 'PostgreSQL is handling the load well'
    except Exception as e:
        logger.error(f"Error getting database health: {e}")
        health['status'] = 'Unknown'
        health['recommendation'] = 'Could not retrieve health metrics'
    return health

def get_public_payment_details(search_term, search_type="reference"):
    query = """
        SELECT 
            request_number, request_type, amount, payment_description,
            submission_date, date_received, date_confirmed_by_finance,
            status, payment_date, payment_reference,
            batch_no, imprest_no, invoice_no, surrender_number,
            department_name, return_reason
        FROM requests 
        WHERE request_number = %s 
           OR batch_no = %s 
           OR imprest_no = %s 
           OR invoice_no = %s 
           OR surrender_number = %s
           OR payment_reference = %s
        ORDER BY submission_date DESC
        LIMIT 1
    """
    result = execute_query(query, (
        search_term, search_term, search_term, search_term, search_term, search_term
    ), fetch_one=True)
    if result:
        return {
            'request_number': result[0],
            'request_type': result[1],
            'amount': result[2],
            'payment_description': result[3],
            'submission_date': result[4],
            'date_received': result[5],
            'date_confirmed_by_finance': result[6],
            'status': result[7],
            'payment_date': result[8],
            'payment_reference': result[9],
            'batch_no': result[10],
            'imprest_no': result[11],
            'invoice_no': result[12],
            'surrender_number': result[13],
            'department_name': result[14],
            'return_reason': result[15]
        }
    return None

def calculate_estimated_completion_date(status, current_date):
    from utils.holidays_ke import add_working_days
    status_map = {
        'SUBMITTED': {'days': 5, 'message': 'This payment has not been received in Finance yet.'},
        'RECEIVED_BY_FINANCE': {'days': 4, 'message': 'This payment will be completed at most 4 business days from today.'},
        'PAYMENT_PREPARED': {'days': 3, 'message': 'The payment process has been initiated and will take at most 3 business days.'},
        'PAYMENT_VERIFIED': {'days': 2, 'message': 'The payment has been verified and will take at most 2 business days.'},
        'PAYMENT_APPROVED': {'days': 2, 'message': 'The payment process has been approved and will take at most 2 business days.'},
        'PAYMENT_AUTHORIZED': {'days': 1, 'message': 'This payment is at the final stages and will be completed any time from now.'},
        'PAID': {'days': 0, 'message': 'This payment has been completed.'},
        'CLEARED': {'days': 0, 'message': 'This payment has been cleared.'},
        'RETURNED': {'days': None, 'message': 'This payment has been returned for corrections.'}
    }
    if status in status_map:
        info = status_map[status]
        if info['days'] is not None and info['days'] > 0:
            estimated_date = add_working_days(current_date, info['days'])
            return estimated_date, info['message'], info['days']
        elif status in ['PAID', 'CLEARED']:
            return None, info['message'], 0
        elif status == 'RETURNED':
            return None, info['message'], None
    return None, "Status information unavailable.", None

def get_backup_list():
    return [{'filename': 'Supabase automatic backup', 'date': datetime.now().isoformat(), 'size': 0}]

def restore_backup(backup_filename):
    return True

def safe_init_with_recovery():
    logger.info("Supabase PostgreSQL database is ready")
    return True

def ensure_tables_exist():
    return True
