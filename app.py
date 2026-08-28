import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date, timedelta
import numpy as np
import calendar
import os
import base64

# ================================================================
# LOAD ENVIRONMENT VARIABLES - CRITICAL FOR PRODUCTION MODE
# ================================================================
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system env

# Set production mode from environment
PRODUCTION_MODE = os.getenv('PRODUCTION_MODE', 'False').lower() == 'true'

if PRODUCTION_MODE:
    print("=" * 60)
    print("⚠️  PRODUCTION MODE ACTIVE - Data protection ENABLED")
    print("=" * 60)

# ================================================================
# IMPORTANT: Initialize database with recovery (replaces init_database)
# ================================================================
from database import (
    safe_init_with_recovery, get_requests, save_request, update_request_status, 
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
    export_bulk_requests, get_database_health, get_sla_from_database,
    get_intelligent_completion_prediction, get_all_request_types,
    add_request_type, update_request_type, delete_request_type, update_sla_days,
    get_backup_list, restore_backup
)
from utils.holidays_ke import working_days_between, add_working_days
from streamlit_option_menu import option_menu

# ================================================================
# DATABASE STATE CHECK - UPDATED FOR SUPABASE
# ================================================================

def check_database_state():
    """Check if database has data before proceeding - prevents data loss"""
    try:
        users_df = get_all_users()
        
        if users_df.empty:
            # Database might be empty (new installation or no data)
            st.warning("⚠️ No users found in the database. This might be a fresh installation.")
            st.info("💡 Please ensure you have run the SQL script to insert default data in Supabase.")
            
            # Show available backups info
            try:
                backups = get_backup_list()
                if backups:
                    st.info("📋 Available backups:")
                    for b in backups[:3]:
                        st.write(f"- {b['filename']} ({b['date']})")
            except Exception as e:
                st.error(f"Error checking backups: {e}")
            
            # Button to check again
            if st.button("🔄 Check Again", type="primary"):
                st.rerun()
            
            # Allow user to continue to login screen
            st.info("If you have inserted default data, click 'Check Again' or refresh the page.")
            return True  # Return True so app doesn't stop
        else:
            st.success(f"✅ Database ready: {len(users_df)} users found")
            return True
            
    except Exception as e:
        st.error(f"❌ Database error: {str(e)}")
        st.info("💡 Please check your DATABASE_URL in .env file or Streamlit secrets.")
        return True  # Return True to allow user to see the error and fix it

# ================================================================
# LOAD HELB LOGO
# ================================================================

def get_helb_logo_base64():
    """Load HELB logo and convert to base64 string for use in HTML"""
    try:
        with open("HELB Logo.png", "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        print("Warning: HELB Logo.png not found. Using emoji fallback.")
        return None
    except Exception as e:
        print(f"Error loading logo: {e}")
        return None

helb_logo_base64 = get_helb_logo_base64()

# Page config
st.set_page_config(
    page_title="HELB Payment & Surrender Monitoring System",
    page_icon="HELB Logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================================================
# RUN DATABASE STATE CHECK BEFORE ANYTHING ELSE - UPDATED FOR SUPABASE
# ================================================================
# For Supabase, just test connection
try:
    users_df = get_all_users()
    print(f"Connected to Supabase. Found {len(users_df)} users")
except Exception as e:
    st.error(f"❌ Database connection error: {str(e)}")
    st.info("💡 Please check your DATABASE_URL in .env file or Streamlit secrets.")
    st.stop()

# Check if database has data (warn but don't stop)
if not check_database_state():
    st.warning("⚠️ Database is empty. Please insert default data in Supabase SQL Editor.")
    st.info("💡 Run the SQL script provided in the documentation to populate default data.")
    # Don't stop - allow user to see the warning

# ================================================================
# CUSTOM CSS - Executive Edition
# ================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Hide Streamlit Cloud management button */
    .stAppDeployButton,
    button[aria-label="Manage app"],
    button:has(svg[data-icon="cloud-upload"]),
    .stStatusWidget,
    [data-testid="stStatusWidget"],
    footer .stDecoration,
    .element-container:has(button[aria-label="Manage app"]) {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    
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
    
    /* Prediction Card Styles */
    .prediction-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.6rem 0.8rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        font-size: 0.7rem;
    }
    .prediction-high {
        background: linear-gradient(135deg, #00843D 0%, #00B347 100%);
    }
    .prediction-medium {
        background: linear-gradient(135deg, #F59E0B 0%, #FFB81C 100%);
    }
    .prediction-low {
        background: linear-gradient(135deg, #6B7280 0%, #9CA3AF 100%);
    }
    .prediction-estimated {
        background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
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

# ================================================================
# FILTER AND HELPER FUNCTIONS (UNCHANGED)
# ================================================================

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
    elif row['request_type'] == "Fare Reimbursement":
        return row.get('fare_reimbursement_details', '-')[:20] if row.get('fare_reimbursement_details') else '-'
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
    
    # Get status from database using the request_id
    request = get_request_by_id(request_id)
    if not request:
        return
    
    status = request.get('status', '')
    
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
    current_stage = status_map.get(status, '')
    
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

# ================================================================
# REQUEST TYPE TAT ANALYZER - SHOWS ALL RECORDS (FIXED)
# ================================================================

def display_tat_by_request_type(data_scope="All Data"):
    """Display TAT analysis grouped by request type - shows ALL records, not just completed"""
    st.markdown("<div class='section-header'>⏱️ Turnaround Time Analysis by Request Type</div>", unsafe_allow_html=True)
    
    # Get all requests
    df_all = get_requests()
    
    if df_all.empty:
        st.info("No data available. Submit some requests first.")
        return
    
    # APPLY ROLE-BASED FILTERING
    finance_roles = ["FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER", "FINANCE_ADMIN"]
    
    if st.session_state.user_role in ["ADMIN", "MANAGEMENT"] + finance_roles:
        # Management and Finance see ALL requests
        df = df_all.copy()
        st.info(f"📊 Showing TAT analysis for ALL departments (Total: {len(df)} records)")
    else:
        # Regular department users see ONLY their department's requests
        df = df_all[df_all['department_name'] == st.session_state.user_dept].copy()
        st.info(f"📊 Showing TAT analysis for {st.session_state.user_dept} department only (Total: {len(df)} records)")
    
    if df.empty:
        st.info(f"No data available for your department. Submit some requests first.")
        return
    
    # Apply date filters
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
        st.info("No data matches your filters.")
        return
    
    # Get SLA from database (real-time)
    sla_map = get_sla_from_database()
    
    results = []
    
    # Process EACH request type - using ALL records (both completed and pending)
    for req_type in df['request_type'].unique():
        type_df = df[df['request_type'] == req_type]
        
        # Count ALL records of this type
        total_records = len(type_df)
        
        # For TAT calculation, use ALL records:
        # - If completed, calculate from submission to payment date
        # - If pending, calculate from submission to today
        tat_values = []
        completed_count = 0
        pending_count = 0
        returned_count = 0
        
        for _, row in type_df.iterrows():
            try:
                if row['status'] in ['PAID', 'CLEARED'] and row.get('payment_date'):
                    # Completed request - calculate TAT to payment date
                    tat = calculate_tat(row['submission_date'], row['payment_date'])
                    completed_count += 1
                elif row['status'] == 'RETURNED':
                    # Returned request - don't include in TAT average
                    returned_count += 1
                    continue
                else:
                    # Pending request - calculate TAT to today
                    tat = calculate_tat(row['submission_date'])
                    pending_count += 1
                
                if tat and tat > 0:
                    tat_values.append(tat)
            except:
                pass
        
        sla_target = sla_map.get(req_type, 5)
        
        if tat_values:
            avg_tat = np.mean(tat_values)
            median_tat = np.median(tat_values)
            min_tat = np.min(tat_values)
            max_tat = np.max(tat_values)
            p95_tat = np.percentile(tat_values, 95)
            
            sla_compliant = sum(1 for t in tat_values if t <= sla_target)
            sla_rate = (sla_compliant / len(tat_values) * 100) if len(tat_values) > 0 else 0
            
            if avg_tat <= sla_target:
                rating = "✅ Excellent"
            elif avg_tat <= sla_target * 1.5:
                rating = "⚠️ Acceptable"
            else:
                rating = "❌ Needs Improvement"
        else:
            avg_tat = 0
            median_tat = 0
            min_tat = 0
            max_tat = 0
            p95_tat = 0
            sla_rate = 0
            rating = "⏳ No data"
        
        results.append({
            'Request Type': req_type,
            'Total Records': total_records,
            'Completed': completed_count,
            'Pending': pending_count,
            'Returned': returned_count,
            'Avg TAT (Days)': round(avg_tat, 1) if avg_tat > 0 else 'N/A',
            'Median (Days)': round(median_tat, 1) if median_tat > 0 else 'N/A',
            'Min (Days)': min_tat if min_tat > 0 else 'N/A',
            'Max (Days)': max_tat if max_tat > 0 else 'N/A',
            'P95 (Days)': round(p95_tat, 1) if p95_tat > 0 else 'N/A',
            'SLA Target': f"{sla_target}d",
            'SLA Compliance %': round(sla_rate, 1) if sla_rate > 0 else 'N/A',
            'Rating': rating,
            '_avg_tat': avg_tat if avg_tat > 0 else 0,
            '_sla_target': sla_target
        })
    
    if not results:
        st.info("No request types found in the data.")
        return
    
    results_df = pd.DataFrame(results)
    # Sort by average TAT (put N/A at the bottom)
    results_df['_avg_tat_sort'] = results_df['_avg_tat'].apply(lambda x: 999 if x == 'N/A' else x)
    results_df = results_df.sort_values('_avg_tat_sort')
    
    st.markdown("### 📊 Performance Metrics by Request Type")
    display_cols = ['Request Type', 'Total Records', 'Completed', 'Pending', 'Returned', 
                    'Avg TAT (Days)', 'Median (Days)', 'P95 (Days)', 'SLA Target', 'SLA Compliance %', 'Rating']
    st.dataframe(results_df[display_cols], use_container_width=True, hide_index=True)
    
    # Filter out rows with no TAT data for charts
    chart_df = results_df[results_df['Avg TAT (Days)'] != 'N/A'].copy()
    
    if not chart_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = go.Figure()
            
            colors = []
            for _, row in chart_df.iterrows():
                if row['_avg_tat'] <= row['_sla_target']:
                    colors.append('#00843D')
                else:
                    colors.append('#DC2626')
            
            fig.add_trace(go.Bar(
                x=chart_df['Request Type'],
                y=chart_df['_avg_tat'],
                marker_color=colors,
                text=chart_df['_avg_tat'].apply(lambda x: f"{x:.1f}d"),
                textposition='outside',
                name='Average TAT'
            ))
            
            fig.add_hline(y=5, line_dash="dash", line_color="#FFB81C", 
                          annotation_text="SLA Threshold (5 days)", annotation_position="top right")
            
            fig.update_layout(
                title="Average Turnaround Time by Request Type",
                xaxis_title="",
                yaxis_title="Days",
                height=400,
                xaxis_tickangle=-45,
                plot_bgcolor='white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Stacked bar for completion status
            fig_stack = go.Figure()
            
            fig_stack.add_trace(go.Bar(
                name='Completed',
                x=results_df['Request Type'],
                y=results_df['Completed'],
                marker_color='#00843D',
                text=results_df['Completed'],
                textposition='inside'
            ))
            
            fig_stack.add_trace(go.Bar(
                name='Pending',
                x=results_df['Request Type'],
                y=results_df['Pending'],
                marker_color='#FFB81C',
                text=results_df['Pending'],
                textposition='inside'
            ))
            
            fig_stack.add_trace(go.Bar(
                name='Returned',
                x=results_df['Request Type'],
                y=results_df['Returned'],
                marker_color='#DC3545',
                text=results_df['Returned'],
                textposition='inside'
            ))
            
            fig_stack.update_layout(
                title="Request Status Distribution by Type",
                xaxis_title="",
                yaxis_title="Number of Requests",
                height=400,
                barmode='stack',
                xaxis_tickangle=-45,
                plot_bgcolor='white'
            )
            
            st.plotly_chart(fig_stack, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📈 Key Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if len(chart_df) > 0:
            fastest = chart_df.iloc[0]
            st.markdown(f"""
            <div class='insight-card'>
                🏆 <strong>Fastest Processing</strong><br>
                {fastest['Request Type']}: {fastest['Avg TAT (Days)']} days avg<br>
                Compliance: {fastest['SLA Compliance %']}%<br>
                Total: {fastest['Total Records']} requests
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='insight-card'>
                🏆 <strong>Fastest Processing</strong><br>
                Complete more requests to see TAT data.
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if len(chart_df) > 0:
            slowest = chart_df.iloc[-1]
            st.markdown(f"""
            <div class='warning-card'>
                ⚠️ <strong>Needs Improvement</strong><br>
                {slowest['Request Type']}: {slowest['Avg TAT (Days)']} days avg<br>
                Compliance: {slowest['SLA Compliance %']}%<br>
                Total: {slowest['Total Records']} requests
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='warning-card'>
                ⚠️ <strong>Needs Improvement</strong><br>
                Complete more requests to see TAT data.
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if len(results_df) > 0:
            # Find highest volume request type
            highest_volume = results_df.loc[results_df['Total Records'].idxmax()]
            st.markdown(f"""
            <div class='insight-card'>
                📊 <strong>Highest Volume</strong><br>
                {highest_volume['Request Type']}: {highest_volume['Total Records']} total requests<br>
                Completed: {highest_volume['Completed']} | Pending: {highest_volume['Pending']}
            </div>
            """, unsafe_allow_html=True)
    
    # Export option
    if len(results_df) > 0:
        export_df = results_df[['Request Type', 'Total Records', 'Completed', 'Pending', 'Returned', 
                                'Avg TAT (Days)', 'Median (Days)', 'Min (Days)', 'Max (Days)', 
                                'P95 (Days)', 'SLA Target', 'SLA Compliance %', 'Rating']]
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export TAT Analysis", csv, f"tat_analysis_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

# Login Screen
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if helb_logo_base64:
            logo_html = f'<img src="data:image/png;base64,{helb_logo_base64}" style="width: 100px; height: auto; margin-bottom: 1rem;">'
        else:
            logo_html = '<div class="login-logo">🏦</div>'
        
        st.markdown(f"""
        <div class='login-container'>
            {logo_html}
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
    if helb_logo_base64:
        logo_html = f'<img src="data:image/png;base64,{helb_logo_base64}" style="width: 40px; height: auto;">'
    else:
        logo_html = '<div style="font-size: 1.3rem;">🏦</div>'
    
    st.markdown(f"""
    <div class='dashboard-header'>
        <div class='header-left'>
            {logo_html}
            <div>
                <h1>HELB Payment & Surrender Monitoring System</h1>
                <p>Real-time analytics | Performance insights | SLA tracking | Intelligent Predictions</p>
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
    if helb_logo_base64:
        logo_html = f'<img src="data:image/png;base64,{helb_logo_base64}" style="width: 60px; height: auto; margin-bottom: 10px;">'
    else:
        logo_html = '<div style="font-size: 1.8rem;">🏦</div>'
    
    st.markdown(f"""
    <div style='text-align: center; padding: 0.5rem 0;'>
        {logo_html}
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
        menu_options = ["📈 Management Dashboard", "📊 TAT by Request Type", "🔍 Search Payment Records", "📑 Reports", "🔐 Change Password"]
    elif st.session_state.user_role == "ADMIN":
        menu_options = ["📊 Department Dashboard", "📈 Management Dashboard", "📊 TAT by Request Type", "🔍 Search Payment Records", 
                       "📝 New Request", "📋 My Requests", "↩️ Returned Requests", "✅ Approval Queue", 
                       "⚡ Bulk Operations", "📑 Reports", "⚙️ Admin Panel", "🔐 Change Password"]
    elif st.session_state.user_role in ["FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER", "FINANCE_ADMIN"]:
        menu_options = ["📊 Department Dashboard", "📈 Management Dashboard", "📊 TAT by Request Type", "🔍 Search Payment Records", 
                       "📝 New Request", "📋 My Requests", "↩️ Returned Requests", "✅ Approval Queue", 
                       "⚡ Bulk Operations", "📑 Reports", "🔐 Change Password"]
    else:
        menu_options = ["📊 Department Dashboard", "📊 TAT by Request Type", "🔍 Search Payment Records", "📝 New Request", 
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
# DEPARTMENT DASHBOARD (UNCHANGED)
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
# MANAGEMENT DASHBOARD (UNCHANGED)
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
        sla_map = get_sla_from_database()
        
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
        
        # KPI Cards
        st.markdown("<div class='kpi-grid'>", unsafe_allow_html=True)
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>📋 TOTAL REQUESTS</div><div class='kpi-value'>{total_requests:,}</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>💰 TOTAL VALUE</div><div class='kpi-value'>KES {total_amount/1e6:.1f}M</div></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>✅ COMPLETION RATE</div><div class='kpi-value'>{completion_rate:.1f}%</div><div class='progress-bar'><div class='progress-fill' style='width:{completion_rate}%;'></div></div></div>", unsafe_allow_html=True)
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
            alert_col1, alert_col2 = st.columns(2)
            with alert_col1:
                if breaches:
                    st.markdown(f"<div class='warning-card'><strong>⚠️ SLA Breaches ({len(breaches)})</strong></div>", unsafe_allow_html=True)
            with alert_col2:
                if long_pending:
                    st.markdown(f"<div class='warning-card'><strong>⏰ Long Pending ({len(long_pending)})</strong></div>", unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Executive Summary", "💰 Payment Analytics", "📤 Surrender Analytics", "🏆 Department Performance", "🚦 Bottlenecks"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                # Horizontal Bar Chart for Status Distribution
                status_counts = df['status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                
                status_colors = {
                    'SUBMITTED': '#FFB81C',
                    'RECEIVED_BY_FINANCE': '#FFA500',
                    'PAYMENT_PREPARED': '#FF8C00',
                    'PAYMENT_VERIFIED': '#00843D',
                    'PAYMENT_APPROVED': '#006030',
                    'PAYMENT_AUTHORIZED': '#00529B',
                    'PAID': '#00B347',
                    'CLEARED': '#00B347',
                    'RETURNED': '#DC3545',
                    'SURRENDER_FIRST_VERIFICATION': '#9C27B0',
                    'SURRENDER_SECOND_VERIFICATION': '#7B1FA2',
                    'SURRENDER_APPROVAL': '#6A1B9A',
                    'SURRENDER_POSTING': '#4A148C'
                }
                
                colors = [status_colors.get(status, '#00843D') for status in status_counts['Status']]
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=status_counts['Status'],
                    x=status_counts['Count'],
                    orientation='h',
                    marker_color=colors,
                    text=status_counts['Count'],
                    textposition='outside',
                    textfont=dict(size=10, color='#1F2937')
                ))
                
                fig.update_layout(
                    title="Status Distribution",
                    height=450,
                    xaxis_title="Number of Requests",
                    yaxis_title="Status",
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    margin=dict(l=120, r=40, t=50, b=40),
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Pie Chart for Request Type Distribution
                type_counts = df['request_type'].value_counts().reset_index()
                type_counts.columns = ['Type', 'Count']
                
                fig2 = go.Figure(data=[go.Pie(
                    labels=type_counts['Type'],
                    values=type_counts['Count'],
                    hole=0.4,
                    marker=dict(colors=px.colors.sequential.Greens_r, line=dict(color='white', width=2)),
                    textinfo='label+percent',
                    textposition='auto',
                    textfont=dict(size=10, color='white')
                )])
                
                fig2.update_layout(
                    title="Request Type Distribution",
                    height=450,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    margin=dict(l=20, r=20, t=50, b=20),
                    showlegend=True,
                    legend=dict(orientation='v', yanchor='top', y=0.5, xanchor='left', x=1.02, font=dict(size=9))
                )
                
                st.plotly_chart(fig2, use_container_width=True)
        
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
                
                # Line Chart for Payment Trends
                payment_df['submission_month'] = pd.to_datetime(payment_df['submission_date']).dt.strftime('%b %Y')
                monthly_payments = payment_df.groupby(['submission_month', 'request_type']).size().reset_index(name='count')
                monthly_payments = monthly_payments.sort_values('submission_month')
                
                request_types = monthly_payments['request_type'].unique()
                color_palette = px.colors.qualitative.Set2 + px.colors.qualitative.Set1
                
                fig = go.Figure()
                
                for i, req_type in enumerate(request_types):
                    type_data = monthly_payments[monthly_payments['request_type'] == req_type]
                    color = color_palette[i % len(color_palette)]
                    
                    fig.add_trace(go.Scatter(
                        x=type_data['submission_month'],
                        y=type_data['count'],
                        mode='lines+markers',
                        name=req_type,
                        line=dict(width=3, color=color, shape='spline'),
                        marker=dict(size=8, color=color, symbol='circle', line=dict(width=1, color='white')),
                        text=type_data['count'],
                        textposition='top center',
                        textfont=dict(size=9, color=color)
                    ))
                
                fig.update_layout(
                    title="Payment Requests Trend by Type",
                    xaxis_title="Month",
                    yaxis_title="Number of Requests",
                    height=450,
                    xaxis_tickangle=-45,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    margin=dict(l=60, r=40, t=50, b=80),
                    hovermode='closest',
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5, font=dict(size=9), bgcolor='rgba(255,255,255,0.9)', bordercolor='#E5E7EB', borderwidth=1)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                if not monthly_payments.empty:
                    latest_month = monthly_payments['submission_month'].iloc[-1]
                    latest_data = monthly_payments[monthly_payments['submission_month'] == latest_month]
                    if not latest_data.empty:
                        top_type = latest_data.loc[latest_data['count'].idxmax(), 'request_type']
                        st.markdown(f"<div class='insight-card'><strong>📈 Trend Insight:</strong> In {latest_month}, <strong>{top_type}</strong> was the most requested payment type with <strong>{latest_data['count'].max()}</strong> requests.</div>", unsafe_allow_html=True)
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
                
                fig_data = pd.DataFrame({
                    'Status': ['Cleared', 'Pending'],
                    'Count': [sur_completed, sur_total - sur_completed]
                })
                fig = px.bar(fig_data, x='Status', y='Count', 
                            title="Surrender Clearance Status",
                            color='Status', color_discrete_sequence=['#00843D', '#FFB81C'],
                            text='Count')
                fig.update_traces(textposition='outside', textfont=dict(size=11, color='#1F2937'))
                fig.update_layout(height=350, plot_bgcolor='white', paper_bgcolor='white')
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
                
                tat_value = avg_tat_dept if not pd.isna(avg_tat_dept) else 15
                tat_score = max(0, min(100, (15 - tat_value) * 6.67))
                score = (completion_rate * 0.6) + (tat_score * 0.4) 
                
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
            fig.update_layout(height=350, plot_bgcolor='white', paper_bgcolor='white')
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
                fig.update_layout(height=400, xaxis_tickangle=-45, plot_bgcolor='white', paper_bgcolor='white')
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
# REQUEST TYPE TAT ANALYSIS 
# ================================================================
elif choice == "📊 TAT by Request Type":
    display_tat_by_request_type(data_scope)

# ================================================================
# ENHANCED SEARCH PAYMENT RECORDS WITH INTELLIGENT PREDICTIONS
# ================================================================
elif choice == "🔍 Search Payment Records":
    st.markdown("<div class='section-header'>🔍 Intelligent Payment Search</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background:#F0F9FF; padding:0.4rem 0.6rem; border-radius:6px; margin-bottom:0.8rem; font-size:0.65rem;'>
        🔎 Search by Request Number, Batch No., Imprest No., Invoice No., Surrender No., Payment Reference, 
        Staff Name, Supplier Name, or Customer Name.<br>
        🧠 <strong>Intelligent Predictions:</strong> Estimated completion dates are calculated using historical patterns 
        and AI-based analysis of similar requests.
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
                
                # Get real-time SLA from database
                sla_map = get_sla_from_database()
                
                for _, row in results.iterrows():
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
                    
                    if row['status'] in ['PAID', 'CLEARED'] and row.get('payment_date'):
                        tat = calculate_tat(row['submission_date'], row['payment_date'])
                        status_badge = f'<span class="status-paid">✅ {row["status"]} (TAT: {tat} days)</span>'
                        is_completed = True
                    else:
                        tat = calculate_tat(row['submission_date'])
                        status_badge = f'<span class="status-pending">⏳ {row["status"]} (Pending: {tat} days)</span>'
                        is_completed = False
                    
                    # Get SLA from database (real-time)
                    sla_days = sla_map.get(row['request_type'], 5)
                    
                    # Generate intelligent prediction
                    predicted_date = None
                    confidence = None
                    reasoning = None
                    
                    if not is_completed:
                        predicted_date, confidence, reasoning = get_intelligent_completion_prediction(
                            row['id'], row['request_type'], row['status'], tat, sla_days
                        )
                    
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
                    
                    ref_number = get_reference_number(row)
                    
                    with st.expander(f"📄 {row['request_number']} - {row['request_type']} - {row['department_name']}", expanded=False):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.markdown(f"**Status:** {status_badge}", unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"**Risk Level:** <span style='color:{risk_color}; font-weight:bold;'>{risk_level}</span>", unsafe_allow_html=True)
                        with col3:
                            if not is_completed and predicted_date:
                                day_name = predicted_date.strftime('%A')
                                # Color code confidence
                                confidence_class = "prediction-high" if confidence == "High" else "prediction-medium" if confidence == "Medium" else "prediction-estimated"
                                st.markdown(f"""
                                <div class='prediction-card {confidence_class}' style='padding:0.4rem;'>
                                    <strong>📅 Estimated Completion:</strong><br>
                                    {predicted_date.strftime('%d %b %Y')} ({day_name})<br>
                                    <span style='font-size:0.55rem;'>🤖 {confidence} Confidence</span>
                                </div>
                                """, unsafe_allow_html=True)
                            elif is_completed and row.get('payment_date'):
                                st.markdown(f"**✅ Completed:** {row['payment_date']}")
                        
                        st.markdown("---")
                        
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
                                progress_pct = min(100, (tat / sla_days) * 100)
                                bar_color = "#DC3545" if progress_pct > 100 else "#F59E0B" if progress_pct > 80 else "#00843D"
                                st.markdown(f"""
                                <div class='progress-bar' style='height:6px; background:#E5E7EB;'>
                                    <div class='progress-fill' style='width:{min(100, progress_pct)}%; background:{bar_color};'></div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        if not is_completed and reasoning:
                            st.markdown(f"<div class='info-card' style='font-size:0.6rem; margin-top:0.3rem;'>💡 <strong>Prediction Reasoning:</strong> {reasoning}</div>", unsafe_allow_html=True)
                        
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
                        if row.get('fare_reimbursement_details'):
                            detail_items.append(("Fare Reimbursement", row['fare_reimbursement_details'][:50]))
                        
                        for i, (label, value) in enumerate(detail_items[:8]):
                            with details_cols[i % 4]:
                                st.markdown(f"**{label}:** {value}")
                        
                        st.markdown("---")
                        st.markdown("**📊 Similar Requests Performance**")
                        
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
                            
                            avg_sim_tat = similar_completed.apply(
                                lambda x: calculate_tat(x['submission_date'], x['payment_date']), axis=1
                            ).mean()
                            st.caption(f"📈 Average TAT for similar requests: {avg_sim_tat:.1f} days (SLA: {sla_days} days)")
                        else:
                            st.caption("No completed similar requests found for comparison.")
                        
                        st.markdown("---")
                        st.markdown("**📅 Progress Timeline**")
                        
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
                        
                        current_index = 0
                        status_order = [s['status_key'] for s in stages]
                        if row['status'] in status_order:
                            current_index = status_order.index(row['status'])
                        
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
                        
                        if can_see_logs:
                            with st.expander("📜 View Full Transaction History"):
                                display_transaction_logs(row['id'])
                        else:
                            st.caption("📜 Full transaction history is available to Finance and Management only.")
            else:
                st.warning("No request matching your search criteria, has been submitted to Finance.")
        else:
            st.info("Please enter a search term.")
    
    if st.button("🔄 Refresh This Page", key="search_refresh"):
        refresh_page()


# ================================================================
# NEW REQUEST (UPDATED - WITH ON-BEHALF SUBMISSION AND FARE REIMBURSEMENT)
# ================================================================
elif choice == "📝 New Request":
    st.markdown("<div class='section-header'>📝 Create New Request</div>", unsafe_allow_html=True)
    
    # Check if user is Finance Admin (can submit on behalf of other departments)
    finance_admin_roles = ["FINANCE_ADMIN", "ADMIN"]
    can_submit_on_behalf = st.session_state.user_role in finance_admin_roles
    
    # Department selection for Finance Admins
    selected_dept = st.session_state.user_dept
    if can_submit_on_behalf:
        departments_list = get_departments()
        dept_options = ["Same as my department"] + departments_list['name'].tolist() if not departments_list.empty else ["Same as my department"]
        dept_choice = st.selectbox("Submitting for Department:", dept_options)
        if dept_choice != "Same as my department":
            selected_dept = dept_choice
            st.info(f"📝 Submitting request on behalf of: **{selected_dept}**")
    
    allowed_main_categories = get_allowed_main_categories(st.session_state.user_role, selected_dept)
    if not allowed_main_categories:
        st.error("Your role does not have permission to submit requests.")
    else:
        main_category = st.radio("What would you like to do?", allowed_main_categories, horizontal=True)
        st.markdown("---")
        allowed_types = get_allowed_request_types(st.session_state.user_role, selected_dept, main_category)
        if not allowed_types:
            st.error("No request types available.")
        else:
            selected_type = st.selectbox("Select Request Type", allowed_types)
            st.markdown("---")
            
            # Get department_id for selected department from database
            dept_df = get_departments()
            dept_id = None
            if not dept_df.empty:
                dept_row = dept_df[dept_df['name'] == selected_dept]
                if not dept_row.empty:
                    dept_id = dept_row.iloc[0]['id']
            if dept_id is None:
                dept_id = st.session_state.user_dept_id
            
            # Student Payment - Regular (Lending)
            if main_category == "Submit Payment Request" and selected_type == "Student Payment" and selected_dept != "External Resource Mobilization":
                products = get_products()
                product_list = products['name'].tolist() if not products.empty else ["Undergraduate", "TVET", "Jielimishe"]
                product_type = st.selectbox("Product Type", product_list)
                with st.form(key="student_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=selected_dept, disabled=True)
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
                                'department_id': dept_id, 'department_name': selected_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'batch_no': batch_no, 'product_type': product_type, 'semester': semester,
                                'payment_type': payment_category, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted for {selected_dept}!")
                            st.balloons()
            
            # Student Payment - ERM
            elif main_category == "Submit Payment Request" and selected_type == "Student Payment" and selected_dept == "External Resource Mobilization":
                with st.form(key="erm_student_form"):
                    st.subheader("🎓 Student Payment Details (Partner Funds)")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=selected_dept, disabled=True)
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
                                'department_id': dept_id, 'department_name': selected_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'batch_no': batch_no, 'funder_name': funder_name,
                                'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted for {selected_dept}!")
                            st.balloons()
            
            # Imprest
            elif main_category == "Submit Payment Request" and selected_type == "Imprest":
                with st.form(key="imprest_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=selected_dept, disabled=True)
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
                                'department_id': dept_id, 'department_name': selected_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'imprest_no': imprest_no, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted for {selected_dept}!")
                            st.balloons()
            
            # Petty Cash
            elif main_category == "Submit Payment Request" and selected_type == "Petty Cash":
                with st.form(key="petty_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=selected_dept, disabled=True)
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
                                'department_id': dept_id, 'department_name': selected_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'imprest_no': petty_cash_no, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted for {selected_dept}!")
                            st.balloons()
            
            # Direct Payment
            elif main_category == "Submit Payment Request" and selected_type == "Direct Payment":
                with st.form(key="direct_form"):
                    st.subheader("💸 Direct Payment Details")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=selected_dept, disabled=True)
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
                                'department_id': dept_id, 'department_name': selected_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'direct_payment_details': direct_payment_details, 'invoice_no': invoice_no,
                                'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted for {selected_dept}!")
                            st.balloons()
            
            # Supplier Payment
            elif main_category == "Submit Payment Request" and selected_type == "Supplier Payment":
                with st.form(key="supplier_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=selected_dept, disabled=True)
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
                                'department_id': dept_id, 'department_name': selected_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'invoice_no': invoice_no, 'supplier_name': supplier_name, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted for {selected_dept}!")
                            st.balloons()
            
            # Salary Payment
            elif main_category == "Submit Payment Request" and selected_type == "Salary Payment":
                with st.form(key="salary_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=selected_dept, disabled=True)
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
                                'department_id': dept_id, 'department_name': selected_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'financial_year': financial_year, 'salary_month': salary_month,
                                'salary_year': salary_year, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted for {selected_dept}!")
                            st.balloons()
            
            # Refund Payment
            elif main_category == "Submit Payment Request" and selected_type == "Refund Payment":
                with st.form(key="refund_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=selected_dept, disabled=True)
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
                                'department_id': dept_id, 'department_name': selected_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'financial_year': financial_year, 'imprest_no': refund_id,
                                'customer_name': customer_name, 'customer_id': customer_id, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted for {selected_dept}!")
                            st.balloons()
            
            # Mileage Claim
            elif main_category == "Submit Payment Request" and selected_type == "Mileage Claim":
                with st.form(key="mileage_form"):
                    st.subheader("⛽ Mileage Claim Details")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=selected_dept, disabled=True)
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
                                'department_id': dept_id, 'department_name': selected_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'mileage_claim_details': mileage_claim_details, 'staff_name': staff_name,
                                'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted for {selected_dept}!")
                            st.balloons()
            
            # Staff Training
            elif main_category == "Submit Payment Request" and selected_type == "Staff Training":
                with st.form(key="training_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=selected_dept, disabled=True)
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
                                'department_id': dept_id, 'department_name': selected_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'training_details': training_details, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted for {selected_dept}!")
                            st.balloons()
            
            # Professional Body
            elif main_category == "Submit Payment Request" and selected_type == "Professional Body":
                with st.form(key="professional_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=selected_dept, disabled=True)
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
                                'department_id': dept_id, 'department_name': selected_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'professional_body': professional_body, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted for {selected_dept}!")
                            st.balloons()
            
            # Fare Reimbursement (NEW)
            elif main_category == "Submit Payment Request" and selected_type == "Fare Reimbursement":
                with st.form(key="fare_reimbursement_form"):
                    st.subheader("🚕 Fare Reimbursement Details")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=selected_dept, disabled=True)
                    with col2:
                        st.date_input("Submission Date", value=datetime.today(), disabled=True)
                    
                    staff_name = st.text_input("Staff Name *")
                    col1, col2 = st.columns(2)
                    with col1:
                        journey_from = st.text_input("Journey From *")
                    with col2:
                        journey_to = st.text_input("Journey To *")
                    
                    journey_purpose = st.text_area("Purpose of Journey *")
                    journey_date = st.date_input("Date of Journey *", value=datetime.today())
                    amount = st.number_input("Amount Claimed (KShs.)", min_value=0.0, format="%.2f", step=100.0)
                    financial_years = get_financial_years()
                    financial_year = st.selectbox("Financial Year", financial_years if financial_years else ["2025/2026", "2026/2027"])
                    payment_description = st.text_area("Additional Notes (Optional)")
                    
                    fare_details = f"From: {journey_from} | To: {journey_to} | Purpose: {journey_purpose} | Date: {journey_date.strftime('%Y-%m-%d')}"
                    
                    if st.form_submit_button("Submit"):
                        if not staff_name or not journey_from or not journey_to or not journey_purpose or amount <= 0:
                            st.error("Please fill all required fields (*)")
                        else:
                            request_data = {
                                'main_category': main_category, 'request_type': selected_type,
                                'department_id': dept_id, 'department_name': selected_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': payment_description or fare_details,
                                'financial_year': financial_year,
                                'fare_reimbursement_details': fare_details,
                                'staff_name': staff_name,
                                'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Fare Reimbursement request {request_number} submitted for {selected_dept}!")
                            st.balloons()
            
            # Surrender
            elif main_category == "Submit Surrender":
                with st.form(key="surrender_form"):
                    st.subheader("📤 Surrender Details")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Department", value=selected_dept, disabled=True)
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
                                'department_id': dept_id, 'department_name': selected_dept,
                                'submitted_by': st.session_state.username,
                                'amount': amount,
                                'payment_description': payment_description, 'financial_year': financial_year,
                                'surrender_number': surrender_no, 'staff_name': staff_name, 'status': 'SUBMITTED'
                            }
                            request_number = save_request(request_data)
                            st.success(f"✅ Request {request_number} submitted for {selected_dept}!")
                            st.balloons()
    
    if st.button("🔄 Refresh This Page", key="new_refresh"):
        refresh_page()


# ================================================================
# MY REQUESTS (UNCHANGED)
# ================================================================
elif choice == "📋 My Requests":
    st.markdown("<div class='section-header'>📋 My Requests</div>", unsafe_allow_html=True)
    
    df_all = get_requests()
    
    if df_all.empty:
        st.info("No requests found in the database.")
    else:
        user_requests = df_all[df_all['submitted_by'] == st.session_state.username]
        if user_requests.empty:
            st.info(f"You haven't submitted any requests yet.")
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
# RETURNED REQUESTS (UNCHANGED)
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
                    elif req['request_type'] == "Fare Reimbursement":
                        corrected_staff = st.text_input("Staff Name", value=req.get('staff_name', ''))
                        corrected_amount = st.number_input("Amount (KShs.)", value=float(req['amount']), min_value=0.0, step=100.0)
                        corrected_description = st.text_area("Fare Details", value=req.get('fare_reimbursement_details', ''))
                        correction_data = {
                            'staff_name': corrected_staff,
                            'amount': corrected_amount,
                            'fare_reimbursement_details': corrected_description
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
# APPROVAL QUEUE (UNCHANGED)
# ================================================================
elif choice == "✅ Approval Queue":
    finance_roles = ["FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER", "FINANCE_ADMIN"]
    if st.session_state.user_role in finance_roles or st.session_state.user_role == "ADMIN" or st.session_state.is_finance:
        st.markdown("<div class='section-header'>✅ Approval Queue</div>", unsafe_allow_html=True)
        
        df_all = get_requests()
        
        payment_df = df_all[df_all['main_category'] == "Submit Payment Request"]
        payment_counts = {
            'submitted': len(payment_df[payment_df['status'] == 'SUBMITTED']),
            'received': len(payment_df[payment_df['status'] == 'RECEIVED_BY_FINANCE']),
            'prepared': len(payment_df[payment_df['status'] == 'PAYMENT_PREPARED']),
            'verified': len(payment_df[payment_df['status'] == 'PAYMENT_VERIFIED']),
            'approved': len(payment_df[payment_df['status'] == 'PAYMENT_APPROVED']),
            'authorized': len(payment_df[payment_df['status'] == 'PAYMENT_AUTHORIZED'])
        }
        
        surrender_df = df_all[df_all['main_category'] == "Submit Surrender"]
        surrender_counts = {
            'submitted': len(surrender_df[surrender_df['status'] == 'SUBMITTED']),
            'received': len(surrender_df[surrender_df['status'] == 'RECEIVED_BY_FINANCE']),
            'first': len(surrender_df[surrender_df['status'] == 'SURRENDER_FIRST_VERIFICATION']),
            'second': len(surrender_df[surrender_df['status'] == 'SURRENDER_SECOND_VERIFICATION']),
            'approval': len(surrender_df[surrender_df['status'] == 'SURRENDER_APPROVAL']),
            'posting': len(surrender_df[surrender_df['status'] == 'SURRENDER_POSTING'])
        }
        
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
        
        tab_payment, tab_surrender = st.tabs(["💰 Payment Requests", "📤 Surrender Requests"])
        
        with tab_payment:
            payment_pending = payment_df[payment_df['status'].isin(['SUBMITTED', 'RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED'])]
            
            if payment_pending.empty:
                st.info("No pending payment requests.")
            else:
                # Section 1: SUBMITTED
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
                            
                            st.markdown("---")
                            st.markdown("**Return Request**")
                            reason = st.text_input("Return Reason", key=f"pay_txt_return_{rid}")
                            pwd_return = st.text_input("Finance Password", type="password", key=f"pay_pwd_return_{rid}")
                            if st.button(f"↩️ Return Request", key=f"pay_btn_return_{rid}"):
                                if reason:
                                    if pwd_return and verify_finance_password(pwd_return):
                                        update_request_status(rid, 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                        st.warning(f"Request returned!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Please provide a return reason")
                
                # Section 2: RECEIVED_BY_FINANCE
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
                            
                            st.markdown("---")
                            st.markdown("**Return Request**")
                            reason = st.text_input("Return Reason", key=f"pay_txt_return2_{rid}")
                            pwd_return = st.text_input("Finance Password", type="password", key=f"pay_pwd_return2_{rid}")
                            if st.button(f"↩️ Return Request", key=f"pay_btn_return2_{rid}"):
                                if reason:
                                    if pwd_return and verify_finance_password(pwd_return):
                                        update_request_status(rid, 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                        st.warning(f"Request returned!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Please provide a return reason")
                
                # Section 3: PAYMENT_PREPARED
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
                            if st.button(f"✅ Mark as Verified", key=f"pay_btn_verify_{rid}"):
                                if pwd and verify_finance_password(pwd):
                                    update_request_status(rid, 'PAYMENT_VERIFIED', performed_by=st.session_state.username)
                                    st.success(f"Payment verified!")
                                    st.rerun()
                                else:
                                    st.error("Incorrect password!")
                            
                            st.markdown("---")
                            st.markdown("**Return Request**")
                            reason = st.text_input("Return Reason", key=f"pay_txt_return3_{rid}")
                            pwd_return = st.text_input("Finance Password", type="password", key=f"pay_pwd_return3_{rid}")
                            if st.button(f"↩️ Return Request", key=f"pay_btn_return3_{rid}"):
                                if reason:
                                    if pwd_return and verify_finance_password(pwd_return):
                                        update_request_status(rid, 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                        st.warning(f"Request returned!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Please provide a return reason")
                
                # Section 4: PAYMENT_VERIFIED
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
                            if st.button(f"✅ Mark as Approved", key=f"pay_btn_approve_{rid}"):
                                if pwd and verify_finance_password(pwd):
                                    update_request_status(rid, 'PAYMENT_APPROVED', performed_by=st.session_state.username)
                                    st.success(f"Payment approved!")
                                    st.rerun()
                                else:
                                    st.error("Incorrect password!")
                            
                            st.markdown("---")
                            st.markdown("**Return Request**")
                            reason = st.text_input("Return Reason", key=f"pay_txt_return4_{rid}")
                            pwd_return = st.text_input("Finance Password", type="password", key=f"pay_pwd_return4_{rid}")
                            if st.button(f"↩️ Return Request", key=f"pay_btn_return4_{rid}"):
                                if reason:
                                    if pwd_return and verify_finance_password(pwd_return):
                                        update_request_status(rid, 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                        st.warning(f"Request returned!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Please provide a return reason")
                
                # Section 5: PAYMENT_APPROVED
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
                            if st.button(f"✅ Mark as Authorized", key=f"pay_btn_authorize_{rid}"):
                                if pwd and verify_finance_password(pwd):
                                    update_request_status(rid, 'PAYMENT_AUTHORIZED', performed_by=st.session_state.username)
                                    st.success(f"Payment authorized!")
                                    st.rerun()
                                else:
                                    st.error("Incorrect password!")
                            
                            st.markdown("---")
                            st.markdown("**Return Request**")
                            reason = st.text_input("Return Reason", key=f"pay_txt_return5_{rid}")
                            pwd_return = st.text_input("Finance Password", type="password", key=f"pay_pwd_return5_{rid}")
                            if st.button(f"↩️ Return Request", key=f"pay_btn_return5_{rid}"):
                                if reason:
                                    if pwd_return and verify_finance_password(pwd_return):
                                        update_request_status(rid, 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                        st.warning(f"Request returned!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Please provide a return reason")
                
                # Section 6: PAYMENT_AUTHORIZED
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
                            
                            st.markdown("---")
                            st.markdown("**Return Request**")
                            reason = st.text_input("Return Reason", key=f"pay_txt_return6_{rid}")
                            pwd_return = st.text_input("Finance Password", type="password", key=f"pay_pwd_return6_{rid}")
                            if st.button(f"↩️ Return Request", key=f"pay_btn_return6_{rid}"):
                                if reason:
                                    if pwd_return and verify_finance_password(pwd_return):
                                        update_request_status(rid, 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                        st.warning(f"Request returned!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Please provide a return reason")
        
        with tab_surrender:
            surrender_pending = surrender_df[surrender_df['status'].isin(['SUBMITTED', 'RECEIVED_BY_FINANCE', 'SURRENDER_FIRST_VERIFICATION', 'SURRENDER_SECOND_VERIFICATION', 'SURRENDER_APPROVAL', 'SURRENDER_POSTING'])]
            
            if surrender_pending.empty:
                st.info("No pending surrender requests.")
            else:
                # Section S1: SUBMITTED
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
                            
                            st.markdown("---")
                            st.markdown("**Return Request**")
                            reason = st.text_input("Return Reason", key=f"surr_txt_return_{rid}")
                            pwd_return = st.text_input("Finance Password", type="password", key=f"surr_pwd_return_{rid}")
                            if st.button(f"↩️ Return Request", key=f"surr_btn_return_{rid}"):
                                if reason:
                                    if pwd_return and verify_finance_password(pwd_return):
                                        update_request_status(rid, 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                        st.warning(f"Request returned!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Please provide a return reason")
                
                # Section S2: RECEIVED_BY_FINANCE
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
                            
                            st.markdown("---")
                            st.markdown("**Return Request**")
                            reason = st.text_input("Return Reason", key=f"surr_txt_return2_{rid}")
                            pwd_return = st.text_input("Finance Password", type="password", key=f"surr_pwd_return2_{rid}")
                            if st.button(f"↩️ Return Request", key=f"surr_btn_return2_{rid}"):
                                if reason:
                                    if pwd_return and verify_finance_password(pwd_return):
                                        update_request_status(rid, 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                        st.warning(f"Request returned!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Please provide a return reason")
                
                # Section S3: SURRENDER_FIRST_VERIFICATION
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
                            
                            st.markdown("---")
                            st.markdown("**Return Request**")
                            reason = st.text_input("Return Reason", key=f"surr_txt_return3_{rid}")
                            pwd_return = st.text_input("Finance Password", type="password", key=f"surr_pwd_return3_{rid}")
                            if st.button(f"↩️ Return Request", key=f"surr_btn_return3_{rid}"):
                                if reason:
                                    if pwd_return and verify_finance_password(pwd_return):
                                        update_request_status(rid, 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                        st.warning(f"Request returned!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Please provide a return reason")
                
                # Section S4: SURRENDER_SECOND_VERIFICATION
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
                            
                            st.markdown("---")
                            st.markdown("**Return Request**")
                            reason = st.text_input("Return Reason", key=f"surr_txt_return4_{rid}")
                            pwd_return = st.text_input("Finance Password", type="password", key=f"surr_pwd_return4_{rid}")
                            if st.button(f"↩️ Return Request", key=f"surr_btn_return4_{rid}"):
                                if reason:
                                    if pwd_return and verify_finance_password(pwd_return):
                                        update_request_status(rid, 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                        st.warning(f"Request returned!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Please provide a return reason")
                
                # Section S5: SURRENDER_APPROVAL
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
                            
                            st.markdown("---")
                            st.markdown("**Return Request**")
                            reason = st.text_input("Return Reason", key=f"surr_txt_return5_{rid}")
                            pwd_return = st.text_input("Finance Password", type="password", key=f"surr_pwd_return5_{rid}")
                            if st.button(f"↩️ Return Request", key=f"surr_btn_return5_{rid}"):
                                if reason:
                                    if pwd_return and verify_finance_password(pwd_return):
                                        update_request_status(rid, 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                        st.warning(f"Request returned!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Please provide a return reason")
                
                # Section S6: SURRENDER_POSTING
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
                            
                            st.markdown("---")
                            st.markdown("**Return Request**")
                            reason = st.text_input("Return Reason", key=f"surr_txt_return6_{rid}")
                            pwd_return = st.text_input("Finance Password", type="password", key=f"surr_pwd_return6_{rid}")
                            if st.button(f"↩️ Return Request", key=f"surr_btn_return6_{rid}"):
                                if reason:
                                    if pwd_return and verify_finance_password(pwd_return):
                                        update_request_status(rid, 'RETURNED', return_reason=reason, performed_by=st.session_state.username)
                                        st.warning(f"Request returned!")
                                        st.rerun()
                                    else:
                                        st.error("Incorrect password!")
                                else:
                                    st.error("Please provide a return reason")
    else:
        st.error("Access denied. Finance only.")
    
    if st.button("🔄 Refresh This Page", key="approval_refresh"):
        refresh_page()


# ================================================================
# BULK OPERATIONS (UNCHANGED)
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
                 "Salary Payment", "Refund Payment", "Direct Payment", "Surrender", "Fare Reimbursement"],
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
# REPORTS (UNCHANGED)
# ================================================================
elif choice == "📑 Reports":
    st.markdown("<div class='section-header'>📑 Reports</div>", unsafe_allow_html=True)
    
    df_raw = get_requests()
    
    if df_raw.empty:
        st.info("No data available in the database.")
    else:
        df = filter_by_filters(df_raw, st.session_state.selected_financial_year, 
                              st.session_state.selected_quarter, st.session_state.selected_month,
                              st.session_state.selected_year)
        
        finance_roles = ["FINANCE_RECEIVER", "FINANCE_PROCESSOR", "FINANCE_RELEASER", "FINANCE_ADMIN"]
        if st.session_state.user_role not in ["ADMIN", "MANAGEMENT"] + finance_roles:
            df = df[df['department_name'] == st.session_state.user_dept]
        
        if df.empty:
            st.info("No data matches your current filters and permissions.")
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
# ADMIN PANEL (UNCHANGED)
# ================================================================
elif choice == "⚙️ Admin Panel" and st.session_state.user_role == "ADMIN":
    st.markdown("<div class='section-header'>⚙️ Admin Panel</div>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(["👥 Users", "🏢 Departments", "📦 Products", "💰 Funders", "📅 Financial Years", "🔐 Finance Settings", "📊 Database Health", "📋 SLA Config", "📝 Request Types"])
    
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
                        if delete_product(product['id']):
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
        
        years_df = get_financial_years()
        
        if years_df:
            for year_name in years_df:
                st.write(f"• {year_name}")
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
        
        sems = get_semesters()
        
        if sems:
            for sem in sems:
                st.write(f"• {sem}")
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
        
        if health['total_requests'] > 100000:
            st.warning("📦 Consider archiving records older than 3 years to improve performance.")
    
    with tab8:
        st.subheader("📋 SLA Configuration (Turnaround Time Targets)")
        st.markdown("Configure Service Level Agreement (SLA) targets for each request type")
        st.info("💡 **SLA Target** = Maximum allowed working days for completion. TAT exceeding this is a breach.")
        
        sla_configs = get_all_request_types()
        
        if not sla_configs:
            st.warning("No SLA configurations found. Please check database.")
        else:
            sla_data = []
            for item in sla_configs:
                req_type = item['request_type']
                sla_days = item['sla_days']
                if sla_days <= 3:
                    color = "#00843D"
                elif sla_days <= 5:
                    color = "#FFB81C"
                else:
                    color = "#F59E0B"
                
                sla_data.append({
                    'Request Type': req_type,
                    'Current SLA (Days)': sla_days,
                    'Priority': '🔴 High' if sla_days <= 3 else '🟡 Medium' if sla_days <= 5 else '🟢 Low'
                })
            
            sla_df = pd.DataFrame(sla_data)
            st.dataframe(sla_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("### ✏️ Update SLA Values")
            
            col1, col2 = st.columns(2)
            with col1:
                request_type_to_update = st.selectbox("Select Request Type", [item['request_type'] for item in sla_configs])
                current_value = next((item['sla_days'] for item in sla_configs if item['request_type'] == request_type_to_update), 5)
                st.caption(f"Current value: **{current_value} days**")
            
            with col2:
                new_sla_days = st.number_input(
                    "New SLA Target (Days)", 
                    min_value=1, 
                    max_value=30, 
                    value=current_value, 
                    step=1,
                    help="Number of working days allowed for completion"
                )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Update SLA", type="primary"):
                    if update_sla_days(request_type_to_update, new_sla_days):
                        st.success(f"✅ Updated {request_type_to_update} SLA to {new_sla_days} days")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Failed to update SLA")
            
            st.markdown("---")
            st.markdown("### 📊 SLA Impact Analysis")
            st.markdown("""
            **How SLA affects the system:**
            
            | Feature | How SLA is used |
            |---------|-----------------|
            | 🔍 Search Records | Shows risk levels (Critical/High/Medium/Low) based on SLA breach |
            | 📈 Management Dashboard | Calculates SLA compliance percentage |
            | 📊 TAT Analysis | Compares actual TAT against SLA targets |
            | 🚨 Alerts | Flags requests approaching or exceeding SLA |
            | 🤖 Intelligent Predictions | Estimated completion dates based on historical data and SLA |
            
            **Color Coding:**
            - 🟢 Green: Within SLA (Good)
            - 🟡 Yellow: At risk (>80% of SLA)
            - 🔴 Red: SLA Breach
            """)
            
            sla_for_chart = [item['sla_days'] for item in sla_configs]
            types_for_chart = [item['request_type'] for item in sla_configs]
            
            fig = go.Figure()
            colors = ['#00843D' if x <= 3 else '#FFB81C' if x <= 5 else '#F59E0B' for x in sla_for_chart]
            
            fig.add_trace(go.Bar(
                x=types_for_chart,
                y=sla_for_chart,
                marker_color=colors,
                text=sla_for_chart,
                textposition='outside',
                name='SLA Days'
            ))
            
            fig.update_layout(
                title="Current SLA Distribution by Request Type",
                xaxis_title="Request Type",
                yaxis_title="SLA Target (Working Days)",
                height=400,
                xaxis_tickangle=-45,
                plot_bgcolor='white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab9:
        st.subheader("📝 Request Type Management")
        st.markdown("Add, edit, or delete request types in the system")
        st.warning("⚠️ **Caution:** Deleting a request type will remove it from the system. Existing requests with this type will still be accessible but may not have SLA targets.")
        
        current_types = get_all_request_types()
        
        if current_types:
            st.markdown("### Current Request Types")
            for item in current_types:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{item['request_type']}**")
                with col2:
                    st.write(f"SLA: {item['sla_days']} days")
                with col3:
                    if st.button(f"🗑️ Delete", key=f"del_reqtype_{item['request_type']}"):
                        if item['request_type'] in ["Student Payment", "Imprest", "Petty Cash", "Supplier Payment", "Salary Payment", "Surrender"]:
                            st.error(f"❌ Cannot delete core request type '{item['request_type']}'")
                        else:
                            if delete_request_type(item['request_type']):
                                st.success(f"✅ Request type '{item['request_type']}' deleted!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete request type")
        
        st.markdown("---")
        st.markdown("### ➕ Add New Request Type")
        with st.form("add_reqtype_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_req_type = st.text_input("Request Type Name *", placeholder="e.g., Conference Fee, Office Supplies")
            with col2:
                new_req_sla = st.number_input("SLA Target (Days) *", min_value=1, max_value=30, value=5)
            
            st.info("💡 New request types will be available for all departments to submit.")
            
            if st.form_submit_button("Add Request Type"):
                if new_req_type:
                    existing = [t['request_type'] for t in current_types]
                    if new_req_type in existing:
                        st.error(f"❌ Request type '{new_req_type}' already exists!")
                    else:
                        if add_request_type(new_req_type, new_req_sla):
                            st.success(f"✅ Request type '{new_req_type}' added with SLA {new_req_sla} days!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Failed to add request type")
                else:
                    st.error("Please enter a request type name")
        
        st.markdown("---")
        st.markdown("### ✏️ Edit Request Type")
        
        if current_types:
            edit_options = [item['request_type'] for item in current_types]
            selected_edit = st.selectbox("Select Request Type to Edit", edit_options)
            
            if selected_edit:
                current_data = next((item for item in current_types if item['request_type'] == selected_edit), None)
                if current_data:
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name = st.text_input("New Name", value=current_data['request_type'])
                    with col2:
                        new_sla = st.number_input("New SLA (Days)", min_value=1, max_value=30, value=current_data['sla_days'])
                    
                    if st.button("Update Request Type", type="primary"):
                        if new_name != current_data['request_type']:
                            if new_name in [t['request_type'] for t in current_types if t['request_type'] != selected_edit]:
                                st.error(f"❌ Request type '{new_name}' already exists!")
                            else:
                                if update_request_type(selected_edit, new_name, new_sla):
                                    st.success(f"✅ Request type updated from '{selected_edit}' to '{new_name}' with SLA {new_sla} days!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to update request type")
                        else:
                            if update_sla_days(selected_edit, new_sla):
                                st.success(f"✅ SLA for '{selected_edit}' updated to {new_sla} days!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to update SLA")
    
    if st.button("🔄 Refresh This Page", key="admin_refresh"):
        refresh_page()

# ================================================================
# CHANGE PASSWORD (UNCHANGED)
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
if helb_logo_base64:
    footer_logo = f'<img src="data:image/png;base64,{helb_logo_base64}" style="width: 18px; height: auto; vertical-align: middle; margin-right: 5px;">'
else:
    footer_logo = '🏦 '

st.markdown(f"""
<div class='main-footer'>
    <p>{footer_logo} © 2026 Higher Education Loans Board (HELB) | Payment & Surrender Monitoring System </p>
    <p>Intelligent Search with AI-Based Predictions | Real-Time SLA Fetching | Bulk Operations | Categorized Approval Queue | On-Behalf Submissions | Request Type Management</p>
</div>
""", unsafe_allow_html=True)
