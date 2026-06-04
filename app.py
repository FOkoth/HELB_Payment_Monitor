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
    add_request_log, get_pending_receive_count, get_pending_stage_count,
    get_pending_completion_count, get_time_lapsed_from_confirmation,
    get_requests_by_stage, get_approval_stages, update_bank_details,
    get_notification_count, mark_notification_read, get_notifications
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
        transition: all 0.3s ease;
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
    .pending-badge {
        background-color: #DC3545;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
    }
    .stage-completed {
        background-color: #00843D20;
        color: #00843D;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .stage-pending {
        background-color: #FFB81C20;
        color: #FFB81C;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .stage-current {
        background-color: #00843D;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-weight: bold;
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
    .log-stage { background-color: #f3e5f5; border-left: 3px solid #9C27B0; }
    .status-paid { background-color: #00843D20; color: #00843D; padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: bold; }
    .status-pending { background-color: #DC354520; color: #DC3545; padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: bold; }
    .notification-badge {
        background-color: #DC3545;
        color: white;
        border-radius: 50%;
        padding: 0.2rem 0.5rem;
        font-size: 0.7rem;
        margin-left: 0.5rem;
    }
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
    notification_count = get_notification_count(st.session_state.user_role)
    notification_badge = f' <span class="notification-badge">{notification_count}</span>' if notification_count > 0 else ''
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
                       "📝 New Request", "📋 My Requests", "↩️ Returned Requests", "📑 Reports", 
                       "⚙️ Admin Panel", "🔐 Change Password"]
    elif st.session_state.user_role == "FINANCE_RECEIVER":
        menu_options = [f"📥 Receive Requests{notification_badge}", "📋 All Requests", "🔐 Change Password"]
    elif st.session_state.user_role == "FINANCE_SENIOR":
        menu_options = [f"⚙️ Process Stages{notification_badge}", "📋 All Requests", "🔐 Change Password"]
    elif st.session_state.user_role == "FINANCE_PAYMENTS":
        menu_options = [f"💰 Release Payments{notification_badge}", "📋 All Requests", "🔐 Change Password"]
    else:
        menu_options = ["📊 Department Dashboard", "🔍 Check Payment Status", "📝 New Request", 
                       "📋 My Requests", "↩️ Returned Requests", "📑 Reports", "🔐 Change Password"]
    
    clean_menu_options = [opt.split('<')[0] if '<' in opt else opt for opt in menu_options]
    choice = option_menu(
        menu_title="Menu",
        options=clean_menu_options,
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

# ================================================================
# Helper Functions
# ================================================================
def display_transaction_logs(request_id):
    logs = get_request_logs(request_id)
    if logs:
        for log in logs:
            timestamp = datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %H:%M')
            action = log['action']
            if action == 'SUBMITTED':
                st.markdown(f"<div class='log-entry log-submitted'>📝 **{timestamp}** - Submitted by {log['performed_by']}</div>", unsafe_allow_html=True)
            elif action == 'RECEIVED':
                st.markdown(f"<div class='log-entry log-received'>📥 **{timestamp}** - Received by {log['performed_by']}</div>", unsafe_allow_html=True)
            elif action in ['Payment Prepared', 'Payment Verified', 'Payment Approved', 'Payment Authorized',
                           'Surrender Verified', 'Surrender Approved', 'Surrender Authorized']:
                st.markdown(f"<div class='log-entry log-stage'>⚙️ **{timestamp}** - {action} by {log['performed_by']}</div>", unsafe_allow_html=True)
            elif action == 'RETURNED':
                st.markdown(f"<div class='log-entry log-returned'>↩️ **{timestamp}** - Returned by {log['performed_by']} - Reason: {log['comment']}</div>", unsafe_allow_html=True)
            elif action in ['PAID', 'CLEARED']:
                st.markdown(f"<div class='log-entry log-paid'>✅ **{timestamp}** - {action} by {log['performed_by']}</div>", unsafe_allow_html=True)
    else:
        st.info("No transaction logs available")

def display_approval_stages(request_id, main_category):
    stages = get_approval_stages(request_id)
    if not stages:
        return
    st.subheader("📋 Approval Stages Progress")
    if main_category == "Submit Payment Request":
        stage_order = ["Payment Prepared", "Payment Verified", "Payment Approved", "Payment Authorized"]
    else:
        stage_order = ["Surrender Verified", "Surrender Approved", "Surrender Authorized"]
    cols = st.columns(len(stage_order))
    for i, stage_name in enumerate(stage_order):
        stage_info = next((s for s in stages if s['stage_name'] == stage_name), None)
        with cols[i]:
            if stage_info and stage_info['status'] == 'COMPLETED':
                st.markdown(f"<div class='stage-completed' style='text-align:center'>✅ {stage_name}<br><small>{stage_info['days_taken']} days</small></div>", unsafe_allow_html=True)
            elif stage_info and stage_info['status'] == 'PENDING' and i == 0:
                st.markdown(f"<div class='stage-current' style='text-align:center'>⏳ {stage_name}<br><small>Current</small></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='stage-pending' style='text-align:center'>⏸ {stage_name}<br><small>Pending</small></div>", unsafe_allow_html=True)

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
        with col1:
            st.metric("Total Requests", len(df))
        with col2:
            st.metric("Pending", len(df[df['status'].isin(['SUBMITTED', 'RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED'])]) + len(df[df['status'].isin(['SURRENDER_VERIFIED', 'SURRENDER_APPROVED', 'SURRENDER_AUTHORIZED'])]))
        with col3:
            st.metric("Completed", len(df[df['status'].isin(['PAID', 'CLEARED'])]))
        with col4:
            st.metric("Returned", len(df[df['status'] == 'RETURNED']))
        st.markdown("---")
        st.subheader("📋 Recent Requests")
        for _, row in df.head(10).iterrows():
            status_display = "✅ Paid" if row['status'] == 'PAID' else "✅ Cleared" if row['status'] == 'CLEARED' else "⏳ Pending"
            with st.expander(f"📄 {row['request_number']} - {row['request_type']}"):
                st.write(f"**Amount:** KES {row['amount']:,.2f}")
                st.write(f"**Submitted:** {row['submission_date']}")
                st.write(f"**Status:** {status_display}")
                display_approval_stages(row['id'], row['main_category'])
                st.markdown("---")
                st.subheader("📜 Transaction Logs")
                display_transaction_logs(row['id'])

# ================================================================
# MANAGEMENT DASHBOARD
# ================================================================
elif choice == "📈 Management Dashboard":
    st.markdown("<h1 style='color: #00843D;'>📈 Management Dashboard</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        financial_years = ["All"] + get_financial_years()
        selected_fy = st.selectbox("Financial Year", financial_years)
    with col2:
        quarters = ["All", "Q1 (Jul-Sep)", "Q2 (Oct-Dec)", "Q3 (Jan-Mar)", "Q4 (Apr-Jun)"]
        selected_quarter = st.selectbox("Quarter", quarters)
    stats = get_management_dashboard_stats(selected_fy if selected_fy != "All" else None,
                                            selected_quarter if selected_quarter != "All" else None)
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Requests", stats['total_requests'])
    with col2:
        st.metric("Total Amount", f"KES {stats['total_amount']:,.0f}")
    with col3:
        st.metric("Avg Completion", f"{stats['avg_completion_time']:.1f} days")
    with col4:
        st.metric("Breach Rate", f"{stats['breach_rate']:.1f}%")
    st.markdown("---")
    st.subheader("📊 Workflow Pipeline")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pending Receive", stats['pending_receive'])
    with col2:
        st.metric("In Progress", stats['pending_stages'])
    with col3:
        st.metric("Pending Payment", stats['pending_payment'])
    st.subheader("📋 All Requests")
    all_requests = get_requests()
    if selected_fy != "All":
        all_requests = all_requests[all_requests['financial_year'] == selected_fy]
    st.dataframe(all_requests[['request_number', 'request_type', 'department_name', 'amount', 'status', 'submission_date']], use_container_width=True)

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
                st.success(f"✅ {result['request_number']} - Status: {result['status']}")
        else:
            st.error("No records found")

# ================================================================
# NEW REQUEST
# ================================================================
elif choice == "📝 New Request":
    st.markdown("<h1 style='color: #00843D;'>📝 Create New Request</h1>", unsafe_allow_html=True)
    allowed_main_categories = get_allowed_main_categories(st.session_state.user_role, st.session_state.user_dept)
    if not allowed_main_categories:
        st.error("Your role does not have permission to submit requests.")
    else:
        main_category = st.radio("What would you like to do?", allowed_main_categories, horizontal=True)
        st.markdown("---")
        allowed_types = get_allowed_request_types(st.session_state.user_role, st.session_state.user_dept, main_category)
        if not allowed_types:
            st.error("No request types available.")
        else:
            selected_type = st.selectbox("Select Request Type", allowed_types)
            st.markdown("---")
            if main_category == "Submit Payment Request" and selected_type == "Student Payment":
                st.subheader("🎓 Student Payment Details")
                products = get_products()
                product_list = products['name'].tolist() if not products.empty else ["Undergraduate", "TVET", "Jielimishe"]
                product_type = st.selectbox("Product Type", product_list)
                st.markdown("---")
                with st.form(key="student_payment_form"):
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
                    semester = None
                    payment_category = None
                    if product_type in ["Undergraduate", "TVET"]:
                        semesters = get_semesters()
                        semester = st.selectbox("Semester", semesters if semesters else ["Semester 1", "Semester 2"])
                        payment_category = st.selectbox("Payment Category", ["Tuition", "Upkeep"])
                    else:
                        semester = None
                        payment_category = "Tuition"
                    batch_no = st.text_input("Batch No.")
                    submitted = st.form_submit_button("Submit Request", use_container_width=True)
                    if submitted:
                        if amount <= 0 or not payment_description or not batch_no:
                            st.error("Please fill all required fields")
                        else:
                            request_data = {
                                'main_category': main_category, 'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id, 'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username, 'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'batch_no': batch_no, 'product_type': product_type, 'semester': semester,
                                'payment_type': payment_category, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()
            elif main_category == "Submit Payment Request" and selected_type == "Imprest":
                with st.form(key="imprest_form"):
                    st.subheader("💰 Imprest Payment Details")
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
                        if not imprest_no or amount <= 0 or not payment_description:
                            st.error("Please fill all required fields")
                        else:
                            request_data = {
                                'main_category': main_category, 'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id, 'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username, 'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'imprest_no': imprest_no, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()
            elif main_category == "Submit Payment Request" and selected_type == "Petty Cash":
                with st.form(key="petty_cash_form"):
                    st.subheader("💵 Petty Cash Payment Details")
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
                        if not petty_cash_no or amount <= 0 or not payment_description:
                            st.error("Please fill all required fields")
                        else:
                            request_data = {
                                'main_category': main_category, 'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id, 'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username, 'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'imprest_no': petty_cash_no, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()
            elif main_category == "Submit Payment Request" and selected_type == "Supplier Payment":
                with st.form(key="supplier_form"):
                    st.subheader("🏢 Supplier Payment Details")
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
                        if not invoice_no or amount <= 0 or not supplier_name or not payment_description:
                            st.error("Please fill all required fields")
                        else:
                            request_data = {
                                'main_category': main_category, 'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id, 'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username, 'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'invoice_no': invoice_no, 'supplier_name': supplier_name, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()
            elif main_category == "Submit Payment Request" and selected_type == "Salary Payment":
                with st.form(key="salary_form"):
                    st.subheader("👔 Salary Payment Details")
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
                        if not salary_month or amount <= 0 or not financial_year:
                            st.error("Please fill all required fields")
                        else:
                            request_data = {
                                'main_category': main_category, 'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id, 'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username, 'amount': amount,
                                'financial_year': financial_year, 'salary_month': salary_month,
                                'salary_year': salary_year, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()
            elif main_category == "Submit Payment Request" and selected_type == "Refund Payment":
                with st.form(key="refund_form"):
                    st.subheader("🔄 Refund Payment Details")
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
                        if not refund_id or amount <= 0 or not customer_name:
                            st.error("Please fill all required fields")
                        else:
                            request_data = {
                                'main_category': main_category, 'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id, 'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username, 'amount': amount,
                                'financial_year': financial_year, 'imprest_no': refund_id,
                                'customer_name': customer_name, 'customer_id': customer_id, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()
            elif main_category == "Submit Surrender":
                with st.form(key="surrender_form"):
                    st.subheader("📤 Surrender Details")
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
                        if not surrender_no or amount <= 0 or not staff_name or not payment_description:
                            st.error("Please fill all required fields")
                        else:
                            request_data = {
                                'main_category': main_category, 'request_type': "Surrender",
                                'department_id': st.session_state.user_dept_id, 'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username, 'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'surrender_number': surrender_no, 'staff_name': staff_name, 'status': 'SUBMITTED'
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
                    display_approval_stages(row['id'], row['main_category'])
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
            with st.expander(f"📄 {req['request_number']} - Returned on: {req['date_returned']}"):
                st.markdown(f"**Return Reason:** :red[{req['return_reason']}]")
                st.markdown(f"**Amount:** KES {req['amount']:,.2f}")
                if st.button(f"Resubmit", key=f"resubmit_{req['id']}"):
                    update_request_status(req['id'], 'SUBMITTED', performed_by=st.session_state.username)
                    add_request_log(req['id'], req['request_number'], "RESUBMITTED", "RETURNED", "SUBMITTED", "Resubmitted", st.session_state.username, st.session_state.user_role, st.session_state.user_dept)
                    st.success(f"Request resubmitted!")
                    st.rerun()

# ================================================================
# FINANCE RECEIVER - RECEIVE REQUESTS
# ================================================================
elif choice == "📥 Receive Requests":
    if st.session_state.user_role == "FINANCE_RECEIVER":
        st.markdown("<h1 style='color: #00843D;'>📥 Receive Requests</h1>", unsafe_allow_html=True)
        notifications = get_notifications(st.session_state.user_role)
        for notif in notifications:
            mark_notification_read(notif['id'])
        df = get_requests_by_stage("FINANCE_RECEIVER")
        if df.empty:
            st.info("No requests pending receive confirmation.")
        else:
            for idx, (_, req) in enumerate(df.iterrows()):
                with st.expander(f"📄 {req['request_number']} - {req['request_type']} - {req['department_name']}"):
                    st.write(f"**Amount:** KES {req['amount']:,.2f}")
                    st.write(f"**Submitted:** {req['submission_date']}")
                    st.markdown("---")
                    checklist_approvals = st.checkbox("✓ All required approvals and signoffs obtained", key=f"approvals_{idx}")
                    checklist_documents = st.checkbox("✓ All relevant documents attached", key=f"documents_{idx}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Confirm & Receive", key=f"confirm_{idx}"):
                            if checklist_approvals and checklist_documents:
                                update_request_status(req['id'], 'RECEIVED_BY_FINANCE', performed_by=st.session_state.username, performed_by_role=st.session_state.user_role, performed_by_dept=st.session_state.user_dept, checklist_approvals=checklist_approvals, checklist_documents=checklist_documents)
                                st.success(f"Request {req['request_number']} confirmed!")
                                st.rerun()
                            else:
                                st.error("Please check both boxes")
                    with col2:
                        reason = st.text_input("Return Reason", key=f"return_{idx}")
                        if st.button(f"↩️ Return", key=f"return_btn_{idx}"):
                            if reason:
                                update_request_status(req['id'], 'RETURNED', return_reason=reason, performed_by=st.session_state.username, performed_by_role=st.session_state.user_role, performed_by_dept=st.session_state.user_dept)
                                st.warning(f"Request returned!")
                                st.rerun()
    else:
        st.error("Access denied.")

# ================================================================
# FINANCE SENIOR - PROCESS STAGES
# ================================================================
elif choice == "⚙️ Process Stages":
    if st.session_state.user_role == "FINANCE_SENIOR":
        st.markdown("<h1 style='color: #00843D;'>⚙️ Process Approval Stages</h1>", unsafe_allow_html=True)
        notifications = get_notifications(st.session_state.user_role)
        for notif in notifications:
            mark_notification_read(notif['id'])
        df = get_requests_by_stage("FINANCE_SENIOR")
        if df.empty:
            st.info("No requests pending stage processing.")
        else:
            for idx, (_, req) in enumerate(df.iterrows()):
                current_status = req['status']
                main_category = req['main_category']
                if main_category == "Submit Payment Request":
                    if current_status == 'RECEIVED_BY_FINANCE':
                        next_stage = 'PAYMENT_PREPARED'
                        next_stage_name = "Payment Prepared"
                    elif current_status == 'PAYMENT_PREPARED':
                        next_stage = 'PAYMENT_VERIFIED'
                        next_stage_name = "Payment Verified"
                    elif current_status == 'PAYMENT_VERIFIED':
                        next_stage = 'PAYMENT_APPROVED'
                        next_stage_name = "Payment Approved"
                    elif current_status == 'PAYMENT_APPROVED':
                        next_stage = 'PAYMENT_AUTHORIZED'
                        next_stage_name = "Payment Authorized"
                    else:
                        next_stage = None
                        next_stage_name = None
                else:
                    if current_status == 'RECEIVED_BY_FINANCE':
                        next_stage = 'SURRENDER_VERIFIED'
                        next_stage_name = "Surrender Verified"
                    elif current_status == 'SURRENDER_VERIFIED':
                        next_stage = 'SURRENDER_APPROVED'
                        next_stage_name = "Surrender Approved"
                    elif current_status == 'SURRENDER_APPROVED':
                        next_stage = 'SURRENDER_AUTHORIZED'
                        next_stage_name = "Surrender Authorized"
                    else:
                        next_stage = None
                        next_stage_name = None
                with st.expander(f"📄 {req['request_number']} - {req['request_type']} - {req['department_name']}"):
                    st.write(f"**Amount:** KES {req['amount']:,.2f}")
                    st.write(f"**Current Stage:** {current_status}")
                    if next_stage:
                        if st.button(f"✓ {next_stage_name}", key=f"stage_{idx}"):
                            update_request_status(req['id'], next_stage, performed_by=st.session_state.username, performed_by_role=st.session_state.user_role, performed_by_dept=st.session_state.user_dept, stage_comment=f"{next_stage_name} completed")
                            st.success(f"Request {req['request_number']} moved to {next_stage_name}")
                            st.rerun()
                    display_approval_stages(req['id'], main_category)
    else:
        st.error("Access denied.")

# ================================================================
# FINANCE PAYMENTS - RELEASE PAYMENTS
# ================================================================
elif choice == "💰 Release Payments":
    if st.session_state.user_role == "FINANCE_PAYMENTS":
        st.markdown("<h1 style='color: #00843D;'>💰 Release Payments</h1>", unsafe_allow_html=True)
        notifications = get_notifications(st.session_state.user_role)
        for notif in notifications:
            mark_notification_read(notif['id'])
        df = get_requests_by_stage("FINANCE_PAYMENTS")
        if df.empty:
            st.info("No requests pending payment release.")
        else:
            for idx, (_, req) in enumerate(df.iterrows()):
                with st.expander(f"📄 {req['request_number']} - {req['request_type']} - {req['department_name']}"):
                    st.write(f"**Amount:** KES {req['amount']:,.2f}")
                    payment_ref = st.text_input("Payment Reference / Transaction ID", key=f"ref_{idx}")
                    if st.button(f"💰 Mark as {'Cleared' if req['main_category'] == 'Submit Surrender' else 'Paid'}", key=f"paid_{idx}"):
                        if payment_ref:
                            new_status = 'CLEARED' if req['main_category'] == 'Submit Surrender' else 'PAID'
                            update_request_status(req['id'], new_status, performed_by=st.session_state.username, performed_by_role=st.session_state.user_role, performed_by_dept=st.session_state.user_dept)
                            update_payment_details(req['id'], payment_ref)
                            st.balloons()
                            st.success(f"Request {req['request_number']} marked as {new_status}!")
                            st.rerun()
                        else:
                            st.error("Please enter a payment reference")
    else:
        st.error("Access denied.")

# ================================================================
# ALL REQUESTS (for Finance roles)
# ================================================================
elif choice == "📋 All Requests":
    st.markdown("<h1 style='color: #00843D;'>📋 All Requests</h1>", unsafe_allow_html=True)
    df = get_requests()
    if df.empty:
        st.info("No requests found.")
    else:
        st.dataframe(df[['request_number', 'request_type', 'department_name', 'amount', 'status', 'submission_date']], use_container_width=True)

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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Users", "🏢 Departments", "📦 Products", "💰 Funders", "📅 Financial Years"])
    with tab1:
        st.subheader("User Management")
        users_df = get_all_users()
        st.dataframe(users_df)
        with st.form("add_user"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", value="password123")
            new_full_name = st.text_input("Full Name")
            new_role = st.selectbox("Role", ["DEPARTMENT", "FINANCE_RECEIVER", "FINANCE_SENIOR", "FINANCE_PAYMENTS", "MANAGEMENT", "ADMIN"])
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
        with st.form("add_dept"):
            dept_name = st.text_input("Department Name")
            if st.form_submit_button("Add Department"):
                perms = [True, True, False, False, True, False, False, False, False]
                create_department(dept_name, perms)
                st.rerun()
    with tab3:
        st.subheader("Product Management")
        st.dataframe(get_products())
        with st.form("add_product"):
            name = st.text_input("Product Name")
            if st.form_submit_button("Add Product"):
                add_product(name, "LOAN", True, True)
                st.rerun()
    with tab4:
        st.subheader("Funder Management")
        for f in get_funders():
            st.write(f"• {f}")
    with tab5:
        st.subheader("Financial Year Management")
        for y in get_financial_years():
            st.write(f"• {y}")

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
