from dataclasses import dataclass

@dataclass(frozen=True)
class Status:
    """It is a well status dictionary for a well."""
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