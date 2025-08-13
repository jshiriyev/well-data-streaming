from dataclasses import dataclass, fields

import numpy as np

@dataclass
class Survey:
    """It is a well survey (direction or trajectory)."""

    MD      : np.ndarray = None
    TVD     : np.ndarray = None
    DX      : np.ndarray = None
    DY      : np.ndarray = None
    INC     : np.ndarray = None
    AZI     : np.ndarray = None

    def get(self,MD=None,TVD=None):

        if MD is None and TVD is None:
            raise ValueError("Either MD or TVD must be provided.")
        
        if MD is None:
        	return self.tvd2md(TVD)

        if TVD is None:
        	return self.md2tvd(MD)

    @staticmethod
    def fields() -> list:
        return [field.name for field in fields(Survey)]

    def md2tvd(self,values:float|np.ndarray):
        return np.interp(values,self.MD,self.TVD)
        
    def tvd2md(self,values:float|np.ndarray):
        return np.interp(values,self.TVD,self.MD)

    @staticmethod
    def inc2tvd(INC:np.ndarray,MD:np.ndarray):

        TVD = MD.copy()

        offset = MD[1:]-MD[:-1]
        radian = INC[1:]/180*np.pi

        TVD[1:] = np.cumsum(offset*np.cos(radian))

        return TVD

    @staticmethod
    def off2tvd(MD:np.ndarray,DX:np.ndarray,DY:np.ndarray):

        TVD = MD.copy()

        offMD = MD[1:]-MD[:-1]
        offDX = DX[1:]-DX[:-1]
        offDY = DY[1:]-DY[:-1]
                         
        TVD[1:] = np.sqrt(offMD**2-offDX**2-offDY**2)

        return np.cumsum(TVD)