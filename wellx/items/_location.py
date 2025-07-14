from dataclasses import dataclass

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

    def index(self,key):
        """Returns the index of formation based on its name."""
        return self.keys.index(key)

    def __getitem__(self,key):
        """Returns the list of formation tops based on formation name."""
        return self.tops[self.index(key)]

    def limit(self,key):
        """Returns the list of formation tops and bottoms based on formation name."""
        return self.tops[self.index(key)], self.tops[self.index(key)+1]
 
    @property
    def keys(self):
        """Getter for the formation keys."""
        return self._keys

    @property
    def tops(self):
        """Getter for the formation tops."""
        return self._tops

if __name__ == "__main__":

    zones = Zones()

    print(zones.tops)
    print(zones.keys)