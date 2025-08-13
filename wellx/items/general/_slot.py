from dataclasses import dataclass

@dataclass
class Slot:
    """It is a slot dictionary for a well."""
    index   : int = None

    plt     : str = None

    xhead   : float = 0.0
    yhead   : float = 0.0
    datum   : float = 0.0