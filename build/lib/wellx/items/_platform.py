from dataclasses import dataclass, field, fields

import datetime
import json

from typing import Any, Dict, Optional, Self

@dataclass(slots=True, frozen=False)
class Platform:

	name : Optional[str] = field(default="P", metadata={
		"head" : "Platform Identifier",
		"descr" : "Platfrom identifier"
		})

	length : Optional[float] = field(default=None, metadata={
		"head" : "",
		"unit" : "m",
		"descr" : ""
		}) 
	width : Optional[float] = field(default=None, metadata={
		"head" : "",
		"unit" : "m",
		"descr" : ""
		})

	year : Optional[int] = field(default=datetime.date.today(), metadata={
		"head" : "Commencement Year",
		"descr" : "Commencement year of the platform"
		})

	lat : Optional[float] = field(default=None, metadata={
		"head" : "",
		"descr" : ""
		})
	lon : Optional[float] = field(default=None, metadata={
		"head" : "",
		"descr" : ""
		})

	north : Optional[float] = field(default=None, metadata={
		"head" : "",
		"descr" : ""
		})

	sea_depth : Optional[float] = field(default=0, metadata={
		"head" : "",
		"descr" : ""
		})

	comment : Optional[str] = field(default="", metadata={
		"head" : "",
		"descr" : ""
		})

	_unit_override: Dict[str, str] = field(default_factory=dict, init=False, repr=False)

	def get_unit(self, key: str) -> Optional[str]:
		"""Return the unit for a field, checking overrides first."""
		if key in self._unit_override:
			return self._unit_override[key]
		for f in fields(self):				 # dataclasses.fields -> tuple[Field, ...]
			if f.name == key:
				return f.metadata.get("unit")  # metadata is a Mapping
		raise AttributeError(f"No field named {key!r}")

	def set_unit(self, **kwargs) -> None:
		"""Override the unit for a field at runtime (does not change class metadata)."""
		for key, unit in kwargs.items():
			if key not in {f.name for f in fields(self)}:
				raise AttributeError(f"No field named {key!r}")
			self._unit_override[key] = unit

	def to_dict(self,metaonly:bool=False) -> Dict[str, Any]:
		"""Convert dataclass to dictionary with metadata included."""
		data = {}
		for f in fields(self):
			if f.name.startswith("_"):   # skip private fields
				continue
			
			value = getattr(self, f.name)

			if isinstance(value, (datetime.date, datetime.datetime)):
				value = value.isoformat()   # <-- convert date to string

			meta = dict(f.metadata)

			if f.name in self._unit_override:
				meta["unit"] = self._unit_override[f.name]

			data[f.name] = {"metadata": meta} if metaonly else {"value": value,"metadata": meta}

		return data

	def to_json(self,filename:str,metaonly:bool=False) -> None:
		"""Dump the content to a JSON file."""
		with open(filename, "w", encoding="utf-8") as f:
			json.dump(self.to_dict(metaonly=metaonly), f, indent=4)

	@classmethod
	def from_dict(cls,data:Dict[str,Any],metaonly:bool=False) -> Self:
		"""Recreate an instance from a dict produced by to_dict().
		Also re-applies unit overrides found in metadata['unit'] when they differ from defaults.
		"""
		# prepare values
		kw: Dict[str, Any] = {}

		if not metaonly:

			for f in fields(cls):
				if f.name.startswith("_"):
					continue
				if f.name not in data:
					continue
				val = data[f.name]["value"]
				# restore dates
				if f.type is datetime.date and isinstance(val, str):
					val = datetime.date.fromisoformat(val)
				elif f.type is datetime.datetime and isinstance(val, str):
					val = datetime.datetime.fromisoformat(val)
				kw[f.name] = val

		obj = cls(**kw)

		# re-apply unit overrides if JSON’s unit differs from class default
		for f in fields(cls):
			if f.name.startswith("_"):
				continue
			if f.name not in data:
				continue
			json_unit = (data[f.name].get("metadata") or {}).get("unit")
			default_unit = f.metadata.get("unit")
			if json_unit and json_unit != default_unit:
				obj._unit_override[f.name] = json_unit

		return obj

	@classmethod
	def from_json(cls,filename:str,metaonly:bool=False) -> Self:
		with open(filename, "r", encoding="utf-8") as f:
			data = json.load(f)
		
		return cls.from_dict(data,metaonly=metaonly)

	@staticmethod
	def fields() -> list[str]:
		"""List of dataclass field names (stable order)."""
		return [f.name for f in fields(Rate) if f.init]
