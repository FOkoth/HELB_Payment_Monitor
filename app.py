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
    get_time_lapsed_from_confirmation, verify_finance_password, update_finance_password,
    get_finance_password, add_financial_year, add_semester, add_funder
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
        transform: translateY(-1px);
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
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
    .warning-badge {
        background-color: #FFB81C;
        color: #1E1E1E;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
    }
    .success-badge {
        background-color: #00843D20;
        color: #00843D;
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
        text-align: center;
    }
    .stage-pending {
        background-color: #FFB81C20;
        color: #FFB81C;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        text-align: center;
    }
    .stage-current {
        background-color: #00843D;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-weight: bold;
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
    .log-stage { background-color: #f3e5f5; border-left: 3px solid #9C27B0; }
    .status-paid { background-color: #00843D20; color: #00843D; padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: bold; display: inline-block; }
    .status-cleared { background-color: #00843D20; color: #00843D; padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: bold; display: inline-block; }
    .status-pending { background-color: #DC354520; color: #DC3545; padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: bold; display: inline-block; }
    .status-confirmed { background-color: #00BCD420; color: #00BCD4; padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: bold; display: inline-block; }
    .password-modal {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        text-align: center;
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
if 'pending_action' not in st.session_state:
    st.session_state.pending_action = None
if 'pending_request_id' not in st.session_state:
    st.session_state.pending_request_id = None
if 'pending_status' not in st.session_state:
    st.session_state.pending_status = None

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

# Password verification function
def verify_and_execute(request_id, status, action_name, additional_params=None):
    st.markdown(f"""
    <div class='password-modal'>
        <h3>🔐 {action_name}</h3>
        <p>Please enter Finance password to confirm this action.</p>
    </div>
    """, unsafe_allow_html=True)
    
    password = st.text_input("Finance Password", type="password", key=f"pwd_{request_id}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Confirm", key=f"confirm_{request_id}"):
            if verify_finance_password(password):
                if additional_params:
                    update_request_status(
                        request_id, status,
                        performed_by=st.session_state.username,
                        performed_by_role=st.session_state.user_role,
                        performed_by_dept=st.session_state.user_dept,
                        **additional_params
                    )
                else:
                    update_request_status(
                        request_id, status,
                        performed_by=st.session_state.username,
                        performed_by_role=st.session_state.user_role,
                        performed_by_dept=st.session_state.user_dept
                    )
                st.success(f"✅ {action_name} completed successfully!")
                st.rerun()
            else:
                st.error("❌ Incorrect password! Action not executed.")
    with col2:
        if st.button("Cancel", key=f"cancel_{request_id}"):
            st.rerun()
    return False

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
    elif st.session_state.user_role == "FINANCE":
        menu_options = ["📊 Department Dashboard", "📈 Management Dashboard", "🔍 Check Payment Status", 
                       "📝 New Request", "📋 My Requests", "↩️ Returned Requests", "✅ Approval Queue", 
                       "📑 Reports", "🔐 Change Password"]
    else:
        menu_options = ["📊 Department Dashboard", "🔍 Check Payment Status", "📝 New Request", 
                       "📋 My Requests", "↩️ Returned Requests", "📑 Reports", "🔐 Change Password"]
    
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


# ================================================================
# HELPER FUNCTIONS
# ================================================================
def display_transaction_logs(request_id):
    logs = get_request_logs(request_id)
    if logs:
        for log in logs:
            timestamp = datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %H:%M')
            action = log['action']
            if action == 'SUBMITTED':
                st.markdown(f"<div class='log-entry log-submitted'>📝 **{timestamp}** - Submitted by {log['performed_by']} ({log['performed_by_dept']})</div>", unsafe_allow_html=True)
            elif action == 'RECEIVED':
                st.markdown(f"<div class='log-entry log-received'>📥 **{timestamp}** - Received by {log['performed_by']} (Finance)</div>", unsafe_allow_html=True)
            elif action in ['PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED', 'SURRENDER_VERIFIED', 'SURRENDER_APPROVED', 'SURRENDER_AUTHORIZED']:
                st.markdown(f"<div class='log-entry log-stage'>⚙️ **{timestamp}** - {action.replace('_', ' ').title()} by {log['performed_by']}</div>", unsafe_allow_html=True)
            elif action == 'RETURNED':
                st.markdown(f"<div class='log-entry log-returned'>↩️ **{timestamp}** - Returned by {log['performed_by']} - Reason: {log['comment']}</div>", unsafe_allow_html=True)
            elif action == 'RESUBMITTED':
                st.markdown(f"<div class='log-entry log-resubmitted'>📤 **{timestamp}** - Resubmitted by {log['performed_by']}</div>", unsafe_allow_html=True)
            elif action in ['PAID', 'CLEARED']:
                st.markdown(f"<div class='log-entry log-paid'>✅ **{timestamp}** - {action} by {log['performed_by']}</div>", unsafe_allow_html=True)
    else:
        st.info("No transaction logs available")

def display_approval_stages(request_id, main_category):
    st.subheader("📋 Approval Progress")
    if main_category == "Submit Payment Request":
        stages = [
            ('RECEIVED_BY_FINANCE', 'Received by Finance'),
            ('PAYMENT_PREPARED', 'Payment Prepared'),
            ('PAYMENT_VERIFIED', 'Payment Verified'),
            ('PAYMENT_APPROVED', 'Payment Approved'),
            ('PAYMENT_AUTHORIZED', 'Payment Authorized'),
            ('PAID', 'Paid')
        ]
    else:
        stages = [
            ('RECEIVED_BY_FINANCE', 'Received by Finance'),
            ('SURRENDER_VERIFIED', 'Surrender Verified'),
            ('SURRENDER_APPROVED', 'Surrender Approved'),
            ('SURRENDER_AUTHORIZED', 'Surrender Authorized'),
            ('CLEARED', 'Cleared')
        ]
    
    # Get current status
    conn = sqlite3.connect("helb_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM requests WHERE id = ?", (request_id,))
    current_status = cursor.fetchone()[0]
    conn.close()
    
    cols = st.columns(len(stages))
    for i, (status_code, status_name) in enumerate(stages):
        with cols[i]:
            if current_status == status_code:
                st.markdown(f"<div class='stage-current'>⏳ {status_name}<br><small>Current</small></div>", unsafe_allow_html=True)
            elif i < stages.index([(s, n) for s, n in stages if s == current_status][0]) if any(s == current_status for s, _ in stages) else False:
                st.markdown(f"<div class='stage-completed'>✅ {status_name}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='stage-pending'>⏸ {status_name}</div>", unsafe_allow_html=True)


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
        pending = len(df[df['status'].isin(['SUBMITTED', 'RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED', 'SURRENDER_VERIFIED', 'SURRENDER_APPROVED', 'SURRENDER_AUTHORIZED'])])
        completed = len(df[df['status'].isin(['PAID', 'CLEARED'])])
        returned = len(df[df['status'] == 'RETURNED'])
        with col1:
            st.metric("Total Requests", total)
        with col2:
            st.metric("Pending", pending)
        with col3:
            st.metric("Completed", completed)
        with col4:
            st.metric("Returned", returned)
        st.markdown("---")
        st.subheader("📋 Recent Requests")
        for _, row in df.head(10).iterrows():
            if row['status'] == 'PAID':
                status_display = '<span class="status-paid">✅ Paid</span>'
            elif row['status'] == 'CLEARED':
                status_display = '<span class="status-cleared">✅ Cleared</span>'
            elif row['status'] in ['PAYMENT_AUTHORIZED', 'SURRENDER_AUTHORIZED']:
                status_display = '<span class="status-confirmed">📌 Authorized - Pending Payment</span>'
            elif row['status'] in ['PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'SURRENDER_VERIFIED', 'SURRENDER_APPROVED']:
                status_display = '<span class="status-confirmed">⚙️ In Progress</span>'
            elif row['status'] == 'RECEIVED_BY_FINANCE':
                status_display = '<span class="status-confirmed">📥 Received by Finance</span>'
            elif row['status'] == 'RETURNED':
                status_display = f'<span class="status-pending">↩️ Returned on {row["date_returned"]}</span>'
            else:
                days = get_pending_duration(row['submission_date'])
                status_display = f'<span class="status-pending">⏳ Pending ({days} days)</span>'
            with st.expander(f"📄 {row['request_number']} - {row['main_category']} - {row['request_type']}"):
                st.write(f"**Amount:** KES {row['amount']:,.2f}")
                st.write(f"**Submitted:** {row['submission_date']}")
                if row['status'] == 'RECEIVED_BY_FINANCE':
                    confirmed_date = row.get('date_confirmed_by_finance', 'N/A')
                    st.write(f"**Received by Finance:** {confirmed_date}")
                st.markdown(f"**Status:** {status_display}", unsafe_allow_html=True)
                if row.get('payment_description'):
                    st.write(f"**Description:** {row['payment_description']}")
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
    stats = get_management_dashboard_stats(selected_fy if selected_fy != "All" else None, selected_quarter if selected_quarter != "All" else None)
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
    pending_receive = len(get_requests()[get_requests()['status'] == 'SUBMITTED']) if not get_requests().empty else 0
    pending_stages = len(get_requests()[get_requests()['status'].isin(['RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'SURRENDER_VERIFIED', 'SURRENDER_APPROVED'])]) if not get_requests().empty else 0
    pending_payment = len(get_requests()[get_requests()['status'].isin(['PAYMENT_AUTHORIZED', 'SURRENDER_AUTHORIZED'])]) if not get_requests().empty else 0
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pending Receive", pending_receive)
    with col2:
        st.metric("In Progress", pending_stages)
    with col3:
        st.metric("Pending Payment", pending_payment)
    st.subheader("📋 All Requests")
    all_requests = get_requests()
    if selected_fy != "All" and not all_requests.empty:
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
            
            # Student Payment
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
            
            # Imprest
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
            
            # Petty Cash
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
            
            # Direct Payment
            elif main_category == "Submit Payment Request" and selected_type == "Direct Payment":
                with st.form(key="direct_payment_form"):
                    st.subheader("💸 Direct Payment Details")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    direct_payment_details = st.text_area("Payment Details (Payee, Purpose, etc.)")
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    payment_description = st.text_area("Additional Notes")
                    submitted = st.form_submit_button("Submit Request", use_container_width=True)
                    if submitted:
                        if not direct_payment_details or amount <= 0:
                            st.error("Please fill all required fields")
                        else:
                            request_data = {
                                'main_category': main_category, 'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id, 'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username, 'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'direct_payment_details': direct_payment_details, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()
            
            # Supplier Payment
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
            
            # Salary Payment
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
            
            # Refund Payment
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
            
            # Mileage Claim
            elif main_category == "Submit Payment Request" and selected_type == "Mileage Claim":
                with st.form(key="mileage_form"):
                    st.subheader("⛽ Mileage Claim Details")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    mileage_claim_details = st.text_area("Trip Details (From, To, Distance, Vehicle Reg No.)")
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=100.0)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    payment_description = st.text_area("Additional Notes")
                    submitted = st.form_submit_button("Submit Request", use_container_width=True)
                    if submitted:
                        if not mileage_claim_details or amount <= 0:
                            st.error("Please fill all required fields")
                        else:
                            request_data = {
                                'main_category': main_category, 'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id, 'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username, 'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'mileage_claim_details': mileage_claim_details, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()
            
            # Staff Training
            elif main_category == "Submit Payment Request" and selected_type == "Staff Training":
                with st.form(key="training_form"):
                    st.subheader("📚 Staff Training Details")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    training_details = st.text_area("Training Details (Course, Institution, Duration, Participants)")
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    payment_description = st.text_area("Additional Notes")
                    submitted = st.form_submit_button("Submit Request", use_container_width=True)
                    if submitted:
                        if not training_details or amount <= 0:
                            st.error("Please fill all required fields")
                        else:
                            request_data = {
                                'main_category': main_category, 'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id, 'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username, 'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'training_details': training_details, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()
            
            # Professional Body
            elif main_category == "Submit Payment Request" and selected_type == "Professional Body":
                with st.form(key="professional_form"):
                    st.subheader("🏛️ Professional Body Membership Details")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    professional_body = st.text_input("Professional Body Name")
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    payment_description = st.text_area("Additional Notes (Membership Period, Member Name)")
                    submitted = st.form_submit_button("Submit Request", use_container_width=True)
                    if submitted:
                        if not professional_body or amount <= 0:
                            st.error("Please fill all required fields")
                        else:
                            request_data = {
                                'main_category': main_category, 'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id, 'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username, 'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'professional_body': professional_body, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted successfully!")
                            st.balloons()
            
            # Surrender
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
                if row['status'] == 'PAID':
                    status_display = '<span class="status-paid">✅ Paid</span>'
                elif row['status'] == 'CLEARED':
                    status_display = '<span class="status-cleared">✅ Cleared</span>'
                elif row['status'] in ['PAYMENT_AUTHORIZED', 'SURRENDER_AUTHORIZED']:
                    status_display = '<span class="status-confirmed">📌 Authorized - Pending Payment</span>'
                elif row['status'] in ['PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'SURRENDER_VERIFIED', 'SURRENDER_APPROVED']:
                    status_display = '<span class="status-confirmed">⚙️ In Progress</span>'
                elif row['status'] == 'RECEIVED_BY_FINANCE':
                    status_display = '<span class="status-confirmed">📥 Received by Finance</span>'
                elif row['status'] == 'RETURNED':
                    status_display = f'<span class="status-pending">↩️ Returned on {row["date_returned"]}</span>'
                else:
                    days = get_pending_duration(row['submission_date'])
                    status_display = f'<span class="status-pending">⏳ Pending ({days} days)</span>'
                with st.expander(f"📄 {row['request_number']} - {row['main_category']} - {row['request_type']}"):
                    st.write(f"**Amount:** KES {row['amount']:,.2f}")
                    st.write(f"**Submitted:** {row['submission_date']}")
                    if row['status'] == 'RECEIVED_BY_FINANCE':
                        confirmed_date = row.get('date_confirmed_by_finance', 'N/A')
                        st.write(f"**Received by Finance:** {confirmed_date}")
                    st.markdown(f"**Status:** {status_display}", unsafe_allow_html=True)
                    if row.get('payment_description'):
                        st.write(f"**Description:** {row['payment_description']}")
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
# APPROVAL QUEUE - FINANCE ACTIONS WITH PASSWORD
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
            else:
                st.info("No requests pending confirmation")
        with col2:
            if pending_completion > 0:
                st.markdown(f'<span class="warning-badge">⏳ {pending_completion} requests in progress</span>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        df = get_requests()
        pending = df[df['status'].isin(['SUBMITTED', 'RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED', 'SURRENDER_VERIFIED', 'SURRENDER_APPROVED', 'SURRENDER_AUTHORIZED'])]
        
        if pending.empty:
            st.info("No pending requests.")
        else:
            for idx, (_, req) in enumerate(pending.iterrows()):
                days_pending = get_pending_duration(req['submission_date'])
                current_status = req['status']
                
                with st.expander(f"📄 {req['request_number']} - {req['main_category']} - {req['request_type']} - {req['department_name']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Department:** {req['department_name']}")
                        st.write(f"**Submitted By:** {req['submitted_by']}")
                        st.write(f"**Submission Date:** {req['submission_date']}")
                        st.write(f"**Amount:** KES {req['amount']:,.2f}")
                        st.write(f"**Pending Duration:** {days_pending} working days")
                    with col2:
                        st.write(f"**Type:** {req['request_type']}")
                        if req['main_category'] == "Submit Payment Request":
                            if req['request_type'] == "Student Payment" and req.get('batch_no'):
                                st.write(f"**Batch No.:** {req['batch_no']}")
                            elif req['request_type'] == "Imprest" and req.get('imprest_no'):
                                st.write(f"**Imprest No.:** {req['imprest_no']}")
                            elif req['request_type'] == "Supplier Payment" and req.get('invoice_no'):
                                st.write(f"**Invoice No.:** {req['invoice_no']}")
                        else:
                            if req.get('surrender_number'):
                                st.write(f"**Surrender No.:** {req['surrender_number']}")
                    
                    if req.get('payment_description'):
                        st.write(f"**Description:** {req['payment_description']}")
                    
                    st.markdown("---")
                    
                    # Determine next action based on current status
                    if current_status == 'SUBMITTED':
                        st.subheader("✅ Confirmation Checklist")
                        checklist_approvals = st.checkbox("✓ All required approvals and signoffs obtained", key=f"approvals_{idx}")
                        checklist_documents = st.checkbox("✓ All relevant documents attached", key=f"documents_{idx}")
                        checklist_comments = st.text_area("Additional Comments (optional)", key=f"checklist_comments_{idx}")
                        
                        if st.button(f"📋 Confirm & Receive Request", key=f"receive_{idx}"):
                            if checklist_approvals and checklist_documents:
                                if verify_finance_password(st.text_input("Finance Password", type="password", key=f"pwd_receive_{idx}")):
                                    update_request_status(
                                        req['id'], 'RECEIVED_BY_FINANCE',
                                        performed_by=st.session_state.username,
                                        performed_by_role=st.session_state.user_role,
                                        performed_by_dept=st.session_state.user_dept,
                                        checklist_approvals=checklist_approvals,
                                        checklist_documents=checklist_documents,
                                        checklist_comments=checklist_comments
                                    )
                                    st.success(f"✅ Request {req['request_number']} confirmed and received!")
                                    st.rerun()
                                else:
                                    st.error("❌ Incorrect Finance Password!")
                            else:
                                st.error("❌ Please check both boxes to confirm the request")
                        
                        return_reason = st.text_input("Return Reason", key=f"return_{idx}")
                        if st.button(f"↩️ Return Request", key=f"return_btn_{idx}"):
                            if return_reason:
                                if verify_finance_password(st.text_input("Finance Password", type="password", key=f"pwd_return_{idx}")):
                                    update_request_status(
                                        req['id'], 'RETURNED', return_reason=return_reason,
                                        performed_by=st.session_state.username,
                                        performed_by_role=st.session_state.user_role,
                                        performed_by_dept=st.session_state.user_dept
                                    )
                                    st.warning(f"⚠️ Request {req['request_number']} returned!")
                                    st.rerun()
                                else:
                                    st.error("❌ Incorrect Finance Password!")
                            else:
                                st.error("❌ Please provide a return reason")
                    
                    elif current_status == 'RECEIVED_BY_FINANCE':
                        if req['main_category'] == "Submit Payment Request":
                            if st.button(f"📋 Mark as Payment Prepared", key=f"prepare_{idx}"):
                                pwd = st.text_input("Finance Password", type="password", key=f"pwd_prepare_{idx}")
                                if pwd:
                                    if verify_finance_password(pwd):
                                        update_request_status(req['id'], 'PAYMENT_PREPARED', performed_by=st.session_state.username)
                                        st.success(f"Request {req['request_number']} marked as Payment Prepared!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Incorrect Finance Password!")
                                else:
                                    st.warning("Please enter Finance Password")
                        else:
                            if st.button(f"📋 Mark as Surrender Verified", key=f"verify_surr_{idx}"):
                                pwd = st.text_input("Finance Password", type="password", key=f"pwd_verify_surr_{idx}")
                                if pwd:
                                    if verify_finance_password(pwd):
                                        update_request_status(req['id'], 'SURRENDER_VERIFIED', performed_by=st.session_state.username)
                                        st.success(f"Request {req['request_number']} marked as Surrender Verified!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Incorrect Finance Password!")
                                else:
                                    st.warning("Please enter Finance Password")
                    
                    elif current_status == 'PAYMENT_PREPARED':
                        if st.button(f"✅ Mark as Payment Verified", key=f"verify_{idx}"):
                            pwd = st.text_input("Finance Password", type="password", key=f"pwd_verify_{idx}")
                            if pwd:
                                if verify_finance_password(pwd):
                                    update_request_status(req['id'], 'PAYMENT_VERIFIED', performed_by=st.session_state.username)
                                    st.success(f"Request {req['request_number']} marked as Payment Verified!")
                                    st.rerun()
                                else:
                                    st.error("❌ Incorrect Finance Password!")
                            else:
                                st.warning("Please enter Finance Password")
                    
                    elif current_status == 'PAYMENT_VERIFIED':
                        if st.button(f"✅ Mark as Payment Approved", key=f"approve_{idx}"):
                            pwd = st.text_input("Finance Password", type="password", key=f"pwd_approve_{idx}")
                            if pwd:
                                if verify_finance_password(pwd):
                                    update_request_status(req['id'], 'PAYMENT_APPROVED', performed_by=st.session_state.username)
                                    st.success(f"Request {req['request_number']} marked as Payment Approved!")
                                    st.rerun()
                                else:
                                    st.error("❌ Incorrect Finance Password!")
                            else:
                                st.warning("Please enter Finance Password")
                    
                    elif current_status == 'PAYMENT_APPROVED':
                        if st.button(f"✅ Mark as Payment Authorized", key=f"authorize_{idx}"):
                            pwd = st.text_input("Finance Password", type="password", key=f"pwd_authorize_{idx}")
                            if pwd:
                                if verify_finance_password(pwd):
                                    update_request_status(req['id'], 'PAYMENT_AUTHORIZED', performed_by=st.session_state.username)
                                    st.success(f"Request {req['request_number']} marked as Payment Authorized!")
                                    st.rerun()
                                else:
                                    st.error("❌ Incorrect Finance Password!")
                            else:
                                st.warning("Please enter Finance Password")
                    
                    elif current_status == 'PAYMENT_AUTHORIZED':
                        payment_ref = st.text_input("Payment Reference Number", key=f"ref_{idx}")
                        if st.button(f"💰 Mark as Paid", key=f"paid_{idx}"):
                            if payment_ref:
                                pwd = st.text_input("Finance Password", type="password", key=f"pwd_paid_{idx}")
                                if pwd:
                                    if verify_finance_password(pwd):
                                        update_request_status(req['id'], 'PAID', performed_by=st.session_state.username)
                                        update_payment_details(req['id'], payment_ref)
                                        submitted_date = datetime.strptime(req['submission_date'], '%Y-%m-%d').date()
                                        days_taken = working_days_between(submitted_date, date.today())
                                        st.balloons()
                                        st.success(f"✅ Request {req['request_number']} completed! Took {days_taken} working days.")
                                        st.rerun()
                                    else:
                                        st.error("❌ Incorrect Finance Password!")
                                else:
                                    st.warning("Please enter Finance Password")
                            else:
                                st.error("❌ Please enter a payment reference number")
                    
                    elif current_status == 'SURRENDER_VERIFIED':
                        if st.button(f"✅ Mark as Surrender Approved", key=f"approve_surr_{idx}"):
                            pwd = st.text_input("Finance Password", type="password", key=f"pwd_approve_surr_{idx}")
                            if pwd:
                                if verify_finance_password(pwd):
                                    update_request_status(req['id'], 'SURRENDER_APPROVED', performed_by=st.session_state.username)
                                    st.success(f"Request {req['request_number']} marked as Surrender Approved!")
                                    st.rerun()
                                else:
                                    st.error("❌ Incorrect Finance Password!")
                            else:
                                st.warning("Please enter Finance Password")
                    
                    elif current_status == 'SURRENDER_APPROVED':
                        if st.button(f"✅ Mark as Surrender Authorized", key=f"authorize_surr_{idx}"):
                            pwd = st.text_input("Finance Password", type="password", key=f"pwd_authorize_surr_{idx}")
                            if pwd:
                                if verify_finance_password(pwd):
                                    update_request_status(req['id'], 'SURRENDER_AUTHORIZED', performed_by=st.session_state.username)
                                    st.success(f"Request {req['request_number']} marked as Surrender Authorized!")
                                    st.rerun()
                                else:
                                    st.error("❌ Incorrect Finance Password!")
                            else:
                                st.warning("Please enter Finance Password")
                    
                    elif current_status == 'SURRENDER_AUTHORIZED':
                        payment_ref = st.text_input("Payment Reference Number", key=f"ref_surr_{idx}")
                        if st.button(f"💰 Mark as Cleared", key=f"cleared_{idx}"):
                            if payment_ref:
                                pwd = st.text_input("Finance Password", type="password", key=f"pwd_cleared_{idx}")
                                if pwd:
                                    if verify_finance_password(pwd):
                                        update_request_status(req['id'], 'CLEARED', performed_by=st.session_state.username)
                                        update_payment_details(req['id'], payment_ref)
                                        st.balloons()
                                        st.success(f"✅ Request {req['request_number']} cleared!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Incorrect Finance Password!")
                                else:
                                    st.warning("Please enter Finance Password")
                            else:
                                st.error("❌ Please enter a reference number")
                    
                    # Show transaction logs
                    st.markdown("---")
                    st.subheader("📜 Transaction Logs")
                    display_transaction_logs(req['id'])
    else:
        st.error("Access denied. Finance only.")


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
# ADMIN PANEL - FULL 5 TABS
# ================================================================
elif choice == "⚙️ Admin Panel" and st.session_state.user_role == "ADMIN":
    st.markdown("<h1 style='color: #00843D;'>⚙️ Admin Panel</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["👥 Users", "🏢 Departments", "📦 Products", "💰 Funders", "📅 Financial Years", "🔐 Finance Settings"])
    
    with tab1:
        st.subheader("👥 User Management")
        users_df = get_all_users()
        st.dataframe(users_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("➕ Add New User")
        with st.form("add_user_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password (default)", type="password", value="password123")
            new_full_name = st.text_input("Full Name")
            new_role = st.selectbox("Role", ["DEPARTMENT", "FINANCE", "MANAGEMENT", "ADMIN"])
            
            depts = get_departments()
            dept_options = {row['name']: row['id'] for _, row in depts.iterrows()}
            new_department = st.selectbox("Department (if DEPARTMENT role)", ["None"] + list(dept_options.keys()))
            
            if st.form_submit_button("Create User"):
                if new_username and new_password and new_full_name:
                    dept_id = dept_options.get(new_department) if new_department != "None" else None
                    success = create_user(new_username, new_password, new_role, dept_id, new_full_name)
                    if success:
                        st.success(f"✅ User {new_username} ({new_full_name}) created!")
                        st.rerun()
                    else:
                        st.error("❌ Username already exists!")
    
    with tab2:
        st.subheader("🏢 Department Management")
        depts = get_departments()
        st.dataframe(depts, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("➕ Add New Department")
        with st.form("add_dept_form"):
            dept_name = st.text_input("Department Name")
            col1, col2 = st.columns(2)
            with col1:
                can_imprest = st.checkbox("Imprest", True)
                can_petty = st.checkbox("Petty Cash", True)
                can_supplier = st.checkbox("Supplier", False)
            with col2:
                can_student = st.checkbox("Student Payment", False)
                can_surrender = st.checkbox("Surrender", True)
                can_refund = st.checkbox("Refund", False)
            requires_product = st.checkbox("Requires Product Type", False)
            requires_funder = st.checkbox("Requires Funder", False)
            is_finance = st.checkbox("Finance Department", False)
            
            if st.form_submit_button("Create Department"):
                if dept_name:
                    perms = [can_imprest, can_petty, can_supplier, can_student, can_surrender, can_refund, requires_product, requires_funder, is_finance]
                    success = create_department(dept_name, perms)
                    if success:
                        st.success(f"✅ Department {dept_name} created!")
                        st.rerun()
    
    with tab3:
        st.subheader("📦 Product Management (Lending)")
        products = get_products()
        st.dataframe(products, use_container_width=True)
        
        st.markdown("---")
        st.subheader("➕ Add New Product")
        with st.form("add_product_form"):
            name = st.text_input("Product Name")
            category = st.selectbox("Category", ["LOAN", "SCHOLARSHIP"])
            has_payment = st.checkbox("Has Payment Category (Tuition/Upkeep)")
            has_sem = st.checkbox("Has Semester", True)
            if st.form_submit_button("Add Product"):
                if name:
                    success = add_product(name, category, has_payment, has_sem)
                    if success:
                        st.success(f"✅ Product {name} added!")
                        st.rerun()
                    else:
                        st.error("❌ Product name already exists!")
    
    with tab4:
        st.subheader("💰 Funder Management (ERM)")
        funders = get_funders()
        if funders:
            st.write("**Current Funders/Partners:**")
            for f in funders:
                st.write(f"• {f}")
        
        st.markdown("---")
        st.subheader("➕ Add New Funder")
        with st.form("add_funder_form"):
            funder_name = st.text_input("Funder/Partner Name")
            if st.form_submit_button("Add Funder"):
                if funder_name:
                    success = add_funder(funder_name)
                    if success:
                        st.success(f"✅ Funder {funder_name} added!")
                        st.rerun()
                    else:
                        st.error("❌ Funder name already exists!")
    
    with tab5:
        st.subheader("📅 Financial Year Management")
        financial_years = get_financial_years()
        if financial_years:
            st.write("**Current Financial Years:**")
            for fy in financial_years:
                st.write(f"• {fy}")
        
        st.markdown("---")
        st.subheader("➕ Add New Financial Year")
        with st.form("add_fy_form"):
            fy_name = st.text_input("Financial Year (e.g., 2027/2028)")
            if st.form_submit_button("Add Financial Year"):
                if fy_name:
                    success = add_financial_year(fy_name)
                    if success:
                        st.success(f"✅ Financial Year {fy_name} added!")
                        st.rerun()
                    else:
                        st.error("❌ Financial year already exists!")
        
        st.markdown("---")
        st.subheader("📚 Semester Management")
        semesters = get_semesters()
        if semesters:
            st.write("**Current Semesters:**")
            for s in semesters:
                st.write(f"• {s}")
        
        st.markdown("---")
        st.subheader("➕ Add New Semester")
        with st.form("add_semester_form"):
            sem_name = st.text_input("Semester Name (e.g., Semester 3)")
            if st.form_submit_button("Add Semester"):
                if sem_name:
                    success = add_semester(sem_name)
                    if success:
                        st.success(f"✅ Semester {sem_name} added!")
                        st.rerun()
                    else:
                        st.error("❌ Semester name already exists!")
    
    with tab6:
        st.subheader("🔐 Finance Password Settings")
        st.info("This password is required for all finance actions (Confirm, Prepare, Verify, Approve, Authorize, Pay/Clear).")
        
        current_pwd = get_finance_password()
        st.text_input("Current Finance Password", value="••••••••", disabled=True)
        
        with st.form("update_finance_pwd_form"):
            new_password = st.text_input("New Finance Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Update Finance Password"):
                if new_password and len(new_password) >= 4:
                    if new_password == confirm_password:
                        update_finance_password(new_password)
                        st.success("✅ Finance password updated successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Passwords do not match!")
                else:
                    st.error("❌ Password must be at least 4 characters!")


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
