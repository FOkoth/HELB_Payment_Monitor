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
    update_request_payment_details
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

# Custom CSS for HELB colors
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
    
    .status-completed {
        background-color: #00843D20;
        color: #00843D;
        padding: 0.25rem 0.5rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    
    .status-pending {
        background-color: #DC354520;
        color: #DC3545;
        padding: 0.25rem 0.5rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    
    .status-approved {
        background-color: #FFB81C20;
        color: #FFB81C;
        padding: 0.25rem 0.5rem;
        border-radius: 20px;
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
    
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .user-info {
        text-align: center;
        padding: 0.5rem;
        background-color: #e8f5e9;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
init_database()

# Session state for login
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

# Password Change Modal (shown after login if needed)
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
                    # Verify current password
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
    
    # Display user info with full name and department
    st.markdown(f"""
        <div class='user-info'>
            <strong>{st.session_state.full_name}</strong><br>
            <span style='color: #00843D;'>{st.session_state.user_role}</span><br>
            <span style='font-size: 0.8rem;'>{st.session_state.user_dept}</span>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    menu_options = ["📊 Dashboard", "📝 New Request", "📋 My Requests", "✅ Approval Queue", "📑 Reports"]
    if st.session_state.user_role == "ADMIN":
        menu_options.append("⚙️ Admin Panel")
    menu_options.append("🔐 Change Password")
    
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

# Change Password option in menu
if choice == "🔐 Change Password":
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
    st.stop()

# ================================================================
# FUNCTION TO GET ALLOWED REQUEST TYPES
# ================================================================
def get_allowed_request_types():
    if st.session_state.user_role == "ADMIN":
        return ["Student Payment", "Imprest Payment", "Petty Cash Payment", "Supplier Payment", "Salary Payment", "Refund Payment", "Surrender"]
    
    user_dept = st.session_state.user_dept
    allowed = ["Imprest Payment", "Petty Cash Payment", "Surrender"]
    
    if user_dept in ["Lending", "External Resource Mobilization"]:
        allowed.append("Student Payment")
    if user_dept == "Supply Chain Management":
        allowed.append("Supplier Payment")
    if user_dept == "Human Resource":
        allowed.append("Salary Payment")
    if user_dept == "Debt Management":
        allowed.append("Refund Payment")
    
    if st.session_state.user_role == "FINANCE":
        return ["Imprest Payment", "Petty Cash Payment"]
    
    return allowed

# ================================================================
# DASHBOARD
# ================================================================
if choice == "📊 Dashboard":
    st.markdown("<h1 style='color: #00843D;'>📊 Performance Dashboard</h1>", unsafe_allow_html=True)
    df = get_requests()
    
    if df.empty:
        st.info("No requests found.")
    else:
        # Convert submission_date to datetime
        df['submission_date_dt'] = pd.to_datetime(df['submission_date'])
        
        # Calculate pending duration for non-completed requests
        pending_requests = df[df['status'] != 'COMPLETED']
        pending_durations = []
        for _, row in pending_requests.iterrows():
            days = get_pending_duration(row['submission_date'])
            pending_durations.append(days)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total = len(df)
            st.markdown(f"""
                <div class="metric-card">
                    <h2 style="color: #00843D; margin:0;">{total}</h2>
                    <p>Total Requests</p>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            pending_count = len(df[df['status'].isin(['SUBMITTED', 'FINANCE_CHECKING', 'APPROVED_FOR_PROCESSING'])])
            st.markdown(f"""
                <div class="metric-card">
                    <h2 style="color: #DC3545; margin:0;">{pending_count}</h2>
                    <p>Pending</p>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            completed_count = len(df[df['status'] == 'COMPLETED'])
            st.markdown(f"""
                <div class="metric-card">
                    <h2 style="color: #00843D; margin:0;">{completed_count}</h2>
                    <p>Completed</p>
                </div>
            """, unsafe_allow_html=True)
        with col4:
            avg_completion = 0
            completed_df = df[df['status'] == 'COMPLETED']
            if not completed_df.empty and 'completion_date' in completed_df.columns:
                completion_times = []
                for _, row in completed_df.iterrows():
                    if row.get('completion_date'):
                        sub = datetime.strptime(row['submission_date'], '%Y-%m-%d').date()
                        comp = datetime.strptime(row['completion_date'], '%Y-%m-%d').date()
                        completion_times.append(working_days_between(sub, comp))
                avg_completion = sum(completion_times) / len(completion_times) if completion_times else 0
            st.markdown(f"""
                <div class="metric-card">
                    <h2 style="color: #00843D; margin:0;">{avg_completion:.1f}</h2>
                    <p>Avg Days to Complete</p>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 Requests by Status")
            status_counts = df['status'].value_counts()
            color_map = {
                'COMPLETED': '#00843D',
                'SUBMITTED': '#DC3545',
                'FINANCE_CHECKING': '#FFB81C',
                'APPROVED_FOR_PROCESSING': '#00529B',
                'RETURNED': '#6C757D'
            }
            colors = [color_map.get(s, '#D3D3D3') for s in status_counts.index]
            fig = px.pie(values=status_counts.values, names=status_counts.index, color_discrete_sequence=colors)
            fig.update_layout(showlegend=True, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("💰 Amount by Request Type")
            amount_by_type = df.groupby('request_type')['amount'].sum().reset_index()
            fig = px.bar(amount_by_type, x='request_type', y='amount',
                        color_discrete_sequence=['#00843D', '#FFB81C', '#00529B'])
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent requests table with status badges
        st.subheader("📋 Recent Requests")
        display_df = df.head(10).copy()
        
        def get_status_badge(status):
            if status == 'COMPLETED':
                return '<span class="status-completed">✓ Paid</span>'
            elif status in ['SUBMITTED', 'FINANCE_CHECKING', 'APPROVED_FOR_PROCESSING']:
                days = 0
                return '<span class="status-pending">⏳ Pending</span>'
            else:
                return f'<span class="status-approved">↺ {status}</span>'
        
        display_df['Status'] = display_df['status'].apply(get_status_badge)
        st.markdown(display_df[['request_number', 'request_type', 'amount', 'Status', 'submission_date']].to_html(escape=False, index=False), unsafe_allow_html=True)

# ================================================================
# NEW REQUEST
# ================================================================
elif choice == "📝 New Request":
    st.markdown("<h1 style='color: #00843D;'>📝 Create New Request</h1>", unsafe_allow_html=True)
    
    allowed_types = get_allowed_request_types()
    
    if not allowed_types:
        st.error("Your department has no submission permissions.")
    else:
        selected_type = st.selectbox("Select Request Type", allowed_types)
        st.markdown("---")
        
        if selected_type == "Student Payment":
            st.subheader("🎓 Student Payment Details")
            
            products = get_products()
            if not products.empty:
                product_type = st.selectbox("Product Type", products['name'].tolist(), key="product_type_select")
            else:
                product_type = st.selectbox("Product Type", ["Undergraduate", "TVET", "Jielimishe"], key="product_type_select")
            
            semester = None
            payment_category = None
            
            if product_type == "Undergraduate":
                st.markdown("---")
                semesters = get_semesters()
                semester = st.selectbox("Semester", semesters if semesters else ["Semester 1", "Semester 2"])
                payment_category = st.selectbox("Payment Category", ["Tuition", "Upkeep"])
            elif product_type == "TVET":
                st.markdown("---")
                semesters = get_semesters()
                semester = st.selectbox("Semester", semesters if semesters else ["Semester 1", "Semester 2"])
                payment_category = st.selectbox("Payment Category", ["Tuition", "Upkeep"])
            else:
                semester = None
                payment_category = "Tuition"
            
            st.markdown("---")
            
            with st.form(key="student_payment_form"):
                batch_no = st.text_input("Batch No.")
                amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                financial_years = get_financial_years()
                financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                payment_description = st.text_area("Payment Description")
                
                submitted = st.form_submit_button("Submit Request", use_container_width=True)
                
                if submitted:
                    errors = []
                    if not batch_no:
                        errors.append("Batch No. is required")
                    if amount <= 0:
                        errors.append("Amount must be greater than 0")
                    if not payment_description:
                        errors.append("Payment Description is required")
                    if product_type in ["Undergraduate", "TVET"]:
                        if not semester:
                            errors.append("Semester is required")
                    
                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
                        request_data = {
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
        
        elif selected_type == "Imprest Payment":
            with st.form(key="imprest_form"):
                st.subheader("💰 Imprest Payment Details")
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
        
        elif selected_type == "Petty Cash Payment":
            with st.form(key="petty_cash_form"):
                st.subheader("💵 Petty Cash Payment Details")
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
        
        elif selected_type == "Supplier Payment":
            with st.form(key="supplier_form"):
                st.subheader("🏢 Supplier Payment Details")
                invoice_no = st.text_input("Invoice No.")
                amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                financial_years = get_financial_years()
                financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                supplier_name = st.text_input("Vendor Name")
                payment_description = st.text_area("Payment Detail")
                submitted = st.form_submit_button("Submit Request", use_container_width=True)
                
                if submitted:
                    errors = []
                    if not invoice_no:
                        errors.append("Invoice No. is required")
                    if amount <= 0:
                        errors.append("Amount must be greater than 0")
                    if not supplier_name:
                        errors.append("Vendor Name is required")
                    if not payment_description:
                        errors.append("Payment Detail is required")
                    
                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
                        request_data = {
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
        
        elif selected_type == "Salary Payment":
            with st.form(key="salary_form"):
                st.subheader("👔 Salary Payment Details")
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
                            'request_type': selected_type,
                            'department_id': st.session_state.user_dept_id,
                            'department_name': st.session_state.user_dept,
                            'submitted_by': st.session_state.username,
                            'amount': amount,
                            'financial_year': financial_year,
                            'salary_month': salary_month,
                            'salary_year': salary_year,
                            'status': 'SUBMITTED'
                        }
                        request_number = save_request(request_data)
                        st.success(f"✅ Request {request_number} submitted successfully!")
                        st.balloons()
        
        elif selected_type == "Refund Payment":
            with st.form(key="refund_form"):
                st.subheader("🔄 Refund Payment Details")
                refund_no = st.text_input("Refund No.")
                amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                financial_years = get_financial_years()
                financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                customer_name = st.text_input("Customer Name")
                customer_id = st.text_input("Customer ID Number")
                submitted = st.form_submit_button("Submit Request", use_container_width=True)
                
                if submitted:
                    errors = []
                    if not refund_no:
                        errors.append("Refund No. is required")
                    if amount <= 0:
                        errors.append("Amount must be greater than 0")
                    if not customer_name:
                        errors.append("Customer Name is required")
                    if not customer_id:
                        errors.append("Customer ID Number is required")
                    
                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
                        request_data = {
                            'request_type': selected_type,
                            'department_id': st.session_state.user_dept_id,
                            'department_name': st.session_state.user_dept,
                            'submitted_by': st.session_state.username,
                            'amount': amount,
                            'financial_year': financial_year,
                            'imprest_no': refund_no,
                            'customer_name': customer_name,
                            'customer_id': customer_id,
                            'status': 'SUBMITTED'
                        }
                        request_number = save_request(request_data)
                        st.success(f"✅ Request {request_number} submitted successfully!")
                        st.balloons()
        
        elif selected_type == "Surrender":
            with st.form(key="surrender_form"):
                st.subheader("📤 Surrender Details")
                surrender_no = st.text_input("Surrender No.")
                amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                financial_years = get_financial_years()
                financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                staff_name = st.text_input("Staff Name")
                submitted = st.form_submit_button("Submit Request", use_container_width=True)
                
                if submitted:
                    errors = []
                    if not surrender_no:
                        errors.append("Surrender No. is required")
                    if amount <= 0:
                        errors.append("Amount must be greater than 0")
                    if not staff_name:
                        errors.append("Staff Name is required")
                    
                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
                        request_data = {
                            'request_type': selected_type,
                            'department_id': st.session_state.user_dept_id,
                            'department_name': st.session_state.user_dept,
                            'submitted_by': st.session_state.username,
                            'amount': amount,
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
            # Add status display and pending duration
            display_data = []
            for _, row in user_requests.iterrows():
                status_display = ""
                if row['status'] == 'COMPLETED':
                    if row['request_type'] == 'Surrender':
                        status_display = "✅ Cleared"
                    else:
                        status_display = "✅ Paid"
                elif row['status'] in ['SUBMITTED', 'FINANCE_CHECKING', 'APPROVED_FOR_PROCESSING']:
                    days = get_pending_duration(row['submission_date'])
                    status_display = f"⏳ Pending ({days} days)"
                else:
                    status_display = f"↺ {row['status']}"
                
                display_data.append({
                    'Request #': row['request_number'],
                    'Type': row['request_type'],
                    'Amount': f"KES {row['amount']:,.2f}",
                    'Status': status_display,
                    'Submitted': row['submission_date']
                })
            
            st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)

# ================================================================
# APPROVAL QUEUE
# ================================================================
elif choice == "✅ Approval Queue":
    if st.session_state.user_role in ["FINANCE", "ADMIN"] or st.session_state.is_finance:
        st.markdown("<h1 style='color: #00843D;'>✅ Approval Queue</h1>", unsafe_allow_html=True)
        df = get_requests()
        pending = df[df['status'].isin(['SUBMITTED', 'FINANCE_CHECKING', 'APPROVED_FOR_PROCESSING'])]
        
        if pending.empty:
            st.info("No pending requests.")
        else:
            for idx, (_, req) in enumerate(pending.iterrows()):
                days_pending = get_pending_duration(req['submission_date'])
                with st.expander(f"📄 {req['request_number']} - {req['request_type']} - {req['department_name']} - Pending for {days_pending} days"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Department:** {req['department_name']}")
                        st.write(f"**Submitted By:** {req['submitted_by']}")
                        st.write(f"**Date:** {req['submission_date']}")
                        st.write(f"**Amount:** KES {req['amount']:,.2f}")
                        st.write(f"**Pending Duration:** {days_pending} working days")
                    with col2:
                        st.write(f"**Type:** {req['request_type']}")
                        if req['request_type'] == "Student Payment":
                            if req.get('product_type'):
                                st.write(f"**Product:** {req['product_type']}")
                            if req.get('semester'):
                                st.write(f"**Semester:** {req['semester']}")
                            if req.get('payment_type'):
                                st.write(f"**Category:** {req['payment_type']}")
                            st.write(f"**Batch No:** {req.get('batch_no', 'N/A')}")
                        elif req['request_type'] == "Imprest Payment":
                            st.write(f"**Imprest No:** {req.get('imprest_no', 'N/A')}")
                        elif req['request_type'] == "Petty Cash Payment":
                            st.write(f"**Petty Cash No:** {req.get('imprest_no', 'N/A')}")
                        elif req['request_type'] == "Supplier Payment":
                            st.write(f"**Supplier:** {req.get('supplier_name', 'N/A')}")
                            st.write(f"**Invoice No:** {req.get('invoice_no', 'N/A')}")
                        elif req['request_type'] == "Salary Payment":
                            st.write(f"**Month:** {req.get('salary_month', 'N/A')}")
                            st.write(f"**Year:** {req.get('salary_year', 'N/A')}")
                        elif req['request_type'] == "Refund Payment":
                            st.write(f"**Refund No:** {req.get('imprest_no', 'N/A')}")
                            st.write(f"**Customer:** {req.get('customer_name', 'N/A')}")
                        elif req['request_type'] == "Surrender":
                            st.write(f"**Surrender No:** {req.get('surrender_number', 'N/A')}")
                            st.write(f"**Staff:** {req.get('staff_name', 'N/A')}")
                    
                    if req.get('payment_description'):
                        st.write(f"**Description:** {req['payment_description']}")
                    
                    st.markdown("---")
                    
                    col3, col4, col5 = st.columns(3)
                    with col3:
                        if req['status'] == 'SUBMITTED':
                            if st.button(f"📋 Start Checking", key=f"start_{idx}"):
                                update_request_status(req['id'], 'FINANCE_CHECKING')
                                st.rerun()
                        elif req['status'] == 'FINANCE_CHECKING':
                            if st.button(f"✅ Approve", key=f"approve_{idx}"):
                                update_request_status(req['id'], 'APPROVED_FOR_PROCESSING')
                                st.rerun()
                        elif req['status'] == 'APPROVED_FOR_PROCESSING':
                            # For completion, ask for payment reference
                            payment_ref = st.text_input("Payment Reference Number", key=f"ref_{idx}")
                            if st.button(f"🎉 Mark Complete", key=f"complete_{idx}"):
                                if payment_ref:
                                    completion_date = date.today().isoformat()
                                    update_request_status(req['id'], 'COMPLETED')
                                    update_request_payment_details(req['id'], payment_ref, completion_date)
                                    
                                    # Calculate completion time
                                    submitted_date = datetime.strptime(req['submission_date'], '%Y-%m-%d').date()
                                    days_taken = working_days_between(submitted_date, date.today())
                                    
                                    st.balloons()
                                    st.success(f"✅ Request {req['request_number']} completed! Took {days_taken} working days.")
                                    st.rerun()
                                else:
                                    st.error("❌ Please enter a payment reference number")
                    
                    with col4:
                        comment = st.text_area("Comment", key=f"comment_{idx}")
                    
                    with col5:
                        reason = st.text_input("Return Reason", key=f"return_{idx}")
                        if st.button(f"↩️ Return", key=f"return_btn_{idx}"):
                            if reason:
                                update_request_status(req['id'], 'RETURNED', comment, reason)
                                st.rerun()
    else:
        st.error("Access denied. Finance only.")

# ================================================================
# REPORTS
# ================================================================
elif choice == "📑 Reports":
    st.markdown("<h1 style='color: #00843D;'>📑 Reports</h1>", unsafe_allow_html=True)
    df = get_requests()
    if df.empty:
        st.info("No data")
    else:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Export CSV", csv, "helb_requests.csv", "text/csv", use_container_width=True)
        
        st.subheader("📊 Summary Statistics")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**By Status:**")
            st.dataframe(df['status'].value_counts().reset_index())
        with col2:
            st.write("**By Department:**")
            st.dataframe(df['department_name'].value_counts().reset_index())

# ================================================================
# ADMIN PANEL
# ================================================================
elif choice == "⚙️ Admin Panel" and st.session_state.user_role == "ADMIN":
    st.markdown("<h1 style='color: #00843D;'>⚙️ Admin Panel</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Users", "🏢 Departments", "📦 Products", "💰 Funders", "📅 Financial Years"])
    
    with tab1:
        st.subheader("👥 User Management")
        
        # Display existing users
        users_df = get_all_users()
        st.dataframe(users_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("➕ Add New User")
        with st.form("add_user_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password (default)", type="password", value="password123")
            new_full_name = st.text_input("Full Name (e.g., Alice Kagucia)")
            new_role = st.selectbox("Role", ["DEPARTMENT", "FINANCE", "ADMIN"])
            
            depts = get_departments()
            dept_options = {row['name']: row['id'] for _, row in depts.iterrows()}
            new_department = st.selectbox("Department", ["None"] + list(dept_options.keys()))
            
            if st.form_submit_button("Create User"):
                if new_username and new_password and new_full_name:
                    dept_id = dept_options.get(new_department) if new_department != "None" else None
                    success = create_user(new_username, new_password, new_role, dept_id, new_full_name)
                    if success:
                        st.success(f"✅ User {new_username} ({new_full_name}) created successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Username already exists!")
                else:
                    st.error("❌ Username, password, and full name are required")
    
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
            
            col3, col4 = st.columns(2)
            with col3:
                requires_product = st.checkbox("Requires Product Type", False)
            with col4:
                requires_funder = st.checkbox("Requires Funder", False)
            
            is_finance = st.checkbox("Finance Department (can approve all)", False)
            
            if st.form_submit_button("Create Department"):
                if dept_name:
                    perms = [can_imprest, can_petty, can_supplier, can_student, can_surrender, can_refund, requires_product, requires_funder, is_finance]
                    success = create_department(dept_name, perms)
                    if success:
                        st.success(f"✅ Department {dept_name} created!")
                        st.rerun()
                    else:
                        st.error("❌ Department name already exists!")
    
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
