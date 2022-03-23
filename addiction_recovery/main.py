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

from repository import SqlRepository, Repository


class MenuScreen(Screen):
    pass


class ProfileScreen(Screen):
    pass


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
