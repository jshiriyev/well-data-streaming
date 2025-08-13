from .general import Name, Slot, Status, Summary
from .location import Survey, Tops
# from ._drilling import Drilling, 
from .completion import Perfs, Layout

class Well():
    """It is a well dictionary with all sub classes."""

    STATUS_OF_WELL = []

    def __init__(self,
        name        : str,
        status      : str = "active",
        slot        : dict = None,
        drill       : dict = None,
        survey      : dict = None,
        tops        : dict = None,
        ):

        self.name   = name
        self.status = status
        self.slot   = slot
        
        self.survey = survey
        self.tops   = tops
        # self.drill  = drill
        self.layout = None
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
    def tops(self):
        return self._tops

    @tops.setter
    def tops(self,value:dict):
        self._tops = Tops(**(value or {}))

    @property
    def perfs(self):
        return self._perfs

    @perfs.setter
    def perfs(self,value):
        self._perfs = Perfs()