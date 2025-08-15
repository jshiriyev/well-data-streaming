from typing import Dict, Any

import pandas as pd

from ._utils import utils

class Table(pd.DataFrame):
    """
    A DataFrame that lets you access columns via custom attribute names.

    Example
    -------
    >>> df = pd.DataFrame({"tarix": [1, 2, 3], "qoil": [10.0, 11.5, 9.7]})
    >>> tf = Table(df, tiein={"date": "tarix", "orate": "qoil"})
    >>> tf.date
    0    1
    1    2
    2    3
    Name: tarix, dtype: int64
    >>> tf.orate.mean()
    10.4

    """
    _metadata = ["_tiein"]

    def __init__(self, *args, tiein: Dict[str, str] | None = None, **kwargs):

        super().__init__(*args, **kwargs)
        
        object.__setattr__(self,"_tiein",tiein)

    @property
    def _constructor(self):
        def _c(*args, **kwargs):
            out = Table(*args, **kwargs)
            object.__setattr__(out, "_tiein", self._tiein.copy())
            return out
        return _c

    # Attribute -> mapped column (via tiein), or fall back to normal behavior
    def __getattr__(self, name: str) -> Any:
        # Only called if normal attribute lookup fails, so it's safe
        # tie = getattr(self, "_tiein", {})
        if name in self._tiein:
            column = self._tiein[name]
            if column in self.columns:
                return self[column]
            raise AttributeError(
                f"Attribute '{name}' is tied to column '{column}', which is not in the frame."
            )
        # As in pandas, allow column-as-attribute if it exists (optional)
        if name in self.columns:
            return self[name]

        raise AttributeError(f"{type(self).__name__!s} has no attribute '{name}'")

    def __getitem__(self, key):
        res = super().__getitem__(key)
        if isinstance(res, pd.DataFrame):
            # make sure it's our subclass and carries the mapping
            if not isinstance(res, Table):
                res = self._constructor(res)
            # ensure an independent copy of the tiein (in case pandas skipped metadata)
            object.__setattr__(res, "_tiein", self._tiein.copy())
        return res

    @property
    def datetimes(self):
        """Returns the list of column names with datetime format."""
        return utils.heads(self.frame,include=('datetime64',))

    @property
    def numbers(self):
        """Returns the list of column names with number format."""
        return utils.heads(self.frame,include=('number',))

    @property
    def nominals(self):
        """Returns the list of column names that are categorical by nature."""
        return utils.heads(self.frame,exclude=('number','datetime64'))

if __name__ == "__main__":

    import datetime

    df = pd.DataFrame({"tarix": [1, 2, 3], "qoil": [10.0, 11.5, 9.7]})

    Table.fields = ["date","orate"]

    tf = Table(df, tiein={"date": "tarix", "orate": "qoil"})

    print(tf.orate)

    print(isinstance(tf,pd.DataFrame))

    print(tf.orate.mean())

    print(type(tf.orate))

    Table.fields.extend(["a","b","c","d"])

    df = pd.DataFrame(dict(
        A=[datetime.date(2020,1,1),datetime.date(2021,1,1),datetime.date(2022,1,1),datetime.date(2023,1,1)],
        B=['A','B','C','D'],
        C=['5-6','7-8','9-10','11'],
        D=['XY','XZ','YZ','ZZ']))

    base = Table(df,tiein=dict(a='A',b='B',c='C'))

    print(base.c)

    # print(base[2].c)
    print(base[2:].c)

    # print(type(df.A))

    print(base.a)
    print(type(base.a))
    print(base.c)

    # print(base.tiein)
    # print(base['A'])
    # print(base[2])

    # print(perfs.tiein)
    # print(perfs[2])

    # print(perfs.layer)

    # perfs2 = PerfFrame()

    # print(perfs2.tiein)

    # # # for d in dir(frame):
    # # #     print(d)
