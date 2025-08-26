from dataclasses import dataclass, field

import types

from typing import Optional

@dataclass
class Section:
    """
    Represents a single tubular section (casing/liner/tubing, etc.)
    along a wellbore.

    All depths are measured along hole (MD). Units are user-defined but
    must be consistent across fields (e.g., meters + millimeters, or
    feet + inches). Geometry-derived properties are unit-consistent
    (area in “diameter units”).

    """
    well        : Optional[str] = field(default="", metadata={"desc": "Well identifier"})
    rank        : Optional[int] = field(default=1, metadata={"desc": "Order of section in layout (1-based recommended)"})
    kind        : Optional[str] = field(default="", metadata={"desc": "Section type (casing, liner, tubing, ...)"})

    top         : Optional[float] = field(default=None, metadata={"unit": "m", "desc": "Section Top"})
    base        : Optional[float] = field(default=None, metadata={"unit": "m", "desc": "Section Base (> top)"})

    outer_diam  : Optional[float] = field(default=None, metadata={"unit": "inch", "desc": "Outer diameter"})
    inner_diam  : Optional[float] = field(default=None, metadata={"unit": "inch", "desc": "Inner diameter, must be <= outer_diam."})
    thickness = None
    hole_diam   : Optional[float] = field(default=None, metadata={"unit": "inch", "desc":"Hole diameter. If provided, should be >= outer_diam."})
    
    weight      : Optional[float] = field(default=None, metadata={"unit": "weight/length"})
    grade       : Optional[str]   = field(default="", metadata={"desc": "Steel grade"})

    hanger      : Optional[float] = field(default=None, metadata={"unit": "m", "desc": "Hanger depth (for liners)"})
    crossover   : Optional[float] = field(default=None, metadata={"unit": "m", "desc": "Crossover depth if present"})
    shoe        : Optional[float] = field(default=None, metadata={"unit": "m", "desc": "Shoe depth; typically ≈ base depth."})

    cement_top  : Optional[float] = field(default=None, metadata={"unit": "m", "desc": "Cement top MD (for cased sections). Should lie in [top, base]"})
    cement_consumption = None
    cement_grade: Optional[str] = field(default=None, metadata={"desc": ""})

    comment     : Optional[str] = field(default="", metadata={"desc": "Free-form notes."})

    @classmethod
    def get_metadata(cls,name:str):
        """Return the dataclass field metadata for field `name`."""
        return cls.__dataclass_fields__[name].metadata

    @classmethod
    def replace_metadata(cls, name: str, new_metadata: dict):
        """Replace the metadata dictionary of a given dataclass field."""
        if not isinstance(new_metadata, dict):
            raise TypeError("new_metadata must be a dictionary")

        f = cls.__dataclass_fields__[name]
        f.metadata = types.MappingProxyType(dict(new_metadata))
        
class Layout():

    def __init__(self,*args:Section):

        self._list = list(args)

    def __getitem__(self,key):
        """Retrieves a 'Section' object by index."""
        return self._list[key]

    def __iter__(self):
        """Allows iteration over the 'Section' objects."""
        return iter(self._list)

    def __len__(self) -> int:
        """Returns the number of 'Section' objects."""
        return len(self._list)

    def add(self,**kwargs):
        """Adds one pipe item."""
        self._list.append(Section(**kwargs))

    def append(self,pipe:Section) -> None:
        """Adds a new 'Section' object to the collection."""
        if not isinstance(pipe, Section):
            raise TypeError("Only Section objects can be added.")
        self._list.append(pipe)

    def extend(self,pipes:Section) -> None:
        """Adds a new 'Section' object to the collection."""
        for pipe in pipes:
            self.append(pipe)

    def __getattr__(self,key):
        """Forwards attribute access to the internal list object."""
        return getattr(self._list,key)