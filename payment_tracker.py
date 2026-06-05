import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sys
import os

# Add parent directory to path to import database functions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_public_payment_details, calculate_estimated_completion_date, add_working_days
from utils.holidays_ke import working_days_between

# Page config - NO authentication required
st.set_page_config(
    page_title="HELB Payment Tracker - Check Your Payment Status",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for public portal
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #00843D 0%, #00529B 100%);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 1.8rem;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        margin: 0.5rem 0 0 0;
    }
    
    .search-box {
        background: #F9FAFB;
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #E5E7EB;
        margin-bottom: 2rem;
    }
    
    .result-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        border: 1px solid #E5E7EB;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .status-paid { background: #E8F5E9; color: #00843D; }
    .status-pending { background: #FFF3E0; color: #FF9800; }
    .status-received { background: #E3F2FD; color: #2196F3; }
    .status-returned { background: #FFEBEE; color: #F44336; }
    .status-process { background: #F3E5F5; color: #9C27B0; }
    
    .info-row {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid #F3F4F6;
    }
    
    .info-label {
        font-weight: 600;
        color: #6B7280;
        font-size: 0.8rem;
    }
    
    .info-value {
        color: #1F2937;
        font-size: 0.9rem;
    }
    
    .timeline {
        margin: 1.5rem 0;
        padding: 1rem;
        background: #F9FAFB;
        border-radius: 10px;
    }
    
    .timeline-step {
        display: flex;
        align-items: center;
        margin: 0.5rem 0;
    }
    
    .timeline-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 10px;
    }
    
    .timeline-dot-completed { background: #00843D; }
    .timeline-dot-current { background: #FFB81C; width: 14px; height: 14px; box-shadow: 0 0 0 3px rgba(255,184,28,0.3); }
    .timeline-dot-pending { background: #D1D5DB; }
    
    .timeline-label {
        font-size: 0.8rem;
        flex: 1;
    }
    
    .timeline-date {
        font-size: 0.7rem;
        color: #6B7280;
    }
    
    .estimate-box {
        background: #F0F9FF;
        border-left: 4px solid #0284C7;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .alert-box {
        background: #FEF2F2;
        border-left: 4px solid #DC2626;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #FFFBEB;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .footer {
        text-align: center;
        padding: 2rem;
        color: #6B7280;
        font-size: 0.7rem;
    }
    
    .amount {
        font-size: 1.5rem;
        font-weight: 700;
        color: #00843D;
    }
    
    hr {
        margin: 1rem 0;
    }
    
    @media (max-width: 768px) {
        .main-header h1 { font-size: 1.2rem; }
        .info-row { flex-direction: column; }
        .info-value { margin-top: 0.2rem; }
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class='main-header'>
    <h1>🔍 HELB Payment Tracker</h1>
    <p>Track the status of your payment or surrender request in real-time</p>
</div>
""", unsafe_allow_html=True)

# Search Section
st.markdown('<div class="search-box">', unsafe_allow_html=True)
st.markdown("### 📋 Enter Your Reference Number")

st.markdown("""
<div style='background: #E8F5E9; padding: 0.75rem; border-radius: 10px; margin-bottom: 1rem; font-size: 0.8rem;'>
    💡 <strong>Tip:</strong> You can search using any of the following:
    <ul style='margin: 0.5rem 0 0 1rem;'>
        <li>Request Number (e.g., HELB-202503-0001)</li>
        <li>Batch Number</li>
        <li>Imprest Number</li>
        <li>Invoice Number</li>
        <li>Surrender Number</li>
        <li>Payment Reference</li>
    </ul>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    search_term = st.text_input("", placeholder="Enter your reference number...", label_visibility="collapsed")
with col2:
    search_button = st.button("🔍 Track Payment", type="primary", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# Search Results
if search_button and search_term:
    with st.spinner("Searching for your payment..."):
        payment = get_public_payment_details(search_term.strip())
        
        if not payment:
            # No record found
            st.markdown("""
            <div class='alert-box'>
                <strong>❌ Payment Not Found</strong><br>
                This payment has not been submitted in Finance. Please check your reference number and try again, or contact your department for assistance.
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class='warning-box'>
                <strong>💡 Need Help?</strong><br>
                If you believe this is an error, please contact:<br>
                • Your Department's Finance Office<br>
                • HELB Finance Helpdesk: helpdesk@helb.co.ke<br>
                • Phone: 020-1234567
            </div>
            """, unsafe_allow_html=True)
        else:
            # Payment found - display details
            status = payment['status']
            submission_date = datetime.strptime(payment['submission_date'], '%Y-%m-%d').date() if payment['submission_date'] else None
            date_received = datetime.strptime(payment['date_received'], '%Y-%m-%d').date() if payment['date_received'] else None
            
            # Calculate SLA days
            sla_days = None
            if submission_date:
                today = date.today()
                if status in ['PAID', 'CLEARED'] and payment['payment_date']:
                    payment_date = datetime.strptime(payment['payment_date'], '%Y-%m-%d').date()
                    sla_days = working_days_between(submission_date, payment_date)
                else:
                    sla_days = working_days_between(submission_date, today)
            
            # Get reference number based on request type
            ref_number = ""
            if payment.get('batch_no'):
                ref_number = f"Batch: {payment['batch_no']}"
            elif payment.get('imprest_no'):
                ref_number = f"Imprest: {payment['imprest_no']}"
            elif payment.get('invoice_no'):
                ref_number = f"Invoice: {payment['invoice_no']}"
            elif payment.get('surrender_number'):
                ref_number = f"Surrender: {payment['surrender_number']}"
            elif payment.get('payment_reference'):
                ref_number = f"Ref: {payment['payment_reference']}"
            
            # Status badge color
            if status in ['PAID', 'CLEARED']:
                status_class = "status-paid"
                status_text = f"✅ {status}"
            elif status == 'RETURNED':
                status_class = "status-returned"
                status_text = f"↩️ {status}"
            elif status in ['RECEIVED_BY_FINANCE', 'PAYMENT_PREPARED', 'PAYMENT_VERIFIED', 'PAYMENT_APPROVED', 'PAYMENT_AUTHORIZED']:
                status_class = "status-received"
                status_text = f"📋 {status}"
            else:
                status_class = "status-pending"
                status_text = f"⏳ {status}"
            
            # Main result card
            st.markdown(f"""
            <div class='result-card'>
                <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;'>
                    <div>
                        <h3 style='margin: 0; color: #00843D;'>{payment['request_number']}</h3>
                        <p style='margin: 0; color: #6B7280; font-size: 0.8rem;'>{payment['request_type']} • {payment['department_name']}</p>
                    </div>
                    <div>
                        <span class='status-badge {status_class}'>{status_text}</span>
                    </div>
                </div>
                <hr>
                <div class='info-row'>
                    <span class='info-label'>💰 Amount</span>
                    <span class='info-value amount'>KES {payment['amount']:,.2f}</span>
                </div>
                <div class='info-row'>
                    <span class='info-label'>📝 Payment Details</span>
                    <span class='info-value'>{payment['payment_description'] or 'No description provided'}</span>
                </div>
                <div class='info-row'>
                    <span class='info-label'>🔢 Reference Number</span>
                    <span class='info-value'>{ref_number or 'N/A'}</span>
                </div>
                <div class='info-row'>
                    <span class='info-label'>📅 Date Submitted</span>
                    <span class='info-value'>{payment['submission_date']}</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Date received in Finance
            if date_received:
                st.markdown(f"""
                <div class='info-row'>
                    <span class='info-label'>📥 Date Received by Finance</span>
                    <span class='info-value'>{payment['date_received']}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class='info-row'>
                    <span class='info-label'>📥 Date Received by Finance</span>
                    <span class='info-value'>Not yet received</span>
                </div>
                """, unsafe_allow_html=True)
            
            # Payment date if completed
            if payment['payment_date']:
                st.markdown(f"""
                <div class='info-row'>
                    <span class='info-label'>✅ Payment Date</span>
                    <span class='info-value'>{payment['payment_date']}</span>
                </div>
                """, unsafe_allow_html=True)
                
                if payment['payment_reference']:
                    st.markdown(f"""
                    <div class='info-row'>
                        <span class='info-label'>🏦 Payment Reference</span>
                        <span class='info-value'>{payment['payment_reference']}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Return reason if returned
            if payment['return_reason']:
                st.markdown(f"""
                <div class='info-row'>
                    <span class='info-label'>↩️ Return Reason</span>
                    <span class='info-value' style='color: #DC2626;'>{payment['return_reason']}</span>
                </div>
                """, unsafe_allow_html=True)
            
            # SLA Information
            if sla_days is not None:
                sla_color = "#00843D" if sla_days <= 5 else "#F59E0B" if sla_days <= 7 else "#DC2626"
                st.markdown(f"""
                <div class='info-row'>
                    <span class='info-label'>⏱️ Turnaround Time</span>
                    <span class='info-value' style='color: {sla_color}; font-weight: 600;'>{sla_days} working days</span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Timeline / Progress Section
            st.markdown("### 📊 Payment Progress Timeline")
            
            # Define workflow stages based on request type
            if payment['request_type'] == "Surrender":
                stages = [
                    {'name': 'Submitted', 'status_key': 'SUBMITTED', 'date': payment['submission_date']},
                    {'name': 'Received', 'status_key': 'RECEIVED_BY_FINANCE', 'date': payment['date_received']},
                    {'name': 'First Verification', 'status_key': 'SURRENDER_FIRST_VERIFICATION', 'date': None},
                    {'name': 'Second Verification', 'status_key': 'SURRENDER_SECOND_VERIFICATION', 'date': None},
                    {'name': 'Approval', 'status_key': 'SURRENDER_APPROVAL', 'date': None},
                    {'name': 'Posting', 'status_key': 'SURRENDER_POSTING', 'date': None},
                    {'name': 'Cleared', 'status_key': 'CLEARED', 'date': payment['payment_date']}
                ]
            else:
                stages = [
                    {'name': 'Submitted', 'status_key': 'SUBMITTED', 'date': payment['submission_date']},
                    {'name': 'Received by Finance', 'status_key': 'RECEIVED_BY_FINANCE', 'date': payment['date_received']},
                    {'name': 'Prepared', 'status_key': 'PAYMENT_PREPARED', 'date': None},
                    {'name': 'Verified', 'status_key': 'PAYMENT_VERIFIED', 'date': None},
                    {'name': 'Approved', 'status_key': 'PAYMENT_APPROVED', 'date': None},
                    {'name': 'Authorized', 'status_key': 'PAYMENT_AUTHORIZED', 'date': None},
                    {'name': 'Paid', 'status_key': 'PAID', 'date': payment['payment_date']}
                ]
            
            # Determine current stage index
            current_index = 0
            status_order = [s['status_key'] for s in stages]
            if status in status_order:
                current_index = status_order.index(status)
            
            # Display timeline
            for i, stage in enumerate(stages):
                is_completed = i < current_index
                is_current = i == current_index
                
                if is_completed:
                    dot_class = "timeline-dot-completed"
                elif is_current:
                    dot_class = "timeline-dot-current"
                else:
                    dot_class = "timeline-dot-pending"
                
                date_str = ""
                if stage['date']:
                    date_str = f"<span class='timeline-date'>{stage['date']}</span>"
                elif is_current and stage['date'] is None:
                    date_str = "<span class='timeline-date'>In progress</span>"
                
                st.markdown(f"""
                <div class='timeline-step'>
                    <div class='timeline-dot {dot_class}'></div>
                    <div class='timeline-label'>
                        <strong>{stage['name']}</strong> {date_str}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Estimated Completion
            if status not in ['PAID', 'CLEARED', 'RETURNED']:
                estimated_date, estimate_message, days_remaining = calculate_estimated_completion_date(status, date.today())
                
                if estimated_date:
                    st.markdown(f"""
                    <div class='estimate-box'>
                        <strong>📅 Estimated Completion Date:</strong> {estimated_date.strftime('%B %d, %Y')}<br>
                        <small>{estimate_message}</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class='estimate-box'>
                        <strong>ℹ️ Status Update:</strong><br>
                        {estimate_message}
                    </div>
                    """, unsafe_allow_html=True)
            elif status == 'RETURNED':
                st.markdown(f"""
                <div class='alert-box'>
                    <strong>⚠️ Action Required</strong><br>
                    This payment has been returned for corrections. Please contact your department's finance office for details on how to resubmit.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class='estimate-box'>
                    <strong>✅ Payment Completed</strong><br>
                    This payment has been successfully processed. Thank you for your patience.
                </div>
                """, unsafe_allow_html=True)

elif search_button and not search_term:
    st.warning("⚠️ Please enter a reference number to track your payment.")

# Footer
st.markdown("""
<div class='footer'>
    <p>© 2026 Higher Education Loans Board (HELB) | Payment Tracking Portal</p>
    <p>For questions about your payment, please contact your department's finance office.</p>
</div>
""", unsafe_allow_html=True)
