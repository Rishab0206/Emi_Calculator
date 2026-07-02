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
    """Calculate EMI, total interest, and total payment."""
    if principal <= 0 or annual_rate <= 0 or months <= 0:
        return {
            "emi": 0.0,
            "total_interest": 0.0,
            "total_payment": 0.0,
            "monthly_rate": 0.0,
        }

    monthly_rate = (annual_rate / 12) / 100
    emi = principal * monthly_rate * ((1 + monthly_rate) ** months) / (((1 + monthly_rate) ** months) - 1)
    total_payment = emi * months
    total_interest = total_payment - principal

    return {
        "emi": emi,
        "total_interest": total_interest,
        "total_payment": total_payment,
        "monthly_rate": monthly_rate,
    }


def build_repayment_schedule(
    principal: float,
    annual_rate: float,
    months: int,
    emi: float,
    start_date: date,
) -> pd.DataFrame:
    """Create month-wise repayment/amortization schedule."""
    monthly_rate = (annual_rate / 12) / 100
    remaining_balance = principal
    rows = []

    for month in range(1, months + 1):
        interest_payment = remaining_balance * monthly_rate
        principal_payment = emi - interest_payment
        remaining_balance -= principal_payment

        # Keep last month clean in case of decimal precision difference
        if month == months or remaining_balance < 0:
            remaining_balance = 0

        due_date = pd.Timestamp(start_date) + pd.DateOffset(months=month - 1)

        rows.append({
            "Month No.": month,
            "Due Month": due_date.strftime("%b-%Y"),
            "Opening Balance": round(max(remaining_balance + principal_payment, 0), 2),
            "EMI": round(emi, 2),
            "Principal Paid": round(max(principal_payment, 0), 2),
            "Interest Paid": round(max(interest_payment, 0), 2),
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
        "Closing Balance",
    ]
    existing_columns = [col for col in currency_columns if col in df.columns]
    return df.style.format({col: "₹{:,.2f}" for col in existing_columns})


def calculator_inputs(title: str, key_prefix: str, default_rate: float) -> dict:
    """Show inputs for one loan option and return values."""
    st.markdown(f"### {title}")

    principal = st.number_input(
        "Loan Amount (Rs.)",
        min_value=1000,
        value=10000000,
        step=10000,
        key=f"{key_prefix}_principal",
    )

    annual_rate = st.number_input(
        "Annual Interest Rate / ROI (%)",
        min_value=1.0,
        max_value=50.0,
        value=default_rate,
        step=0.01,
        key=f"{key_prefix}_rate",
    )

    months = st.number_input(
        "Tenure (Months)",
        min_value=1,
        max_value=360,
        value=84,
        step=1,
        key=f"{key_prefix}_months",
    )

    st.info(f"Tenure: **{months / 12:.1f} Years ({months} Months)**")

    result = calculate_emi(principal, annual_rate, int(months))
    result.update({
        "principal": principal,
        "annual_rate": annual_rate,
        "months": int(months),
    })
    return result


# -----------------------------
# UI Header
# -----------------------------
st.title("💰 Loan EMI Comparison Calculator")
st.write(
    "Compare two loan offers on the same page with EMI, total interest, total payment, "
    "savings, and full repayment schedule."
)
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
    st.info(
        "This date is used only to show the Due Month in the repayment schedule. "
        "EMI and interest calculation is based on loan amount, ROI, and tenure."
    )

# -----------------------------
# Breakdown metrics
# -----------------------------
st.markdown("---")
st.subheader("📊 Loan Breakdown Comparison")

comparison_data = pd.DataFrame([
    {
        "Particulars": "Loan Amount",
        "Calculator 1": format_inr(option_1["principal"]),
        "Calculator 2": format_inr(option_2["principal"]),
    },
    {
        "Particulars": "ROI",
        "Calculator 1": f'{option_1["annual_rate"]:.2f}%',
        "Calculator 2": f'{option_2["annual_rate"]:.2f}%',
    },
    {
        "Particulars": "Tenure",
        "Calculator 1": f'{option_1["months"]} Months',
        "Calculator 2": f'{option_2["months"]} Months',
    },
    {
        "Particulars": "Monthly EMI",
        "Calculator 1": format_inr(option_1["emi"]),
        "Calculator 2": format_inr(option_2["emi"]),
    },
    {
        "Particulars": "Total Interest",
        "Calculator 1": format_inr(option_1["total_interest"]),
        "Calculator 2": format_inr(option_2["total_interest"]),
    },
    {
        "Particulars": "Total Payment",
        "Calculator 1": format_inr(option_1["total_payment"]),
        "Calculator 2": format_inr(option_2["total_payment"]),
    },
])

st.dataframe(comparison_data, use_container_width=True, hide_index=True)

# -----------------------------
# Savings / difference section
# -----------------------------
st.markdown("---")
st.subheader("💡 Difference / Savings Details")

emi_difference = option_1["emi"] - option_2["emi"]
interest_difference = option_1["total_interest"] - option_2["total_interest"]
total_payment_difference = option_1["total_payment"] - option_2["total_payment"]

m1, m2, m3 = st.columns(3)
with m1:
    st.metric(
        "EMI Difference",
        format_inr(abs(emi_difference)),
        delta="Calculator 2 lower" if emi_difference > 0 else "Calculator 1 lower",
    )
with m2:
    st.metric(
        "Interest Difference",
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
    st.success(
        f"Calculator 2 can save approximately **{format_inr(interest_difference)}** in total interest "
        f"and **{format_inr(emi_difference)}** per month in EMI compared to Calculator 1."
    )
elif interest_difference < 0:
    st.warning(
        f"Calculator 1 is cheaper by approximately **{format_inr(abs(interest_difference))}** in total interest."
    )
else:
    st.info("Both calculators have the same total interest cost.")

# -----------------------------
# Repayment schedules
# -----------------------------
st.markdown("---")
st.subheader("📅 Repayment Schedule / Amortization Table")

schedule_1 = build_repayment_schedule(
    option_1["principal"],
    option_1["annual_rate"],
    option_1["months"],
    option_1["emi"],
    repayment_start_date,
)

schedule_2 = build_repayment_schedule(
    option_2["principal"],
    option_2["annual_rate"],
    option_2["months"],
    option_2["emi"],
    repayment_start_date,
)

view_type = st.radio(
    "Schedule View",
    ["Calculator 1 Schedule", "Calculator 2 Schedule", "Both Side-by-Side", "Year-wise Summary"],
    horizontal=True,
)

if view_type == "Calculator 1 Schedule":
    st.markdown("#### Calculator 1 Repayment Schedule")
    st.dataframe(currency_style(schedule_1), use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download Calculator 1 Schedule CSV",
        schedule_1.to_csv(index=False).encode("utf-8"),
        file_name="calculator_1_repayment_schedule.csv",
        mime="text/csv",
    )

elif view_type == "Calculator 2 Schedule":
    st.markdown("#### Calculator 2 Repayment Schedule")
    st.dataframe(currency_style(schedule_2), use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download Calculator 2 Schedule CSV",
        schedule_2.to_csv(index=False).encode("utf-8"),
        file_name="calculator_2_repayment_schedule.csv",
        mime="text/csv",
    )

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
        "Closing Balance": "last",
    })
    summary_1.insert(0, "Calculator", "Calculator 1")

    summary_2 = year_summary_2.groupby("Year", as_index=False).agg({
        "EMI": "sum",
        "Principal Paid": "sum",
        "Interest Paid": "sum",
        "Closing Balance": "last",
    })
    summary_2.insert(0, "Calculator", "Calculator 2")

    yearly_summary = pd.concat([summary_1, summary_2], ignore_index=True)
    st.dataframe(currency_style(yearly_summary), use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download Year-wise Summary CSV",
        yearly_summary.to_csv(index=False).encode("utf-8"),
        file_name="year_wise_repayment_summary.csv",
        mime="text/csv",
    )

# -----------------------------
# Footer note
# -----------------------------
st.markdown("---")
st.caption(
    "Note: This calculator is for estimation. Final EMI, ROI, processing fee, insurance, foreclosure, "
    "and bank charges may vary as per lender policy."
)
