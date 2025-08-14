from dataclasses import dataclass, field, fields

import numpy as np

_EPS = 1e-12

@dataclass(slots=True)
class Survey:
    """
    Wellbore survey container and utilities.

    This class stores and computes well trajectory quantities and exposes
    NumPy-only APIs suited for high-throughput pipelines and Streamlit apps.

    Coordinates & angles
    --------------------
    - MD: Measured Depth, strictly increasing.
    - TVD: True Vertical Depth, positive downward.
    - DX: Easting offset (local X).
    - DY: Northing offset (local Y).
    - INC: Inclination in degrees.
    - AZI: Azimuth in degrees (0°=North, 90°=East).  (Grid/True/Magnetic handling
           is out of scope here; provide corrected azimuths.)

    Initialization options
    ----------------------
    You may initialize with *any* combination that respects geometry, e.g.:
      - MD + TVD  (vertical profile only)
      - MD + INC + AZI (+ optional tie-in xhead,yhead,datum)  -> compute TVD, DX, DY via minimum curvature
      - MD + TVD + DX + DY  (fully specified)

    Validation
    ----------
    - MD must be strictly increasing (no duplicates).
    - All provided arrays must have the same length.
    - Interpolation outside the data range **raises**.
    - `off2tvd` clips invalid intervals to zero (sqrt argument < 0).

    Notes
    -----
    - All methods return NumPy arrays (or scalars); no pandas dependencies.
    - Plotting is intentionally omitted; use the view helpers to feed your UI.

    """
    # Trajectory arrays (all or some may be None depending on init path)
    MD:  np.ndarray | None = None
    TVD: np.ndarray | None = None
    DX:  np.ndarray | None = None   # East
    DY:  np.ndarray | None = None   # North
    INC: np.ndarray | None = None   # deg
    AZI: np.ndarray | None = None   # deg

    # Optional tie-in (used when computing from INC/AZI)
    xhead: float = 0.0
    yhead: float = 0.0
    datum: float = 0.0

    # --- lifecycle ---------------------------------------------------------
    def __post_init__(self) -> None:
        self._validate_shapes_and_monotonicity()

    @staticmethod
    def fields() -> list[str]:
        """Return dataclass field names (for schema/serialization)."""
        return [f.name for f in fields(Survey)]

    # --- basic interpolation helpers --------------------------------------
    def md2tvd(self, values: float | np.ndarray) -> np.ndarray:
        self._ensure_available(self.MD, "MD")
        self._ensure_available(self.TVD, "TVD")
        vals = np.asanyarray(values)
        self._check_in_range(vals, self.MD, "MD")
        return np.interp(vals,self.MD,self.TVD)
        
    def tvd2md(self, values: float | np.ndarray) -> np.ndarray:
        self._ensure_available(self.MD, "MD")
        self._ensure_available(self.TVD, "TVD")
        if not np.all(np.diff(self.TVD) > 0):
            raise ValueError("TVD must be strictly increasing for TVD→MD interpolation.")
        vals = np.asanyarray(values)
        self._check_in_range(vals, self.TVD, "TVD")
        return np.interp(vals,self.TVD,self.MD)

    @staticmethod
    def inc2tvd(INC:np.ndarray,MD:np.ndarray):
        """
        Fast tangential approximation: TVD[i] = TVD[i-1] + dMD * cos(INC[i]).
        Angles are degrees. Returns TVD with TVD[0]=0.
        """
        INC = np.asanyarray(INC); MD = np.asanyarray(MD)

        Survey._require_strictly_increasing(MD, "MD")

        TVD = MD.copy()

        offset = np.diff(MD)
        radian = np.deg2rad(INC[1:])

        TVD[1:] = np.cumsum(offset*np.cos(radian))

        return TVD

    @staticmethod
    def off2tvd(MD:np.ndarray,DX:np.ndarray,DY:np.ndarray):
        """
        Recover TVD by Pythagorean segments:
            dTVD = sqrt(max(0, dMD^2 - dX^2 - dY^2))
        Returns cumulative TVD with TVD[0]=0.
        """
        MD = np.asanyarray(MD); DX = np.asanyarray(DX); DY = np.asanyarray(DY)
        Survey._require_strictly_increasing(MD, "MD")

        TVD = MD.copy()

        offMD = np.diff(MD); offDX = np.diff(DX); offDY = np.diff(DY)
                         
        TVD[1:] = np.sqrt(offMD**2-offDX**2-offDY**2)

        return np.cumsum(TVD)

    @staticmethod
    def minimum_curvature(
        MD: np.ndarray,
        INC_deg: np.ndarray,
        AZI_deg: np.ndarray,
        xhead: float = 0.0,
        yhead: float = 0.0,
        datum: float = 0.0,
        small_angle: float = 1e-8,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute (DX, DY, TVD) from MD/INC/AZI using the minimum curvature method.

        Parameters
        ----------
        MD, INC_deg, AZI_deg : np.ndarray
            Station arrays (same length). MD must be strictly increasing.
        xhead, yhead, datum : float
            Tie-in coordinates (Easting, Northing, TVD) for station 0.
        small_angle : float
            Threshold (radians) below which RF≈1 is assumed.

        Returns
        -------
        DX, DY, TVD : np.ndarray
            Easting, Northing, and true vertical depth (positive down).

        Notes
        -----
        - Angles in degrees are converted to radians internally.
        - Azimuth reference: 0°=North, 90°=East.
        """
        MD = np.asanyarray(MD, dtype=float)
        INC = np.deg2rad(np.asanyarray(INC_deg, dtype=float))
        AZI = np.deg2rad(np.asanyarray(AZI_deg, dtype=float))
        n = MD.size
        Survey._require_strictly_increasing(MD, "MD")
        if not (INC.size == AZI.size == n):
            raise ValueError("MD, INC, AZI must have the same length.")

        DX = np.empty(n, dtype=float); DY = np.empty(n, dtype=float); TVD = np.empty(n, dtype=float)
        DX[0] = xhead; DY[0] = yhead; TVD[0] = datum

        for i in range(1, n):
            dmd = MD[i] - MD[i-1]
            i1, a1 = INC[i-1], AZI[i-1]
            i2, a2 = INC[i],   AZI[i]

            cos_dl = np.clip(np.cos(i1)*np.cos(i2) + np.sin(i1)*np.sin(i2)*np.cos(a2 - a1), -1.0, 1.0)
            dl = np.arccos(cos_dl)
            rf = 1.0 if dl < small_angle else (2.0/ dl) * np.tan(dl/2.0)

            dN = 0.5 * dmd * rf * (np.sin(i1)*np.cos(a1) + np.sin(i2)*np.cos(a2))  # North
            dE = 0.5 * dmd * rf * (np.sin(i1)*np.sin(a1) + np.sin(i2)*np.sin(a2))  # East
            dV = 0.5 * dmd * rf * (np.cos(i1) + np.cos(i2))                        # Down

            DY[i]   = DY[i-1]  + dN
            DX[i]   = DX[i-1]  + dE
            TVD[i]  = TVD[i-1] + dV

        return DX, DY, TVD

    @staticmethod
    def solve_straight_to_target(
        x_target: float, y_target: float, tvd_target: float,
        x0: float, y0: float, tvd0: float,
        md_start: float, md_end: float,
    ) -> tuple[float, float]:
        """
        Compute constant INC/AZI that would connect (x0,y0,tvd0) to target over
        a *single straight segment* between MDs [md_start, md_end].

        This is a practical heuristic for planning; it is **not** a full trajectory
        optimizer. For multi-station paths, chain several segments or use a
        separate planner.

        Returns
        -------
        INC_deg, AZI_deg : float, float
        """
        dmd = md_end - md_start
        if dmd <= 0:
            raise ValueError("md_end must be greater than md_start.")

        dE = float(x_target - x0)
        dN = float(y_target - y0)
        dV = float(tvd_target - tvd0)
        dh = np.hypot(dE, dN)
        dist = np.sqrt(dh*dh + dV*dV)

        # Straight-line along MD: require dist ~= dmd; if not, assume stretch/compression.
        if dist < _EPS:
            return 0.0, 0.0

        INC = np.degrees(np.arctan2(dh, dV if dV != 0 else _EPS))   # 0° down, 90° horizontal
        AZI = (np.degrees(np.arctan2(dE, dN)) + 360.0) % 360.0      # 0°=North, 90°=East
        return float(INC), float(AZI)

    # --- UI helpers (arrays only) ------------------------------------------
    def view_plan(self) -> tuple[np.ndarray, np.ndarray]:
        """Return (X=DX, Y=DY) for plan view. Requires DX/DY."""
        self._ensure_available(self.DX, "DX")
        self._ensure_available(self.DY, "DY")
        return self.DX, self.DY

    def view_section(self) -> tuple[np.ndarray, np.ndarray]:
        """Return (MD, TVD) for side/section view. Requires MD/TVD."""
        self._ensure_available(self.MD, "MD")
        self._ensure_available(self.TVD, "TVD")
        return self.MD, self.TVD

    def downsample(self, max_points: int) -> tuple[np.ndarray, ...]:
        """
        Downsample all available arrays to at most `max_points`, preserving endpoints.
        Returns a tuple of arrays in this order (skipping Nones):
        (MD, TVD, DX, DY, INC, AZI)
        """
        if max_points < 2:
            raise ValueError("max_points must be >= 2.")
        self._ensure_available(self.MD, "MD")
        n = self.MD.size
        if n <= max_points:
            return tuple([a for a in (self.MD, self.TVD, self.DX, self.DY, self.INC, self.AZI) if a is not None])

        idx = np.unique(np.rint(np.linspace(0, n-1, max_points)).astype(int))
        return tuple([a[idx] for a in (self.MD, self.TVD, self.DX, self.DY, self.INC, self.AZI) if a is not None])

    # --- convenience constructors ------------------------------------------
    @classmethod
    def from_md_tvd(cls, MD: np.ndarray, TVD: np.ndarray) -> "Survey":
        """Construct from MD/TVD arrays."""
        s = cls(MD=np.asarray(MD, float), TVD=np.asarray(TVD, float))
        s._validate_shapes_and_monotonicity()
        return s

    @classmethod
    def from_md_inc_azi(
        cls,
        MD: np.ndarray, INC_deg: np.ndarray, AZI_deg: np.ndarray,
        xhead: float = 0.0, yhead: float = 0.0, datum: float = 0.0
    ) -> "Survey":
        """Construct by computing DX/DY/TVD via minimum curvature from MD/INC/AZI."""
        MD = np.asarray(MD, float)
        INC_deg = np.asarray(INC_deg, float)
        AZI_deg = np.asarray(AZI_deg, float)
        DX, DY, TVD = cls.minimum_curvature(MD, INC_deg, AZI_deg, xhead=xhead, yhead=yhead, datum=datum)
        s = cls(MD=MD, INC=INC_deg, AZI=AZI_deg, DX=DX, DY=DY, TVD=TVD, xhead=xhead, yhead=yhead, datum=datum)
        s._validate_shapes_and_monotonicity()
        return s

    @classmethod
    def from_md_xyz(cls, MD: np.ndarray, DX: np.ndarray, DY: np.ndarray, TVD: np.ndarray) -> "Survey":
        """Construct directly from MD and XYZ arrays."""
        s = cls(MD=np.asarray(MD, float),
                DX=np.asarray(DX, float),
                DY=np.asarray(DY, float),
                TVD=np.asarray(TVD, float))
        s._validate_shapes_and_monotonicity()
        return s

    # --- internals ---------------------------------------------------------
    def _validate_shapes_and_monotonicity(self) -> None:
        # shape alignment (ignore None)
        arrays = [a for a in (self.MD, self.TVD, self.DX, self.DY, self.INC, self.AZI) if a is not None]
        if arrays:
            n0 = arrays[0].size
            for a in arrays[1:]:
                if a.size != n0:
                    raise ValueError("All provided arrays must have the same length.")
        # MD monotonicity
        if self.MD is not None:
            self._require_strictly_increasing(self.MD, "MD")

    @staticmethod
    def _require_strictly_increasing(arr: np.ndarray, name: str) -> None:
        if arr.ndim != 1:
            raise ValueError(f"{name} must be 1-D.")
        if not np.all(np.diff(arr) > 0):
            raise ValueError(f"{name} must be strictly increasing.")

    @staticmethod
    def _ensure_available(arr: np.ndarray | None, name: str) -> None:
        if arr is None:
            raise ValueError(f"{name} is not available in this Survey instance.")

    @staticmethod
    def _check_in_range(query: np.ndarray, base: np.ndarray, base_name: str) -> None:
        qmin = np.min(query); qmax = np.max(query)
        if qmin < base[0] or qmax > base[-1]:
            raise ValueError(
                f"Query values [{qmin:.6g}, {qmax:.6g}] are outside the {base_name} range "
                f"[{base[0]:.6g}, {base[-1]:.6g}]."
            )

if __name__ == "__main__":

    md  = np.linspace(0.0, 100.0, 101)
    tvd = md.copy()
    s = Survey.from_md_tvd(md, tvd)

    print(s)

    downs = s.downsample(max_points=5)
    # downs returns tuple skipping None -> here (MD, TVD)

    print(downs)

    md_d, tvd_d = downs