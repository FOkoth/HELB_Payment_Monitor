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
    
    .status-paid {
        background-color: #00843D20;
        color: #00843D;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: bold;
    }
    
    .status-cleared {
        background-color: #00843D20;
        color: #00843D;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: bold;
    }
    
    .status-pending {
        background-color: #DC354520;
        color: #DC3545;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: bold;
    }
    
    .status-confirmed {
        background-color: #00BCD420;
        color: #00BCD4;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: bold;
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
    
    st.markdown(f"""
        <div class='user-info'>
            <strong>{st.session_state.full_name}</strong><br>
            <span style='color: #00843D;'>{st.session_state.user_role}</span><br>
            <span style='font-size: 0.8rem;'>{st.session_state.user_dept}</span>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    # Dynamic menu based on role
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


# ================================================================
# FUNCTION TO DISPLAY TRANSACTION LOGS
# ================================================================
def display_transaction_logs(request_id):
    """Display transaction logs for a request"""
    logs = get_request_logs(request_id)
    if logs:
        for log in logs:
            timestamp = datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %H:%M')
            action = log['action']
            
            if action == 'SUBMITTED':
                css_class = "log-submitted"
                icon = "📝"
                text = f"**{timestamp}** - Submitted by {log['performed_by']} ({log['performed_by_dept']})"
            elif action == 'RECEIVED':
                css_class = "log-received"
                icon = "📥"
                text = f"**{timestamp}** - Received by {log['performed_by']} (Finance)"
            elif action == 'CONFIRMED':
                css_class = "log-confirmed"
                icon = "✅"
                text = f"**{timestamp}** - Confirmed by {log['performed_by']} (Finance) with checklist"
            elif action == 'RETURNED':
                css_class = "log-returned"
                icon = "↩️"
                text = f"**{timestamp}** - Returned by {log['performed_by']} - Reason: {log['comment']}"
            elif action == 'RESUBMITTED':
                css_class = "log-resubmitted"
                icon = "📤"
                text = f"**{timestamp}** - Resubmitted by {log['performed_by']} ({log['performed_by_dept']})"
            elif action in ['PAID', 'CLEARED']:
                css_class = "log-paid"
                icon = "✅"
                text = f"**{timestamp}** - {action} by {log['performed_by']}"
            else:
                css_class = "log-entry"
                icon = "📌"
                text = f"**{timestamp}** - {action}: {log['comment'] if log['comment'] else ''}"
            
            st.markdown(f"<div class='log-entry {css_class}'>{icon} {text}</div>", unsafe_allow_html=True)
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
        returned = len(df[df['status'] == 'RETURNED'])
        total_amount = df['amount'].sum()
        
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
            elif row['status'] == 'CONFIRMED_BY_FINANCE':
                time_lapsed = get_time_lapsed_from_confirmation(row['id'])
                if time_lapsed:
                    status_display = f'<span class="status-confirmed">📌 Confirmed ({time_lapsed} days)</span>'
                else:
                    status_display = '<span class="status-confirmed">📌 Confirmed</span>'
            elif row['status'] == 'RETURNED':
                status_display = f'<span class="status-pending">↩️ Returned on {row["date_returned"]}</span>'
            else:
                days = get_pending_duration(row['submission_date'])
                status_display = f'<span class="status-pending">⏳ Pending ({days} days)</span>'
            
            with st.expander(f"📄 {row['request_number']} - {row['main_category']} - {row['request_type']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Amount:** KES {row['amount']:,.2f}")
                    st.write(f"**Submitted:** {row['submission_date']}")
                    if row['status'] == 'CONFIRMED_BY_FINANCE':
                        confirmed_date = row.get('date_confirmed_by_finance', 'N/A')
                        st.write(f"**Confirmed by Finance:** {confirmed_date}")
                with col2:
                    st.write(f"**Financial Year:** {row.get('financial_year', 'N/A')}")
                    st.markdown(f"**Status:** {status_display}", unsafe_allow_html=True)
                
                if row.get('payment_description'):
                    st.write(f"**Description:** {row['payment_description']}")
                
                # Show reference number based on type
                if row['main_category'] == "Submit Payment Request":
                    if row['request_type'] == "Student Payment" and row.get('batch_no'):
                        st.write(f"**Batch No.:** {row['batch_no']}")
                        if row.get('product_type'):
                            st.write(f"**Product:** {row['product_type']}")
                        if row.get('semester'):
                            st.write(f"**Semester:** {row['semester']}")
                        if row.get('payment_type'):
                            st.write(f"**Payment Category:** {row['payment_type']}")
                    elif row['request_type'] == "Imprest" and row.get('imprest_no'):
                        st.write(f"**Imprest No.:** {row['imprest_no']}")
                    elif row['request_type'] == "Petty Cash" and row.get('imprest_no'):
                        st.write(f"**Petty Cash No.:** {row['imprest_no']}")
                    elif row['request_type'] == "Supplier Payment" and row.get('invoice_no'):
                        st.write(f"**Invoice No.:** {row['invoice_no']}")
                        st.write(f"**Supplier:** {row.get('supplier_name', 'N/A')}")
                    elif row['request_type'] == "Salary Payment":
                        st.write(f"**Month:** {row.get('salary_month', 'N/A')}")
                        st.write(f"**Year:** {row.get('salary_year', 'N/A')}")
                    elif row['request_type'] == "Refund Payment" and row.get('imprest_no'):
                        st.write(f"**Refund ID:** {row['imprest_no']}")
                        st.write(f"**Customer:** {row.get('customer_name', 'N/A')}")
                else:  # Surrender
                    if row.get('surrender_number'):
                        st.write(f"**Surrender No.:** {row['surrender_number']}")
                    if row.get('staff_name'):
                        st.write(f"**Staff Name:** {row['staff_name']}")
                
                st.markdown("---")
                st.subheader("📜 Transaction Logs")
                display_transaction_logs(row['id'])


# ================================================================
# MANAGEMENT DASHBOARD
# ================================================================
elif choice == "📈 Management Dashboard":
    st.markdown("<h1 style='color: #00843D;'>📈 Management Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p><strong>Executive View</strong> - All departments, all requests</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        financial_years = ["All"] + get_financial_years()
        selected_fy = st.selectbox("Financial Year", financial_years, key="mgmt_fy")
    with col2:
        quarters = ["All", "Q1 (Jul-Sep)", "Q2 (Oct-Dec)", "Q3 (Jan-Mar)", "Q4 (Apr-Jun)"]
        selected_quarter = st.selectbox("Quarter", quarters, key="mgmt_qtr")
    
    stats = get_management_dashboard_stats(selected_fy if selected_fy != "All" else None,
                                            selected_quarter if selected_quarter != "All" else None)
    
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #00843D; margin:0;">{stats['total_requests']}</h3>
                <p>Total Requests</p>
                <small>📥 Received: {stats['total_received']} | ↩️ Returned: {stats['total_returned']}</small>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #00843D; margin:0;">KES {stats['total_amount']:,.0f}</h3>
                <p>Total Amount</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #00843D; margin:0;">{stats['avg_completion_time']:.1f}</h3>
                <p>Avg Completion (Days)</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        breach_color = "#DC3545" if stats['breach_rate'] > 20 else "#00843D"
        st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: {breach_color}; margin:0;">{stats['breach_rate']:.1f}%</h3>
                <p>Breach Rate</p>
                <small>{stats['total_breaches']} of {stats['completed_count']} requests</small>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Monthly Trends")
        trend_data = get_trend_data(selected_fy if selected_fy != "All" else None)
        if not trend_data.empty:
            fig = px.line(trend_data, x='month', y='request_count', 
                         title="Request Volume Trend",
                         color_discrete_sequence=['#00843D'])
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("💰 Amount by Type")
        df = get_requests()
        if selected_fy != "All":
            df = df[df['financial_year'] == selected_fy]
        amount_by_type = df.groupby('main_category')['amount'].sum().reset_index()
        if not amount_by_type.empty:
            fig = px.bar(amount_by_type, x='main_category', y='amount',
                        color_discrete_sequence=['#00843D', '#FFB81C'])
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("🏢 Department Performance Summary")
    dept_summary = get_all_departments_summary()
    if not dept_summary.empty:
        st.dataframe(dept_summary, use_container_width=True, hide_index=True)
    
    st.subheader("📋 All Requests")
    all_requests = get_requests()
    if selected_fy != "All":
        all_requests = all_requests[all_requests['financial_year'] == selected_fy]
    display_cols = ['request_number', 'main_category', 'request_type', 'department_name', 'amount', 'status', 'submission_date']
    st.dataframe(all_requests[display_cols], use_container_width=True, hide_index=True)


# ================================================================
# CHECK PAYMENT STATUS (BATCH SEARCH)
# ================================================================
elif choice == "🔍 Check Payment Status":
    st.markdown("<h1 style='color: #00843D;'>🔍 Check Payment Status</h1>", unsafe_allow_html=True)
    st.markdown("<p>Enter a Batch Number to check the payment status of a student payment request.</p>", unsafe_allow_html=True)
    
    batch_numbers = get_all_batch_numbers()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if batch_numbers:
            selected_batch = st.selectbox("Select Batch Number", [""] + batch_numbers)
            batch_no = st.text_input("Or enter Batch Number manually", value=selected_batch if selected_batch else "")
        else:
            batch_no = st.text_input("Enter Batch Number")
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_clicked = st.button("🔍 Search", use_container_width=True)
    
    if search_clicked and batch_no:
        results = search_by_batch_number(batch_no)
        
        if results:
            st.success(f"✅ Found {len(results)} record(s) for Batch Number: {batch_no}")
            st.markdown("---")
            
            for result in results:
                if result['status'] == 'PAID':
                    status_color = "#00843D"
                    status_icon = "✅"
                    status_text = "Paid"
                elif result['status'] == 'CLEARED':
                    status_color = "#00843D"
                    status_icon = "✅"
                    status_text = "Cleared"
                elif result['status'] == 'CONFIRMED_BY_FINANCE':
                    status_color = "#00BCD4"
                    status_icon = "📌"
                    status_text = "Confirmed by Finance"
                elif result['status'] == 'RETURNED':
                    status_color = "#DC3545"
                    status_icon = "↩️"
                    status_text = "Returned"
                else:
                    status_color = "#FFB81C"
                    status_icon = "⏳"
                    status_text = "Pending"
                
                st.markdown(f"""
                <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border-left: 4px solid {status_color};'>
                    <h3 style='color: {status_color}; margin: 0;'>{status_icon} {status_text}</h3>
                    <table style='width: 100%; margin-top: 0.5rem;'>
                        <tr>
                            <td><strong>Request Number:</strong></td>
                            <td>{result['request_number']}</td>
                         </tr>
                         <tr>
                             <td><strong>Department:</strong></td>
                             <td>{result['department']}</td>
                         </tr>
                         <tr>
                             <td><strong>Amount:</strong></td>
                             <td>KES {result['amount']:,.2f}</td>
                         </tr>
                         <tr>
                             <td><strong>Submission Date:</strong></td>
                             <td>{result['submission_date']}</td>
                         </tr>
                """, unsafe_allow_html=True)
                
                if result['payment_date']:
                    st.markdown(f"""
                         <tr>
                             <td><strong>Payment Date:</strong></td>
                             <td>{result['payment_date']}</td>
                         </tr>
                         <tr>
                             <td><strong>Payment Reference:</strong></td>
                             <td>{result['payment_reference'] if result['payment_reference'] else 'N/A'}</td>
                         </tr>
                    """, unsafe_allow_html=True)
                
                st.markdown("</table></div>", unsafe_allow_html=True)
        else:
            st.error(f"❌ No records found for Batch Number: {batch_no}")
    
    if batch_numbers:
        st.markdown("---")
        st.subheader("📋 Recent Batch Numbers")
        for batch in batch_numbers[:10]:
            st.write(f"• {batch}")


# ================================================================
# NEW REQUEST - WITH PROPER CONDITIONAL STUDENT PAYMENT FIELDS
# ================================================================
elif choice == "📝 New Request":
    st.markdown("<h1 style='color: #00843D;'>📝 Create New Request</h1>", unsafe_allow_html=True)
    
    allowed_main_categories = get_allowed_main_categories(st.session_state.user_role, st.session_state.user_dept)
    
    if not allowed_main_categories:
        st.error("Your role does not have permission to submit requests.")
    else:
        # Step 1: Select Main Category
        main_category = st.radio(
            "What would you like to do?",
            allowed_main_categories,
            horizontal=True
        )
        
        st.markdown("---")
        
        # Step 2: Get allowed request types based on main category
        allowed_types = get_allowed_request_types(st.session_state.user_role, st.session_state.user_dept, main_category)
        
        if not allowed_types:
            st.error("No request types available for your selection.")
        else:
            selected_type = st.selectbox("Select Request Type", allowed_types)
            st.markdown("---")
            
            # Common fields for all
            with st.form(key="request_form"):
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
                
                # ======================================================
                # PAYMENT REQUEST TYPES
                # ======================================================
                if main_category == "Submit Payment Request":
                    
                    # STUDENT PAYMENT - WITH PROPER CONDITIONAL FIELDS
                    if selected_type == "Student Payment":
                        st.subheader("🎓 Student Payment Details")
                        
                        # Product Type selection (OUTSIDE form for dynamic updates)
                        products = get_products()
                        if not products.empty:
                            product_type = st.selectbox("Product Type", products['name'].tolist(), key="student_product_type")
                        else:
                            product_type = st.selectbox("Product Type", ["Undergraduate", "TVET", "Jielimishe"], key="student_product_type")
                        
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
                            # Jielimishe - No semester, no payment category
                            semester = None
                            payment_category = "Tuition"
                        
                        st.markdown("---")
                        
                        # Batch Number (for ALL student payments)
                        batch_no = st.text_input("Batch No.", placeholder="Enter batch number")
                        
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
                    
                    # IMPREST
                    elif selected_type == "Imprest":
                        st.subheader("💰 Imprest Payment Details")
                        imprest_no = st.text_input("Imprest No.", placeholder="Enter imprest number")
                        
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
                    
                    # PETTY CASH
                    elif selected_type == "Petty Cash":
                        st.subheader("💵 Petty Cash Payment Details")
                        petty_cash_no = st.text_input("Petty Cash No.", placeholder="Enter petty cash number")
                        
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
                    
                    # SUPPLIER PAYMENT
                    elif selected_type == "Supplier Payment":
                        st.subheader("🏢 Supplier Payment Details")
                        invoice_no = st.text_input("Invoice No.", placeholder="Enter invoice number")
                        supplier_name = st.text_input("Supplier Name")
                        
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
                    
                    # SALARY PAYMENT
                    elif selected_type == "Salary Payment":
                        st.subheader("👔 Salary Payment Details")
                        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                        salary_month = st.selectbox("Salary Month", months)
                        current_year = datetime.now().year
                        salary_year = st.number_input("Year", min_value=2020, max_value=2030, value=current_year)
                        
                        request_data = {
                            'main_category': main_category,
                            'request_type': selected_type,
                            'department_id': st.session_state.user_dept_id,
                            'department_name': st.session_state.user_dept,
                            'submitted_by': st.session_state.username,
                            'amount': amount,
                            'payment_description': payment_description,
                            'financial_year': financial_year,
                            'salary_month': salary_month,
                            'salary_year': salary_year,
                            'status': 'SUBMITTED'
                        }
                    
                    # REFUND PAYMENT
                    elif selected_type == "Refund Payment":
                        st.subheader("🔄 Refund Payment Details")
                        refund_id = st.text_input("Refund ID", placeholder="Enter refund ID")
                        customer_name = st.text_input("Customer Name")
                        customer_id = st.text_input("Customer ID Number")
                        
                        request_data = {
                            'main_category': main_category,
                            'request_type': selected_type,
                            'department_id': st.session_state.user_dept_id,
                            'department_name': st.session_state.user_dept,
                            'submitted_by': st.session_state.username,
                            'amount': amount,
                            'payment_description': payment_description,
                            'financial_year': financial_year,
                            'imprest_no': refund_id,
                            'customer_name': customer_name,
                            'customer_id': customer_id,
                            'status': 'SUBMITTED'
                        }
                    
                    else:
                        st.error("Invalid request type")
                        st.stop()
                
                # ======================================================
                # SURRENDER
                # ======================================================
                else:  # Submit Surrender
                    st.subheader("📤 Surrender Details")
                    surrender_no = st.text_input("Surrender No.", placeholder="Enter surrender number")
                    staff_name = st.text_input("Staff Name")
                    
                    request_data = {
                        'main_category': main_category,
                        'request_type': selected_type,
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
                
                submitted = st.form_submit_button("Submit Request", use_container_width=True)
                
                if submitted:
                    errors = []
                    if amount <= 0:
                        errors.append("Amount must be greater than 0")
                    if not payment_description:
                        errors.append("Payment Description is required")
                    
                    # Validation based on type
                    if main_category == "Submit Payment Request":
                        if selected_type == "Student Payment":
                            if not request_data.get('batch_no'):
                                errors.append("Batch No. is required")
                            if request_data.get('product_type') in ["Undergraduate", "TVET"]:
                                if not request_data.get('semester'):
                                    errors.append("Semester is required")
                                if not request_data.get('payment_type'):
                                    errors.append("Payment Category is required")
                        elif selected_type == "Imprest" and not request_data.get('imprest_no'):
                            errors.append("Imprest No. is required")
                        elif selected_type == "Petty Cash" and not request_data.get('imprest_no'):
                            errors.append("Petty Cash No. is required")
                        elif selected_type == "Supplier Payment" and (not request_data.get('invoice_no') or not request_data.get('supplier_name')):
                            errors.append("Invoice No. and Supplier Name are required")
                        elif selected_type == "Salary Payment" and not request_data.get('salary_month'):
                            errors.append("Salary Month is required")
                        elif selected_type == "Refund Payment" and (not request_data.get('imprest_no') or not request_data.get('customer_name')):
                            errors.append("Refund ID and Customer Name are required")
                    else:  # Surrender
                        if not request_data.get('surrender_number'):
                            errors.append("Surrender No. is required")
                        if not request_data.get('staff_name'):
                            errors.append("Staff Name is required")
                    
                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
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
                elif row['status'] == 'CONFIRMED_BY_FINANCE':
                    time_lapsed = get_time_lapsed_from_confirmation(row['id'])
                    if time_lapsed:
                        status_display = f'<span class="status-confirmed">📌 Confirmed ({time_lapsed} days)</span>'
                    else:
                        status_display = '<span class="status-confirmed">📌 Confirmed</span>'
                elif row['status'] == 'RETURNED':
                    status_display = f'<span class="status-pending">↩️ Returned on {row["date_returned"]}</span>'
                else:
                    days = get_pending_duration(row['submission_date'])
                    status_display = f'<span class="status-pending">⏳ Pending ({days} days)</span>'
                
                with st.expander(f"📄 {row['request_number']} - {row['main_category']} - {row['request_type']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Amount:** KES {row['amount']:,.2f}")
                        st.write(f"**Submitted:** {row['submission_date']}")
                        if row['status'] == 'CONFIRMED_BY_FINANCE':
                            confirmed_date = row.get('date_confirmed_by_finance', 'N/A')
                            st.write(f"**Confirmed by Finance:** {confirmed_date}")
                    with col2:
                        st.write(f"**Financial Year:** {row.get('financial_year', 'N/A')}")
                        st.markdown(f"**Status:** {status_display}", unsafe_allow_html=True)
                    
                    # Show reference number based on type
                    if row['main_category'] == "Submit Payment Request":
                        if row['request_type'] == "Student Payment" and row.get('batch_no'):
                            st.write(f"**Batch No.:** {row['batch_no']}")
                            if row.get('product_type'):
                                st.write(f"**Product:** {row['product_type']}")
                            if row.get('semester'):
                                st.write(f"**Semester:** {row['semester']}")
                            if row.get('payment_type'):
                                st.write(f"**Payment Category:** {row['payment_type']}")
                        elif row['request_type'] == "Imprest" and row.get('imprest_no'):
                            st.write(f"**Imprest No.:** {row['imprest_no']}")
                        elif row['request_type'] == "Petty Cash" and row.get('imprest_no'):
                            st.write(f"**Petty Cash No.:** {row['imprest_no']}")
                        elif row['request_type'] == "Supplier Payment" and row.get('invoice_no'):
                            st.write(f"**Invoice No.:** {row['invoice_no']}")
                            st.write(f"**Supplier:** {row.get('supplier_name', 'N/A')}")
                        elif row['request_type'] == "Salary Payment":
                            st.write(f"**Month:** {row.get('salary_month', 'N/A')}")
                            st.write(f"**Year:** {row.get('salary_year', 'N/A')}")
                        elif row['request_type'] == "Refund Payment" and row.get('imprest_no'):
                            st.write(f"**Refund ID:** {row['imprest_no']}")
                            st.write(f"**Customer:** {row.get('customer_name', 'N/A')}")
                    else:
                        if row.get('surrender_number'):
                            st.write(f"**Surrender No.:** {row['surrender_number']}")
                    
                    if row.get('payment_description'):
                        st.write(f"**Description:** {row['payment_description']}")
                    
                    if row['status'] == 'RETURNED' and row.get('return_reason'):
                        st.error(f"**Return Reason:** {row['return_reason']}")
                    
                    st.markdown("---")
                    st.subheader("📜 Transaction Logs")
                    display_transaction_logs(row['id'])


# ================================================================
# RETURNED REQUESTS - REVIEW AND RESUBMIT
# ================================================================
elif choice == "↩️ Returned Requests":
    st.markdown("<h1 style='color: #00843D;'>↩️ Returned Requests</h1>", unsafe_allow_html=True)
    st.markdown("<p>Review requests that were returned by Finance and resubmit with corrections.</p>", unsafe_allow_html=True)
    
    df = get_returned_requests(st.session_state.user_dept)
    
    if df.empty:
        st.info("No returned requests found for your department.")
    else:
        st.info(f"📋 You have {len(df)} returned request(s) that need your attention.")
        
        for idx, (_, req) in enumerate(df.iterrows()):
            with st.expander(f"📄 {req['request_number']} - {req['main_category']} - {req['request_type']} - Returned on: {req['date_returned']}"):
                st.markdown(f"**Return Reason:** :red[{req['return_reason']}]")
                st.markdown(f"**Original Submission Date:** {req['submission_date']}")
                st.markdown(f"**Original Amount:** KES {req['amount']:,.2f}")
                
                if req.get('payment_description'):
                    st.markdown(f"**Original Description:** {req['payment_description']}")
                
                st.markdown("---")
                st.subheader("📝 Resubmit Request (Make Corrections)")
                
                with st.form(key=f"resubmit_form_{req['id']}"):
                    new_amount = st.number_input("Amount (KShs.)", value=float(req['amount']), min_value=0.0, format="%.2f", step=1000.0)
                    new_description = st.text_area("Payment Description", value=req.get('payment_description', ''))
                    
                    # Request type specific fields
                    if req['main_category'] == "Submit Payment Request":
                        if req['request_type'] == "Student Payment":
                            new_batch_no = st.text_input("Batch No.", value=req.get('batch_no', ''))
                        elif req['request_type'] == "Imprest":
                            new_imprest_no = st.text_input("Imprest No.", value=req.get('imprest_no', ''))
                        elif req['request_type'] == "Petty Cash":
                            new_petty_cash_no = st.text_input("Petty Cash No.", value=req.get('imprest_no', ''))
                        elif req['request_type'] == "Supplier Payment":
                            new_invoice_no = st.text_input("Invoice No.", value=req.get('invoice_no', ''))
                            new_supplier_name = st.text_input("Supplier Name", value=req.get('supplier_name', ''))
                        elif req['request_type'] == "Salary Payment":
                            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                            current_month = req.get('salary_month', 'January')
                            month_index = months.index(current_month) if current_month in months else 0
                            new_salary_month = st.selectbox("Salary Month", months, index=month_index)
                            new_salary_year = st.number_input("Year", value=int(req.get('salary_year', datetime.now().year)) if req.get('salary_year') else datetime.now().year)
                        elif req['request_type'] == "Refund Payment":
                            new_refund_id = st.text_input("Refund ID", value=req.get('imprest_no', ''))
                            new_customer_name = st.text_input("Customer Name", value=req.get('customer_name', ''))
                            new_customer_id = st.text_input("Customer ID Number", value=req.get('customer_id', ''))
                    else:  # Surrender
                        new_surrender_no = st.text_input("Surrender No.", value=req.get('surrender_number', ''))
                        new_staff_name = st.text_input("Staff Name", value=req.get('staff_name', ''))
                    
                    resubmitted = st.form_submit_button("📤 Resubmit Request", use_container_width=True)
                    
                    if resubmitted:
                        update_data = {
                            'amount': new_amount,
                            'payment_description': new_description,
                            'status': 'SUBMITTED'
                        }
                        
                        if req['main_category'] == "Submit Payment Request":
                            if req['request_type'] == "Student Payment":
                                update_data['batch_no'] = new_batch_no
                            elif req['request_type'] == "Imprest":
                                update_data['imprest_no'] = new_imprest_no
                            elif req['request_type'] == "Petty Cash":
                                update_data['imprest_no'] = new_petty_cash_no
                            elif req['request_type'] == "Supplier Payment":
                                update_data['invoice_no'] = new_invoice_no
                                update_data['supplier_name'] = new_supplier_name
                            elif req['request_type'] == "Salary Payment":
                                update_data['salary_month'] = new_salary_month
                                update_data['salary_year'] = new_salary_year
                            elif req['request_type'] == "Refund Payment":
                                update_data['imprest_no'] = new_refund_id
                                update_data['customer_name'] = new_customer_name
                                update_data['customer_id'] = new_customer_id
                        else:
                            update_data['surrender_number'] = new_surrender_no
                            update_data['staff_name'] = new_staff_name
                        
                        resubmit_request(req['id'], update_data)
                        
                        add_request_log(
                            req['id'], req['request_number'], "RESUBMITTED", 
                            "RETURNED", "SUBMITTED", "Request resubmitted with corrections",
                            st.session_state.username, st.session_state.user_role, 
                            st.session_state.user_dept
                        )
                        
                        st.success(f"✅ Request {req['request_number']} has been resubmitted successfully!")
                        st.balloons()
                        st.rerun()
                
                st.markdown("---")
                st.subheader("📜 Transaction Logs")
                display_transaction_logs(req['id'])


# ================================================================
# APPROVAL QUEUE - WITH CHECKLIST
# ================================================================
elif choice == "✅ Approval Queue":
    if st.session_state.user_role in ["FINANCE", "ADMIN"] or st.session_state.is_finance:
        st.markdown("<h1 style='color: #00843D;'>✅ Approval Queue</h1>", unsafe_allow_html=True)
        
        # Show pending counts
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
                st.markdown(f'<span class="warning-badge">⏳ {pending_completion} requests pending payment completion</span>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        df = get_requests()
        pending = df[df['status'].isin(['SUBMITTED', 'CONFIRMED_BY_FINANCE'])]
        
        if pending.empty:
            st.info("No pending requests.")
        else:
            for idx, (_, req) in enumerate(pending.iterrows()):
                days_pending = get_pending_duration(req['submission_date'])
                
                if req['status'] == 'SUBMITTED':
                    status_text = f"Awaiting Confirmation ({days_pending} days)"
                    status_color = "#DC3545"
                else:
                    time_lapsed = get_time_lapsed_from_confirmation(req['id'])
                    if time_lapsed:
                        status_text = f"Confirmed - Awaiting Payment ({time_lapsed} days)"
                    else:
                        status_text = "Confirmed - Awaiting Payment"
                    status_color = "#00BCD4"
                
                with st.expander(f"📄 {req['request_number']} - {req['main_category']} - {req['request_type']} - {req['department_name']} - {status_text}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Department:** {req['department_name']}")
                        st.write(f"**Submitted By:** {req['submitted_by']}")
                        st.write(f"**Submission Date:** {req['submission_date']}")
                        st.write(f"**Amount:** KES {req['amount']:,.2f}")
                    with col2:
                        st.write(f"**Type:** {req['request_type']}")
                        if req['main_category'] == "Submit Payment Request":
                            if req['request_type'] == "Student Payment" and req.get('batch_no'):
                                st.write(f"**Batch No.:** {req['batch_no']}")
                                if req.get('product_type'):
                                    st.write(f"**Product:** {req['product_type']}")
                                if req.get('semester'):
                                    st.write(f"**Semester:** {req['semester']}")
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
                    
                    if req['status'] == 'SUBMITTED':
                        st.subheader("✅ Confirmation Checklist")
                        st.markdown("<p>Please verify the following before confirming this request:</p>", unsafe_allow_html=True)
                        
                        checklist_approvals = st.checkbox("✓ All required approvals and signoffs obtained", key=f"approvals_{idx}")
                        checklist_documents = st.checkbox("✓ All relevant documents attached", key=f"documents_{idx}")
                        checklist_comments = st.text_area("Additional Comments (optional)", key=f"checklist_comments_{idx}")
                        
                        col3, col4, col5 = st.columns(3)
                        
                        with col3:
                            if st.button(f"✅ Confirm & Receive", key=f"confirm_{idx}"):
                                if checklist_approvals and checklist_documents:
                                    update_request_status(
                                        req['id'], 'CONFIRMED_BY_FINANCE',
                                        performed_by=st.session_state.username,
                                        performed_by_role=st.session_state.user_role,
                                        performed_by_dept=st.session_state.user_dept,
                                        checklist_approvals=checklist_approvals,
                                        checklist_documents=checklist_documents,
                                        checklist_comments=checklist_comments
                                    )
                                    st.success(f"✅ Request {req['request_number']} confirmed and received by Finance")
                                    st.rerun()
                                else:
                                    st.error("❌ Please check both boxes to confirm the request")
                        
                        with col4:
                            comment = st.text_area("Comment", key=f"comment_{idx}")
                        
                        with col5:
                            reason = st.text_input("Return Reason", key=f"return_{idx}")
                            if st.button(f"↩️ Return Request", key=f"return_btn_{idx}"):
                                if reason:
                                    update_request_status(
                                        req['id'], 'RETURNED', 
                                        finance_comment=comment, 
                                        return_reason=reason,
                                        performed_by=st.session_state.username,
                                        performed_by_role=st.session_state.user_role,
                                        performed_by_dept=st.session_state.user_dept
                                    )
                                    st.warning(f"⚠️ Request {req['request_number']} returned to department")
                                    st.rerun()
                                else:
                                    st.error("❌ Please provide a return reason")
                    
                    elif req['status'] == 'CONFIRMED_BY_FINANCE':
                        st.info(f"✅ This request was confirmed by Finance on {req['date_confirmed_by_finance']}")
                        
                        col3, col4 = st.columns(2)
                        
                        with col3:
                            payment_ref = st.text_input("Payment Reference Number", key=f"ref_{idx}")
                            if st.button(f"💰 Mark as { 'Cleared' if req['main_category'] == 'Submit Surrender' else 'Paid'}", key=f"paid_{idx}"):
                                if payment_ref:
                                    new_status = 'CLEARED' if req['main_category'] == 'Submit Surrender' else 'PAID'
                                    update_request_status(
                                        req['id'], new_status,
                                        performed_by=st.session_state.username,
                                        performed_by_role=st.session_state.user_role,
                                        performed_by_dept=st.session_state.user_dept
                                    )
                                    update_payment_details(req['id'], payment_ref)
                                    submitted_date = datetime.strptime(req['submission_date'], '%Y-%m-%d').date()
                                    days_taken = working_days_between(submitted_date, date.today())
                                    st.balloons()
                                    st.success(f"✅ Request {req['request_number']} completed! Took {days_taken} working days.")
                                    st.rerun()
                                else:
                                    st.error("❌ Please enter a payment reference number")
                        
                        with col4:
                            comment = st.text_area("Comment", key=f"comment_complete_{idx}")
                    
                    # Show transaction logs
                    st.markdown("---")
                    st.subheader("📜 Transaction Logs")
                    display_transaction_logs(req['id'])
    else:
        st.error("Access denied. Finance only.")


# ================================================================
# REPORTS - DEPARTMENT LEVEL ACCESS ONLY
# ================================================================
elif choice == "📑 Reports":
    st.markdown("<h1 style='color: #00843D;'>📑 Reports</h1>", unsafe_allow_html=True)
    
    df = get_reports_data(st.session_state.user_role, st.session_state.user_dept)
    
    if df.empty:
        if st.session_state.user_role not in ["ADMIN", "MANAGEMENT", "FINANCE"]:
            st.info(f"No requests found for your department: {st.session_state.user_dept}")
        else:
            st.info("No data available")
    else:
        if st.session_state.user_role == "ADMIN":
            st.info("📊 Admin View: Showing all departments' requests")
        elif st.session_state.user_role == "MANAGEMENT":
            st.info("📊 Management View: Showing all departments' requests")
        elif st.session_state.user_role == "FINANCE":
            st.info("📊 Finance View: Showing all departments' requests")
        else:
            st.info(f"📊 Department View: Showing only {st.session_state.user_dept} department requests")
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export to CSV", csv, f"helb_requests_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)
        
        st.markdown("---")
        st.subheader("📊 Summary Statistics")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**By Status:**")
            status_counts = df['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            st.dataframe(status_counts, use_container_width=True, hide_index=True)
        
        with col2:
            st.write("**By Main Category:**")
            category_counts = df['main_category'].value_counts().reset_index()
            category_counts.columns = ['Category', 'Count']
            st.dataframe(category_counts, use_container_width=True, hide_index=True)
        
        if 'financial_year' in df.columns and df['financial_year'].notna().any():
            st.subheader("📅 Financial Year Summary")
            fy_summary = df.groupby('financial_year').agg({
                'amount': 'sum',
                'request_number': 'count'
            }).reset_index()
            fy_summary.columns = ['Financial Year', 'Total Amount', 'Request Count']
            fy_summary['Total Amount'] = fy_summary['Total Amount'].apply(lambda x: f"KES {x:,.2f}")
            st.dataframe(fy_summary, use_container_width=True, hide_index=True)
        
        st.subheader("📋 Detailed Requests")
        display_cols = ['request_number', 'main_category', 'request_type', 'amount', 'status', 'submission_date']
        if 'payment_date' in df.columns:
            display_cols.append('payment_date')
        if 'payment_reference' in df.columns:
            display_cols.append('payment_reference')
        
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)


# ================================================================
# ADMIN PANEL
# ================================================================
elif choice == "⚙️ Admin Panel" and st.session_state.user_role == "ADMIN":
    st.markdown("<h1 style='color: #00843D;'>⚙️ Admin Panel</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Users", "🏢 Departments", "📦 Products", "💰 Funders", "📅 Financial Years"])
    
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
        st.subheader("📦 Product Management")
        products = get_products()
        st.dataframe(products, use_container_width=True)
        with st.form("add_product"):
            name = st.text_input("Product Name")
            category = st.selectbox("Category", ["LOAN", "SCHOLARSHIP"])
            has_payment = st.checkbox("Has Payment Category")
            has_sem = st.checkbox("Has Semester", True)
            if st.form_submit_button("Add"):
                if name:
                    add_product(name, category, has_payment, has_sem)
                    st.rerun()
    
    with tab4:
        st.subheader("💰 Funder Management")
        for f in get_funders():
            st.write(f"• {f}")
        with st.form("add_funder"):
            name = st.text_input("Funder Name")
            if st.form_submit_button("Add"):
                if name:
                    import sqlite3
                    conn = sqlite3.connect("helb_data.db")
                    conn.execute("INSERT INTO funders (name) VALUES (?)", (name,))
                    conn.commit()
                    conn.close()
                    st.rerun()
    
    with tab5:
        st.subheader("📅 Financial Year Management")
        for y in get_financial_years():
            st.write(f"• {y}")
        with st.form("add_year"):
            year = st.text_input("Financial Year (e.g., 2027/2028)")
            if st.form_submit_button("Add"):
                if year:
                    import sqlite3
                    conn = sqlite3.connect("helb_data.db")
                    conn.execute("INSERT INTO financial_years (name, is_active) VALUES (?, 1)", (year,))
                    conn.commit()
                    conn.close()
                    st.rerun()


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
