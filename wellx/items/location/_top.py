from dataclasses import dataclass, fields

import numpy as np

@dataclass
class Top:

    formation       : str
    depth           : np.ndarray
    facecolor       : str = None

    @staticmethod
    def fields() -> list:
        return [field.name for field in fields(Top)]