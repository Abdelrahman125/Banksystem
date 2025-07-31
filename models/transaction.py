class Transaction:
    def __init__(self, transactionID, transactionType, amount, transactionDate, customerID):
        self.transactionID = transactionID
        self.transactionType = transactionType
        self.amount = amount
        self.transactionDate = transactionDate
        self.customerID = customerID