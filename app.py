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

# Custom CSS for Professional Design
st.markdown("""
<style>
    /* ============================================
       IMPORT FONTS
    ============================================ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* ============================================
       ROOT VARIABLES
    ============================================ */
    :root {
        --helb-green: #00843D;
        --helb-green-light: #00B347;
        --helb-green-dark: #006030;
        --helb-gold: #FFB81C;
        --helb-gold-light: #FFCD4D;
        --helb-blue: #00529B;
        --helb-blue-light: #0073D4;
        --helb-red: #DC3545;
        --gray-50: #F9FAFB;
        --gray-100: #F3F4F6;
        --gray-200: #E5E7EB;
        --gray-300: #D1D5DB;
        --gray-400: #9CA3AF;
        --gray-500: #6B7280;
        --gray-600: #4B5563;
        --gray-700: #374151;
        --gray-800: #1F2937;
        --gray-900: #111827;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --radius-sm: 0.375rem;
        --radius-md: 0.5rem;
        --radius-lg: 0.75rem;
        --radius-xl: 1rem;
    }
    
    /* ============================================
       GLOBAL STYLES
    ============================================ */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Fix for scroll - make content fit properly */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Sticky Header */
    .stApp header {
        background: linear-gradient(135deg, #00843D 0%, #00529B 100%);
        backdrop-filter: blur(0px);
        box-shadow: var(--shadow-md);
    }
    
    /* Main Header Banner */
    .main-header {
        background: linear-gradient(135deg, #00843D 0%, #00529B 100%);
        padding: 1rem 2rem;
        border-radius: var(--radius-lg);
        margin-bottom: 1rem;
        box-shadow: var(--shadow-md);
        position: sticky;
        top: 0;
        z-index: 999;
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        margin: 0.25rem 0 0 0;
        font-size: 0.8rem;
    }
    
    /* Footer */
    .main-footer {
        background: var(--gray-800);
        color: var(--gray-400);
        padding: 1rem 2rem;
        margin-top: 2rem;
        border-radius: var(--radius-lg);
        text-align: center;
        font-size: 0.75rem;
    }
    
    /* ============================================
       BUTTON STYLES
    ============================================ */
    .stButton > button {
        background: linear-gradient(135deg, var(--helb-green) 0%, var(--helb-green-dark) 100%);
        color: white;
        border: none;
        border-radius: var(--radius-md);
        padding: 0.5rem 1rem;
        font-weight: 600;
        font-size: 0.8rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }
    
    /* ============================================
       METRIC CARDS - UNIFORM SIZE
    ============================================ */
    .metric-card {
        background: white;
        padding: 0.75rem;
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-sm);
        text-align: center;
        transition: all 0.3s ease;
        border: 1px solid var(--gray-200);
        height: 100%;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
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
        line-height: 1.2;
    }
    
    .metric-card p {
        margin: 0.25rem 0 0 0;
        color: var(--gray-500);
        font-size: 0.7rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-card small {
        font-size: 0.65rem;
        color: var(--gray-400);
    }
    
    /* ============================================
       FILTER SECTION - CLEAN AND NEAT
    ============================================ */
    .filter-section {
        background: var(--gray-50);
        padding: 0.75rem;
        border-radius: var(--radius-lg);
        margin-bottom: 1rem;
        border: 1px solid var(--gray-200);
    }
    
    .filter-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--gray-600);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.25rem;
    }
    
    /* ============================================
       SIDEBAR STYLES
    ============================================ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--gray-50) 0%, white 100%);
        border-right: 1px solid var(--gray-200);
        padding-top: 1rem;
    }
    
    [data-testid="stSidebar"] .user-info {
        background: linear-gradient(135deg, var(--helb-green) 0%, var(--helb-blue) 100%);
        padding: 0.75rem;
        border-radius: var(--radius-lg);
        margin: 0.5rem 0;
        color: white;
        text-align: center;
    }
    
    [data-testid="stSidebar"] .user-info strong {
        font-size: 0.9rem;
        display: block;
    }
    
    [data-testid="stSidebar"] .user-info span {
        font-size: 0.7rem;
        opacity: 0.9;
    }
    
    /* ============================================
       TABS STYLES
    ============================================ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
        background: var(--gray-100);
        padding: 0.25rem;
        border-radius: var(--radius-xl);
        margin-bottom: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-lg);
        padding: 0.4rem 1rem;
        font-weight: 500;
        font-size: 0.8rem;
        color: var(--gray-600);
        transition: all 0.3s ease;
        white-space: nowrap;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--helb-green) 0%, var(--helb-blue) 100%);
        color: white !important;
    }
    
    /* ============================================
       EXPANDER STYLES
    ============================================ */
    .streamlit-expanderHeader {
        background: var(--gray-50);
        border-radius: var(--radius-md);
        font-weight: 500;
        font-size: 0.85rem;
        border: 1px solid var(--gray-200);
    }
    
    /* ============================================
       FORM STYLES
    ============================================ */
    .stForm {
        background: white;
        padding: 1rem;
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--gray-200);
    }
    
    /* ============================================
       DATA TABLE STYLES
    ============================================ */
    .dataframe {
        font-size: 0.8rem;
    }
    
    .dataframe thead tr th {
        background: linear-gradient(135deg, var(--helb-green) 0%, var(--helb-blue) 100%);
        color: white;
        font-weight: 600;
        padding: 0.5rem;
        font-size: 0.75rem;
    }
    
    /* ============================================
       RESPONSIVE GRID
    ============================================ */
    @media (max-width: 1200px) {
        .metric-card h3 {
            font-size: 1.2rem;
        }
        .metric-card p {
            font-size: 0.6rem;
        }
    }
    
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.1rem;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.3rem 0.6rem;
            font-size: 0.7rem;
        }
    }
    
    /* ============================================
       STATUS BADGES
    ============================================ */
    .status-paid, .status-cleared, .status-pending, .status-confirmed {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    
    .status-paid, .status-cleared {
        background: #E8F5E9;
        color: #00843D;
    }
    
    .status-pending {
        background: #FFEBEE;
        color: #DC3545;
    }
    
    .status-confirmed {
        background: #E0F7FA;
        color: #00BCD4;
    }
    
    /* ============================================
       LOG ENTRY STYLES
    ============================================ */
    .log-entry {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: var(--radius-md);
        font-size: 0.75rem;
    }
    
    .log-submitted { background: #E3F2FD; border-left: 3px solid #2196F3; }
    .log-received { background: #E8F5E9; border-left: 3px solid #4CAF50; }
    .log-returned { background: #FFEBEE; border-left: 3px solid #F44336; }
    .log-paid { background: #E8F5E9; border-left: 3px solid #00843D; }
    
    /* ============================================
       STAGE STYLES
    ============================================ */
    .stage-completed, .stage-pending, .stage-current {
        padding: 0.4rem;
        border-radius: var(--radius-md);
        margin: 0.25rem 0;
        text-align: center;
        font-size: 0.7rem;
    }
    
    .stage-completed {
        background: #E8F5E9;
        color: #00843D;
    }
    
    .stage-pending {
        background: #FFF8E1;
        color: #FFB81C;
    }
    
    .stage-current {
        background: linear-gradient(135deg, #00843D 0%, #00529B 100%);
        color: white;
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
if 'selected_financial_year' not in st.session_state:
    st.session_state.selected_financial_year = "All"
if 'selected_quarter' not in st.session_state:
    st.session_state.selected_quarter = "All"
if 'selected_month' not in st.session_state:
    st.session_state.selected_month = "All"

# Helper function to filter by financial year, quarter, month
def filter_by_filters(df, financial_year, quarter, month):
    if df.empty or 'submission_date' not in df.columns:
        return df
    
    df['submission_date_dt'] = pd.to_datetime(df['submission_date'])
    
    # Filter by Financial Year (July to June)
    if financial_year and financial_year != "All":
        year_start = int(financial_year.split('/')[0])
        year_end = int(financial_year.split('/')[1])
        start_date = date(year_start, 7, 1)
        end_date = date(year_end, 6, 30)
        df = df[(df['submission_date_dt'].dt.date >= start_date) & (df['submission_date_dt'].dt.date <= end_date)]
    
    # Filter by Quarter
    if quarter and quarter != "All":
        if quarter == "Q1 (Jul-Sep)":
            df = df[df['submission_date_dt'].dt.month.isin([7, 8, 9])]
        elif quarter == "Q2 (Oct-Dec)":
            df = df[df['submission_date_dt'].dt.month.isin([10, 11, 12])]
        elif quarter == "Q3 (Jan-Mar)":
            df = df[df['submission_date_dt'].dt.month.isin([1, 2, 3])]
        elif quarter == "Q4 (Apr-Jun)":
            df = df[df['submission_date_dt'].dt.month.isin([4, 5, 6])]
    
    # Filter by Month
    if month and month != "All":
        month_num = {
            "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
            "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
        }.get(month, 0)
        if month_num:
            df = df[df['submission_date_dt'].dt.month == month_num]
    
    return df

# Helper function for trend indicator
def get_trend_indicator(current, previous):
    if previous == 0:
        return '<span style="color: #00843D; font-size: 0.65rem;">📈 New</span>'
    percent_change = ((current - previous) / previous) * 100
    if percent_change > 0:
        return f'<span style="color: #00843D; font-size: 0.65rem;">📈 +{percent_change:.1f}%</span>'
    elif percent_change < 0:
        return f'<span style="color: #DC3545; font-size: 0.65rem;">📉 {percent_change:.1f}%</span>'
    else:
        return '<span style="color: #6B7280; font-size: 0.65rem;">➡️ No change</span>'

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

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 0.5rem 0;'>
        <h2 style='color: #00843D; margin: 0; font-size: 1.3rem;'>HELB</h2>
        <p style='color: #FFB81C; margin: 0; font-size: 0.7rem;'>Monitoring System</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class='user-info'>
            <strong>{st.session_state.full_name}</strong>
            <span>{st.session_state.user_role}</span>
            <span style='font-size: 0.65rem;'>{st.session_state.user_dept}</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Filter Section
    st.markdown("<div class='filter-section'>", unsafe_allow_html=True)
    st.markdown("<div class='filter-label'>📅 FILTERS</div>", unsafe_allow_html=True)
    
    # Financial Year
    financial_years_list = ["All"] + get_financial_years()
    if not financial_years_list:
        financial_years_list = ["All", "2024/2025", "2025/2026", "2026/2027"]
    st.session_state.selected_financial_year = st.selectbox("Financial Year", financial_years_list, key="fy_filter")
    
    # Quarters
    quarters = ["All", "Q1 (Jul-Sep)", "Q2 (Oct-Dec)", "Q3 (Jan-Mar)", "Q4 (Apr-Jun)"]
    st.session_state.selected_quarter = st.selectbox("Quarter", quarters, key="quarter_filter")
    
    # Months
    months = ["All", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    st.session_state.selected_month = st.selectbox("Month", months, key="month_filter")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Menu
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
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#00843D", "font-size": "16px"},
            "nav-link": {"font-size": "13px", "text-align": "left", "margin": "0px", "padding": "8px", "border-radius": "8px"},
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
                st.markdown(f"<div class='log-entry log-submitted'>📝 **{timestamp}** - Submitted by {log['performed_by']}</div>", unsafe_allow_html=True)
            elif action == 'RECEIVED':
                st.markdown(f"<div class='log-entry log-received'>📥 **{timestamp}** - Received by {log['performed_by']}</div>", unsafe_allow_html=True)
            elif action in ['PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED']:
                st.markdown(f"<div class='log-entry log-received'>⚙️ **{timestamp}** - {action.replace('_', ' ').title()} by {log['performed_by']}</div>", unsafe_allow_html=True)
            elif action == 'RETURNED':
                st.markdown(f"<div class='log-entry log-returned'>↩️ **{timestamp}** - Returned by {log['performed_by']}</div>", unsafe_allow_html=True)
            elif action in ['PAID', 'CLEARED']:
                st.markdown(f"<div class='log-entry log-paid'>✅ **{timestamp}** - {action} by {log['performed_by']}</div>", unsafe_allow_html=True)
    else:
        st.info("No transaction logs available")

def display_approval_stages(request_id, main_category):
    st.markdown("---")
    st.markdown("**Approval Progress:**")
    if main_category == "Submit Payment Request":
        stages = ['Received', 'Prepared', 'Verified', 'Approved', 'Authorized', 'Paid']
    else:
        stages = ['Received', 'Verified', 'Approved', 'Authorized', 'Cleared']
    
    # Get current status
    conn = sqlite3.connect("helb_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM requests WHERE id = ?", (request_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return
    
    current = result[0]
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
    current_stage = status_map.get(current, '')
    
    cols = st.columns(len(stages))
    for i, stage in enumerate(stages):
        with cols[i]:
            if current_stage == stage:
                st.markdown(f"<div class='stage-current' style='text-align:center'>⏳ {stage}</div>", unsafe_allow_html=True)
            elif i < stages.index(current_stage) if current_stage in stages else False:
                st.markdown(f"<div class='stage-completed' style='text-align:center'>✅ {stage}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='stage-pending' style='text-align:center'>⏸ {stage}</div>", unsafe_allow_html=True)


# ================================================================
# DEPARTMENT DASHBOARD
# ================================================================
if choice == "📊 Department Dashboard":
    st.markdown("<h2 style='color: #00843D; margin-bottom: 0.5rem;'>📊 Department Dashboard</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #6B7280; margin-bottom: 1rem;'>Viewing data for: <strong style='color: #00843D;'>{st.session_state.user_dept}</strong></p>", unsafe_allow_html=True)
    
    # Get department data
    df = get_department_requests(st.session_state.user_dept)
    df = filter_by_filters(df, st.session_state.selected_financial_year, st.session_state.selected_quarter, st.session_state.selected_month)
    
    if df.empty:
        st.info("No requests found for your department with the selected filters.")
    else:
        # Create tabs
        tab1, tab2, tab3 = st.tabs(["📊 Overview", "📋 Recent Requests", "📜 History"])
        
        with tab1:
            # Previous period for trends
            df_previous = filter_by_filters(get_department_requests(st.session_state.user_dept), "All", "All", "All")
            
            total_current = len(df)
            pending_current = len(df[df['status'].isin(['SUBMITTED', 'RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED'])])
            completed_current = len(df[df['status'].isin(['PAID', 'CLEARED'])])
            amount_current = df['amount'].sum()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>{total_current}</h3>
                        <p>Total Requests</p>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>{pending_current}</h3>
                        <p>Pending</p>
                    </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>{completed_current}</h3>
                        <p>Completed</p>
                    </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>KES {amount_current:,.0f}</h3>
                        <p>Total Amount</p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Request Type Distribution**")
                type_counts = df['request_type'].value_counts().reset_index()
                type_counts.columns = ['Type', 'Count']
                if not type_counts.empty:
                    fig = px.pie(type_counts, values='Count', names='Type', hole=0.3,
                                color_discrete_sequence=['#00843D', '#FFB81C', '#00529B', '#DC3545'])
                    fig.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("**Amount by Request Type**")
                amount_by_type = df.groupby('request_type')['amount'].sum().reset_index()
                if not amount_by_type.empty:
                    fig = px.bar(amount_by_type, x='request_type', y='amount',
                                color='amount', color_continuous_scale=['#FFB81C', '#00843D'])
                    fig.update_layout(height=350, xaxis_title="", yaxis_title="Amount (KES)", margin=dict(l=20, r=20, t=30, b=20))
                    st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            for _, row in df.head(15).iterrows():
                if row['status'] == 'PAID':
                    status_badge = '<span class="status-paid">✅ Paid</span>'
                elif row['status'] == 'CLEARED':
                    status_badge = '<span class="status-cleared">✅ Cleared</span>'
                elif row['status'] in ['PAYMENT_AUTHORIZED']:
                    status_badge = '<span class="status-confirmed">📌 Authorized</span>'
                elif row['status'] in ['PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED']:
                    status_badge = '<span class="status-confirmed">⚙️ In Progress</span>'
                elif row['status'] == 'RECEIVED_BY_FINANCE':
                    status_badge = '<span class="status-confirmed">📥 Received</span>'
                elif row['status'] == 'RETURNED':
                    status_badge = f'<span class="status-pending">↩️ Returned</span>'
                else:
                    status_badge = f'<span class="status-pending">⏳ Pending</span>'
                
                with st.expander(f"📄 {row['request_number']} - {row['request_type']} - {row['submission_date']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Amount:** KES {row['amount']:,.2f}")
                        st.write(f"**Department:** {row['department_name']}")
                    with col2:
                        st.markdown(f"**Status:** {status_badge}", unsafe_allow_html=True)
                    if row.get('payment_description'):
                        st.write(f"**Description:** {row['payment_description']}")
                    display_approval_stages(row['id'], row['main_category'])
        
        with tab3:
            for _, row in df.head(30).iterrows():
                with st.expander(f"📄 {row['request_number']} - {row['request_type']}"):
                    st.write(f"**Amount:** KES {row['amount']:,.2f}")
                    st.write(f"**Submitted:** {row['submission_date']}")
                    st.markdown("---")
                    display_transaction_logs(row['id'])


# ================================================================
# MANAGEMENT DASHBOARD
# ================================================================
elif choice == "📈 Management Dashboard":
    st.markdown("<h2 style='color: #00843D; margin-bottom: 0.5rem;'>📈 Management Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B7280; margin-bottom: 1rem;'><strong>Executive View</strong> - All departments</p>", unsafe_allow_html=True)
    
    # Get all data
    df = get_requests()
    df = filter_by_filters(df, st.session_state.selected_financial_year, st.session_state.selected_quarter, st.session_state.selected_month)
    
    if df.empty:
        st.info("No data available with the selected filters.")
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Department Performance", "💰 Financial Analytics", "📋 All Requests"])
        
        with tab1:
            total_current = len(df)
            pending_current = len(df[df['status'].isin(['SUBMITTED', 'RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED'])])
            completed_current = len(df[df['status'].isin(['PAID', 'CLEARED'])])
            amount_current = df['amount'].sum()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>{total_current}</h3>
                        <p>Total Requests</p>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>{pending_current}</h3>
                        <p>Pending</p>
                    </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>{completed_current}</h3>
                        <p>Completed</p>
                    </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3>KES {amount_current:,.0f}</h3>
                        <p>Total Amount</p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Workflow Pipeline
            col1, col2, col3 = st.columns(3)
            pending_receive = len(df[df['status'] == 'SUBMITTED'])
            pending_stages = len(df[df['status'].isin(['RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED'])])
            pending_payment = len(df[df['status'].isin(['PAYMENT_AUTHORIZED'])])
            
            with col1:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3 style='color: #DC3545;'>{pending_receive}</h3>
                        <p>Pending Receive</p>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3 style='color: #FFB81C;'>{pending_stages}</h3>
                        <p>In Progress</p>
                    </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                    <div class='metric-card'>
                        <h3 style='color: #00843D;'>{pending_payment}</h3>
                        <p>Pending Payment</p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Monthly Request Trend**")
                df['month'] = pd.to_datetime(df['submission_date']).dt.strftime('%b %Y')
                monthly = df.groupby('month')['request_number'].count().reset_index()
                monthly.columns = ['month', 'count']
                if not monthly.empty:
                    fig = px.line(monthly, x='month', y='count', markers=True,
                                color_discrete_sequence=['#00843D'])
                    fig.update_layout(height=350, xaxis_title="", yaxis_title="Requests")
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("**Request Type Distribution**")
                type_counts = df['request_type'].value_counts().reset_index()
                type_counts.columns = ['Type', 'Count']
                if not type_counts.empty:
                    fig = px.pie(type_counts, values='Count', names='Type', hole=0.3,
                                color_discrete_sequence=['#00843D', '#FFB81C', '#00529B', '#DC3545'])
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.markdown("**Department Performance**")
            dept_summary = df.groupby('department_name').agg({
                'request_number': 'count',
                'amount': 'sum'
            }).reset_index()
            dept_summary.columns = ['Department', 'Requests', 'Amount']
            
            # Add completion rates
            completion_rates = []
            for dept in dept_summary['Department']:
                dept_df = df[df['department_name'] == dept]
                completed = len(dept_df[dept_df['status'].isin(['PAID', 'CLEARED'])])
                total = len(dept_df)
                rate = (completed / total * 100) if total > 0 else 0
                completion_rates.append(round(rate, 1))
            dept_summary['Completion %'] = completion_rates
            dept_summary = dept_summary.sort_values('Completion %', ascending=False)
            
            st.dataframe(dept_summary, use_container_width=True, hide_index=True)
            
            fig = px.bar(dept_summary, x='Department', y='Completion %',
                        title="Completion Rate by Department",
                        color='Completion %',
                        color_continuous_scale=['#DC3545', '#FFB81C', '#00843D'])
            fig.update_layout(height=400, xaxis_title="", yaxis_title="Completion Rate (%)")
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Amount by Request Type**")
                amount_by_type = df.groupby('request_type')['amount'].sum().reset_index()
                if not amount_by_type.empty:
                    fig = px.pie(amount_by_type, values='amount', names='request_type', hole=0.3,
                                color_discrete_sequence=['#00843D', '#FFB81C', '#00529B', '#DC3545'])
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("**Amount by Department**")
                amount_by_dept = df.groupby('department_name')['amount'].sum().reset_index()
                amount_by_dept = amount_by_dept.sort_values('amount', ascending=True).tail(10)
                if not amount_by_dept.empty:
                    fig = px.bar(amount_by_dept, x='amount', y='department_name', orientation='h',
                                color='amount', color_continuous_scale=['#FFB81C', '#00843D'])
                    fig.update_layout(height=400, xaxis_title="Amount (KES)", yaxis_title="")
                    st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            display_cols = ['request_number', 'request_type', 'department_name', 'amount', 'status', 'submission_date']
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export to CSV", csv, f"helb_export_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")


# ================================================================
# CHECK PAYMENT STATUS
# ================================================================
elif choice == "🔍 Check Payment Status":
    st.markdown("<h2 style='color: #00843D; margin-bottom: 1rem;'>🔍 Check Payment Status</h2>", unsafe_allow_html=True)
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
    st.markdown("<h2 style='color: #00843D; margin-bottom: 1rem;'>📝 Create New Request</h2>", unsafe_allow_html=True)
    
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
    st.markdown("<h2 style='color: #00843D; margin-bottom: 1rem;'>📋 My Requests</h2>", unsafe_allow_html=True)
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
                    status_badge = '<span class="status-paid">✅ Paid</span>'
                elif row['status'] == 'CLEARED':
                    status_badge = '<span class="status-cleared">✅ Cleared</span>'
                elif row['status'] == 'RECEIVED_BY_FINANCE':
                    status_badge = '<span class="status-confirmed">📥 Received</span>'
                elif row['status'] == 'RETURNED':
                    status_badge = f'<span class="status-pending">↩️ Returned</span>'
                else:
                    status_badge = f'<span class="status-pending">⏳ Pending</span>'
                
                with st.expander(f"📄 {row['request_number']} - {row['request_type']} - {row['submission_date']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Amount:** KES {row['amount']:,.2f}")
                        st.write(f"**Department:** {row['department_name']}")
                    with col2:
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
    st.markdown("<h2 style='color: #00843D; margin-bottom: 1rem;'>↩️ Returned Requests</h2>", unsafe_allow_html=True)
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
        st.markdown("<h2 style='color: #00843D; margin-bottom: 1rem;'>✅ Approval Queue</h2>", unsafe_allow_html=True)
        
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
                        checklist_approvals = st.checkbox("✓ Approvals obtained", key=f"app_{idx}")
                        checklist_documents = st.checkbox("✓ Documents attached", key=f"doc_{idx}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            pwd = st.text_input("Finance Password", type="password", key=f"pwd_{idx}")
                            if st.button(f"Confirm & Receive", key=f"confirm_{idx}"):
                                if checklist_approvals and checklist_documents:
                                    if pwd and verify_finance_password(pwd):
                                        update_request_status(req['id'], 'RECEIVED_BY_FINANCE', performed_by=st.session_state.username)
                                        st.success(f"Request confirmed!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Check both boxes!")
                        with col2:
                            reason = st.text_input("Return Reason", key=f"ret_{idx}")
                            if st.button(f"Return", key=f"return_{idx}"):
                                if reason:
                                    if pwd and verify_finance_password(pwd):
                                        update_request_status(req['id'], 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                        st.warning(f"Request returned!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                    
                    elif req['status'] == 'RECEIVED_BY_FINANCE':
                        pwd = st.text_input("Finance Password", type="password", key=f"pwd_prep_{idx}")
                        if st.button(f"Mark as Payment Prepared", key=f"prepare_{idx}"):
                            if pwd and verify_finance_password(pwd):
                                update_request_status(req['id'], 'PAYMENT_PREPARED', performed_by=st.session_state.username)
                                st.success(f"Request prepared!")
                                st.rerun()
                            else:
                                st.error("Incorrect password!")
                    
                    elif req['status'] == 'PAYMENT_PREPARED':
                        pwd = st.text_input("Finance Password", type="password", key=f"pwd_ver_{idx}")
                        if st.button(f"Mark as Verified", key=f"verify_{idx}"):
                            if pwd and verify_finance_password(pwd):
                                update_request_status(req['id'], 'PAYMENT_VERIFIED', performed_by=st.session_state.username)
                                st.success(f"Request verified!")
                                st.rerun()
                            else:
                                st.error("Incorrect password!")
                    
                    elif req['status'] == 'PAYMENT_VERIFIED':
                        pwd = st.text_input("Finance Password", type="password", key=f"pwd_app_{idx}")
                        if st.button(f"Mark as Approved", key=f"approve_{idx}"):
                            if pwd and verify_finance_password(pwd):
                                update_request_status(req['id'], 'PAYMENT_APPROVED', performed_by=st.session_state.username)
                                st.success(f"Request approved!")
                                st.rerun()
                            else:
                                st.error("Incorrect password!")
                    
                    elif req['status'] == 'PAYMENT_APPROVED':
                        pwd = st.text_input("Finance Password", type="password", key=f"pwd_auth_{idx}")
                        if st.button(f"Mark as Authorized", key=f"authorize_{idx}"):
                            if pwd and verify_finance_password(pwd):
                                update_request_status(req['id'], 'PAYMENT_AUTHORIZED', performed_by=st.session_state.username)
                                st.success(f"Request authorized!")
                                st.rerun()
                            else:
                                st.error("Incorrect password!")
                    
                    elif req['status'] == 'PAYMENT_AUTHORIZED':
                        payment_ref = st.text_input("Payment Reference", key=f"ref_{idx}")
                        pwd = st.text_input("Finance Password", type="password", key=f"pwd_pay_{idx}")
                        if st.button(f"Mark as Paid", key=f"paid_{idx}"):
                            if payment_ref:
                                if pwd and verify_finance_password(pwd):
                                    update_request_status(req['id'], 'PAID', performed_by=st.session_state.username)
                                    update_payment_details(req['id'], payment_ref)
                                    st.balloons()
                                    st.success(f"Request paid!")
                                    st.rerun()
                                else:
                                    st.error("Incorrect password!")
                            else:
                                st.error("Enter payment reference!")
    else:
        st.error("Access denied.")


# ================================================================
# REPORTS
# ================================================================
elif choice == "📑 Reports":
    st.markdown("<h2 style='color: #00843D; margin-bottom: 1rem;'>📑 Reports</h2>", unsafe_allow_html=True)
    df = get_reports_data(st.session_state.user_role, st.session_state.user_dept)
    df = filter_by_filters(df, st.session_state.selected_financial_year, st.session_state.selected_quarter, st.session_state.selected_month)
    
    if df.empty:
        st.info("No data available")
    else:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export to CSV", csv, f"helb_export_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        st.dataframe(df[['request_number', 'request_type', 'amount', 'status', 'submission_date']], use_container_width=True)


# ================================================================
# ADMIN PANEL
# ================================================================
elif choice == "⚙️ Admin Panel" and st.session_state.user_role == "ADMIN":
    st.markdown("<h2 style='color: #00843D; margin-bottom: 1rem;'>⚙️ Admin Panel</h2>", unsafe_allow_html=True)
    
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
        current_pwd = get_finance_password()
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
    st.markdown("<h2 style='color: #00843D; margin-bottom: 1rem;'>🔐 Change Password</h2>", unsafe_allow_html=True)
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
