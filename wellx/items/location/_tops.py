from ._top import Top

class Tops():
    """A class to store and utilize formation tops across the geom."""

    def __init__(self,**kwargs):
        """Initializes the Zone with named top values."""

        formation,depth = [],[]

        for name,vals in kwargs.items():
            formation.append(name)
            depth.append(vals)

        sorted_pairs = sorted(zip(depth,formation))

        if sorted_pairs:
            self._depth,self._formation = zip(*sorted_pairs)
        else:
            self._depth,self._formation = [],[]

    @staticmethod
    def fields() -> list:
        return Top.fields()

    @property
    def formation(self):
        """Getter for the formation names."""
        return self._formation

    @property
    def depth(self):
        """Getter for the formation tops."""
        return self._depth

    def index(self,key):
        """Returns the index of formation based on its name."""
        return self.formation.index(key)

    def __getitem__(self,key):
        """Returns the list of formation tops based on formation name."""
        return self.depth[self.index(key)]

    def limit(self,key):
        """Returns the list of formation tops and bottoms based on formation name."""
        index = self.index(key)

        lower = None if index==len(self._depth)-1 else self._depth[index+1]

        return self._depth[index], lower

if __name__ == "__main__":

    zones = Tops(A=1952,B=2775)

    print(zones.depth)
    print(zones.formation)

    print(zones.index("B"))
    print(zones.limit("B"))