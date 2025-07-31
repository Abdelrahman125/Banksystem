class Customer:
    def __init__(self, customerUserName, nationalID, customerPassword, customerEmail, customerAccountID, customerID,customerName):
    
        
        self.customerUserName = customerUserName
        self.nationalID = nationalID
        self.customerPassword = customerPassword
        self.customerEmail = customerEmail
        self.customerAccountID = customerAccountID
        self.customerID = customerID
        self.customerName = customerName
        self.account = None
        self.debit_card = None

    def check_password(self, password):
        return self.customerPassword == password  
    def link_account(self, account):
        self.account = account

    def link_debit_card(self, debit_card):
        self.debit_card = debit_card