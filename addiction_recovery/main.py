# base Class of your App inherits from the App class.
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
import datetime

import entities
from repository import SqlRepository, Repository


class MenuScreen(Screen):
    pass


class ProfileScreen(Screen):
    
    #when page loads run assign hint text with database values
    
    def Submit(self):
        person_name = self.person_name.text
        weight = self.weight.text
        person_height = self.person_height.text
        birth = self.birth.text
        
        print(f"Your name is {person_name} and you have a weight of {weight}, a height of {person_height} and your birthday is {birth}")
        #update the data base with new values

        try:
            person = entities.Person(person_name, int(weight), int(person_height), datetime.datetime.strptime(birth, "%Y/%m/%d").timestamp())
        except ValueError as e:
            # TODO: show error popup
            return
        person_id = Repository.instance.create_person(person)
        
        self.AssignHintText(person_name,weight,person_height,birth)
    
    def AssignHintText(self,name,weight,height,birth):
        #assign all the hint text 
        self.person_name.hint_text=name
        self.weight.hint_text=weight
        self.person_height.hint_text=height
        self.birth.hint_text=birth
        

class LoggingScreen(Screen):
    pass


class GraphScreen(Screen):
    pass


class AddictionRecovery(App):

    def build(self):
        # Create the screen manager
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(ProfileScreen(name='profile'))
        sm.add_widget(LoggingScreen(name='logging'))
        sm.add_widget(GraphScreen(name='graph'))

        return sm

    def on_start(self):
        if not SqlRepository().start():
            # TODO: add error popup
            pass

    def on_stop(self):
        if Repository.instance:
            Repository.instance.close()


if __name__ == '__main__':
    AddictionRecovery().run()
