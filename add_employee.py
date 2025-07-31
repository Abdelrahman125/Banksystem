from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
import uuid
from models.employee import Employee
from globals import employee_objects
from db import Database
import hashlib
import traceback

class AddEmployeeWindow(QtWidgets.QWidget):
    employee_added = pyqtSignal()

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Add New Employee")
        self.setGeometry(100, 100, 400, 500)
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

        self.position_label = QtWidgets.QLabel("Position:")
        self.position_input = QtWidgets.QLineEdit()
        layout.addWidget(self.position_label)
        layout.addWidget(self.position_input)

        self.email_label = QtWidgets.QLabel("Email:")
        self.email_input = QtWidgets.QLineEdit()
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)

        self.phone_label = QtWidgets.QLabel("Phone (e.g., 01234567890):")
        self.phone_input = QtWidgets.QLineEdit()
        layout.addWidget(self.phone_label)
        layout.addWidget(self.phone_input)

        self.add_button = QtWidgets.QPushButton("Add Employee")
        self.add_button.clicked.connect(self.add_new_employee)
        layout.addWidget(self.add_button)

        self.status_label = QtWidgets.QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def add_new_employee(self):
        try:
            # Collect input data
            name = self.name_input.text().strip()
            national_id = self.national_id_input.text().strip()
            username = self.username_input.text().strip()
            password = self.password_input.text().strip()
            position = self.position_input.text().strip()
            email = self.email_input.text().strip()
            phone = self.phone_input.text().strip()

            # Validate inputs
            if not all([name, national_id, username, password, position]):
                self.status_label.setText("Please fill all required fields!")
                return
            if len(national_id) != 14 or not national_id.isdigit():
                self.status_label.setText("National ID must be exactly 14 digits!")
                return
            if any(emp.employeeUserName == username for emp in employee_objects.values()):
                self.status_label.setText("Username already exists!")
                return
            if not email or "@" not in email or "." not in email.split("@")[1]:
                self.status_label.setText("Invalid email format!")
                return
            if not phone or not phone.isdigit() or len(phone) < 10 or len(phone) > 11:
                self.status_label.setText("Phone must be 10-11 digits!")
                return

            # Generate unique ID
            employee_id = str(uuid.uuid4())
            print(f"Generated EmployeeID: {employee_id}, Length: {len(employee_id)}")

            # Hash password with MD5
            hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()
            print(f"Hashed password for {username}: {hashed_password}")

            # Create employee object
            employee = Employee(name, national_id, employee_id, position, email, phone)
            employee.set_credentials(username, hashed_password)

            # Save to database
            self.db.save_employee(employee)
            print(f"Saved employee {username} to database")

            # Update global dictionary
            employee_objects[employee_id] = employee
            print(f"Added employee {username} to employee_objects")

            self.status_label.setText("Employee added successfully!")
            self.clear_fields()
            self.employee_added.emit()
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            print(f"Error in add_new_employee: {str(e)}")
            traceback.print_exc()

    def clear_fields(self):
        self.name_input.clear()
        self.national_id_input.clear()
        self.username_input.clear()
        self.password_input.clear()
        self.position_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
