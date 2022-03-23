from abc import ABC, abstractmethod
import sqlite3
from typing import Iterable, List, Tuple


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
                    age INTEGER
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
        :return: A list of tuples that represent the rows that matched the query
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
