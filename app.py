import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from datetime import datetime, date, timedelta
import numpy as np
import calendar
import os

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
    get_finance_password, add_financial_year, add_semester, add_funder, calculate_tat,
    delete_funder, delete_product, delete_financial_year, delete_semester,
    search_payment_records, update_user_permissions, delete_user,
    get_user_permissions, get_fastest_request_types, identify_bottlenecks,
    get_returned_request_by_id, get_bulk_eligible_requests, bulk_update_status,
    export_bulk_requests, get_database_health
)
from utils.holidays_ke import working_days_between, add_working_days
from streamlit_option_menu import option_menu

# Page config
st.set_page_config(
    page_title="HELB Payment & Surrender Monitoring System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Executive Edition
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Login Page Styling */
    .login-container {
        background: linear-gradient(135deg, #00843D 0%, #00529B 100%);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
    }
    .login-logo {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    .login-title {
        color: white;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }
    .login-subtitle {
        color: rgba(255,255,255,0.8);
        font-size: 0.8rem;
        margin-top: 0.25rem;
    }
    
    /* Dashboard Header */
    .dashboard-header {
        background: linear-gradient(135deg, #00843D 0%, #00529B 100%);
        padding: 0.6rem 1.2rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .header-left {
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }
    .dashboard-header h1 {
        color: white;
        margin: 0;
        font-size: 1rem;
        font-weight: 600;
    }
    .dashboard-header p {
        color: rgba(255,255,255,0.85);
        margin: 0;
        font-size: 0.6rem;
    }
    
    /* Main KPI Cards - Solid Green Background */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 0.6rem;
        margin-bottom: 1rem;
    }
    .kpi-card {
        background: #00843D;
        border-radius: 8px;
        padding: 0.6rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: all 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .kpi-label {
        font-size: 0.6rem;
        text-transform: uppercase;
        color: #FFB81C;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 1.3rem;
        font-weight: 700;
        margin: 0.2rem 0;
        color: white;
        line-height: 1.2;
    }
    .kpi-trend {
        font-size: 0.55rem;
        color: rgba(255,255,255,0.7);
    }
    .trend-up { color: #90EE90; }
    .trend-down { color: #FFB6C1; }
    
    /* Secondary Cards - Light Grey Background */
    .secondary-card {
        background: #F3F4F6;
        border-radius: 8px;
        padding: 0.5rem;
        text-align: center;
        border: 1px solid #E5E7EB;
    }
    .secondary-label {
        font-size: 0.55rem;
        text-transform: uppercase;
        color: #6B7280;
        font-weight: 600;
    }
    .secondary-value {
        font-size: 1rem;
        font-weight: 700;
        color: #1F2937;
    }
    
    /* Progress Bar */
    .progress-bar {
        height: 3px;
        background: rgba(255,255,255,0.3);
        border-radius: 2px;
        overflow: hidden;
        margin-top: 0.3rem;
    }
    .progress-fill {
        height: 100%;
        background: #FFB81C;
        border-radius: 2px;
    }
    
    /* Custom Tabs - Gold Selected, Grey Unselected */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.2rem;
        background: #F3F4F6;
        padding: 0.3rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 7px;
        padding: 0.3rem 0.8rem;
        font-weight: 500;
        font-size: 0.7rem;
        color: #4B5563;
        white-space: nowrap;
        transition: all 0.2s;
        background-color: #F3F4F6;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFB81C !important;
        color: #1F2937 !important;
        font-weight: 600;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(255,184,28,0.2);
        color: #FFB81C;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #F9FAFB 0%, white 100%);
        border-right: 1px solid #E5E7EB;
        padding-top: 0.5rem;
    }
    [data-testid="stSidebar"] .user-info {
        background: linear-gradient(135deg, #00843D 0%, #00529B 100%);
        padding: 0.5rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        color: white;
        text-align: center;
    }
    [data-testid="stSidebar"] .user-info strong {
        font-size: 0.7rem;
        display: block;
    }
    [data-testid="stSidebar"] .user-info span {
        font-size: 0.55rem;
        opacity: 0.85;
    }
    
    /* Status Badges */
    .status-paid, .status-cleared {
        background: #E8F5E9;
        color: #00843D;
        padding: 0.15rem 0.4rem;
        border-radius: 15px;
        font-size: 0.6rem;
        font-weight: 600;
        display: inline-block;
    }
    .status-pending {
        background: #FFF3E0;
        color: #ED6C02;
        padding: 0.15rem 0.4rem;
        border-radius: 15px;
        font-size: 0.6rem;
        font-weight: 600;
        display: inline-block;
    }
    .status-returned {
        background: #FFEBEE;
        color: #DC2626;
        padding: 0.15rem 0.4rem;
        border-radius: 15px;
        font-size: 0.6rem;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Section Headers for Approval Queue */
    .approval-section {
        background: #F8FAFC;
        padding: 0.6rem 1rem;
        border-radius: 10px;
        margin: 0.75rem 0 0.5rem 0;
        border-left: 4px solid #00843D;
    }
    .approval-section h4 {
        margin: 0;
        font-size: 0.8rem;
        font-weight: 600;
        color: #1F2937;
    }
    .approval-section p {
        margin: 0.2rem 0 0 0;
        font-size: 0.6rem;
        color: #6B7280;
    }
    .approval-count-badge {
        background: #00843D;
        color: white;
        padding: 0.15rem 0.5rem;
        border-radius: 20px;
        font-size: 0.6rem;
        margin-left: 0.5rem;
    }
    
    /* Finance Request Form */
    .finance-request-card {
        background: #F0FDF4;
        border: 1px solid #00843D;
        border-radius: 10px;
        padding: 0.8rem;
        margin-bottom: 1rem;
    }
    
    /* Insight Cards */
    .insight-card {
        background: #F0FDF4;
        border-left: 3px solid #00843D;
        padding: 0.4rem 0.6rem;
        border-radius: 6px;
        margin: 0.4rem 0;
        font-size: 0.65rem;
    }
    .warning-card {
        background: #FEF2F2;
        border-left: 3px solid #DC2626;
        padding: 0.4rem 0.6rem;
        border-radius: 6px;
        margin: 0.4rem 0;
        font-size: 0.65rem;
    }
    .info-card {
        background: #EFF6FF;
        border-left: 3px solid #3B82F6;
        padding: 0.4rem 0.6rem;
        border-radius: 6px;
        margin: 0.4rem 0;
        font-size: 0.65rem;
    }
    
    /* Log Entries */
    .log-submitted { background: #E3F2FD; border-left: 3px solid #2196F3; padding: 0.2rem; margin: 0.15rem 0; border-radius: 4px; font-size: 0.6rem; }
    .log-received { background: #E8F5E9; border-left: 3px solid #4CAF50; padding: 0.2rem; margin: 0.15rem 0; border-radius: 4px; font-size: 0.6rem; }
    .log-returned { background: #FFEBEE; border-left: 3px solid #F44336; padding: 0.2rem; margin: 0.15rem 0; border-radius: 4px; font-size: 0.6rem; }
    .log-paid { background: #E8F5E9; border-left: 3px solid #00843D; padding: 0.2rem; margin: 0.15rem 0; border-radius: 4px; font-size: 0.6rem; }
    .log-stage { background: #F3E5F5; border-left: 3px solid #9C27B0; padding: 0.2rem; margin: 0.15rem 0; border-radius: 4px; font-size: 0.6rem; }
    
    /* Footer */
    .main-footer {
        background: #1F2937;
        color: #9CA3AF;
        padding: 0.4rem 0.8rem;
        margin-top: 1rem;
        border-radius: 8px;
        text-align: center;
        font-size: 0.55rem;
    }
    
    /* Data Table */
    .dataframe {
        font-size: 0.65rem;
    }
    .dataframe thead tr th {
        background: #F3F4F6;
        color: #1F2937;
        font-weight: 600;
        padding: 0.3rem;
        font-size: 0.65rem;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #F9FAFB;
        border-radius: 6px;
        font-weight: 500;
        font-size: 0.65rem;
        border: 1px solid #E5E7EB;
    }
    
    /* Approval Stages */
    .stage-completed {
        background: #00843D;
        color: white;
        text-align: center;
        padding: 0.15rem;
        border-radius: 5px;
        font-size: 0.55rem;
        font-weight: 500;
    }
    .stage-pending {
        background: #FFF8E1;
        color: #FFB81C;
        text-align: center;
        padding: 0.15rem;
        border-radius: 5px;
        font-size: 0.55rem;
        border: 1px solid #FFB81C;
    }
    .stage-current {
        background: #00843D;
        color: white;
        text-align: center;
        padding: 0.15rem;
        border-radius: 5px;
        font-size: 0.55rem;
        font-weight: bold;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 0.85rem;
        font-weight: 600;
        color: #1F2937;
        margin: 0.5rem 0 0.3rem 0;
        padding-bottom: 0.2rem;
        border-bottom: 2px solid #00843D;
        display: inline-block;
    }
    
    /* Compact Filter Bar */
    .compact-filter {
        background: #F9FAFB;
        padding: 0.4rem 0.8rem;
        border-radius: 8px;
        margin-bottom: 0.8rem;
        border: 1px solid #E5E7EB;
    }
    .filter-label {
        font-size: 0.55rem;
        font-weight: 600;
        color: #6B7280;
        margin-bottom: 0.15rem;
    }
    
    /* Resubmit Form */
    .resubmit-container {
        background: #FFFBEB;
        border: 1px solid #FFB81C;
        border-radius: 8px;
        padding: 0.8rem;
        margin-top: 0.5rem;
    }
    
    /* Bulk Operations */
    .bulk-summary {
        background: #E8F5E9;
        border: 1px solid #00843D;
        border-radius: 8px;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    
    @media (max-width: 768px) {
        .kpi-value { font-size: 1rem; }
        .kpi-card { padding: 0.4rem; }
        .kpi-grid { gap: 0.4rem; }
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
if 'selected_year' not in st.session_state:
    st.session_state.selected_year = "All"

def filter_by_filters(df, financial_year, quarter, month, year):
    if df.empty or 'submission_date' not in df.columns:
        return df
    
    df = df.copy()
    df['submission_date_dt'] = pd.to_datetime(df['submission_date'])
    
    if financial_year and financial_year != "All":
        year_start = int(financial_year.split('/')[0])
        year_end = int(financial_year.split('/')[1])
        start_date = date(year_start, 7, 1)
        end_date = date(year_end, 6, 30)
        df = df[(df['submission_date_dt'].dt.date >= start_date) & (df['submission_date_dt'].dt.date <= end_date)]
    
    if year and year != "All":
        df = df[df['submission_date_dt'].dt.year == int(year)]
    
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
        return row.get('invoice_no', '-')
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
            elif action in ['Payment Prepared', 'Payment Verified', 'Payment Approved', 'Payment Authorized',
                           'First Verification', 'Second Verification', 'Surrender Approval', 'Surrender Posting']:
                st.markdown(f"<div class='log-stage'>⚙️ **{timestamp}** - {action} by {log['performed_by']}</div>", unsafe_allow_html=True)
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
        stages = ['Received', 'First Verification', 'Second Verification', 'Approval', 'Posting', 'Cleared']
    
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
        'SURRENDER_FIRST_VERIFICATION': 'First Verification',
        'SURRENDER_SECOND_VERIFICATION': 'Second Verification',
        'SURRENDER_APPROVAL': 'Approval',
        'SURRENDER_POSTING': 'Posting',
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

def refresh_page():
    st.rerun()

# Login Screen
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class='login-container'>
            <div class='login-logo'>🏦</div>
            <h1 class='login-title'>HIGHER EDUCATION LOANS BOARD</h1>
            <p class='login-subtitle'>Payment & Surrender Monitoring System</p>
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

# Header with Refresh Button
col_header, col_refresh = st.columns([6, 1])
with col_header:
    st.markdown("""
    <div class='dashboard-header'>
        <div class='header-left'>
            <div style='font-size: 1.3rem;'>🏦</div>
            <div>
                <h1>HELB Payment & Surrender Monitoring System</h1>
                <p>Real-time analytics | Performance insights | SLA tracking</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_refresh:
    if st.button("🔄 Refresh", key="global_refresh"):
        refresh_page()

# Compact Filter Bar
st.markdown("<div class='compact-filter'>", unsafe_allow_html=True)
st.markdown("<p class='filter-label'>📊 FILTERS</p>", unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    financial_years_list = ["All"] + get_financial_years()
    if not financial_years_list:
        financial_years_list = ["All", "2024/2025", "2025/2026", "2026/2027"]
    st.session_state.selected_financial_year = st.selectbox("Financial Year", financial_years_list, key="fy_filter")
with col2:
    years_list = ["All"] + list(range(2023, datetime.now().year + 2))
    st.session_state.selected_year = st.selectbox("Calendar Year", years_list, key="year_filter")
with col3:
    quarters = ["All", "Q1 (Jul-Sep)", "Q2 (Oct-Dec)", "Q3 (Jan-Mar)", "Q4 (Apr-Jun)"]
    st.session_state.selected_quarter = st.selectbox("Quarter", quarters, key="quarter_filter")
with col4:
    months = ["All", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    st.session_state.selected_month = st.selectbox("Month", months, key="month_filter")
with col5:
    data_scope = st.selectbox("Data Scope", ["All Data", "Last 30 Days", "Last 90 Days", "This Year"])
st.markdown("</div>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 0.5rem 0;'>
        <div style='font-size: 1.8rem;'>🏦</div>
        <p style='color: #00843D; font-weight: 700; margin: 0; font-size: 0.8rem;'>HELB</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class='user-info'>
            <strong>{st.session_state.full_name}</strong>
            <span>{st.session_state.user_role}</span>
            <span style='font-size: 0.55rem;'>{st.session_state.user_dept}</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    menu_options = []
    if st.session_state.user_role == "MANAGEMENT":
        menu_options = ["📈 Management Dashboard", "🔍 Search Payment Records", "📑 Reports", "🔐 Change Password"]
    elif st.session_state.user_role == "ADMIN":
        menu_options = ["📊 Department Dashboard", "📈 Management Dashboard", "🔍 Search Payment Records", 
                       "📝 New Request", "📋 My Requests", "↩️ Returned Requests", "✅ Approval Queue", 
                       "⚡ Bulk Operations", "📑 Reports", "⚙️ Admin Panel", "🔐 Change Password"]
    elif st.session_state.user_role in ["FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER", "FINANCE_ADMIN"]:
        menu_options = ["📊 Department Dashboard", "📈 Management Dashboard", "🔍 Search Payment Records", 
                       "📝 New Request (Department)", "📝 Submit on Behalf", "📋 My Requests", 
                       "↩️ Returned Requests", "✅ Approval Queue", "⚡ Bulk Operations", 
                       "📑 Reports", "🔐 Change Password"]
    else:
        menu_options = ["📊 Department Dashboard", "🔍 Search Payment Records", "📝 New Request", 
                       "📋 My Requests", "↩️ Returned Requests", "📑 Reports", "🔐 Change Password"]
    
    choice = option_menu(
        menu_title="",
        options=menu_options,
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#00843D", "font-size": "13px"},
            "nav-link": {"font-size": "11px", "text-align": "left", "margin": "0px", "padding": "5px 8px", "border-radius": "6px"},
            "nav-link-selected": {"background": "linear-gradient(135deg, #00843D 0%, #00529B 100%)", "color": "white"},
        }
    )
    
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()


# ================================================================
# DEPARTMENT DASHBOARD (PRESERVED)
# ================================================================
if choice == "📊 Department Dashboard":
    st.markdown("<div class='section-header'>📊 Department Performance Dashboard</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#6B7280; font-size:0.65rem; margin-bottom:0.8rem;'>{st.session_state.user_dept}</p>", unsafe_allow_html=True)
    
    df = get_department_requests(st.session_state.user_dept)
    
    if data_scope != "All Data" and not df.empty:
        df['submission_date_dt'] = pd.to_datetime(df['submission_date'])
        today = date.today()
        if data_scope == "Last 30 Days":
            cutoff = today - timedelta(days=30)
        elif data_scope == "Last 90 Days":
            cutoff = today - timedelta(days=90)
        elif data_scope == "This Year":
            cutoff = date(today.year, 1, 1)
        df = df[df['submission_date_dt'].dt.date >= cutoff]
    
    df = filter_by_filters(df, st.session_state.selected_financial_year, 
                          st.session_state.selected_quarter, st.session_state.selected_month,
                          st.session_state.selected_year)
    
    if df.empty:
        st.info("No data available for the selected filters.")
    else:
        total_requests = len(df)
        pending = len(df[df['status'].isin(['SUBMITTED', 'RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 
                                           'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED',
                                           'SURRENDER_FIRST_VERIFICATION', 'SURRENDER_SECOND_VERIFICATION', 
                                           'SURRENDER_APPROVAL', 'SURRENDER_POSTING'])])
        completed = len(df[df['status'].isin(['PAID', 'CLEARED'])])
        completion_rate = (completed / total_requests * 100) if total_requests > 0 else 0
        total_amount = df['amount'].sum()
        
        completed_df = df[df['status'].isin(['PAID', 'CLEARED'])]
        if not completed_df.empty:
            tat_values = completed_df.apply(
                lambda x: calculate_tat(x['submission_date'], x['payment_date']) if x['payment_date'] else 0, 
                axis=1
            )
            avg_tat = tat_values.mean()
        else:
            avg_tat = 0
        
        st.markdown("<div class='kpi-grid'>", unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>📋 TOTAL REQUESTS</div><div class='kpi-value'>{total_requests}</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>⏳ PENDING</div><div class='kpi-value'>{pending}</div></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>✅ COMPLETION RATE</div><div class='kpi-value'>{completion_rate:.1f}%</div><div class='progress-bar'><div class='progress-fill' style='width:{completion_rate}%;'></div></div></div>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>⏱️ AVG TAT</div><div class='kpi-value'>{avg_tat:.1f}d</div></div>", unsafe_allow_html=True)
        with col5:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>💰 TOTAL VALUE</div><div class='kpi-value'>KES {total_amount/1e6:.1f}M</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4 = st.tabs(["💰 Payment Requests", "📤 Surrender Requests", "⚡ Performance Analytics", "📋 Recent Activity"])
        
        with tab1:
            payment_requests = df[df['main_category'] == "Submit Payment Request"]
            if not payment_requests.empty:
                pay_total = len(payment_requests)
                pay_completed = len(payment_requests[payment_requests['status'].isin(['PAID', 'CLEARED'])])
                pay_pending = pay_total - pay_completed
                pay_amount = payment_requests['amount'].sum()
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"<div class='secondary-card'><div class='secondary-label'>📋 TOTAL</div><div class='secondary-value'>{pay_total}</div></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div class='secondary-card'><div class='secondary-label'>⏳ PENDING</div><div class='secondary-value'>{pay_pending}</div></div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div class='secondary-card'><div class='secondary-label'>✅ COMPLETED</div><div class='secondary-value'>{pay_completed}</div></div>", unsafe_allow_html=True)
                with col4:
                    st.markdown(f"<div class='secondary-card'><div class='secondary-label'>💰 VALUE</div><div class='secondary-value'>KES {pay_amount/1e6:.1f}M</div></div>", unsafe_allow_html=True)
                
                pay_df = payment_requests[['request_number', 'request_type', 'amount', 'status', 'submission_date']].head(10)
                st.dataframe(pay_df, use_container_width=True, hide_index=True)
            else:
                st.info("No payment requests found.")
        
        with tab2:
            surrender_requests = df[df['main_category'] == "Submit Surrender"]
            if not surrender_requests.empty:
                sur_total = len(surrender_requests)
                sur_completed = len(surrender_requests[surrender_requests['status'] == 'CLEARED'])
                sur_pending = sur_total - sur_completed
                sur_amount = surrender_requests['amount'].sum()
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"<div class='secondary-card'><div class='secondary-label'>📋 TOTAL</div><div class='secondary-value'>{sur_total}</div></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div class='secondary-card'><div class='secondary-label'>⏳ PENDING</div><div class='secondary-value'>{sur_pending}</div></div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div class='secondary-card'><div class='secondary-label'>✅ CLEARED</div><div class='secondary-value'>{sur_completed}</div></div>", unsafe_allow_html=True)
                with col4:
                    st.markdown(f"<div class='secondary-card'><div class='secondary-label'>💰 VALUE</div><div class='secondary-value'>KES {sur_amount/1e6:.1f}M</div></div>", unsafe_allow_html=True)
                
                sur_df = surrender_requests[['request_number', 'amount', 'status', 'submission_date']].head(10)
                st.dataframe(sur_df, use_container_width=True, hide_index=True)
            else:
                st.info("No surrender requests found.")
        
        with tab3:
            tat_analysis = get_fastest_request_types(df)
            if tat_analysis is not None and not tat_analysis.empty and 'Average TAT' in tat_analysis.columns:
                tat_analysis = tat_analysis.sort_values('Average TAT')
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=tat_analysis['Request Type'],
                    y=tat_analysis['Average TAT'],
                    name='Average TAT (Days)',
                    marker_color='#00843D',
                    text=tat_analysis['Average TAT'],
                    textposition='outside'
                ))
                fig.update_layout(
                    title="Turnaround Time by Request Type",
                    xaxis_title="",
                    yaxis_title="Days",
                    height=300,
                    xaxis_tickangle=-45,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
                
                if len(tat_analysis) > 0:
                    fastest = tat_analysis.iloc[0]
                    st.markdown(f"<div class='insight-card'><strong>🏆 Fastest Processing:</strong> {fastest['Request Type']} - {fastest['Average TAT']} days average</div>", unsafe_allow_html=True)
            else:
                st.info("Complete more requests to see TAT analysis.")
        
        with tab4:
            display_df = df.head(20).copy()
            display_df['Reference'] = display_df.apply(get_reference_number, axis=1)
            display_df['TAT'] = display_df.apply(lambda x: calculate_tat(x['submission_date'], x['payment_date']) 
                                                 if x['status'] in ['PAID', 'CLEARED'] else 'In Progress', axis=1)
            show_cols = ['request_number', 'request_type', 'Reference', 'amount', 'status', 'TAT', 'submission_date']
            st.dataframe(display_df[show_cols], use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Data", csv, f"dept_report_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        
        if st.button("🔄 Refresh This Page", key="dept_refresh"):
            refresh_page()


# ================================================================
# MANAGEMENT DASHBOARD (PRESERVED)
# ================================================================
elif choice == "📈 Management Dashboard":
    st.markdown("<div class='section-header'>🏢 Executive Management Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#6B7280; font-size:0.65rem; margin-bottom:0.8rem;'>Enterprise-wide analytics and performance insights</p>", unsafe_allow_html=True)
    
    df = get_requests()
    
    if data_scope != "All Data" and not df.empty:
        df['submission_date_dt'] = pd.to_datetime(df['submission_date'])
        today = date.today()
        if data_scope == "Last 30 Days":
            cutoff = today - timedelta(days=30)
        elif data_scope == "Last 90 Days":
            cutoff = today - timedelta(days=90)
        elif data_scope == "This Year":
            cutoff = date(today.year, 1, 1)
        df = df[df['submission_date_dt'].dt.date >= cutoff]
    
    df = filter_by_filters(df, st.session_state.selected_financial_year, 
                          st.session_state.selected_quarter, st.session_state.selected_month,
                          st.session_state.selected_year)
    
    if df.empty:
        st.info("No data available for the selected filters.")
    else:
        total_requests = len(df)
        total_amount = df['amount'].sum()
        completed = len(df[df['status'].isin(['PAID', 'CLEARED'])])
        completion_rate = (completed / total_requests * 100) if total_requests > 0 else 0
        pending = total_requests - completed
        
        completed_df = df[df['status'].isin(['PAID', 'CLEARED']) & df['payment_date'].notna()]
        sla_compliant = 0
        sla_map = {'Student Payment': 3, 'Imprest': 5, 'Petty Cash': 3, 
                   'Supplier Payment': 7, 'Salary Payment': 5, 'Refund Payment': 10,
                   'Surrender': 4, 'Mileage Claim': 3, 'Staff Training': 5,
                   'Professional Body': 5, 'Direct Payment': 3}
        
        for _, row in completed_df.iterrows():
            try:
                submitted = datetime.strptime(row['submission_date'], '%Y-%m-%d').date()
                paid = datetime.strptime(row['payment_date'], '%Y-%m-%d').date()
                days = working_days_between(submitted, paid)
                sla_days = sla_map.get(row['request_type'], 5)
                if days <= sla_days:
                    sla_compliant += 1
            except:
                pass
        
        sla_rate = (sla_compliant / len(completed_df) * 100) if len(completed_df) > 0 else 0
        avg_tat = completed_df.apply(lambda x: calculate_tat(x['submission_date'], x['payment_date']), axis=1).mean() if not completed_df.empty else 0
        
        st.markdown("<div class='kpi-grid'>", unsafe_allow_html=True)
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>📋 TOTAL REQUESTS</div><div class='kpi-value'>{total_requests:,}</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>💰 TOTAL VALUE</div><div class='kpi-value'>KES {total_amount/1e6:.1f}M</div></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>✅ COMPLETION RATE</div><div class='kpi-value'>{completion_rate:.1f}%</div></div>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>⏳ PENDING</div><div class='kpi-value'>{pending:,}</div></div>", unsafe_allow_html=True)
        with col5:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>🎯 SLA COMPLIANCE</div><div class='kpi-value'>{sla_rate:.1f}%</div></div>", unsafe_allow_html=True)
        with col6:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>⏱️ AVG TAT</div><div class='kpi-value'>{avg_tat:.1f}d</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Alerts
        breaches = []
        for _, row in completed_df.iterrows():
            try:
                submitted = datetime.strptime(row['submission_date'], '%Y-%m-%d').date()
                paid = datetime.strptime(row['payment_date'], '%Y-%m-%d').date()
                days = working_days_between(submitted, paid)
                sla_days = sla_map.get(row['request_type'], 5)
                if days > sla_days:
                    breaches.append({
                        'Request': row['request_number'],
                        'Type': row['request_type'],
                        'Department': row['department_name'],
                        'Days Taken': days,
                        'SLA Days': sla_days,
                        'Overdue By': days - sla_days
                    })
            except:
                pass
        
        long_pending = []
        pending_df = df[~df['status'].isin(['PAID', 'CLEARED', 'RETURNED'])]
        for _, row in pending_df.iterrows():
            days_pending = calculate_tat(row['submission_date'])
            if days_pending > 10:
                long_pending.append({
                    'Request': row['request_number'],
                    'Type': row['request_type'],
                    'Department': row['department_name'],
                    'Days Pending': days_pending,
                    'Status': row['status']
                })
        
        if breaches or long_pending:
            st.markdown("### 🚨 Alerts")
            col1, col2 = st.columns(2)
            with col1:
                if breaches:
                    st.markdown(f"<div class='warning-card'><strong>⚠️ SLA Breaches ({len(breaches)})</strong></div>", unsafe_allow_html=True)
            with col2:
                if long_pending:
                    st.markdown(f"<div class='warning-card'><strong>⏰ Long Pending ({len(long_pending)})</strong></div>", unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Executive Summary", "💰 Payment Analytics", "📤 Surrender Analytics", "🏆 Department Performance", "🚦 Bottlenecks"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                type_counts = df['request_type'].value_counts().reset_index()
                type_counts.columns = ['Type', 'Count']
                fig = px.pie(type_counts, values='Count', names='Type', hole=0.4,
                            color_discrete_sequence=px.colors.sequential.Greens_r,
                            title="Request Type Distribution")
                fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                status_counts = df['status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                fig = px.bar(status_counts, x='Status', y='Count', color='Count',
                            color_continuous_scale='Greens', title="Status Distribution")
                fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            payment_df = df[df['main_category'] == "Submit Payment Request"]
            if not payment_df.empty:
                pay_total = len(payment_df)
                pay_completed = len(payment_df[payment_df['status'].isin(['PAID', 'CLEARED'])])
                pay_amount = payment_df['amount'].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"<div class='secondary-card'><div class='secondary-label'>📋 TOTAL PAYMENT REQUESTS</div><div class='secondary-value'>{pay_total:,}</div></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div class='secondary-card'><div class='secondary-label'>✅ COMPLETED</div><div class='secondary-value'>{pay_completed:,}</div></div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div class='secondary-card'><div class='secondary-label'>💰 TOTAL VALUE</div><div class='secondary-value'>KES {pay_amount/1e6:.1f}M</div></div>", unsafe_allow_html=True)
                
                pay_by_type = payment_df.groupby('request_type').agg({'request_number': 'count', 'amount': 'sum'}).reset_index()
                pay_by_type.columns = ['Type', 'Count', 'Amount']
                fig = px.bar(pay_by_type, x='Type', y='Count', title="Payment Requests by Type",
                            color='Count', color_continuous_scale='Greens', text='Count')
                fig.update_traces(textposition='outside')
                fig.update_layout(height=300, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No payment requests found.")
        
        with tab3:
            surrender_df = df[df['main_category'] == "Submit Surrender"]
            if not surrender_df.empty:
                sur_total = len(surrender_df)
                sur_completed = len(surrender_df[surrender_df['status'] == 'CLEARED'])
                sur_amount = surrender_df['amount'].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"<div class='secondary-card'><div class='secondary-label'>📋 TOTAL SURRENDER REQUESTS</div><div class='secondary-value'>{sur_total:,}</div></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div class='secondary-card'><div class='secondary-label'>✅ CLEARED</div><div class='secondary-value'>{sur_completed:,}</div></div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div class='secondary-card'><div class='secondary-label'>💰 TOTAL VALUE</div><div class='secondary-value'>KES {sur_amount/1e6:.1f}M</div></div>", unsafe_allow_html=True)
                
                fig = px.bar(x=['Cleared', 'Pending'], y=[sur_completed, sur_total - sur_completed],
                            title="Surrender Clearance Status",
                            color=['Cleared', 'Pending'], color_discrete_sequence=['#00843D', '#FFB81C'],
                            text_auto=True)
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No surrender requests found.")
        
        with tab4:
            dept_performance = []
            for dept in df['department_name'].unique():
                dept_df = df[df['department_name'] == dept]
                total = len(dept_df)
                completed_dept = len(dept_df[dept_df['status'].isin(['PAID', 'CLEARED'])])
                completion_rate = (completed_dept / total * 100) if total > 0 else 0
                total_value = dept_df['amount'].sum()
                
                completed_dept_df = dept_df[dept_df['status'].isin(['PAID', 'CLEARED'])]
                if not completed_dept_df.empty:
                    avg_tat_dept = completed_dept_df.apply(
                        lambda x: calculate_tat(x['submission_date'], x['payment_date']) if x['payment_date'] else 0, 
                        axis=1
                    ).mean()
                else:
                    avg_tat_dept = 0
                
                score = (completion_rate * 0.6) + (max(0, min(100, (15 - (avg_tat_dept if not pd.isna(avg_tat_dept) else 15)) * 6.67)) * 0.4)
                
                dept_performance.append({
                    'Department': dept,
                    'Total': total,
                    'Completed': completed_dept,
                    'Completion %': f"{completion_rate:.1f}%",
                    'Value (KES M)': f"{total_value/1e6:.1f}",
                    'Avg TAT (Days)': f"{avg_tat_dept:.1f}",
                    'Performance Score': f"{score:.1f}%"
                })
            
            perf_df = pd.DataFrame(dept_performance).sort_values('Performance Score', ascending=False)
            st.dataframe(perf_df, use_container_width=True, hide_index=True)
            
            top_depts = perf_df.head(5)
            fig = px.bar(top_depts, x='Department', y='Performance Score', 
                        title="Top 5 Performing Departments",
                        color='Performance Score', color_continuous_scale='Greens',
                        text='Performance Score')
            fig.update_traces(textposition='outside')
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab5:
            bottlenecks = identify_bottlenecks(df)
            if bottlenecks is not None and not bottlenecks.empty:
                fig = px.bar(bottlenecks, x='Stage', y='Avg Days',
                            title="Average Time Spent per Stage",
                            color='Is Bottleneck',
                            color_discrete_map={True: '#DC3545', False: '#00843D'},
                            text='Avg Days')
                fig.update_traces(textposition='outside')
                fig.update_layout(height=350, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
                
                bottlenecks_list = bottlenecks[bottlenecks['Is Bottleneck']]['Stage'].tolist()
                if bottlenecks_list:
                    st.markdown(f"<div class='warning-card'><strong>⚠️ Bottlenecks Detected:</strong> {', '.join(bottlenecks_list)}</div>", unsafe_allow_html=True)
            else:
                st.info("Insufficient data for bottleneck analysis.")
        
        csv_full = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Full Data", csv_full, f"helb_export_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        
        if st.button("🔄 Refresh This Page", key="mgmt_refresh"):
            refresh_page()


# ================================================================
# ENHANCED SEARCH PAYMENT RECORDS - ALL USERS CAN SEE PREDICTIONS
# ================================================================
elif choice == "🔍 Search Payment Records":
    st.markdown("<div class='section-header'>🔍 Intelligent Payment Search</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background:#F0F9FF; padding:0.4rem 0.6rem; border-radius:6px; margin-bottom:0.8rem; font-size:0.65rem;'>
        🔎 Search by Request Number, Batch No., Imprest No., Invoice No., Surrender No., Payment Reference, 
        Staff Name, Supplier Name, or Customer Name. View predicted completion dates and risk assessment.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("Enter search term", placeholder="e.g., HELB-202503-0001, BATCH001, INV-12345, John Doe...")
    with col2:
        search_type = st.selectbox("Search by", ["All Fields", "Request Number", "Batch No.", "Imprest No.", 
                                                  "Invoice No.", "Surrender No.", "Staff Name", "Supplier Name", 
                                                  "Customer Name", "Payment Reference"])
    with col3:
        status_filter = st.selectbox("Status", ["All", "SUBMITTED", "RECEIVED_BY_FINANCE", "PAYMENT_PREPARED", 
                                                "PAYMENT_VERIFIED", "PAYMENT_APPROVED", "PAYMENT_AUTHORIZED", 
                                                "PAID", "CLEARED", "RETURNED"])
    
    # Define roles that can see transaction logs (sensitive audit trail)
    finance_roles = ["FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER", "FINANCE_ADMIN"]
    sensitive_roles = ["ADMIN", "MANAGEMENT"] + finance_roles
    can_see_logs = st.session_state.user_role in sensitive_roles or st.session_state.is_finance
    
    if st.button("🔍 Search", type="primary"):
        if search_term:
            type_map = {
                "Request Number": "request_number",
                "Batch No.": "batch_no",
                "Imprest No.": "imprest_no",
                "Invoice No.": "invoice_no",
                "Surrender No.": "surrender_number",
                "Staff Name": "all_names",
                "Supplier Name": "all_names",
                "Customer Name": "all_names",
                "Payment Reference": "payment_reference",
                "All Fields": "all"
            }
            db_search_type = type_map.get(search_type, "all")
            
            results = search_payment_records(search_term, db_search_type)
            
            if status_filter != "All":
                results = results[results['status'] == status_filter]
            
            if not results.empty:
                st.markdown(f"### 📋 Search Results ({len(results)} records found)")
                
                for _, row in results.iterrows():
                    # Determine entity name (staff, supplier, customer)
                    entity_name = ""
                    entity_type = ""
                    
                    if row.get('staff_name') and row['staff_name'] != '-' and row['staff_name']:
                        entity_name = row['staff_name']
                        entity_type = "Staff"
                    elif row.get('supplier_name') and row['supplier_name'] != '-' and row['supplier_name']:
                        entity_name = row['supplier_name']
                        entity_type = "Supplier"
                    elif row.get('customer_name') and row['customer_name'] != '-' and row['customer_name']:
                        entity_name = row['customer_name']
                        entity_type = "Customer"
                    
                    # Calculate current TAT and SLA status
                    if row['status'] in ['PAID', 'CLEARED'] and row.get('payment_date'):
                        tat = calculate_tat(row['submission_date'], row['payment_date'])
                        status_badge = f'<span class="status-paid">✅ {row["status"]} (TAT: {tat} days)</span>'
                        is_completed = True
                    else:
                        tat = calculate_tat(row['submission_date'])
                        status_badge = f'<span class="status-pending">⏳ {row["status"]} (Pending: {tat} days)</span>'
                        is_completed = False
                    
                    # SLA Days for this request type
                    sla_map = {'Student Payment': 3, 'Imprest': 5, 'Petty Cash': 3, 
                               'Supplier Payment': 7, 'Salary Payment': 5, 'Refund Payment': 10,
                               'Surrender': 4, 'Mileage Claim': 3, 'Staff Training': 5,
                               'Professional Body': 5, 'Direct Payment': 3}
                    sla_days = sla_map.get(row['request_type'], 5)
                    
                    # Risk assessment - visible to ALL users now
                    if not is_completed:
                        if tat > sla_days:
                            risk_level = "Critical - Overdue"
                            risk_color = "#DC2626"
                        elif tat > sla_days * 0.8:
                            risk_level = "High - At Risk"
                            risk_color = "#F59E0B"
                        elif tat > sla_days * 0.5:
                            risk_level = "Medium - On Track"
                            risk_color = "#FFB81C"
                        else:
                            risk_level = "Low - Good Progress"
                            risk_color = "#00843D"
                    else:
                        if tat > sla_days:
                            risk_level = "Completed (Delayed)"
                            risk_color = "#F59E0B"
                        else:
                            risk_level = "Completed (On Time)"
                            risk_color = "#00843D"
                    
                    # Get reference number
                    ref_number = get_reference_number(row)
                    
                    # Predict completion date for pending requests - visible to ALL users
                    predicted_date = None
                    confidence = None
                    if not is_completed:
                        # Calculate average TAT for similar completed requests
                        df_all = get_requests()
                        similar_completed = df_all[
                            (df_all['request_type'] == row['request_type']) & 
                            (df_all['status'].isin(['PAID', 'CLEARED'])) &
                            (df_all['payment_date'].notna())
                        ]
                        if not similar_completed.empty:
                            avg_tat_similar = similar_completed.apply(
                                lambda x: calculate_tat(x['submission_date'], x['payment_date']), axis=1
                            ).mean()
                            remaining_days = max(1, avg_tat_similar - tat)
                            predicted_date = date.today() + timedelta(days=remaining_days)
                            confidence = "High" if len(similar_completed) > 20 else "Medium" if len(similar_completed) > 5 else "Low"
                        else:
                            # Use SLA-based prediction
                            remaining_days = max(1, sla_days - tat)
                            predicted_date = date.today() + timedelta(days=remaining_days)
                            confidence = "Medium (based on SLA)"
                    
                    # Create expandable result card
                    with st.expander(f"📄 {row['request_number']} - {row['request_type']} - {row['department_name']}", expanded=False):
                        # Header with status and risk
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.markdown(f"**Status:** {status_badge}", unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"**Risk Level:** <span style='color:{risk_color}; font-weight:bold;'>{risk_level}</span>", unsafe_allow_html=True)
                        with col3:
                            if not is_completed and predicted_date:
                                st.markdown(f"**📅 Predicted Completion:** {predicted_date.strftime('%d %b %Y')} <span style='font-size:0.6rem;'>({confidence} confidence)</span>", unsafe_allow_html=True)
                            elif is_completed and row.get('payment_date'):
                                st.markdown(f"**✅ Completed:** {row['payment_date']}")
                        
                        st.markdown("---")
                        
                        # Two-column layout for details
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**💰 Amount:** KES {row['amount']:,.2f}")
                            st.markdown(f"**📅 Submitted:** {row['submission_date']}")
                            if row.get('date_received'):
                                st.markdown(f"**📥 Received by Finance:** {row['date_received']}")
                            if ref_number and ref_number != '-':
                                st.markdown(f"**🔢 Reference:** {ref_number}")
                            if entity_name:
                                st.markdown(f"**👤 {entity_type} Name:** {entity_name}")
                        
                        with col2:
                            if row.get('payment_description'):
                                st.markdown(f"**📝 Description:** {row['payment_description'][:100]}{'...' if len(row['payment_description']) > 100 else ''}")
                            if row.get('payment_reference'):
                                st.markdown(f"**🏦 Payment Ref:** {row['payment_reference']}")
                            if row.get('return_reason'):
                                st.markdown(f"**↩️ Return Reason:** :red[{row['return_reason']}]")
                            if not is_completed:
                                st.markdown(f"**⏱️ Current TAT:** {tat} / {sla_days} days")
                                # Progress bar
                                progress_pct = min(100, (tat / sla_days) * 100)
                                bar_color = "#DC3545" if progress_pct > 100 else "#F59E0B" if progress_pct > 80 else "#00843D"
                                st.markdown(f"""
                                <div class='progress-bar' style='height:6px; background:#E5E7EB;'>
                                    <div class='progress-fill' style='width:{min(100, progress_pct)}%; background:{bar_color};'></div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Additional details for specific request types
                        st.markdown("---")
                        st.markdown("**📋 Additional Details:**")
                        details_cols = st.columns(4)
                        detail_items = []
                        
                        if row.get('batch_no'):
                            detail_items.append(("Batch No.", row['batch_no']))
                        if row.get('imprest_no'):
                            detail_items.append(("Imprest/Petty No.", row['imprest_no']))
                        if row.get('invoice_no'):
                            detail_items.append(("Invoice No.", row['invoice_no']))
                        if row.get('supplier_name'):
                            detail_items.append(("Supplier", row['supplier_name']))
                        if row.get('staff_name'):
                            detail_items.append(("Staff", row['staff_name']))
                        if row.get('customer_name'):
                            detail_items.append(("Customer", row['customer_name']))
                        if row.get('product_type'):
                            detail_items.append(("Product", row['product_type']))
                        if row.get('semester'):
                            detail_items.append(("Semester", row['semester']))
                        if row.get('funder_name'):
                            detail_items.append(("Funder", row['funder_name']))
                        if row.get('salary_month') and row.get('salary_year'):
                            detail_items.append(("Salary Period", f"{row['salary_month']} {row['salary_year']}"))
                        if row.get('professional_body'):
                            detail_items.append(("Professional Body", row['professional_body']))
                        
                        for i, (label, value) in enumerate(detail_items[:8]):
                            with details_cols[i % 4]:
                                st.markdown(f"**{label}:** {value}")
                        
                        # Similar requests performance - visible to ALL users
                        st.markdown("---")
                        st.markdown("**📊 Similar Requests Performance**")
                        
                        # Get similar completed requests
                        df_all = get_requests()
                        similar_completed = df_all[
                            (df_all['request_type'] == row['request_type']) & 
                            (df_all['status'].isin(['PAID', 'CLEARED'])) &
                            (df_all['payment_date'].notna())
                        ].head(5)
                        
                        if not similar_completed.empty:
                            similar_data = []
                            for _, sim in similar_completed.iterrows():
                                sim_tat = calculate_tat(sim['submission_date'], sim['payment_date'])
                                similar_data.append({
                                    'Request': sim['request_number'],
                                    'TAT (days)': sim_tat,
                                    'Status': 'On Time' if sim_tat <= sla_map.get(sim['request_type'], 5) else 'Delayed'
                                })
                            sim_df = pd.DataFrame(similar_data)
                            st.dataframe(sim_df, use_container_width=True, hide_index=True)
                            
                            # Show average
                            avg_sim_tat = similar_completed.apply(
                                lambda x: calculate_tat(x['submission_date'], x['payment_date']), axis=1
                            ).mean()
                            st.caption(f"📈 Average TAT for similar requests: {avg_sim_tat:.1f} days (SLA: {sla_days} days)")
                        else:
                            st.caption("No completed similar requests found for comparison.")
                        
                        # Timeline/Progress Section
                        st.markdown("---")
                        st.markdown("**📅 Progress Timeline**")
                        
                        # Define stages based on request type
                        if row['request_type'] == "Surrender":
                            stages = [
                                {'name': 'Submitted', 'status_key': 'SUBMITTED', 'date': row['submission_date']},
                                {'name': 'Received', 'status_key': 'RECEIVED_BY_FINANCE', 'date': row['date_received']},
                                {'name': 'First Verification', 'status_key': 'SURRENDER_FIRST_VERIFICATION', 'date': None},
                                {'name': 'Second Verification', 'status_key': 'SURRENDER_SECOND_VERIFICATION', 'date': None},
                                {'name': 'Approval', 'status_key': 'SURRENDER_APPROVAL', 'date': None},
                                {'name': 'Posting', 'status_key': 'SURRENDER_POSTING', 'date': None},
                                {'name': 'Cleared', 'status_key': 'CLEARED', 'date': row['payment_date']}
                            ]
                        else:
                            stages = [
                                {'name': 'Submitted', 'status_key': 'SUBMITTED', 'date': row['submission_date']},
                                {'name': 'Received', 'status_key': 'RECEIVED_BY_FINANCE', 'date': row['date_received']},
                                {'name': 'Prepared', 'status_key': 'PAYMENT_PREPARED', 'date': None},
                                {'name': 'Verified', 'status_key': 'PAYMENT_VERIFIED', 'date': None},
                                {'name': 'Approved', 'status_key': 'PAYMENT_APPROVED', 'date': None},
                                {'name': 'Authorized', 'status_key': 'PAYMENT_AUTHORIZED', 'date': None},
                                {'name': 'Paid', 'status_key': 'PAID', 'date': row['payment_date']}
                            ]
                        
                        # Determine current stage index
                        current_index = 0
                        status_order = [s['status_key'] for s in stages]
                        if row['status'] in status_order:
                            current_index = status_order.index(row['status'])
                        
                        # Display timeline
                        for i, stage in enumerate(stages):
                            is_completed_stage = i < current_index
                            is_current = i == current_index
                            
                            if is_completed_stage:
                                icon = "✅"
                                color = "#00843D"
                            elif is_current:
                                icon = "📍"
                                color = "#FFB81C"
                            else:
                                icon = "○"
                                color = "#D1D5DB"
                            
                            date_str = ""
                            if stage['date']:
                                date_str = f"<span style='font-size:0.6rem; color:#6B7280;'>{stage['date']}</span>"
                            elif is_current and stage['date'] is None:
                                date_str = "<span style='font-size:0.6rem; color:#F59E0B;'>In progress</span>"
                            
                            st.markdown(f"""
                            <div style='display: flex; align-items: center; margin: 0.3rem 0;'>
                                <div style='width: 20px; text-align: center;'>{icon}</div>
                                <div style='flex: 1; margin-left: 0.5rem;'>
                                    <strong style='font-size:0.7rem;'>{stage['name']}</strong>
                                    {date_str}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Warning for overdue
                        if not is_completed:
                            if tat > sla_days:
                                st.markdown(f"""
                                <div class='warning-card' style='margin-top:0.5rem;'>
                                    <strong>⚠️ URGENT: SLA BREACH</strong><br>
                                    This request is {tat - sla_days} days overdue. Please follow up immediately.
                                </div>
                                """, unsafe_allow_html=True)
                            elif tat > sla_days * 0.8:
                                st.markdown(f"""
                                <div class='warning-card' style='margin-top:0.5rem;'>
                                    <strong>⚠️ At Risk of SLA Breach</strong><br>
                                    This request is approaching its SLA deadline. {sla_days - tat} days remaining.
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Transaction History - ONLY for authorized roles (Finance, Management, Admin)
                        if can_see_logs:
                            with st.expander("📜 View Full Transaction History"):
                                display_transaction_logs(row['id'])
                        else:
                            st.caption("📜 Full transaction history is available to Finance and Management only.")
            else:
                st.warning("No records found matching your search criteria.")
        else:
            st.info("Please enter a search term.")
    
    if st.button("🔄 Refresh This Page", key="search_refresh"):
        refresh_page()


# ================================================================
# NEW REQUEST (PRESERVED)
# ================================================================
elif choice == "📝 New Request" or choice == "📝 New Request (Department)":
    st.markdown("<div class='section-header'>📝 Create New Request</div>", unsafe_allow_html=True)
    
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
            
            # Student Payment - Regular
            if main_category == "Submit Payment Request" and selected_type == "Student Payment" and st.session_state.user_dept != "External Resource Mobilization":
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
            
            # Student Payment - ERM
            elif main_category == "Submit Payment Request" and selected_type == "Student Payment" and st.session_state.user_dept == "External Resource Mobilization":
                with st.form(key="erm_student_form"):
                    st.subheader("🎓 Student Payment Details (Partner Funds)")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    
                    funders = get_funders()
                    if not funders.empty:
                        funder_name = st.selectbox("Partner / Funder", funders['name'].tolist())
                    else:
                        funder_name = st.text_input("Partner / Funder Name *")
                    
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    
                    batch_no = st.text_input("Batch No. *")
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                    payment_description = st.text_area("Payment Details")
                    
                    if st.form_submit_button("Submit"):
                        if not funder_name or not batch_no or amount <= 0:
                            st.error("Please fill all required fields")
                        else:
                            request_data = {
                                'main_category': main_category, 'request_type': "Student Payment",
                                'department_id': st.session_state.user_dept_id, 'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username, 'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'batch_no': batch_no, 'funder_name': funder_name,
                                'status': 'SUBMITTED'
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
                    st.subheader("💸 Direct Payment Details")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    
                    invoice_no = st.text_input("Invoice No. *")
                    direct_payment_details = st.text_area("Payment Details (Payee, Purpose)")
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    payment_description = st.text_area("Additional Notes")
                    
                    if st.form_submit_button("Submit"):
                        if not invoice_no or not direct_payment_details or amount <= 0:
                            st.error("Please fill all required fields")
                        else:
                            request_data = {
                                'main_category': main_category, 'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id, 'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username, 'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'direct_payment_details': direct_payment_details, 'invoice_no': invoice_no,
                                'status': 'SUBMITTED'
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
                    st.subheader("⛽ Mileage Claim Details")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=st.session_state.user_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    
                    staff_name = st.text_input("Staff Name *")
                    mileage_claim_details = st.text_area("Trip Details (From, To, Distance, Vehicle Reg No.)")
                    amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=100.0)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    payment_description = st.text_area("Additional Notes")
                    
                    if st.form_submit_button("Submit"):
                        if not staff_name or not mileage_claim_details or amount <= 0:
                            st.error("Please fill all required fields")
                        else:
                            request_data = {
                                'main_category': main_category, 'request_type': selected_type,
                                'department_id': st.session_state.user_dept_id, 'department_name': st.session_state.user_dept,
                                'submitted_by': st.session_state.username, 'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'mileage_claim_details': mileage_claim_details, 'staff_name': staff_name,
                                'status': 'SUBMITTED'
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
    
    if st.button("🔄 Refresh This Page", key="new_refresh"):
        refresh_page()


# ================================================================
# SUBMIT ON BEHALF (FOR FINANCE USERS)
# ================================================================
elif choice == "📝 Submit on Behalf":
    finance_roles = ["FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER", "FINANCE_ADMIN"]
    if st.session_state.user_role in finance_roles or st.session_state.user_role == "ADMIN":
        st.markdown("<div class='section-header'>📝 Submit Request on Behalf of Department</div>", unsafe_allow_html=True)
        st.markdown("<p style='color:#6B7280; font-size:0.65rem; margin-bottom:0.8rem;'>Finance users can submit requests for any department</p>", unsafe_allow_html=True)
        
        depts = get_departments()
        dept_list = depts['name'].tolist() if not depts.empty else []
        
        col1, col2 = st.columns(2)
        with col1:
            selected_department = st.selectbox("Select Department", dept_list)
            dept_id = depts[depts['name'] == selected_department]['id'].values[0] if not depts.empty else None
        with col2:
            main_category = st.radio("Request Type", ["Submit Payment Request", "Submit Surrender"], horizontal=True)
        
        st.markdown("---")
        
        if main_category == "Submit Payment Request":
            request_type = st.selectbox("Payment Request Type", [
                "Student Payment", "Imprest", "Petty Cash", "Supplier Payment", 
                "Salary Payment", "Refund Payment", "Direct Payment", "Mileage Claim", 
                "Staff Training", "Professional Body"
            ])
        else:
            request_type = "Surrender"
        
        st.markdown("---")
        
        with st.form(key="on_behalf_form"):
            st.markdown(f"**Submitting for: {selected_department}**")
            st.markdown(f"**Request Type: {request_type}**")
            
            amount = st.number_input("Amount (KShs.)", min_value=0.0, format="%.2f", step=1000.0)
            payment_description = st.text_area("Payment Description")
            financial_years = get_financial_years()
            financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
            
            if request_type == "Student Payment":
                batch_no = st.text_input("Batch No.")
                if st.form_submit_button("Submit Request"):
                    if batch_no and amount > 0:
                        request_data = {
                            'main_category': main_category, 'request_type': request_type,
                            'department_id': dept_id, 'department_name': selected_department,
                            'submitted_by': st.session_state.username, 'amount': amount,
                            'payment_description': payment_description, 'financial_year': financial_year,
                            'batch_no': batch_no, 'status': 'SUBMITTED'
                        }
                        request_number = save_request(request_data)
                        st.success(f"✅ Request {request_number} submitted for {selected_department}!")
                        st.balloons()
            
            elif request_type == "Imprest":
                imprest_no = st.text_input("Imprest No.")
                if st.form_submit_button("Submit Request"):
                    if imprest_no and amount > 0:
                        request_data = {
                            'main_category': main_category, 'request_type': request_type,
                            'department_id': dept_id, 'department_name': selected_department,
                            'submitted_by': st.session_state.username, 'amount': amount,
                            'payment_description': payment_description, 'financial_year': financial_year,
                            'imprest_no': imprest_no, 'status': 'SUBMITTED'
                        }
                        request_number = save_request(request_data)
                        st.success(f"✅ Request {request_number} submitted for {selected_department}!")
                        st.balloons()
            
            elif request_type == "Petty Cash":
                petty_no = st.text_input("Petty Cash No.")
                if st.form_submit_button("Submit Request"):
                    if petty_no and amount > 0:
                        request_data = {
                            'main_category': main_category, 'request_type': request_type,
                            'department_id': dept_id, 'department_name': selected_department,
                            'submitted_by': st.session_state.username, 'amount': amount,
                            'payment_description': payment_description, 'financial_year': financial_year,
                            'imprest_no': petty_no, 'status': 'SUBMITTED'
                        }
                        request_number = save_request(request_data)
                        st.success(f"✅ Request {request_number} submitted for {selected_department}!")
                        st.balloons()
            
            elif request_type == "Supplier Payment":
                invoice_no = st.text_input("Invoice No.")
                supplier_name = st.text_input("Supplier Name")
                if st.form_submit_button("Submit Request"):
                    if invoice_no and supplier_name and amount > 0:
                        request_data = {
                            'main_category': main_category, 'request_type': request_type,
                            'department_id': dept_id, 'department_name': selected_department,
                            'submitted_by': st.session_state.username, 'amount': amount,
                            'payment_description': payment_description, 'financial_year': financial_year,
                            'invoice_no': invoice_no, 'supplier_name': supplier_name, 'status': 'SUBMITTED'
                        }
                        request_number = save_request(request_data)
                        st.success(f"✅ Request {request_number} submitted for {selected_department}!")
                        st.balloons()
            
            elif request_type == "Surrender":
                surrender_no = st.text_input("Surrender No.")
                staff_name = st.text_input("Staff Name")
                if st.form_submit_button("Submit Request"):
                    if surrender_no and staff_name and amount > 0:
                        request_data = {
                            'main_category': main_category, 'request_type': request_type,
                            'department_id': dept_id, 'department_name': selected_department,
                            'submitted_by': st.session_state.username, 'amount': amount,
                            'payment_description': payment_description, 'financial_year': financial_year,
                            'surrender_number': surrender_no, 'staff_name': staff_name, 'status': 'SUBMITTED'
                        }
                        request_number = save_request(request_data)
                        st.success(f"✅ Request {request_number} submitted for {selected_department}!")
                        st.balloons()
            
            else:
                if st.form_submit_button("Submit Request"):
                    if amount > 0:
                        request_data = {
                            'main_category': main_category, 'request_type': request_type,
                            'department_id': dept_id, 'department_name': selected_department,
                            'submitted_by': st.session_state.username, 'amount': amount,
                            'payment_description': payment_description, 'financial_year': financial_year,
                            'status': 'SUBMITTED'
                        }
                        request_number = save_request(request_data)
                        st.success(f"✅ Request {request_number} submitted for {selected_department}!")
                        st.balloons()
    
    if st.button("🔄 Refresh This Page", key="onbehalf_refresh"):
        refresh_page()


# ================================================================
# MY REQUESTS (PRESERVED)
# ================================================================
elif choice == "📋 My Requests":
    st.markdown("<div class='section-header'>📋 My Requests</div>", unsafe_allow_html=True)
    df = get_requests()
    if df.empty:
        st.info("No requests found.")
    else:
        user_requests = df[df['submitted_by'] == st.session_state.username]
        if user_requests.empty:
            st.info("You haven't submitted any requests yet.")
        else:
            for _, row in user_requests.iterrows():
                if row['status'] in ['PAID', 'CLEARED'] and row.get('payment_date'):
                    tat = calculate_tat(row['submission_date'], row['payment_date'])
                    if row['status'] == 'PAID':
                        status_badge = f'<span class="status-paid">✅ Paid ({tat} days)</span>'
                    else:
                        status_badge = f'<span class="status-paid">✅ Cleared ({tat} days)</span>'
                else:
                    pending_days = calculate_tat(row['submission_date'])
                    status_badge = f'<span class="status-pending">⏳ Pending ({pending_days} days)</span>'
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
    
    if st.button("🔄 Refresh This Page", key="my_refresh"):
        refresh_page()


# ================================================================
# RETURNED REQUESTS (PRESERVED)
# ================================================================
elif choice == "↩️ Returned Requests":
    st.markdown("<div class='section-header'>↩️ Returned Requests - Action Required</div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#6B7280; font-size:0.65rem; margin-bottom:0.8rem;'>Review the return reasons below and resubmit your requests after making corrections.</p>", unsafe_allow_html=True)
    
    df = get_returned_requests(st.session_state.user_dept)
    
    if df.empty:
        st.info("No returned requests found. Great job! All your requests are on track.")
    else:
        for _, req in df.iterrows():
            with st.expander(f"📄 {req['request_number']} - Returned on: {req['date_returned']} - {req['request_type']}", expanded=True):
                st.markdown(f"""
                <div class='warning-card'>
                    <strong>⚠️ Return Reason:</strong> {req['return_reason']}<br>
                    <strong>💰 Amount:</strong> KES {req['amount']:,.2f}<br>
                    <strong>📅 Submitted:</strong> {req['submission_date']}<br>
                    <strong>🏢 Department:</strong> {req['department_name']}
                </div>
                """, unsafe_allow_html=True)
                
                if req.get('payment_description'):
                    st.markdown(f"**Original Description:** {req['payment_description']}")
                
                st.markdown("---")
                st.markdown("### 📝 Make Corrections and Resubmit")
                
                with st.form(key=f"resubmit_form_{req['id']}"):
                    st.markdown("**Please correct the following information:**")
                    
                    corrected_description = st.text_area(
                        "Payment Description (if correction needed)", 
                        value=req.get('payment_description', ''),
                        help="Update the payment description if required"
                    )
                    
                    if req['request_type'] == "Student Payment":
                        corrected_batch = st.text_input("Batch No.", value=req.get('batch_no', ''))
                        corrected_amount = st.number_input("Amount (KShs.)", value=float(req['amount']), min_value=0.0, step=1000.0)
                        correction_data = {
                            'batch_no': corrected_batch,
                            'amount': corrected_amount
                        }
                    elif req['request_type'] in ["Imprest", "Petty Cash"]:
                        corrected_imprest = st.text_input("Imprest/Petty Cash No.", value=req.get('imprest_no', ''))
                        corrected_amount = st.number_input("Amount (KShs.)", value=float(req['amount']), min_value=0.0, step=1000.0)
                        correction_data = {
                            'imprest_no': corrected_imprest,
                            'amount': corrected_amount
                        }
                    elif req['request_type'] == "Supplier Payment":
                        corrected_invoice = st.text_input("Invoice No.", value=req.get('invoice_no', ''))
                        corrected_supplier = st.text_input("Supplier Name", value=req.get('supplier_name', ''))
                        corrected_amount = st.number_input("Amount (KShs.)", value=float(req['amount']), min_value=0.0, step=1000.0)
                        correction_data = {
                            'invoice_no': corrected_invoice,
                            'supplier_name': corrected_supplier,
                            'amount': corrected_amount
                        }
                    elif req['request_type'] == "Surrender":
                        corrected_surrender = st.text_input("Surrender No.", value=req.get('surrender_number', ''))
                        corrected_staff = st.text_input("Staff Name", value=req.get('staff_name', ''))
                        corrected_amount = st.number_input("Amount (KShs.)", value=float(req['amount']), min_value=0.0, step=1000.0)
                        correction_data = {
                            'surrender_number': corrected_surrender,
                            'staff_name': corrected_staff,
                            'amount': corrected_amount
                        }
                    else:
                        corrected_amount = st.number_input("Amount (KShs.)", value=float(req['amount']), min_value=0.0, step=1000.0)
                        correction_data = {'amount': corrected_amount}
                    
                    st.markdown("<div class='resubmit-container'>", unsafe_allow_html=True)
                    st.info("💡 Please ensure all corrections are made before resubmitting. The request will go back to Finance for review.")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        resubmit = st.form_submit_button("✅ Confirm Corrections & Resubmit", type="primary")
                    with col2:
                        cancel = st.form_submit_button("❌ Cancel")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    if resubmit:
                        updated_data = {
                            'payment_description': corrected_description,
                            'status': 'SUBMITTED',
                            'return_reason': None,
                            'date_returned': None,
                            **correction_data
                        }
                        
                        success = resubmit_request(req['id'], updated_data)
                        
                        if success:
                            add_request_log(
                                req['id'], req['request_number'], "RESUBMITTED", 
                                "RETURNED", "SUBMITTED", 
                                f"Resubmitted after correction. Original return reason: {req['return_reason']}",
                                st.session_state.username, st.session_state.user_role, st.session_state.user_dept
                            )
                            
                            st.success(f"✅ Request {req['request_number']} has been resubmitted successfully!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Failed to resubmit request. Please try again.")
                    
                    if cancel:
                        st.info("Resubmission cancelled.")
    
    if st.button("🔄 Refresh This Page", key="returned_refresh"):
        refresh_page()


# ================================================================
# APPROVAL QUEUE (PRESERVED - Full from previous message)
# ================================================================
elif choice == "✅ Approval Queue":
    finance_roles = ["FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER", "FINANCE_ADMIN"]
    if st.session_state.user_role in finance_roles or st.session_state.user_role == "ADMIN" or st.session_state.is_finance:
        st.markdown("<div class='section-header'>✅ Approval Queue</div>", unsafe_allow_html=True)
        
        # Summary metrics at the top
        df_all = get_requests()
        
        # Payment summary
        payment_df = df_all[df_all['main_category'] == "Submit Payment Request"]
        payment_counts = {
            'submitted': len(payment_df[payment_df['status'] == 'SUBMITTED']),
            'received': len(payment_df[payment_df['status'] == 'RECEIVED_BY_FINANCE']),
            'prepared': len(payment_df[payment_df['status'] == 'PAYMENT_PREPARED']),
            'verified': len(payment_df[payment_df['status'] == 'PAYMENT_VERIFIED']),
            'approved': len(payment_df[payment_df['status'] == 'PAYMENT_APPROVED']),
            'authorized': len(payment_df[payment_df['status'] == 'PAYMENT_AUTHORIZED'])
        }
        
        # Surrender summary
        surrender_df = df_all[df_all['main_category'] == "Submit Surrender"]
        surrender_counts = {
            'submitted': len(surrender_df[surrender_df['status'] == 'SUBMITTED']),
            'received': len(surrender_df[surrender_df['status'] == 'RECEIVED_BY_FINANCE']),
            'first': len(surrender_df[surrender_df['status'] == 'SURRENDER_FIRST_VERIFICATION']),
            'second': len(surrender_df[surrender_df['status'] == 'SURRENDER_SECOND_VERIFICATION']),
            'approval': len(surrender_df[surrender_df['status'] == 'SURRENDER_APPROVAL']),
            'posting': len(surrender_df[surrender_df['status'] == 'SURRENDER_POSTING'])
        }
        
        # Display summary in a clean row
        st.markdown("### 📊 Queue Summary")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**💰 Payment Requests**")
            pay_cols = st.columns(6)
            with pay_cols[0]:
                st.markdown(f"<div class='secondary-card'><div class='secondary-label'>📋 NEW</div><div class='secondary-value'>{payment_counts['submitted']}</div></div>", unsafe_allow_html=True)
            with pay_cols[1]:
                st.markdown(f"<div class='secondary-card'><div class='secondary-label'>📥 RECEIVED</div><div class='secondary-value'>{payment_counts['received']}</div></div>", unsafe_allow_html=True)
            with pay_cols[2]:
                st.markdown(f"<div class='secondary-card'><div class='secondary-label'>⚙️ PREPARED</div><div class='secondary-value'>{payment_counts['prepared']}</div></div>", unsafe_allow_html=True)
            with pay_cols[3]:
                st.markdown(f"<div class='secondary-card'><div class='secondary-label'>✅ VERIFIED</div><div class='secondary-value'>{payment_counts['verified']}</div></div>", unsafe_allow_html=True)
            with pay_cols[4]:
                st.markdown(f"<div class='secondary-card'><div class='secondary-label'>✓ APPROVED</div><div class='secondary-value'>{payment_counts['approved']}</div></div>", unsafe_allow_html=True)
            with pay_cols[5]:
                st.markdown(f"<div class='secondary-card'><div class='secondary-label'>🔐 AUTHORIZED</div><div class='secondary-value'>{payment_counts['authorized']}</div></div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("**📤 Surrender Requests**")
            sur_cols = st.columns(6)
            with sur_cols[0]:
                st.markdown(f"<div class='secondary-card'><div class='secondary-label'>📋 NEW</div><div class='secondary-value'>{surrender_counts['submitted']}</div></div>", unsafe_allow_html=True)
            with sur_cols[1]:
                st.markdown(f"<div class='secondary-card'><div class='secondary-label'>📥 RECEIVED</div><div class='secondary-value'>{surrender_counts['received']}</div></div>", unsafe_allow_html=True)
            with sur_cols[2]:
                st.markdown(f"<div class='secondary-card'><div class='secondary-label'>🔍 FIRST</div><div class='secondary-value'>{surrender_counts['first']}</div></div>", unsafe_allow_html=True)
            with sur_cols[3]:
                st.markdown(f"<div class='secondary-card'><div class='secondary-label'>🔍 SECOND</div><div class='secondary-value'>{surrender_counts['second']}</div></div>", unsafe_allow_html=True)
            with sur_cols[4]:
                st.markdown(f"<div class='secondary-card'><div class='secondary-label'>✓ APPROVAL</div><div class='secondary-value'>{surrender_counts['approval']}</div></div>", unsafe_allow_html=True)
            with sur_cols[5]:
                st.markdown(f"<div class='secondary-card'><div class='secondary-label'>📋 POSTING</div><div class='secondary-value'>{surrender_counts['posting']}</div></div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Create tabs for Payment and Surrender
        tab_payment, tab_surrender = st.tabs(["💰 Payment Requests", "📤 Surrender Requests"])
        
        # ======================================================
        # PAYMENT REQUESTS TAB
        # ======================================================
        with tab_payment:
            payment_pending = payment_df[payment_df['status'].isin(['SUBMITTED', 'RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED'])]
            
            if payment_pending.empty:
                st.info("No pending payment requests.")
            else:
                # Section 1: Pending Confirmation
                section1 = payment_pending[payment_pending['status'] == 'SUBMITTED']
                if not section1.empty:
                    st.markdown(f"""
                    <div class='approval-section'>
                        <h4>📋 LEVEL 1: PENDING CONFIRMATION</h4>
                        <p>Action Required: Review documents, verify checklist, and receive request</p>
                        <span class='approval-count-badge'>{len(section1)} request(s)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for _, req in section1.iterrows():
                        rid = req['id']
                        with st.expander(f"📄 {req['request_number']} - {req['request_type']} - {req['department_name']} - KES {req['amount']:,.2f}", expanded=False):
                            st.caption(f"Submitted: {req['submission_date']}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                checklist_approvals = st.checkbox("✓ Approvals Complete", key=f"pay_chk_app_{rid}")
                                checklist_documents = st.checkbox("✓ Documents Complete", key=f"pay_chk_doc_{rid}")
                            with col2:
                                pwd = st.text_input("Finance Password", type="password", key=f"pay_pwd_{rid}")
                                if st.button(f"📋 Receive Request", key=f"pay_btn_receive_{rid}"):
                                    if checklist_approvals and checklist_documents:
                                        if pwd and verify_finance_password(pwd):
                                            update_request_status(rid, 'RECEIVED_BY_FINANCE', performed_by=st.session_state.username)
                                            st.success(f"Request received!")
                                            st.rerun()
                                        else:
                                            st.error("Incorrect password!")
                                    else:
                                        st.error("Please check both boxes")
                            
                            reason = st.text_input("Return Reason", key=f"pay_txt_return_{rid}")
                            if st.button(f"↩️ Return Request", key=f"pay_btn_return_{rid}"):
                                if reason:
                                    if pwd and verify_finance_password(pwd):
                                        update_request_status(rid, 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                        st.warning(f"Request returned!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Please provide a return reason")
                
                # Section 2: Received
                section2 = payment_pending[payment_pending['status'] == 'RECEIVED_BY_FINANCE']
                if not section2.empty:
                    st.markdown(f"""
                    <div class='approval-section'>
                        <h4>📥 LEVEL 2: RECEIVED</h4>
                        <p>Action Required: Prepare payment for processing</p>
                        <span class='approval-count-badge'>{len(section2)} request(s)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for _, req in section2.iterrows():
                        rid = req['id']
                        with st.expander(f"📄 {req['request_number']} - {req['request_type']} - {req['department_name']} - KES {req['amount']:,.2f}", expanded=False):
                            st.caption(f"Received: {req['date_received']}")
                            
                            pwd = st.text_input("Finance Password", type="password", key=f"pay_pwd_prep_{rid}")
                            if st.button(f"📋 Prepare Payment", key=f"pay_btn_prepare_{rid}"):
                                if pwd and verify_finance_password(pwd):
                                    update_request_status(rid, 'PAYMENT_PREPARED', performed_by=st.session_state.username)
                                    st.success(f"Payment prepared!")
                                    st.rerun()
                                else:
                                    st.error("Incorrect password!")
                
                # Section 3: Prepared
                section3 = payment_pending[payment_pending['status'] == 'PAYMENT_PREPARED']
                if not section3.empty:
                    st.markdown(f"""
                    <div class='approval-section'>
                        <h4>⚙️ LEVEL 3: PREPARED</h4>
                        <p>Action Required: Verify payment details</p>
                        <span class='approval-count-badge'>{len(section3)} request(s)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for _, req in section3.iterrows():
                        rid = req['id']
                        with st.expander(f"📄 {req['request_number']} - {req['request_type']} - {req['department_name']} - KES {req['amount']:,.2f}", expanded=False):
                            pwd = st.text_input("Finance Password", type="password", key=f"pay_pwd_ver_{rid}")
                            if st.button(f"✅ Verify Payment", key=f"pay_btn_verify_{rid}"):
                                if pwd and verify_finance_password(pwd):
                                    update_request_status(rid, 'PAYMENT_VERIFIED', performed_by=st.session_state.username)
                                    st.success(f"Payment verified!")
                                    st.rerun()
                                else:
                                    st.error("Incorrect password!")
                
                # Section 4: Verified
                section4 = payment_pending[payment_pending['status'] == 'PAYMENT_VERIFIED']
                if not section4.empty:
                    st.markdown(f"""
                    <div class='approval-section'>
                        <h4>✅ LEVEL 4: VERIFIED</h4>
                        <p>Action Required: Approve payment</p>
                        <span class='approval-count-badge'>{len(section4)} request(s)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for _, req in section4.iterrows():
                        rid = req['id']
                        with st.expander(f"📄 {req['request_number']} - {req['request_type']} - {req['department_name']} - KES {req['amount']:,.2f}", expanded=False):
                            pwd = st.text_input("Finance Password", type="password", key=f"pay_pwd_app_{rid}")
                            if st.button(f"✅ Approve Payment", key=f"pay_btn_approve_{rid}"):
                                if pwd and verify_finance_password(pwd):
                                    update_request_status(rid, 'PAYMENT_APPROVED', performed_by=st.session_state.username)
                                    st.success(f"Payment approved!")
                                    st.rerun()
                                else:
                                    st.error("Incorrect password!")
                
                # Section 5: Approved
                section5 = payment_pending[payment_pending['status'] == 'PAYMENT_APPROVED']
                if not section5.empty:
                    st.markdown(f"""
                    <div class='approval-section'>
                        <h4>✓ LEVEL 5: APPROVED</h4>
                        <p>Action Required: Authorize payment for release</p>
                        <span class='approval-count-badge'>{len(section5)} request(s)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for _, req in section5.iterrows():
                        rid = req['id']
                        with st.expander(f"📄 {req['request_number']} - {req['request_type']} - {req['department_name']} - KES {req['amount']:,.2f}", expanded=False):
                            pwd = st.text_input("Finance Password", type="password", key=f"pay_pwd_auth_{rid}")
                            if st.button(f"✅ Authorize Payment", key=f"pay_btn_authorize_{rid}"):
                                if pwd and verify_finance_password(pwd):
                                    update_request_status(rid, 'PAYMENT_AUTHORIZED', performed_by=st.session_state.username)
                                    st.success(f"Payment authorized!")
                                    st.rerun()
                                else:
                                    st.error("Incorrect password!")
                
                # Section 6: Authorized
                section6 = payment_pending[payment_pending['status'] == 'PAYMENT_AUTHORIZED']
                if not section6.empty:
                    st.markdown(f"""
                    <div class='approval-section'>
                        <h4>🔐 LEVEL 6: AUTHORIZED</h4>
                        <p>Action Required: Mark as paid and provide payment reference</p>
                        <span class='approval-count-badge'>{len(section6)} request(s)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for _, req in section6.iterrows():
                        rid = req['id']
                        with st.expander(f"📄 {req['request_number']} - {req['request_type']} - {req['department_name']} - KES {req['amount']:,.2f}", expanded=False):
                            payment_ref = st.text_input("Payment Reference", key=f"pay_ref_{rid}")
                            pwd = st.text_input("Finance Password", type="password", key=f"pay_pwd_pay_{rid}")
                            if st.button(f"💰 Mark as Paid", key=f"pay_btn_paid_{rid}"):
                                if payment_ref:
                                    if pwd and verify_finance_password(pwd):
                                        update_request_status(rid, 'PAID', performed_by=st.session_state.username)
                                        update_payment_details(rid, payment_ref)
                                        tat = calculate_tat(req['submission_date'], datetime.now().strftime('%Y-%m-%d'))
                                        st.balloons()
                                        st.success(f"Payment completed! TAT: {tat} working days")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Enter payment reference!")
        
        # ======================================================
        # SURRENDER REQUESTS TAB
        # ======================================================
        with tab_surrender:
            surrender_pending = surrender_df[surrender_df['status'].isin(['SUBMITTED', 'RECEIVED_BY_FINANCE', 'SURRENDER_FIRST_VERIFICATION', 'SURRENDER_SECOND_VERIFICATION', 'SURRENDER_APPROVAL', 'SURRENDER_POSTING'])]
            
            if surrender_pending.empty:
                st.info("No pending surrender requests.")
            else:
                # Section S1: Pending Confirmation
                s_section1 = surrender_pending[surrender_pending['status'] == 'SUBMITTED']
                if not s_section1.empty:
                    st.markdown(f"""
                    <div class='approval-section'>
                        <h4>📋 LEVEL 1: PENDING CONFIRMATION</h4>
                        <p>Action Required: Review documents, verify checklist, and receive surrender</p>
                        <span class='approval-count-badge'>{len(s_section1)} request(s)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for _, req in s_section1.iterrows():
                        rid = req['id']
                        with st.expander(f"📄 {req['request_number']} - Surrender - {req['department_name']} - KES {req['amount']:,.2f}", expanded=False):
                            st.caption(f"Submitted: {req['submission_date']}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                checklist_approvals = st.checkbox("✓ Approvals Complete", key=f"surr_chk_app_{rid}")
                                checklist_documents = st.checkbox("✓ Documents Complete", key=f"surr_chk_doc_{rid}")
                            with col2:
                                pwd = st.text_input("Finance Password", type="password", key=f"surr_pwd_{rid}")
                                if st.button(f"📋 Receive Surrender", key=f"surr_btn_receive_{rid}"):
                                    if checklist_approvals and checklist_documents:
                                        if pwd and verify_finance_password(pwd):
                                            update_request_status(rid, 'RECEIVED_BY_FINANCE', performed_by=st.session_state.username)
                                            st.success(f"Surrender received!")
                                            st.rerun()
                                        else:
                                            st.error("Incorrect password!")
                                    else:
                                        st.error("Please check both boxes")
                            
                            reason = st.text_input("Return Reason", key=f"surr_txt_return_{rid}")
                            if st.button(f"↩️ Return Request", key=f"surr_btn_return_{rid}"):
                                if reason:
                                    if pwd and verify_finance_password(pwd):
                                        update_request_status(rid, 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                        st.warning(f"Request returned!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Please provide a return reason")
                
                # Section S2: Received
                s_section2 = surrender_pending[surrender_pending['status'] == 'RECEIVED_BY_FINANCE']
                if not s_section2.empty:
                    st.markdown(f"""
                    <div class='approval-section'>
                        <h4>📥 LEVEL 2: RECEIVED</h4>
                        <p>Action Required: Perform first verification</p>
                        <span class='approval-count-badge'>{len(s_section2)} request(s)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for _, req in s_section2.iterrows():
                        rid = req['id']
                        with st.expander(f"📄 {req['request_number']} - Surrender - {req['department_name']} - KES {req['amount']:,.2f}", expanded=False):
                            st.caption(f"Received: {req['date_received']}")
                            
                            pwd = st.text_input("Finance Password", type="password", key=f"surr_pwd_first_{rid}")
                            if st.button(f"🔍 First Verification", key=f"surr_btn_first_verify_{rid}"):
                                if pwd and verify_finance_password(pwd):
                                    update_request_status(rid, 'SURRENDER_FIRST_VERIFICATION', performed_by=st.session_state.username)
                                    st.success(f"First verification completed!")
                                    st.rerun()
                                else:
                                    st.error("Incorrect password!")
                
                # Section S3: First Verification Complete
                s_section3 = surrender_pending[surrender_pending['status'] == 'SURRENDER_FIRST_VERIFICATION']
                if not s_section3.empty:
                    st.markdown(f"""
                    <div class='approval-section'>
                        <h4>🔍 LEVEL 3: FIRST VERIFICATION COMPLETE</h4>
                        <p>Action Required: Perform second verification</p>
                        <span class='approval-count-badge'>{len(s_section3)} request(s)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for _, req in s_section3.iterrows():
                        rid = req['id']
                        with st.expander(f"📄 {req['request_number']} - Surrender - {req['department_name']} - KES {req['amount']:,.2f}", expanded=False):
                            pwd = st.text_input("Finance Password", type="password", key=f"surr_pwd_second_{rid}")
                            if st.button(f"🔍 Second Verification", key=f"surr_btn_second_verify_{rid}"):
                                if pwd and verify_finance_password(pwd):
                                    update_request_status(rid, 'SURRENDER_SECOND_VERIFICATION', performed_by=st.session_state.username)
                                    st.success(f"Second verification completed!")
                                    st.rerun()
                                else:
                                    st.error("Incorrect password!")
                
                # Section S4: Second Verification Complete
                s_section4 = surrender_pending[surrender_pending['status'] == 'SURRENDER_SECOND_VERIFICATION']
                if not s_section4.empty:
                    st.markdown(f"""
                    <div class='approval-section'>
                        <h4>🔍 LEVEL 4: SECOND VERIFICATION COMPLETE</h4>
                        <p>Action Required: Approve surrender</p>
                        <span class='approval-count-badge'>{len(s_section4)} request(s)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for _, req in s_section4.iterrows():
                        rid = req['id']
                        with st.expander(f"📄 {req['request_number']} - Surrender - {req['department_name']} - KES {req['amount']:,.2f}", expanded=False):
                            pwd = st.text_input("Finance Password", type="password", key=f"surr_pwd_approve_{rid}")
                            if st.button(f"✅ Approve Surrender", key=f"surr_btn_approve_{rid}"):
                                if pwd and verify_finance_password(pwd):
                                    update_request_status(rid, 'SURRENDER_APPROVAL', performed_by=st.session_state.username)
                                    st.success(f"Surrender approved!")
                                    st.rerun()
                                else:
                                    st.error("Incorrect password!")
                
                # Section S5: Approval
                s_section5 = surrender_pending[surrender_pending['status'] == 'SURRENDER_APPROVAL']
                if not s_section5.empty:
                    st.markdown(f"""
                    <div class='approval-section'>
                        <h4>✓ LEVEL 5: APPROVED</h4>
                        <p>Action Required: Post surrender</p>
                        <span class='approval-count-badge'>{len(s_section5)} request(s)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for _, req in s_section5.iterrows():
                        rid = req['id']
                        with st.expander(f"📄 {req['request_number']} - Surrender - {req['department_name']} - KES {req['amount']:,.2f}", expanded=False):
                            pwd = st.text_input("Finance Password", type="password", key=f"surr_pwd_post_{rid}")
                            if st.button(f"📋 Post Surrender", key=f"surr_btn_post_{rid}"):
                                if pwd and verify_finance_password(pwd):
                                    update_request_status(rid, 'SURRENDER_POSTING', performed_by=st.session_state.username)
                                    st.success(f"Surrender posted!")
                                    st.rerun()
                                else:
                                    st.error("Incorrect password!")
                
                # Section S6: Posting
                s_section6 = surrender_pending[surrender_pending['status'] == 'SURRENDER_POSTING']
                if not s_section6.empty:
                    st.markdown(f"""
                    <div class='approval-section'>
                        <h4>📋 LEVEL 6: POSTING</h4>
                        <p>Action Required: Mark as cleared with reference number</p>
                        <span class='approval-count-badge'>{len(s_section6)} request(s)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for _, req in s_section6.iterrows():
                        rid = req['id']
                        with st.expander(f"📄 {req['request_number']} - Surrender - {req['department_name']} - KES {req['amount']:,.2f}", expanded=False):
                            reference = st.text_input("Reference Number", key=f"surr_ref_{rid}")
                            pwd = st.text_input("Finance Password", type="password", key=f"surr_pwd_clear_{rid}")
                            if st.button(f"✅ Mark as Cleared", key=f"surr_btn_cleared_{rid}"):
                                if reference:
                                    if pwd and verify_finance_password(pwd):
                                        update_request_status(rid, 'CLEARED', performed_by=st.session_state.username)
                                        update_payment_details(rid, reference)
                                        tat = calculate_tat(req['submission_date'], datetime.now().strftime('%Y-%m-%d'))
                                        st.balloons()
                                        st.success(f"Surrender cleared! TAT: {tat} working days")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Enter reference number!")
    else:
        st.error("Access denied. Finance only.")
    
    if st.button("🔄 Refresh This Page", key="approval_refresh"):
        refresh_page()


# ================================================================
# BULK OPERATIONS (PRESERVED)
# ================================================================
elif choice == "⚡ Bulk Operations":
    finance_roles = ["FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER", "FINANCE_ADMIN"]
    if st.session_state.user_role in finance_roles or st.session_state.user_role == "ADMIN":
        st.markdown("<div class='section-header'>⚡ Bulk Operations</div>", unsafe_allow_html=True)
        st.markdown("<p style='color:#6B7280; font-size:0.65rem; margin-bottom:0.8rem;'>Process multiple requests at once to save time</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            bulk_status_filter = st.multiselect(
                "Filter by Status",
                ["SUBMITTED", "RECEIVED_BY_FINANCE", "PAYMENT_PREPARED", "PAYMENT_VERIFIED", "PAYMENT_APPROVED"],
                default=["SUBMITTED"]
            )
        with col2:
            bulk_type_filter = st.multiselect(
                "Filter by Request Type",
                ["Student Payment", "Imprest", "Petty Cash", "Supplier Payment", 
                 "Salary Payment", "Refund Payment", "Direct Payment", "Surrender"],
                default=[]
            )
        with col3:
            departments_list = get_departments()
            dept_names = ["All"] + departments_list['name'].tolist() if not departments_list.empty else ["All"]
            bulk_dept_filter = st.selectbox("Filter by Department", dept_names)
        
        bulk_limit = st.slider("Maximum requests to load", min_value=10, max_value=200, value=50)
        
        if st.button("🔍 Load Eligible Requests", type="primary"):
            dept_param = None if bulk_dept_filter == "All" else bulk_dept_filter
            requests_list = get_bulk_eligible_requests(
                statuses=bulk_status_filter if bulk_status_filter else None,
                request_types=bulk_type_filter if bulk_type_filter else None,
                department=dept_param,
                limit=bulk_limit
            )
            
            if requests_list:
                st.session_state.bulk_requests = requests_list
                st.success(f"✅ Loaded {len(requests_list)} requests")
            else:
                st.warning("No requests found matching the criteria")
        
        if 'bulk_requests' in st.session_state and st.session_state.bulk_requests:
            st.markdown("### Step 2: Select Requests to Process")
            
            df_bulk = pd.DataFrame(st.session_state.bulk_requests)
            df_bulk['Select'] = False
            
            edited_df = st.data_editor(
                df_bulk[['Select', 'request_number', 'request_type', 'department_name', 'amount', 'status']],
                column_config={
                    "Select": st.column_config.CheckboxColumn("Select", default=False),
                    "request_number": "Request Number",
                    "request_type": "Type",
                    "department_name": "Department",
                    "amount": st.column_config.NumberColumn("Amount (KES)", format="KES %.0f"),
                    "status": "Status"
                },
                hide_index=True,
                use_container_width=True,
                key="bulk_selector"
            )
            
            selected_ids = []
            for idx, row in edited_df.iterrows():
                if row['Select']:
                    selected_ids.append(st.session_state.bulk_requests[idx]['id'])
            
            if selected_ids:
                st.markdown(f"<div class='bulk-summary'>📋 {len(selected_ids)} request(s) selected for processing</div>", unsafe_allow_html=True)
                
                st.markdown("### Step 3: Choose Action")
                
                col1, col2 = st.columns(2)
                with col1:
                    bulk_action = st.selectbox(
                        "Action to perform",
                        ["Receive Requests", "Prepare Payment", "Verify Payment", 
                         "Approve Payment", "Authorize Payment", "Mark as Paid", 
                         "Return Requests", "Export to CSV"]
                    )
                
                with col2:
                    if bulk_action == "Mark as Paid":
                        bulk_payment_ref = st.text_input("Payment Reference (will apply to all selected)")
                    elif bulk_action == "Return Requests":
                        bulk_return_reason = st.text_area("Return Reason (will apply to all selected)")
                
                pwd = st.text_input("Finance Password", type="password", key="bulk_pwd")
                
                if st.button(f"▶️ Execute Bulk Action: {bulk_action}", type="primary"):
                    if pwd and verify_finance_password(pwd):
                        action_map = {
                            "Receive Requests": "RECEIVED_BY_FINANCE",
                            "Prepare Payment": "PAYMENT_PREPARED",
                            "Verify Payment": "PAYMENT_VERIFIED",
                            "Approve Payment": "PAYMENT_APPROVED",
                            "Authorize Payment": "PAYMENT_AUTHORIZED",
                            "Mark as Paid": "PAID",
                            "Return Requests": "RETURNED"
                        }
                        
                        if bulk_action in action_map:
                            new_status = action_map[bulk_action]
                            payment_ref = bulk_payment_ref if bulk_action == "Mark as Paid" else None
                            return_reason = bulk_return_reason if bulk_action == "Return Requests" else None
                            
                            with st.spinner(f"Processing {len(selected_ids)} requests..."):
                                success_count, failed_ids = bulk_update_status(
                                    selected_ids, new_status, 
                                    st.session_state.username, st.session_state.user_role,
                                    st.session_state.user_dept,
                                    payment_reference=payment_ref,
                                    finance_comment=return_reason
                                )
                            
                            if success_count > 0:
                                st.success(f"✅ Successfully processed {success_count} requests!")
                                if failed_ids:
                                    st.warning(f"⚠️ Failed to process {len(failed_ids)} requests. Check logs.")
                                st.balloons()
                                del st.session_state.bulk_requests
                                st.rerun()
                            else:
                                st.error("❌ No requests were processed successfully")
                        elif bulk_action == "Export to CSV":
                            export_df = export_bulk_requests(selected_ids)
                            csv = export_df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                "📥 Download Export.csv",
                                csv,
                                f"bulk_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                "text/csv"
                            )
                    else:
                        st.error("❌ Incorrect finance password")
                
                if len(selected_ids) > 20:
                    st.warning(f"⚠️ You are about to process {len(selected_ids)} requests. This may take a moment.")
            else:
                st.info("Please select at least one request to process")
        
        with st.expander("ℹ️ Bulk Operations Guide"):
            st.markdown("""
            **How to use Bulk Operations:**
            1. Filter requests by status, type, or department
            2. Select requests by checking the boxes
            3. Choose an action (Receive, Prepare, Verify, Approve, Authorize, Pay, Return, Export)
            4. Enter Finance Password and click Execute
            """)
    
    if st.button("🔄 Refresh This Page", key="bulk_refresh"):
        refresh_page()


# ================================================================
# REPORTS (PRESERVED)
# ================================================================
elif choice == "📑 Reports":
    st.markdown("<div class='section-header'>📑 Reports</div>", unsafe_allow_html=True)
    
    df = get_reports_data(st.session_state.user_role, st.session_state.user_dept)
    df = filter_by_filters(df, st.session_state.selected_financial_year, 
                          st.session_state.selected_quarter, st.session_state.selected_month,
                          st.session_state.selected_year)
    
    if df.empty:
        st.info("No data available")
    else:
        display_df = pd.DataFrame()
        display_df['Request No.'] = df['request_number']
        display_df['Type'] = df['request_type']
        display_df['Department'] = df['department_name']
        display_df['Reference'] = df.apply(get_reference_number, axis=1)
        display_df['Amount (KES)'] = df['amount'].apply(lambda x: f"{x:,.0f}")
        display_df['Status'] = df['status']
        display_df['TAT (Days)'] = df.apply(lambda x: calculate_tat(x['submission_date'], x['payment_date']) if x['status'] in ['PAID', 'CLEARED'] else calculate_tat(x['submission_date']), axis=1)
        display_df['Submitted'] = df['submission_date']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export to CSV", csv, f"helb_export_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
    
    if st.button("🔄 Refresh This Page", key="reports_refresh"):
        refresh_page()


# ================================================================
# ADMIN PANEL (PRESERVED)
# ================================================================
elif choice == "⚙️ Admin Panel" and st.session_state.user_role == "ADMIN":
    st.markdown("<div class='section-header'>⚙️ Admin Panel</div>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["👥 Users", "🏢 Departments", "📦 Products", "💰 Funders", "📅 Financial Years", "🔐 Finance Settings", "📊 Database Health"])
    
    with tab1:
        st.subheader("👥 User Management")
        users_df = get_all_users()
        st.dataframe(users_df, use_container_width=True, hide_index=True)
        
        with st.expander("🗑️ Delete User"):
            users_list = users_df['username'].tolist() if not users_df.empty else []
            if users_list:
                user_to_delete = st.selectbox("Select user to delete", users_list)
                if st.button("Delete User", type="secondary"):
                    if user_to_delete == st.session_state.username:
                        st.error("❌ Cannot delete your own account!")
                    elif user_to_delete == "admin":
                        st.error("❌ Cannot delete the main admin account!")
                    else:
                        if delete_user(user_to_delete):
                            st.success(f"✅ User '{user_to_delete}' deleted!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete user")
            else:
                st.info("No users available")
        
        with st.expander("➕ Add New User"):
            with st.form("add_user_form"):
                st.markdown("**Basic Information**")
                col1, col2 = st.columns(2)
                with col1:
                    new_username = st.text_input("Username *")
                    new_password = st.text_input("Password", value="password123", type="default")
                with col2:
                    new_full_name = st.text_input("Full Name *")
                    new_role = st.selectbox("Role *", ["DEPARTMENT", "FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER", "FINANCE_ADMIN", "MANAGEMENT", "ADMIN"])
                
                depts = get_departments()
                dept_options = {row['name']: row['id'] for _, row in depts.iterrows()}
                new_department = st.selectbox("Department", ["None"] + list(dept_options.keys()))
                
                st.markdown("---")
                st.markdown("**Finance Permissions (applies to FINANCE_* roles only)**")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    can_receive = st.checkbox("📋 Can Receive Requests")
                with col2:
                    can_process = st.checkbox("⚙️ Can Process Stages")
                with col3:
                    can_release = st.checkbox("💰 Can Release Payments")
                
                st.info("💡 Note: FINANCE_ADMIN automatically gets all permissions regardless of checkboxes")
                
                if st.form_submit_button("Create User"):
                    if not new_username or not new_full_name:
                        st.error("Please fill all required fields (*)")
                    else:
                        dept_id = dept_options.get(new_department) if new_department != "None" else None
                        if new_role == "FINANCE_ADMIN":
                            can_receive = True
                            can_process = True
                            can_release = True
                        
                        success = create_user(new_username, new_password, new_role, dept_id, new_full_name,
                                            1 if can_receive else 0, 1 if can_process else 0, 1 if can_release else 0)
                        if success:
                            st.success(f"✅ User {new_username} created successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Username already exists!")
        
        with st.expander("✏️ Edit User Permissions"):
            users_list = users_df['username'].tolist() if not users_df.empty else []
            if users_list:
                selected_user = st.selectbox("Select user to edit permissions", users_list, key="edit_user_select")
                if selected_user:
                    user_data = get_user_by_username(selected_user)
                    if user_data:
                        current_role = user_data[1]
                        current_can_receive = user_data[5] == 1 if len(user_data) > 5 else False
                        current_can_process = user_data[6] == 1 if len(user_data) > 6 else False
                        current_can_release = user_data[7] == 1 if len(user_data) > 7 else False
                        
                        st.markdown(f"**Editing: {selected_user}** (Role: {current_role})")
                        
                        if current_role in ["FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER", "FINANCE_ADMIN"]:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                new_can_receive = st.checkbox("Can Receive Requests", value=current_can_receive, key="edit_receive")
                            with col2:
                                new_can_process = st.checkbox("Can Process Stages", value=current_can_process, key="edit_process")
                            with col3:
                                new_can_release = st.checkbox("Can Release Payments", value=current_can_release, key="edit_release")
                            
                            if st.button("Update Permissions"):
                                if update_user_permissions(selected_user, new_can_receive, new_can_process, new_can_release):
                                    st.success(f"✅ Permissions updated for {selected_user}")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to update permissions")
                        else:
                            st.info(f"User with role '{current_role}' does not have finance permissions to edit.")
            else:
                st.info("No users available")
    
    with tab2:
        st.subheader("🏢 Department Management")
        depts = get_departments()
        st.dataframe(depts, use_container_width=True, hide_index=True)
        with st.expander("➕ Add New Department"):
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
                        create_department(dept_name, perms)
                        st.rerun()
    
    with tab3:
        st.subheader("📦 Product Management (Lending)")
        products_df = get_products()
        if not products_df.empty:
            for idx, product in products_df.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"• {product['name']} ({product['category']})")
                with col2:
                    if st.button(f"🗑️ Delete", key=f"del_product_{idx}"):
                        conn = sqlite3.connect("helb_data.db")
                        cursor = conn.cursor()
                        cursor.execute("SELECT id FROM products WHERE name = ?", (product['name'],))
                        prod_id = cursor.fetchone()
                        conn.close()
                        if prod_id:
                            delete_product(prod_id[0])
                            st.success(f"Product '{product['name']}' deleted!")
                            st.rerun()
        else:
            st.info("No products added yet.")
        
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
        funders_df = get_funders()
        if not funders_df.empty:
            for _, funder in funders_df.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"• {funder['name']}")
                with col2:
                    if st.button(f"🗑️ Delete", key=f"del_funder_{funder['id']}"):
                        delete_funder(funder['id'])
                        st.success(f"Funder '{funder['name']}' deleted!")
                        st.rerun()
        else:
            st.info("No funders added yet.")
        
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
        
        conn = sqlite3.connect("helb_data.db")
        years_df = pd.read_sql_query("SELECT id, name FROM financial_years WHERE is_active = 1 ORDER BY name DESC", conn)
        conn.close()
        
        if not years_df.empty:
            for _, year in years_df.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"• {year['name']}")
                with col2:
                    if st.button(f"🗑️ Delete", key=f"del_year_{year['id']}"):
                        delete_financial_year(year['id'])
                        st.success(f"Financial Year '{year['name']}' deleted!")
                        st.rerun()
        else:
            st.info("No financial years added yet.")
        
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
        
        conn = sqlite3.connect("helb_data.db")
        sems_df = pd.read_sql_query("SELECT id, name FROM semesters ORDER BY name", conn)
        conn.close()
        
        if not sems_df.empty:
            for _, sem in sems_df.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"• {sem['name']}")
                with col2:
                    if st.button(f"🗑️ Delete", key=f"del_sem_{sem['id']}"):
                        delete_semester(sem['id'])
                        st.success(f"Semester '{sem['name']}' deleted!")
                        st.rerun()
        else:
            st.info("No semesters added yet.")
        
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
        st.text_input("Current Password", value="••••••••", disabled=True)
        with st.form("update_finance_pwd_form"):
            new_password = st.text_input("New Finance Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("Update Finance Password"):
                if new_password and len(new_password) >= 4 and new_password == confirm_password:
                    update_finance_password(new_password)
                    st.success("✅ Finance password updated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Invalid password!")
    
    with tab7:
        st.subheader("📊 Database Health & Capacity Planning")
        health = get_database_health()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Database Size", f"{health['db_size_mb']:.1f} MB")
        with col2:
            st.metric("Total Requests", f"{health['total_requests']:,}")
        with col3:
            st.metric("Audit Logs", f"{health['total_logs']:,}")
        with col4:
            st.metric("Active Users", f"{health['total_users']}")
        
        status_color = "#00843D" if health['status'] == "Healthy" else "#F59E0B" if "Warning" in health['status'] else "#DC3545"
        st.markdown(f"""
        <div class='info-card' style='border-left-color: {status_color};'>
            <strong>System Status:</strong> {health['status']}<br>
            <strong>Recommendation:</strong> {health['recommendation']}
        </div>
        """, unsafe_allow_html=True)
        
        capacity_percent = min(100, (health['db_size_mb'] / 500) * 100)
        gauge_color = "#00843D" if capacity_percent < 50 else "#F59E0B" if capacity_percent < 80 else "#DC3545"
        st.markdown(f"""
        <div class='progress-bar' style='height:20px; background:#E5E7EB;'>
            <div class='progress-fill' style='width:{capacity_percent}%; background:{gauge_color};'></div>
        </div>
        <p style='font-size:0.7rem; margin-top:0.3rem;'>
            {'✅ Healthy - Good capacity' if capacity_percent < 50 else 
             '🟡 Moderate usage - Monitor growth' if capacity_percent < 80 else 
             '⚠️ Near capacity - Plan PostgreSQL migration'}
        </p>
        """, unsafe_allow_html=True)
        
        if capacity_percent > 70:
            with st.expander("📖 PostgreSQL Migration Guide", expanded=True):
                st.markdown("""
                **When to Migrate to PostgreSQL:**
                - Database size exceeds 500MB
                - More than 200,000 requests in the system
                - Experiencing frequent "database is locked" errors
                
                **Migration Steps:**
                1. Install PostgreSQL: `sudo apt install postgresql`
                2. Create database: `createdb helb_db`
                3. Export current data: Use the backup feature
                4. Import to PostgreSQL: Use pgloader or manual import
                5. Update connection string in database.py
                
                **Need Help?** Contact your system administrator for assistance with migration.
                """)
        
        if health['total_requests'] > 100000:
            st.warning("📦 Consider archiving records older than 3 years to improve performance.")
    
    if st.button("🔄 Refresh This Page", key="admin_refresh"):
        refresh_page()


# ================================================================
# CHANGE PASSWORD (PRESERVED)
# ================================================================
elif choice == "🔐 Change Password":
    st.markdown("<div class='section-header'>🔐 Change Password</div>", unsafe_allow_html=True)
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
    
    if st.button("🔄 Refresh This Page", key="pwd_refresh"):
        refresh_page()


# Footer
st.markdown("""
<div class='main-footer'>
    <p>© 2026 Higher Education Loans Board (HELB) | Payment & Surrender Monitoring System v5.0</p>
    <p>Intelligent Search with Predictions | Bulk Operations | Categorized Approval Queue | On-Behalf Submissions</p>
</div>
""", unsafe_allow_html=True)
