from dataclasses import dataclass, fields

import datetime

from ._interval import Interval

@dataclass
class Perf:
    """It is a dictionary for a perforation in a well."""
    interval    : tuple

    layer       : str = None
    guntype     : str = None
    date        : datetime.date = None

    def __post_init__(self):

        self.interval = Interval(*self.interval)

    @staticmethod
    def fields() -> list:
        """Returns the list of field names in the Perf dataclass."""
        return [f.name for f in fields(Perf)]