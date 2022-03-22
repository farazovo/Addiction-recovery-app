from abc import ABC, abstractmethod
import sqlite3


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
    def start(self): pass

    @abstractmethod
    def close(self): pass


class SqlRepository(Repository):
    """
    A repository that provides an interface for the rest of the program to interact with a
    database.
    """

    def __init__(self):
        super().__init__()
        self.connection = None
        self.cursor = None

    def start(self, filepath="database.db"):
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
        if self.connection:
            self.connection.close()
            
    def write(self, tableName, data):
	    self.connection = sqlite3.connect("statistics.db")
		self.cursor = self.connection.cursor()
		self.cursor.execute("INSERT INTO (:tableName) VALUES (:data)", 
		{
			'tableName': tableName,
			'data': data,
		})	
		self.connection.commit()
		self.close()
    def basics(self, name, weight, height):
		self.write(user, name)
		self.write(user, weight)
		self.write(user, height)
       
