from ._perf import Perf

class Perfs():
    """A collection of 'Perf' objects with list-like access."""

    def __init__(self,*args:Perf):

        self._list = list(args)

    @staticmethod
    def fields() -> list:
        """Returns the list of field names in the Perf dataclass."""
        return Perf.fields()

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
