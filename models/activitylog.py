class ActivityLog:
    def __init__(self, logID, userType, userID, actionType, amount, logTime):
        self.logID = logID
        self.userType = userType
        self.userID = userID
        self.actionType = actionType
        self.amount = amount
        self.logTime = logTime