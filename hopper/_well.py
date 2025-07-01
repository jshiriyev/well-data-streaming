from dataclasses import dataclass

import re

import numpy

from .welly._survey import Survey
from .welly._drilling import Drilling
from .welly._zones import Zones
from .welly._layout import Layout
from .welly._perfs import Perfs

class Well():
    """It is a well dictionary with all sub classes."""

    STATUS_OF_WELL = []

    def __init__(self,
        name        : str,
        status      : str = "active",
        slot        : dict = None,
        drill       : dict = None,
        survey      : dict = None,
        zones       : dict = None,
        ):

        self.name   = name
        self.status = status
        self.slot   = slot
        
        self.drill  = drill
        self.layout = None
        self.survey = survey
        self.zones  = zones
        self.perfs  = None

        self.las    = []

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self,value:str):
        self._name = Name(value)

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self,value:str):
        self._status = value

    @property
    def slot(self):
        return self._slot

    @slot.setter
    def slot(self,value:dict):
        self._slot = Slot(**(value or {}))

    @property
    def drill(self):
        return self._drill

    @drill.setter
    def drill(self,value:dict):
        self._drill = Drilling(**(value or {}))

    @property
    def layout(self):
        return self._layout

    @layout.setter
    def layout(self,value):
        self._layout = Layout()

    @property
    def survey(self):
        return self._survey

    @survey.setter
    def survey(self,value:dict):
        self._survey = Survey(**(value or {}))

    @property
    def zones(self):
        return self._zones

    @zones.setter
    def zones(self,value:dict):
        self._zones = Zones(**(value or {}))

    @property
    def perfs(self):
        return self._perfs

    @perfs.setter
    def perfs(self,value):
        self._perfs = Perfs()