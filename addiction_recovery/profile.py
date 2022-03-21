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
        #used for the fact that when a day changes the age may aswell
        self.age=calculate_age(date(self.DOB))

    def return_name(self):
         return self.name

    def return_weight(self):
        return self.weight

    def return_height(self):
        return self.height

    def return_age(self):
        return self.age
