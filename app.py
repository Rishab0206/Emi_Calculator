import os
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    emi = None
    total_interest = None
    total_amount = None
    schedule = []
    part_payments_data = []

    if request.method == 'POST':
        try:
            principal = float(request.form['principal'])
            rate = float(request.form['rate'])
            months = int(request.form['months'])

            # Collect up to 5 part-payments from form
            part_pay_dict = {}
            for i in range(1, 6):
                month_val = request.form.get(f'part_month_{i}')
                amount_val = request.form.get(f'part_amount_{i}')
                if month_val and amount_val:
                    m = int(month_val)
                    amt = float(amount_val)
                    part_pay_dict[m] = part_pay_dict.get(m, 0) + amt
                    part_payments_data.append({'month': m, 'amount': amt})

            # Base Monthly Interest Rate
            monthly_rate = rate / (12 * 100)
            
            # Base EMI Calculation
            if monthly_rate == 0:
                emi = principal / months
            else:
                emi = (principal * monthly_rate * ((1 + monthly_rate) ** months)) / (((1 + monthly_rate) ** months) - 1)
            
            # Generate Amortization Schedule with Part Payments
            balance = principal
            total_interest_calculated = 0
            actual_months = 0

            for m in range(1, months + 1):
                if balance <= 0:
                    break
                
                actual_months += 1
                interest_for_month = balance * monthly_rate
                principal_for_month = emi - interest_for_month
                
                # Check if part payment occurs this month
                extra_payment = part_pay_dict.get(m, 0)
                
                # Ensure principal doesn't go negative
                if principal_for_month + extra_payment > balance:
                    principal_for_month = balance
                    emi_actual = principal_for_month + interest_for_month
                    balance = 0
                else:
                    balance -= (principal_for_month + extra_payment)

                total_interest_calculated += interest_for_month

                schedule.append({
                    'month': m,
                    'emi': round(emi, 2),
                    'principal': round(principal_for_month + extra_payment, 2),
                    'interest': round(interest_for_month, 2),
                    'extra': round(extra_payment, 2),
                    'balance': round(max(0, balance), 2)
                })

            total_amount_calculated = principal + total_interest_calculated

            emi = round(emi, 2)
            total_interest = round(total_interest_calculated, 2)
            total_amount = round(total_amount_calculated, 2)

        except Exception as e:
            print("Error:", e)

    return render_template('index.html', 
                           emi=emi, 
                           total_interest=total_interest, 
                           total_amount=total_amount, 
                           schedule=schedule,
                           part_payments_data=part_payments_data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
