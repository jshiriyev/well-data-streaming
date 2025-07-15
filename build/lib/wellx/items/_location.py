import numpy as np

from dataclasses import dataclass, fields

@dataclass
class Survey:
    """It is a well survey (direction or trajectory)."""

    MD      : np.ndarray = None
    TVD     : np.ndarray = None
    DX      : np.ndarray = None
    DY      : np.ndarray = None
    INC     : np.ndarray = None
    AZI     : np.ndarray = None

    @staticmethod
    def fields() -> list:
        return [field.name for field in fields(Survey)]

    def md2td(self,values):
        return np.interp(values,self.MD,self.TVD)
        
    def td2md(self,values):
        return np.interp(values,self.TVD,self.MD)

    @staticmethod
    def inc2td(INC:np.ndarray,MD:np.ndarray):

        TVD = MD.copy()

        offset = MD[1:]-MD[:-1]
        radian = INC[1:]/180*np.pi

        TVD[1:] = np.cumsum(offset*np.cos(radian))

        return TVD

    @staticmethod
    def off2td(DX:np.ndarray,DY:np.ndarray,MD:np.ndarray):

        TVD = MD.copy()

        offMD = MD[1:]-MD[:-1]
        offDX = DX[1:]-DX[:-1]
        offDY = DY[1:]-DY[:-1]
                         
        TVD[1:] = np.sqrt(offMD**2-offDX**2-offDY**2)

        return np.cumsum(TVD)

class Depth():
    """A class representing depth, which can be either Measured Depth (MD) or True Vertical Depth (TVD)."""

    def __init__(self,MD=None,TVD=None):

        if MD is None and TVD is None:
            raise ValueError("Either MD or TVD must be provided.")
        
        self.MD = MD
        self.TVD = TVD
    
    def __repr__(self):
        return f"Depth(MD={self.MD}, TVD={self.TVD})"

class Zones():
    """A class to store and utilize formation tops across the geom."""

    def __init__(self,**kwargs):
        """Initializes the Zone with named top values."""

        keys,tops = [],[]

        for name,vals in kwargs.items():
            keys.append(name)
            tops.append(vals)

        sorted_pairs = sorted(zip(tops,keys))

        if sorted_pairs:
            self._tops,self._keys = zip(*sorted_pairs)
        else:
            self._tops,self._keys = [],[]

    @property
    def keys(self):
        """Getter for the formation keys."""
        return self._keys

    @property
    def tops(self):
        """Getter for the formation tops."""
        return self._tops

    def index(self,key):
        """Returns the index of formation based on its name."""
        return self.keys.index(key)

    def __getitem__(self,key):
        """Returns the list of formation tops based on formation name."""
        return self.tops[self.index(key)]

    def limit(self,key):
        """Returns the list of formation tops and bottoms based on formation name."""
        index = self.index(key)

        lower = None if index==len(self._tops)-1 else self._tops[index+1]

        return self._tops[index], lower

if __name__ == "__main__":

    zones = Zones(A=1952,B=2775)

    print(zones.tops)
    print(zones.keys)

    print(zones.index("B"))
    print(zones.limit("B"))