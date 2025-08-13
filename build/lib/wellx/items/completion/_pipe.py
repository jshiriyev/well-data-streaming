from dataclasses import dataclass

@dataclass
class Pipe:
    """It is a base dictionary for a tubing or casing."""
    ID      : float = None # Inner diameter
    OD      : float = None # Outer diameter

    above   : dict = None # MD of pipe top
    below   : dict = None # MD of pipe shoe

    def __post_init__(self):

        self.above = Depth(**(self.above or {}))
        self.below = Depth(**(self.below or {}))