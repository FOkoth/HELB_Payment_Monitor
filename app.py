import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
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
        transform: translateY(-1px);
    }
    
    .success-box {
        background-color: #00843D10;
        border-left: 4px solid #00843D;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background-color: #FFB81C10;
        border-left: 4px solid #FFB81C;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .info-box {
        background-color: #00529B10;
        border-left: 4px solid #00529B;
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
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    h1, h2, h3 {
        color: #00843D;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
    }
    
    div[data-testid="stExpander"] details summary p {
        font-weight: 600;
        color: #00843D;
    }
    
    .stAlert {
        border-radius: 5px;
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
    
    hr {
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
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
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
                    st.error("❌ Invalid credentials. Please try again.")
        
        st.markdown("---")
        st.markdown("<p style='text-align: center; font-size: 0.8rem; color: gray;'>© 2026 Higher Education Loans Board. All rights reserved.</p>", unsafe_allow_html=True)
    st.stop()

# Main App
# Sidebar with nice navigation menu
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <h2 style='color: #00843D; margin: 0;'>HELB</h2>
            <p style='color: #FFB81C; margin: 0;'>Monitoring System</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style='text-align: center; padding: 0.5rem; background-color: #e8f5e9; border-radius: 10px; margin: 1rem 0;'>
            <strong>{st.session_state.full_name}</strong><br>
            <span style='color: #00843D;'>{st.session_state.user_role}</span><br>
            <span style='font-size: 0.8rem; color: gray;'>{st.session_state.user_dept}</span>
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
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#00843D", "font-size": "18px"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin": "0px", "padding": "10px", "border-radius": "10px"},
            "nav-link-selected": {"background-color": "#00843D", "color": "white"},
        }
    )
    
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# Function to get allowed request types based on department
def get_allowed_request_types():
    if st.session_state.user_role == "ADMIN":
        return ["Student Payment", "Imprest", "Petty Cash", "Supplier", "Surrender", "Refund"]
    
    result = get_user_department(st.session_state.username)
    if result:
        allowed = []
        if result[5]: allowed.append("Student Payment")
        if result[2]: allowed.append("Imprest")
        if result[3]: allowed.append("Petty Cash")
        if result[4]: allowed.append("Supplier")
        if result[6]: allowed.append("Surrender")
        if result[7]: allowed.append("Refund")
        return allowed
    return ["Imprest", "Petty Cash", "Surrender"]

# ================================================================
# DASHBOARD
# ================================================================
if choice == "📊 Dashboard":
    st.markdown("<h1 style='color: #00843D;'>📊 Performance Dashboard</h1>", unsafe_allow_html=True)
    
    df = get_requests()
    
    if df.empty:
        st.info("📭 No requests found. Create your first request using 'New Request' menu.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        
        total_requests = len(df)
        pending = len(df[df['status'].isin(['SUBMITTED', 'FINANCE_CHECKING'])])
        completed = len(df[df['status'] == 'COMPLETED'])
        
        completed_requests = df[df['status'] == 'COMPLETED'].copy()
        avg_days = 0
        if not completed_requests.empty:
            completion_times = []
            for _, row in completed_requests.iterrows():
                if row['completion_date']:
                    submitted = datetime.strptime(row['submission_date'], '%Y-%m-%d')
                    completed_date = datetime.strptime(row['completion_date'], '%Y-%m-%d')
                    days = working_days_between(submitted.date(), completed_date.date())
                    completion_times.append(days)
            avg_days = sum(completion_times) / len(completion_times) if completion_times else 0
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #00843D; margin:0;">{total_requests}</h2>
                <p style="margin:0; color: gray;">Total Requests</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #FFB81C; margin:0;">{pending}</h2>
                <p style="margin:0; color: gray;">Pending</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #00529B; margin:0;">{completed}</h2>
                <p style="margin:0; color: gray;">Completed</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #00843D; margin:0;">{avg_days:.1f}</h2>
                <p style="margin:0; color: gray;">Avg Days</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Requests by Status")
            status_counts = df['status'].value_counts()
            if not status_counts.empty:
                fig = px.pie(values=status_counts.values, names=status_counts.index, 
                            color_discrete_sequence=['#00843D', '#FFB81C', '#00529B', '#D3D3D3'])
                fig.update_layout(showlegend=True, height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("💰 Amount by Request Type")
            amount_by_type = df.groupby('request_type')['amount'].sum().reset_index()
            if not amount_by_type.empty:
                fig = px.bar(amount_by_type, x='request_type', y='amount', 
                            color='request_type', color_discrete_sequence=['#00843D', '#FFB81C', '#00529B'])
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)

# ================================================================
# NEW REQUEST - CORRECTED LOGIC
# ================================================================
elif choice == "📝 New Request":
    st.markdown("<h1 style='color: #00843D;'>📝 Create New Request</h1>", unsafe_allow_html=True)
    
    allowed_types = get_allowed_request_types()
    
    if not allowed_types:
        st.error("❌ Your department does not have permission to submit any request types.")
    else:
        with st.form("request_form"):
            request_type = st.selectbox("Request Type", allowed_types)
            
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Department", value=st.session_state.user_dept, disabled=True)
            with col2:
                st.date_input("Submission Date", value=datetime.today(), disabled=True)
            
            amount = st.number_input("Amount (KES)", min_value=0.0, format="%.2f", step=1000.0)
            payment_description = st.text_area("Payment Description *", placeholder="Enter a detailed description...")
            
            st.markdown("---")
            
            # Initialize all variables
            batch_no = None
            product_type = None
            semester = None
            payment_category = None
            financial_year = None
            funder_name = None
            imprest_no = None
            petty_cash_no = None
            supplier_name = None
            invoice_no = None
            lpo_no = None
            surrender_no = None
            previous_imprest_no = None
            refund_no = None
            refund_reason = None
            original_payment_ref = None
            
            # ======================================================
            # STUDENT PAYMENT
            # ======================================================
            if request_type == "Student Payment":
                st.subheader("🎓 Student Payment Details")
                
                # Product Type dropdown
                products = get_products()
                if products.empty:
                    st.error("No products configured. Contact admin.")
                else:
                    product_type = st.selectbox("Product Type", products['name'].tolist())
                    
                    # Financial Year (for ALL student payments)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    
                    # For Undergraduate or TVET: Show Semester and Payment Category
                    if product_type in ["Undergraduate", "TVET"]:
                        semesters = get_semesters()
                        semester = st.selectbox("Semester", semesters if semesters else ["Semester 1", "Semester 2"])
                        payment_category = st.selectbox("Payment Category", ["Tuition", "Upkeep"])
                    
                    # For Jielimishe: No Semester, No Payment Category (just show info)
                    elif product_type == "Jielimishe":
                        st.info("ℹ️ Jielimishe: Tuition payment only. No semester selection required.")
                        payment_category = "Tuition"
                    
                    # For External Resource Mobilization department
                    if st.session_state.user_dept == "External Resource Mobilization":
                        funders = get_funders()
                        if funders:
                            funder_name = st.selectbox("Funder/Partner", funders)
                        else:
                            funder_name = st.text_input("Funder/Partner Name")
                        payment_category = "Tuition"
                        st.info("ℹ️ External Resource Mobilization: Tuition payment only")
                    
                    # Batch Number (for ALL student payments)
                    batch_no = st.text_input("Batch Number *", placeholder="Enter batch number")
            
            # ======================================================
            # IMPREST
            # ======================================================
            elif request_type == "Imprest":
                st.subheader("💰 Imprest Details")
                imprest_no = st.text_input("Imprest Number *", placeholder="Enter imprest number")
            
            # ======================================================
            # PETTY CASH
            # ======================================================
            elif request_type == "Petty Cash":
                st.subheader("💵 Petty Cash Details")
                petty_cash_no = st.text_input("Petty Cash Number *", placeholder="Enter petty cash number")
            
            # ======================================================
            # SUPPLIER
            # ======================================================
            elif request_type == "Supplier":
                st.subheader("🏢 Supplier Payment Details")
                supplier_name = st.text_input("Supplier Name *")
                invoice_no = st.text_input("Invoice Number *", placeholder="Enter invoice number")
                lpo_no = st.text_input("LPO Number", placeholder="Local Purchase Order Number (optional)")
            
            # ======================================================
            # SURRENDER
            # ======================================================
            elif request_type == "Surrender":
                st.subheader("📤 Surrender Details")
                surrender_no = st.text_input("Surrender Number *", placeholder="Enter surrender number")
                previous_imprest_no = st.text_input("Previous Imprest Number *", placeholder="Enter previous imprest number")
            
            # ======================================================
            # REFUND
            # ======================================================
            elif request_type == "Refund":
                st.subheader("🔄 Refund Details")
                refund_no = st.text_input("Refund Number *", placeholder="Enter refund number")
                refund_reason = st.text_area("Reason for Refund *")
                original_payment_ref = st.text_input("Original Payment Reference *")
            
            st.markdown("---")
            submitted = st.form_submit_button("Submit Request", use_container_width=True)
            
            if submitted:
                errors = []
                if amount <= 0:
                    errors.append("Amount must be greater than 0")
                if not payment_description:
                    errors.append("Payment Description is required")
                
                # Request-specific validations
                if request_type == "Student Payment":
                    if not batch_no:
                        errors.append("Batch Number is required")
                    if not product_type:
                        errors.append("Product Type is required")
                    if not financial_year:
                        errors.append("Financial Year is required")
                    if product_type in ["Undergraduate", "TVET"]:
                        if not semester:
                            errors.append("Semester is required")
                        if not payment_category:
                            errors.append("Payment Category is required")
                    if st.session_state.user_dept == "External Resource Mobilization" and not funder_name:
                        errors.append("Funder/Partner is required")
                elif request_type == "Imprest" and not imprest_no:
                    errors.append("Imprest Number is required")
                elif request_type == "Petty Cash" and not petty_cash_no:
                    errors.append("Petty Cash Number is required")
                elif request_type == "Supplier" and (not supplier_name or not invoice_no):
                    errors.append("Supplier Name and Invoice Number are required")
                elif request_type == "Surrender" and (not surrender_no or not previous_imprest_no):
                    errors.append("Surrender Number and Previous Imprest Number are required")
                elif request_type == "Refund" and (not refund_no or not refund_reason or not original_payment_ref):
                    errors.append("Refund Number, Reason, and Original Reference are required")
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    request_data = {
                        'request_type': request_type,
                        'department_id': st.session_state.user_dept_id,
                        'department_name': st.session_state.user_dept,
                        'submitted_by': st.session_state.username,
                        'amount': amount,
                        'payment_description': payment_description,
                        # Student Payment fields
                        'batch_no': batch_no,
                        'product_type': product_type,
                        'semester': semester,
                        'payment_type': payment_category,
                        'financial_year': financial_year,
                        'funder_name': funder_name,
                        # Imprest
                        'imprest_no': imprest_no,
                        # Petty Cash (using imprest_no field)
                        'imprest_no': petty_cash_no if petty_cash_no else imprest_no,
                        # Supplier fields
                        'supplier_name': supplier_name,
                        'invoice_no': invoice_no,
                        'lpo_no': lpo_no,
                        # Surrender fields
                        'surrender_number': surrender_no,
                        'previous_imprest_no': previous_imprest_no,
                        # Refund fields
                        'refund_reason': refund_reason,
                        'original_payment_ref': original_payment_ref,
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
        st.info("📭 No requests found.")
    else:
        user_requests = df[df['submitted_by'] == st.session_state.username]
        if user_requests.empty:
            st.info("📭 You haven't submitted any requests yet.")
        else:
            display_cols = ['request_number', 'request_type', 'amount', 'status', 'submission_date', 'payment_description']
            st.dataframe(user_requests[display_cols], use_container_width=True, hide_index=True)

# ================================================================
# APPROVAL QUEUE
# ================================================================
elif choice == "✅ Approval Queue":
    if st.session_state.user_role in ["FINANCE", "ADMIN"] or st.session_state.is_finance:
        st.markdown("<h1 style='color: #00843D;'>✅ Approval Queue</h1>", unsafe_allow_html=True)
        
        df = get_requests()
        pending_requests = df[df['status'].isin(['SUBMITTED', 'FINANCE_CHECKING', 'APPROVED_FOR_PROCESSING'])]
        
        if pending_requests.empty:
            st.info("📭 No pending requests.")
        else:
            for idx, (_, req) in enumerate(pending_requests.iterrows()):
                with st.expander(f"📄 {req['request_number']} - {req['request_type']} - {req['department_name']}"):
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
                                st.write(f"**Payment Category:** {req['payment_type']}")
                            st.write(f"**Batch No:** {req['batch_no']}")
                        elif req['request_type'] == "Imprest":
                            st.write(f"**Imprest No:** {req['imprest_no']}")
                        elif req['request_type'] == "Petty Cash":
                            st.write(f"**Petty Cash No:** {req['imprest_no']}")
                        elif req['request_type'] == "Supplier":
                            st.write(f"**Supplier:** {req['supplier_name']}")
                            st.write(f"**Invoice No:** {req['invoice_no']}")
                        elif req['request_type'] == "Surrender":
                            st.write(f"**Surrender No:** {req['surrender_number']}")
                        elif req['request_type'] == "Refund":
                            st.write(f"**Refund No:** {req['imprest_no']}")
                    
                    st.write(f"**Description:** {req['payment_description']}")
                    st.markdown("---")
                    
                    col3, col4, col5 = st.columns([1, 1, 1])
                    with col3:
                        if req['status'] == 'SUBMITTED':
                            if st.button(f"Start Checking", key=f"start_{idx}"):
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
                        return_reason = st.text_input("Return Reason", key=f"return_{idx}")
                        if st.button(f"Return", key=f"return_btn_{idx}"):
                            if return_reason:
                                update_request_status(req['id'], 'RETURNED', comment, return_reason)
                                st.rerun()
    else:
        st.error("❌ Access denied. Finance only.")

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
        st.download_button("Export CSV", csv, "helb_requests.csv", "text/csv")

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
            has_payment = st.checkbox("Has Payment Category (Tuition/Upkeep)")
            has_sem = st.checkbox("Has Semester", True)
            if st.form_submit_button("Add"):
                add_product(name, category, has_payment, has_sem)
                st.rerun()
    
    with tab2:
        st.subheader("Funders")
        funders = get_funders()
        for f in funders:
            st.write(f"• {f}")
        with st.form("add_funder"):
            name = st.text_input("Funder Name")
            if st.form_submit_button("Add"):
                conn = sqlite3.connect("helb_data.db")
                conn.execute("INSERT INTO funders (name) VALUES (?)", (name,))
                conn.commit()
                conn.close()
                st.rerun()
    
    with tab3:
        st.subheader("Financial Years")
        years = get_financial_years()
        for y in years:
            st.write(f"• {y}")
        with st.form("add_year"):
            year = st.text_input("Financial Year (e.g., 2027/2028)")
            if st.form_submit_button("Add"):
                conn = sqlite3.connect("helb_data.db")
                conn.execute("INSERT INTO financial_years (name, is_active) VALUES (?, 1)", (year,))
                conn.commit()
                conn.close()
                st.rerun()
    
    with tab4:
        st.subheader("Semesters")
        semesters = get_semesters()
        for s in semesters:
            st.write(f"• {s}")
        with st.form("add_semester"):
            sem = st.text_input("Semester Name")
            if st.form_submit_button("Add"):
                conn = sqlite3.connect("helb_data.db")
                conn.execute("INSERT INTO semesters (name) VALUES (?)", (sem,))
                conn.commit()
                conn.close()
                st.rerun()
