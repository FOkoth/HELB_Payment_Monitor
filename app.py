import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import init_database, get_requests, save_request, update_request_status, authenticate_user
from utils.holidays_ke import working_days_between
import streamlit_option_menu as option_menu

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
    
    .warning-box {
        background-color: #FFB81C10;
        border-left: 4px solid #FFB81C;
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
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
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

# Login Screen
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center;'>🎓 HELB Loans Board</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #00843D;'>Payment & Surrender Monitoring System</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
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
                    st.session_state.user_dept = user[2]
                    st.session_state.full_name = user[3]
                    st.rerun()
                else:
                    st.error("Invalid credentials. Use: dept_user/dept123, finance_officer/fin123, admin/admin123")
    
    st.markdown("---")
    st.markdown("<p style='text-align: center; font-size: 0.8rem;'>© 2026 Higher Education Loans Board. All rights reserved.</p>", unsafe_allow_html=True)
    st.stop()

# Main App
# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/00843D/FFFFFF?text=HELB", use_column_width=True)
    st.markdown(f"### Welcome, {st.session_state.full_name}")
    st.markdown(f"**Role:** {st.session_state.user_role}")
    st.markdown(f"**Department:** {st.session_state.user_dept if st.session_state.user_dept else 'N/A'}")
    st.markdown("---")
    
    menu_options = ["Dashboard", "New Request", "My Requests", "Approval Queue", "Reports"]
    if st.session_state.user_role == "ADMIN":
        menu_options.append("Admin")
    
    choice = option_menu.option_menu(
        menu_title="Menu",
        options=menu_options,
        icons=["house", "file-plus", "list-task", "check-circle", "bar-chart", "gear"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "#00843D", "font-size": "18px"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin": "0px"},
            "nav-link-selected": {"background-color": "#00843D"},
        }
    )
    
    if st.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# Main content area
if choice == "Dashboard":
    st.markdown("<h1 style='color: #00843D;'>📊 Performance Dashboard</h1>", unsafe_allow_html=True)
    
    df = get_requests()
    
    if df.empty:
        st.info("No requests found. Create your first request using 'New Request' menu.")
    else:
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_requests = len(df)
        pending = len(df[df['status'].isin(['SUBMITTED', 'FINANCE_CHECKING'])])
        completed = len(df[df['status'] == 'COMPLETED'])
        
        # Calculate average completion time
        completed_requests = df[df['status'] == 'COMPLETED'].copy()
        avg_days = 0
        if not completed_requests.empty:
            completion_times = []
            for _, row in completed_requests.iterrows():
                submitted = datetime.fromisoformat(row['submission_date'])
                completed_date = datetime.fromisoformat(row['completion_date'])
                days = working_days_between(submitted.date(), completed_date.date())
                completion_times.append(days)
            avg_days = sum(completion_times) / len(completion_times) if completion_times else 0
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #00843D; margin:0;">{total_requests}</h3>
                <p style="margin:0;">Total Requests</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #FFB81C; margin:0;">{pending}</h3>
                <p style="margin:0;">Pending</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #00529B; margin:0;">{completed}</h3>
                <p style="margin:0;">Completed</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #00843D; margin:0;">{avg_days:.1f}</h3>
                <p style="margin:0;">Avg Completion (Days)</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Requests by Status")
            status_counts = df['status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, 
                        color_discrete_sequence=['#00843D', '#FFB81C', '#00529B', '#D3D3D3'])
            fig.update_layout(showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("💰 Total Amount by Type")
            amount_by_type = df.groupby('request_type')['amount'].sum().reset_index()
            fig = px.bar(amount_by_type, x='request_type', y='amount', 
                        color='request_type', color_discrete_sequence=['#00843D', '#FFB81C', '#00529B'])
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # SLA Compliance Table
        st.subheader("⏱️ SLA Compliance & Insights")
        
        # Calculate SLA for each request
        sla_data = []
        for _, row in df.iterrows():
            if row['status'] == 'COMPLETED':
                submitted = datetime.fromisoformat(row['submission_date'])
                completed_date = datetime.fromisoformat(row['completion_date'])
                actual_days = working_days_between(submitted.date(), completed_date.date())
                
                # Get SLA days
                if row['request_type'] == 'Imprest':
                    sla_days = 5
                elif row['request_type'] == 'Supplier':
                    sla_days = 7
                elif row['request_type'] == 'Student Payment':
                    sla_days = 3
                else:  # Surrender
                    sla_days = 4
                
                breached = actual_days > sla_days
                sla_data.append({
                    'Request #': row['request_number'],
                    'Type': row['request_type'],
                    'Actual Days': actual_days,
                    'SLA Days': sla_days,
                    'Breached': '⚠️ Yes' if breached else '✅ No',
                    'Status': row['status']
                })
        
        if sla_data:
            sla_df = pd.DataFrame(sla_data)
            st.dataframe(sla_df, use_container_width=True, hide_index=True)
            
            # Insights
            breach_rate = (sla_df['Breached'].str.contains('Yes').sum() / len(sla_df)) * 100
            st.markdown(f"""
            <div class="success-box">
                <strong>📊 Intelligent Insights:</strong><br>
                • Overall SLA breach rate: {breach_rate:.1f}%<br>
                • Average processing time: {avg_days:.1f} working days<br>
                • {sla_df['Type'].value_counts().index[0]} requests are the most common type<br>
                • {'Finance department processing time is within acceptable range' if breach_rate < 20 else '⚠️ High breach rate detected - review workflow'}
            </div>
            """, unsafe_allow_html=True)

elif choice == "New Request":
    st.markdown("<h1 style='color: #00843D;'>📝 Create New Request</h1>", unsafe_allow_html=True)
    
    with st.form("request_form"):
        request_type = st.selectbox("Request Type", ["Imprest", "Supplier", "Student Payment", "Surrender"])
        department = st.text_input("Department", value=st.session_state.user_dept if st.session_state.user_dept else "")
        amount = st.number_input("Amount (KES)", min_value=0.0, format="%.2f")
        
        # Conditional fields
        imprest_no = batch_no = supplier_name = invoice_no = surrender_number = previous_imprest_no = None
        
        if request_type == "Imprest":
            imprest_no = st.text_input("Imprest Number *")
        elif request_type == "Supplier":
            supplier_name = st.text_input("Supplier Name *")
            invoice_no = st.text_input("Invoice Number *")
        elif request_type == "Student Payment":
            batch_no = st.text_input("Batch Number *")
        else:  # Surrender
            surrender_number = st.text_input("Surrender Number *")
            previous_imprest_no = st.text_input("Previous Imprest Number *")
        
        submitted = st.form_submit_button("Submit Request", use_container_width=True)
        
        if submitted:
            # Validation
            if request_type == "Imprest" and not imprest_no:
                st.error("Imprest Number is required")
            elif request_type == "Supplier" and (not supplier_name or not invoice_no):
                st.error("Supplier Name and Invoice Number are required")
            elif request_type == "Student Payment" and not batch_no:
                st.error("Batch Number is required")
            elif request_type == "Surrender" and (not surrender_number or not previous_imprest_no):
                st.error("Surrender Number and Previous Imprest Number are required")
            else:
                request_data = {
                    'request_type': request_type,
                    'department': department,
                    'submitted_by': st.session_state.username,
                    'amount': amount,
                    'imprest_no': imprest_no,
                    'batch_no': batch_no,
                    'supplier_name': supplier_name,
                    'invoice_no': invoice_no,
                    'surrender_number': surrender_number,
                    'previous_imprest_no': previous_imprest_no,
                    'status': 'SUBMITTED'
                }
                
                request_number = save_request(request_data)
                st.success(f"✅ Request {request_number} submitted successfully! Finance will review shortly.")
                st.balloons()

elif choice == "My Requests":
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

elif choice == "Approval Queue" and st.session_state.user_role in ["FINANCE", "ADMIN"]:
    st.markdown("<h1 style='color: #00843D;'>✅ Finance Approval Queue</h1>", unsafe_allow_html=True)
    
    df = get_requests()
    pending_requests = df[df['status'].isin(['SUBMITTED', 'FINANCE_CHECKING'])]
    
    if pending_requests.empty:
        st.info("No pending requests for approval.")
    else:
        for _, req in pending_requests.iterrows():
            with st.expander(f"{req['request_number']} - {req['request_type']} - {req['status']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Department:** {req['department']}")
                    st.write(f"**Amount:** KES {req['amount']:,.2f}")
                    st.write(f"**Submitted:** {req['submission_date'][:10]}")
                with col2:
                    if req['request_type'] == 'Imprest':
                        st.write(f"**Imprest No:** {req['imprest_no']}")
                    elif req['request_type'] == 'Supplier':
                        st.write(f"**Supplier:** {req['supplier_name']}")
                        st.write(f"**Invoice:** {req['invoice_no']}")
                    elif req['request_type'] == 'Student Payment':
                        st.write(f"**Batch No:** {req['batch_no']}")
                    else:
                        st.write(f"**Surrender No:** {req['surrender_number']}")
                
                col3, col4 = st.columns(2)
                with col3:
                    if req['status'] == 'SUBMITTED':
                        if st.button(f"Start Checking", key=f"start_{req['id']}"):
                            update_request_status(req['id'], 'FINANCE_CHECKING')
                            st.rerun()
                    elif req['status'] == 'FINANCE_CHECKING':
                        comment = st.text_area("Finance Comment", key=f"comment_{req['id']}")
                        if st.button(f"Approve", key=f"approve_{req['id']}"):
                            update_request_status(req['id'], 'APPROVED_FOR_PROCESSING', comment)
                            st.success("Request approved for processing")
                            st.rerun()
                with col4:
                    if req['status'] == 'APPROVED_FOR_PROCESSING':
                        if st.button(f"Mark Complete", key=f"complete_{req['id']}"):
                            update_request_status(req['id'], 'COMPLETED')
                            st.success("Payment completed!")
                            st.rerun()
                    if req['status'] in ['SUBMITTED', 'FINANCE_CHECKING']:
                        return_reason = st.text_input("Return reason (if returning)", key=f"return_{req['id']}")
                        if st.button(f"Return to Department", key=f"return_btn_{req['id']}"):
                            update_request_status(req['id'], 'RETURNED', return_reason=return_reason)
                            st.warning("Request returned to department")
                            st.rerun()

elif choice == "Reports":
    st.markdown("<h1 style='color: #00843D;'>📑 Reports & Export</h1>", unsafe_allow_html=True)
    
    df = get_requests()
    if df.empty:
        st.info("No data available for reports.")
    else:
        st.download_button(
            label="📥 Export to Excel",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f"helb_requests_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.subheader("Filter Reports")
        status_filter = st.multiselect("Status", df['status'].unique())
        if status_filter:
            df = df[df['status'].isin(status_filter)]
        
        st.dataframe(df, use_container_width=True)

elif choice == "Admin" and st.session_state.user_role == "ADMIN":
    st.markdown("<h1 style='color: #00843D;'>⚙️ Admin Panel</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Users", "SLA Configuration"])
    
    with tab1:
        st.subheader("User Management")
        conn = sqlite3.connect("helb_data.db")
        users_df = pd.read_sql_query("SELECT username, role, department, full_name FROM users", conn)
        conn.close()
        st.dataframe(users_df, use_container_width=True, hide_index=True)
    
    with tab2:
        st.subheader("SLA Timeline Configuration")
        st.info("Set expected completion days for each request type (excluding weekends & holidays)")
        
        conn = sqlite3.connect("helb_data.db")
        sla_df = pd.read_sql_query("SELECT * FROM sla_config", conn)
        conn.close()
        
        for _, row in sla_df.iterrows():
            new_days = st.number_input(f"{row['request_type']} (days)", 
                                       min_value=1, max_value=30, 
                                       value=int(row['sla_days']), 
                                       key=f"sla_{row['request_type']}")
            if new_days != row['sla_days']:
                conn = sqlite3.connect("helb_data.db")
                cursor = conn.cursor()
                cursor.execute("UPDATE sla_config SET sla_days = ? WHERE request_type = ?", 
                              (new_days, row['request_type']))
                conn.commit()
                conn.close()
                st.success(f"Updated {row['request_type']} SLA to {new_days} days")
                st.rerun()
