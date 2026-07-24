def calculator_inputs(title: str, key_prefix: str, default_rate: float) -> dict:
    """Show inputs for one loan option including inline part payment impact."""
    st.markdown(f"### {title}")

    principal = st.number_input(
        "Loan Amount (Rs.)",
        min_value=1000, value=1000000, step=10000, key=f"{key_prefix}_principal",
    )

    annual_rate = st.number_input(
        "Annual Interest Rate / ROI (%)",
        min_value=1.0, max_value=50.0, value=default_rate, step=0.01, key=f"{key_prefix}_rate",
    )

    months = st.number_input(
        "Tenure (Months)",
        min_value=1, max_value=360, value=60, step=1, key=f"{key_prefix}_months",
    )

    st.info(f"Tenure: **{months / 12:.1f} Years ({months} Months)**")

    result = calculate_emi(principal, annual_rate, int(months))
    part_payments = {}

    # ---- Part Payment Section with Inline Calculation ----
    enable_pp = st.toggle("Enable Part Payments", key=f"{key_prefix}_pp_toggle")
    if enable_pp:
        st.write("Add multiple part payments below. Click the **'+'** to add more rows.")
        
        # Initialize an empty dataframe with one blank row for the data editor
        df_pp_init = pd.DataFrame([{"Month No.": None, "Part Payment Amount": None}])
        
        # Use st.data_editor to allow dynamic addition of multiple rows
        edited_df = st.data_editor(
            df_pp_init,
            num_rows="dynamic",
            key=f"{key_prefix}_pp_editor",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Month No.": st.column_config.NumberColumn(
                    "At Month No.", 
                    min_value=1, 
                    max_value=int(months), 
                    step=1,
                    help="Enter the month number when the part payment will be made."
                ),
                "Part Payment Amount": st.column_config.NumberColumn(
                    "Part Payment Amount", 
                    min_value=1.0, 
                    step=1000.0, 
                    format="₹ %d"
                )
            }
        )
        
        total_pp_amount = 0.0
        
        # Process the edited table into the part_payments dictionary
        for index, row in edited_df.iterrows():
            m = row["Month No."]
            amt = row["Part Payment Amount"]
            
            # Check for valid inputs before adding
            if pd.notna(m) and pd.notna(amt) and amt > 0:
                m = int(m)
                # If a user enters multiple payments for the exact same month, accumulate them
                part_payments[m] = part_payments.get(m, 0.0) + float(amt)
                total_pp_amount += float(amt)
        
        # If valid part payments exist, calculate and show the detailed impact
        if part_payments:
            temp_schedule = build_repayment_schedule(
                principal, annual_rate, int(months), result["emi"], date.today(), part_payments
            )
            
            if not temp_schedule.empty:
                actual_months = int(temp_schedule["Month No."].max())
                actual_interest = temp_schedule["Interest Paid"].sum()
                
                interest_saved = result["standard_total_interest"] - actual_interest
                tenure_reduced = int(months) - actual_months

                st.success(
                    f"✅ **Total Part Payment Amount:** {format_inr(total_pp_amount)}\n\n"
                    f"🎉 **Total Interest Saved:** {format_inr(interest_saved)}\n\n"
                    f"📉 **Revised Pending EMIs:** {actual_months} Months\n\n"
                    f"⏳ **Total Tenure Reduced By:** {tenure_reduced} Months"
                )
    # ----------------------------------------------------

    result.update({
        "principal": principal,
        "annual_rate": annual_rate,
        "months": int(months),
        "part_payments": part_payments
    })
    return result
