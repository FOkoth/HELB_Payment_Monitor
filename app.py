import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database import (
    init_database, get_requests, save_request, update_request_status, 
    authenticate_user, get_user_department, get_products, get_funders,
    get_all_users, create_user, create_department, get_departments,
    get_financial_years, get_semesters, add_product
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

# Sidebar
with st.sidebar:
    st.markdown("<h2 style='color: #00843D; text-align: center;'>HELB</h2>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align: center; padding: 0.5rem; background-color: #e8f5e9; border-radius: 10px;'>
            <strong>{st.session_state.full_name}</strong><br>
            <span style='color: #00843D;'>{st.session_state.user_role}</span><br>
            <span style='font-size: 0.8rem;'>{st.session_state.user_dept}</span>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    menu_options = ["📊 Dashboard", "📝 New Request", "📋 My Requests", "✅ Approval Queue", "📑 Reports"]
    if st.session_state.user_role == "ADMIN":
        menu_options.append("⚙️ Admin Panel")
    
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
# FUNCTION TO GET ALLOWED REQUEST TYPES BASED ON DEPARTMENT
# ================================================================
def get_allowed_request_types():
    # Admin can see everything
    if st.session_state.user_role == "ADMIN":
        return ["Student Payment", "Imprest Payment", "Petty Cash Payment", "Supplier Payment", "Salary Payment", "Refund Payment", "Surrender"]
    
    user_dept = st.session_state.user_dept
    
    # Base allowed types for all departments
    allowed = ["Imprest Payment", "Petty Cash Payment", "Surrender"]
    
    # Lending and External Resource Mobilization can see Student Payment
    if user_dept in ["Lending", "External Resource Mobilization"]:
        allowed.append("Student Payment")
    
    # Only Supply Chain Management can see Supplier Payment
    if user_dept == "Supply Chain Management":
        allowed.append("Supplier Payment")
    
    # Only Human Resource can see Salary Payment
    if user_dept == "Human Resource":
        allowed.append("Salary Payment")
    
    # Only Debt Management can see Refund Payment
    if user_dept == "Debt Management":
        allowed.append("Refund Payment")
    
    # Finance department can see everything for approval, but for submission they have limited types
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
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Requests", len(df))
        with col2:
            st.metric("Pending", len(df[df['status'].isin(['SUBMITTED', 'FINANCE_CHECKING'])]))
        with col3:
            st.metric("Completed", len(df[df['status'] == 'COMPLETED']))
        with col4:
            st.metric("Returned", len(df[df['status'] == 'RETURNED']))
        
        col1, col2 = st.columns(2)
        with col1:
            status_counts = df['status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, 
                        color_discrete_sequence=['#00843D', '#FFB81C', '#00529B', '#D3D3D3'])
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            amount_by_type = df.groupby('request_type')['amount'].sum().reset_index()
            fig = px.bar(amount_by_type, x='request_type', y='amount',
                        color_discrete_sequence=['#00843D', '#FFB81C', '#00529B'])
            st.plotly_chart(fig, use_container_width=True)

# ================================================================
# NEW REQUEST - DYNAMIC WITH PROPER CONDITIONAL LOGIC
# ================================================================
elif choice == "📝 New Request":
    st.markdown("<h1 style='color: #00843D;'>📝 Create New Request</h1>", unsafe_allow_html=True)
    
    allowed_types = get_allowed_request_types()
    
    if not allowed_types:
        st.error("Your department has no submission permissions.")
    else:
        # Select Request Type first
        selected_type = st.selectbox("Select Request Type", allowed_types)
        
        st.markdown("---")
        
        # Create the form - ONE form for the entire section
        with st.form(key="request_form"):
            # Common fields for all request types
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Department", value=st.session_state.user_dept, disabled=True)
            with col2:
                st.date_input("Submission Date", value=datetime.today(), disabled=True)
            
            # ============================================================
            # STUDENT PAYMENT - WITH CORRECT CONDITIONAL LOGIC
            # ============================================================
            if selected_type == "Student Payment":
                st.subheader("🎓 Student Payment Details")
                
                batch_no = st.text_input("Batch No.")
                amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                
                financial_years = get_financial_years()
                financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                
                payment_description = st.text_area("Payment Description")
                
                # Product Type selection
                products = get_products()
                if not products.empty:
                    product_type = st.selectbox("Product Type", products['name'].tolist())
                else:
                    product_type = st.selectbox("Product Type", ["Undergraduate", "TVET", "Jielimishe"])
                
                # Conditional fields based on Product Type
                # ONLY show Semester and Payment Category for Undergraduate or TVET
                if product_type == "Undergraduate":
                    semesters = get_semesters()
                    semester = st.selectbox("Semester", semesters if semesters else ["Semester 1", "Semester 2"])
                    payment_category = st.selectbox("Payment Category", ["Tuition", "Upkeep"])
                elif product_type == "TVET":
                    semesters = get_semesters()
                    semester = st.selectbox("Semester", semesters if semesters else ["Semester 1", "Semester 2"])
                    payment_category = st.selectbox("Payment Category", ["Tuition", "Upkeep"])
                else:
                    # Jielimishe: DO NOT show Semester and DO NOT show Payment Category
                    semester = None
                    payment_category = "Tuition"
                
                submitted = st.form_submit_button("Submit Request", use_container_width=True)
                
                if submitted:
                    errors = []
                    if not batch_no:
                        errors.append("Batch No. is required")
                    if amount <= 0:
                        errors.append("Amount must be greater than 0")
                    if not financial_year:
                        errors.append("Financial Year is required")
                    if not payment_description:
                        errors.append("Payment Description is required")
                    
                    # Only validate semester and payment_category for Undergraduate and TVET
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
            # IMPREST PAYMENT
            # ============================================================
            elif selected_type == "Imprest Payment":
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
                    if not financial_year:
                        errors.append("Financial Year is required")
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
            
            # ============================================================
            # PETTY CASH PAYMENT
            # ============================================================
            elif selected_type == "Petty Cash Payment":
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
                    if not financial_year:
                        errors.append("Financial Year is required")
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
            
            # ============================================================
            # SUPPLIER PAYMENT
            # ============================================================
            elif selected_type == "Supplier Payment":
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
                    if not financial_year:
                        errors.append("Financial Year is required")
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
            
            # ============================================================
            # SALARY PAYMENT
            # ============================================================
            elif selected_type == "Salary Payment":
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
                    if not salary_year:
                        errors.append("Year is required")
                    
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
            
            # ============================================================
            # REFUND PAYMENT
            # ============================================================
            elif selected_type == "Refund Payment":
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
                    if not financial_year:
                        errors.append("Financial Year is required")
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
            
            # ============================================================
            # SURRENDER
            # ============================================================
            elif selected_type == "Surrender":
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
                    if not financial_year:
                        errors.append("Financial Year is required")
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
            st.dataframe(user_requests[['request_number', 'request_type', 'amount', 'status', 'submission_date']], 
                        use_container_width=True, hide_index=True)

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
                with st.expander(f"{req['request_number']} - {req['request_type']} - {req['department_name']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Department:** {req['department_name']}")
                        st.write(f"**Submitted By:** {req['submitted_by']}")
                        st.write(f"**Date:** {req['submission_date']}")
                        st.write(f"**Amount:** KES {req['amount']:,.2f}")
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
                    
                    col3, col4, col5 = st.columns(3)
                    with col3:
                        if req['status'] == 'SUBMITTED':
                            if st.button(f"Start", key=f"start_{idx}"):
                                update_request_status(req['id'], 'FINANCE_CHECKING')
                                st.rerun()
                        elif req['status'] == 'FINANCE_CHECKING':
                            if st.button(f"Approve", key=f"approve_{idx}"):
                                update_request_status(req['id'], 'APPROVED_FOR_PROCESSING')
                                st.rerun()
                        elif req['status'] == 'APPROVED_FOR_PROCESSING':
                            if st.button(f"Complete", key=f"complete_{idx}"):
                                update_request_status(req['id'], 'COMPLETED')
                                st.balloons()
                                st.rerun()
                    with col4:
                        comment = st.text_area("Comment", key=f"comment_{idx}")
                    with col5:
                        reason = st.text_input("Return Reason", key=f"return_{idx}")
                        if st.button(f"Return", key=f"return_btn_{idx}"):
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

# ================================================================
# ADMIN PANEL
# ================================================================
elif choice == "⚙️ Admin Panel" and st.session_state.user_role == "ADMIN":
    st.markdown("<h1 style='color: #00843D;'>⚙️ Admin Panel</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Products", "Funders", "Financial Years", "Semesters"])
    
    with tab1:
        st.subheader("Products")
        products = get_products()
        st.dataframe(products)
        with st.form("add_product"):
            name = st.text_input("Product Name")
            category = st.selectbox("Category", ["LOAN", "SCHOLARSHIP"])
            has_payment = st.checkbox("Has Payment Category")
            has_sem = st.checkbox("Has Semester", True)
            if st.form_submit_button("Add"):
                add_product(name, category, has_payment, has_sem)
                st.rerun()
    
    with tab2:
        st.subheader("Funders")
        for f in get_funders():
            st.write(f"• {f}")
        with st.form("add_funder"):
            name = st.text_input("Funder Name")
            if st.form_submit_button("Add"):
                import sqlite3
                conn = sqlite3.connect("helb_data.db")
                conn.execute("INSERT INTO funders (name) VALUES (?)", (name,))
                conn.commit()
                conn.close()
                st.rerun()
    
    with tab3:
        st.subheader("Financial Years")
        for y in get_financial_years():
            st.write(f"• {y}")
        with st.form("add_year"):
            year = st.text_input("Financial Year (e.g., 2027/2028)")
            if st.form_submit_button("Add"):
                import sqlite3
                conn = sqlite3.connect("helb_data.db")
                conn.execute("INSERT INTO financial_years (name, is_active) VALUES (?, 1)", (year,))
                conn.commit()
                conn.close()
                st.rerun()
    
    with tab4:
        st.subheader("Semesters")
        for s in get_semesters():
            st.write(f"• {s}")
        with st.form("add_semester"):
            sem = st.text_input("Semester Name")
            if st.form_submit_button("Add"):
                import sqlite3
                conn = sqlite3.connect("helb_data.db")
                conn.execute("INSERT INTO semesters (name) VALUES (?)", (sem,))
                conn.commit()
                conn.close()
                st.rerun()
