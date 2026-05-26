import streamlit as st
import pandas as pd

# Page configuration
st.set_page_config(page_title="Loan EMI Calculator", page_icon="💰", layout="centered")

# Clear cache automatically on reload
st.cache_data.clear()

# Main Title (Pure English)
st.title("💰 Loan EMI & Interest Calculator")
st.write("Calculate your monthly EMI, total interest, and total payable amount instantly.")

st.markdown("---")

# Input Section
col1, col2 = st.columns(2)

with col1:
    principal = st.number_input("Loan Amount (Rs.)", min_value=1000, value=500000, step=10000)
    annual_rate = st.number_input("Annual Interest Rate (%)", min_value=1.0, max_value=50.0, value=10.5, step=0.1)

with col2:
    months = st.number_input("Tenure (Months)", min_value=1, max_value=360, value=60, step=1)
    years_display = months / 12
    st.info(f"Total Tenure: **{years_display:.1f} Years ({months} Months)**")

# Calculation Logic
if principal > 0 and annual_rate > 0 and months > 0:
    monthly_rate = (annual_rate / 12) / 100
    emi = principal * monthly_rate * ((1 + monthly_rate) ** months) / (((1 + monthly_rate) ** months) - 1)
    
    total_payment = emi * months
    total_interest = total_payment - principal
    
    st.markdown("---")
    st.subheader("📊 Loan Breakdown Details")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(label="Monthly EMI", value=f"₹{emi:,.2f}")
    with c2:
        st.metric(label="Total Interest", value=f"₹{total_interest:,.2f}")
    with c3:
        st.metric(label="Total Payment", value=f"₹{total_payment:,.2f}")
        
    st.markdown("---")
    st.markdown(f"**Principal Amount:** ₹{principal:,.2f}  \n"
                f"**Total Interest Payable:** ₹{total_interest:,.2f}  \n"
                f"**Monthly Installment (EMI):** **₹{emi:,.2f}**")

    # Amortization Table Logic
    st.markdown("---")
    st.subheader("📅 Monthly Amortization Schedule")
    st.write("Track how your balance reduces with each monthly payment:")

    remaining_balance = principal
    schedule_data = []

    for month in range(1, months + 1):
        interest_payment = remaining_balance * monthly_rate
        principal_payment = emi - interest_payment
        remaining_balance -= principal_payment
        
        # Negative balance check for last month precision
        if remaining_balance < 0:
            remaining_balance = 0
            
        schedule_data.append({
            "Month": month,
            "EMI (Payment)": round(emi, 2),
            "Principal Paid": round(principal_payment, 2),
            "Interest Paid": round(interest_payment, 2),
            "Remaining Balance": round(remaining_balance, 2)
        })

    # Convert to Dataframe and format currency display
    df = pd.DataFrame(schedule_data)
    
    # Custom formatting for a cleaner bank-like look
    formatted_df = df.style.format({
        "EMI (Payment)": "₹{:,.2f}",
        "Principal Paid": "₹{:,.2f}",
        "Interest Paid": "₹{:,.2f}",
        "Remaining Balance": "₹{:,.2f}"
    })

    # Display Table in Streamlit
    st.dataframe(formatted_df, use_container_width=True, hide_index=True)
