import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from datetime import datetime, date, timedelta
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {
        --helb-green: #00843D;
        --helb-green-light: #00B347;
        --helb-green-dark: #006030;
        --helb-gold: #FFB81C;
        --helb-blue: #00529B;
        --helb-red: #DC3545;
        --gray-50: #F9FAFB;
        --gray-100: #F3F4F6;
        --gray-200: #E5E7EB;
        --gray-300: #D1D5DB;
        --gray-400: #9CA3AF;
        --gray-500: #6B7280;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --radius-sm: 0.375rem;
        --radius-md: 0.5rem;
        --radius-lg: 0.75rem;
        --radius-xl: 1rem;
    }
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Compact Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--gray-50) 0%, white 100%);
        border-right: 1px solid var(--gray-200);
        padding-top: 0.5rem;
        min-width: 220px;
    }
    
    [data-testid="stSidebar"] .user-info {
        background: linear-gradient(135deg, var(--helb-green) 0%, var(--helb-blue) 100%);
        padding: 0.5rem;
        border-radius: var(--radius-lg);
        margin: 0.5rem 0;
        color: white;
        text-align: center;
    }
    
    [data-testid="stSidebar"] .user-info strong {
        font-size: 0.8rem;
        display: block;
    }
    
    [data-testid="stSidebar"] .user-info span {
        font-size: 0.65rem;
        opacity: 0.9;
    }
    
    /* Header Banner */
    .main-header {
        background: linear-gradient(135deg, #00843D 0%, #00529B 100%);
        padding: 0.75rem 1.5rem;
        border-radius: var(--radius-lg);
        margin-bottom: 1rem;
        box-shadow: var(--shadow-md);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 1.3rem;
        font-weight: 700;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        margin: 0.1rem 0 0 0;
        font-size: 0.7rem;
    }
    
    /* Filter Bar */
    .filter-bar {
        background: var(--gray-50);
        padding: 0.5rem 1rem;
        border-radius: var(--radius-lg);
        margin-bottom: 1rem;
        border: 1px solid var(--gray-200);
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        align-items: flex-end;
    }
    
    .filter-label {
        font-size: 0.65rem;
        font-weight: 600;
        color: var(--gray-600);
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }
    
    /* Footer */
    .main-footer {
        background: var(--gray-800);
        color: var(--gray-400);
        padding: 0.5rem 1rem;
        margin-top: 1.5rem;
        border-radius: var(--radius-lg);
        text-align: center;
        font-size: 0.65rem;
    }
    
    /* Metric Cards */
    .metric-card {
        background: white;
        padding: 0.8rem;
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-sm);
        text-align: center;
        border: 1px solid var(--gray-200);
        height: 100%;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
        border-color: var(--helb-green);
    }
    
    .metric-card h3 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--helb-green);
    }
    
    .metric-card p {
        margin: 0.2rem 0 0 0;
        color: var(--gray-500);
        font-size: 0.7rem;
        text-transform: uppercase;
        font-weight: 600;
    }
    
    .metric-card small {
        font-size: 0.6rem;
        color: var(--gray-400);
    }
    
    .trend-up { color: #00843D; font-weight: bold; }
    .trend-down { color: #DC3545; font-weight: bold; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
        background: var(--gray-100);
        padding: 0.25rem;
        border-radius: var(--radius-xl);
        margin-bottom: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-lg);
        padding: 0.3rem 0.8rem;
        font-weight: 500;
        font-size: 0.75rem;
        color: var(--gray-600);
        white-space: nowrap;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00843D 0%, #00529B 100%);
        color: white !important;
    }
    
    /* Status Badges */
    .status-paid, .status-cleared, .status-pending, .status-confirmed {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 20px;
        font-size: 0.65rem;
        font-weight: 600;
    }
    .status-paid, .status-cleared { background: #E8F5E9; color: #00843D; }
    .status-pending { background: #FFEBEE; color: #DC3545; }
    .status-confirmed { background: #E0F7FA; color: #00BCD4; }
    
    /* Data Table */
    .dataframe {
        font-size: 0.7rem;
    }
    .dataframe thead tr th {
        background: linear-gradient(135deg, #00843D 0%, #00529B 100%);
        color: white;
        font-weight: 600;
        padding: 0.4rem;
        font-size: 0.7rem;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00843D 0%, #006030 100%);
        color: white;
        border: none;
        border-radius: var(--radius-md);
        padding: 0.3rem 0.8rem;
        font-weight: 500;
        font-size: 0.7rem;
        width: 100%;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: var(--gray-50);
        border-radius: var(--radius-md);
        font-weight: 500;
        font-size: 0.75rem;
        border: 1px solid var(--gray-200);
    }
    
    /* Approval Stages */
    .stage-completed {
        background-color: #00843D;
        color: white;
        text-align: center;
        padding: 0.3rem;
        border-radius: 8px;
        font-size: 0.7rem;
        font-weight: 500;
    }
    
    .stage-pending {
        background-color: #FFF8E1;
        color: #FFB81C;
        text-align: center;
        padding: 0.3rem;
        border-radius: 8px;
        font-size: 0.7rem;
        border: 1px solid #FFB81C;
    }
    
    .stage-current {
        background-color: #00843D;
        color: white;
        text-align: center;
        padding: 0.3rem;
        border-radius: 8px;
        font-size: 0.7rem;
        font-weight: bold;
    }
    
    /* Insight Box */
    .insight-box {
        background: #F0F9FF;
        border-left: 4px solid #0284C7;
        padding: 0.75rem;
        border-radius: var(--radius-md);
        margin: 0.5rem 0;
    }
    
    .alert-box {
        background: #FEF2F2;
        border-left: 4px solid #DC2626;
        padding: 0.75rem;
        border-radius: var(--radius-md);
        margin: 0.5rem 0;
    }
    
    .warning-box {
        background: #FFFBEB;
        border-left: 4px solid #F59E0B;
        padding: 0.75rem;
        border-radius: var(--radius-md);
        margin: 0.5rem 0;
    }
    
    /* Log Entries */
    .log-submitted { background: #E3F2FD; border-left: 3px solid #2196F3; padding: 0.3rem; margin: 0.2rem 0; border-radius: 5px; font-size: 0.7rem; }
    .log-received { background: #E8F5E9; border-left: 3px solid #4CAF50; padding: 0.3rem; margin: 0.2rem 0; border-radius: 5px; font-size: 0.7rem; }
    .log-returned { background: #FFEBEE; border-left: 3px solid #F44336; padding: 0.3rem; margin: 0.2rem 0; border-radius: 5px; font-size: 0.7rem; }
    .log-paid { background: #E8F5E9; border-left: 3px solid #00843D; padding: 0.3rem; margin: 0.2rem 0; border-radius: 5px; font-size: 0.7rem; }
    .log-stage { background: #F3E5F5; border-left: 3px solid #9C27B0; padding: 0.3rem; margin: 0.2rem 0; border-radius: 5px; font-size: 0.7rem; }
    
    @media (max-width: 768px) {
        .metric-card h3 { font-size: 1rem; }
        .main-header h1 { font-size: 1rem; }
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
if 'selected_financial_year' not in st.session_state:
    st.session_state.selected_financial_year = "All"
if 'selected_quarter' not in st.session_state:
    st.session_state.selected_quarter = "All"
if 'selected_month' not in st.session_state:
    st.session_state.selected_month = "All"

def filter_by_filters(df, financial_year, quarter, month):
    if df.empty or 'submission_date' not in df.columns:
        return df
    
    df['submission_date_dt'] = pd.to_datetime(df['submission_date'])
    
    if financial_year and financial_year != "All":
        year_start = int(financial_year.split('/')[0])
        year_end = int(financial_year.split('/')[1])
        start_date = date(year_start, 7, 1)
        end_date = date(year_end, 6, 30)
        df = df[(df['submission_date_dt'].dt.date >= start_date) & (df['submission_date_dt'].dt.date <= end_date)]
    
    if quarter and quarter != "All":
        if quarter == "Q1 (Jul-Sep)":
            df = df[df['submission_date_dt'].dt.month.isin([7, 8, 9])]
        elif quarter == "Q2 (Oct-Dec)":
            df = df[df['submission_date_dt'].dt.month.isin([10, 11, 12])]
        elif quarter == "Q3 (Jan-Mar)":
            df = df[df['submission_date_dt'].dt.month.isin([1, 2, 3])]
        elif quarter == "Q4 (Apr-Jun)":
            df = df[df['submission_date_dt'].dt.month.isin([4, 5, 6])]
    
    if month and month != "All":
        month_num = {"January":1, "February":2, "March":3, "April":4, "May":5, "June":6,
                     "July":7, "August":8, "September":9, "October":10, "November":11, "December":12}.get(month, 0)
        if month_num:
            df = df[df['submission_date_dt'].dt.month == month_num]
    
    return df

def get_reference_number(row):
    if row['request_type'] == "Student Payment":
        return row.get('batch_no', '-')
    elif row['request_type'] == "Imprest":
        return row.get('imprest_no', '-')
    elif row['request_type'] == "Petty Cash":
        return row.get('imprest_no', '-')
    elif row['request_type'] == "Supplier Payment":
        return row.get('invoice_no', '-')
    elif row['request_type'] == "Surrender":
        return row.get('surrender_number', '-')
    elif row['request_type'] == "Refund Payment":
        return row.get('imprest_no', '-')
    elif row['request_type'] == "Direct Payment":
        return row.get('direct_payment_details', '-')[:20] if row.get('direct_payment_details') else '-'
    elif row['request_type'] == "Mileage Claim":
        return row.get('mileage_claim_details', '-')[:20] if row.get('mileage_claim_details') else '-'
    elif row['request_type'] == "Staff Training":
        return row.get('training_details', '-')[:20] if row.get('training_details') else '-'
    elif row['request_type'] == "Professional Body":
        return row.get('professional_body', '-')
    elif row['request_type'] == "Salary Payment":
        return f"{row.get('salary_month', '')} {row.get('salary_year', '')}" if row.get('salary_month') else '-'
    else:
        return '-'

def get_trend_indicator(current, previous):
    if previous == 0:
        return '<span class="trend-up">📈 New</span>'
    percent_change = ((current - previous) / previous) * 100
    if percent_change > 0:
        return f'<span class="trend-up">📈 +{percent_change:.1f}%</span>'
    elif percent_change < 0:
        return f'<span class="trend-down">📉 {percent_change:.1f}%</span>'
    else:
        return '<span>➡️ No change</span>'

# Login Screen
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #00843D 0%, #00529B 100%); border-radius: 20px;'>
                <h1 style='color: white; margin: 0;'>🎓 HELB Loans Board</h1>
                <h3 style='color: #FFB81C; margin: 0.5rem 0 0 0;'>Payment & Surrender Monitoring System</h3>
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

# Header
st.markdown("""
<div class='main-header'>
    <h1>🎓 HELB Payment & Surrender Monitoring System</h1>
    <p>Track, manage, and monitor all payment and surrender requests in real-time</p>
</div>
""", unsafe_allow_html=True)

# Filter Bar
st.markdown("<div class='filter-bar'>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
with col1:
    st.markdown("<div class='filter-label'>📅 FINANCIAL YEAR</div>", unsafe_allow_html=True)
    financial_years_list = ["All"] + get_financial_years()
    if not financial_years_list:
        financial_years_list = ["All", "2024/2025", "2025/2026", "2026/2027"]
    st.session_state.selected_financial_year = st.selectbox("", financial_years_list, key="fy_filter", label_visibility="collapsed")
with col2:
    st.markdown("<div class='filter-label'>📊 QUARTER</div>", unsafe_allow_html=True)
    quarters = ["All", "Q1 (Jul-Sep)", "Q2 (Oct-Dec)", "Q3 (Jan-Mar)", "Q4 (Apr-Jun)"]
    st.session_state.selected_quarter = st.selectbox("", quarters, key="quarter_filter", label_visibility="collapsed")
with col3:
    st.markdown("<div class='filter-label'>📆 MONTH</div>", unsafe_allow_html=True)
    months = ["All", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    st.session_state.selected_month = st.selectbox("", months, key="month_filter", label_visibility="collapsed")
with col4:
    st.markdown("&nbsp;", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 0.3rem 0;'>
        <h2 style='color: #00843D; margin: 0; font-size: 1.1rem;'>HELB</h2>
        <p style='color: #FFB81C; margin: 0; font-size: 0.6rem;'>Monitoring System</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class='user-info'>
            <strong>{st.session_state.full_name}</strong>
            <span>{st.session_state.user_role}</span>
            <span style='font-size: 0.6rem;'>{st.session_state.user_dept}</span>
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
        menu_title="",
        options=menu_options,
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#00843D", "font-size": "14px"},
            "nav-link": {"font-size": "12px", "text-align": "left", "margin": "0px", "padding": "6px 8px", "border-radius": "6px"},
            "nav-link-selected": {"background": "linear-gradient(135deg, #00843D 0%, #00529B 100%)", "color": "white"},
        }
    )
    
    st.markdown("---")
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
                st.markdown(f"<div class='log-submitted'>📝 **{timestamp}** - Submitted by {log['performed_by']}</div>", unsafe_allow_html=True)
            elif action == 'RECEIVED':
                st.markdown(f"<div class='log-received'>📥 **{timestamp}** - Received by {log['performed_by']}</div>", unsafe_allow_html=True)
            elif action in ['PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED']:
                st.markdown(f"<div class='log-stage'>⚙️ **{timestamp}** - {action.replace('_', ' ').title()} by {log['performed_by']}</div>", unsafe_allow_html=True)
            elif action == 'RETURNED':
                st.markdown(f"<div class='log-returned'>↩️ **{timestamp}** - Returned by {log['performed_by']}</div>", unsafe_allow_html=True)
            elif action in ['PAID', 'CLEARED']:
                st.markdown(f"<div class='log-paid'>✅ **{timestamp}** - {action} by {log['performed_by']}</div>", unsafe_allow_html=True)
    else:
        st.info("No logs available")

def display_approval_stages(request_id, main_category):
    st.markdown("---")
    st.markdown("**Approval Progress:**")
    
    if main_category == "Submit Payment Request":
        stages = ['Received', 'Prepared', 'Verified', 'Approved', 'Authorized', 'Paid']
    else:
        stages = ['Received', 'Verified', 'Approved', 'Authorized', 'Cleared']
    
    conn = sqlite3.connect("helb_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM requests WHERE id = ?", (request_id,))
    result = cursor.fetchone()
    conn.close()
    if not result:
        return
    
    status_map = {
        'RECEIVED_BY_FINANCE': 'Received',
        'PAYMENT_PREPARED': 'Prepared',
        'PAYMENT_VERIFIED': 'Verified',
        'PAYMENT_APPROVED': 'Approved',
        'PAYMENT_AUTHORIZED': 'Authorized',
        'PAID': 'Paid',
        'SURRENDER_VERIFIED': 'Verified',
        'SURRENDER_APPROVED': 'Approved',
        'SURRENDER_AUTHORIZED': 'Authorized',
        'CLEARED': 'Cleared'
    }
    current_stage = status_map.get(result[0], '')
    
    cols = st.columns(len(stages))
    for i, stage in enumerate(stages):
        with cols[i]:
            if current_stage == stage:
                st.markdown(f"<div class='stage-current'>⏳ {stage}</div>", unsafe_allow_html=True)
            elif current_stage and i < stages.index(current_stage):
                st.markdown(f"<div class='stage-completed'>✅ {stage}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='stage-pending'>⏸ {stage}</div>", unsafe_allow_html=True)


# ================================================================
# DEPARTMENT DASHBOARD - DETAILED
# ================================================================
if choice == "📊 Department Dashboard":
    st.markdown("<h2 style='color: #00843D; margin-bottom: 0.5rem; font-size: 1.3rem;'>📊 Department Dashboard</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #6B7280; margin-bottom: 1rem; font-size: 0.75rem;'>Viewing data for: <strong style='color: #00843D;'>{st.session_state.user_dept}</strong></p>", unsafe_allow_html=True)
    
    # Get data
    df = get_department_requests(st.session_state.user_dept)
    df_filtered = filter_by_filters(df, st.session_state.selected_financial_year, st.session_state.selected_quarter, st.session_state.selected_month)
    df_previous = filter_by_filters(df, "All", "All", "All")
    
    if df_filtered.empty:
        st.info("No requests found for your department with the selected filters.")
    else:
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💰 Financial Analytics", "📈 Performance", "📋 History"])
        
        with tab1:
            # Key Metrics
            total = len(df_filtered)
            total_prev = len(df_previous) if not df_previous.empty else 0
            
            pending = len(df_filtered[df_filtered['status'].isin(['SUBMITTED', 'RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED'])])
            pending_prev = len(df_previous[df_previous['status'].isin(['SUBMITTED', 'RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED'])]) if not df_previous.empty else 0
            
            completed = len(df_filtered[df_filtered['status'].isin(['PAID', 'CLEARED'])])
            completed_prev = len(df_previous[df_previous['status'].isin(['PAID', 'CLEARED'])]) if not df_previous.empty else 0
            
            returned = len(df_filtered[df_filtered['status'] == 'RETURNED'])
            amount = df_filtered['amount'].sum()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>{total}</h3>
                        <p>Total Requests</p>
                        <small>{get_trend_indicator(total, total_prev)}</small>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>{pending}</h3>
                        <p>Pending</p>
                        <small>{get_trend_indicator(pending, pending_prev)}</small>
                    </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>{completed}</h3>
                        <p>Completed</p>
                        <small>{get_trend_indicator(completed, completed_prev)}</small>
                    </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>KES {amount:,.0f}</h3>
                        <p>Total Amount</p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Charts
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📊 Request Type Distribution**")
                type_counts = df_filtered['request_type'].value_counts().reset_index()
                type_counts.columns = ['Type', 'Count']
                if not type_counts.empty:
                    fig = px.pie(type_counts, values='Count', names='Type', hole=0.3,
                                color_discrete_sequence=['#00843D', '#FFB81C', '#00529B', '#DC3545', '#00BCD4', '#9C27B0'])
                    fig.update_layout(height=350, margin=dict(l=10, r=10, t=20, b=10))
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("**💰 Amount by Request Type**")
                amount_by_type = df_filtered.groupby('request_type')['amount'].sum().reset_index()
                if not amount_by_type.empty:
                    fig = px.bar(amount_by_type, x='request_type', y='amount',
                                color='amount', color_continuous_scale=['#FFB81C', '#00843D'])
                    fig.update_layout(height=350, xaxis_title="", yaxis_title="Amount (KES)", margin=dict(l=10, r=10, t=20, b=10))
                    st.plotly_chart(fig, use_container_width=True)
            
            # Monthly Trend
            st.markdown("**📈 Monthly Request Trend**")
            df_filtered['month'] = pd.to_datetime(df_filtered['submission_date']).dt.strftime('%b %Y')
            monthly = df_filtered.groupby('month').agg({
                'request_number': 'count',
                'amount': 'sum'
            }).reset_index()
            monthly.columns = ['month', 'requests', 'amount']
            if not monthly.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(name='Request Count', x=monthly['month'], y=monthly['requests'], 
                                      marker_color='#FFB81C', yaxis='y'))
                fig.add_trace(go.Scatter(name='Amount (KES)', x=monthly['month'], y=monthly['amount'],
                                          marker_color='#00843D', yaxis='y2', mode='lines+markers'))
                fig.update_layout(
                    height=350,
                    xaxis_title="Month",
                    yaxis=dict(title="Request Count", side="left"),
                    yaxis2=dict(title="Amount (KES)", side="right", overlaying="y", showgrid=False),
                    margin=dict(l=10, r=10, t=20, b=10)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Insights
            st.markdown("**💡 Key Insights**")
            insights = []
            if returned > 0:
                insights.append(f"<div class='warning-box'>⚠️ You have <strong>{returned}</strong> returned request(s) that need your attention.</div>")
            if pending > 7:
                insights.append(f"<div class='alert-box'>🔔 <strong>{pending}</strong> request(s) have been pending for review. Please follow up.</div>")
            if completed > 0:
                completion_rate = (completed / total) * 100
                if completion_rate > 80:
                    insights.append(f"<div class='insight-box'>✅ Excellent! Your department has a <strong>{completion_rate:.1f}%</strong> completion rate.</div>")
                elif completion_rate < 50:
                    insights.append(f"<div class='warning-box'>📊 Your completion rate is <strong>{completion_rate:.1f}%</strong>. Consider reviewing pending requests.</div>")
            
            for insight in insights:
                st.markdown(insight, unsafe_allow_html=True)
        
        with tab2:
            st.markdown("**💰 Financial Overview**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Amount by Request Type**")
                amount_by_type = df_filtered.groupby('request_type')['amount'].sum().reset_index()
                if not amount_by_type.empty:
                    fig = px.pie(amount_by_type, values='amount', names='request_type', hole=0.3,
                                color_discrete_sequence=['#00843D', '#FFB81C', '#00529B', '#DC3545'])
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("**Average Amount by Request Type**")
                avg_by_type = df_filtered.groupby('request_type')['amount'].mean().reset_index()
                if not avg_by_type.empty:
                    fig = px.bar(avg_by_type, x='request_type', y='amount',
                                color='amount', color_continuous_scale=['#FFB81C', '#00843D'])
                    fig.update_layout(height=400, xaxis_title="", yaxis_title="Average Amount (KES)")
                    st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("**📅 Monthly Financial Impact**")
            if not monthly.empty:
                fig = px.line(monthly, x='month', y='amount', markers=True,
                             title="Total Amount Over Time",
                             color_discrete_sequence=['#00843D'])
                fig.update_layout(height=350, xaxis_title="Month", yaxis_title="Amount (KES)")
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.markdown("**⏱️ Processing Performance**")
            
            # Calculate processing times
            processing_times = []
            for _, row in df_filtered.iterrows():
                if row['status'] in ['PAID', 'CLEARED'] and row.get('payment_date'):
                    submitted = datetime.strptime(row['submission_date'], '%Y-%m-%d').date()
                    paid = datetime.strptime(row['payment_date'], '%Y-%m-%d').date()
                    days = working_days_between(submitted, paid)
                    processing_times.append({'request_type': row['request_type'], 'days': days})
            
            if processing_times:
                time_df = pd.DataFrame(processing_times)
                avg_by_type = time_df.groupby('request_type')['days'].mean().reset_index()
                fig = px.bar(avg_by_type, x='request_type', y='days',
                             title="Average Processing Time (Working Days)",
                             color='days', color_continuous_scale=['#00843D', '#FFB81C', '#DC3545'])
                fig.update_layout(height=400, xaxis_title="", yaxis_title="Working Days")
                st.plotly_chart(fig, use_container_width=True)
                
                overall_avg = time_df['days'].mean()
                st.markdown(f"<div class='insight-box'>📊 Overall average processing time: <strong>{overall_avg:.1f} working days</strong></div>", unsafe_allow_html=True)
            else:
                st.info("No completed requests to calculate processing times")
        
        with tab4:
            st.markdown("**📋 Complete Request History**")
            for _, row in df_filtered.head(50).iterrows():
                status_badge = '<span class="status-paid">✅ Paid</span>' if row['status'] == 'PAID' else '<span class="status-pending">⏳ Pending</span>'
                ref_number = get_reference_number(row)
                with st.expander(f"📄 {row['request_number']} - {row['request_type']} - Ref: {ref_number}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Amount:** KES {row['amount']:,.2f}")
                        st.write(f"**Submitted:** {row['submission_date']}")
                    with col2:
                        st.markdown(f"**Status:** {status_badge}", unsafe_allow_html=True)
                    if row.get('payment_description'):
                        st.write(f"**Description:** {row['payment_description']}")
                    display_approval_stages(row['id'], row['main_category'])
                    st.markdown("---")
                    display_transaction_logs(row['id'])


# ================================================================
# MANAGEMENT DASHBOARD - DETAILED
# ================================================================
elif choice == "📈 Management Dashboard":
    st.markdown("<h2 style='color: #00843D; margin-bottom: 0.5rem; font-size: 1.3rem;'>📈 Management Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B7280; margin-bottom: 1rem; font-size: 0.75rem;'><strong>Executive View</strong> - All departments, all requests</p>", unsafe_allow_html=True)
    
    # Get data
    df = get_requests()
    df_filtered = filter_by_filters(df, st.session_state.selected_financial_year, st.session_state.selected_quarter, st.session_state.selected_month)
    df_previous = filter_by_filters(df, "All", "All", "All")
    
    if df_filtered.empty:
        st.info("No data available with the selected filters.")
    else:
        # Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "💰 Financial Analytics", "🏢 Department Performance", "⏱️ SLA & Processing", "📋 All Requests"])
        
        with tab1:
            # Key Metrics
            total = len(df_filtered)
            total_prev = len(df_previous) if not df_previous.empty else 0
            
            pending = len(df_filtered[df_filtered['status'].isin(['SUBMITTED', 'RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED'])])
            pending_prev = len(df_previous[df_previous['status'].isin(['SUBMITTED', 'RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED'])]) if not df_previous.empty else 0
            
            completed = len(df_filtered[df_filtered['status'].isin(['PAID', 'CLEARED'])])
            completed_prev = len(df_previous[df_previous['status'].isin(['PAID', 'CLEARED'])]) if not df_previous.empty else 0
            
            amount = df_filtered['amount'].sum()
            amount_prev = df_previous['amount'].sum() if not df_previous.empty else 0
            
            returned = len(df_filtered[df_filtered['status'] == 'RETURNED'])
            returned_prev = len(df_previous[df_previous['status'] == 'RETURNED']) if not df_previous.empty else 0
            
            # Row 1 - Main KPIs
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>{total}</h3>
                        <p>Total Requests</p>
                        <small>{get_trend_indicator(total, total_prev)}</small>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>KES {amount:,.0f}</h3>
                        <p>Total Amount</p>
                        <small>{get_trend_indicator(amount, amount_prev)}</small>
                    </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>{completed}</h3>
                        <p>Completed</p>
                        <small>{get_trend_indicator(completed, completed_prev)}</small>
                    </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>{returned}</h3>
                        <p>Returned</p>
                        <small>{get_trend_indicator(returned, returned_prev)}</small>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Row 2 - Pipeline KPIs
            st.markdown("**📊 Workflow Pipeline**")
            col1, col2, col3 = st.columns(3)
            pending_receive = len(df_filtered[df_filtered['status'] == 'SUBMITTED'])
            pending_stages = len(df_filtered[df_filtered['status'].isin(['RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED'])])
            pending_payment = len(df_filtered[df_filtered['status'].isin(['PAYMENT_AUTHORIZED'])])
            
            with col1:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3 style='color: #DC3545;'>{pending_receive}</h3>
                        <p>Pending Receive</p>
                        <small>Awaiting Finance confirmation</small>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3 style='color: #FFB81C;'>{pending_stages}</h3>
                        <p>In Progress</p>
                        <small>At various approval stages</small>
                    </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3 style='color: #00843D;'>{pending_payment}</h3>
                        <p>Pending Payment</p>
                        <small>Authorized - Awaiting release</small>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Charts
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📊 Request Type Distribution**")
                type_counts = df_filtered['request_type'].value_counts().reset_index()
                type_counts.columns = ['Type', 'Count']
                if not type_counts.empty:
                    fig = px.pie(type_counts, values='Count', names='Type', hole=0.3,
                                color_discrete_sequence=['#00843D', '#FFB81C', '#00529B', '#DC3545', '#00BCD4', '#9C27B0', '#FF9800'])
                    fig.update_layout(height=400, margin=dict(l=10, r=10, t=20, b=10))
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("**💰 Amount by Request Type**")
                amount_by_type = df_filtered.groupby('request_type')['amount'].sum().reset_index()
                if not amount_by_type.empty:
                    fig = px.bar(amount_by_type, x='request_type', y='amount',
                                color='amount', color_continuous_scale=['#FFB81C', '#00843D'])
                    fig.update_layout(height=400, xaxis_title="", yaxis_title="Amount (KES)", margin=dict(l=10, r=10, t=20, b=10))
                    st.plotly_chart(fig, use_container_width=True)
            
            # Monthly Trends
            st.markdown("**📈 Monthly Trends**")
            df_filtered['month'] = pd.to_datetime(df_filtered['submission_date']).dt.strftime('%b %Y')
            monthly = df_filtered.groupby('month').agg({
                'request_number': 'count',
                'amount': 'sum'
            }).reset_index()
            monthly.columns = ['month', 'requests', 'amount']
            
            if not monthly.empty:
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.line(monthly, x='month', y='requests', markers=True,
                                 title="Request Volume Trend",
                                 color_discrete_sequence=['#00843D'])
                    fig.update_layout(height=350, xaxis_title="Month", yaxis_title="Number of Requests")
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    fig = px.line(monthly, x='month', y='amount', markers=True,
                                 title="Amount Trend",
                                 color_discrete_sequence=['#FFB81C'])
                    fig.update_layout(height=350, xaxis_title="Month", yaxis_title="Amount (KES)")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Executive Insights
            st.markdown("**💡 Executive Insights**")
            insights = []
            
            if pending_receive > 10:
                insights.append(f"<div class='alert-box'>🚨 <strong>{pending_receive}</strong> requests are pending Finance confirmation. Action required.</div>")
            if returned > 5:
                insights.append(f"<div class='warning-box'>⚠️ <strong>{returned}</strong> requests have been returned to departments for correction.</div>")
            if pending_payment > 5:
                insights.append(f"<div class='warning-box'>💰 <strong>{pending_payment}</strong> authorized requests are pending payment release.</div>")
            
            # Calculate SLA compliance
            completed_requests = df_filtered[df_filtered['status'].isin(['PAID', 'CLEARED'])]
            if not completed_requests.empty:
                sla_map = {'Student Payment': 3, 'Imprest': 5, 'Petty Cash': 3, 
                           'Supplier Payment': 7, 'Salary Payment': 5, 'Refund Payment': 10,
                           'Surrender': 4, 'Mileage Claim': 3, 'Staff Training': 5,
                           'Professional Body': 5, 'Direct Payment': 3}
                breaches = 0
                for _, row in completed_requests.iterrows():
                    if row['payment_date']:
                        submitted = datetime.strptime(row['submission_date'], '%Y-%m-%d').date()
                        paid = datetime.strptime(row['payment_date'], '%Y-%m-%d').date()
                        days = working_days_between(submitted, paid)
                        sla_days = sla_map.get(row['request_type'], 5)
                        if days > sla_days:
                            breaches += 1
                compliance_rate = ((len(completed_requests) - breaches) / len(completed_requests)) * 100
                if compliance_rate < 80:
                    insights.append(f"<div class='alert-box'>📉 SLA compliance rate is <strong>{compliance_rate:.1f}%</strong>. Below target of 90%.</div>")
                elif compliance_rate < 90:
                    insights.append(f"<div class='warning-box'>📊 SLA compliance rate is <strong>{compliance_rate:.1f}%</strong>. Room for improvement.</div>")
                else:
                    insights.append(f"<div class='insight-box'>✅ SLA compliance rate is <strong>{compliance_rate:.1f}%</strong>. Excellent performance!</div>")
            
            if not insights:
                insights.append("<div class='insight-box'>✅ All metrics are within acceptable ranges. Good performance!</div>")
            
            for insight in insights:
                st.markdown(insight, unsafe_allow_html=True)
        
        with tab2:
            st.markdown("**💰 Financial Analytics**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Amount by Request Type**")
                amount_by_type = df_filtered.groupby('request_type')['amount'].sum().reset_index()
                if not amount_by_type.empty:
                    fig = px.pie(amount_by_type, values='amount', names='request_type', hole=0.3,
                                color_discrete_sequence=['#00843D', '#FFB81C', '#00529B', '#DC3545', '#00BCD4'])
                    fig.update_layout(height=450)
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("**Amount by Department (Top 10)**")
                amount_by_dept = df_filtered.groupby('department_name')['amount'].sum().reset_index()
                amount_by_dept = amount_by_dept.sort_values('amount', ascending=True).tail(10)
                if not amount_by_dept.empty:
                    fig = px.bar(amount_by_dept, x='amount', y='department_name', orientation='h',
                                color='amount', color_continuous_scale=['#FFB81C', '#00843D'])
                    fig.update_layout(height=450, xaxis_title="Amount (KES)", yaxis_title="")
                    st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("**📅 Monthly Financial Impact**")
            if not monthly.empty:
                fig = px.area(monthly, x='month', y='amount',
                             title="Cumulative Amount Over Time",
                             color_discrete_sequence=['#00843D'])
                fig.update_layout(height=350, xaxis_title="Month", yaxis_title="Amount (KES)")
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.markdown("**🏢 Department Performance**")
            
            # Department summary
            dept_summary = df_filtered.groupby('department_name').agg({
                'request_number': 'count',
                'amount': 'sum'
            }).reset_index()
            dept_summary.columns = ['Department', 'Requests', 'Amount']
            
            # Add completion rates
            completion_rates = []
            avg_times = []
            for dept in dept_summary['Department']:
                dept_df = df_filtered[df_filtered['department_name'] == dept]
                completed = len(dept_df[dept_df['status'].isin(['PAID', 'CLEARED'])])
                total = len(dept_df)
                rate = (completed / total * 100) if total > 0 else 0
                completion_rates.append(round(rate, 1))
                
                # Average processing time
                times = []
                for _, row in dept_df.iterrows():
                    if row['status'] in ['PAID', 'CLEARED'] and row.get('payment_date'):
                        submitted = datetime.strptime(row['submission_date'], '%Y-%m-%d').date()
                        paid = datetime.strptime(row['payment_date'], '%Y-%m-%d').date()
                        days = working_days_between(submitted, paid)
                        times.append(days)
                avg_times.append(round(sum(times)/len(times), 1) if times else 0)
            
            dept_summary['Completion %'] = completion_rates
            dept_summary['Avg Days'] = avg_times
            dept_summary = dept_summary.sort_values('Completion %', ascending=False)
            
            st.dataframe(dept_summary, use_container_width=True, hide_index=True)
            
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(dept_summary, x='Department', y='Completion %',
                             title="Completion Rate by Department",
                             color='Completion %',
                             color_continuous_scale=['#DC3545', '#FFB81C', '#00843D'])
                fig.update_layout(height=450, xaxis_title="", yaxis_title="Completion Rate (%)")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(dept_summary, x='Department', y='Avg Days',
                             title="Average Processing Time by Department",
                             color='Avg Days',
                             color_continuous_scale=['#00843D', '#FFB81C', '#DC3545'])
                fig.update_layout(height=450, xaxis_title="", yaxis_title="Working Days")
                st.plotly_chart(fig, use_container_width=True)
            
            # Top Submitters
            st.markdown("**📝 Top Submitters**")
            top_submitters = df_filtered.groupby('submitted_by')['request_number'].count().reset_index()
            top_submitters.columns = ['User', 'Requests']
            top_submitters = top_submitters.sort_values('Requests', ascending=False).head(10)
            
            if not top_submitters.empty:
                fig = px.bar(top_submitters, x='User', y='Requests',
                             title="Top 10 Request Submitters",
                             color='Requests',
                             color_continuous_scale=['#FFB81C', '#00843D'])
                fig.update_layout(height=400, xaxis_title="", yaxis_title="Number of Requests")
                st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            st.markdown("**⏱️ SLA & Processing Analytics**")
            
            # Overall SLA Gauge
            completed_requests = df_filtered[df_filtered['status'].isin(['PAID', 'CLEARED'])]
            if not completed_requests.empty:
                sla_map = {'Student Payment': 3, 'Imprest': 5, 'Petty Cash': 3, 
                           'Supplier Payment': 7, 'Salary Payment': 5, 'Refund Payment': 10,
                           'Surrender': 4, 'Mileage Claim': 3, 'Staff Training': 5,
                           'Professional Body': 5, 'Direct Payment': 3}
                
                breaches = 0
                type_breaches = {}
                for _, row in completed_requests.iterrows():
                    if row['payment_date']:
                        submitted = datetime.strptime(row['submission_date'], '%Y-%m-%d').date()
                        paid = datetime.strptime(row['payment_date'], '%Y-%m-%d').date()
                        days = working_days_between(submitted, paid)
                        sla_days = sla_map.get(row['request_type'], 5)
                        if days > sla_days:
                            breaches += 1
                            req_type = row['request_type']
                            type_breaches[req_type] = type_breaches.get(req_type, 0) + 1
                
                compliance_rate = ((len(completed_requests) - breaches) / len(completed_requests)) * 100
                
                col1, col2 = st.columns(2)
                with col1:
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number+delta",
                        value = compliance_rate,
                        title = {'text': "SLA Compliance Rate", 'font': {'size': 16}},
                        delta = {'reference': 90, 'increasing': {'color': "#00843D"}, 'decreasing': {'color': "#DC3545"}},
                        gauge = {
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "#00843D"},
                            'steps': [
                                {'range': [0, 70], 'color': '#FFEBEE'},
                                {'range': [70, 90], 'color': '#FFF8E1'},
                                {'range': [90, 100], 'color': '#E8F5E9'}
                            ],
                            'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': 90}
                        }
                    ))
                    fig.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    if type_breaches:
                        breach_df = pd.DataFrame(list(type_breaches.items()), columns=['Request Type', 'Breaches'])
                        breach_df = breach_df.sort_values('Breaches', ascending=False)
                        fig = px.bar(breach_df, x='Request Type', y='Breaches',
                                     title="Breaches by Request Type",
                                     color='Breaches',
                                     color_continuous_scale=['#FFB81C', '#DC3545'])
                        fig.update_layout(height=350)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.markdown("<div class='insight-box'>✅ No SLA breaches detected. Great job!</div>", unsafe_allow_html=True)
            
            # Processing time by stage
            st.markdown("**⏱️ Average Processing Time by Stage**")
            stage_times = []
            for _, row in df_filtered.iterrows():
                if row['status'] in ['PAID', 'CLEARED'] and row.get('payment_date'):
                    submitted = datetime.strptime(row['submission_date'], '%Y-%m-%d').date()
                    paid = datetime.strptime(row['payment_date'], '%Y-%m-%d').date()
                    days = working_days_between(submitted, paid)
                    stage_times.append({'request_type': row['request_type'], 'days': days})
            
            if stage_times:
                stage_df = pd.DataFrame(stage_times)
                avg_by_type = stage_df.groupby('request_type')['days'].mean().reset_index()
                avg_by_type = avg_by_type.sort_values('days', ascending=False)
                fig = px.bar(avg_by_type, x='request_type', y='days',
                             title="Average Processing Time by Request Type (Working Days)",
                             color='days',
                             color_continuous_scale=['#00843D', '#FFB81C', '#DC3545'])
                fig.update_layout(height=400, xaxis_title="", yaxis_title="Working Days")
                st.plotly_chart(fig, use_container_width=True)
        
        with tab5:
            st.markdown("**📋 All Requests**")
            display_df = df_filtered.copy()
            display_df['Reference No.'] = display_df.apply(get_reference_number, axis=1)
            display_cols = ['request_number', 'request_type', 'department_name', 'Reference No.', 'amount', 'status', 'submission_date']
            if 'payment_date' in display_df.columns:
                display_cols.append('payment_date')
            st.dataframe(display_df[display_cols], use_container_width=True, hide_index=True)
            
            csv = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export to CSV", csv, f"helb_export_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")


# ================================================================
# CHECK PAYMENT STATUS
# ================================================================
elif choice == "🔍 Check Payment Status":
    st.markdown("<h2 style='color: #00843D; margin-bottom: 1rem; font-size: 1.3rem;'>🔍 Check Payment Status</h2>", unsafe_allow_html=True)
    
    search_term = st.text_input("Enter Batch No., Imprest No., Invoice No., or Surrender No.")
    
    if st.button("Search"):
        df = get_requests()
        if df.empty:
            st.error("No records found")
        else:
            mask = (
                df['batch_no'].str.contains(search_term, case=False, na=False) |
                df['imprest_no'].str.contains(search_term, case=False, na=False) |
                df['invoice_no'].str.contains(search_term, case=False, na=False) |
                df['surrender_number'].str.contains(search_term, case=False, na=False) |
                df['request_number'].str.contains(search_term, case=False, na=False)
            )
            results = df[mask]
            
            if not results.empty:
                for _, row in results.iterrows():
                    status_badge = '<span class="status-paid">✅ Paid</span>' if row['status'] == 'PAID' else '<span class="status-pending">⏳ Pending</span>'
                    ref_number = get_reference_number(row)
                    st.markdown(f"""
                    <div style='background:#F9FAFB; padding:0.75rem; border-radius:10px; margin-bottom:0.5rem; border-left:4px solid #00843D;'>
                        <strong>{row['request_number']}</strong><br>
                        Reference: {ref_number}<br>
                        Amount: KES {row['amount']:,.2f}<br>
                        Status: {status_badge}<br>
                        Submitted: {row['submission_date']}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.error("No records found")


# ================================================================
# NEW REQUEST (same as before - keep all existing functionality)
# ================================================================
elif choice == "📝 New Request":
    st.markdown("<h2 style='color: #00843D; margin-bottom: 1rem; font-size: 1.3rem;'>📝 Create New Request</h2>", unsafe_allow_html=True)
    
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
                products = get_products()
                product_list = products['name'].tolist() if not products.empty else ["Undergraduate", "TVET", "Jielimishe"]
                product_type = st.selectbox("Product Type", product_list)
                with st.form(key="student_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                    payment_description = st.text_area("Payment Description")
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    semester, payment_category = None, None
                    if product_type in ["Undergraduate", "TVET"]:
                        semesters = get_semesters()
                        semester = st.selectbox("Semester", semesters if semesters else ["Semester 1", "Semester 2"])
                        payment_category = st.selectbox("Payment Category", ["Tuition", "Upkeep"])
                    else:
                        payment_category = "Tuition"
                    batch_no = st.text_input("Batch No.")
                    if st.form_submit_button("Submit"):
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
                            st.success(f"✅ Request {request_number} submitted!")
                            st.balloons()
            
            # Imprest
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
                    if st.form_submit_button("Submit"):
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
                            st.success(f"✅ Request {request_number} submitted!")
                            st.balloons()
            
            # Petty Cash
            elif main_category == "Submit Payment Request" and selected_type == "Petty Cash":
                with st.form(key="petty_form"):
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
                    if st.form_submit_button("Submit"):
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
                            st.success(f"✅ Request {request_number} submitted!")
                            st.balloons()
            
            # Direct Payment
            elif main_category == "Submit Payment Request" and selected_type == "Direct Payment":
                with st.form(key="direct_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    direct_payment_details = st.text_area("Payment Details (Payee, Purpose)")
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    payment_description = st.text_area("Additional Notes")
                    if st.form_submit_button("Submit"):
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
                            st.success(f"✅ Request {request_number} submitted!")
                            st.balloons()
            
            # Supplier Payment
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
                    if st.form_submit_button("Submit"):
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
                            st.success(f"✅ Request {request_number} submitted!")
                            st.balloons()
            
            # Salary Payment
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
                    salary_year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.now().year)
                    if st.form_submit_button("Submit"):
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
                            st.success(f"✅ Request {request_number} submitted!")
                            st.balloons()
            
            # Refund Payment
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
                    if st.form_submit_button("Submit"):
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
                            st.success(f"✅ Request {request_number} submitted!")
                            st.balloons()
            
            # Mileage Claim
            elif main_category == "Submit Payment Request" and selected_type == "Mileage Claim":
                with st.form(key="mileage_form"):
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
                    if st.form_submit_button("Submit"):
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
                            st.success(f"✅ Request {request_number} submitted!")
                            st.balloons()
            
            # Staff Training
            elif main_category == "Submit Payment Request" and selected_type == "Staff Training":
                with st.form(key="training_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    training_details = st.text_area("Training Details (Course, Institution, Duration)")
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    payment_description = st.text_area("Additional Notes")
                    if st.form_submit_button("Submit"):
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
                            st.success(f"✅ Request {request_number} submitted!")
                            st.balloons()
            
            # Professional Body
            elif main_category == "Submit Payment Request" and selected_type == "Professional Body":
                with st.form(key="professional_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    professional_body = st.text_input("Professional Body Name")
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    payment_description = st.text_area("Additional Notes")
                    if st.form_submit_button("Submit"):
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
                            st.success(f"✅ Request {request_number} submitted!")
                            st.balloons()
            
            # Surrender
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
                    if st.form_submit_button("Submit"):
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
                            st.success(f"✅ Request {request_number} submitted!")
                            st.balloons()


# ================================================================
# MY REQUESTS
# ================================================================
elif choice == "📋 My Requests":
    st.markdown("<h2 style='color: #00843D; margin-bottom: 1rem; font-size: 1.3rem;'>📋 My Requests</h2>", unsafe_allow_html=True)
    df = get_requests()
    if df.empty:
        st.info("No requests found.")
    else:
        user_requests = df[df['submitted_by'] == st.session_state.username]
        if user_requests.empty:
            st.info("You haven't submitted any requests yet.")
        else:
            for _, row in user_requests.iterrows():
                status_badge = '<span class="status-paid">✅ Paid</span>' if row['status'] == 'PAID' else '<span class="status-pending">⏳ Pending</span>'
                ref_number = get_reference_number(row)
                with st.expander(f"📄 {row['request_number']} - {row['request_type']} - Ref: {ref_number}"):
                    st.write(f"**Amount:** KES {row['amount']:,.2f}")
                    st.markdown(f"**Status:** {status_badge}", unsafe_allow_html=True)
                    if row.get('payment_description'):
                        st.write(f"**Description:** {row['payment_description']}")
                    if row['status'] == 'RETURNED' and row.get('return_reason'):
                        st.error(f"**Return Reason:** {row['return_reason']}")
                    display_approval_stages(row['id'], row['main_category'])
                    st.markdown("---")
                    display_transaction_logs(row['id'])


# ================================================================
# RETURNED REQUESTS
# ================================================================
elif choice == "↩️ Returned Requests":
    st.markdown("<h2 style='color: #00843D; margin-bottom: 1rem; font-size: 1.3rem;'>↩️ Returned Requests</h2>", unsafe_allow_html=True)
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
# APPROVAL QUEUE
# ================================================================
elif choice == "✅ Approval Queue":
    if st.session_state.user_role in ["FINANCE", "ADMIN"] or st.session_state.is_finance:
        st.markdown("<h2 style='color: #00843D; margin-bottom: 1rem; font-size: 1.3rem;'>✅ Approval Queue</h2>", unsafe_allow_html=True)
        
        pending_confirmation = get_pending_confirmation_count()
        if pending_confirmation > 0:
            st.info(f"📋 {pending_confirmation} request(s) pending confirmation")
        
        df = get_requests()
        pending = df[df['status'].isin(['SUBMITTED', 'RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED'])]
        
        if pending.empty:
            st.info("No pending requests.")
        else:
            for idx, (_, req) in enumerate(pending.iterrows()):
                with st.expander(f"📄 {req['request_number']} - {req['request_type']} - {req['department_name']}"):
                    st.write(f"**Amount:** KES {req['amount']:,.2f}")
                    st.write(f"**Submitted:** {req['submission_date']}")
                    
                    if req['status'] == 'SUBMITTED':
                        col1, col2 = st.columns(2)
                        with col1:
                            checklist_approvals = st.checkbox("✓ Approvals", key=f"app_{idx}")
                            checklist_documents = st.checkbox("✓ Documents", key=f"doc_{idx}")
                        with col2:
                            pwd = st.text_input("Finance Password", type="password", key=f"pwd_{idx}")
                            if st.button(f"Confirm", key=f"confirm_{idx}"):
                                if checklist_approvals and checklist_documents:
                                    if pwd and verify_finance_password(pwd):
                                        update_request_status(req['id'], 'RECEIVED_BY_FINANCE', performed_by=st.session_state.username)
                                        st.success(f"Confirmed!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Check both boxes!")
                        
                        reason = st.text_input("Return Reason", key=f"ret_{idx}")
                        if st.button(f"Return", key=f"return_{idx}"):
                            if reason:
                                if pwd and verify_finance_password(pwd):
                                    update_request_status(req['id'], 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                    st.warning(f"Returned!")
                                    st.rerun()
                                else:
                                    st.error("Incorrect password!")
                    
                    elif req['status'] == 'RECEIVED_BY_FINANCE':
                        pwd = st.text_input("Finance Password", type="password", key=f"pwd_prep_{idx}")
                        if st.button(f"Prepare", key=f"prepare_{idx}"):
                            if pwd and verify_finance_password(pwd):
                                update_request_status(req['id'], 'PAYMENT_PREPARED', performed_by=st.session_state.username)
                                st.success(f"Prepared!")
                                st.rerun()
                            else:
                                st.error("Incorrect password!")
                    
                    elif req['status'] == 'PAYMENT_PREPARED':
                        pwd = st.text_input("Finance Password", type="password", key=f"pwd_ver_{idx}")
                        if st.button(f"Verify", key=f"verify_{idx}"):
                            if pwd and verify_finance_password(pwd):
                                update_request_status(req['id'], 'PAYMENT_VERIFIED', performed_by=st.session_state.username)
                                st.success(f"Verified!")
                                st.rerun()
                            else:
                                st.error("Incorrect password!")
                    
                    elif req['status'] == 'PAYMENT_VERIFIED':
                        pwd = st.text_input("Finance Password", type="password", key=f"pwd_app_{idx}")
                        if st.button(f"Approve", key=f"approve_{idx}"):
                            if pwd and verify_finance_password(pwd):
                                update_request_status(req['id'], 'PAYMENT_APPROVED', performed_by=st.session_state.username)
                                st.success(f"Approved!")
                                st.rerun()
                            else:
                                st.error("Incorrect password!")
                    
                    elif req['status'] == 'PAYMENT_APPROVED':
                        pwd = st.text_input("Finance Password", type="password", key=f"pwd_auth_{idx}")
                        if st.button(f"Authorize", key=f"authorize_{idx}"):
                            if pwd and verify_finance_password(pwd):
                                update_request_status(req['id'], 'PAYMENT_AUTHORIZED', performed_by=st.session_state.username)
                                st.success(f"Authorized!")
                                st.rerun()
                            else:
                                st.error("Incorrect password!")
                    
                    elif req['status'] == 'PAYMENT_AUTHORIZED':
                        payment_ref = st.text_input("Payment Reference", key=f"ref_{idx}")
                        pwd = st.text_input("Finance Password", type="password", key=f"pwd_pay_{idx}")
                        if st.button(f"Mark Paid", key=f"paid_{idx}"):
                            if payment_ref:
                                if pwd and verify_finance_password(pwd):
                                    update_request_status(req['id'], 'PAID', performed_by=st.session_state.username)
                                    update_payment_details(req['id'], payment_ref)
                                    st.balloons()
                                    st.success(f"Paid!")
                                    st.rerun()
                                else:
                                    st.error("Incorrect password!")
                            else:
                                st.error("Enter reference!")
    else:
        st.error("Access denied.")


# ================================================================
# REPORTS
# ================================================================
elif choice == "📑 Reports":
    st.markdown("<h2 style='color: #00843D; margin-bottom: 1rem; font-size: 1.3rem;'>📑 Reports</h2>", unsafe_allow_html=True)
    
    df = get_reports_data(st.session_state.user_role, st.session_state.user_dept)
    df = filter_by_filters(df, st.session_state.selected_financial_year, st.session_state.selected_quarter, st.session_state.selected_month)
    
    if df.empty:
        st.info("No data available")
    else:
        display_df = pd.DataFrame()
        display_df['Request No.'] = df['request_number']
        display_df['Type'] = df['request_type']
        display_df['Department'] = df['department_name']
        display_df['Reference No.'] = df.apply(get_reference_number, axis=1)
        display_df['Amount'] = df['amount'].apply(lambda x: f"KES {x:,.2f}")
        display_df['Status'] = df['status']
        display_df['Submitted'] = df['submission_date']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export to CSV", csv, f"helb_export_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")


# ================================================================
# ADMIN PANEL
# ================================================================
elif choice == "⚙️ Admin Panel" and st.session_state.user_role == "ADMIN":
    st.markdown("<h2 style='color: #00843D; margin-bottom: 1rem; font-size: 1.3rem;'>⚙️ Admin Panel</h2>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["👥 Users", "🏢 Departments", "📦 Products", "💰 Funders", "📅 Financial Years", "🔐 Finance Settings"])
    
    with tab1:
        st.subheader("User Management")
        users_df = get_all_users()
        st.dataframe(users_df, use_container_width=True, hide_index=True)
        with st.expander("➕ Add New User"):
            with st.form("add_user_form"):
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
        st.dataframe(get_departments(), use_container_width=True)
        with st.expander("➕ Add New Department"):
            with st.form("add_dept_form"):
                dept_name = st.text_input("Department Name")
                if st.form_submit_button("Create"):
                    perms = [True, True, False, False, True, False, False, False, False]
                    create_department(dept_name, perms)
                    st.rerun()
    
    with tab3:
        st.subheader("Product Management")
        st.dataframe(get_products(), use_container_width=True)
        with st.expander("➕ Add New Product"):
            with st.form("add_product_form"):
                name = st.text_input("Product Name")
                if st.form_submit_button("Add"):
                    add_product(name, "LOAN", True, True)
                    st.rerun()
    
    with tab4:
        st.subheader("Funder Management")
        for f in get_funders():
            st.write(f"• {f}")
        with st.expander("➕ Add New Funder"):
            with st.form("add_funder_form"):
                name = st.text_input("Funder Name")
                if st.form_submit_button("Add"):
                    add_funder(name)
                    st.rerun()
    
    with tab5:
        st.subheader("Financial Year Management")
        for y in get_financial_years():
            st.write(f"• {y}")
        with st.expander("➕ Add New Financial Year"):
            with st.form("add_fy_form"):
                year = st.text_input("Financial Year (e.g., 2027/2028)")
                if st.form_submit_button("Add"):
                    add_financial_year(year)
                    st.rerun()
        
        st.markdown("---")
        st.subheader("Semester Management")
        for s in get_semesters():
            st.write(f"• {s}")
        with st.expander("➕ Add New Semester"):
            with st.form("add_semester_form"):
                sem = st.text_input("Semester Name")
                if st.form_submit_button("Add"):
                    add_semester(sem)
                    st.rerun()
    
    with tab6:
        st.subheader("Finance Password Settings")
        st.text_input("Current Password", value="••••••••", disabled=True)
        with st.form("update_pwd_form"):
            new_pwd = st.text_input("New Password", type="password")
            confirm_pwd = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Update"):
                if new_pwd and len(new_pwd) >= 4 and new_pwd == confirm_pwd:
                    update_finance_password(new_pwd)
                    st.success("Password updated!")
                    st.rerun()
                else:
                    st.error("Invalid password!")


# ================================================================
# CHANGE PASSWORD
# ================================================================
elif choice == "🔐 Change Password":
    st.markdown("<h2 style='color: #00843D; margin-bottom: 1rem; font-size: 1.3rem;'>🔐 Change Password</h2>", unsafe_allow_html=True)
    with st.form("change_pwd_form"):
        current = st.text_input("Current Password", type="password")
        new = st.text_input("New Password", type="password")
        confirm = st.text_input("Confirm New Password", type="password")
        if st.form_submit_button("Update"):
            if new == confirm and len(new) >= 4:
                user = authenticate_user(st.session_state.username, current)
                if user:
                    update_user_password(st.session_state.username, new)
                    st.success("Password updated!")
                else:
                    st.error("Current password incorrect")
            else:
                st.error("Passwords do not match or too short")


# Footer
st.markdown("""
<div class='main-footer'>
    <p>© 2026 Higher Education Loans Board (HELB) | Payment & Surrender Monitoring System v3.0</p>
</div>
""", unsafe_allow_html=True)
