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
from plyer import notification
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
        AddictionRecovery.current_person_id = Repository.instance.create_person(person)
        AddictionRecovery.create_substance_tracking()

        self.AssignHintText(person)

    def AssignHintText(self, person: entities.Person):
        # assign all the hint text
        self.person_name.hint_text = str(person.name)
        self.weight.hint_text = str(person.weight)
        self.person_height.hint_text = str(person.height)
        self.birth.hint_text = str(person.calculate_age())

    def return_to_menu(self):
        if AddictionRecovery.current_person_id == -1:
            # TODO: show error popup
            pass
        else:
            self.manager.current = "menu"


class LoggingScreen(Screen):

    def on_pre_enter(self, *args):
        self.update_presets()

    def update_presets(self):
        for widget in self.walk():
            if isinstance(widget, SubstancePresets):
                widget.update_presets()

    def Submit(self):
        substance = self.substance.text
        amount = self.amount.text
        cost = self.cost.text
        specific_name = self.specific_name.text

        print(
            f"You have logged an intake of {amount} of {substance}, specifically {specific_name}, that costed £{cost}")

        # Add the use to the data repository
        tracking_id = AddictionRecovery.substance_tracking_ids.get(substance)
        existing_preset = Repository.instance.get_substance_amount_from_data(amount, cost, specific_name, tracking_id)
        if existing_preset:
            # If the manually entered data is the same as a preset, use that instead
            use = entities.SubstanceUse(tracking_id, existing_preset.id, 1)
            Repository.instance.create_substance_use(use)
        else:
            # Else add the substance use by creating a new amount
            amount = entities.SubstanceAmount(amount, cost, specific_name)
            amount_id = Repository.instance.create_substance_amount(amount)
            use = entities.SubstanceUse(tracking_id, amount_id, 1)
            Repository.instance.create_substance_use(use)

        # Update the GUI to display the newly preset
        self.update_presets()

    def spinner_clicked(self, value):
        print(value)


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
        self.presets = Repository.instance.get_common_substance_amounts(cols * rows)

    def on_presets(self, _, presets):
        """ Updates widgets to show the new presets. """
        self.clear_widgets()
        if len(presets) == 0:
            self.show_no_presets()
            return
        for preset in presets:
            self.add_widget(PresetButton(preset))

    def show_no_presets(self):
        self.clear_widgets()
        self.add_widget(Label(text="Manually enter data to create presets."))


class PresetButton(Button):
    """ Button that is used to record a substance use in the data repository. """

    def __init__(self, preset: entities.SubstanceAmount, **kwargs):
        # super(PresetButton, self).__init__(
        #     static self.lastDateUsed = datetime.datetime.now()
        #     text=f"amount: {preset.amount}, cost: £{preset.cost / 100}",
        #     **kwargs
        # )
        super(PresetButton, self).__init__(
            text=f"{preset.name}:\namount: {preset.amount}, cost: £{preset.cost / 100}",
            halign="center",
            valign="bottom",
            **kwargs
        )
        self.preset = preset

    def on_press(self):
        self.lastDateUsed = datetime.datetime.now()
        tracking_id = Repository.instance.get_tracking_id_from_amount(self.preset.id)
        if tracking_id != -1:
            use = entities.SubstanceUse(tracking_id, self.preset.id, 1)
            Repository.instance.create_substance_use(use)


class GraphScreen(Screen):
    pass


class AddictionRecovery(App):

    current_person_id = -1
    substance_tracking_ids = {}

    def build(self):
        self.notifsent = False
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
            return

        person = Repository.instance.get_person(1)
        if not person:
            self.root.current = "profile"
        else:
            AddictionRecovery.current_person_id = person.id

    def on_stop(self):
        self.save_and_close()

    def on_pause(self):
        pass
        # #Runs every frame while the app is sleeping
        # self.saveandclose()
        # now = datetime.dateTime.now()
        # timedifference = (1440*now.day + 60*now.hour + now.minute) - (1440*PresetButton.lastdateused.day + 60*PresetButton.lastdateused.hour + PresetButton.lastdateused.minute)
        # if (timedifference > 1440):
        #     notify("Check-In", "Let us know how you're doing", "We need an app name here"', "nonexistantappicon.png", timeout=10, "Let us know how you're doing", False)
        #     PresetButton.lastdateused = datetime.dateTime.now()
        # elif (timedifference > 60):
        #     notify("Check-In", "How are you recovering from your last intake?", "We need an app name here"', "nonexistantappicon.png", timeout=10, "Let us know how you're doing", False)
        #     PresetButton.lastdateused = datetime.dateTime.now()
        # return True

    def on_resume(self):
        # If any data might need replacing (which it probably won't)
        pass

    def save_and_close(self):
        if Repository.instance:
            Repository.instance.close()

    @staticmethod
    def create_substance_tracking():
        for substance_name in ("Alcohol", "Coffee"):
            # TODO: use actual half-life
            substance = entities.Substance(substance_name, 1)
            substance_id = Repository.instance.create_substance(substance)
            substance_tracking = entities.SubstanceTracking(AddictionRecovery.current_person_id, substance_id)
            AddictionRecovery.substance_tracking_ids[substance_name] = \
                Repository.instance.create_substance_tracking(substance_tracking)



if __name__ == '__main__':
    AddictionRecovery().run()
