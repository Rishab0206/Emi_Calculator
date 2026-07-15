import streamlit as st
import pandas as pd
from datetime import date

# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="Loan EMI Comparison Calculator",
    page_icon="💰",
    layout="wide"
)

# -----------------------------
# Helper functions
# -----------------------------
def format_inr(amount: float) -> str:
    """Return amount formatted in INR style with rupee symbol."""
    return f"₹{amount:,.2f}"

def calculate_emi(principal: float, annual_rate: float, months: int) -> dict:
    """Calculate basic standard EMI and standard totals without part payment."""
    if principal <= 0 or annual_rate <= 0 or months <= 0:
        return {"emi": 0.0, "monthly_rate": 0.0, "standard_total_interest": 0.0, "standard_total_payment": 0.0}

    monthly_rate = (annual_rate / 12) / 100
    emi = principal * monthly_rate * ((1 + monthly_rate) ** months) / (((1 + monthly_rate) ** months) - 1)
    
    standard_total_payment = emi * months
    standard_total_interest = standard_total_payment - principal

    return {
        "emi": emi, 
        "monthly_rate": monthly_rate,
        "standard_total_interest": standard_total_interest,
        "standard_total_payment": standard_total_payment
    }

def build_repayment_schedule(
    principal: float,
    annual_rate: float,
    months: int,
    emi: float,
    start_date: date,
    part_payments: dict = None
) -> pd.DataFrame:
    """Create month-wise repayment schedule including part payments."""
    if part_payments is None:
        part_payments = {}
        
    monthly_rate = (annual_rate / 12) / 100
    remaining_balance = principal
    rows = []

    for month in range(1, months + 1):
        if remaining_balance <= 0.01: # Handle floating point precision
            break

        interest_payment = remaining_balance * monthly_rate
        principal_payment = emi - interest_payment

        # Adjust last EMI if remaining balance is less than principal payment
        if remaining_balance < principal_payment:
            principal_payment = remaining_balance
            emi_paid = principal_payment + interest_payment
        else:
            emi_paid = emi

        remaining_balance -= principal_payment

        # Handle Part Payment for this month
        pp_this_month = part_payments.get(month, 0.0)
        if pp_this_month > 0:
            if pp_this_month > remaining_balance:
                pp_this_month = remaining_balance # Prevent overpaying
            remaining_balance -= pp_this_month

        due_date = pd.Timestamp(start_date) + pd.DateOffset(months=month - 1)

        rows.append({
            "Month No.": month,
            "Due Month": due_date.strftime("%b-%Y"),
            "Opening Balance": round(remaining_balance + principal_payment + pp_this_month, 2),
            "EMI": round(emi_paid, 2),
            "Principal Paid": round(principal_payment, 2),
            "Interest Paid": round(interest_payment, 2),
            "Part Payment": round(pp_this_month, 2),
            "Closing Balance": round(max(remaining_balance, 0), 2),
        })

    return pd.DataFrame(rows)

def currency_style(df: pd.DataFrame):
    """Format dataframe currency columns for display."""
    currency_columns = [
        "Opening Balance",
        "EMI",
        "Principal Paid",
        "Interest Paid",
        "Part Payment",
        "Closing Balance",
    ]
    existing_columns = [col for col in currency_columns if col in df.columns]
    return df.style.format({col: "₹{:,.2f}" for col in existing_columns})

def calculator_inputs(title: str, key_prefix: str, default_rate: float) -> dict:
    """Show inputs for one loan option including part payment toggle."""
    st.markdown(f"### {title}")

    principal = st.number_input(
        "Loan Amount (Rs.)",
        min_value=1000, value=10000000, step=10000, key=f"{key_prefix}_principal",
    )

    annual_rate = st.number_input(
        "Annual Interest Rate / ROI (%)",
        min_value=1.0, max_value=50.0, value=default_rate, step=0.01, key=f"{key_prefix}_rate",
    )

    months = st.number_input(
        "Tenure (Months)",
        min_value=1, max_value=360, value=84, step=1, key=f"{key_prefix}_months",
    )

    st.info(f"Tenure: **{months / 12:.1f} Years ({months} Months)**")

    # ---- Part Payment Section ----
    part_payments = {}
    enable_pp = st.toggle("Enable Part Payment", key=f"{key_prefix}_pp_toggle")
    if enable_pp:
        c1, c2 = st.columns(2)
        with c1:
            pp_amt = st.number_input("Part Payment Amount", min_value=0.0, value=100000.0, step=10000.0, key=f"{key_prefix}_pp_amt")
        with c2:
            pp_month = st.number_input("At Month No.", min_value=1, max_value=int(months), value=12, step=1, key=f"{key_prefix}_pp_month")
        
        if pp_amt > 0:
            part_payments[int(pp_month)] = pp_amt
            st.success(f"₹{pp_amt:,.2f} will be paid extra at month {int(pp_month)}.")
    # ------------------------------

    result = calculate_emi(principal, annual_rate, int(months))
    result.update({
        "principal": principal,
        "annual_rate": annual_rate,
        "months": int(months),
        "part_payments": part_payments
    })
    return result

def get_actual_metrics(schedule_df, option_dict):
    """Calculate actual totals and savings from the schedule DataFrame."""
    if schedule_df.empty:
        return option_dict
        
    actual_months = int(schedule_df["Month No."].max())
    actual_interest = schedule_df["Interest Paid"].sum()
    actual_payment = schedule_df["EMI"].sum() + schedule_df["Part Payment"].sum()

    interest_saved = option_dict["standard_total_interest"] - actual_interest
    tenure_reduced = option_dict["months"] - actual_months

    return {
        "principal": option_dict["principal"],
        "annual_rate": option_dict["annual_rate"],
        "original_months": option_dict["months"],
        "actual_months": actual_months,
        "tenure_reduced": tenure_reduced,
        "emi": option_dict["emi"],
        "total_interest": actual_interest,
        "interest_saved": interest_saved,
        "total_payment": actual_payment
    }

# -----------------------------
# UI Header
# -----------------------------
st.title("💰 Loan EMI Comparison Calculator")
st.write("Compare two loan offers with EMI, total interest, total payment, savings, part payments, and full repayment schedule.")
st.markdown("---")

# -----------------------------
# Input section: two calculators
# -----------------------------
left_col, right_col = st.columns(2, gap="large")

with left_col:
    option_1 = calculator_inputs("Calculator 1 - Current / Existing Loan", "option_1", 13.00)

with right_col:
    option_2 = calculator_inputs("Calculator 2 - New / Transfer Offer", "option_2", 9.99)

# -----------------------------
# Repayment start date
# -----------------------------
st.markdown("---")
schedule_col_1, schedule_col_2 = st.columns([1, 2])
with schedule_col_1:
    repayment_start_date = st.date_input("Repayment Schedule Start Month", value=date.today())
with schedule_col_2:
    st.info("This date is used only to show the Due Month in the repayment schedule.")

# -----------------------------
# Generate Schedules First (To get exact metrics)
# -----------------------------
schedule_1 = build_repayment_schedule(
    option_1["principal"], option_1["annual_rate"], option_1["months"], 
    option_1["emi"], repayment_start_date, option_1["part_payments"]
)

schedule_2 = build_repayment_schedule(
    option_2["principal"], option_2["annual_rate"], option_2["months"], 
    option_2["emi"], repayment_start_date, option_2["part_payments"]
)

act_1 = get_actual_metrics(schedule_1, option_1)
act_2 = get_actual_metrics(schedule_2, option_2)


# -----------------------------
# Part Payment Impact Section
# -----------------------------
st.markdown("---")
st.subheader("🚀 Part Payment Impact")

pp_col1, pp_col2 = st.columns(2)

with pp_col1:
    if act_1["interest_saved"] > 0:
        st.success(f"**Calculator 1:** Due to part payment, you save **{format_inr(act_1['interest_saved'])}** in Interest and your tenure is reduced by **{act_1['tenure_reduced']} Months**.")
    else:
        st.info("**Calculator 1:** No part payment impact.")

with pp_col2:
    if act_2["interest_saved"] > 0:
        st.success(f"**Calculator 2:** Due to part payment, you save **{format_inr(act_2['interest_saved'])}** in Interest and your tenure is reduced by **{act_2['tenure_reduced']} Months**.")
    else:
        st.info("**Calculator 2:** No part payment impact.")


# -----------------------------
# Breakdown metrics
# -----------------------------
st.markdown("---")
st.subheader("📊 Loan Breakdown Comparison")

comparison_data = pd.DataFrame([
    {
        "Particulars": "Loan Amount",
        "Calculator 1": format_inr(act_1["principal"]),
        "Calculator 2": format_inr(act_2["principal"]),
    },
    {
        "Particulars": "ROI",
        "Calculator 1": f'{act_1["annual_rate"]:.2f}%',
        "Calculator 2": f'{act_2["annual_rate"]:.2f}%',
    },
    {
        "Particulars": "Actual Tenure (Months)",
        "Calculator 1": f'{act_1["actual_months"]} (Originally {act_1["original_months"]})',
        "Calculator 2": f'{act_2["actual_months"]} (Originally {act_2["original_months"]})',
    },
    {
        "Particulars": "Monthly EMI",
        "Calculator 1": format_inr(act_1["emi"]),
        "Calculator 2": format_inr(act_2["emi"]),
    },
    {
        "Particulars": "Total Interest (Actual)",
        "Calculator 1": format_inr(act_1["total_interest"]),
        "Calculator 2": format_inr(act_2["total_interest"]),
    },
    {
        "Particulars": "Total Payment (Actual)",
        "Calculator 1": format_inr(act_1["total_payment"]),
        "Calculator 2": format_inr(act_2["total_payment"]),
    },
])

st.dataframe(comparison_data, use_container_width=True, hide_index=True)

# -----------------------------
# Savings / difference section
# -----------------------------
st.markdown("---")
st.subheader("💡 Difference / Savings Details (Calculator 1 vs 2)")

emi_difference = act_1["emi"] - act_2["emi"]
interest_difference = act_1["total_interest"] - act_2["total_interest"]
total_payment_difference = act_1["total_payment"] - act_2["total_payment"]

m1, m2, m3 = st.columns(3)
with m1:
    st.metric(
        "Standard EMI Difference",
        format_inr(abs(emi_difference)),
        delta="Calculator 2 lower" if emi_difference > 0 else "Calculator 1 lower",
    )
with m2:
    st.metric(
        "Actual Interest Difference",
        format_inr(abs(interest_difference)),
        delta="Calculator 2 saves interest" if interest_difference > 0 else "Calculator 1 saves interest",
    )
with m3:
    st.metric(
        "Total Payment Difference",
        format_inr(abs(total_payment_difference)),
        delta="Calculator 2 lower payout" if total_payment_difference > 0 else "Calculator 1 lower payout",
    )

if interest_difference > 0:
    st.success(f"Calculator 2 can save approximately **{format_inr(interest_difference)}** in actual total interest compared to Calculator 1.")
elif interest_difference < 0:
    st.warning(f"Calculator 1 is cheaper by approximately **{format_inr(abs(interest_difference))}** in actual total interest.")
else:
    st.info("Both calculators have the same total actual interest cost.")

# -----------------------------
# Repayment schedules
# -----------------------------
st.markdown("---")
st.subheader("📅 Repayment Schedule / Amortization Table")

view_type = st.radio(
    "Schedule View",
    ["Calculator 1 Schedule", "Calculator 2 Schedule", "Both Side-by-Side", "Year-wise Summary"],
    horizontal=True,
)

if view_type == "Calculator 1 Schedule":
    st.markdown("#### Calculator 1 Repayment Schedule")
    st.dataframe(currency_style(schedule_1), use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download Calculator 1 Schedule CSV", schedule_1.to_csv(index=False).encode("utf-8"), "calc_1_schedule.csv", "text/csv")

elif view_type == "Calculator 2 Schedule":
    st.markdown("#### Calculator 2 Repayment Schedule")
    st.dataframe(currency_style(schedule_2), use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download Calculator 2 Schedule CSV", schedule_2.to_csv(index=False).encode("utf-8"), "calc_2_schedule.csv", "text/csv")

elif view_type == "Both Side-by-Side":
    side_1, side_2 = st.columns(2, gap="large")
    with side_1:
        st.markdown("#### Calculator 1")
        st.dataframe(currency_style(schedule_1), use_container_width=True, hide_index=True)
    with side_2:
        st.markdown("#### Calculator 2")
        st.dataframe(currency_style(schedule_2), use_container_width=True, hide_index=True)

else:
    year_summary_1 = schedule_1.copy()
    year_summary_2 = schedule_2.copy()
    year_summary_1["Year"] = ((year_summary_1["Month No."] - 1) // 12) + 1
    year_summary_2["Year"] = ((year_summary_2["Month No."] - 1) // 12) + 1

    summary_1 = year_summary_1.groupby("Year", as_index=False).agg({
        "EMI": "sum",
        "Principal Paid": "sum",
        "Interest Paid": "sum",
        "Part Payment": "sum",
        "Closing Balance": "last",
    })
    summary_1.insert(0, "Calculator", "Calculator 1")

    summary_2 = year_summary_2.groupby("Year", as_index=False).agg({
        "EMI": "sum",
        "Principal Paid": "sum",
        "Interest Paid": "sum",
        "Part Payment": "sum",
        "Closing Balance": "last",
    })
    summary_2.insert(0, "Calculator", "Calculator 2")

    yearly_summary = pd.concat([summary_1, summary_2], ignore_index=True)
    st.dataframe(currency_style(yearly_summary), use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download Year-wise Summary CSV", yearly_summary.to_csv(index=False).encode("utf-8"), "year_wise_summary.csv", "text/csv")

# -----------------------------
# Footer note
# -----------------------------
st.markdown("---")
st.caption("Note: This calculator is for estimation. Final terms may vary as per lender policy.")