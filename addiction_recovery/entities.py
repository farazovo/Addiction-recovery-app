from dataclasses import dataclass
import datetime


@dataclass
class Person:
    """
    Properties:
        names, weight, height, dob (date of birth as unix timestamp), id (automatically assigned)
    """
    name: str
    weight: int
    height: int
    dob: int  # Unix timestamp
    id: int = None

    def calculate_age(self) -> int:
        dob_datetime = datetime.datetime.fromtimestamp(self.dob)
        return int((datetime.datetime.today() - dob_datetime).days / 365.2425)


@dataclass
class SubstanceTracking:
    """
    Properties:
        person_id, substance_id, id (automatically assigned)
    """
    person_id: int
    substance_id: int
    id: int = None


@dataclass
class Substance:
    """
    Properties:
        name, half_life, id (automatically assigned)
    """
    name: str
    half_life: float
    id: int = None


@dataclass
class SubstanceUse:
    """
    Properties:
        substance_tracking_id, amount_id, time (unix timestamp), id (automatically assigned)
    """
    substance_tracking_id: int
    amount_id: int
    time: int  # Unix timestamp
    id: int = None


@dataclass
class SubstanceAmount:
    """
    Properties:
        amount, cost (in pence), name, id (automatically assigned)
    """
    amount: float
    cost: int
    name: str
    id: int = None


@dataclass
class Goal:
    """
    Properties:
        substance_tracking_id, goal_type_id, value, id (automatically assigned)
    """
    substance_tracking_id: int
    goal_type_id: int
    value: int
    id: int = None


@dataclass
class GoalType:
    """
    Properties:
        name, description, id (automatically assigned)
    """
    name: str
    description: str
    id: int = None
