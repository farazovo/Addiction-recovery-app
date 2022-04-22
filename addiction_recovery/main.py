import time
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, ListProperty, NumericProperty, StringProperty
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.garden.graph import Graph, MeshLinePlot, BarPlot, HBar
from plyer import notification
import datetime
import random

import entities
from repository import SqlRepository, Repository


class MenuScreen(Screen):
    def on_pre_enter(self):
        # Get a random image of a random substance
        substances = list(AddictionRecovery.substance_tracking_ids.keys())
        if len(substances):
            substance_name = substances[random.randrange(0, len(substances))]
            filename = f"motivation/{substance_name}/{str(random.randrange(1, 5))}.png"
            wimg = Image(source=filename)


class ProfileScreen(Screen):

    def on_pre_enter(self, *args):
        """ When page loads run assign hint text with database values. """
        person = Repository.instance.get_person(1)
        goal = Repository.instance.get_goal(1)
        if person:
            self.AssignHintText(person, goal)

    def Submit(self):
        person_name = self.person_name.text
        weight = self.weight.text
        person_height = self.person_height.text
        birth = self.birth.text
        substance = self.substance.text
        goal = self.goal.text

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
            _ = int(goal)
        except ValueError as e:
            # TODO: show error popup
            print(f"\033[91mInvalid profile inputs \033[0m")
            return
        AddictionRecovery.current_person_id = Repository.instance.create_person(person)
        AddictionRecovery.create_substance_tracking()

        tracking_id = AddictionRecovery.substance_tracking_ids.get(substance)
        goal_entity = None
        if tracking_id:
            goal_entity = entities.Goal(tracking_id, 1, int(goal), int(time.time()))
            Repository.instance.create_goal(goal_entity)

        self.AssignHintText(person, goal_entity)

    def AssignHintText(self, person: entities.Person, goal: entities.Goal):
        # assign all the hint text
        self.person_name.hint_text = str(person.name)
        self.weight.hint_text = str(person.weight)
        self.person_height.hint_text = str(person.height)
        self.birth.hint_text = str(person.calculate_dob())
        if goal:
            substance = AddictionRecovery.get_substance_name_from_tracking_id(goal.substance_tracking_id)
            print(goal.substance_tracking_id)
            if substance:
                self.substance.text = substance
            self.goal.hint_text = str(goal.value)


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
            use = entities.SubstanceUse(tracking_id, existing_preset.id, int(time.time()))
            Repository.instance.create_substance_use(use)
        else:
            # Else add the substance use by creating a new amount
            amount = entities.SubstanceAmount(amount, cost, specific_name)
            amount_id = Repository.instance.create_substance_amount(amount)
            use = entities.SubstanceUse(tracking_id, amount_id, int(time.time()))
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
    lastDateUsed = datetime.datetime.now()

    def __init__(self, preset: entities.SubstanceAmount, **kwargs):
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
            use = entities.SubstanceUse(tracking_id, self.preset.id, int(time.time()))
            Repository.instance.create_substance_use(use)


class GraphScreen(Screen):

    def __init__(self, **kw):
        super(GraphScreen, self).__init__(**kw)
        self.tracking_id = -1

    def on_pre_enter(self, *args):
        self.tracking_id = list(AddictionRecovery.substance_tracking_ids.values())[0]
        self.update_graphs()

    def update_graphs(self):
        for widget in self.walk():
            if isinstance(widget, SubstanceGraph):
                widget.update_graph()
            elif isinstance(widget, CostGraph):
                widget.update_graph()
            elif isinstance(widget, GraphSubstanceButtons):
                widget.update_substances()


class GraphSubstanceButtons(GridLayout):
    """ A row of buttons that allow users to select which substance they want to view the graphs for. """
    substances = ListProperty()

    def __init__(self, **kwargs):
        super(GraphSubstanceButtons, self).__init__(**kwargs)
        self.clear_widgets()

    def update_substances(self):
        """ Retrieves the substance presets from the data repository. """
        self.substances = Repository.instance.get_substances_and_tracking(AddictionRecovery.current_person_id)
        self.rows = 1
        self.cols = len(self.substances)

    def on_substances(self, _, substances):
        """ Updates widgets to show the substances. """
        self.clear_widgets()
        if len(substances) != 0:
            for substance in substances:
                self.add_widget(SubstanceGraphButton(*substance))


class SubstanceGraphButton(Button):
    """ Button that is used to switch between viewing the graphs for different substances. """

    def __init__(self, substance: entities.Substance, tracking: entities.SubstanceTracking, **kwargs):
        super(SubstanceGraphButton, self).__init__(
            text=substance.name,
            halign="center",
            valign="bottom",
            **kwargs
        )
        self.tracking_id = tracking.id

    def on_press(self):
        AddictionRecovery.screens.get("graph").tracking_id = self.tracking_id
        AddictionRecovery.screens.get("graph").update_graphs()


class SubstanceGraph(Graph):

    def __init__(self, **kwargs):
        super(SubstanceGraph, self).__init__(
            xlabel='Time (days)', ylabel='Amount',
            x_ticks_minor=24, x_ticks_major=1,
            y_ticks_major=5,
            y_grid_label=True, x_grid_label=True,
            padding=5,
            x_grid=True, y_grid=True,
            xmin=0, xmax=1,
            ymin=0, ymax=1
        )

        self.current_week_plot = MeshLinePlot(color=[0, 1, 0, 1])
        self.current_week_plot.points = [(0, 0)]
        self.add_plot(self.current_week_plot)

        self.last_week_plot = MeshLinePlot(color=[0, 1, 1, 1])
        self.last_week_plot.points = [(0, 0)]
        self.add_plot(self.last_week_plot)

        self.goal_plot = HBar(color=[1, 0, 0, 1])
        self.goal_plot.points = [0]
        self.add_plot(self.goal_plot)

    def update_graph(self):
        # Determine when the last two weeks start and end
        current_time = int(time.time())
        week_length = 7 * 24 * 60 * 60
        one_week_time = current_time - week_length
        two_week_time = one_week_time - week_length

        # coffee = AddictionRecovery.substance_tracking_ids.get("Coffee")
        # print(AddictionRecovery.substance_tracking_ids)
        # small = Repository.instance.create_substance_amount(
        #     entities.SubstanceAmount(5, 50, "small")
        # )
        # medium = Repository.instance.create_substance_amount(
        #     entities.SubstanceAmount(10, 100, "medium")
        # )
        # large = Repository.instance.create_substance_amount(
        #     entities.SubstanceAmount(20, 200, "large")
        # )
        #
        # for i in (0.5, 0.1, 0.67, 0.98, 0.02):
        #     Repository.instance.create_substance_use(
        #         entities.SubstanceUse(coffee, small, int(one_week_time + i * week_length))
        #     )
        # for i in (0.4, 0.12, 0.82):
        #     Repository.instance.create_substance_use(
        #         entities.SubstanceUse(coffee, medium, int(one_week_time + i * week_length))
        #     )
        # for i in (0.28, 0.34, 0.77, 0.89):
        #     Repository.instance.create_substance_use(
        #         entities.SubstanceUse(coffee, large, int(one_week_time + i * week_length))
        #     )
        #
        # for i in (0.01, 0.12, 0.24, 0.6345, 0.9345, 0.21):
        #     Repository.instance.create_substance_use(
        #         entities.SubstanceUse(coffee, small, int(two_week_time + i * week_length))
        #     )
        # for i in (0.2345, 0.11234, 0.65):
        #     Repository.instance.create_substance_use(
        #         entities.SubstanceUse(coffee, medium, int(two_week_time + i * week_length))
        #     )
        # for i in (0.586, 0.98, 0.23, 0.56):
        #     Repository.instance.create_substance_use(
        #         entities.SubstanceUse(coffee, large, int(two_week_time + i * week_length))
        #     )

        # Find all the substance uses in those two weeks
        tracking_id = AddictionRecovery.screens.get("graph").tracking_id
        one_week_uses = Repository.instance.get_uses_from_time_period(
            one_week_time,
            current_time,
            tracking_id
        )
        two_week_uses = Repository.instance.get_uses_from_time_period(
            two_week_time,
            one_week_time,
            tracking_id
        )

        # set the graph to have the right scale
        x_axis_scale = 24 * 60 * 60
        self.xmax = week_length / x_axis_scale
        self.ymax = max([amount.amount for _, amount in one_week_uses + two_week_uses], default=1.59) * 1.25

        # Plot this week's and last week's substance uses
        # TODO: calculate amounts properly
        self.current_week_plot.points = \
            [((use.time - one_week_time) / x_axis_scale, amount.amount) for use, amount in one_week_uses]
        self.last_week_plot.points = \
            [((use.time - two_week_time) / x_axis_scale, amount.amount) for use, amount in two_week_uses]

        # Display the user's goal
        goal = Repository.instance.get_goal(1)      # Currently, only one goal is used
        if goal:
            if goal.substance_tracking_id == tracking_id:
                self.goal_plot.points = [goal.value]
            else:
                self.goal_plot.points = [0]
        else:
            self.goal_plot.points = [0]


class CostGraph(Graph):

    def __init__(self, **kwargs):
        super(CostGraph, self).__init__(
            xlabel='Time (days)', ylabel='Money Spent (£)',
            x_ticks_minor=7, x_ticks_major=7,
            y_ticks_major=5,
            y_grid_label=True, x_grid_label=True,
            padding=5,
            x_grid=True, y_grid=True,
            xmin=0, xmax=1,
            ymin=0, ymax=1
        )
        self.cost_plot = BarPlot(color=[1, 0, 0, 1])
        self.cost_plot.points = [(0, 0)]
        self.cost_plot.bar_width = -1
        self.add_plot(self.cost_plot)

    def update_graph(self):

        # Get all substance uses
        tracking_id = AddictionRecovery.screens.get("graph").tracking_id
        current_time = int(time.time())
        uses = Repository.instance.get_uses_from_time_period(0, current_time, tracking_id)

        if len(uses):
            week_length = 7 * 24 * 60 * 60

            # Find from what times the graph should show data from
            oldest_use, _ = uses[0]
            start_time = int(oldest_use.time - week_length / 7)

            # Calculate the total cost for each week
            weekly_costs = [((t + week_length / 2 - start_time) / (week_length / 7), 0)
                            for t in range(start_time, current_time, week_length)]
            week = 0
            for use, amount in uses:
                while week < len(weekly_costs):
                    if use.time < start_time + (week + 1) * week_length:
                        t, c = weekly_costs[week]
                        weekly_costs[week] = (t, c + amount.cost / 100)
                        break
                    week += 1

            # set the graph to have the right scale
            self.xmax = len(weekly_costs) * 7
            self.ymax = max([cost for _, cost in weekly_costs], default=15.9) * 1.25
            self.cost_plot.points = weekly_costs
            self.cost_plot.update_bar_width()
        else:
            self.cost_plot.points = []


class GoalsScreen(Screen):
    target_substance = StringProperty("None")
    weekly_intake = StringProperty("None")
    target_set_on = StringProperty("Not set")
    total_days = StringProperty("N/A")

    def on_pre_enter(self, *args):
        goal = Repository.instance.get_goal(1)  # Currently, only one goal is used
        self.set_default_values()
        if not goal:
            return

        # Display the target substance
        substance = AddictionRecovery.get_substance_name_from_tracking_id(goal.substance_tracking_id)
        if substance:
            self.target_substance = substance

        # Display the weekly intake
        self.weekly_intake = str(goal.value)

        # Display when the target was set
        self.target_set_on = \
            datetime.datetime.utcfromtimestamp(goal.time_set).strftime("%d/%m/%Y")

        # Display for how long they've met their target
        current_time = int(time.time())
        uses = Repository.instance.get_uses_from_time_period(0, current_time, goal.substance_tracking_id)
        for i, (use, amount) in enumerate(reversed(uses)):
            if amount.amount > goal.value or i == len(uses) - 1:
                # The user failed their goal here
                streak_length = int((current_time - use.time) // (24 * 60 * 60))
                if streak_length == 1:
                    self.total_days = str(streak_length) + " day"
                else:
                    self.total_days = str(streak_length) + " days"
                break

    def set_default_values(self):
        self.target_substance = "None"
        self.weekly_intake = "None"
        self.target_set_on = "Not set"
        self.total_days = "N/A"


class AddictionRecovery(App):
    screens = {}
    current_person_id = -1
    substance_tracking_ids = {}

    def build(self):
        self.notifsent = False
        # Setup data repository
        if not SqlRepository().start():
            Repository.instance = None

        # Create the screen manager
        sm = ScreenManager()
        AddictionRecovery.screens["menu"] = MenuScreen(name='menu')
        sm.add_widget(AddictionRecovery.screens["menu"])
        AddictionRecovery.screens["profile"] = ProfileScreen(name='profile')
        sm.add_widget(AddictionRecovery.screens["profile"])
        AddictionRecovery.screens["logging"] = LoggingScreen(name='logging')
        sm.add_widget(AddictionRecovery.screens["logging"])
        AddictionRecovery.screens["graph"] = GraphScreen(name='graph')
        sm.add_widget(AddictionRecovery.screens["graph"])
        AddictionRecovery.screens["goals"] = GoalsScreen(name='goals')
        sm.add_widget(AddictionRecovery.screens["goals"])

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
            substances = Repository.instance.get_substances_and_tracking(person.id)
            for substance, tracking in substances:
                AddictionRecovery.substance_tracking_ids[substance.name] = tracking.id

    def on_stop(self):
        self.save_and_close()

    def on_pause(self):
        # Runs every frame while the app is sleeping
        self.save_and_close()
        now = datetime.datetime.now()
        timedifference = (1440 * now.day + 60 * now.hour + now.minute) - (
                    1440 * PresetButton.lastdateused.day + 60 * PresetButton.lastdateused.hour + PresetButton.lastdateused.minute)
        if (timedifference > 1440):
            notify("Let us know how you're doing")
            PresetButton.lastdateused = datetime.datetime.now()
        elif (timedifference > 60):
            notify("How are you recovering from your last intake")
            PresetButton.lastdateused = datetime.datetime.now()
        return True

    def on_resume(self):
        # If any data might need replacing (which it probably won't)
        pass

    def save_and_close(self):
        if Repository.instance:
            Repository.instance.close()

    @staticmethod
    def create_substance_tracking():
        for substance_name in ("Alcohol", "Coffee", "Nicotine"):
            # TODO: use actual half-life
            substance = entities.Substance(substance_name, 1)
            substance_id = Repository.instance.create_substance(substance)
            substance_tracking = entities.SubstanceTracking(AddictionRecovery.current_person_id, substance_id)
            AddictionRecovery.substance_tracking_ids[substance_name] = \
                Repository.instance.create_substance_tracking(substance_tracking)

    @staticmethod
    def get_substance_name_from_tracking_id(tracking_id: int) -> str:
        for substance, substance_tracking_id in AddictionRecovery.substance_tracking_ids.items():
            if substance_tracking_id == tracking_id:
                return substance


def notify(message):
    AndroidString = notification.autoclass('java.lang.String')
    PythonActivity = notification.autoclass('org.kivy.android.PythonActivity')
    NotificationBuilder = notification.autoclass('android.app.Notification$Builder')
    Drawable = notification.autoclass('org.test.notify.R$drawable')
    Context = notification.autoclass('android.content.Context')
    notification_service = PythonActivity.mActivity.getSystemService(Context.NOTIFICATION_SERVICE)
    icon = Drawable.icon
    notification_builder = NotificationBuilder(PythonActivity.mActivity)
    notification_builder.setContentTitle(AndroidString('Title'.encode('utf-8')))
    notification_builder.setContentText(AndroidString('Message'.encode('utf-8')))
    notification_builder.setSmallIcon(icon)
    notification_builder.setAutoCancel(True)
    notification_service = PythonActivity.mActivity.getSystemService(PythonActivity.NOTIFICATION_SERVICE)
    notification_service.notify(0, notification_builder.build())


if __name__ == '__main__':
    AddictionRecovery().run()
