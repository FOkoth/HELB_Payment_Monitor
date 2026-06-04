import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from database import (
    init_database, get_requests, save_request, update_request_status, 
    authenticate_user, get_user_department, get_products, get_funders,
    get_all_users, create_user, create_department, get_departments,
    get_financial_years, get_semesters, add_product,
    update_user_password, get_user_by_username, get_pending_duration,
    update_payment_details, get_department_requests, get_management_dashboard_stats,
    get_trend_data, get_all_departments_summary, search_by_batch_number,
    get_all_batch_numbers, get_allowed_main_categories, get_allowed_request_types, 
    get_reports_data, get_returned_requests, resubmit_request, get_request_logs, 
    add_request_log, get_pending_confirmation_count, get_pending_completion_count,
    get_time_lapsed_from_confirmation
)
from utils.holidays_ke import working_days_between
from streamlit_option_menu import option_menu

# Page config
st.set_page_config(
    page_title="HELB Payment & Surrender Monitoring System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    :root {
        --helb-green: #00843D;
        --helb-gold: #FFB81C;
        --helb-blue: #00529B;
        --helb-red: #DC3545;
    }
    .stButton > button {
        background-color: #00843D;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #00529B;
        color: white;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    h1, h2, h3 {
        color: #00843D;
    }
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    .stForm {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .user-info {
        text-align: center;
        padding: 0.5rem;
        background-color: #e8f5e9;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .log-entry {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 5px;
        font-size: 0.9rem;
    }
    .log-submitted { background-color: #e3f2fd; border-left: 3px solid #2196F3; }
    .log-received { background-color: #e8f5e9; border-left: 3px solid #4CAF50; }
    .log-returned { background-color: #ffebee; border-left: 3px solid #f44336; }
    .log-resubmitted { background-color: #fff3e0; border-left: 3px solid #FF9800; }
    .log-paid { background-color: #e8f5e9; border-left: 3px solid #00843D; }
    .log-confirmed { background-color: #e0f7fa; border-left: 3px solid #00BCD4; }
    .status-paid { background-color: #00843D20; color: #00843D; padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: bold; }
    .status-cleared { background-color: #00843D20; color: #00843D; padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: bold; }
    .status-pending { background-color: #DC354520; color: #DC3545; padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: bold; }
    .status-confirmed { background-color: #00BCD420; color: #00BCD4; padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: bold; }
    .pending-badge { background-color: #DC3545; color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }
    .warning-badge { background-color: #FFB81C; color: #1E1E1E; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Initialize database
init_database()

# Session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_dept' not in st.session_state:
    st.session_state.user_dept = None
if 'user_dept_id' not in st.session_state:
    st.session_state.user_dept_id = None
if 'is_finance' not in st.session_state:
    st.session_state.is_finance = False
if 'full_name' not in st.session_state:
    st.session_state.full_name = None
if 'show_password_change' not in st.session_state:
    st.session_state.show_password_change = False

# Login Screen
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style='text-align: center; padding: 2rem;'>
                <h1 style='color: #00843D;'>🎓 HELB Loans Board</h1>
                <h3 style='color: #FFB81C;'>Payment & Surrender Monitoring System</h3>
                <hr>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                user = authenticate_user(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user_role = user[1]
                    st.session_state.username = user[0]
                    st.session_state.user_dept = user[2] if user[2] else "No Department"
                    st.session_state.user_dept_id = user[4] if user[4] else None
                    st.session_state.is_finance = user[5] == 1 if len(user) > 5 else False
                    st.session_state.full_name = user[3]
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
    st.stop()

# Password Change
if st.session_state.show_password_change:
    st.markdown("### 🔐 Change Your Password")
    st.info("Please change your default password for security reasons.")
    
    with st.form("change_password_form"):
        current_pwd = st.text_input("Current Password", type="password")
        new_pwd = st.text_input("New Password", type="password")
        confirm_pwd = st.text_input("Confirm New Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Update Password"):
                if new_pwd == confirm_pwd and len(new_pwd) >= 4:
                    user = authenticate_user(st.session_state.username, current_pwd)
                    if user:
                        update_user_password(st.session_state.username, new_pwd)
                        st.success("✅ Password updated successfully!")
                        st.session_state.show_password_change = False
                        st.rerun()
                    else:
                        st.error("❌ Current password is incorrect")
                else:
                    st.error("❌ Passwords do not match or are too short (min 4 characters)")
        with col2:
            if st.form_submit_button("Skip for Now"):
                st.session_state.show_password_change = False
                st.rerun()
    st.stop()

# Sidebar
with st.sidebar:
    st.markdown("<h2 style='color: #00843D; text-align: center;'>HELB</h2>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='user-info'>
            <strong>{st.session_state.full_name}</strong><br>
            <span style='color: #00843D;'>{st.session_state.user_role}</span><br>
            <span style='font-size: 0.8rem;'>{st.session_state.user_dept}</span>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    menu_options = []
    if st.session_state.user_role == "MANAGEMENT":
        menu_options = ["📈 Management Dashboard", "🔍 Check Payment Status", "📑 Reports", "🔐 Change Password"]
    elif st.session_state.user_role == "ADMIN":
        menu_options = ["📊 Department Dashboard", "📈 Management Dashboard", "🔍 Check Payment Status", 
                       "📝 New Request", "📋 My Requests", "↩️ Returned Requests", "✅ Approval Queue", 
                       "📑 Reports", "⚙️ Admin Panel", "🔐 Change Password"]
    else:
        menu_options = ["📊 Department Dashboard", "🔍 Check Payment Status", "📝 New Request", 
                       "📋 My Requests", "↩️ Returned Requests", "✅ Approval Queue", "📑 Reports", "🔐 Change Password"]
    
    choice = option_menu(
        menu_title="Menu",
        options=menu_options,
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important"},
            "icon": {"color": "#00843D"},
            "nav-link-selected": {"background-color": "#00843D"},
        }
    )
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()


def display_transaction_logs(request_id):
    logs = get_request_logs(request_id)
    if logs:
        for log in logs:
            timestamp = datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %H:%M')
            action = log['action']
            if action == 'SUBMITTED':
                st.markdown(f"<div class='log-entry log-submitted'>📝 **{timestamp}** - Submitted by {log['performed_by']} ({log['performed_by_dept']})</div>", unsafe_allow_html=True)
            elif action == 'CONFIRMED':
                st.markdown(f"<div class='log-entry log-confirmed'>✅ **{timestamp}** - Confirmed by {log['performed_by']} (Finance)</div>", unsafe_allow_html=True)
            elif action == 'RETURNED':
                st.markdown(f"<div class='log-entry log-returned'>↩️ **{timestamp}** - Returned by {log['performed_by']} - Reason: {log['comment']}</div>", unsafe_allow_html=True)
            elif action == 'RESUBMITTED':
                st.markdown(f"<div class='log-entry log-resubmitted'>📤 **{timestamp}** - Resubmitted by {log['performed_by']}</div>", unsafe_allow_html=True)
            elif action in ['PAID', 'CLEARED']:
                st.markdown(f"<div class='log-entry log-paid'>✅ **{timestamp}** - {action} by {log['performed_by']}</div>", unsafe_allow_html=True)
    else:
        st.info("No transaction logs available")


# ================================================================
# DEPARTMENT DASHBOARD
# ================================================================
if choice == "📊 Department Dashboard":
    st.markdown("<h1 style='color: #00843D;'>📊 Department Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(f"<p>Viewing data for: <strong>{st.session_state.user_dept}</strong></p>", unsafe_allow_html=True)
    
    df = get_department_requests(st.session_state.user_dept)
    if df.empty:
        st.info("No requests found for your department.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        total = len(df)
        pending = len(df[df['status'].isin(['SUBMITTED', 'CONFIRMED_BY_FINANCE'])])
        completed = len(df[df['status'].isin(['PAID', 'CLEARED'])])
        total_amount = df['amount'].sum()
        with col1:
            st.metric("Total Requests", total)
        with col2:
            st.metric("Pending", pending)
        with col3:
            st.metric("Completed", completed)
        with col4:
            st.metric("Total Amount", f"KES {total_amount:,.0f}")
        
        st.markdown("---")
        st.subheader("📋 Recent Requests")
        for _, row in df.head(10).iterrows():
            status_display = "✅ Paid" if row['status'] == 'PAID' else "✅ Cleared" if row['status'] == 'CLEARED' else "⏳ Pending"
            with st.expander(f"📄 {row['request_number']} - {row['request_type']}"):
                st.write(f"**Amount:** KES {row['amount']:,.2f}")
                st.write(f"**Submitted:** {row['submission_date']}")
                st.write(f"**Status:** {status_display}")
                st.markdown("---")
                st.subheader("📜 Transaction Logs")
                display_transaction_logs(row['id'])


# ================================================================
# MANAGEMENT DASHBOARD
# ================================================================
elif choice == "📈 Management Dashboard":
    st.markdown("<h1 style='color: #00843D;'>📈 Management Dashboard</h1>", unsafe_allow_html=True)
    df = get_requests()
    if df.empty:
        st.info("No data available")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Requests", len(df))
        with col2:
            st.metric("Pending", len(df[df['status'].isin(['SUBMITTED', 'CONFIRMED_BY_FINANCE'])]))
        with col3:
            st.metric("Completed", len(df[df['status'].isin(['PAID', 'CLEARED'])]))
        with col4:
            st.metric("Total Amount", f"KES {df['amount'].sum():,.0f}")
        
        st.markdown("---")
        st.subheader("📋 All Requests")
        st.dataframe(df[['request_number', 'request_type', 'department_name', 'amount', 'status', 'submission_date']], use_container_width=True)


# ================================================================
# CHECK PAYMENT STATUS
# ================================================================
elif choice == "🔍 Check Payment Status":
    st.markdown("<h1 style='color: #00843D;'>🔍 Check Payment Status</h1>", unsafe_allow_html=True)
    batch_no = st.text_input("Enter Batch Number")
    if st.button("Search"):
        results = search_by_batch_number(batch_no)
        if results:
            for result in results:
                st.success(f"✅ Request {result['request_number']} - Status: {result['status']}")
        else:
            st.error("No records found")


# ================================================================
# NEW REQUEST - THE FIXED VERSION
# ================================================================
elif choice == "📝 New Request":
    st.markdown("<h1 style='color: #00843D;'>📝 Create New Request</h1>", unsafe_allow_html=True)
    
    allowed_main_categories = get_allowed_main_categories(st.session_state.user_role, st.session_state.user_dept)
    
    if not allowed_main_categories:
        st.error("Your role does not have permission to submit requests.")
    else:
        # Step 1: Select Main Category
        main_category = st.radio("What would you like to do?", allowed_main_categories, horizontal=True)
        st.markdown("---")
        
        # Step 2: Select Request Type
        allowed_types = get_allowed_request_types(st.session_state.user_role, st.session_state.user_dept, main_category)
        
        if not allowed_types:
            st.error("No request types available.")
        else:
            selected_type = st.selectbox("Select Request Type", allowed_types)
            st.markdown("---")
            
            # ============================================================
            # STUDENT PAYMENT - WITH PRODUCT TYPE OUTSIDE THE FORM
            # ============================================================
            if main_category == "Submit Payment Request" and selected_type == "Student Payment":
                st.subheader("🎓 Student Payment Details")
                
                # PRODUCT TYPE SELECTION - OUTSIDE THE FORM (this makes it dynamic)
                products = get_products()
                if not products.empty:
                    product_list = products['name'].tolist()
                else:
                    product_list = ["Undergraduate", "TVET", "Jielimishe"]
                
                product_type = st.selectbox("Product Type", product_list, key="student_product_select")
                
                st.markdown("---")
                
                # Now the form with conditional fields
                with st.form(key="student_payment_form"):
                    # Common fields
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                    payment_description = st.text_area("Payment Description")
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    
                    st.markdown("---")
                    
                    # Conditional fields based on Product Type
                    semester = None
                    payment_category = None
                    
                    if product_type == "Undergraduate":
                        st.markdown("**Undergraduate Payment Details**")
                        semesters = get_semesters()
                        semester = st.selectbox("Semester", semesters if semesters else ["Semester 1", "Semester 2"])
                        payment_category = st.selectbox("Payment Category", ["Tuition", "Upkeep"])
                    
                    elif product_type == "TVET":
                        st.markdown("**TVET Payment Details**")
                        semesters = get_semesters()
                        semester = st.selectbox("Semester", semesters if semesters else ["Semester 1", "Semester 2"])
                        payment_category = st.selectbox("Payment Category", ["Tuition", "Upkeep"])
                    
                    else:
                        # Jielimishe - NO fields shown
                        semester = None
                        payment_category = "Tuition"
                    
                    # Batch Number for all
                    batch_no = st.text_input("Batch No.", placeholder="Enter batch number")
                    
                    submitted = st.form_submit_button("Submit Request", use_container_width=True)
                    
                    if submitted:
                        errors = []
                        if amount <= 0:
                            errors.append("Amount must be greater than 0")
                        if not payment_description:
                            errors.append("Payment Description is required")
                        if not batch_no:
                            errors.append("Batch No. is required")
                        if product_type in ["Undergraduate", "TVET"]:
                            if not semester:
                                errors.append("Semester is required")
                            if not payment_category:
                                errors.append("Payment Category is required")
                        
                        if errors:
                            for error in errors:
                                st.error(f"❌ {error}")
                        else:
                            request_data = {
                                'main_category': main_category,
                                'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id,
                                'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': payment_description,
                                'financial_year': financial_year,
                                'batch_no': batch_no,
                                'product_type': product_type,
                                'semester': semester,
                                'payment_type': payment_category,
                                'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()
            
            # ============================================================
            # IMPREST
            # ============================================================
            elif main_category == "Submit Payment Request" and selected_type == "Imprest":
                with st.form(key="imprest_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    
                    imprest_no = st.text_input("Imprest No.")
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    payment_description = st.text_area("Payment Detail")
                    
                    submitted = st.form_submit_button("Submit Request", use_container_width=True)
                    
                    if submitted:
                        errors = []
                        if not imprest_no:
                            errors.append("Imprest No. is required")
                        if amount <= 0:
                            errors.append("Amount must be greater than 0")
                        if not payment_description:
                            errors.append("Payment Detail is required")
                        
                        if errors:
                            for error in errors:
                                st.error(f"❌ {error}")
                        else:
                            request_data = {
                                'main_category': main_category,
                                'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id,
                                'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': payment_description,
                                'financial_year': financial_year,
                                'imprest_no': imprest_no,
                                'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()
            
            # ============================================================
            # PETTY CASH
            # ============================================================
            elif main_category == "Submit Payment Request" and selected_type == "Petty Cash":
                with st.form(key="petty_cash_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    
                    petty_cash_no = st.text_input("Petty Cash No.")
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    payment_description = st.text_area("Payment Detail")
                    
                    submitted = st.form_submit_button("Submit Request", use_container_width=True)
                    
                    if submitted:
                        errors = []
                        if not petty_cash_no:
                            errors.append("Petty Cash No. is required")
                        if amount <= 0:
                            errors.append("Amount must be greater than 0")
                        if not payment_description:
                            errors.append("Payment Detail is required")
                        
                        if errors:
                            for error in errors:
                                st.error(f"❌ {error}")
                        else:
                            request_data = {
                                'main_category': main_category,
                                'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id,
                                'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': payment_description,
                                'financial_year': financial_year,
                                'imprest_no': petty_cash_no,
                                'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()
            
            # ============================================================
            # SUPPLIER PAYMENT
            # ============================================================
            elif main_category == "Submit Payment Request" and selected_type == "Supplier Payment":
                with st.form(key="supplier_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    
                    invoice_no = st.text_input("Invoice No.")
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    supplier_name = st.text_input("Supplier Name")
                    payment_description = st.text_area("Payment Detail")
                    
                    submitted = st.form_submit_button("Submit Request", use_container_width=True)
                    
                    if submitted:
                        errors = []
                        if not invoice_no:
                            errors.append("Invoice No. is required")
                        if amount <= 0:
                            errors.append("Amount must be greater than 0")
                        if not supplier_name:
                            errors.append("Supplier Name is required")
                        if not payment_description:
                            errors.append("Payment Detail is required")
                        
                        if errors:
                            for error in errors:
                                st.error(f"❌ {error}")
                        else:
                            request_data = {
                                'main_category': main_category,
                                'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id,
                                'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': payment_description,
                                'financial_year': financial_year,
                                'invoice_no': invoice_no,
                                'supplier_name': supplier_name,
                                'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()
            
            # ============================================================
            # SALARY PAYMENT
            # ============================================================
            elif main_category == "Submit Payment Request" and selected_type == "Salary Payment":
                with st.form(key="salary_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    
                    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                    salary_month = st.selectbox("Salary Month", months)
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    current_year = datetime.now().year
                    salary_year = st.number_input("Year", min_value=2020, max_value=2030, value=current_year)
                    
                    submitted = st.form_submit_button("Submit Request", use_container_width=True)
                    
                    if submitted:
                        errors = []
                        if not salary_month:
                            errors.append("Salary Month is required")
                        if amount <= 0:
                            errors.append("Amount must be greater than 0")
                        if not financial_year:
                            errors.append("Financial Year is required")
                        
                        if errors:
                            for error in errors:
                                st.error(f"❌ {error}")
                        else:
                            request_data = {
                                'main_category': main_category,
                                'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id,
                                'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': None,
                                'financial_year': financial_year,
                                'salary_month': salary_month,
                                'salary_year': salary_year,
                                'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()
            
            # ============================================================
            # REFUND PAYMENT
            # ============================================================
            elif main_category == "Submit Payment Request" and selected_type == "Refund Payment":
                with st.form(key="refund_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    
                    refund_id = st.text_input("Refund ID")
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    customer_name = st.text_input("Customer Name")
                    customer_id = st.text_input("Customer ID Number")
                    
                    submitted = st.form_submit_button("Submit Request", use_container_width=True)
                    
                    if submitted:
                        errors = []
                        if not refund_id:
                            errors.append("Refund ID is required")
                        if amount <= 0:
                            errors.append("Amount must be greater than 0")
                        if not customer_name:
                            errors.append("Customer Name is required")
                        
                        if errors:
                            for error in errors:
                                st.error(f"❌ {error}")
                        else:
                            request_data = {
                                'main_category': main_category,
                                'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id,
                                'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': None,
                                'financial_year': financial_year,
                                'imprest_no': refund_id,
                                'customer_name': customer_name,
                                'customer_id': customer_id,
                                'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()
            
            # ============================================================
            # SURRENDER
            # ============================================================
            elif main_category == "Submit Surrender":
                with st.form(key="surrender_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    
                    surrender_no = st.text_input("Surrender No.")
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    staff_name = st.text_input("Staff Name")
                    payment_description = st.text_area("Payment Detail")
                    
                    submitted = st.form_submit_button("Submit Request", use_container_width=True)
                    
                    if submitted:
                        errors = []
                        if not surrender_no:
                            errors.append("Surrender No. is required")
                        if amount <= 0:
                            errors.append("Amount must be greater than 0")
                        if not staff_name:
                            errors.append("Staff Name is required")
                        if not payment_description:
                            errors.append("Payment Detail is required")
                        
                        if errors:
                            for error in errors:
                                st.error(f"❌ {error}")
                        else:
                            request_data = {
                                'main_category': main_category,
                                'request_type': "Surrender",
                                'department_id': st.session_state.user_dept_id,
                                'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': payment_description,
                                'financial_year': financial_year,
                                'surrender_number': surrender_no,
                                'staff_name': staff_name,
                                'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()


# ================================================================
# MY REQUESTS
# ================================================================
elif choice == "📋 My Requests":
    st.markdown("<h1 style='color: #00843D;'>📋 My Requests</h1>", unsafe_allow_html=True)
    df = get_requests()
    if df.empty:
        st.info("No requests found.")
    else:
        user_requests = df[df['submitted_by'] == st.session_state.username]
        if user_requests.empty:
            st.info("You haven't submitted any requests yet.")
        else:
            for _, row in user_requests.iterrows():
                status_display = "✅ Paid" if row['status'] == 'PAID' else "✅ Cleared" if row['status'] == 'CLEARED' else "⏳ Pending"
                with st.expander(f"📄 {row['request_number']} - {row['request_type']}"):
                    st.write(f"**Amount:** KES {row['amount']:,.2f}")
                    st.write(f"**Submitted:** {row['submission_date']}")
                    st.write(f"**Status:** {status_display}")
                    if row['status'] == 'RETURNED' and row.get('return_reason'):
                        st.error(f"**Return Reason:** {row['return_reason']}")
                    st.markdown("---")
                    st.subheader("📜 Transaction Logs")
                    display_transaction_logs(row['id'])


# ================================================================
# RETURNED REQUESTS
# ================================================================
elif choice == "↩️ Returned Requests":
    st.markdown("<h1 style='color: #00843D;'>↩️ Returned Requests</h1>", unsafe_allow_html=True)
    df = get_returned_requests(st.session_state.user_dept)
    if df.empty:
        st.info("No returned requests found.")
    else:
        for _, req in df.iterrows():
            with st.expander(f"📄 {req['request_number']} - {req['request_type']} - Returned on: {req['date_returned']}"):
                st.markdown(f"**Return Reason:** :red[{req['return_reason']}]")
                st.markdown(f"**Original Amount:** KES {req['amount']:,.2f}")
                if st.button(f"Resubmit {req['request_number']}", key=f"resubmit_{req['id']}"):
                    # Simple resubmit logic
                    update_request_status(req['id'], 'SUBMITTED', performed_by=st.session_state.username)
                    add_request_log(req['id'], req['request_number'], "RESUBMITTED", "RETURNED", "SUBMITTED", "Resubmitted", st.session_state.username, st.session_state.user_role, st.session_state.user_dept)
                    st.success(f"Request {req['request_number']} resubmitted!")
                    st.rerun()


# ================================================================
# APPROVAL QUEUE
# ================================================================
elif choice == "✅ Approval Queue":
    if st.session_state.user_role in ["FINANCE", "ADMIN"] or st.session_state.is_finance:
        st.markdown("<h1 style='color: #00843D;'>✅ Approval Queue</h1>", unsafe_allow_html=True)
        pending_confirmation = get_pending_confirmation_count()
        pending_completion = get_pending_completion_count()
        
        col1, col2 = st.columns(2)
        with col1:
            if pending_confirmation > 0:
                st.markdown(f'<span class="pending-badge">📋 {pending_confirmation} requests pending confirmation</span>', unsafe_allow_html=True)
        with col2:
            if pending_completion > 0:
                st.markdown(f'<span class="warning-badge">⏳ {pending_completion} requests pending payment</span>', unsafe_allow_html=True)
        
        df = get_requests()
        pending = df[df['status'].isin(['SUBMITTED', 'CONFIRMED_BY_FINANCE'])]
        
        for _, req in pending.iterrows():
            with st.expander(f"📄 {req['request_number']} - {req['request_type']} - {req['department_name']}"):
                st.write(f"**Amount:** KES {req['amount']:,.2f}")
                st.write(f"**Submitted:** {req['submission_date']}")
                
                if req['status'] == 'SUBMITTED':
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Confirm", key=f"confirm_{req['id']}"):
                            update_request_status(req['id'], 'CONFIRMED_BY_FINANCE', performed_by=st.session_state.username)
                            st.success(f"Request {req['request_number']} confirmed!")
                            st.rerun()
                    with col2:
                        reason = st.text_input("Return Reason", key=f"return_reason_{req['id']}")
                        if st.button(f"↩️ Return", key=f"return_{req['id']}"):
                            if reason:
                                update_request_status(req['id'], 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                st.warning(f"Request {req['request_number']} returned!")
                                st.rerun()
                elif req['status'] == 'CONFIRMED_BY_FINANCE':
                    payment_ref = st.text_input("Payment Reference", key=f"ref_{req['id']}")
                    if st.button(f"💰 Mark as Paid", key=f"paid_{req['id']}"):
                        if payment_ref:
                            new_status = 'CLEARED' if req['main_category'] == 'Submit Surrender' else 'PAID'
                            update_request_status(req['id'], new_status, performed_by=st.session_state.username)
                            update_payment_details(req['id'], payment_ref)
                            st.success(f"Request {req['request_number']} marked as {new_status}!")
                            st.rerun()


# ================================================================
# REPORTS
# ================================================================
elif choice == "📑 Reports":
    st.markdown("<h1 style='color: #00843D;'>📑 Reports</h1>", unsafe_allow_html=True)
    df = get_reports_data(st.session_state.user_role, st.session_state.user_dept)
    if df.empty:
        st.info("No data available")
    else:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export to CSV", csv, "helb_requests.csv", "text/csv", use_container_width=True)
        st.dataframe(df[['request_number', 'request_type', 'amount', 'status', 'submission_date']], use_container_width=True)


# ================================================================
# ADMIN PANEL
# ================================================================
elif choice == "⚙️ Admin Panel" and st.session_state.user_role == "ADMIN":
    st.markdown("<h1 style='color: #00843D;'>⚙️ Admin Panel</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["👥 Users", "🏢 Departments"])
    
    with tab1:
        st.subheader("User Management")
        users_df = get_all_users()
        st.dataframe(users_df)
        
        with st.form("add_user"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", value="password123")
            new_full_name = st.text_input("Full Name")
            new_role = st.selectbox("Role", ["DEPARTMENT", "FINANCE", "MANAGEMENT", "ADMIN"])
            depts = get_departments()
            dept_options = {row['name']: row['id'] for _, row in depts.iterrows()}
            new_department = st.selectbox("Department", ["None"] + list(dept_options.keys()))
            if st.form_submit_button("Create User"):
                dept_id = dept_options.get(new_department) if new_department != "None" else None
                create_user(new_username, new_password, new_role, dept_id, new_full_name)
                st.rerun()
    
    with tab2:
        st.subheader("Department Management")
        st.dataframe(get_departments())


# ================================================================
# CHANGE PASSWORD
# ================================================================
elif choice == "🔐 Change Password":
    st.markdown("<h1 style='color: #00843D;'>🔐 Change Password</h1>", unsafe_allow_html=True)
    with st.form("change_pwd_form"):
        current = st.text_input("Current Password", type="password")
        new = st.text_input("New Password", type="password")
        confirm = st.text_input("Confirm New Password", type="password")
        if st.form_submit_button("Update Password"):
            if new == confirm and len(new) >= 4:
                user = authenticate_user(st.session_state.username, current)
                if user:
                    update_user_password(st.session_state.username, new)
                    st.success("✅ Password updated successfully!")
                else:
                    st.error("❌ Current password is incorrect")
            else:
                st.error("❌ Passwords do not match or are too short")
