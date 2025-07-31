from PyQt5 import QtWidgets, QtCore
import sys
import traceback
import hashlib
from db import Database
from add_customer import AddCustomerWindow
from add_employee import AddEmployeeWindow
from globals import customer_objects, employee_objects, account_objects, transactions, activity_logs
import mysql.connector
from models.transaction import Transaction
from models.customer import Customer
from models.employee import Employee
from models.account import Account
from models.activitylog import ActivityLog


class TransferDialog(QtWidgets.QDialog):
    def __init__(self, db, from_account_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.from_account_id = from_account_id
        self.setWindowTitle("Transfer Funds")
        self.setGeometry(150, 150, 400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        self.from_account_label = QtWidgets.QLabel("From Account ID:")
        self.from_account_input = QtWidgets.QLineEdit()
        self.from_account_input.setText(self.from_account_id)
        self.from_account_input.setEnabled(False)
        layout.addWidget(self.from_account_label)
        layout.addWidget(self.from_account_input)

        self.to_account_label = QtWidgets.QLabel("To Account Number:")
        self.to_account_input = QtWidgets.QLineEdit()
        layout.addWidget(self.to_account_label)
        layout.addWidget(self.to_account_input)

        self.amount_label = QtWidgets.QLabel("Amount:")
        self.amount_input = QtWidgets.QLineEdit()
        layout.addWidget(self.amount_label)
        layout.addWidget(self.amount_input)

        self.transfer_button = QtWidgets.QPushButton("Transfer")
        self.transfer_button.clicked.connect(self.perform_transfer)
        layout.addWidget(self.transfer_button)

        self.status_label = QtWidgets.QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def perform_transfer(self):
        from_account_id = self.from_account_input.text()
        to_account_number = self.to_account_input.text()
        try:
            amount = float(self.amount_input.text())
            if not to_account_number:
                self.status_label.setText("Please enter a destination account number!")
                return
            if from_account_id not in account_objects:
                self.status_label.setText("Invalid source account!")
                return
            to_account_id = next((acc_id for acc_id, acc in account_objects.items() if acc.AccountNumber == to_account_number), None)
            if not to_account_id:
                self.status_label.setText("Invalid destination account number!")
                return
            if amount <= 0:
                self.status_label.setText("Amount must be positive!")
                return
            if account_objects[from_account_id].Balance < amount:
                self.status_label.setText("Insufficient funds!")
                return

            account_objects[from_account_id].Balance -= amount
            account_objects[to_account_id].Balance += amount

            self.db.cursor.execute("UPDATE account SET Balance = %s WHERE AccountID = %s",
                                   (account_objects[from_account_id].Balance, from_account_id))
            self.db.cursor.execute("UPDATE account SET Balance = %s WHERE AccountID = %s",
                                   (account_objects[to_account_id].Balance, to_account_id))
            self.db.conn.commit()

            from_customer_id = next((c.customerID for c in customer_objects.values() if c.customerAccountID == from_account_id), None)
            if from_customer_id:
                import uuid
                from models.transaction import Transaction
                transaction_id = str(uuid.uuid4())
                transaction = Transaction(transaction_id, "Transfer", amount, QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.ISODate), from_customer_id)
                self.db.save_transaction(transaction)

            self.status_label.setText("Transfer successful!")
            self.accept()
        except ValueError:
            self.status_label.setText("Invalid amount!")
        except mysql.connector.Error as e:
            self.status_label.setText(f"Database error: {str(e)}")
            self.db.conn.rollback()

class EmployeeDashboard(QtWidgets.QWidget):
    def __init__(self, db, employee, is_manager=False, login_page=None):
        super().__init__()  # FIXED: Removed parent parameter to prevent overlap
        self.db = db
        self.employee = employee
        self.is_manager = is_manager
        self.login_page = login_page
        self.setWindowTitle(f"Employee Dashboard - {employee.employeeUserName}")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()

    def init_ui(self):
        if not self.employee or not hasattr(self.employee, 'employeeID') or str(self.employee.employeeID) not in employee_objects:
            print(f"Invalid employee data or not found: {self.employee.employeeUserName if self.employee else 'None'}: "
                  f"employeeID={self.employee.employeeID if self.employee else 'None'}, "
                  f"employee_objects keys={list(employee_objects.keys())}")
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid employee data.")
            self.close()
            return
        
        # FIXED: Create main layout properly
        main_layout = QtWidgets.QVBoxLayout()
        
        # Employee info section
        info_layout = QtWidgets.QFormLayout()
        info_layout.addRow("Name:", QtWidgets.QLabel(str(self.employee.employeeName) or "N/A"))
        info_layout.addRow("Employee ID:", QtWidgets.QLabel(str(self.employee.employeeID) if self.employee.employeeID is not None else "N/A"))
        info_layout.addRow("Username:", QtWidgets.QLabel(str(self.employee.employeeUserName) or "N/A"))
        info_layout.addRow("Position:", QtWidgets.QLabel(str(self.employee.position) or "N/A"))
        info_layout.addRow("Email:", QtWidgets.QLabel(str(self.employee.employeeEmail) or "N/A"))
        info_layout.addRow("Phone:", QtWidgets.QLabel(str(self.employee.employeePhone) or "N/A"))
        
        info_widget = QtWidgets.QWidget()
        info_widget.setLayout(info_layout)
        main_layout.addWidget(info_widget)

        # Tabs section
        tabs = QtWidgets.QTabWidget()

        # Customer List Tab
        self.customer_list_widget = QtWidgets.QWidget()
        customer_layout = QtWidgets.QVBoxLayout()
        self.customer_table = QtWidgets.QTableWidget()
        self.customer_table.setColumnCount(5)
        self.customer_table.setHorizontalHeaderLabels(["Customer ID", "Username", "Name", "Account ID", "Balance"])
        self.load_customers()
        customer_layout.addWidget(self.customer_table)
        self.customer_list_widget.setLayout(customer_layout)
        tabs.addTab(self.customer_list_widget, "Customer List")

        # Transaction History Tab
        self.transaction_widget = QtWidgets.QWidget()
        transaction_layout = QtWidgets.QVBoxLayout()
        self.transaction_customer_input = QtWidgets.QComboBox()
        # FIXED: Convert customerID to string for QComboBox
        self.transaction_customer_input.addItems([str(c.customerID) for c in customer_objects.values()])
        self.transaction_table = QtWidgets.QTableWidget()
        self.transaction_table.setColumnCount(5)
        self.transaction_table.setHorizontalHeaderLabels(["Transaction ID", "Type", "Amount", "Date", "Customer ID"])
        self.transaction_customer_input.currentTextChanged.connect(self.load_transactions)
        transaction_layout.addWidget(QtWidgets.QLabel("Select Customer:"))
        transaction_layout.addWidget(self.transaction_customer_input)
        transaction_layout.addWidget(self.transaction_table)

        self.transfer_button = QtWidgets.QPushButton("Transfer Between Accounts")
        self.transfer_button.clicked.connect(self.transfer_money)
        transaction_layout.addWidget(self.transfer_button)

        self.deposit_button = QtWidgets.QPushButton("Deposit to Account")
        self.deposit_button.clicked.connect(self.deposit_to_account)
        transaction_layout.addWidget(self.deposit_button)

        self.withdraw_button = QtWidgets.QPushButton("Withdraw from Account")
        self.withdraw_button.clicked.connect(self.withdraw_from_account)
        transaction_layout.addWidget(self.withdraw_button)

        self.view_accounts_btn = QtWidgets.QPushButton("View All Bank Accounts")
        self.view_accounts_btn.clicked.connect(self.view_all_accounts)
        transaction_layout.addWidget(self.view_accounts_btn)

        self.transaction_widget.setLayout(transaction_layout)
        tabs.addTab(self.transaction_widget, "Transaction History")

        # Manager Privileges Tab (if manager)
        if self.is_manager:
            self.manager_widget = QtWidgets.QWidget()
            manager_layout = QtWidgets.QVBoxLayout()
            self.activity_log_table = QtWidgets.QTableWidget()
            self.activity_log_table.setColumnCount(6)
            self.activity_log_table.setHorizontalHeaderLabels(["Log ID", "User Type", "User ID", "Action Type", "Amount", "Time"])
            self.load_activity_logs()
            manager_layout.addWidget(self.activity_log_table)

            self.change_employee_username_btn = QtWidgets.QPushButton("Change Employee Username")
            self.change_employee_username_btn.clicked.connect(self.change_employee_username)
            manager_layout.addWidget(self.change_employee_username_btn)

            self.change_employee_password_btn = QtWidgets.QPushButton("Change Employee Password")
            self.change_employee_password_btn.clicked.connect(self.change_employee_password)
            manager_layout.addWidget(self.change_employee_password_btn)

            self.change_customer_username_btn = QtWidgets.QPushButton("Change Customer Username")
            self.change_customer_username_btn.clicked.connect(self.change_customer_username)
            manager_layout.addWidget(self.change_customer_username_btn)

            self.change_customer_password_btn = QtWidgets.QPushButton("Change Customer Password")
            self.change_customer_password_btn.clicked.connect(self.change_customer_password)
            manager_layout.addWidget(self.change_customer_password_btn)

            self.manager_widget.setLayout(manager_layout)
            tabs.addTab(self.manager_widget, "Manager Controls")

        main_layout.addWidget(tabs)

        self.home_button = QtWidgets.QPushButton("Back to Home")
        self.home_button.clicked.connect(self.back_to_home)
        main_layout.addWidget(self.home_button)

        self.setLayout(main_layout)

    def load_customers(self):
        self.customer_table.setRowCount(len(customer_objects))
        for row, customer in enumerate(customer_objects.values()):
            # FIXED: Convert all values to strings for QTableWidget
            self.customer_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(customer.customerID)))
            self.customer_table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(customer.customerUserName)))
            self.customer_table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(customer.customerName or "N/A")))
            self.customer_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(customer.customerAccountID or "None")))
            balance = account_objects.get(str(customer.customerAccountID), None)
            self.customer_table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(balance.Balance) if balance else "0"))

    def load_transactions(self):
        customer_id = self.transaction_customer_input.currentText()
        self.transaction_table.setRowCount(0)
        for transaction in transactions.values():
            # FIXED: Compare as strings consistently
            if str(transaction.customerID) == customer_id:
                row = self.transaction_table.rowCount()
                self.transaction_table.insertRow(row)
                # FIXED: Convert all values to strings for QTableWidget
                self.transaction_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(transaction.transactionID)))
                self.transaction_table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(transaction.transactionType)))
                self.transaction_table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(transaction.amount)))
                self.transaction_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(transaction.transactionDate)))
                self.transaction_table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(transaction.customerID)))

    def load_activity_logs(self):
        self.activity_log_table.setRowCount(len(activity_logs))
        for row, log in enumerate(activity_logs.values()):
            # FIXED: Convert all values to strings for QTableWidget
            self.activity_log_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(log.logID)))
            self.activity_log_table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(log.userType)))
            self.activity_log_table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(log.userID)))
            self.activity_log_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(log.actionType)))
            self.activity_log_table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(log.amount)))
            self.activity_log_table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(log.logTime)))

    def transfer_money(self):
        from_acc, ok1 = QtWidgets.QInputDialog.getText(self, "Transfer", "Enter source account number:")
        if not ok1 or from_acc not in account_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or non-existent source account number.")
            return
        to_acc, ok2 = QtWidgets.QInputDialog.getText(self, "Transfer", "Enter target account number:")
        if not ok2 or to_acc not in account_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or non-existent target account number.")
            return
        max_transfer = account_objects[from_acc].Balance
        amount, ok3 = QtWidgets.QInputDialog.getDouble(self, "Transfer", "Enter amount to transfer:", 0, 0.01, max_transfer, 2)
        if ok3:
            if amount > max_transfer:
                QtWidgets.QMessageBox.warning(self, "Error", "Insufficient funds in source account.")
            else:
                account_objects[from_acc].Balance -= amount
                account_objects[to_acc].Balance += amount
                self.db.cursor.execute("UPDATE account SET Balance = %s WHERE AccountID = %s",
                                       (account_objects[from_acc].Balance, from_acc))
                self.db.cursor.execute("UPDATE account SET Balance = %s WHERE AccountID = %s",
                                       (account_objects[to_acc].Balance, to_acc))
                self.db.conn.commit()
                QtWidgets.QMessageBox.information(self, "Transferred", f"Transferred ${amount:.2f} from {from_acc} to {to_acc}.")
                self.load_customers()

    def deposit_to_account(self):
        acc, ok1 = QtWidgets.QInputDialog.getText(self, "Deposit", "Enter account number:")
        if not ok1 or acc not in account_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid account number.")
            return
        amount, ok2 = QtWidgets.QInputDialog.getDouble(self, "Deposit", "Enter deposit amount:", 0, 0.01, 1e9, 2)
        if ok2:
            account_objects[acc].Balance += amount
            self.db.cursor.execute("UPDATE account SET Balance = %s WHERE AccountID = %s",
                                   (account_objects[acc].Balance, acc))
            self.db.conn.commit()
            QtWidgets.QMessageBox.information(self, "Deposit", f"Deposited ${amount:.2f} to account {acc}.")
            self.load_customers()

    def withdraw_from_account(self):
        acc, ok1 = QtWidgets.QInputDialog.getText(self, "Withdraw", "Enter account number:")
        if not ok1 or acc not in account_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid account number.")
            return
        max_amount = account_objects[acc].Balance
        amount, ok2 = QtWidgets.QInputDialog.getDouble(self, "Withdraw", "Enter withdrawal amount:", 0, 0.01, max_amount, 2)
        if ok2:
            if amount > max_amount:
                QtWidgets.QMessageBox.warning(self, "Error", "Insufficient funds.")
            else:
                account_objects[acc].Balance -= amount
                self.db.cursor.execute("UPDATE account SET Balance = %s WHERE AccountID = %s",
                                       (account_objects[acc].Balance, acc))
                self.db.conn.commit()
                QtWidgets.QMessageBox.information(self, "Withdraw", f"Withdrew ${amount:.2f} from account {acc}.")
                self.load_customers()

    def view_all_accounts(self):
        accounts_info = "\n".join([f"Account: {acc_id}, Name: {c.customerName or 'N/A'}, Balance: ${acc.Balance:.2f}"
                                  for acc_id, acc in account_objects.items()
                                  for c in customer_objects.values() if c.customerAccountID == acc_id])
        QtWidgets.QMessageBox.information(self, "All Bank Accounts", accounts_info if accounts_info else "No accounts found.")

    def change_employee_username(self):
        if not self.is_manager:
            QtWidgets.QMessageBox.warning(self, "Error", "Only managers can change usernames.")
            return
        eid, ok1 = QtWidgets.QInputDialog.getText(self, "Change Employee Username", "Enter employee ID:")
        if not ok1 or eid not in employee_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or non-existent employee ID.")
            return
        old_username = next((uname for uname, (pwd, emp) in employee_objects.items() if emp.employee_id == eid), None)
        if not old_username:
            QtWidgets.QMessageBox.warning(self, "Error", "Employee not found in authentication system.")
            return
        new_username, ok2 = QtWidgets.QInputDialog.getText(self, "Change Employee Username", f"Enter new username for {eid}:")
        if not ok2 or new_username in employee_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or existing username.")
            return
        employee_objects[new_username] = employee_objects.pop(old_username)
        employee_objects[eid].employeeUserName = new_username
        self.db.update_employee_username(eid, new_username)
        QtWidgets.QMessageBox.information(self, "Success", f"Employee username changed to {new_username} for employee {eid}.")

    def change_employee_password(self):
        if not self.is_manager:
            QtWidgets.QMessageBox.warning(self, "Error", "Only managers can change passwords.")
            return
        eid, ok1 = QtWidgets.QInputDialog.getText(self, "Change Employee Password", "Enter employee ID:")
        if not ok1 or eid not in employee_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or non-existent employee ID.")
            return
        username = next((uname for uname, (pwd, emp) in employee_objects.items() if emp.employee_id == eid), None)
        if not username:
            QtWidgets.QMessageBox.warning(self, "Error", "Employee not found in authentication system.")
            return
        new_password, ok2 = QtWidgets.QInputDialog.getText(self, "Change Employee Password", f"Enter new password for {eid}:", echo=QtWidgets.QLineEdit.Password)
        if not ok2 or not new_password:
            QtWidgets.QMessageBox.warning(self, "Error", "Password cannot be empty.")
            return
        hashed_password = hashlib.md5(new_password.encode('utf-8')).hexdigest()
        employee_objects[username] = (hashed_password, employee_objects[username][1])
        employee_objects[eid].employeePassword = hashed_password
        self.db.update_employee_password(eid, hashed_password)
        QtWidgets.QMessageBox.information(self, "Success", f"Employee password changed for employee {eid}.")

    def change_customer_username(self):
        if not self.is_manager:
            QtWidgets.QMessageBox.warning(self, "Error", "Only managers can change customer usernames.")
            return
        acc_num, ok1 = QtWidgets.QInputDialog.getText(self, "Change Customer Username", "Enter account number:")
        if not ok1 or acc_num not in account_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or non-existent account number.")
            return
        customer = next((c for c in customer_objects.values() if c.customerAccountID == acc_num), None)
        if not customer:
            QtWidgets.QMessageBox.warning(self, "Error", "Customer not found.")
            return
        old_username = next((uname for uname, (pwd, cust) in customer_objects.items() if cust.customerAccountID == acc_num), None)
        if not old_username:
            QtWidgets.QMessageBox.warning(self, "Error", "Customer not found in authentication system.")
            return
        new_username, ok2 = QtWidgets.QInputDialog.getText(self, "Change Customer Username", f"Enter new username for account {acc_num}:")
        if not ok2 or new_username in customer_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or existing username.")
            return
        customer_objects[new_username] = customer_objects.pop(old_username)
        customer.customerUserName = new_username
        self.db.update_customer_username(acc_num, new_username)
        QtWidgets.QMessageBox.information(self, "Success", f"Customer username changed to {new_username} for account {acc_num}.")

    def change_customer_password(self):
        if not self.is_manager:
            QtWidgets.QMessageBox.warning(self, "Error", "Only managers can change customer passwords.")
            return
        acc_num, ok1 = QtWidgets.QInputDialog.getText(self, "Change Customer Password", "Enter account number:")
        if not ok1 or acc_num not in account_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or non-existent account number.")
            return
        customer = next((c for c in customer_objects.values() if c.customerAccountID == acc_num), None)
        if not customer:
            QtWidgets.QMessageBox.warning(self, "Error", "Customer not found.")
            return
        username = next((uname for uname, (pwd, cust) in customer_objects.items() if cust.customerAccountID == acc_num), None)
        if not username:
            QtWidgets.QMessageBox.warning(self, "Error", "Customer not found in authentication system.")
            return
        new_password, ok2 = QtWidgets.QInputDialog.getText(self, "Change Customer Password", f"Enter new password for account {acc_num}:", echo=QtWidgets.QLineEdit.Password)
        if not ok2 or not new_password:
            QtWidgets.QMessageBox.warning(self, "Error", "Password cannot be empty.")
            return
        hashed_password = hashlib.md5(new_password.encode('utf-8')).hexdigest()
        customer_objects[username] = (hashed_password, customer_objects[username][1])
        customer.customerPassword = hashed_password
        self.db.update_customer_password(acc_num, hashed_password)
        QtWidgets.QMessageBox.information(self, "Success", f"Customer password changed for account {acc_num}.")

    def back_to_home(self):
        self.close()
        if self.login_page and not self.login_page.isVisible():
            self.login_page.show()
            self.login_page.activateWindow()

class CustomerDashboard(QtWidgets.QWidget):
    def __init__(self, db, customer, login_page=None):
        super().__init__()  # FIXED: Removed parent parameter to prevent overlap
        self.db = db
        self.customer = customer
        self.login_page = login_page
        print(f"Initializing CustomerDashboard for {customer.customerUserName}, AccountID: {customer.customerAccountID}")
        self.setWindowTitle(f"Customer Dashboard - {customer.customerUserName}")
        self.setGeometry(200, 200, 600, 400)
        self.init_ui()
        print(f"CustomerDashboard initialized for {customer.customerUserName}")

    def init_ui(self):
        if not self.customer or not hasattr(self.customer, 'customerAccountID') or str(self.customer.customerAccountID) not in account_objects:
            print(f"Invalid customer data or account not found for {self.customer.customerUserName if self.customer else 'None'}: "
                  f"customerAccountID={self.customer.customerAccountID if self.customer else 'None'}, "
                  f"account_objects keys={list(account_objects.keys())}")
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid customer account data.")
            self.close()
            return

        layout = QtWidgets.QFormLayout()
        layout.addRow("Name:", QtWidgets.QLabel(self.customer.customerName or "N/A"))
        layout.addRow("National ID:", QtWidgets.QLabel(str(self.customer.nationalID) if self.customer.nationalID is not None else "N/A"))
        layout.addRow("Account ID:", QtWidgets.QLabel(str(self.customer.customerAccountID) if self.customer.customerAccountID is not None else "None"))
        balance = account_objects.get(str(self.customer.customerAccountID), None)
        layout.addRow("Balance:", QtWidgets.QLabel(f"${balance.Balance:.2f}" if balance else "0.00"))
        layout.addRow("Email:", QtWidgets.QLabel(str(self.customer.customerEmail) or "N/A"))
        account_type = account_objects.get(str(self.customer.customerAccountID), None)
        layout.addRow("Account Type:", QtWidgets.QLabel(account_type.AccountType if account_type else "N/A"))
        layout.addRow("Username:", QtWidgets.QLabel(str(self.customer.customerUserName) or "N/A"))

        self.transfer_button = QtWidgets.QPushButton("Transfer to Account")
        self.transfer_button.clicked.connect(self.transfer_money)
        layout.addRow(self.transfer_button)

        self.check_balance_btn = QtWidgets.QPushButton("Check Balance")
        self.check_balance_btn.clicked.connect(self.check_balance)
        layout.addRow(self.check_balance_btn)

        self.home_button = QtWidgets.QPushButton("Back to Home")
        self.home_button.clicked.connect(self.back_to_home)
        layout.addRow(self.home_button)

        self.setLayout(layout)
        print(f"UI initialized for CustomerDashboard of {self.customer.customerUserName}")

    def check_balance(self):
        if self.customer.customerAccountID and str(self.customer.customerAccountID) in account_objects:
            balance = account_objects[str(self.customer.customerAccountID)].Balance
            QtWidgets.QMessageBox.information(self, "Balance", f"Account balance: ${balance:.2f}")
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Account not found.")

    def transfer_money(self):
        from_acc = str(self.customer.customerAccountID)  # FIXED: Convert to string
        if not from_acc or from_acc not in account_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid source account.")
            return
        to_acc, ok1 = QtWidgets.QInputDialog.getText(self, "Transfer", "Enter target account number:")
        if not ok1 or to_acc not in account_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid or non-existent target account number.")
            return
        if to_acc == from_acc:
            QtWidgets.QMessageBox.warning(self, "Error", "Cannot transfer to the same account.")
            return
        max_transfer = account_objects[from_acc].Balance
        amount, ok2 = QtWidgets.QInputDialog.getDouble(self, "Transfer", "Enter amount to transfer:", 0, 0.01, max_transfer, 2)
        if ok2:
            if amount > max_transfer:
                QtWidgets.QMessageBox.warning(self, "Error", "Insufficient funds in your account.")
            else:
                account_objects[from_acc].Balance -= amount
                account_objects[to_acc].Balance += amount
                self.db.cursor.execute("UPDATE account SET Balance = %s WHERE AccountID = %s",
                                       (account_objects[from_acc].Balance, from_acc))
                self.db.cursor.execute("UPDATE account SET Balance = %s WHERE AccountID = %s",
                                       (account_objects[to_acc].Balance, to_acc))
                self.db.conn.commit()
                QtWidgets.QMessageBox.information(self, "Transferred", f"Transferred ${amount:.2f} to account {to_acc}.")
                self.refresh_balance()  # FIXED: Refresh balance instead of recreating UI

    def refresh_balance(self):
        """ADDED: Method to refresh balance display without recreating the entire UI"""
        balance = account_objects.get(str(self.customer.customerAccountID), None)
        if balance:
            # Find and update the balance label
            for i in range(self.layout().rowCount()):
                label = self.layout().itemAt(i, QtWidgets.QFormLayout.LabelRole)
                if label and label.widget().text() == "Balance:":
                    field = self.layout().itemAt(i, QtWidgets.QFormLayout.FieldRole)
                    if field and field.widget():
                        field.widget().setText(f"${balance.Balance:.2f}")
                    break

    def back_to_home(self):
        self.close()
        if self.login_page and not self.login_page.isVisible():
            self.login_page.show()
            self.login_page.activateWindow()

class LoginPage(QtWidgets.QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.add_customer_window = None
        self.add_employee_window = None
        self.customer_dashboard = None  # ADDED: Keep reference to dashboard
        self.employee_dashboard = None  # ADDED: Keep reference to dashboard
        self.setWindowTitle("Bank System Login")
        self.setGeometry(100, 100, 400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        self.username_label = QtWidgets.QLabel("Username:")
        self.username_input = QtWidgets.QLineEdit()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        self.password_label = QtWidgets.QLabel("Password:")
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        self.role_label = QtWidgets.QLabel("Role:")
        self.role_input = QtWidgets.QComboBox()
        self.role_input.addItems(["Customer", "Employee"])
        layout.addWidget(self.role_label)
        layout.addWidget(self.role_input)

        self.login_button = QtWidgets.QPushButton("Login")
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        self.check_balance_btn = QtWidgets.QPushButton("Check Balance")
        self.check_balance_btn.clicked.connect(self.check_balance)
        layout.addWidget(self.check_balance_btn)

        self.add_customer_button = QtWidgets.QPushButton("Add New Customer")
        self.add_customer_button.clicked.connect(self.open_add_customer)
        layout.addWidget(self.add_customer_button)

        self.add_employee_button = QtWidgets.QPushButton("Add New Employee")
        self.add_employee_button.clicked.connect(self.open_add_employee)
        self.add_employee_button.setVisible(not employee_objects)
        layout.addWidget(self.add_employee_button)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("color: red")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def check_balance(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "Check Balance", "Enter your account number:")
        if ok and text in account_objects:
            balance = account_objects[text].Balance
            QtWidgets.QMessageBox.information(self, "Balance", f"Account balance: ${balance:.2f}")
        elif ok:
            QtWidgets.QMessageBox.warning(self, "Not Found", "Account number not found.")

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        role = self.role_input.currentText()
        
        # ADDED: Clear previous status
        self.status_label.setText("")
        self.login_button.setEnabled(False)
        
        try:
            hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()
            print(f"Attempting login for username: {username}, hashed password: {hashed_password}")

            if role == "Customer":
                for customer in customer_objects.values():
                    if customer.customerUserName == username and customer.customerPassword == hashed_password:
                        customer.customerAccountID = customer.customerAccountID or None
                        print(f"Customer login successful for {customer.customerUserName}, AccountID: {customer.customerAccountID}")
                        if not customer.customerAccountID or str(customer.customerAccountID) not in account_objects:
                            self.status_label.setText("Invalid customer account data.")
                            return
                        self.status_label.setText("Customer login successful!")
                        self.show_customer_dashboard(customer)
                        return
            elif role == "Employee":
                for employee in employee_objects.values():
                    if employee.employeeUserName == username and employee.employeePassword == hashed_password:
                        self.status_label.setText("Employee login successful!")
                        is_manager = employee.position.lower() == "manager"
                        self.show_employee_dashboard(employee, is_manager)
                        return
            self.status_label.setText("Invalid credentials. Please try again.")
        except Exception as e:
            self.status_label.setText(f"Login error: {str(e)}")
            traceback.print_exc()
        finally:
            self.login_button.setEnabled(True)

    def open_add_customer(self):
        if self.add_customer_window is None:
            self.add_customer_window = AddCustomerWindow(self.db)
            self.add_customer_window.customer_added.connect(self.refresh_data)
        self.add_customer_window.show()

    def open_add_employee(self):
        if self.add_employee_window is None:
            self.add_employee_window = AddEmployeeWindow(self.db)
            self.add_employee_window.employee_added.connect(self.refresh_data)
        self.add_employee_window.show()

    def show_employee_dashboard(self, employee, is_manager):
        # FIXED: Close any existing dashboard first
        if self.customer_dashboard:
            self.customer_dashboard.close()
            self.customer_dashboard = None
        if self.employee_dashboard:
            self.employee_dashboard.close()
            
        self.employee_dashboard = EmployeeDashboard(self.db, employee, is_manager, self)
        self.employee_dashboard.show()
        self.employee_dashboard.raise_()
        self.employee_dashboard.activateWindow()
        self.hide()  # FIXED: Hide login page properly
        print(f"EmployeeDashboard shown for {employee.employeeUserName}")

    def show_customer_dashboard(self, customer):
        if not customer or not customer.customerUserName:
            self.status_label.setText("Invalid customer data.")
            return
        try:
            print(f"Showing CustomerDashboard for {customer.customerUserName}, AccountID: {customer.customerAccountID}")
            if not customer.customerAccountID or str(customer.customerAccountID) not in account_objects:
                print(f"Invalid account data for {customer.customerUserName}: "
                      f"customerAccountID={customer.customerAccountID}, account_objects keys={list(account_objects.keys())}")
                self.status_label.setText("Invalid customer account data.")
                return
            
            # FIXED: Close any existing dashboard first
            if self.employee_dashboard:
                self.employee_dashboard.close()
                self.employee_dashboard = None
            if self.customer_dashboard:
                self.customer_dashboard.close()
            
            self.customer_dashboard = CustomerDashboard(self.db, customer, self)
            if self.customer_dashboard:
                self.customer_dashboard.show()
                self.customer_dashboard.raise_()
                self.customer_dashboard.activateWindow()
                print(f"CustomerDashboard shown and activated for {customer.customerUserName}, isVisible: {self.customer_dashboard.isVisible()}")
                self.hide()  # FIXED: Hide login page properly
                
                # ADDED: Clear login form for security
                self.username_input.clear()
                self.password_input.clear()
            else:
                print("CustomerDashboard initialization failed")
                self.status_label.setText("Failed to open customer dashboard.")
        except Exception as e:
            print(f"Error showing CustomerDashboard: {str(e)}")
            traceback.print_exc()
            self.status_label.setText(f"Dashboard error: {str(e)}")

    def refresh_data(self):
        self.db.load_data()
        if self.employee_dashboard and self.employee_dashboard.isVisible():
            self.employee_dashboard.load_customers()
            self.employee_dashboard.load_transactions()
            if self.employee_dashboard.is_manager:
                self.employee_dashboard.load_activity_logs()
        elif self.customer_dashboard and self.customer_dashboard.isVisible():
            self.customer_dashboard.refresh_balance()

    def closeEvent(self, event):
        """ADDED: Proper cleanup when login window is closed"""
        if self.customer_dashboard:
            self.customer_dashboard.close()
        if self.employee_dashboard:
            self.employee_dashboard.close()
        event.accept()

def cleanup_and_exit():
    print("Application closing, performing cleanup...")
    if 'db' in globals() and db:
        db.close()
    QtWidgets.QApplication.quit()

def main():
    print("Starting main.py...")
    try:
        print("Initializing database...")
        global db
        db = Database()
        print("Database initialized, loading data...")
        db.load_data()
        print(f"Loaded customer_objects: {len(customer_objects)}, account_objects: {len(account_objects)}, "
              f"employee_objects: {len(employee_objects)}, transactions: {len(transactions)}, "
              f"activity_logs: {len(activity_logs)}")
        print("QApplication initialized")
        app = QtWidgets.QApplication(sys.argv)
        login_page = LoginPage(db)
        print("LoginPage created")
        login_page.show()
        print("LoginPage shown")
        app.aboutToQuit.connect(cleanup_and_exit)
        print("Starting Qt event loop")
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error in main: {str(e)}")
        traceback.print_exc()
    finally:
        if 'db' in globals() and db:
            print("Closing database in finally block...")
            db.close()

if __name__ == "__main__":
    main()