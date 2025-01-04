from flask import Flask, render_template, request, jsonify, redirect
import json
import os
from datetime import datetime

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
DATA_FILE = 'expenses.json'
LOG_FILE = 'expenses_log.json'


# Load expenses from file
def load_expenses():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    return []

# Save expenses to file
def save_expenses(expenses):
    with open(DATA_FILE, 'w') as file:
        json.dump(expenses, file, indent=4)

# Save logs to file
def save_log(logs):
    with open(LOG_FILE, 'w') as file:
        json.dump(logs, file, indent=4)

# Add a new expense to the log
def log_change(action, expense):
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as file:
            logs = json.load(file)
    log_entry = {
        'action': action,
        'expense': expense,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    logs.append(log_entry)
    save_log(logs)

@app.route('/')
def index():
    categories = ["food", "entertainment", "travel", "shopping", "edu", "provisions",
                  "vegetables", "fruits", "milk", "health", "hotels", "clothes",
                  "investments", "vehicle", "donations", "homeapp", "misc"]
    persons = ["common", "sampath", "manisha", "shannu", "shiny", "others"]
    return render_template('index.html', categories=categories, persons=persons)

# Get all expenses
@app.route('/expenses', methods=['GET'])
def get_expenses():
    expenses = load_expenses()
    category_filter = request.args.get('category')
    person_filter = request.args.get('person')
    sort_by = request.args.get('sort_by')

    # Filtering
    if category_filter:
        expenses = [exp for exp in expenses if exp['category'] == category_filter]
    if person_filter:
        expenses = [exp for exp in expenses if exp['person'] == person_filter]

    # Sorting
    if sort_by == 'amount':
        expenses.sort(key=lambda x: x['amount'], reverse=True)
    elif sort_by == 'date':
        expenses.sort(key=lambda x: x['date'], reverse=True)

    return jsonify(expenses)

# Add expense
@app.route('/add', methods=['POST'])
def add_expense():
    data = request.form
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_expense = {
        "id": datetime.now().timestamp(),  # Unique ID based on timestamp
        "date": data['inputdate'],
        "category": data['category'],
        "person": data['person'],
        "amount": float(data['amount']),
        "added_date": current_time,
        "last_modified": current_time
    }

    expenses = load_expenses()
    expenses.append(new_expense)
    save_expenses(expenses)
    log_change("Added", new_expense)

    return redirect("http://127.0.0.1:5000/")

# Edit expense
@app.route('/edit/<expense_id>', methods=['POST'])
def edit_expense(expense_id):
    data = request.form
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Load the current list of expenses
    expenses = load_expenses()

    # Find the expense that matches the provided ID
    expense_to_edit = None
    for expense in expenses:
        if str(expense['id']) == expense_id:
            expense_to_edit = expense
            break

    # If the expense is not found, return an error
    if not expense_to_edit:
        return jsonify({"error": "Expense not found"}), 404

    # Create a copy of the current (old) expense for logging
    old_expense = expense_to_edit.copy()

    # Update the fields based on the data received
    if 'inputdate' in data:
        expense_to_edit['date'] = data['inputdate']
    if 'category' in data:
        expense_to_edit['category'] = data['category']
    if 'person' in data:
        expense_to_edit['person'] = data['person']
    if 'amount' in data:
        expense_to_edit['amount'] = float(data['amount'])

    # Mark the expense as modified with the current time
    expense_to_edit['last_modified'] = current_time

    # Create a log entry for the action performed (edit)
    log_entry = {
        'action': 'Edited',
        'expense': {
            'id': expense_to_edit['id'],
            'date': expense_to_edit['date'],
            'category': expense_to_edit['category'],
            'person': expense_to_edit['person'],
            'amount': expense_to_edit['amount'],
            'added_date': expense_to_edit['added_date'],
            'last_modified': expense_to_edit['last_modified']
        },
        'timestamp': current_time
    }

    # Append the log entry to the log file
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as file:
            logs = json.load(file)

    logs.append(log_entry)
    save_log(logs)

    # Save the updated expenses list to the file
    save_expenses(expenses)

    return redirect("http://127.0.0.1:5000/")


# Remove expense
@app.route('/remove/<expense_id>', methods=['POST'])
def remove_expense(expense_id):
    expenses = load_expenses()
    expense_to_edit = next((exp for exp in expenses if str(exp['id']) == expense_id), None)

    if expense_to_edit:
        expenses = [exp for exp in expenses if str(exp['id']) != expense_id]
        save_expenses(expenses)
        log_entry = {
            'action': 'Removed',
            'expense': {
                'id': expense_to_edit['id'],
                'date': expense_to_edit['date'],
                'category': expense_to_edit['category'],
                'person': expense_to_edit['person'],
                'amount': expense_to_edit['amount'],
                'added_date': expense_to_edit['added_date'],
                'last_modified': expense_to_edit['last_modified']
            },
            'timestamp': current_time
        }

    # Append the log entry to the log file
        logs = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as file:
                logs = json.load(file)

        logs.append(log_entry)
        save_log(logs)

        return redirect("http://127.0.0.1:5000/")
    else:
        return jsonify({"status": "error", "message": "Expense not found"})


# View log
@app.route('/log', methods=['GET'])
def view_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as file:
            logs = json.load(file)
        return jsonify(logs)
    return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)

