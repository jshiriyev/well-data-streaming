import copy

from typing import Dict, Any

import pandas as pd

class Table(pd.DataFrame):
    """
    A ``DataFrame`` subclass that lets you access **columns via alias attributes**
    defined in the ``tiein`` mapping (alias -> column name).

    Parameters
    ----------
    *args, **kwargs :
        Passed through to ``pandas.DataFrame``.
    tiein : Dict[str, str], optional
        Mapping from **alias** (attribute you want to use) to **real column name**
        in the frame. If provided, Table will allow ``table.alias`` to access
        ``table["real_column"]``.

    Attributes
    ----------
    tiein : Mapping[str, str] | None
        The alias->column mapping (preserved across DataFrame-returning ops).

    Notes
    -----
    - ``_metadata`` lists custom attributes pandas should preserve on objects
      created by DataFrame-returning operations (e.g., filtering, copy). We also
      implement ``__finalize__`` to copy this metadata (deeply for mutables).
    - Column **attribute** access (``table.col``) falls back to standard pandas
      behavior if the name is not in ``tiein``.
    - Top-level constructors like ``pd.concat`` or ``pd.merge`` may return a plain
      ``DataFrame`` (pandas limitation). Methods like ``df.merge`` typically round-trip
      through your subclass and preserve metadata.

    Example
    -------
    >>> import pandas as pd
    >>> df = pd.DataFrame({"tarix": [1, 2, 3], "qoil": [10.0, 11.5, 9.7]})
    >>> tf = Table(df, tiein={"date": "tarix", "orate": "qoil"})
    >>> tf.date
    0    1
    1    2
    2    3
    Name: tarix, dtype: int64
    >>> tf.orate.mean()
    10.4
    >>> tf2 = tf[["tarix"]]      # preserves subclass and metadata
    >>> isinstance(tf2, Table), tf2.tiein
    (True, {'date': 'tarix', 'orate': 'qoil'})

    """
    _metadata = ["_tiein"]

    def __init__(self, *args, tiein: Dict[str, str] = None, **kwargs):

        super().__init__(*args, **kwargs)
        
        object.__setattr__(self,"_tiein",tiein)

    @property
    def tiein(self) -> Dict[str, str]:
        """Read-only view of the alias->column mapping (may be None)."""
        return self._tiein

    @property
    def _constructor(self):
        # Ensure new 2D results come back as Table and carry metadata
        def _ctor(*args, **kwargs):
            return type(self)(*args, **kwargs).__finalize__(self)
        return _ctor

    def __finalize__(self, other, method=None, **kwargs):
        if other is None:
            return self
        for name in getattr(other, "_metadata", []):
            if name in self._metadata:
                val = getattr(other, name, None)
                # Deep copy mutable metadata to avoid shared state
                if isinstance(val, (dict, list, set)):
                    val = copy.deepcopy(val)
                object.__setattr__(self, name, val)

        return self

    # Attribute -> mapped column (via tiein), or fall back to normal behavior
    def __getattr__(self, name: str) -> Any:
        """
        Resolve attribute access in this order:
        1) If ``name`` is an alias in ``tiein`` and the mapped column exists, return that column (Series).
        2) If ``name`` is an actual column name, return that column (Series).
        3) Otherwise, raise AttributeError.

        """
        # Only called if normal attribute lookup fails, so it's safe
        if self._tiein and name in self._tiein:
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

    @property
    def datetimes(self):
        """Returns the list of column names with datetime format."""
        return self.get_heads(self,include=('datetime64',))

    @property
    def numbers(self):
        """Returns the list of column names with number format."""
        return self.get_heads(self,include=('number',))

    @property
    def nominals(self):
        """Returns the list of column names that are categorical by nature."""
        return self.get_heads(self,exclude=('number','datetime64'))

    @staticmethod
    def get_heads(frame:pd.DataFrame,*args,include:tuple[str]=None,exclude:tuple[str]=None)->list[str]:
        """
        Returns the list of heads that are in the DataFrame and after
        including & excluding the dtypes.

        Parameters:

        *args   : Positional column names to check in the DataFrame.

        include  : Include dtypes for the head selection.
        exclude  : Exclude dtypes for the head selection.

        Return:

        A list of column names that exist in the DataFrame and that match the
        specified include and exclude criteria.

        """
        head_list = [head for head in args if head in frame.columns]

        if include is None and exclude is None:
            return head_list

        head_list += frame.select_dtypes(include=include,exclude=exclude).columns.tolist()

        return list(set(head_list))

    @staticmethod
    def join_columns(frame:pd.DataFrame,*args,sep:str=None,**kwargs)->pd.DataFrame:
        """
        Joins the frame columns specified by the args and kwargs and
        returns a new joined frame.

        Parameters:

        *args     : Positional column names to check in the DataFrame.
        sep       : The characters to add between column items.
        **kwargs  : include and exclude dtypes for the head selection.

        Returns:

        The joined frame.

        """
        heads = Table.get_heads(frame,*args,**kwargs)

        sep = " " if sep is None else sep

        value = frame[heads].astype("str").agg(sep.join,axis=1)

        return pd.DataFrame({sep.join(heads):value})

    @staticmethod
    def filter_column(frame:pd.DataFrame,column:str,*args)->pd.DataFrame:
        """
        Filters the non-empty input frame by checking the 
        series specified by column for args.
        
        Parameters:
        ----------
        column   : Column name where to search for args
        *args   : Positional values to keep in the column series.

        Returns:
        -------
        A new filtered frame.
        
        """
        return frame[frame[column].isin(args)].reset_index(drop=True)

    @staticmethod
    def groupsum_column(frame:pd.DataFrame,column:str,*args):
        """
        Groups the non-empty input frame based on column and
        returns a new frame after summing the other columns.
        
        Parameters:
        ----------
        column   : Column name which to group
        *args   : Positional values to keep in the column series.

        Returns:
        -------
        A new summed frame.

        """
        frame = frame[Table.get_heads(frame,column,include=('number',))]

        frame = Table.filter_column(frame,column,*args)

        frame[column] = "".join(frame[column].unique())

        frame = frame.groupby(column).sum().reset_index(drop=True)

        return frame

if __name__ == "__main__":

    import datetime

    df = pd.DataFrame(dict(
        A=[datetime.date(2020,1,1),datetime.date(2021,1,1),datetime.date(2022,1,1),datetime.date(2023,1,1)],
        B=['A','B','C','D'],
        C=['5-6','7-8','9-10','11'],
        D=['XY','XZ','YZ','ZZ']))

    base = Table(df,tiein=dict(a='A',b='B',c='C'))

    print(base.shape)

    print(base)

    print(base.iloc[0])

    print(base.tiein)

    print(base.a)
    print(base['A'])
    print(type(base.a))
    print(type(base.A))

    # print(base[2])

    print(base.c)
    # print(base[2].c)
    print(base[2:].c)