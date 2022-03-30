# base Class of your App inherits from the App class.
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, ListProperty, NumericProperty
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
import datetime

import entities
from repository import SqlRepository, Repository


class MenuScreen(Screen):
    pass


class ProfileScreen(Screen):

    def on_pre_enter(self, *args):
        """ When page loads run assign hint text with database values. """
        person = Repository.instance.get_person(1)
        if person:
            self.AssignHintText(person)

    def Submit(self):
        person_name = self.person_name.text
        weight = self.weight.text
        person_height = self.person_height.text
        birth = self.birth.text

        print(
            f"Your name is {person_name} and you have a weight of {weight}, a height of {person_height} and your birthday is {birth}")

        # Update the database with new values
        try:
            person = entities.Person(
                person_name,
                int(weight),
                int(person_height),
                int(datetime.datetime.strptime(birth, "%Y/%m/%d").timestamp())
            )
        except ValueError as e:
            # TODO: show error popup
            return
        person_id = Repository.instance.create_person(person)
        self.AssignHintText(person)

    def AssignHintText(self, person: entities.Person):
        # assign all the hint text
        self.person_name.hint_text = str(person.name)
        self.weight.hint_text = str(person.weight)
        self.person_height.hint_text = str(person.height)
        self.birth.hint_text = str(person.calculate_age())


class LoggingScreen(Screen):
    def on_pre_enter(self, *args):
        self.update_presets()

    def update_presets(self):
        for widget in self.walk():
            if isinstance(widget, SubstancePresets):
                widget.update_presets()


class SubstancePresets(GridLayout):
    """ A row of buttons that allow users to select previously used substance amount presets. """
    presets = ListProperty()

    def __init__(self, **kwargs):
        super(SubstancePresets, self).__init__(**kwargs)
        self.show_no_presets()

    def update_presets(self):
        """ Retrieves the substance presets from the data repository. """
        cols = super().cols
        rows = super().rows
        if not cols:
            cols = 3
        if not rows:
            rows = 1
        # TODO: select from correct substance_tracking_id
        self.presets = Repository.instance.get_common_substance_amounts(1, cols * rows)

    def on_presets(self, _, presets):
        """ Updates widgets to show the new presets. """
        self.clear_widgets()
        if len(presets) == 0:
            self.show_no_presets()
            return
        for preset in presets:
            # TODO: add functioning button
            self.add_widget(Button(text=f"amount: {preset.amount}, cost: £{preset.cost / 100}"))

    def show_no_presets(self):
        self.clear_widgets()
        self.add_widget(Label(text="Manually enter data to create presets."))


class GraphScreen(Screen):
    pass


class AddictionRecovery(App):

    def build(self):
        # Setup data repository
        if not SqlRepository().start():
            Repository.instance = None

        # Create the screen manager
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(ProfileScreen(name='profile'))
        sm.add_widget(LoggingScreen(name='logging'))
        sm.add_widget(GraphScreen(name='graph'))

        return sm

    def on_start(self):
        if not Repository.instance:
            # TODO: add error popup
            pass


        print(Repository.instance.get_common_substance_amounts(1, 3))

    def on_stop(self):
        if Repository.instance:
            Repository.instance.close()


if __name__ == '__main__':
    AddictionRecovery().run()
