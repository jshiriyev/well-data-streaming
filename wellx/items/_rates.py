from dataclasses import dataclass, fields

import datetime

@dataclass
class Rates:
    """It is a Rate dictionary for a perf in a well."""

    date    : datetime.date = None
    well    : str = None

    days    : int = None

    horizon : str = None

    optype  : str = "production"

    orate   : float = None
    wrate   : float = None
    grate   : float = None

    @staticmethod
    def fields() -> list:
        return [field.name for field in fields(Rates)]