from dataclasses import dataclass

import datetime

from ._location import Depth

@dataclass
class Target:
	"""It is a Target dictionary for a well."""
	x 		: float = None
	y 		: float = None

	depth   : dict = None

	def __post_init__(self):

		if self.depth is not None:
			self.depth = Depth(**self.depth)

@dataclass
class Drilling:
	"""It is a drilling dictionary for a well."""
	start	: datetime.date = None
	end		: datetime.date = None

	depth 	: dict = None
	target  : dict = None

	def __post_init__(self):

		if self.depth is not None:
			self.depth = Depth(**self.depth)

		if self.target is not None:
			self.target = Target(**self.target)

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

class Layout():

    def __init__(self,*args:Pipe):

        self._list = list(args)

    def __getitem__(self,key):
        """Retrieves a 'Pipe' object by index."""
        return self._list[key]

    def __iter__(self):
        """Allows iteration over the 'Pipe' objects."""
        return iter(self._list)

    def __len__(self) -> int:
        """Returns the number of 'Pipe' objects."""
        return len(self._list)

    def add(self,**kwargs):
        """Adds one pipe item."""
        self._list.append(Pipe(**kwargs))

    def append(self,pipe:Pipe) -> None:
        """Adds a new 'Pipe' object to the collection."""
        if not isinstance(pipe, Pipe):
            raise TypeError("Only Pipe objects can be added.")
        self._list.append(pipe)

    def extend(self,pipes:Pipe) -> None:
        """Adds a new 'Pipe' object to the collection."""
        for pipe in pipes:
            self.append(pipe)

    def __getattr__(self,key):
        """Forwards attribute access to the internal list object."""
        return getattr(self._list,key)

if __name__ == "__main__":

	drill = Drilling(
		datetime.date(1990,2,2),
		datetime.date(1990,4,3),
		depth={}
		)

	print(drill.end)

	print(drill.start)

	print(drill.depth)