import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from database import (
    init_database, get_requests, save_request, update_request_status, 
    authenticate_user, get_user_department, get_products, get_funders,
    get_all_users, create_user, create_department, get_departments,
    get_financial_years, get_semesters, add_product,
    update_user_password, get_user_by_username, get_pending_duration,
    update_payment_details, get_dashboard_stats, get_department_performance,
    get_trend_data, get_breach_analysis
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
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #00529B;
        color: white;
        transform: translateY(-1px);
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
    
    div[data-testid="stExpander"] details summary p {
        font-weight: 600;
        color: #00843D;
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

# Password Change Modal
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

# Change Password option
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
    
    # Filters
    st.subheader("🔍 Filter Data")
    col1, col2 = st.columns(2)
    with col1:
        financial_years = ["All"] + get_financial_years()
        selected_fy = st.selectbox("Financial Year", financial_years)
    with col2:
        quarters = ["All", "Q1 (Jul-Sep)", "Q2 (Oct-Dec)", "Q3 (Jan-Mar)", "Q4 (Apr-Jun)"]
        selected_quarter = st.selectbox("Quarter", quarters)
    
    # Get statistics
    stats = get_dashboard_stats(selected_fy if selected_fy != "All" else None, 
                                 selected_quarter if selected_quarter != "All" else None)
    
    # KPI Cards
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
                <small>Working days only</small>
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
    
    # Charts Row
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Monthly Trends")
        trend_data = get_trend_data(selected_fy if selected_fy != "All" else None)
        if not trend_data.empty:
            fig = px.line(trend_data, x='month', y='request_count', 
                         title="Request Volume Trend",
                         color_discrete_sequence=['#00843D'])
            fig.update_layout(xaxis_title="Month", yaxis_title="Number of Requests", height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trend data available")
    
    with col2:
        st.subheader("💰 Amount by Request Type")
        df = get_requests()
        if selected_fy != "All":
            df = df[df['financial_year'] == selected_fy]
        amount_by_type = df.groupby('request_type')['amount'].sum().reset_index()
        if not amount_by_type.empty:
            fig = px.bar(amount_by_type, x='request_type', y='amount',
                        color_discrete_sequence=['#00843D', '#FFB81C', '#00529B'])
            fig.update_layout(xaxis_title="Request Type", yaxis_title="Amount (KES)", height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No amount data available")
    
    # Department Performance
    st.subheader("🏢 Department Performance")
    dept_perf = get_department_performance(selected_fy if selected_fy != "All" else None)
    if not dept_perf.empty:
        fig = px.bar(dept_perf, x='department', y='completion_rate',
                    title="Completion Rate by Department",
                    color='completion_rate',
                    color_continuous_scale=['#DC3545', '#FFB81C', '#00843D'])
        fig.update_layout(xaxis_title="Department", yaxis_title="Completion Rate (%)", height=450)
        st.plotly_chart(fig, use_container_width=True)
    
    # Breach Analysis Table
    st.subheader("⚠️ SLA Breach Analysis")
    breach_df = get_breach_analysis(selected_fy if selected_fy != "All" else None)
    if not breach_df.empty:
        breached_only = breach_df[breach_df['status'] == 'Breached']
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Breached Requests", len(breached_only))
        with col2:
            breach_percent = (len(breached_only) / len(breach_df) * 100) if len(breach_df) > 0 else 0
            st.metric("Breach Percentage", f"{breach_percent:.1f}%")
        st.dataframe(breach_df, use_container_width=True, hide_index=True)
    else:
        st.info("No completed requests to analyze SLA compliance")
    
    # Insights
    st.subheader("💡 Intelligent Insights")
    
    insights = []
    if stats['breach_rate'] > 20:
        insights.append("⚠️ **High breach rate detected** - Review workflow efficiency and resource allocation")
    elif stats['breach_rate'] > 10:
        insights.append("📊 **Moderate breach rate** - Consider process improvements and staff training")
    else:
        insights.append("✅ **Excellent performance** - Breach rate is within acceptable range")
    
    if stats['avg_completion_time'] > 5:
        insights.append(f"⏱️ **Average completion time is {stats['avg_completion_time']:.1f} days** - Target is 3-5 working days")
    elif stats['avg_completion_time'] > 3:
        insights.append(f"📈 **Average completion time is {stats['avg_completion_time']:.1f} days** - Room for improvement")
    
    if not dept_perf.empty:
        worst_dept = dept_perf.loc[dept_perf['completion_rate'].idxmin()]
        best_dept = dept_perf.loc[dept_perf['completion_rate'].idxmax()]
        insights.append(f"🏆 **Best performing department:** {best_dept['department']} ({best_dept['completion_rate']:.1f}% completion rate)")
        insights.append(f"⚠️ **Needs attention:** {worst_dept['department']} ({worst_dept['completion_rate']:.1f}% completion rate)")
    
    if stats['total_returned'] > stats['total_requests'] * 0.1:
        insights.append(f"↩️ **High return rate** ({stats['total_returned']} requests returned) - Review submission quality")
    
    for insight in insights:
        st.info(insight)

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
            display_data = []
            for _, row in user_requests.iterrows():
                status_display = ""
                if row['status'] == 'PAID':
                    status_display = "✅ Paid"
                elif row['status'] == 'CLEARED':
                    status_display = "✅ Cleared"
                elif row['status'] == 'RECEIVED_BY_FINANCE':
                    days = get_pending_duration(row['submission_date'])
                    status_display = f"⏳ Received by Finance ({days} days)"
                elif row['status'] == 'RETURNED':
                    status_display = f"↩️ Returned"
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
        pending = df[df['status'].isin(['SUBMITTED', 'RECEIVED_BY_FINANCE', 'FINANCE_CHECKING', 'APPROVED_FOR_PROCESSING'])]
        
        if pending.empty:
            st.info("No pending requests.")
        else:
            for idx, (_, req) in enumerate(pending.iterrows()):
                days_pending = get_pending_duration(req['submission_date'])
                with st.expander(f"📄 {req['request_number']} - {req['request_type']} - {req['department_name']} - {req['status']} (Pending {days_pending} days)"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Department:** {req['department_name']}")
                        st.write(f"**Submitted By:** {req['submitted_by']}")
                        st.write(f"**Submission Date:** {req['submission_date']}")
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
                            if st.button(f"📋 Receive Request", key=f"receive_{idx}"):
                                update_request_status(req['id'], 'RECEIVED_BY_FINANCE')
                                st.success(f"✅ Request {req['request_number']} received by Finance")
                                st.rerun()
                        
                        elif req['status'] == 'RECEIVED_BY_FINANCE':
                            payment_ref = st.text_input("Payment Reference Number", key=f"ref_{idx}")
                            if st.button(f"✅ Mark as Paid", key=f"paid_{idx}"):
                                if payment_ref:
                                    if req['request_type'] == 'Surrender':
                                        update_request_status(req['id'], 'CLEARED')
                                    else:
                                        update_request_status(req['id'], 'PAID')
                                    update_payment_details(req['id'], payment_ref)
                                    
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
                        if req['status'] == 'SUBMITTED':
                            reason = st.text_input("Return Reason", key=f"return_{idx}")
                            if st.button(f"↩️ Return Request", key=f"return_btn_{idx}"):
                                if reason:
                                    update_request_status(req['id'], 'RETURNED', comment, reason)
                                    st.warning(f"⚠️ Request {req['request_number']} returned to department")
                                    st.rerun()
                                else:
                                    st.error("❌ Please provide a return reason")
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
        st.download_button("📥 Export to CSV", csv, "helb_requests.csv", "text/csv", use_container_width=True)
        
        st.subheader("📊 Summary Statistics")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**By Status:**")
            status_counts = df['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            st.dataframe(status_counts, use_container_width=True, hide_index=True)
        with col2:
            st.write("**By Department:**")
            dept_counts = df['department_name'].value_counts().reset_index()
            dept_counts.columns = ['Department', 'Count']
            st.dataframe(dept_counts, use_container_width=True, hide_index=True)
        
        st.subheader("📅 Financial Year Summary")
        fy_summary = df.groupby('financial_year').agg({
            'amount': 'sum',
            'request_number': 'count'
        }).reset_index()
        fy_summary.columns = ['Financial Year', 'Total Amount', 'Request Count']
        st.dataframe(fy_summary, use_container_width=True, hide_index=True)

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
