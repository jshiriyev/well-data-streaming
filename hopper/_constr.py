
from dataclasses import dataclass, fields

import datetime

import numpy

from ._survey import Depth

@dataclass
class Target:
	"""It is a Target dictionary for a well."""
	x 		: float = None
	y 		: float = None

	depth   : dict = None

	def __post_init__(self):

		if self.depth is not None:
			self.depth = Depth(**self.depth)

class Depth():
    """A class representing depth, which can be either Measured Depth (MD) or True Vertical Depth (TVD)."""

    def __init__(self,MD=None,TVD=None):

        if MD is None and TVD is None:
            raise ValueError("Either MD or TVD must be provided.")
        
        self.MD = MD
        self.TVD = TVD
    
    def __repr__(self):
        return f"Depth(MD={self.MD}, TVD={self.TVD})"

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
class Survey:
    """It is a well survey (direction or trajectory)."""

    MD      : numpy.ndarray = None
    TVD     : numpy.ndarray = None
    DX      : numpy.ndarray = None
    DY      : numpy.ndarray = None
    INC     : numpy.ndarray = None
    AZI     : numpy.ndarray = None

    def md2td(self,values):
        return numpy.interp(values,self.MD,self.TVD)
        
    def td2md(self,values):
        return numpy.interp(values,self.TVD,self.MD)

    @staticmethod
    def inc2td(INC:numpy.ndarray,MD:numpy.ndarray):

        TVD = MD.copy()

        offset = MD[1:]-MD[:-1]
        radian = INC[1:]/180*numpy.pi

        TVD[1:] = numpy.cumsum(offset*numpy.cos(radian))

        return TVD

    @staticmethod
    def off2td(DX:numpy.ndarray,DY:numpy.ndarray,MD:numpy.ndarray):

        TVD = MD.copy()

        offMD = MD[1:]-MD[:-1]
        offDX = DX[1:]-DX[:-1]
        offDY = DY[1:]-DY[:-1]
                         
        TVD[1:] = numpy.sqrt(offMD**2-offDX**2-offDY**2)

        return numpy.cumsum(TVD)

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

@dataclass
class Interval:

    above   : float
    below   : float

    def tostr(self,template:str=None):
        """Converts the interval into a string."""
        if template is None:
            template = "{}-{}"

        return template.format(self.below,self.above)
    
    @staticmethod
    def tolist(interval:str,delimiter:str="-",decsep:str=".") -> list:
        """Converts a string interval into a list of floats.

        Parameters:
        ----------
        interval  : The interval string (e.g., "1005-1092").
        delimiter : The delimiter separating depths in the interval. Defaults to "-".
        decsep    : The decimal separator in the depth of the interval. Defaults to ".".
        
        Returns:
        -------
        List: A list containing one or two float values. If only one value
            is provided, the second element will be None.
        """
        try:
            depths = [float(depth.replace(decsep,'.')) for depth in interval.split(delimiter)]
            if len(depths)==1:
                depths.append(None)
            elif len(depths) > 2:
                raise ValueError(f"Unexpected format: '{interval}'. Expected format 'depth_1{delimiter}depth_2'.")
            return depths
        except ValueError as e:
            raise ValueError(f"Invalid interval format: {interval}. Error: {e}")

@dataclass
class Perf:
    """It is a dictionary for a perforation in a well."""
    interval    : tuple

    layer       : str = None
    guntype     : str = None
    start       : datetime.date = None
    stop        : datetime.date = None

    def __post_init__(self):

        self.interval = Interval(*self.interval)

    @staticmethod
    def fields() -> list:
        """Returns the list of field names in the Perf dataclass."""
        return [f.name for f in fields(Perf)]

class Perfs():
    """A collection of 'Perf' objects with list-like access."""

    def __init__(self,*args:Perf):

        self._list = list(args)

    def __getitem__(self,key):
        """Retrieves a 'Perf' object by index."""
        return self._list[key]

    def __iter__(self):
        """Allows iteration over the 'Perf' objects."""
        return iter(self._list)

    def __len__(self) -> int:
        """Returns the number of 'Perf' objects."""
        return len(self._list)

    def add(self,**kwargs):
        """Adds one perforation item."""
        self._list.append(Perf(**kwargs))

    def append(self,perf:Perf) -> None:
        """Adds a new 'Perf' object to the collection."""
        if not isinstance(perf, Perf):
            raise TypeError("Only Perf objects can be added.")
        self._list.append(perf)

    def extend(self,perfs:Perf) -> None:
        """Adds a new 'Perf' object to the collection."""
        for perf in perfs:
            self.append(perf)

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