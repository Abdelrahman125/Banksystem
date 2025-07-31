class Employee:
    def __init__(self, employeeName, nationalID, employeeID, position, employeeEmail, employeePhone):
        self.employeeName = employeeName
        self.nationalID = nationalID
        self.employeeID = employeeID
        self.position = position
        self.employeeEmail = employeeEmail
        self.employeePhone = employeePhone
        self.employeeUserName = None
        self.employeePassword = None

    def set_credentials(self, employeeUserName, employeePassword):
        self.employeeUserName = employeeUserName
        self.employeePassword = employeePassword

    def check_password(self, password):
        return self.employeePassword == password  