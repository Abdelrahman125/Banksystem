class DebitCard:
    def __init__(self, cardNumber, cardPin, cardExpiryDate, cardStatus, customerID):
        self.cardNumber = cardNumber
        self.cardPin = cardPin
        self.cardExpiryDate = cardExpiryDate
        self.cardStatus = cardStatus
        self.customerID = customerID

    def block_card(self):
        if self.cardStatus == "Active":
            self.cardStatus = "Blocked"
            return True
        return False

    def unblock_card(self):
        if self.cardStatus == "Blocked":
            self.cardStatus = "Active"
            return True
        return False

    def update_pin(self, new_pin):
        if new_pin.isdigit() and len(new_pin) == 4:
            self.cardPin = new_pin
            return True
        return False