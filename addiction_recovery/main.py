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
    image_source = StringProperty("")
    goal_text = StringProperty("")
    cost_text = StringProperty("")

    def on_pre_enter(self):
        self.update_page()

    def update_page(self):
        # Get a random image of a random substance
        substances = list(AddictionRecovery.substance_tracking_ids.keys())
        if len(substances):
            substance_name = substances[random.randrange(0, len(substances))]
            self.image_source = f"motivation/{substance_name}/{str(random.randrange(1, 5))}.jpg"

        # Show statistics
        goal = Repository.instance.get_goal(1)
        self.goal_text = ""
        if goal:
            streak = calculate_goal_streak(goal)
            if streak:
                self.goal_text = f"You've met your goal of {goal.value} for {streak}"
        last_week_cost = 0
        for tracking_id in AddictionRecovery.substance_tracking_ids.values():
            weekly_costs = calculate_weekly_costs(tracking_id)
            if len(weekly_costs):
                last_week_cost += weekly_costs[-1][1]
        self.cost_text = f"Last week, you spent £{'{:,.2f}'.format(last_week_cost)} on substances"


class ProfileScreen(Screen):
    submit_button_text = StringProperty("Submit")

    def on_pre_enter(self, *args):
        """ When page loads run assign hint text with database values. """
        person = Repository.instance.get_person(1)
        goal = Repository.instance.get_goal(1)
        if person:
            self.AssignHintText(person, goal)
        else:
            self.submit_button_text = "Submit"

    def Submit(self):
        person_name = self.person_name.text
        weight = self.weight.text
        person_height = self.person_height.text
        birth = self.birth.text
        substance = self.substance.text
        goal = self.goal.text

        # print(
        #     f"Your name is {person_name} and you have a weight of {weight}, a height of {person_height} and your "
        #     f"birthday is {birth}")

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

        if AddictionRecovery.current_person_id == -1:
            # Create new person
            AddictionRecovery.current_person_id = Repository.instance.create_person(person)
            AddictionRecovery.create_substance_tracking()
        else:
            # Update old person
            person.id = AddictionRecovery.current_person_id
            Repository.instance.update_person(person)

        # Create the goal
        tracking_id = AddictionRecovery.substance_tracking_ids.get(substance)
        goal_entity = None
        if tracking_id:
            goal_entity = entities.Goal(tracking_id, 1, int(goal), int(time.time()))
            prev_goal_entity = Repository.instance.get_goal(1)
            if prev_goal_entity:
                # Update old goal
                goal_entity.id = 1
                Repository.instance.update_goal(goal_entity)
            else:
                # Create new goal
                Repository.instance.create_goal(goal_entity)

        self.AssignHintText(person, goal_entity)

    def AssignHintText(self, person: entities.Person, goal: entities.Goal):
        self.person_name.text = str(person.name)
        self.weight.text = str(person.weight)
        self.person_height.text = str(person.height)
        self.birth.text = str(person.calculate_dob())
        self.submit_button_text = "Update"
        if goal:
            substance = AddictionRecovery.get_substance_name_from_tracking_id(goal.substance_tracking_id)
            if substance:
                self.substance.text = substance
            self.goal.text = str(goal.value)

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

        # print(
        #    f"You have logged an intake of {amount} of {substance}, specifically {specific_name}, that costed £{cost}")

        # Add the use to the data repository
        try:
            tracking_id = AddictionRecovery.substance_tracking_ids.get(substance)
            if tracking_id is None:
                raise ValueError()
            existing_preset = Repository.instance.get_substance_amount_from_data(
                float(amount),
                int(float(cost) * 100),
                specific_name,
                tracking_id
            )
            if existing_preset:
                # If the manually entered data is the same as a preset, use that instead
                use = entities.SubstanceUse(tracking_id, existing_preset.id, int(time.time()))
                Repository.instance.create_substance_use(use)
            else:
                # Else add the substance use by creating a new amount
                amount = entities.SubstanceAmount(float(amount), int(float(cost) * 100), specific_name)
                amount_id = Repository.instance.create_substance_amount(amount)
                use = entities.SubstanceUse(tracking_id, amount_id, int(time.time()))
                Repository.instance.create_substance_use(use)
        except ValueError as e:
            # TODO: show error popup
            print(f"\033[91mInvalid substance values \033[0m")
            return

        # Update the GUI to display the newly preset
        self.update_presets()

        # Reset the text boxes
        self.substance.text = "Choose Substance"
        self.amount.text = ""
        self.cost.text = ""
        self.specific_name.text = ""

    def spinner_clicked(self, value):
        # print(value)
        pass


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
            text=f"{preset.name}:\namount: {preset.amount}, cost: £{'{:,.2f}'.format(preset.cost / 100)}",
            halign="center",
            valign="bottom",
            **kwargs
        )
        self.preset = preset

    def on_press(self):
        self.lastDateUsed = datetime.datetime.now()
        tracking_id = Repository.instance.get_tracking_id_from_amount(self.preset.id)
        if tracking_id != -1:
            # Display the details of the preset on the logging page
            logging_screen = AddictionRecovery.screens.get("logging")
            substance = AddictionRecovery.get_substance_name_from_tracking_id(tracking_id)
            if substance:
                logging_screen.substance.text = substance
            logging_screen.amount.text = str(self.preset.amount)
            logging_screen.cost.text = "{:,.2f}".format(self.preset.cost / 100)
            logging_screen.specific_name.text = self.preset.name


class GraphScreen(Screen):

    def __init__(self, **kwargs):
        super(GraphScreen, self).__init__(**kwargs)
        self.tracking_id = -1

    def on_pre_enter(self):
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
        # notify("heelo")
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

    def calculate_graph(self, points):
        # Calculates points on graph according to half-life
        substance_id = Repository.instance.get_substance_tracking(AddictionRecovery.screens.get("graph").tracking_id).substance_id
        substance = Repository.instance.get_substance(substance_id)
        half_life = substance.half_life
        half_life /= (24*60) #scale

        p = points.copy()
        acc = 0 # accumulation of drug check
        for i in range(len(points)): # Each point is one 'use'
            t = points[i][0]
            amount = points[i][1] + acc

            while amount > 0.01:
                if points[i+1][0] > t: # no accumulation
                    t+=half_life
                    amount/=2
                    p.append((t, amount))
                    acc = 0
                else:
                    # Accumulate drug
                    acc = amount
                    continue

        p.sort()
        return p

    def update_graph(self):
        # Determine when the last two weeks start and end
        current_time = int(time.time())
        week_length = 7 * 24 * 60 * 60
        one_week_time = current_time - week_length
        two_week_time = one_week_time - week_length

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

        x_axis_scale = 24 * 60 * 60

        # Plot this week's and last week's substance uses
        # TODO: calculate amounts properly
        self.current_week_plot.points = \
            self.calculate_graph([((use.time - one_week_time) / x_axis_scale, amount.amount) for use, amount in one_week_uses])
        self.last_week_plot.points = \
            self.calculate_graph([((use.time - two_week_time) / x_axis_scale, amount.amount) for use, amount in two_week_uses])

        # set the graph to have the right scale
        self.xmax = week_length / x_axis_scale
        self.ymax = max([amount for _, amount in self.current_week_plot.points + self.last_week_plot.points],
                        default=1.59) * 1.25

        # Display the user's goal
        goal = Repository.instance.get_goal(1)  # Currently, only one goal is used
        if goal:
            if goal.substance_tracking_id == tracking_id:
                self.goal_plot.points = [goal.value]
                self.ymax = max(self.ymax, goal.value * 1.25)
            else:
                self.goal_plot.points = [0]
        else:
            self.goal_plot.points = [0]


def calculate_weekly_costs(tracking_id):
    # Get all substance uses
    current_time = int(time.time())
    uses = Repository.instance.get_uses_from_time_period(0, current_time, tracking_id)

    if len(uses):
        week_length = 7 * 24 * 60 * 60

        # Find from what times the graph should show data from
        oldest_use, _ = uses[0]
        start_time = int(oldest_use.time)

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
        return weekly_costs
    return []


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
        self.cost_plot.points = []
        self.cost_plot.bar_width = -1
        self.add_plot(self.cost_plot)

    def update_graph(self):
        tracking_id = AddictionRecovery.screens.get("graph").tracking_id
        weekly_costs = calculate_weekly_costs(tracking_id)
        if len(weekly_costs):
            # set the graph to have the right scale
            self.xmax = len(weekly_costs) * 7
            self.ymax = max([cost for _, cost in weekly_costs], default=15.9) * 1.25
            self.cost_plot.points = weekly_costs
            self.cost_plot.update_bar_width()
        else:
            self.cost_plot.points = []


def calculate_goal_streak(goal):
    current_time = int(time.time())
    uses = Repository.instance.get_uses_from_time_period(0, current_time, goal.substance_tracking_id)
    for i, (use, amount) in enumerate(reversed(uses)):
        if amount.amount > goal.value or i == len(uses) - 1:
            # The user failed their goal here
            streak_length = int((current_time - use.time) // (24 * 60 * 60))
            if streak_length == 1:
                return str(streak_length) + " day"
            else:
                return str(streak_length) + " days"
    return None


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
        streak = calculate_goal_streak(goal)
        if streak:
            self.total_days = streak

    def set_default_values(self):
        self.target_substance = "None"
        self.weekly_intake = "None"
        self.target_set_on = "Not set"
        self.total_days = "N/A"


class AddictionRecovery(App):
    screens = {}
    current_person_id = -1
    substance_tracking_ids = {}

    def __init__(self, database_filepath="database.db", **kwargs):
        super(AddictionRecovery, self).__init__(**kwargs)
        SqlRepository(database_filepath)
        AddictionRecovery.screens = {}
        AddictionRecovery.current_person_id = -1
        AddictionRecovery.substance_tracking_ids = {}

    def build(self):
        self.notifsent = False
        # Setup data repository
        if Repository.instance:
            if not Repository.instance.start():
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

        AddictionRecovery.screens["menu"].update_page()

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
