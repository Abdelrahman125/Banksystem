# models/account.py
class Account:
    def __init__(self, AccountID, AccountType, Balance, AccountNumber):
        self.AccountID = AccountID
        self.AccountType = AccountType
        self.Balance = Balance
        self.AccountNumber = AccountNumber

    def deposit(self, amount):
        self.Balance += amount

    def withdraw(self, amount):
        if amount <= self.Balance:
            self.Balance -= amount
            return True
        return False