from dataclasses import dataclass, fields

@dataclass
class Interval:

    above   : float
    below   : float

    def tostr(self,template:str=None):
        """Converts the interval into a string."""
        if template is None:
            template = "{}-{}"

        return template.format(self.below,self.above)
    
    @staticmethod
    def tolist(interval:str,delimiter:str="-",decsep:str=".") -> list:
        """Converts a string interval into a list of floats.

        Parameters:
        ----------
        interval  : The interval string (e.g., "1005-1092").
        delimiter : The delimiter separating depths in the interval. Defaults to "-".
        decsep    : The decimal separator in the depth of the interval. Defaults to ".".
        
        Returns:
        -------
        List: A list containing one or two float values. If only one value
            is provided, the second element will be None.
        """
        try:
            depths = [float(depth.replace(decsep,'.')) for depth in interval.split(delimiter)]
            if len(depths)==1:
                depths.append(None)
            elif len(depths) > 2:
                raise ValueError(f"Unexpected format: '{interval}'. Expected format 'depth_1{delimiter}depth_2'.")
            return depths
        except ValueError as e:
            raise ValueError(f"Invalid interval format: {interval}. Error: {e}")