from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import json
import os

# -----------------------------
# OOP Design
# -----------------------------
class Person:
    def __init__(self, name, national_id):
        self.name = name
        self.national_id = national_id

class Customer(Person):
    def __init__(self, name, national_id, account_number, balance, username=None, password=None):
        super().__init__(name, national_id)
        self.account_number = account_number
        self.balance = balance
        self.username = username
        self.password = password

class Employee(Person):
    def __init__(self, name, national_id, employee_id, position):
        super().__init__(name, national_id)
        self.employee_id = employee_id
        self.position = position
        self.monthly_target = 10
        self.tasks_completed = 0

# Load data from files
CUSTOMER_DATA_FILE = "customers.json"
EMPLOYEE_DATA_FILE = "employees.json"

# In-memory log of employee tasks
employee_task_log = []

customer_objects = {}
employee_objects = {}

def initialize_employees():
    # Check if employees.json exists and is not empty
    if os.path.exists(EMPLOYEE_DATA_FILE) and os.path.getsize(EMPLOYEE_DATA_FILE) > 0:
        return
    # Prompt user to create an initial manager via UI
    QtWidgets.QMessageBox.warning(None, "Setup Required", 
        f"No employees found in {EMPLOYEE_DATA_FILE}. Please create an initial manager account after launching the application.")
    print(f"Warning: {EMPLOYEE_DATA_FILE} not found or empty. Please create an initial manager.")

def initialize_customers():
    # Check if customers.json exists and is not empty
    if os.path.exists(CUSTOMER_DATA_FILE) and os.path.getsize(CUSTOMER_DATA_FILE) > 0:
        return
    # Prompt user to create an initial customer via UI
    QtWidgets.QMessageBox.warning(None, "Setup Required", 
        f"No customers found in {CUSTOMER_DATA_FILE}. Please create an initial customer account after launching the application.")
    print(f"Warning: {CUSTOMER_DATA_FILE} not found or empty. Please create an initial customer.")

def load_customers():
    if not os.path.exists(CUSTOMER_DATA_FILE) or os.path.getsize(CUSTOMER_DATA_FILE) == 0:
        initialize_customers()
        return {}, {}
    try:
        with open(CUSTOMER_DATA_FILE, "r") as f:
            data = json.load(f)
            customers = {}
            auth_dict = {}
            if isinstance(data, dict):
                for acc, d in data.items():
                    cust = Customer(
                        d["name"], 
                        d["national_id"], 
                        acc, 
                        d["balance"], 
                        d.get("username", f"user_{acc}"), 
                        d.get("password", "pass")
                    )
                    customers[acc] = cust
                    auth_dict[d.get("username", f"user_{acc}")] = (d.get("password", "pass"), cust)
            else:
                print(f"Error: {CUSTOMER_DATA_FILE} must contain a dictionary")
                return {}, {}
            return customers, auth_dict
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error loading {CUSTOMER_DATA_FILE}: {e}")
        return {}, {}

def save_customers():
    with open(CUSTOMER_DATA_FILE, "w") as f:
        json.dump({
            acc: {
                "username": c.username or f"user_{acc}",
                "password": c.password or "pass",
                "name": c.name,
                "national_id": c.national_id,
                "balance": c.balance
            } for acc, c in customer_objects.items()
        }, f, indent=4)

def load_employees():
    if not os.path.exists(EMPLOYEE_DATA_FILE) or os.path.getsize(EMPLOYEE_DATA_FILE) == 0:
        initialize_employees()
        return {}, {}
    try:
        with open(EMPLOYEE_DATA_FILE, "r") as f:
            data = json.load(f)
            employees = {}
            auth_dict = {}
            if isinstance(data, dict):
                for eid, d in data.items():
                    emp = Employee(d["name"], d["national_id"], eid, d["position"])
                    emp.monthly_target = d.get("monthly_target", 10)
                    emp.tasks_completed = d.get("tasks_completed", 0)
                    employees[eid] = emp
                    auth_dict[d.get("username", f"user_{eid}")] = (d.get("password", "pass"), emp)
            else:
                print(f"Error: {EMPLOYEE_DATA_FILE} must contain a dictionary")
                return {}, {}
            return employees, auth_dict
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error loading {EMPLOYEE_DATA_FILE}: {e}")
        return {}, {}

def save_employees():
    with open(EMPLOYEE_DATA_FILE, "w") as f:
        json.dump({
            eid: {
                "username": next((uname for uname, (pwd, emp) in employees.items() if emp.employee_id == eid), f"user_{eid}"),
                "password": next((pwd for uname, (pwd, emp) in employees.items() if emp.employee_id == eid), "pass"),
                "name": e.name,
                "national_id": e.national_id,
                "position": e.position,
                "monthly_target": getattr(e, "monthly_target", 10),
                "tasks_completed": getattr(e, "tasks_completed", 0)
            } for eid, e in employee_objects.items()
        }, f, indent=4)

customer_objects, customers = load_customers()
employee_objects, employees = load_employees()

# -----------------------------
# UI Design
# -----------------------------
class LoginPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bank System Login")
        self.setGeometry(100, 100, 400, 250)
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QVBoxLayout()   

        self.username = QtWidgets.QLineEdit(self)
        self.username.setPlaceholderText("Username")
        self.password = QtWidgets.QLineEdit(self)
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)

        self.role = QtWidgets.QComboBox(self)
        self.role.addItems(["Customer", "Employee"])

        self.check_balance_btn = QtWidgets.QPushButton("Check Balance", self)
        self.check_balance_btn.clicked.connect(self.check_balance)

        self.login_btn = QtWidgets.QPushButton("Login", self)
        self.login_btn.clicked.connect(self.handle_login)

        self.message = QtWidgets.QLabel("")
        self.message.setStyleSheet("color: red")

        layout.addWidget(QtWidgets.QLabel("Welcome to Our Creative Bank UI!"))
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.role)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.message)
        layout.addWidget(self.check_balance_btn)

        self.new_customer_btn = QtWidgets.QPushButton("Add New Customer", self)
        self.new_customer_btn.clicked.connect(self.add_new_customer)
        layout.addWidget(self.new_customer_btn)

        self.new_employee_btn = QtWidgets.QPushButton("Add New Employee", self)
        self.new_employee_btn.clicked.connect(self.add_new_employee)
        # Show Add New Employee button only if no employees exist or logged in as manager
        self.new_employee_btn.setVisible(not employee_objects)
        layout.addWidget(self.new_employee_btn)

        self.setLayout(layout)

    def check_balance(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "Check Balance", "Enter your account number:")
        if ok and text in customer_objects:
            balance = customer_objects[text].balance
            QtWidgets.QMessageBox.information(self, "Balance", f"Account balance: ${balance:.2f}")
        elif ok:
            QtWidgets.QMessageBox.warning(self, "Not Found", "Account number not found.")

    def handle_login(self):
        user = self.username.text()
        pwd = self.password.text()
        role = self.role.currentText()

        if role == "Customer" and user in customers and customers[user][0] == pwd:
            self.open_customer_ui(customers[user][1])
        elif role == "Employee" and user in employees and employees[user][0] == pwd:
            self.open_employee_ui(employees[user][1])
        else:
            self.message.setText("Invalid credentials. Please try again.")

    def open_customer_ui(self, customer):
        self.customer_ui = CustomerUI(customer)
        self.customer_ui.show()
        self.close()

    def open_employee_ui(self, employee):
        self.employee_ui = EmployeeUI(employee)
        if employee.position.lower() == "manager":
            self.new_employee_btn.setVisible(True)
        else:
            self.new_employee_btn.setVisible(False)
        self.employee_ui.show()
        self.close()

    def add_new_customer(self):
        name, ok1 = QtWidgets.QInputDialog.getText(self, "New Customer", "Enter name:")
        if not ok1: return
        national_id, ok2 = QtWidgets.QInputDialog.getText(self, "New Customer", "Enter national ID:")
        if not ok2: return
        for customer in customer_objects.values():
            if customer.national_id == national_id:
                QtWidgets.QMessageBox.warning(self, "Error", "National ID already exists.")
                return
        account_number, ok3 = QtWidgets.QInputDialog.getText(self, "New Customer", "Enter new account number:")
        if not ok3 or account_number in customer_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or existing account number.")
            return
        username, ok4 = QtWidgets.QInputDialog.getText(self, "New Customer", "Enter username:")
        if not ok4 or username in customers:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or existing username.")
            return
        password, ok5 = QtWidgets.QInputDialog.getText(self, "New Customer", "Enter password:", echo=QtWidgets.QLineEdit.Password)
        if not ok5 or not password:
            QtWidgets.QMessageBox.warning(self, "Error", "Password cannot be empty.")
            return
        balance, ok6 = QtWidgets.QInputDialog.getDouble(self, "New Customer", "Enter starting balance:", 0, 0.0, 1e9, 2)
        if not ok6: return

        new_customer = Customer(name, national_id, account_number, balance, username, password)
        customer_objects[account_number] = new_customer
        customers[username] = (password, new_customer)
        save_customers()
        QtWidgets.QMessageBox.information(self, "Success", f"Customer added successfully! Username: {username}, Password: {password}")

    def add_new_employee(self):
        name, ok1 = QtWidgets.QInputDialog.getText(self, "New Employee", "Enter name:")
        if not ok1: return
        national_id, ok2 = QtWidgets.QInputDialog.getText(self, "New Employee", "Enter national ID:")
        if not ok2: return
        for employee in employee_objects.values():
            if employee.national_id == national_id:
                QtWidgets.QMessageBox.warning(self, "Error", "National ID already exists.")
                return
        employee_id, ok3 = QtWidgets.QInputDialog.getText(self, "New Employee", "Enter employee ID:")
        if not ok3 or employee_id in employee_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or existing employee ID.")
            return
        username, ok4 = QtWidgets.QInputDialog.getText(self, "New Employee", "Enter username:")
        if not ok4 or username in employees:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or existing username.")
            return
        password, ok5 = QtWidgets.QInputDialog.getText(self, "New Employee", "Enter password:", echo=QtWidgets.QLineEdit.Password)
        if not ok5 or not password:
            QtWidgets.QMessageBox.warning(self, "Error", "Password cannot be empty.")
            return
        position, ok6 = QtWidgets.QInputDialog.getText(self, "New Employee", "Enter position (e.g., Employee, Manager):")
        if not ok6: return

        new_employee = Employee(name, national_id, employee_id, position)
        employee_objects[employee_id] = new_employee
        employees[username] = (password, new_employee)
        save_employees()
        QtWidgets.QMessageBox.information(self, "Success", f"Employee added successfully! Username: {username}, Password: {password}")

# -----------------------------
# Customer UI
# -----------------------------
class CustomerUI(QtWidgets.QWidget):
    def __init__(self, customer):
        super().__init__()
        self.customer = customer
        self.setWindowTitle("Customer Dashboard")
        self.setGeometry(200, 200, 400, 300)
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QFormLayout()
        layout.addRow("Name:", QtWidgets.QLabel(self.customer.name))
        layout.addRow("National ID:", QtWidgets.QLabel(self.customer.national_id))
        layout.addRow("Account Number:", QtWidgets.QLabel(self.customer.account_number))
        layout.addRow("Balance:", QtWidgets.QLabel(f"${self.customer.balance:.2f}"))

        self.refresh_btn = QtWidgets.QPushButton("Refresh Balance")
        self.refresh_btn.clicked.connect(self.refresh_balance)
        layout.addRow(self.refresh_btn)

        self.home_button = QtWidgets.QPushButton("Back to Home")
        self.home_button.clicked.connect(self.back_to_home)
        layout.addRow(self.home_button)

        self.setLayout(layout)

    def refresh_balance(self):
        self.initUI()

    def back_to_home(self):
        self.close()
        self.login_page = LoginPage()
        self.login_page.show()

# -----------------------------
# Employee UI
# -----------------------------
class EmployeeUI(QtWidgets.QWidget):
    def __init__(self, employee):
        super().__init__()
        self.employee = employee
        self.setWindowTitle("Employee Dashboard")
        self.setGeometry(200, 200, 400, 400)
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QFormLayout()
        layout.addRow("Name:", QtWidgets.QLabel(self.employee.name))
        layout.addRow("National ID:", QtWidgets.QLabel(self.employee.national_id))
        layout.addRow("Employee ID:", QtWidgets.QLabel(self.employee.employee_id))
        layout.addRow("Position:", QtWidgets.QLabel(self.employee.position))
        layout.addRow("Monthly Target:", QtWidgets.QLabel(str(self.employee.monthly_target)))
        layout.addRow("Tasks Completed:", QtWidgets.QLabel(str(self.employee.tasks_completed)))

        self.complete_task_btn = QtWidgets.QPushButton("Complete Task")
        self.complete_task_btn.clicked.connect(self.complete_task)
        layout.addRow(self.complete_task_btn)

        self.transfer_button = QtWidgets.QPushButton("Transfer Between Accounts")
        self.transfer_button.clicked.connect(self.transfer_money)
        layout.addRow(self.transfer_button)

        self.deposit_button = QtWidgets.QPushButton("Deposit to Account")
        self.deposit_button.clicked.connect(self.deposit_to_account)
        layout.addRow(self.deposit_button)

        self.withdraw_button = QtWidgets.QPushButton("Withdraw from Account")
        self.withdraw_button.clicked.connect(self.withdraw_from_account)
        layout.addRow(self.withdraw_button)

        self.view_accounts_btn = QtWidgets.QPushButton("View All Bank Accounts")
        self.view_accounts_btn.clicked.connect(self.view_all_accounts)
        layout.addRow(self.view_accounts_btn)

        if self.employee.position.lower() == "manager":
            self.change_username_btn = QtWidgets.QPushButton("Change Employee Username", self)
            self.change_username_btn.clicked.connect(self.change_employee_username)
            layout.addRow(self.change_username_btn)

            self.change_password_btn = QtWidgets.QPushButton("Change Employee Password", self)
            self.change_password_btn.clicked.connect(self.change_employee_password)
            layout.addRow(self.change_password_btn)

            self.change_customer_username_btn = QtWidgets.QPushButton("Change Customer Username", self)
            self.change_customer_username_btn.clicked.connect(self.change_customer_username)
            layout.addRow(self.change_customer_username_btn)

            self.change_customer_password_btn = QtWidgets.QPushButton("Change Customer Password", self)
            self.change_customer_password_btn.clicked.connect(self.change_customer_password)
            layout.addRow(self.change_customer_password_btn)

        self.home_button = QtWidgets.QPushButton("Back to Home")
        self.home_button.clicked.connect(self.back_to_home)
        layout.addRow(self.home_button)

        self.setLayout(layout)

    def complete_task(self):
        self.employee.tasks_completed += 1
        QtWidgets.QMessageBox.information(self, "Task", f"Task completed! Total: {self.employee.tasks_completed}")
        self.initUI()

    def change_employee_username(self):
        if self.employee.position.lower() != "manager":
            QtWidgets.QMessageBox.warning(self, "Error", "Only managers can change usernames.")
            return
        eid, ok1 = QtWidgets.QInputDialog.getText(self, "Change Employee Username", "Enter employee ID:")
        if not ok1 or eid not in employee_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or non-existent employee ID.")
            return
        old_username = next((uname for uname, (pwd, emp) in employees.items() if emp.employee_id == eid), None)
        if not old_username:
            QtWidgets.QMessageBox.warning(self, "Error", "Employee not found in authentication system.")
            return
        new_username, ok2 = QtWidgets.QInputDialog.getText(self, "Change Employee Username", f"Enter new username for {eid}:")
        if not ok2 or new_username in employees:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or existing username.")
            return
        employees[new_username] = employees.pop(old_username)
        save_employees()
        QtWidgets.QMessageBox.information(self, "Success", f"Employee username changed to {new_username} for employee {eid}.")

    def change_employee_password(self):
        if self.employee.position.lower() != "manager":
            QtWidgets.QMessageBox.warning(self, "Error", "Only managers can change passwords.")
            return
        eid, ok1 = QtWidgets.QInputDialog.getText(self, "Change Employee Password", "Enter employee ID:")
        if not ok1 or eid not in employee_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or non-existent employee ID.")
            return
        username = next((uname for uname, (pwd, emp) in employees.items() if emp.employee_id == eid), None)
        if not username:
            QtWidgets.QMessageBox.warning(self, "Error", "Employee not found in authentication system.")
            return
        new_password, ok2 = QtWidgets.QInputDialog.getText(self, "Change Employee Password", f"Enter new password for {eid}:", echo=QtWidgets.QLineEdit.Password)
        if not ok2 or not new_password:
            QtWidgets.QMessageBox.warning(self, "Error", "Password cannot be empty.")
            return
        employees[username] = (new_password, employees[username][1])
        save_employees()
        QtWidgets.QMessageBox.information(self, "Success", f"Employee password changed for employee {eid}.")

    def change_customer_username(self):
        if self.employee.position.lower() != "manager":
            QtWidgets.QMessageBox.warning(self, "Error", "Only managers can change customer usernames.")
            return
        acc_num, ok1 = QtWidgets.QInputDialog.getText(self, "Change Customer Username", "Enter account number:")
        if not ok1 or acc_num not in customer_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or non-existent account number.")
            return
        old_username = next((uname for uname, (pwd, cust) in customers.items() if cust.account_number == acc_num), None)
        if not old_username:
            QtWidgets.QMessageBox.warning(self, "Error", "Customer not found in authentication system.")
            return
        new_username, ok2 = QtWidgets.QInputDialog.getText(self, "Change Customer Username", f"Enter new username for account {acc_num}:")
        if not ok2 or new_username in customers:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or existing username.")
            return
        customers[new_username] = customers.pop(old_username)
        customer_objects[acc_num].username = new_username
        save_customers()
        QtWidgets.QMessageBox.information(self, "Success", f"Customer username changed to {new_username} for account {acc_num}.")

    def change_customer_password(self):
        if self.employee.position.lower() != "manager":
            QtWidgets.QMessageBox.warning(self, "Error", "Only managers can change customer passwords.")
            return
        acc_num, ok1 = QtWidgets.QInputDialog.getText(self, "Change Customer Password", "Enter account number:")
        if not ok1 or acc_num not in customer_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or non-existent account number.")
            return
        username = next((uname for uname, (pwd, cust) in customers.items() if cust.account_number == acc_num), None)
        if not username:
            QtWidgets.QMessageBox.warning(self, "Error", "Customer not found in authentication system.")
            return
        new_password, ok2 = QtWidgets.QInputDialog.getText(self, "Change Customer Password", f"Enter new password for account {acc_num}:", echo=QtWidgets.QLineEdit.Password)
        if not ok2 or not new_password:
            QtWidgets.QMessageBox.warning(self, "Error", "Password cannot be empty.")
            return
        customers[username] = (new_password, customers[username][1])
        customer_objects[acc_num].password = new_password
        save_customers()
        QtWidgets.QMessageBox.information(self, "Success", f"Customer password changed for account {acc_num}.")

    def transfer_money(self):
        from_acc, ok1 = QtWidgets.QInputDialog.getText(self, "Transfer", "Enter source account number:")
        if not ok1 or from_acc not in customer_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or non-existent source account number.")
            return
        to_acc, ok2 = QtWidgets.QInputDialog.getText(self, "Transfer", "Enter target account number:")
        if not ok2 or to_acc not in customer_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or non-existent target account number.")
            return
        max_transfer = customer_objects[from_acc].balance
        amount, ok3 = QtWidgets.QInputDialog.getDouble(self, "Transfer", "Enter amount to transfer:", 0, 0.01, max_transfer, 2)
        if ok3:
            if amount > max_transfer:
                QtWidgets.QMessageBox.warning(self, "Error", "Insufficient funds in source account.")
            else:
                customer_objects[from_acc].balance -= amount
                customer_objects[to_acc].balance += amount
                save_customers()
                QtWidgets.QMessageBox.information(self, "Transferred", f"Transferred ${amount:.2f} from {from_acc} to {to_acc}.")

    def deposit_to_account(self):
        acc, ok1 = QtWidgets.QInputDialog.getText(self, "Deposit", "Enter account number:")
        if not ok1 or acc not in customer_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid account number.")
            return
        amount, ok2 = QtWidgets.QInputDialog.getDouble(self, "Deposit", "Enter deposit amount:", 0, 0.01, 1e9, 2)
        if ok2:
            customer_objects[acc].balance += amount
            save_customers()
            QtWidgets.QMessageBox.information(self, "Deposit", f"Deposited ${amount:.2f} to account {acc}.")

    def withdraw_from_account(self):
        acc, ok1 = QtWidgets.QInputDialog.getText(self, "Withdraw", "Enter account number:")
        if not ok1 or acc not in customer_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid account number.")
            return
        max_amount = customer_objects[acc].balance
        amount, ok2 = QtWidgets.QInputDialog.getDouble(self, "Withdraw", "Enter withdrawal amount:", 0, 0.01, max_amount, 2)
        if ok2:
            if amount > max_amount:
                QtWidgets.QMessageBox.warning(self, "Error", "Insufficient funds.")
            else:
                customer_objects[acc].balance -= amount
                save_customers()
                QtWidgets.QMessageBox.information(self, "Withdraw", f"Withdrew ${amount:.2f} from account {acc}.")

    def view_all_accounts(self):
        accounts_info = ""
        for acc_num, cust in customer_objects.items():
            accounts_info += f"Account: {acc_num}, Name: {cust.name}, Balance: ${cust.balance:.2f}\n"
        QtWidgets.QMessageBox.information(self, "All Bank Accounts", accounts_info)

    def back_to_home(self):
        self.close()
        self.login_page = LoginPage()
        self.login_page.show()

# -----------------------------
# App Entry Point
# -----------------------------
def main():
    app = QtWidgets.QApplication(sys.argv)
    login = LoginPage()
    login.show()

    def handle_exit():
        save_customers()
        save_employees()

    app.aboutToQuit.connect(handle_exit)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()