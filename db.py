import mysql.connector
from dotenv import load_dotenv
import os
import traceback
import hashlib
from models.customer import Customer
from models.employee import Employee
from models.debitcard import DebitCard
from models.account import Account
from models.transaction import Transaction
from models.activitylog import ActivityLog
from globals import customer_objects, account_objects, employee_objects, transactions, activity_logs

load_dotenv()

class Database:
    def __init__(self):
        try:
            self.conn = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_DATABASE'),
                port=int(os.getenv('DB_PORT', 3306)),
                use_pure=True,
                connection_timeout=10
            )
            self.cursor = self.conn.cursor(dictionary=True)
        except mysql.connector.Error as e:
            print(f"Database initialization error (MySQL): {str(e)}")
            traceback.print_exc()
            raise
        except Exception as e:
            print(f"Unexpected error in Database __init__: {str(e)}")
            traceback.print_exc()
            raise

    def save_customer(self, customer):
        try:
            self.cursor.execute('''
                INSERT INTO customer (customerID, customerUserName, customerPassword, customerName, nationalID, customerEmail, customerAccountID)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (customer.customerID, customer.customerUserName, customer.customerPassword, customer.customerName, customer.nationalID, customer.customerEmail, customer.customerAccountID))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error saving customer: {str(e)}")
            raise

    def save_account(self, account):
        try:
            self.cursor.execute('''
                INSERT INTO account (AccountID, AccountType, Balance, AccountNumber)
                VALUES (%s, %s, %s, %s)
            ''', (account.AccountID, account.AccountType, account.Balance, account.AccountNumber))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error saving account: {str(e)}")
            raise

    def save_debit_card(self, debit_card):
        try:
            self.cursor.execute('''
                INSERT INTO debitcard (cardNumber, cardPin, cardExpiryDate, cardStatus, customerID)
                VALUES (%s, %s, %s, %s, %s)
            ''', (debit_card.cardNumber, debit_card.cardPin, debit_card.cardExpiryDate, debit_card.cardStatus, debit_card.customerID))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error saving debit card: {str(e)}")
            raise

    def save_employee(self, employee):
        try:
            hashed_password = hashlib.md5(employee.employeePassword.encode('utf-8')).hexdigest()
            self.cursor.execute('''
                INSERT INTO employee (employeeID, employeeUserName, employeePassword, employeeName, nationalID, position, employeeEmail, employeePhone)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (employee.employeeID, employee.employeeUserName, hashed_password, employee.employeeName, employee.nationalID, employee.position, employee.employeeEmail, employee.employeePhone))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error saving employee: {str(e)}")
            raise

    def save_transaction(self, transaction):
        try:
            self.cursor.execute('''
                INSERT INTO transaction (transactionID, transactionType, amount, transactionDate, customerID)
                VALUES (%s, %s, %s, %s, %s)
            ''', (transaction.transactionID, transaction.transactionType, transaction.amount, transaction.transactionDate, transaction.customerID))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error saving transaction: {str(e)}")
            raise

    def save_activity_log(self, activity_log):
        try:
            self.cursor.execute('''
                INSERT INTO activitylog (logID, userType, userID, actionType, amount, logTime)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (activity_log.logID, activity_log.userType, activity_log.userID, activity_log.actionType, activity_log.amount, activity_log.logTime))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error saving activity log: {str(e)}")
            raise

    def load_data(self):
        try:
            self.cursor.execute("SELECT customerID, customerUserName, nationalID, customerPassword, customerEmail, customerAccountID, customerName FROM customer")
            for row in self.cursor.fetchall():
                customer = Customer(
                    row['customerUserName'],
                    row['nationalID'],
                    row['customerPassword'],
                    row['customerEmail'],
                    row['customerAccountID'],
                    row['customerID'],
                    row['customerName']
                )
                customer_objects[str(row['customerID'])] = customer

            self.cursor.execute("SELECT AccountID, AccountType, Balance, AccountNumber FROM account")
            for row in self.cursor.fetchall():
                account = Account(row['AccountID'], row['AccountType'], row['Balance'], row['AccountNumber'])
                account_objects[str(row['AccountID'])] = account
                for customer_id, customer in customer_objects.items():
                    if customer.customerAccountID == row['AccountID']:
                        customer.link_account(account)

            self.cursor.execute("SELECT cardNumber, cardPin, cardExpiryDate, cardStatus, customerID FROM debitcard")
            for row in self.cursor.fetchall():
                debit_card = DebitCard(row['cardNumber'], row['cardPin'], row['cardExpiryDate'], row['cardStatus'], row['customerID'])
                if str(row['customerID']) in customer_objects:
                    customer_objects[str(row['customerID'])].link_debit_card(debit_card)

            self.cursor.execute("SELECT employeeID, employeeUserName, employeePassword, employeeName, nationalID, position, employeeEmail, employeePhone FROM employee")
            for row in self.cursor.fetchall():
                employee = Employee(row['employeeName'], row['nationalID'], row['employeeID'], row['position'], row['employeeEmail'], row['employeePhone'])
                employee.set_credentials(row['employeeUserName'], row['employeePassword'])
                employee_objects[str(row['employeeID'])] = employee

            self.cursor.execute("SELECT transactionID, transactionType, amount, transactionDate, customerID FROM transaction")
            for row in self.cursor.fetchall():
                transactions[row['transactionID']] = Transaction(row['transactionID'], row['transactionType'], row['amount'], row['transactionDate'], row['customerID'])

            self.cursor.execute("SELECT logID, userType, userID, actionType, amount, logTime FROM activitylog")
            for row in self.cursor.fetchall():
                activity_logs[row['logID']] = ActivityLog(row['logID'], row['userType'], row['userID'], row['actionType'], row['amount'], row['logTime'])
        except mysql.connector.Error as e:
            print(f"Error loading data: {str(e)}")
            raise
        except Exception as e:
            print(f"Unexpected error in load_data: {str(e)}")
            traceback.print_exc()
            raise

    def close(self):
        try:
            self.cursor.close()
            self.conn.close()
        except mysql.connector.Error as e:
            print(f"Error closing database: {str(e)}")
            raise

    def update_employee_username(self, employee_id, new_username):
        try:
            self.cursor.execute('''
                UPDATE employee SET employeeUserName = %s WHERE employeeID = %s
            ''', (new_username, employee_id))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error updating employee username: {str(e)}")
            self.conn.rollback()
            raise

    def update_employee_password(self, employee_id, new_password):
        try:
            self.cursor.execute('''
                UPDATE employee SET employeePassword = %s WHERE employeeID = %s
            ''', (new_password, employee_id))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error updating employee password: {str(e)}")
            self.conn.rollback()
            raise

    def update_customer_username(self, account_id, new_username):
        try:
            self.cursor.execute('''
                UPDATE customer c
                JOIN account a ON c.customerAccountID = a.AccountID
                SET c.customerUserName = %s
                WHERE a.AccountID = %s
            ''', (new_username, account_id))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error updating customer username: {str(e)}")
            self.conn.rollback()
            raise

    def update_customer_password(self, account_id, new_password):
        try:
            self.cursor.execute('''
                UPDATE customer c
                JOIN account a ON c.customerAccountID = a.AccountID
                SET c.customerPassword = %s
                WHERE a.AccountID = %s
            ''', (new_password, account_id))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error updating customer password: {str(e)}")
            self.conn.rollback()
            raise