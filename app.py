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
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #00529B;
        color: white;
    }
    
    .success-box {
        background-color: #00843D10;
        border-left: 4px solid #00843D;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
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

def get_allowed_request_types():
    if st.session_state.user_role == "ADMIN":
        return ["Student Payment", "Imprest Payment", "Petty Cash Payment", "Supplier Payment", "Salary Payment", "Refund Payment", "Surrender"]
    result = get_user_department(st.session_state.username)
    if result:
        allowed = []
        if result[5]: allowed.append("Student Payment")
        if result[2]: allowed.append("Imprest Payment")
        if result[3]: allowed.append("Petty Cash Payment")
        if result[4]: allowed.append("Supplier Payment")
        if result[7]: allowed.append("Refund Payment")
        if result[6]: allowed.append("Surrender")
        # Salary Payment - add if department has permission
        if result[2] or result[3]: allowed.append("Salary Payment")
        return allowed
    return ["Imprest Payment", "Petty Cash Payment", "Surrender"]

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
# NEW REQUEST
# ================================================================
elif choice == "📝 New Request":
    st.markdown("<h1 style='color: #00843D;'>📝 Create New Request</h1>", unsafe_allow_html=True)
    
    allowed_types = get_allowed_request_types()
    
    if not allowed_types:
        st.error("Your department has no submission permissions.")
    else:
        with st.form("request_form"):
            request_type = st.selectbox("Request Type", allowed_types)
            
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Department", value=st.session_state.user_dept, disabled=True)
            with col2:
                st.date_input("Submission Date", value=datetime.today(), disabled=True)
            
            st.markdown("---")
            
            # ======================================================
            # STUDENT PAYMENT
            # ======================================================
            if request_type == "Student Payment":
                st.subheader("🎓 Student Payment Details")
                
                batch_no = st.text_input("Batch No.")
                amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                
                financial_years = get_financial_years()
                financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                
                payment_description = st.text_area("Payment Description")
                
                # Product Type
                products = get_products()
                if not products.empty:
                    product_type = st.selectbox("Product Type", products['name'].tolist())
                else:
                    product_type = st.selectbox("Product Type", ["Undergraduate", "TVET", "Jielimishe"])
                
                # Conditional fields based on Product Type
                if product_type == "Undergraduate":
                    semesters = get_semesters()
                    semester = st.selectbox("Semester", semesters if semesters else ["Semester 1", "Semester 2"])
                    payment_category = st.selectbox("Payment Category", ["Tuition", "Upkeep"])
                elif product_type == "TVET":
                    semesters = get_semesters()
                    semester = st.selectbox("Semester", semesters if semesters else ["Semester 1", "Semester 2"])
                    payment_category = st.selectbox("Payment Category", ["Tuition", "Upkeep"])
                else:  # Jielimishe
                    semester = None
                    payment_category = "Tuition"
                
                # Initialize other variables
                imprest_no = None
                petty_cash_no = None
                supplier_name = None
                invoice_no = None
                lpo_no = None
                salary_month = None
                salary_year = None
                refund_no = None
                customer_name = None
                customer_id = None
                surrender_no = None
                staff_name = None
                previous_imprest_no = None
                refund_reason = None
                original_payment_ref = None
            
            # ======================================================
            # IMPREST PAYMENT
            # ======================================================
            elif request_type == "Imprest Payment":
                st.subheader("💰 Imprest Payment Details")
                
                imprest_no = st.text_input("Imprest No.")
                amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                
                financial_years = get_financial_years()
                financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                
                payment_description = st.text_area("Payment Detail")
                
                # Initialize other variables
                batch_no = None
                product_type = None
                semester = None
                payment_category = None
                petty_cash_no = None
                supplier_name = None
                invoice_no = None
                lpo_no = None
                salary_month = None
                salary_year = None
                refund_no = None
                customer_name = None
                customer_id = None
                surrender_no = None
                staff_name = None
                previous_imprest_no = None
                refund_reason = None
                original_payment_ref = None
            
            # ======================================================
            # PETTY CASH PAYMENT
            # ======================================================
            elif request_type == "Petty Cash Payment":
                st.subheader("💵 Petty Cash Payment Details")
                
                petty_cash_no = st.text_input("Petty Cash No.")
                amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                
                financial_years = get_financial_years()
                financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                
                payment_description = st.text_area("Payment Detail")
                
                # Initialize other variables
                imprest_no = None
                batch_no = None
                product_type = None
                semester = None
                payment_category = None
                supplier_name = None
                invoice_no = None
                lpo_no = None
                salary_month = None
                salary_year = None
                refund_no = None
                customer_name = None
                customer_id = None
                surrender_no = None
                staff_name = None
                previous_imprest_no = None
                refund_reason = None
                original_payment_ref = None
            
            # ======================================================
            # SUPPLIER PAYMENT
            # ======================================================
            elif request_type == "Supplier Payment":
                st.subheader("🏢 Supplier Payment Details")
                
                invoice_no = st.text_input("Invoice No.")
                amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                
                financial_years = get_financial_years()
                financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                
                supplier_name = st.text_input("Vendor Name")
                payment_description = st.text_area("Payment Detail")
                
                # Initialize other variables
                imprest_no = None
                petty_cash_no = None
                batch_no = None
                product_type = None
                semester = None
                payment_category = None
                lpo_no = None
                salary_month = None
                salary_year = None
                refund_no = None
                customer_name = None
                customer_id = None
                surrender_no = None
                staff_name = None
                previous_imprest_no = None
                refund_reason = None
                original_payment_ref = None
            
            # ======================================================
            # SALARY PAYMENT
            # ======================================================
            elif request_type == "Salary Payment":
                st.subheader("👔 Salary Payment Details")
                
                months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                salary_month = st.selectbox("Salary Month", months)
                
                amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                
                financial_years = get_financial_years()
                financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                
                current_year = datetime.now().year
                salary_year = st.number_input("Year", min_value=2020, max_value=2030, value=current_year)
                
                # Initialize other variables
                imprest_no = None
                petty_cash_no = None
                batch_no = None
                product_type = None
                semester = None
                payment_category = None
                supplier_name = None
                invoice_no = None
                lpo_no = None
                refund_no = None
                customer_name = None
                customer_id = None
                surrender_no = None
                staff_name = None
                previous_imprest_no = None
                refund_reason = None
                original_payment_ref = None
                payment_description = None
            
            # ======================================================
            # REFUND PAYMENT
            # ======================================================
            elif request_type == "Refund Payment":
                st.subheader("🔄 Refund Payment Details")
                
                refund_no = st.text_input("Refund No.")
                amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                
                financial_years = get_financial_years()
                financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                
                customer_name = st.text_input("Customer Name")
                customer_id = st.text_input("Customer ID Number")
                
                # Initialize other variables
                imprest_no = None
                petty_cash_no = None
                batch_no = None
                product_type = None
                semester = None
                payment_category = None
                supplier_name = None
                invoice_no = None
                lpo_no = None
                salary_month = None
                salary_year = None
                surrender_no = None
                staff_name = None
                previous_imprest_no = None
                refund_reason = None
                original_payment_ref = None
                payment_description = None
            
            # ======================================================
            # SURRENDER
            # ======================================================
            elif request_type == "Surrender":
                st.subheader("📤 Surrender Details")
                
                surrender_no = st.text_input("Surrender No.")
                amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                
                financial_years = get_financial_years()
                financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                
                staff_name = st.text_input("Staff Name")
                
                # Initialize other variables
                imprest_no = None
                petty_cash_no = None
                batch_no = None
                product_type = None
                semester = None
                payment_category = None
                supplier_name = None
                invoice_no = None
                lpo_no = None
                salary_month = None
                salary_year = None
                refund_no = None
                customer_name = None
                customer_id = None
                previous_imprest_no = None
                refund_reason = None
                original_payment_ref = None
                payment_description = None
            
            st.markdown("---")
            submitted = st.form_submit_button("Submit Request", use_container_width=True)
            
            if submitted:
                errors = []
                
                # Validation based on request type
                if request_type == "Student Payment":
                    if not batch_no:
                        errors.append("Batch No. is required")
                    if amount <= 0:
                        errors.append("Amount must be greater than 0")
                    if not financial_year:
                        errors.append("Financial Year is required")
                    if not payment_description:
                        errors.append("Payment Description is required")
                    if not product_type:
                        errors.append("Product Type is required")
                    if product_type in ["Undergraduate", "TVET"]:
                        if not semester:
                            errors.append("Semester is required")
                        if not payment_category:
                            errors.append("Payment Category is required")
                
                elif request_type == "Imprest Payment":
                    if not imprest_no:
                        errors.append("Imprest No. is required")
                    if amount <= 0:
                        errors.append("Amount must be greater than 0")
                    if not financial_year:
                        errors.append("Financial Year is required")
                    if not payment_description:
                        errors.append("Payment Detail is required")
                
                elif request_type == "Petty Cash Payment":
                    if not petty_cash_no:
                        errors.append("Petty Cash No. is required")
                    if amount <= 0:
                        errors.append("Amount must be greater than 0")
                    if not financial_year:
                        errors.append("Financial Year is required")
                    if not payment_description:
                        errors.append("Payment Detail is required")
                
                elif request_type == "Supplier Payment":
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
                
                elif request_type == "Salary Payment":
                    if not salary_month:
                        errors.append("Salary Month is required")
                    if amount <= 0:
                        errors.append("Amount must be greater than 0")
                    if not financial_year:
                        errors.append("Financial Year is required")
                    if not salary_year:
                        errors.append("Year is required")
                
                elif request_type == "Refund Payment":
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
                
                elif request_type == "Surrender":
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
                        'request_type': request_type,
                        'department_id': st.session_state.user_dept_id,
                        'department_name': st.session_state.user_dept,
                        'submitted_by': st.session_state.username,
                        'amount': amount if 'amount' in dir() else 0,
                        'payment_description': payment_description if 'payment_description' in dir() else None,
                        'financial_year': financial_year if 'financial_year' in dir() else None,
                        # Student Payment fields
                        'batch_no': batch_no if request_type == "Student Payment" else None,
                        'product_type': product_type if request_type == "Student Payment" else None,
                        'semester': semester if request_type == "Student Payment" and product_type in ["Undergraduate", "TVET"] else None,
                        'payment_type': payment_category if request_type == "Student Payment" and product_type in ["Undergraduate", "TVET"] else None,
                        # Imprest
                        'imprest_no': imprest_no if request_type == "Imprest Payment" else None,
                        # Petty Cash
                        'petty_cash_no': petty_cash_no if request_type == "Petty Cash Payment" else None,
                        # Supplier fields
                        'supplier_name': supplier_name if request_type == "Supplier Payment" else None,
                        'invoice_no': invoice_no if request_type == "Supplier Payment" else None,
                        # Salary fields
                        'salary_month': salary_month if request_type == "Salary Payment" else None,
                        'salary_year': salary_year if request_type == "Salary Payment" else None,
                        # Refund fields
                        'refund_no': refund_no if request_type == "Refund Payment" else None,
                        'customer_name': customer_name if request_type == "Refund Payment" else None,
                        'customer_id': customer_id if request_type == "Refund Payment" else None,
                        # Surrender fields
                        'surrender_number': surrender_no if request_type == "Surrender" else None,
                        'staff_name': staff_name if request_type == "Surrender" else None,
                        'status': 'SUBMITTED'
                    }
                    
                    # Clean up None values
                    request_data = {k: v for k, v in request_data.items() if v is not None}
                    
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
            display_cols = ['request_number', 'request_type', 'amount', 'status', 'submission_date']
            if 'payment_description' in user_requests.columns:
                display_cols.append('payment_description')
            st.dataframe(user_requests[display_cols], use_container_width=True, hide_index=True)

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
                            if req['product_type']:
                                st.write(f"**Product:** {req['product_type']}")
                            if req['semester']:
                                st.write(f"**Semester:** {req['semester']}")
                            if req['payment_type']:
                                st.write(f"**Category:** {req['payment_type']}")
                            st.write(f"**Batch No:** {req['batch_no']}")
                        elif req['request_type'] == "Imprest Payment":
                            st.write(f"**Imprest No:** {req['imprest_no']}")
                        elif req['request_type'] == "Petty Cash Payment":
                            st.write(f"**Petty Cash No:** {req['petty_cash_no'] or req['imprest_no']}")
                        elif req['request_type'] == "Supplier Payment":
                            st.write(f"**Supplier:** {req['supplier_name']}")
                            st.write(f"**Invoice No:** {req['invoice_no']}")
                        elif req['request_type'] == "Salary Payment":
                            st.write(f"**Month:** {req['salary_month']}")
                            st.write(f"**Year:** {req['salary_year']}")
                        elif req['request_type'] == "Refund Payment":
                            st.write(f"**Refund No:** {req['refund_no'] or req['imprest_no']}")
                            st.write(f"**Customer:** {req['customer_name']}")
                        elif req['request_type'] == "Surrender":
                            st.write(f"**Surrender No:** {req['surrender_number']}")
                            st.write(f"**Staff:** {req['staff_name']}")
                    
                    if req['payment_description']:
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
