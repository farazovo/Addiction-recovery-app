import unittest

from repository import SqlRepository, Repository
from entities import *


class TestSqlRepository(unittest.TestCase):

    def test_repository_start_and_close(self):
        """
        Test whether the repository can be started, closed and whether this sets the Repository
        singleton's instance.
        """

        # Test constructor
        self.assertIsNone(Repository.instance)
        repository = SqlRepository()
        self.assertIsNone(repository.cursor)
        self.assertIsNone(repository.connection)
        self.assertEqual(Repository.instance, repository)

        # Test start
        self.assertTrue(repository.start(filepath=":memory:"))
        self.assertIsNotNone(repository.cursor)
        self.assertIsNotNone(repository.connection)

        # Test close
        repository.close()
        self.assertIsNone(repository.cursor)
        self.assertIsNone(repository.connection)
        self.assertIsNone(Repository.instance)

    def test_person(self):
        with SqlRepository(":memory:") as r:
            person = Person("name", 1, 10, 100)
            self.assertIsNone(person.id)
            person.id = r.create_person(person)
            self.assertIsNotNone(person.id)
            retrieved_person = r.get_person(person.id)
            self.assertEqual(person, retrieved_person)

    def test_substance_tracking(self):
        with SqlRepository(":memory:") as r:
            substance_tracking = SubstanceTracking(1, 1)
            self.assertIsNone(substance_tracking.id)
            substance_tracking.id = r.create_substance_tracking(substance_tracking)
            self.assertIsNotNone(substance_tracking.id)
            retrieved_substance_tracking = r.get_substance_tracking(substance_tracking.id)
            self.assertEqual(substance_tracking, retrieved_substance_tracking)

    def test_substance(self):
        with SqlRepository(":memory:") as r:
            substance = Substance("Coffee", 1)
            self.assertIsNone(substance.id)
            substance.id = r.create_substance(substance)
            self.assertIsNotNone(substance.id)
            retrieved_substance = r.get_substance(substance.id)
            self.assertEqual(substance, retrieved_substance)

    def test_substance_use(self):
        with SqlRepository(":memory:") as r:
            substance_use = SubstanceUse(1, 1, 0)
            self.assertIsNone(substance_use.id)
            substance_use.id = r.create_substance_use(substance_use)
            self.assertIsNotNone(substance_use.id)
            retrieved_substance_use = r.get_substance_use(substance_use.id)
            self.assertEqual(substance_use, retrieved_substance_use)

    def test_substance_amount(self):
        with SqlRepository(":memory:") as r:
            substance_amount = SubstanceAmount(1, 100, "Small coffee")
            self.assertIsNone(substance_amount.id)
            substance_amount.id = r.create_substance_amount(substance_amount)
            self.assertIsNotNone(substance_amount.id)
            retrieved_substance_amount = r.get_substance_amount(substance_amount.id)
            self.assertEqual(substance_amount, retrieved_substance_amount)

    def test_goal(self):
        with SqlRepository(":memory:") as r:
            goal = Goal(1, 1, 10, 0)
            self.assertIsNone(goal.id)
            goal.id = r.create_goal(goal)
            self.assertIsNotNone(goal.id)
            retrieved_goal = r.get_goal(goal.id)
            self.assertEqual(goal, retrieved_goal)

    def test_goal_type(self):
        with SqlRepository(":memory:") as r:
            goal_type = GoalType("Use limit", "Stay under this amount at all times.")
            self.assertIsNone(goal_type.id)
            goal_type.id = r.create_goal_type(goal_type)
            self.assertIsNotNone(goal_type.id)
            retrieved_goal_type = r.get_goal_type(goal_type.id)
            self.assertEqual(goal_type, retrieved_goal_type)

    def test_update_person(self):
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


if __name__ == "__main__":
    unittest.main()
