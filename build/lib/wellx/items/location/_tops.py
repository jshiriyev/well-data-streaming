from dataclasses import dataclass, field, fields
from typing import Iterable, Dict, List, Optional, Tuple

import numpy as np

@dataclass(slots=True)
class Tops:
    """
    Formation tops for a single well (MD-based), with geology-aware utilities.

    Geologic model
    --------------
    - Each item is a *formation top* picked in **measured depth (MD)**.
    - Depth is positive and increases downward.
    - Intervals are defined by pairing each top with the **next deeper top**.
      The deepest formation has bottom = **None** (open-ended).

    Assumptions (per user spec)
    ---------------------------
    - **One top per formation** per well (names are case-sensitive).
    - All depths must be **finite and >= 0**; inputs are sorted shallow→deep.
      Duplicate formation names **raise**.
    - Missing formations are treated as errors when queried (raise).
    - `facecolor` is optional metadata stored per formation and may be
      merged/overridden by the user (no color validation is enforced).

    Parameters
    ----------
    formation : Iterable[str]
        Formation names (case-sensitive).
    depth : Iterable[float]
        MD tops (positive downward). Will be sorted shallow→deep if not already.
    facecolor : Optional[Dict[str, str]]
        Optional mapping of formation name → facecolor string for plotting.

    Key methods
    -----------
    - `formations` / `depths` : ordered names and MD tops (numpy array copy).
    - `get_top(name)`         : MD at top of a formation.
    - `get_limit(name)`       : (top, bottom) MD pair; bottom is next deeper top or None.
    - `intervals()`           : list of (name, top, bottom) shallow→deep.
    - `find_at_md(md)`        : formation containing a given MD (or None if outside all intervals).
    - `add(...)` / `remove(...)` / `rename(...)`
    - `merge_facecolors(mapping)` / `facecolor_map()`

    Notes
    -----
    - This class holds tops for **one well**. Correlation across wells is a separate concern.
    - Returns are plain Python/numpy types; no pandas dependency.

    """
    formation: Iterable[str]
    depth:     Iterable[float]
    facecolor: Optional[Dict[str, str]] = None

    # Declare internal storage so slots know about them:
    _formation: List[str] = field(init=False, repr=False)
    _depth: np.ndarray     = field(init=False, repr=False)
    _facecolor: Dict[str, str] = field(init=False, repr=False, default_factory=dict)

    def __post_init__(self) -> None:
        names = list(self.formation)
        depths = np.asarray(list(self.depth), dtype=float)

        if len(names) != len(depths):
            raise ValueError("formation and depth must have the same length.")
        if depths.ndim != 1:
            raise ValueError("depth must be 1-D.")
        if not np.isfinite(depths).all():
            raise ValueError("All depths must be finite numbers.")
        if np.any(depths < 0):
            raise ValueError("All depths must be >= 0 for MD (positive downward).")

        # enforce unique formation names (case-sensitive)
        if len(set(names)) != len(names):
            dup = [n for n in set(names) if names.count(n) > 1]
            raise ValueError(f"Duplicate formation names not allowed: {dup}")

        # sort shallow → deep by MD; keep names aligned
        order = np.argsort(depths, kind="mergesort")
        self._depth = depths[order]
        self._formation = [names[i] for i in order]

        # store colors as a name→color dict (optional)
        self._facecolor = dict(self.facecolor) if self.facecolor else {}

    @staticmethod
    def fields() -> list:
        """Field names for I/O schemas."""
        return ["formation", "depth", "facecolor"]

    @property
    def formations(self) -> List[str]:
        """Ordered formation names (shallow→deep)."""
        return list(self._formation)

    @property
    def depths(self) -> np.ndarray:
        """MD tops aligned to `formations` (copy)."""
        return self._depth.copy()

    def __len__(self) -> int:
        return len(self._formation)

    def __contains__(self, name: str) -> bool:
        return name in self._formation

    def index(self, name: str) -> int:
        """Index of a formation by exact (case-sensitive) name."""
        try:
            return self._formation.index(name)
        except ValueError as e:
            raise ValueError(f"Formation '{name}' not found.") from e

    def __getitem__(self, name: str) -> float:
        """Alias for `get_top(name)`."""
        return self.get_top(name)

    def get_top(self, name: str) -> float:
        """Return the MD top of `name`."""
        return float(self._depth[self.index(name)])

    def get_limit(self, name: str) -> Tuple[float, Optional[float]]:
        """
        Return (top, bottom) MD for `name`.
        Bottom is the next deeper top; if none exists, returns None.
        """
        i = self.index(name)
        top = float(self._depth[i])
        bottom = float(self._depth[i + 1]) if i < len(self._depth) - 1 else None
        return top, bottom

    def intervals(self) -> List[Tuple[str, float, Optional[float]]]:
        """
        Return all formation intervals as (formation, top, bottom), shallow→deep.
        The bottom of the deepest formation is None.
        """
        out: List[Tuple[str, float, Optional[float]]] = []
        n = len(self._formation)
        for i, name in enumerate(self._formation):
            top = float(self._depth[i])
            bottom = float(self._depth[i + 1]) if i < n - 1 else None
            out.append((name, top, bottom))
        return out

    def find_at_md(self, md: float) -> Optional[str]:
        """
        Return the formation that contains measured depth `md`, or None if
        the depth is shallower than the first top or deeper than the last bottom.

        Interval convention: [top, bottom) — inclusive at top, exclusive at bottom.
        """
        md = float(md)
        ints = self.intervals()
        for name, top, bottom in ints:
            if bottom is None:
                if md >= top:
                    return name
            else:
                if top <= md < bottom:
                    return name
        return None

    def get_facecolor(self, name: str) -> Optional[str]:
        """Return the facecolor for `name`, if set; otherwise None."""
        return self._facecolor.get(name)

    def merge_facecolors(self, mapping: Dict[str, str]) -> None:
        """
        Merge/override facecolors with `mapping` (formation → color).
        Unknown formation keys are ignored.
        """
        for k, v in mapping.items():
            if k in self._formation:
                self._facecolor[k] = v

    def facecolor_map(self) -> Dict[str, Optional[str]]:
        """Return a dict of formation → facecolor (None if unset)."""
        return {name: self._facecolor.get(name) for name in self._formation}

    # ---------- mutation ----------
    def add(self, name: str, depth: float, facecolor: Optional[str] = None) -> None:
        """
        Add a new formation top (name must not already exist). Keeps ordering by depth.
        Raises if name exists or depth is invalid.
        """
        if name in self._formation:
            raise ValueError(f"Formation '{name}' already exists.")
        depth = float(depth)
        if not np.isfinite(depth) or depth < 0:
            raise ValueError("Depth must be a finite number >= 0.")

        # insert in order
        insert_at = int(np.searchsorted(self._depth, depth, side="left"))
        self._formation.insert(insert_at, name)
        self._depth = np.insert(self._depth, insert_at, depth)
        if facecolor is not None:
            self._facecolor[name] = facecolor

    def remove(self, name: str) -> None:
        """Remove a formation top by name (no-op if absent)."""
        if name not in self._formation:
            return
        i = self.index(name)
        self._formation.pop(i)
        self._depth = np.delete(self._depth, i, axis=0)
        self._facecolor.pop(name, None)

    def rename(self, old: str, new: str) -> None:
        """
        Rename a formation (case-sensitive). Fails if `new` already exists.
        Depth and facecolor are preserved.
        """
        if new in self._formation:
            raise ValueError(f"Formation '{new}' already exists.")
        i = self.index(old)
        self._formation[i] = new
        if old in self._facecolor:
            self._facecolor[new] = self._facecolor.pop(old)

    # ---------- convenience ----------
    @classmethod
    def from_mapping(cls, mapping: Dict[str, float], facecolor: Optional[Dict[str, str]] = None):
        """
        Build from a simple name→MD mapping, e.g., {'A': 1234.0, 'B': 1560.5}.
        """
        return cls(list(mapping.keys()), list(mapping.values()), facecolor)

    def to_mapping(self) -> Dict[str, float]:
        """Export as a name→MD dict (ordered shallow→deep)."""
        return {name: float(md) for name, md in zip(self._formation, self._depth)}

if __name__ == "__main__":

    zones = Tops(
        formation=["Shale", "Sandstone", "Limestone"],
        depth=[1000, 1500, 2000],   # MD in meters
        facecolor={"Shale": "gray", "Sandstone": "gold"}  # Limestone has no color yet
    )

    print(zones.depth)
    print(zones.formation)

    print(Tops.fields())

    # print(zones.index("B"))
    # print(zones.limit("B"))