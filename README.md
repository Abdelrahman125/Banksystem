# 🏦 Bank System Application

## Overview

The Bank System Application is a desktop-based banking management system built with Python and PyQt5. It provides a user-friendly graphical interface for customers and employees to perform banking operations, including account management, transactions, and administrative tasks. The application integrates with a MySQL database to store customer, employee, account, transaction, and activity log data, ensuring secure and persistent data management.

## 📦 Requirements

To run this application, make sure you have the following installed:

* **Python 3.13.1**
* **PyQt5** (Used for GUI: `from PyQt5 import QtWidgets, QtCore`)
* **mysql-connector-python** (MySQL database connectivity)
* **python-dotenv** 



---

## ✨ Features

### 🔐 General

* **User Authentication**: Secure login using username and hashed password (MD5).
* **Role-Based Access**: Separate interfaces for customers and employees, with special privileges for managers.
* **MySQL Integration**: Real-time syncing with database tables.
* **GUI with PyQt5**: Modern and responsive interface across Windows, macOS, and Linux.

### 🔑 Login Page

* **Login Functionality**: Login as customer or employee with role selection.
* **Check Balance Without Login**: Check account balance by entering the account number.
* **Add New Users**:

  * Add Customer: Via `AddCustomerWindow`.
  * Add Employee: Via `AddEmployeeWindow` (only when no employees exist).
* **Error Handling**: Friendly error messages for invalid credentials or issues.

### 📅 Customer Dashboard

* **Account Information**: Displays:

  * Name
  * National ID
  * Account ID & Balance
  * Email, Account Type, Username
* **Transfer Funds**:

  * Validate target account number, sufficient funds, and distinct source/target accounts.
* **Balance Check**: Pop-up dialog for real-time balance.
* **Back to Home**: Seamless return to login page.

### 💼 Employee Dashboard

* **Employee Information**: Displays employee ID, name, username, email, phone, and position.

#### 📃 Customer List Tab

* Table view of all customers: ID, username, name, account ID, balance.
* Real-time updates from database.

#### 💳 Transaction History Tab

* Select customer via dropdown.
* View transaction logs: ID, type, amount, date, customer ID.
* Perform:

  * Transfers between any accounts.
  * Deposits & Withdrawals.
  * View all bank accounts.

#### 📊 Manager Controls Tab (Manager Only)

* View activity logs: user type, user ID, action type, amount, time.

* Change usernames/passwords for:

  * Employees (by Employee ID)
  * Customers (by Account ID)

* **Back to Home**: Closes dashboard and returns to login page.

---

## 🗂️ Database Management

* **Persistence**: Data stored in MySQL:

  * `customer`, `employee`, `account`, `transaction`, `activitylog`
* **Dynamic Loading**:

  * Data loaded into global dictionaries (`customer_objects`, etc.)
  * Automatic refresh on new entries
* **Transaction Safety**:

  * Uses `commit()` & `rollback()` to protect against failure during fund operations

---

## 🔐 Security

* **MD5 Hashing**: Passwords are hashed before storage (consider bcrypt for production).
* **Input Validation**: Validates account numbers, usernames, amounts, etc.
* **Access Control**: Sensitive operations restricted to users with "manager" role.

---

## ⚠️ Error Handling

* Clear, user-friendly popups for:

  * Invalid input
  * Insufficient funds
  * SQL/database issues
* Buttons re-enabled automatically after each operation
* Detailed logs to console for debugging

---

## 🌐 Requirements

### Software

* **Python**: 3.13.1
* **MySQL Server**: 8.0+ recommended
* **OS**: Windows, macOS, Linux

### Python Dependencies

Install with pip:

```bash
pip install PyQt5 mysql-connector-python
pip install python-dotenv
```

* `PyQt5`: GUI framework
* `mysql-connector-python`: Connects to MySQL

### Standard Libraries

* `uuid`: Generates transaction/log IDs
* `hashlib`: Handles MD5 hashing

---

## 📊 Database Setup

```sql
CREATE DATABASE bank_system;
USE bank_system;

CREATE TABLE customer (
    customerID INT PRIMARY KEY,
    customerUserName VARCHAR(50) UNIQUE,
    customerPassword VARCHAR(255),
    customerName VARCHAR(100),
    nationalID VARCHAR(20),
    customerAccountID VARCHAR(10),
    customerEmail VARCHAR(100)
);

CREATE TABLE employee (
    employeeID VARCHAR(10) PRIMARY KEY,
    employeeName VARCHAR(100),
    employeeUserName VARCHAR(50) UNIQUE,
    employeePassword VARCHAR(255),
    position VARCHAR(50),
    employeeEmail VARCHAR(100),
    employeePhone VARCHAR(20)
);

CREATE TABLE account (
    AccountID VARCHAR(10) PRIMARY KEY,
    AccountNumber VARCHAR(20) UNIQUE,
    Balance DECIMAL(15, 2),
    AccountType VARCHAR(50)
);

CREATE TABLE transaction (
    transactionID VARCHAR(36) PRIMARY KEY,
    transactionType VARCHAR(50),
    amount DECIMAL(15, 2),
    transactionDate VARCHAR(50),
    customerID INT,
    FOREIGN KEY (customerID) REFERENCES customer(customerID)
);

CREATE TABLE activitylog (
    logID VARCHAR(36) PRIMARY KEY,
    userType VARCHAR(50),
    userID VARCHAR(50),
    actionType VARCHAR(50),
    amount DECIMAL(15, 2),
    logTime VARCHAR(50)
);
```

---

## 🌟 Usage Guide

### 🔄 Installation

```bash
git clone <repository-url>
cd bank-system
pip install PyQt5 mysql-connector-python
```

### 🏢 Run the App

```bash
python main.py
```

### 🔓 Login

* Select Role: **Customer** or **Employee**
* Enter credentials and login

### 🚀 Customer Actions

* View account details
* Transfer funds
* Check balance
* Go back to login

### 🧑‍💼 Employee Actions

* View all customers & accounts
* Manage transactions
* View logs & manage credentials (managers only)

### ➕ Add Users

* From Login Page:

  * "Add New Customer"
  * "Add New Employee" (if no employees exist)

---

## ❓ Troubleshooting

### ❌ Database Issues

* Ensure MySQL server is running
* Verify database credentials in `db.py`

### ⚠️ UI Not Working

* Check console for errors
* Ensure proper ID formats:

  * `employeeID`: e.g., `E001`
  * `customerAccountID`: matches Account table

### 🚪 Application Won't Close

* Use "Back to Home" button
* Confirm `QApplication.quitOnLastWindowClosed = True`

---

## 📁 File Structure

```
.
├── main.py               # Main GUI and logic
├── db.py                 # Database connection & queries
├── add_customer.py       # Customer registration window
├── add_employee.py       # Employee registration window
├── models/               # Data model classes
├── globals.py            # Global data dictionaries
```

---

## 🔐 Notes

* `employeeID`: Stored as string (e.g., `E001`)
* `customerID`: Integer
* Passwords are hashed using MD5 (consider stronger algorithms like bcrypt in production)

---

## 💍 License

This project is licensed under the **MIT License**.

---

Enjoy building and managing your digital bank with confidence! 🌟
