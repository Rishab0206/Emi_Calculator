import streamlit as st

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
