from abc import ABC, abstractmethod
import sqlite3
from typing import Iterable, List, Tuple, Optional

from entities import *


class Repository(ABC):
    """
    Abstract repository class that ensures that subclasses have all the methods that are needed
    by the rest of the program to interact with a datasource. Repository is a singleton so
    instantiations of any subclass will make that the active one.
    """
    instance = None

    def __init__(self):
        Repository.instance = self

    @abstractmethod
    def start(self) -> bool: pass

    @abstractmethod
    def close(self):
        if Repository.instance == self:
            Repository.instance = None

    """
    Create entities:
        These methods create an entity and return their id
    """

    @abstractmethod
    def create_person(self, person: Person) -> int: pass

    @abstractmethod
    def create_substance_tracking(self, tracking: SubstanceTracking) -> int: pass

    @abstractmethod
    def create_substance(self, substance: Substance) -> int: pass

    @abstractmethod
    def create_substance_use(self, use: SubstanceUse) -> int: pass

    @abstractmethod
    def create_substance_amount(self, amount: SubstanceAmount) -> int: pass

    @abstractmethod
    def create_goal(self, goal: Goal) -> int: pass

    @abstractmethod
    def create_goal_type(self, goal_type: GoalType) -> int: pass

    """
    Retrieve data:
        These methods perform queries on the data. They either return the requested data
        or None if data matching the query cannot be found.
    """

    @abstractmethod
    def get_person(self, person_id: int) -> Optional[Person]: pass

    @abstractmethod
    def get_substance_tracking(self, tracking_id: int) -> Optional[SubstanceTracking]: pass

    @abstractmethod
    def get_substance(self, substance_id: int) -> Optional[Substance]: pass

    @abstractmethod
    def get_substance_use(self, use_id: int) -> Optional[SubstanceUse]: pass

    @abstractmethod
    def get_substance_amount(self, amount_id: int) -> Optional[SubstanceAmount]: pass

    @abstractmethod
    def get_goal(self, goal_id: int) -> Optional[Goal]: pass

    @abstractmethod
    def get_goal_type(self, goal_type_id: int) -> Optional[GoalType]: pass

    @abstractmethod
    def get_common_substance_amounts(self, tracking_id: int, count: int) -> List[SubstanceAmount]:
        """
        Gets the most commonly used substance amounts for quick access.

        :param tracking_id: the id of the substance tracking that the substance amounts are for.
        :param count: the maximum number of substance amounts to be returned.
        :return: A list of SubstanceAmount objects
        """

    @abstractmethod
    def get_substance_amount_from_data(self, amount: int, cost: int) -> Optional[SubstanceAmount]:
        """
        Gets a substance amount from the amount and cost, returning a SubstanceAmount data class if
        a match was found.
        """


class SqlRepository(Repository):
    """
    A repository that provides an interface for the rest of the program to interact with a
    database.
    """

    def __init__(self):
        super().__init__()
        self.connection = None
        self.cursor = None

    def start(self, filepath="database.db") -> bool:
        """
        Initialises the connection to the database and creates tables if needed.

        :param filepath: the filepath to the database. The default is database.db.
        :return: a bool of whether the database was created successfully.
        """
        try:
            # Setup database connection
            self.connection = sqlite3.connect(filepath)
            self.cursor = self.connection.cursor()

            # Create the tables for the first start-up
            # Doesn't use self.try_execute_command() as this commits after every command.
            # This will leave the database in an invalid state if there is an error after one of
            # the commands.
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Person (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    weight INTEGER,
                    height INTEGER,
                    dob INTEGER
                );
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS SubstanceTracking (
                    id INTEGER PRIMARY KEY,
                    person_id INTEGER,
                    substance_id INTEGER,
                    FOREIGN KEY(person_id) REFERENCES Person(id),
                    FOREIGN KEY(substance_id) REFERENCES Substance(id)
                );
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Substance (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    half_life REAL
                );
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS SubstanceUse (
                    id INTEGER PRIMARY KEY,
                    substance_tracking_id INTEGER,
                    amount_id INTEGER,
                    time INTEGER,
                    FOREIGN KEY(substance_tracking_id) REFERENCES SubstanceTracking(id),
                    FOREIGN KEY(amount_id) REFERENCES SubstanceAmount(id)
                );
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS SubstanceAmount (
                    id INTEGER PRIMARY KEY,
                    amount REAL,
                    cost INTEGER
                );
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Goal (
                    id INTEGER PRIMARY KEY,
                    substance_tracking_id INTEGER,
                    goal_type_id INTEGER,
                    value INTEGER,
                    FOREIGN KEY(substance_tracking_id) REFERENCES SubstanceTracking(id),
                    FOREIGN KEY(goal_type_id) REFERENCES GoalType(id)
                );
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS GoalType (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    description TEXT
                );
            """)
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Error in setting up database: {e.args}")
            return False
        return True

    def close(self):
        super().close()
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None

    def try_execute_command(self, command: str, parameters: Iterable = ...) -> bool:
        """
        Attempts to execute an SQL command without throwing an exception if there is an error.

        :param command: the SQL command to be executed
        :param parameters: the parameters that are to be supplied to the SQL command
        :return: a bool of whether the command was executed without errors
        """
        try:
            self.cursor.execute(command, parameters)
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            if parameters is ...:
                print(f"\033[91m Error in executing command '{command}' : {e.args} \033[0m")
            else:
                print(
                    f"\033[91m Error in executing command '{command}'\
                    with parameters '{parameters}' : {e.args} \033[0m"
                )
            return False

    def try_execute_query(self, query: str, parameters: Iterable = ...) -> List[Tuple]:
        """
        Attempts to execute an SQL query without throwing an exception if there is an error.

        :param query: the SQL query to be executed
        :param parameters: the parameters that are to be supplied to the SQL query
        :return: a list of tuples that represent the rows that matched the query
        """
        try:
            self.cursor.execute(query, parameters)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            if parameters is ...:
                print(f"\033[91m Error in executing query '{query}' : {e.args} \033[0m")
            else:
                print(
                    f"\033[91m Error in executing query '{query}'\
                    with parameters '{parameters}' : {e.args} \033[0m"
                )
            return []

    """ Create entities """

    def create_person(self, person: Person) -> int:
        self.try_execute_command(
            "INSERT INTO Person(name, weight, height, dob) VALUES (?, ?, ?, ?);",
            (person.name, person.weight, person.height, person.dob)
        )
        return self.cursor.lastrowid

    def create_substance_tracking(self, tracking: SubstanceTracking) -> int:
        self.try_execute_command(
            "INSERT INTO SubstanceTracking(person_id, substance_id) VALUES (?, ?);",
            (tracking.person_id, tracking.substance_id)
        )
        return self.cursor.lastrowid

    def create_substance(self, substance: Substance) -> int:
        self.try_execute_command(
            "INSERT INTO Substance(name, half_life) VALUES (?, ?);",
            (substance.name, substance.half_life)
        )
        return self.cursor.lastrowid

    def create_substance_use(self, use: SubstanceUse) -> int:
        self.try_execute_command(
            "INSERT INTO SubstanceUse(substance_tracking_id, amount_id, time) VALUES (?, ?, ?);",
            (use.substance_tracking_id, use.amount_id, use.time)
        )
        return self.cursor.lastrowid

    def create_substance_amount(self, amount: SubstanceAmount) -> int:
        self.try_execute_command(
            "INSERT INTO SubstanceAmount(amount, cost) VALUES (?, ?);",
            (amount.amount, amount.cost)
        )
        return self.cursor.lastrowid

    def create_goal(self, goal: Goal) -> int:
        self.try_execute_command(
            "INSERT INTO Goal(substance_tracking_id, goal_type_id, value) VALUES (?, ?, ?);",
            (goal.substance_tracking_id, goal.goal_type_id, goal.value)
        )
        return self.cursor.lastrowid

    def create_goal_type(self, goal_type: GoalType) -> int:
        self.try_execute_command(
            "INSERT INTO GoalType(name, description) VALUES (?, ?);",
            (goal_type.name, goal_type.description)
        )
        return self.cursor.lastrowid

    """ Retrieve data """

    def get_entity(self, table: str, entity_id: int) -> Optional[Tuple]:
        """
        Helper function to query the database to find an entity.

        :param table: the name of the table in the database to be queried
        :param entity_id: the id of the entity to be retrieved
        :return: a tuple that represents the entity that matched the query
        """
        entities = self.try_execute_query(
            f"SELECT * FROM {''.join(filter(lambda c: c.isalpha(), table))} WHERE id = ?",
            (entity_id,)
        )
        if len(entities):
            # Unpack and reorder tuple to put id last
            return *entities[0][1:], entities[0][0]
        return None

    def get_person(self, person_id: int) -> Optional[Person]:
        if data := self.get_entity("Person", person_id):
            return Person(*data)
        return None

    def get_substance_tracking(self, tracking_id: int) -> Optional[SubstanceTracking]:
        if data := self.get_entity("SubstanceTracking", tracking_id):
            return SubstanceTracking(*data)
        return None

    def get_substance(self, substance_id: int) -> Optional[Substance]:
        if data := self.get_entity("Substance", substance_id):
            return Substance(*data)
        return None

    def get_substance_use(self, use_id: int) -> Optional[SubstanceUse]:
        if data := self.get_entity("SubstanceUse", use_id):
            return SubstanceUse(*data)
        return None

    def get_substance_amount(self, amount_id: int) -> Optional[SubstanceAmount]:
        if data := self.get_entity("SubstanceAmount", amount_id):
            return SubstanceAmount(*data)
        return None

    def get_goal(self, goal_id: int) -> Optional[Goal]:
        if data := self.get_entity("Goal", goal_id):
            return Goal(*data)
        return None

    def get_goal_type(self, goal_type_id: int) -> Optional[GoalType]:
        if data := self.get_entity("GoalType", goal_type_id):
            return GoalType(*data)
        return None

    def get_common_substance_amounts(self, tracking_id: int, count: int) -> List[SubstanceAmount]:
        substance_amounts = self.try_execute_query(
            """
            SELECT SubstanceAmount.*
            FROM SubstanceAmount, (
                SELECT SubstanceUse.amount_id, COUNT(*) AS uses
                FROM SubstanceUse
                WHERE SubstanceUse.substance_tracking_id = ?
                GROUP BY SubstanceUse.amount_id
                ORDER BY uses DESC
                LIMIT ?
            ) AS CommonAmounts
            WHERE CommonAmounts.amount_id = SubstanceAmount.id
            ORDER BY CommonAmounts.uses DESC;
            """,
            (tracking_id, count)
        )
        return [SubstanceAmount(*s[1:], s[0]) for s in substance_amounts]

    def get_substance_amount_from_data(self, amount: int, cost: int) -> Optional[SubstanceAmount]:
        substance_amounts = self.try_execute_query(
            "SELECT * FROM SubstanceAmount WHERE amount = ? AND cost = ?",
            (amount, cost)
        )
        if len(substance_amounts):
            # Unpack and reorder tuple to put id last
            return SubstanceAmount(*substance_amounts[0][1:], substance_amounts[0][0])
        return None
