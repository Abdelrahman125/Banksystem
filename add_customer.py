from PyQt5 import QtWidgets, QtCore
from datetime import datetime
from models.customer import Customer
from models.account import Account
from models.debitcard import DebitCard
from globals import customer_objects, account_objects
import hashlib
import uuid
import traceback
import random

class AddCustomerWindow(QtWidgets.QWidget):
    customer_added = QtCore.pyqtSignal()

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Add New Customer")
        self.setGeometry(100, 100, 400, 600)
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        self.name_label = QtWidgets.QLabel("Name:")
        self.name_input = QtWidgets.QLineEdit()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)

        self.national_id_label = QtWidgets.QLabel("National ID (14 digits):")
        self.national_id_input = QtWidgets.QLineEdit()
        layout.addWidget(self.national_id_label)
        layout.addWidget(self.national_id_input)

        self.username_label = QtWidgets.QLabel("Username:")
        self.username_input = QtWidgets.QLineEdit()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        self.password_label = QtWidgets.QLabel("Password:")
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        self.balance_label = QtWidgets.QLabel("Initial Balance:")
        self.balance_input = QtWidgets.QLineEdit()
        layout.addWidget(self.balance_label)
        layout.addWidget(self.balance_input)

        self.email_label = QtWidgets.QLabel("Email:")
        self.email_input = QtWidgets.QLineEdit()
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)

        self.account_type_label = QtWidgets.QLabel("Account Type:")
        self.account_type_input = QtWidgets.QComboBox()
        self.account_type_input.addItems(["Saving", "Current"])
        layout.addWidget(self.account_type_label)
        layout.addWidget(self.account_type_input)

        self.expiry_date_label = QtWidgets.QLabel("Card Expiry Date (YYYY-MM-DD):")
        self.expiry_date_input = QtWidgets.QLineEdit()
        layout.addWidget(self.expiry_date_label)
        layout.addWidget(self.expiry_date_input)

        self.pin_label = QtWidgets.QLabel("Card PIN (4 digits):")
        self.pin_input = QtWidgets.QLineEdit()
        self.pin_input.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(self.pin_label)
        layout.addWidget(self.pin_input)

        self.add_button = QtWidgets.QPushButton("Add Customer")
        self.add_button.clicked.connect(self.add_new_customer)
        layout.addWidget(self.add_button)

        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        layout.addWidget(self.cancel_button)

        self.status_label = QtWidgets.QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        print("AddCustomerWindow UI setup complete")

    def add_new_customer(self):
        try:
            # Collect input data
            name = self.name_input.text()
            national_id = self.national_id_input.text()
            username = self.username_input.text()
            password = self.password_input.text()
            balance_text = self.balance_input.text()
            email = self.email_input.text()
            account_type = self.account_type_input.currentText()
            expiry_date = self.expiry_date_input.text()
            pin = self.pin_input.text()

            # Validate inputs
            if not username or not national_id or not password or not name:
                self.status_label.setText("Error: Username, National ID, Password, and Name are required!")
                return
            if len(national_id) != 14 or not national_id.isdigit():
                self.status_label.setText("Error: National ID must be 14 digits!")
                return
            if email and "@" not in email:
                self.status_label.setText("Error: Invalid email!")
                return
            try:
                balance = float(balance_text)
                if balance < 0:
                    raise ValueError("Balance must be non-negative!")
            except ValueError:
                self.status_label.setText("Error: Invalid balance (must be a non-negative number)!")
                return
            if not expiry_date or not self.is_valid_date(expiry_date):
                self.status_label.setText("Error: Invalid expiry date (use YYYY-MM-DD)!")
                return
            if not pin or len(pin) != 4 or not pin.isdigit():
                self.status_label.setText("Error: PIN must be 4 digits!")
                return

            # Generate unique IDs
            max_attempts = 10
            for _ in range(max_attempts):
                customer_id = random.randint(1, 999999999)
                if str(customer_id) not in customer_objects:
                    break
            else:
                self.status_label.setText("Error: Could not generate unique Customer ID!")
                return

            for _ in range(max_attempts):
                account_id = random.randint(1, 999999999)
                if str(account_id) not in account_objects:
                    break
            else:
                self.status_label.setText("Error: Could not generate unique Account ID!")
                return

            account_number = str(uuid.uuid4().int)[:16].zfill(16)
            card_number = ''.join(str(uuid.uuid4().int % 10) for _ in range(16))

            if customer_id > 999999999 or account_id > 999999999:
                self.status_label.setText("Error: Generated IDs too large for database!")
                return

            print(f"Generated CustomerID: {customer_id}, Type: {type(customer_id)}")
            print(f"Generated AccountID: {account_id}, Type: {type(account_id)}")

            # Hash password with MD5
            hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()

            # Debug: Print arguments to verify
            print(f"Creating Customer with args: {username}, {national_id}, {hashed_password}, {email or None}, {account_id}, {customer_id}, {name}")
            # Create objects
            customer = Customer(username, national_id, hashed_password, email or None, account_id, customer_id, name)
            account = Account(account_id, account_type, balance, account_number)
            debit_card = DebitCard(card_number, pin, expiry_date, "Active", customer_id)

            # Link account and debit card
            customer.link_account(account)
            customer.link_debit_card(debit_card)

            # Save to database within a transaction
            self.db.conn.autocommit = False
            try:
                self.db.save_account(account)
                self.db.save_customer(customer)
                self.db.save_debit_card(debit_card)
                self.db.conn.commit()
                print(f"Saving customer: {customer.customerUserName}")
                print(f"Saving account: {account.AccountID}")
                print(f"Saving debit card: {debit_card.cardNumber}")
            except Exception as e:
                self.db.conn.rollback()
                self.status_label.setText(f"Error saving to database: {str(e)}")
                print(f"Database error: {str(e)}")
                traceback.print_exc()
                return

            # Update global dictionaries
            customer_objects[str(customer_id)] = customer
            account_objects[str(account_id)] = account
            print(f"Added customer to customer_objects: {customer.customerUserName} with customerID={customer_id}, customerAccountID={customer.customerAccountID}")

            self.status_label.setText("Customer added successfully!")
            self.clear_fields()
            self.customer_added.emit()

        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            print(f"Error in add_new_customer: {str(e)}")
            traceback.print_exc()

    def is_valid_date(self, date_str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def clear_fields(self):
        self.name_input.clear()
        self.national_id_input.clear()
        self.username_input.clear()
        self.password_input.clear()
        self.balance_input.clear()
        self.email_input.clear()
        self.expiry_date_input.clear()
        self.pin_input.clear()