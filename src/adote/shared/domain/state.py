"""The 27 federative units. A closed set, so a value object, not a table."""

from enum import StrEnum


class State(StrEnum):
    AC = "AC"
    AL = "AL"
    AP = "AP"
    AM = "AM"
    BA = "BA"
    CE = "CE"
    DF = "DF"
    ES = "ES"
    GO = "GO"
    MA = "MA"
    MT = "MT"
    MS = "MS"
    MG = "MG"
    PA = "PA"
    PB = "PB"
    PR = "PR"
    PE = "PE"
    PI = "PI"
    RJ = "RJ"
    RN = "RN"
    RS = "RS"
    RO = "RO"
    RR = "RR"
    SC = "SC"
    SP = "SP"
    SE = "SE"
    TO = "TO"

    @property
    def full_name(self) -> str:
        return _NAMES[self]


_NAMES: dict[State, str] = {
    State.AC: "Acre",
    State.AL: "Alagoas",
    State.AP: "Amapá",
    State.AM: "Amazonas",
    State.BA: "Bahia",
    State.CE: "Ceará",
    State.DF: "Distrito Federal",
    State.ES: "Espírito Santo",
    State.GO: "Goiás",
    State.MA: "Maranhão",
    State.MT: "Mato Grosso",
    State.MS: "Mato Grosso do Sul",
    State.MG: "Minas Gerais",
    State.PA: "Pará",
    State.PB: "Paraíba",
    State.PR: "Paraná",
    State.PE: "Pernambuco",
    State.PI: "Piauí",
    State.RJ: "Rio de Janeiro",
    State.RN: "Rio Grande do Norte",
    State.RS: "Rio Grande do Sul",
    State.RO: "Rondônia",
    State.RR: "Roraima",
    State.SC: "Santa Catarina",
    State.SP: "São Paulo",
    State.SE: "Sergipe",
    State.TO: "Tocantins",
}
