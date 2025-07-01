from dataclasses import dataclass

@dataclass
class Name:

    name : str

    @staticmethod
    def apply(index:int,template:str=None) -> str:
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
            return template.format(index)
        except Error as e:
            raise ValueError(f"Invalid template '{template}' for index '{index}'. Error: {e}")

    @staticmethod
    def parse(name:str,regex:str=None) -> str:
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

@dataclass
class Slot:
    """It is a slot dictionary for a well."""
    index   : int = None

    plt     : str = None

    xhead   : float = 0.0
    yhead   : float = 0.0
    datum   : float = 0.0

@dataclass(frozen=True)
class Status:

  prospect      : "white"

  construction  : "gray"
  drilling      : "purple"
  completion    : "yellow"
  installation  : "pink"

  delay         : "white"
  mobilization  : "black"

  optimization  : "lightgreen"
  remediation   : "lightgreen"
  recompletion  : "lighgreen"
  fishing       : "red"
  sidetrack     : "darkblue"

  production    : "darkgreen"
  injection     : "blue"

  @staticmethod
  def fields() -> list:
    return [field.name for field in fields(Status)]

@dataclass
class Summary:
    """"""
    text