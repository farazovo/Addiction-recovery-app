from datetime import date
class profile:
    def __init__(self, name, weight, height, DOB):
        self.name=name
        self.weight=weight
        self.height=height
        #DOB in (year, month, day) format
        self.DOB=DOB
        self.age=calculate_age(date(DOB))


    def update_name(self, newname):
        self.name=newname

    def update_weight(self, newweight):
        self.weight=newweight

    def update_height(self, newheight):
        self.height=newheight

    def update_DOB(self, newDOB):
        self.DOB=newDOB
        self.age=calculate_age(date(newDOB))

    def calculate_age(self, DOB):
        yeardays = 365.2425   
        age = int((date.today() - DOB).days / yeardays)
        return age

    def recacl_age(self):
        self.age=calculate_age(date(self.DOB))

