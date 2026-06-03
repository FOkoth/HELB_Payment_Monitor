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
    /* HELB Primary Colors */
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
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    
    /* Form styling */
    .stForm {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Required field indicator */
    .required-field::after {
        content: " *";
        color: red;
        font-weight: bold;
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
# Sidebar
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
        return ["Imprest", "Petty Cash", "Supplier", "Student Payment", "Surrender", "Refund"]
    
    result = get_user_department(st.session_state.username)
    if result:
        allowed = []
        if result[2]: allowed.append("Imprest")
        if result[3]: allowed.append("Petty Cash")
        if result[4]: allowed.append("Supplier")
        if result[5]: allowed.append("Student Payment")
        if result[6]: allowed.append("Surrender")
        if result[7]: allowed.append("Refund")
        return allowed
    return ["Imprest", "Petty Cash", "Surrender"]

# Main content area
if choice == "📊 Dashboard":
    st.markdown("<h1 style='color: #00843D;'>📊 Performance Dashboard</h1>", unsafe_allow_html=True)
    
    df = get_requests()
    
    if df.empty:
        st.info("📭 No requests found. Create your first request using 'New Request' menu.")
    else:
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_requests = len(df)
        pending = len(df[df['status'].isin(['SUBMITTED', 'FINANCE_CHECKING'])])
        completed = len(df[df['status'] == 'COMPLETED'])
        returned = len(df[df['status'] == 'RETURNED'])
        
        # Calculate average completion time
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
                <p style="margin:0; color: gray;">Avg Days to Complete</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Requests by Status")
            status_counts = df['status'].value_counts()
            if not status_counts.empty:
                fig = px.pie(values=status_counts.values, names=status_counts.index, 
                            color_discrete_sequence=['#00843D', '#FFB81C', '#00529B', '#D3D3D3', '#999999'])
                fig.update_layout(showlegend=True, height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No status data available")
        
        with col2:
            st.subheader("💰 Amount by Request Type")
            amount_by_type = df.groupby('request_type')['amount'].sum().reset_index()
            if not amount_by_type.empty:
                fig = px.bar(amount_by_type, x='request_type', y='amount', 
                            color='request_type', color_discrete_sequence=['#00843D', '#FFB81C', '#00529B'])
                fig.update_layout(showlegend=False, height=400, xaxis_title="Request Type", yaxis_title="Amount (KES)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No amount data available")
        
        # SLA Compliance Table
        st.subheader("⏱️ SLA Compliance & Insights")
        
        # Calculate SLA for each request
        sla_data = []
        sla_map = {'Imprest': 5, 'Supplier': 7, 'Student Payment': 3, 'Surrender': 4, 'Petty Cash': 3, 'Refund': 10}
        
        for _, row in df.iterrows():
            if row['status'] == 'COMPLETED' and row['completion_date']:
                submitted = datetime.strptime(row['submission_date'], '%Y-%m-%d')
                completed_date = datetime.strptime(row['completion_date'], '%Y-%m-%d')
                actual_days = working_days_between(submitted.date(), completed_date.date())
                
                sla_days = sla_map.get(row['request_type'], 5)
                breached = actual_days > sla_days
                sla_data.append({
                    'Request #': row['request_number'],
                    'Type': row['request_type'],
                    'Department': row['department_name'],
                    'Actual Days': actual_days,
                    'SLA Days': sla_days,
                    'Breached': '⚠️ Yes' if breached else '✅ No',
                })
        
        if sla_data:
            sla_df = pd.DataFrame(sla_data)
            st.dataframe(sla_df, use_container_width=True, hide_index=True)
            
            # Insights
            breach_rate = (sla_df['Breached'].str.contains('Yes').sum() / len(sla_df)) * 100
            worst_dept = sla_df.groupby('Department')['Actual Days'].mean().idxmax() if not sla_df.empty else "N/A"
            most_common_type = sla_df['Type'].mode().iloc[0] if not sla_df.empty else "N/A"
            
            insight_color = "#00843D" if breach_rate < 20 else "#FFB81C"
            st.markdown(f"""
            <div class="success-box">
                <strong>💡 Intelligent Insights:</strong><br>
                • Overall SLA breach rate: <span style='color: {insight_color}; font-weight: bold;'>{breach_rate:.1f}%</span><br>
                • Average processing time: <strong>{avg_days:.1f}</strong> working days<br>
                • Department with longest processing time: <strong>{worst_dept}</strong><br>
                • Most common request type: <strong>{most_common_type}</strong><br>
                • {'✅ System performance is within acceptable range' if breach_rate < 20 else '⚠️ High breach rate detected - review workflow and resource allocation'}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Complete some requests to see SLA insights.")

elif choice == "📝 New Request":
    st.markdown("<h1 style='color: #00843D;'>📝 Create New Request</h1>", unsafe_allow_html=True)
    
    allowed_types = get_allowed_request_types()
    
    if not allowed_types:
        st.error("❌ Your department does not have permission to submit any request types. Please contact admin.")
    else:
        with st.form("request_form"):
            request_type = st.selectbox("Request Type", allowed_types)
            
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Department", value=st.session_state.user_dept, disabled=True)
            with col2:
                st.date_input("Submission Date", value=datetime.today(), disabled=True)
            
            amount = st.number_input("Amount (KES)", min_value=0.0, format="%.2f", step=1000.0)
            
            # Payment Description - for ALL request types
            payment_description = st.text_area("Payment Description", 
                                               placeholder="Enter a detailed description of this payment request...",
                                               help="Provide clear description of what this payment is for")
            
            # Initialize variables
            imprest_no = batch_no = supplier_name = invoice_no = lpo_no = None
            product_type = payment_type = funder_name = None
            financial_year = semester = None
            refund_reason = original_payment_ref = None
            surrender_number = previous_imprest_no = None
            
            # Imprest / Petty Cash
            if request_type in ["Imprest", "Petty Cash"]:
                imprest_no = st.text_input(f"{request_type} Number *", 
                                           placeholder=f"Enter {request_type} number")
            
            # Supplier Payment
            if request_type == "Supplier":
                supplier_name = st.text_input("Supplier Name *")
                invoice_no = st.text_input("Invoice Number *")
                lpo_no = st.text_input("LPO Number", help="Local Purchase Order Number if available")
            
            # Student Payment - Lending department
            if request_type == "Student Payment" and st.session_state.user_dept == "Lending":
                products = get_products()
                if not products.empty:
                    product_type = st.selectbox("Product Type", products['name'].tolist())
                    
                    # Financial Year (for all Student Payments)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    
                    # Get product details to check if semester is required
                    product_row = products[products['name'] == product_type]
                    has_semester = product_row['has_semester'].iloc[0] if not product_row.empty else 1
                    has_payment_type = product_row['has_payment_type'].iloc[0] if not product_row.empty else 1
                    
                    # Semester (only for products that have it - Undergraduate, TVET)
                    if has_semester:
                        semesters = get_semesters()
                        semester = st.selectbox("Semester", semesters if semesters else ["Semester 1", "Semester 2"])
                    
                    # Payment Type (Tuition/Upkeep)
                    if has_payment_type and product_type in ["Undergraduate", "TVET"]:
                        payment_type = st.selectbox("Payment Type", ["Upkeep", "Tuition"])
                    elif product_type == "Jielimishe":
                        payment_type = "Tuition"
                        st.info("ℹ️ Jielimishe product: Tuition payment only")
                    
                    batch_no = st.text_input("Batch Number *")
                else:
                    st.warning("No products configured. Contact admin to add products.")
            
            # Student Payment - ERM department (Partner Funds)
            elif request_type == "Student Payment" and st.session_state.user_dept == "External Resource Mobilization":
                funders = get_funders()
                if funders:
                    funder_name = st.selectbox("Select Funder/Partner", funders)
                else:
                    funder_name = st.text_input("Funder/Partner Name *")
                
                # Financial Year for ERM
                financial_years = get_financial_years()
                financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                
                # ERM - Tuition by default
                payment_type = "Tuition"
                st.info("ℹ️ External Resource Mobilization: Tuition payment only")
                
                batch_no = st.text_input("Batch Number *")
            
            # Refund - Debt Management
            if request_type == "Refund":
                refund_reason = st.text_area("Reason for Refund *")
                original_payment_ref = st.text_input("Original Payment Reference *")
            
            # Surrender
            if request_type == "Surrender":
                surrender_number = st.text_input("Surrender Number *")
                previous_imprest_no = st.text_input("Previous Imprest Number *")
            
            submitted = st.form_submit_button("Submit Request", use_container_width=True)
            
            if submitted:
                # Validation
                errors = []
                if amount <= 0:
                    errors.append("Amount must be greater than 0")
                if not payment_description:
                    errors.append("Payment Description is required")
                if request_type in ["Imprest", "Petty Cash"] and not imprest_no:
                    errors.append(f"{request_type} number is required")
                if request_type == "Supplier" and (not supplier_name or not invoice_no):
                    errors.append("Supplier name and invoice number are required")
                if request_type == "Student Payment" and not batch_no:
                    errors.append("Batch number is required")
                if request_type == "Student Payment" and not financial_year:
                    errors.append("Financial Year is required")
                if request_type == "Surrender" and (not surrender_number or not previous_imprest_no):
                    errors.append("Surrender number and previous imprest number are required")
                if request_type == "Refund" and (not refund_reason or not original_payment_ref):
                    errors.append("Refund reason and original payment reference are required")
                
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
                        'imprest_no': imprest_no,
                        'batch_no': batch_no,
                        'supplier_name': supplier_name,
                        'invoice_no': invoice_no,
                        'lpo_no': lpo_no,
                        'product_type': product_type,
                        'payment_type': payment_type,
                        'funder_name': funder_name,
                        'financial_year': financial_year,
                        'semester': semester,
                        'refund_reason': refund_reason,
                        'original_payment_ref': original_payment_ref,
                        'surrender_number': surrender_number,
                        'previous_imprest_no': previous_imprest_no,
                        'status': 'SUBMITTED'
                    }
                    
                    request_number = save_request(request_data)
                    st.success(f"✅ Request {request_number} submitted successfully on {datetime.today().strftime('%d/%m/%Y')}!")
                    st.balloons()

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

elif choice == "✅ Approval Queue":
    if st.session_state.user_role in ["FINANCE", "ADMIN"] or st.session_state.is_finance:
        st.markdown("<h1 style='color: #00843D;'>✅ Approval Queue</h1>", unsafe_allow_html=True)
        
        df = get_requests()
        pending_requests = df[df['status'].isin(['SUBMITTED', 'FINANCE_CHECKING', 'APPROVED_FOR_PROCESSING'])]
        
        if pending_requests.empty:
            st.info("📭 No pending requests for approval.")
        else:
            for idx, (_, req) in enumerate(pending_requests.iterrows()):
                with st.expander(f"📄 {req['request_number']} - {req['request_type']} - {req['department_name']} - {req['status']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Department:** {req['department_name']}")
                        st.markdown(f"**Submitted By:** {req['submitted_by']}")
                        st.markdown(f"**Submission Date:** {req['submission_date']}")
                        st.markdown(f"**Amount:** KES {req['amount']:,.2f}")
                    
                    with col2:
                        st.markdown(f"**Request Type:** {req['request_type']}")
                        if req['request_type'] == 'Imprest':
                            st.markdown(f"**Imprest No:** {req['imprest_no']}")
                        elif req['request_type'] == 'Petty Cash':
                            st.markdown(f"**Reference No:** {req['imprest_no']}")
                        elif req['request_type'] == 'Supplier':
                            st.markdown(f"**Supplier:** {req['supplier_name']}")
                            st.markdown(f"**Invoice:** {req['invoice_no']}")
                            st.markdown(f"**LPO:** {req['lpo_no'] if req['lpo_no'] else 'N/A'}")
                        elif req['request_type'] == 'Student Payment':
                            if req['product_type']:
                                st.markdown(f"**Product:** {req['product_type']}")
                            if req['payment_type']:
                                st.markdown(f"**Payment Type:** {req['payment_type']}")
                            if req['funder_name']:
                                st.markdown(f"**Funder:** {req['funder_name']}")
                            if req['financial_year']:
                                st.markdown(f"**Financial Year:** {req['financial_year']}")
                            if req['semester']:
                                st.markdown(f"**Semester:** {req['semester']}")
                            st.markdown(f"**Batch No:** {req['batch_no']}")
                        elif req['request_type'] == 'Refund':
                            st.markdown(f"**Reason:** {req['refund_reason']}")
                            st.markdown(f"**Original Ref:** {req['original_payment_ref']}")
                        elif req['request_type'] == 'Surrender':
                            st.markdown(f"**Surrender No:** {req['surrender_number']}")
                            st.markdown(f"**Previous Imprest:** {req['previous_imprest_no']}")
                    
                    st.markdown("**Payment Description:**")
                    st.info(req['payment_description'] if req['payment_description'] else "No description provided")
                    
                    st.markdown("---")
                    
                    col3, col4, col5 = st.columns([1, 1, 1])
                    
                    with col3:
                        if req['status'] == 'SUBMITTED':
                            if st.button(f"📋 Start Checking", key=f"start_{req['id']}_{idx}"):
                                update_request_status(req['id'], 'FINANCE_CHECKING')
                                st.success(f"✅ Request {req['request_number']} moved to checking stage")
                                st.rerun()
                        
                        elif req['status'] == 'FINANCE_CHECKING':
                            if st.button(f"✅ Approve", key=f"approve_{req['id']}_{idx}"):
                                update_request_status(req['id'], 'APPROVED_FOR_PROCESSING')
                                st.success(f"✅ Request {req['request_number']} approved for processing")
                                st.rerun()
                        
                        elif req['status'] == 'APPROVED_FOR_PROCESSING':
                            if st.button(f"🎉 Mark Complete", key=f"complete_{req['id']}_{idx}"):
                                update_request_status(req['id'], 'COMPLETED')
                                st.balloons()
                                st.success(f"✅ Request {req['request_number']} completed!")
                                st.rerun()
                    
                    with col4:
                        if req['status'] in ['SUBMITTED', 'FINANCE_CHECKING']:
                            finance_comment = st.text_area("Finance Comment (optional)", 
                                                          key=f"comment_{req['id']}_{idx}",
                                                          placeholder="Add any notes about this request...")
                    
                    with col5:
                        if req['status'] in ['SUBMITTED', 'FINANCE_CHECKING']:
                            return_reason = st.text_input("Return Reason (if returning)", 
                                                         key=f"return_{req['id']}_{idx}",
                                                         placeholder="Why is this being returned?")
                            if st.button(f"↩️ Return to Dept", key=f"return_btn_{req['id']}_{idx}"):
                                if return_reason:
                                    update_request_status(req['id'], 'RETURNED', finance_comment, return_reason)
                                    st.warning(f"⚠️ Request {req['request_number']} returned to department")
                                    st.rerun()
                                else:
                                    st.error("❌ Please provide a return reason")
    else:
        st.error("❌ Access denied. Finance department only.")

elif choice == "📑 Reports":
    st.markdown("<h1 style='color: #00843D;'>📑 Reports & Export</h1>", unsafe_allow_html=True)
    
    df = get_requests()
    if df.empty:
        st.info("📭 No data available for reports.")
    else:
        # Export button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export to CSV",
            data=csv,
            file_name=f"helb_requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.markdown("---")
        st.subheader("🔍 Filter Reports")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.multiselect("Status", df['status'].unique())
        with col2:
            dept_filter = st.multiselect("Department", df['department_name'].dropna().unique())
        with col3:
            type_filter = st.multiselect("Request Type", df['request_type'].unique())
        
        filtered_df = df.copy()
        if status_filter:
            filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
        if dept_filter:
            filtered_df = filtered_df[filtered_df['department_name'].isin(dept_filter)]
        if type_filter:
            filtered_df = filtered_df[filtered_df['request_type'].isin(type_filter)]
        
        st.markdown(f"**Showing {len(filtered_df)} of {len(df)} requests**")
        st.dataframe(filtered_df, use_container_width=True)

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
            new_password = st.text_input("Password", type="password")
            new_full_name = st.text_input("Full Name")
            new_role = st.selectbox("Role", ["DEPARTMENT", "FINANCE", "ADMIN"])
            
            depts = get_departments()
            dept_options = {row['name']: row['id'] for _, row in depts.iterrows()}
            new_department = st.selectbox("Department (if DEPARTMENT role)", ["None"] + list(dept_options.keys()))
            
            if st.form_submit_button("Create User"):
                if new_username and new_password:
                    dept_id = dept_options.get(new_department) if new_department != "None" else None
                    success = create_user(new_username, new_password, new_role, dept_id, new_full_name)
                    if success:
                        st.success(f"✅ User {new_username} created successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Username already exists!")
                else:
                    st.error("❌ Username and password are required")
    
    with tab2:
        st.subheader("🏢 Department Management")
        
        depts = get_departments()
        st.dataframe(depts, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("➕ Add New Department")
        with st.form("add_dept_form"):
            dept_name = st.text_input("Department Name")
            
            st.markdown("**Request Type Permissions:**")
            col1, col2 = st.columns(2)
            with col1:
                can_imprest = st.checkbox("Can submit Imprest", value=True)
                can_petty = st.checkbox("Can submit Petty Cash", value=True)
                can_supplier = st.checkbox("Can submit Supplier", value=False)
            with col2:
                can_student = st.checkbox("Can submit Student Payment", value=False)
                can_surrender = st.checkbox("Can submit Surrender", value=True)
                can_refund = st.checkbox("Can submit Refund", value=False)
            
            st.markdown("**Special Requirements:**")
            col3, col4 = st.columns(2)
            with col3:
                requires_product = st.checkbox("Requires Product Type (Lending)", value=False)
            with col4:
                requires_funder = st.checkbox("Requires Funder (ERM)", value=False)
            
            is_finance = st.checkbox("This is Finance Department (can approve all)", value=False)
            
            if st.form_submit_button("Create Department"):
                if dept_name:
                    permissions = [can_imprest, can_petty, can_supplier, can_student, can_surrender, can_refund, requires_product, requires_funder, is_finance]
                    success = create_department(dept_name, permissions)
                    if success:
                        st.success(f"✅ Department {dept_name} created!")
                        st.rerun()
                    else:
                        st.error("❌ Department name already exists!")
                else:
                    st.error("❌ Department name is required")
    
    with tab3:
        st.subheader("📦 Product Management (Lending)")
        
        products = get_products()
        st.dataframe(products, use_container_width=True)
        
        st.markdown("---")
        st.subheader("➕ Add New Product")
        with st.form("add_product_form"):
            product_name = st.text_input("Product Name")
            product_category = st.selectbox("Category", ["LOAN", "SCHOLARSHIP", "FUNDER"])
            has_payment_type = st.checkbox("Has Payment Type (Upkeep/Tuition)")
            has_semester = st.checkbox("Has Semester Selection", value=True)
            
            if st.form_submit_button("Add Product"):
                if product_name:
                    success = add_product(product_name, product_category, 1 if has_payment_type else 0, 1 if has_semester else 0)
                    if success:
                        st.success(f"✅ Product {product_name} added!")
                        st.rerun()
                    else:
                        st.error("❌ Product name already exists!")
                else:
                    st.error("❌ Product name required")
    
    with tab4:
        st.subheader("💰 Funder Management (ERM)")
        
        funders = get_funders()
        if funders:
            st.write("**Current Funders/Partners:**")
            for f in funders:
                st.markdown(f"• {f}")
        else:
            st.info("No funders added yet.")
        
        st.markdown("---")
        st.subheader("➕ Add New Funder")
        with st.form("add_funder_form"):
            funder_name = st.text_input("Funder/Partner Name")
            if st.form_submit_button("Add Funder"):
                if funder_name:
                    conn = sqlite3.connect("helb_data.db")
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO funders (name) VALUES (?)", (funder_name,))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Funder {funder_name} added!")
                    st.rerun()
                else:
                    st.error("❌ Funder name required")
    
    with tab5:
        st.subheader("📅 Financial Year Management")
        
        financial_years = get_financial_years()
        if financial_years:
            st.write("**Current Financial Years:**")
            for fy in financial_years:
                st.markdown(f"• {fy}")
        else:
            st.info("No financial years added yet.")
        
        st.markdown("---")
        st.subheader("➕ Add New Financial Year")
        with st.form("add_fy_form"):
            fy_name = st.text_input("Financial Year (e.g., 2027/2028)")
            if st.form_submit_button("Add Financial Year"):
                if fy_name:
                    conn = sqlite3.connect("helb_data.db")
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO financial_years (name, is_active) VALUES (?, 1)", (fy_name,))
                        conn.commit()
                        st.success(f"✅ Financial Year {fy_name} added!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Financial year already exists!")
                    finally:
                        conn.close()
                else:
                    st.error("❌ Financial year name required")
