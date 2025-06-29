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
    def __init__(self, name, national_id, account_number, balance):
        super().__init__(name, national_id)
        self.account_number = account_number
        self.balance = balance

class Employee(Person):
    def __init__(self, name, national_id, employee_id, position):
        super().__init__(name, national_id)
        self.employee_id = employee_id
        self.position = position
        self.monthly_target = 10
        self.tasks_completed = 0

# Load data from file
DATA_FILE = "customers.json"

# In-memory log of employee tasks
employee_task_log = []

customer_objects = {}

def load_customers():
    if not os.path.exists(DATA_FILE):
        return {
            "10001": Customer("John Doe", "123456789", "10001", 1500.75),
            "10002": Customer("Alice Brown", "223344556", "10002", 2000.00)
        }
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
        return {acc: Customer(d["name"], d["national_id"], acc, d["balance"]) for acc, d in data.items()}

def save_customers():
    with open(DATA_FILE, "w") as f:
        json.dump({acc: {"name": c.name, "national_id": c.national_id, "balance": c.balance} for acc, c in customer_objects.items()}, f)

customer_objects = load_customers()

customers = {
    "customer1": ("pass123", customer_objects["10001"]),
    "customer2": ("pass456", customer_objects["10002"])
}

employees = {
    "employee1": ("admin456", Employee("Jane Smith", "987654321", "E001", "Employee")),
    "manager1": ("managerpass", Employee("Bob Johnson", "112233445", "M001", "Manager"))
}

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

        self.setLayout(layout)

    def check_balance(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "Check Balance", "Enter your account number:")
        if ok and text in customer_objects:
            balance = customer_objects[text].balance
            QtWidgets.QMessageBox.information(self, "Balance", f"Account {text} has a balance of: ${balance:.2f}")
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
        balance, ok4 = QtWidgets.QInputDialog.getDouble(self, "New Customer", "Enter starting balance:", 0, 0.0, 1e9, 2)
        if not ok4: return

        new_customer = Customer(name, national_id, account_number, balance)
        customer_objects[account_number] = new_customer
        customers[f"user_{account_number}"] = ("pass", new_customer)
        save_customers()
        QtWidgets.QMessageBox.information(self, "Success", f"Customer {name} added successfully! Username: user_{account_number}, Password: pass")

    def open_employee_ui(self, employee):
        self.employee_ui = EmployeeUI(employee)
        self.employee_ui.show()
        self.close()

class EmployeeUI(QtWidgets.QWidget):
    def __init__(self, employee):
        super().__init__()
        self.employee = employee
        self.setWindowTitle("Employee Dashboard")
        self.setGeometry(200, 200, 400, 350)
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QFormLayout()
        layout.addRow("Name:", QtWidgets.QLabel(self.employee.name))
        layout.addRow("National ID:", QtWidgets.QLabel(self.employee.national_id))
        layout.addRow("Employee ID:", QtWidgets.QLabel(self.employee.employee_id))
        layout.addRow("Position:", QtWidgets.QLabel(self.employee.position))
        layout.addRow("Monthly Target:", QtWidgets.QLabel(str(self.employee.monthly_target)))
        layout.addRow("Tasks Completed:", QtWidgets.QLabel(str(self.employee.tasks_completed)))

        self.perform_task_btn = QtWidgets.QPushButton("Perform Task")
        self.perform_task_btn.clicked.connect(self.perform_task)
        layout.addRow(self.perform_task_btn)

        self.view_accounts_btn = QtWidgets.QPushButton("View All Bank Accounts")
        self.view_accounts_btn.clicked.connect(self.view_all_accounts)
        layout.addRow(self.view_accounts_btn)

        self.delete_account_btn = QtWidgets.QPushButton("Delete Account")
        self.delete_account_btn.clicked.connect(self.delete_account)
        layout.addRow(self.delete_account_btn)

        self.home_button = QtWidgets.QPushButton("Back to Home")
        self.home_button.clicked.connect(self.back_to_home)
        layout.addRow(self.home_button)

        self.setLayout(layout)

    def perform_task(self):
        self.employee.tasks_completed += 1
        employee_task_log.append(f"{self.employee.name} performed a task. Total: {self.employee.tasks_completed}")
        QtWidgets.QMessageBox.information(self, "Task Performed", f"Task done. Total tasks: {self.employee.tasks_completed}")
        self.initUI()

    def view_all_accounts(self):
        all_info = ""
        for acc, cust in customer_objects.items():
            all_info += f"\nAccount: {acc}, Name: {cust.name}, Balance: ${cust.balance:.2f}"
        QtWidgets.QMessageBox.information(self, "All Accounts", all_info)

    def delete_account(self):
        acc_num, ok = QtWidgets.QInputDialog.getText(self, "Delete Account", "Enter account number to delete:")
        if ok:
            if acc_num in customer_objects:
                del customer_objects[acc_num]
                to_delete = [k for k, v in customers.items() if v[1].account_number == acc_num]
                for k in to_delete:
                    del customers[k]
                save_customers()
                QtWidgets.QMessageBox.information(self, "Deleted", f"Account {acc_num} deleted.")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Account number not found.")

    def back_to_home(self):
        self.close()
        self.login_page = LoginPage()
        self.login_page.show()

class CustomerUI(QtWidgets.QWidget):
    def __init__(self, customer):
        super().__init__()
        self.customer = customer
        self.setWindowTitle("Customer Dashboard")
        self.setGeometry(150, 150, 400, 300)
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QFormLayout()

        layout.addRow("Name:", QtWidgets.QLabel(self.customer.name))
        layout.addRow("National ID:", QtWidgets.QLabel(self.customer.national_id))
        layout.addRow("Account Number:", QtWidgets.QLabel(self.customer.account_number))
        layout.addRow("Balance:", QtWidgets.QLabel(f"${self.customer.balance:.2f}"))

        self.transfer_button = QtWidgets.QPushButton("Transfer to Another Account")
        self.transfer_button.clicked.connect(self.transfer_money)
        layout.addRow(self.transfer_button)

        self.home_button = QtWidgets.QPushButton("Back to Home")
        self.home_button.clicked.connect(self.back_to_home)
        layout.addRow(self.home_button)

        self.setLayout(layout)

    def transfer_money(self):
        target_acc, ok1 = QtWidgets.QInputDialog.getText(self, "Transfer", "Enter target account number:")
        if not ok1 or target_acc not in customer_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or non-existent account number.")
            return
        amount, ok2 = QtWidgets.QInputDialog.getDouble(self, "Transfer", "Enter amount to transfer:", 0, 0.01, self.customer.balance, 2)
        if ok2:
            if amount > self.customer.balance:
                QtWidgets.QMessageBox.warning(self, "Error", "Insufficient funds.")
            else:
                self.customer.balance -= amount
                customer_objects[target_acc].balance += amount
                save_customers()
                QtWidgets.QMessageBox.information(self, "Transferred", f"Transferred ${amount:.2f} to account {target_acc}.")
                self.initUI()

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

    app.aboutToQuit.connect(handle_exit)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
