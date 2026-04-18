"""F1 Grand Prix names — map circuit/country to official English GP name."""

CIRCUIT_TO_GP = {
    "Melbourne":          "Australian Grand Prix",
    "Shanghai":           "Chinese Grand Prix",
    "Suzuka":             "Japanese Grand Prix",
    "Sakhir":             "Bahrain Grand Prix",
    "Jeddah":             "Saudi Arabian Grand Prix",
    "Miami":              "Miami Grand Prix",
    "Imola":              "Emilia Romagna Grand Prix",
    "Monaco":             "Monaco Grand Prix",
    "Barcelona":          "Spanish Grand Prix",
    "Montréal":           "Canadian Grand Prix",
    "Montreal":           "Canadian Grand Prix",
    "Spielberg":          "Austrian Grand Prix",
    "Silverstone":        "British Grand Prix",
    "Spa-Francorchamps":  "Belgian Grand Prix",
    "Spa":                "Belgian Grand Prix",
    "Budapest":           "Hungarian Grand Prix",
    "Hungaroring":        "Hungarian Grand Prix",
    "Zandvoort":          "Dutch Grand Prix",
    "Monza":              "Italian Grand Prix",
    "Baku":               "Azerbaijan Grand Prix",
    "Marina Bay":         "Singapore Grand Prix",
    "Singapore":          "Singapore Grand Prix",
    "Austin":             "United States Grand Prix",
    "Mexico City":        "Mexico City Grand Prix",
    "São Paulo":          "São Paulo Grand Prix",
    "Sao Paulo":          "São Paulo Grand Prix",
    "Interlagos":         "São Paulo Grand Prix",
    "Las Vegas":          "Las Vegas Grand Prix",
    "Lusail":             "Qatar Grand Prix",
    "Losail":             "Qatar Grand Prix",
    "Yas Marina":         "Abu Dhabi Grand Prix",
    "Yas Island":         "Abu Dhabi Grand Prix",
    "Portimão":           "Portuguese Grand Prix",
    "Portimao":           "Portuguese Grand Prix",
    "Istanbul":           "Turkish Grand Prix",
    "Nürburgring":        "Eifel Grand Prix",
    "Mugello":            "Tuscan Grand Prix",
}

COUNTRY_TO_GP = {
    "Australia":             "Australian Grand Prix",
    "China":                 "Chinese Grand Prix",
    "Japan":                 "Japanese Grand Prix",
    "Bahrain":               "Bahrain Grand Prix",
    "Saudi Arabia":          "Saudi Arabian Grand Prix",
    "United States":         "United States Grand Prix",
    "USA":                   "United States Grand Prix",
    "Italy":                 "Italian Grand Prix",
    "Monaco":                "Monaco Grand Prix",
    "Spain":                 "Spanish Grand Prix",
    "Canada":                "Canadian Grand Prix",
    "Austria":               "Austrian Grand Prix",
    "United Kingdom":        "British Grand Prix",
    "UK":                    "British Grand Prix",
    "Belgium":               "Belgian Grand Prix",
    "Hungary":               "Hungarian Grand Prix",
    "Netherlands":           "Dutch Grand Prix",
    "Azerbaijan":            "Azerbaijan Grand Prix",
    "Singapore":             "Singapore Grand Prix",
    "Mexico":                "Mexico City Grand Prix",
    "Brazil":                "São Paulo Grand Prix",
    "Qatar":                 "Qatar Grand Prix",
    "UAE":                   "Abu Dhabi Grand Prix",
    "United Arab Emirates":  "Abu Dhabi Grand Prix",
    "Portugal":              "Portuguese Grand Prix",
    "Turkey":                "Turkish Grand Prix",
}

# Circuit type classification
CIRCUIT_TYPE = {
    "Melbourne":          "street",
    "Shanghai":           "technical",
    "Suzuka":             "technical",
    "Sakhir":             "high_speed",
    "Jeddah":             "high_speed",
    "Miami":              "street",
    "Imola":              "technical",
    "Monaco":             "street",
    "Barcelona":          "technical",
    "Montréal":           "street",
    "Montreal":           "street",
    "Spielberg":          "high_speed",
    "Silverstone":        "high_speed",
    "Spa-Francorchamps":  "high_speed",
    "Budapest":           "technical",
    "Hungaroring":        "technical",
    "Zandvoort":          "technical",
    "Monza":              "high_speed",
    "Baku":               "street",
    "Marina Bay":         "street",
    "Singapore":          "street",
    "Austin":             "technical",
    "Mexico City":        "high_speed",
    "São Paulo":          "technical",
    "Sao Paulo":          "technical",
    "Las Vegas":          "street",
    "Lusail":             "high_speed",
    "Yas Marina":         "technical",
}

CIRCUIT_TYPE_LABEL = {
    "high_speed": "High-Speed Circuit",
    "street":     "Street Circuit",
    "technical":  "Technical Circuit",
}


def get_race_name(circuit: str = "", country: str = "", meeting: str = "") -> str:
    """Return the official English Grand Prix name for this circuit/country.

    Falls back to a sensible pattern when we don't have a mapping. The
    upstream meeting_name from OpenF1 is usually already English — accept
    it as-is when present, unless it's the placeholder 'Race'.
    """
    if meeting and meeting not in ("?", "Race", ""):
        return meeting
    name = CIRCUIT_TO_GP.get(circuit, "")
    if not name:
        name = COUNTRY_TO_GP.get(country, "")
    if not name:
        base = country or circuit
        name = f"{base} Grand Prix" if base else "Grand Prix"
    return name


def get_circuit_type(circuit: str) -> str:
    ct = CIRCUIT_TYPE.get(circuit, "technical")
    return CIRCUIT_TYPE_LABEL.get(ct, "Technical Circuit")


def get_circuit_type_raw(circuit: str) -> str:
    return CIRCUIT_TYPE.get(circuit, "technical")
