import unittest
import io
import sys

from kivy.clock import Clock
from kivy.tests.common import GraphicUnitTest

from repository import *
from entities import *
from main import *


class TestSqlRepository(unittest.TestCase):

    def test_repository_start_and_close(self):
        """
        Tests whether the repository can be started, closed and whether this sets the Repository
        singleton's instance.
        """

        # Test constructor
        self.assertIsNone(Repository.instance)
        repository = SqlRepository(filepath=":memory:")
        self.assertIsNone(repository.cursor)
        self.assertIsNone(repository.connection)
        self.assertEqual(Repository.instance, repository)

        # Test start
        self.assertTrue(repository.start())
        self.assertIsNotNone(repository.cursor)
        self.assertIsNotNone(repository.connection)

        # Test close
        repository.close()
        self.assertIsNone(repository.cursor)
        self.assertIsNone(repository.connection)
        self.assertIsNone(Repository.instance)

    def test_person(self):
        """ Tests adding and retrieving a person to and from the database. """
        with SqlRepository(":memory:") as r:
            person = Person("name", 1, 10, 100)
            self.assertIsNone(person.id)
            person.id = r.create_person(person)
            self.assertIsNotNone(person.id)
            retrieved_person = r.get_person(person.id)
            self.assertEqual(person, retrieved_person)

    def test_substance_tracking(self):
        """ Tests adding and retrieving a substance tracking instance to and from the database. """
        with SqlRepository(":memory:") as r:
            substance_tracking = SubstanceTracking(1, 1)
            self.assertIsNone(substance_tracking.id)
            substance_tracking.id = r.create_substance_tracking(substance_tracking)
            self.assertIsNotNone(substance_tracking.id)
            retrieved_substance_tracking = r.get_substance_tracking(substance_tracking.id)
            self.assertEqual(substance_tracking, retrieved_substance_tracking)

    def test_substance(self):
        """ Tests adding and retrieving a substance to and from the database. """
        with SqlRepository(":memory:") as r:
            substance = Substance("Coffee", 1)
            self.assertIsNone(substance.id)
            substance.id = r.create_substance(substance)
            self.assertIsNotNone(substance.id)
            retrieved_substance = r.get_substance(substance.id)
            self.assertEqual(substance, retrieved_substance)

    def test_substance_use(self):
        """ Tests adding and retrieving a substance use to and from the database. """
        with SqlRepository(":memory:") as r:
            substance_use = SubstanceUse(1, 1, 0)
            self.assertIsNone(substance_use.id)
            substance_use.id = r.create_substance_use(substance_use)
            self.assertIsNotNone(substance_use.id)
            retrieved_substance_use = r.get_substance_use(substance_use.id)
            self.assertEqual(substance_use, retrieved_substance_use)

    def test_substance_amount(self):
        """ Tests adding and retrieving a substance amount to and from the database. """
        with SqlRepository(":memory:") as r:
            substance_amount = SubstanceAmount(1, 100, "Small coffee")
            self.assertIsNone(substance_amount.id)
            substance_amount.id = r.create_substance_amount(substance_amount)
            self.assertIsNotNone(substance_amount.id)
            retrieved_substance_amount = r.get_substance_amount(substance_amount.id)
            self.assertEqual(substance_amount, retrieved_substance_amount)

    def test_goal(self):
        """ Tests adding and retrieving a goal to and from the database. """
        with SqlRepository(":memory:") as r:
            goal = Goal(1, 1, 10, 0)
            self.assertIsNone(goal.id)
            goal.id = r.create_goal(goal)
            self.assertIsNotNone(goal.id)
            retrieved_goal = r.get_goal(goal.id)
            self.assertEqual(goal, retrieved_goal)

    def test_goal_type(self):
        """ Tests adding and retrieving a goal type to and from the database. """
        with SqlRepository(":memory:") as r:
            goal_type = GoalType("Use limit", "Stay under this amount at all times.")
            self.assertIsNone(goal_type.id)
            goal_type.id = r.create_goal_type(goal_type)
            self.assertIsNotNone(goal_type.id)
            retrieved_goal_type = r.get_goal_type(goal_type.id)
            self.assertEqual(goal_type, retrieved_goal_type)

    def test_update_person(self):
        """
        Tests updating a person's details in the database. This also makes sure that other
        records are unaffected.
        """
        with SqlRepository(":memory:") as r:
            person = Person("name", 1, 10, 100)
            person2 = Person("name 2", 2, 20, 200)
            person.id = r.create_person(person)
            person2.id = r.create_person(person2)
            updated_person = Person("new name", 3, 30, 300, person.id)
            r.update_person(updated_person)
            retrieved_person = r.get_person(person.id)
            self.assertEqual(updated_person, retrieved_person)
            self.assertNotEqual(person, retrieved_person)
            retrieved_person2 = r.get_person(person2.id)
            self.assertEqual(person2, retrieved_person2)

    def test_update_goal(self):
        """
        Tests updating a goal's details in the database. This also makes sure that other
        records are unaffected.
        """
        with SqlRepository(":memory:") as r:
            goal = Goal(1, 1, 10, 0)
            goal2 = Goal(2, 1, 20, 20)
            goal.id = r.create_goal(goal)
            goal2.id = r.create_goal(goal2)
            updated_goal = Goal(1, 1, 15, 10, goal.id)
            r.update_goal(updated_goal)
            retrieved_goal = r.get_goal(goal.id)
            self.assertEqual(updated_goal, retrieved_goal)
            self.assertNotEqual(goal, retrieved_goal)
            retrieved_goal2 = r.get_goal(goal2.id)
            self.assertEqual(goal2, retrieved_goal2)

    def test_get_substances_and_tracking(self):
        """
        Tests that the database can store and retrieve substances tracking instances that are
        linked to their substance through the foreign key.
        """
        with SqlRepository(":memory:") as r:
            actual = []
            person_id = 1
            for substance_name in ("Alcohol", "Coffee", "Nicotine"):
                substance = Substance(substance_name, 1)
                substance.id = r.create_substance(substance)
                substance_tracking = SubstanceTracking(person_id, substance.id)
                substance_tracking.id = r.create_substance_tracking(substance_tracking)
                actual.append((substance, substance_tracking))
            self.assertEqual(actual, r.get_substances_and_tracking(person_id))

    def test_get_common_substance_amounts(self):
        """
        Tests that the SQL query that retrieves substance amount in the order of how many times
        they have been used (needed to get presets).
        """
        with SqlRepository(":memory:") as r:
            substance_amounts = [
                SubstanceAmount(1, 100, "small (used least)"),
                SubstanceAmount(2, 200, "medium (used in the middle)"),
                SubstanceAmount(3, 300, "large (used most)")
            ]

            # Create amounts and uses
            for amount in substance_amounts:
                amount.id = r.create_substance_amount(amount)
                for i in range(int(amount.amount) * 3):  # Use each one by 3x its amount
                    use = SubstanceUse(1, amount.id, i)
                    r.create_substance_use(use)

            self.assertEqual(substance_amounts[::-1], r.get_common_substance_amounts(3))
            self.assertEqual(substance_amounts[::-1][:-1], r.get_common_substance_amounts(2))
            self.assertEqual([substance_amounts[-1]], r.get_common_substance_amounts(1))
            self.assertEqual([], r.get_common_substance_amounts(0))

    def test_get_substance_amount_from_data(self):
        """ Test retrieving a substance amount using what data it contains (used to avoid duplicate presets). """
        with SqlRepository(":memory:") as r:
            tracking_id = 1
            amount = 1
            cost = 1
            substance_amount = SubstanceAmount(amount, cost, "name")
            substance_amount.id = r.create_substance_amount(substance_amount)
            use = SubstanceUse(tracking_id, substance_amount.id, 0)
            use.id = r.create_substance_use(use)
            self.assertEqual(
                substance_amount,
                r.get_substance_amount_from_data(amount, cost, "name", tracking_id)
            )

    def test_get_tracking_id_from_amount(self):
        """ Test retrieving the tracking id from a substance amount. """
        with SqlRepository(":memory:") as r:
            tracking_id = 1
            substance_amount = SubstanceAmount(1, 1, "name")
            substance_amount.id = r.create_substance_amount(substance_amount)
            use = SubstanceUse(tracking_id, substance_amount.id, 0)
            use.id = r.create_substance_use(use)
            self.assertEqual(tracking_id, r.get_tracking_id_from_amount(substance_amount.id))

    def test_get_uses_from_time_period(self):
        """ Tests retrieving substance uses from a given time period. """
        with SqlRepository(":memory:") as r:
            amount = SubstanceAmount(1.0, 1, "name")
            amount.id = r.create_substance_amount(amount)

            # Uses with time from 0 to 49 inclusive
            tracking_id = 1
            uses = [SubstanceUse(tracking_id, 1, i) for i in range(50)]
            for use in uses:
                use.id = r.create_substance_use(use)

            # get_uses_from_time_period is not inclusive
            uses_and_amounts = [(use, amount) for use in uses]
            self.assertEqual(uses_and_amounts, r.get_uses_from_time_period(-1, 50, tracking_id))
            self.assertEqual(uses_and_amounts[1:], r.get_uses_from_time_period(0, 50, tracking_id))
            self.assertEqual(uses_and_amounts[1:-1], r.get_uses_from_time_period(0, 49, tracking_id))
            self.assertEqual(uses_and_amounts[11:-10], r.get_uses_from_time_period(10, 40, tracking_id))
            self.assertEqual([uses_and_amounts[-1]], r.get_uses_from_time_period(48, 50, tracking_id))
            self.assertEqual([], r.get_uses_from_time_period(49, 100, tracking_id))


class TestProfileScreen(GraphicUnitTest):

    def test_submit(self):
        app = AddictionRecovery(database_filepath=":memory:")
        Repository.instance.reset()

        def test(*args):
            profile = app.screens.get("profile")
            self.assertEqual(profile.submit_button_text, "Submit")

            # Load fake information
            profile.person_name.text = "name"
            profile.weight.text = "123"
            profile.person_height.text = "123"
            profile.birth.text = "2000/01/01"
            profile.substance.text = "Coffee"
            profile.goal.text = "10"

            # Check that there are no errors
            output = io.StringIO()
            sys.stdout = output
            profile.Submit()
            sys.stdout = sys.__stdout__
            self.assertEqual("", output.getvalue())
            self.assertEqual(profile.submit_button_text, "Update")

            self.assertIsNotNone(Repository.instance.get_person(AddictionRecovery.current_person_id))

            app.stop()

        Clock.schedule_once(test, 0)
        app.run()

    def test_stays_on_profile(self):
        app = AddictionRecovery(database_filepath=":memory:")
        Repository.instance.reset()

        def test(*args):
            profile = app.screens.get("profile")
            self.assertEqual(app.root.current, "profile")
            profile.return_to_menu()
            self.assertEqual(app.root.current, "profile")

            # Load fake information
            profile.person_name.text = "name"
            profile.weight.text = "123"
            profile.person_height.text = "123"
            profile.birth.text = "2000/01/01"
            profile.substance.text = "Coffee"
            profile.goal.text = "10"

            profile.Submit()

            profile.return_to_menu()
            self.assertEqual(app.root.current, "menu")

            app.stop()

        Clock.schedule_once(test, 0)
        app.run()

    def test_invalid_weight(self):
        app = AddictionRecovery(database_filepath=":memory:")
        Repository.instance.reset()

        def test(*args):
            profile = app.screens.get("profile")
            self.assertEqual(profile.submit_button_text, "Submit")

            # Load fake information
            profile.person_name.text = "name"
            profile.weight.text = "text"
            profile.person_height.text = "123"
            profile.birth.text = "2000/01/01"
            profile.substance.text = "Coffee"
            profile.goal.text = "10"

            # Check that there are errors
            output = io.StringIO()
            sys.stdout = output
            profile.Submit()
            sys.stdout = sys.__stdout__
            self.assertEqual(f"\033[91mInvalid profile inputs \033[0m\n", output.getvalue())
            self.assertEqual(-1, AddictionRecovery.current_person_id)

            self.assertTrue(profile.person_name.text == "name")
            self.assertTrue(profile.weight.text == "text")
            self.assertTrue(profile.person_height.text == "123")
            self.assertTrue(profile.birth.text == "2000/01/01")
            self.assertTrue(profile.substance.text == "Coffee")
            self.assertTrue(profile.goal.text == "10")

            app.stop()

        Clock.schedule_once(test, 0)
        app.run()

    def test_invalid_height(self):
        app = AddictionRecovery(database_filepath=":memory:")
        Repository.instance.reset()

        def test(*args):
            profile = app.screens.get("profile")
            self.assertEqual(profile.submit_button_text, "Submit")

            # Load fake information
            profile.person_name.text = "name"
            profile.weight.text = "123"
            profile.person_height.text = "text"
            profile.birth.text = "2000/01/01"
            profile.substance.text = "Coffee"
            profile.goal.text = "10"

            # Check that there are errors
            output = io.StringIO()
            sys.stdout = output
            profile.Submit()
            sys.stdout = sys.__stdout__
            self.assertEqual(f"\033[91mInvalid profile inputs \033[0m\n", output.getvalue())

            app.stop()

        Clock.schedule_once(test, 0)
        app.run()

    def test_invalid_birth(self):
        app = AddictionRecovery(database_filepath=":memory:")
        Repository.instance.reset()

        def test(*args):
            profile = app.screens.get("profile")
            self.assertEqual(profile.submit_button_text, "Submit")

            # Load fake information
            profile.person_name.text = "name"
            profile.weight.text = "123"
            profile.person_height.text = "123"
            profile.birth.text = "00/01/01"  # Must be exactly yyyy/mm/dd
            profile.substance.text = "Coffee"
            profile.goal.text = "10"

            # Check that there are errors
            output = io.StringIO()
            sys.stdout = output
            profile.Submit()
            sys.stdout = sys.__stdout__
            self.assertEqual(f"\033[91mInvalid profile inputs \033[0m\n", output.getvalue())

            app.stop()

        Clock.schedule_once(test, 0)
        app.run()

    def test_invalid_goal(self):
        app = AddictionRecovery(database_filepath=":memory:")
        Repository.instance.reset()

        def test(*args):
            profile = app.screens.get("profile")
            self.assertEqual(profile.submit_button_text, "Submit")

            # Load fake information
            profile.person_name.text = "name"
            profile.weight.text = "123"
            profile.person_height.text = "123"
            profile.birth.text = "2000/01/01"
            profile.substance.text = "Coffee"
            profile.goal.text = "text"

            # Check that there are errors
            output = io.StringIO()
            sys.stdout = output
            profile.Submit()
            sys.stdout = sys.__stdout__
            self.assertEqual(f"\033[91mInvalid profile inputs \033[0m\n", output.getvalue())

            app.stop()

        Clock.schedule_once(test, 0)
        app.run()


class TestLoggingScreen(GraphicUnitTest):

    def create_profile(self, app):
        profile = app.screens.get("profile")
        profile.person_name.text = "name"
        profile.weight.text = "123"
        profile.person_height.text = "123"
        profile.birth.text = "2000/01/01"
        profile.substance.text = "Coffee"
        profile.goal.text = "10"
        profile.Submit()

    def test_submit(self):
        app = AddictionRecovery(database_filepath=":memory:")
        Repository.instance.reset()

        def test(*args):
            self.create_profile(app)
            logging = app.screens.get("logging")

            self.assertEqual(len(Repository.instance.get_uses_from_time_period(
                0, int(time.time()) + 10, AddictionRecovery.substance_tracking_ids.get("Coffee"))), 0)
            self.assertEqual(len(Repository.instance.get_common_substance_amounts(10)), 0)

            # Load fake information
            logging.substance.text = "Coffee"
            logging.amount.text = "10"
            logging.cost.text = "2.50"
            logging.specific_name.text = "small"

            # Check that there are no errors
            output = io.StringIO()
            sys.stdout = output
            logging.Submit()
            sys.stdout = sys.__stdout__
            self.assertEqual("", output.getvalue())

            self.assertEqual(len(Repository.instance.get_uses_from_time_period(
                0, int(time.time()) + 10, AddictionRecovery.substance_tracking_ids.get("Coffee"))), 1)
            self.assertEqual(len(Repository.instance.get_common_substance_amounts(10)), 1)

            self.assertEqual("Choose Substance", logging.substance.text)
            self.assertEqual("", logging.amount.text)
            self.assertEqual("", logging.cost.text)
            self.assertEqual("", logging.specific_name.text)

            app.stop()

        Clock.schedule_once(test, 0)
        app.run()

    def test_presets(self):
        app = AddictionRecovery(database_filepath=":memory:")
        Repository.instance.reset()

        def test(*args):
            self.create_profile(app)
            logging = app.screens.get("logging")

            for widget in logging.walk():
                if isinstance(widget, SubstancePresets):
                    self.assertEqual(len(list(filter(lambda c: isinstance(c, PresetButton), widget.walk()))), 0)

            # Load fake information
            logging.substance.text = "Coffee"
            logging.amount.text = "10"
            logging.cost.text = "2.50"
            logging.specific_name.text = "small"
            logging.Submit()

            for widget in logging.walk():
                if isinstance(widget, SubstancePresets):
                    self.assertEqual(len(Repository.instance.get_common_substance_amounts(10)), 1)

            app.stop()

        Clock.schedule_once(test, 0)
        app.run()

    def test_preset_submit(self):
        app = AddictionRecovery(database_filepath=":memory:")
        Repository.instance.reset()

        def test(*args):
            self.create_profile(app)
            logging = app.screens.get("logging")

            # Load fake information
            logging.substance.text = "Coffee"
            logging.amount.text = "10"
            logging.cost.text = "2.50"
            logging.specific_name.text = "small"
            logging.Submit()

            self.assertEqual(len(Repository.instance.get_uses_from_time_period(
                0, int(time.time()) + 10, AddictionRecovery.substance_tracking_ids.get("Coffee"))), 1)

            # Press preset button
            for widget in logging.walk():
                if isinstance(widget, SubstancePresets):
                    for child in widget.walk():
                        if isinstance(child, PresetButton):
                            child.on_press()
                            break

            self.assertEqual("Coffee", logging.substance.text)
            self.assertEqual("10.0", logging.amount.text)
            self.assertEqual("2.50", logging.cost.text)
            self.assertEqual("small", logging.specific_name.text)
            logging.Submit()

            self.assertEqual(len(Repository.instance.get_uses_from_time_period(
                0, int(time.time()) + 10, AddictionRecovery.substance_tracking_ids.get("Coffee"))), 2)
            self.assertEqual(len(Repository.instance.get_common_substance_amounts(10)), 1)

            self.assertEqual("Choose Substance", logging.substance.text)
            self.assertEqual("", logging.amount.text)
            self.assertEqual("", logging.cost.text)
            self.assertEqual("", logging.specific_name.text)

            app.stop()

        Clock.schedule_once(test, 0)
        app.run()

    def test_invalid_substance(self):
        app = AddictionRecovery(database_filepath=":memory:")
        Repository.instance.reset()

        def test(*args):
            self.create_profile(app)
            logging = app.screens.get("logging")

            # Load fake information
            logging.substance.text = "Cauliflower"
            logging.amount.text = "10"
            logging.cost.text = "2.50"
            logging.specific_name.text = "small"

            # Check that there are errors
            output = io.StringIO()
            sys.stdout = output
            logging.Submit()
            sys.stdout = sys.__stdout__
            self.assertEqual(f"\033[91mInvalid substance values \033[0m\n", output.getvalue())
            self.assertEqual(len(Repository.instance.get_common_substance_amounts(10)), 0)

            self.assertEqual("Cauliflower", logging.substance.text)
            self.assertEqual("10", logging.amount.text)
            self.assertEqual("2.50", logging.cost.text)
            self.assertEqual("small", logging.specific_name.text)

            app.stop()

        Clock.schedule_once(test, 0)
        app.run()

    def test_invalid_amount(self):
        app = AddictionRecovery(database_filepath=":memory:")
        Repository.instance.reset()

        def test(*args):
            self.create_profile(app)
            logging = app.screens.get("logging")

            # Load fake information
            logging.substance.text = "Coffee"
            logging.amount.text = "text"
            logging.cost.text = "2.50"
            logging.specific_name.text = "small"

            # Check that there are errors
            output = io.StringIO()
            sys.stdout = output
            logging.Submit()
            sys.stdout = sys.__stdout__
            self.assertEqual(f"\033[91mInvalid substance values \033[0m\n", output.getvalue())

            app.stop()

        Clock.schedule_once(test, 0)
        app.run()

    def test_invalid_cost(self):
        app = AddictionRecovery(database_filepath=":memory:")
        Repository.instance.reset()

        def test(*args):
            self.create_profile(app)
            logging = app.screens.get("logging")

            # Load fake information
            logging.substance.text = "Coffee"
            logging.amount.text = "10"
            logging.cost.text = "text"
            logging.specific_name.text = "small"

            # Check that there are errors
            output = io.StringIO()
            sys.stdout = output
            logging.Submit()
            sys.stdout = sys.__stdout__
            self.assertEqual(f"\033[91mInvalid substance values \033[0m\n", output.getvalue())

            app.stop()

        Clock.schedule_once(test, 0)
        app.run()


if __name__ == "__main__":
    unittest.main()
