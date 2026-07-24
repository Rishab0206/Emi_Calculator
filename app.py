from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    # Shuru mein variables khali rahenge
    emi = None
    total_interest = None
    total_amount = None

    if request.method == 'POST':
        try:
            # HTML form se user ka data nikalna
            principal = float(request.form['principal'])
            rate = float(request.form['rate'])
            months = int(request.form['months'])

            # EMI Calculation Formula
            monthly_rate = rate / (12 * 100)
            
            if monthly_rate == 0: # Agar 0% interest ho
                emi_calculated = principal / months
            else:
                emi_calculated = principal * monthly_rate * ((1 + monthly_rate) ** months) / (((1 + monthly_rate) ** months) - 1)
            
            # Total values calculate karna
            total_amount_calculated = emi_calculated * months
            total_interest_calculated = total_amount_calculated - principal

            # Decimal ke baad sirf 2 digits tak round off karna taaki clean dikhe
            emi = round(emi_calculated, 2)
            total_interest = round(total_interest_calculated, 2)
            total_amount = round(total_amount_calculated, 2)

        except Exception as e:
            print("Error:", e)

    # Calculate hone ke baad data wapas index.html ko bhej dena
    return render_template('index.html', emi=emi, total_interest=total_interest, total_amount=total_amount)

if __name__ == '__main__':
    # GitHub codespaces/local dono par chalane ke liye
    app.run(host='0.0.0.0', port=5000, debug=True)
