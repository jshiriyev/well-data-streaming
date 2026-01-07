from dataclasses import dataclass

from typing import Optional, Dict, Any

import re

_DEFAULT_INDEX_RE = re.compile(r"(?P<prefix>.*?)(?P<index>\d+)(?P<suffix>.*)$")

@dataclass(frozen=True, slots=True)
class Name:
    """Well name with helpers for formatting, parsing, normalization, and validation."""

    name :  str

    # ---------- Representation ----------
    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Name(name='{self.name}')"

    # ---------- Normalization ----------
    @staticmethod
    def _canonicalize(name:str) -> str:
        # trim, collapse whitespace, uppercase for consistent matching
        return re.sub(r"\s+", " ", name.strip()).upper()

    def canonical(self,sep:str="-") -> str:
        """Uppercased, collapsed whitespace version of the name."""
        return self._canonicalize(self.name).replace(" ", sep)

    def slug(self,sep:str="-") -> str:
        """Filesystem/URL-friendly slug."""
        s = self.canonical(sep=sep)
        s = re.sub(rf"[^A-Z0-9{re.escape(sep)}]+", "", s)
        s = re.sub(rf"{re.escape(sep)}+", sep, s).strip(sep)
        return s

    # ---------- Parsing ----------
    def split(self, regex: re.Pattern[str] = _DEFAULT_INDEX_RE
              ) -> tuple[str, Optional[int], str]:
        """
        Split into (prefix, index, suffix). If no match, returns (name, None, "").
        """
        m = regex.match(self.name)
        if not m:
            return (self.name, None, "")
        idx = int(m.group("index")) if m.group("index") is not None else None
        return (m.group("prefix"), idx, m.group("suffix"))

    def extract(self, regex: str | re.Pattern[str], group: int = 0,
                default: Optional[str] = None, flags: int = 0) -> Optional[str]:
        """
        Return the first regex group found in the name (or default).
        Example: name.extract(r'(\\d+)', group=1) -> '12'
        """
        pat = re.compile(regex, flags) if isinstance(regex, str) else regex
        m = pat.search(self.name)
        return (m.group(group) if m else default)

    @staticmethod
    def parse(name:str,regex:str|None=None) -> str:
        """Returns a searched part of the name. If no match is found, returns the original name.

        Parameters:
        ----------
        name (str): The name to parse.
        regex (raw str): A custom regular expression for extraction. Defaults to extracting digits.

        Returns:
        -------
        str: The extracted content, or the original string if no match is found.

        """
        regex = r'\d+' if regex is None else regex
        # previous version of the code : r"'(.*?)'"
        # previous chatgpt suggestion : r"'([^']*)'"

        match = re.search(regex,name)
        
        return match.group() if match else name

    # ---------- Formatting / generation ----------
    @staticmethod
    def apply(index:int,template:str|None=None) -> str:
        """Generates a well name by formatting a given index into a string template.

        Parameters:
        ----------
        index    : The well index (number)
        template : A string template containing a placeholder (e.g., "Well-{}").
        
        Returns:
        -------
        str: The formatted well name.

        Raises:
        ------
        ValueError: If the template does not contain a valid placeholder.

        """
        template = "Well-{}" if template is None else template

        try:
            return template.format(index) if "{}" in template else template.format(index=index)
        except Exception as e:
            raise ValueError(
                f"Invalid template '{template}' for index '{index}'. Error: {e}"
            ) from e

    @classmethod
    def from_components(cls, prefix: str = "Well-", index: Optional[int] = None,
                        suffix: str = "", pad: Optional[int] = None) -> "Name":
        """Build a name from pieces with optional zero-padding for the index."""
        if index is None:
            return cls(prefix + suffix)
        idx = f"{index:0{pad}d}" if pad else str(index)
        return cls(prefix + idx + suffix)

    def with_index_padding(self,width:int,regex:re.Pattern[str]= _DEFAULT_INDEX_RE) -> "Name":
        """Return a new Name with the numeric part zero-padded to `width`."""
        m = regex.match(self.name)
        if not m:
            return self
        new = f"{m.group('prefix')}{int(m.group('index')):0{width}d}{m.group('suffix')}"
        return Name(new)

    # ---------- Validation ----------
    def matches(self, pattern: str | re.Pattern[str], flags: int = 0) -> bool:
        pat = re.compile(pattern, flags) if isinstance(pattern, str) else pattern
        return bool(pat.search(self.name))

    # ---------- (De)serialization ----------
    def to_dict(self) -> Dict[str, Any]:
        prefix, idx, suffix = self.split()
        return {"name": self.name, "prefix": prefix, "index": idx, "suffix": suffix}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Name":
        if "name" in d and d["name"]:
            return cls(d["name"])
        return cls.from_components(d.get("prefix", ""),
                                   d.get("index", None),
                                   d.get("suffix", ""),
                                   pad=None)

if __name__ == "__main__":

    # w = Name("Gun-38")

    # print(w)
    # print(w.canonical(sep='-'))
    # print(w.split())
    # print(w.extract(r'\d+'))
    # print(Name.apply(42))
    # print(Name.from_components("GUN-", 42))
    # print(w.with_index_padding(3))
    # print(w.matches(r'^GUN-\d+$'))
    # print(w.to_dict())
    # print(Name.from_dict({'prefix': 'GUN-', 'index':38}))
    print(Name.apply(42, template="Well-{index:03d}"))