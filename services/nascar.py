"""NASCAR Cup Series static driver data (no free public API available)."""

MANUFACTURER_COLOR = {
    "Chevrolet": "#cfb634",
    "Ford":      "#003476",
    "Toyota":    "#eb0a1e",
}

# 2025 NASCAR Cup Series driver roster
_DRIVERS_2025 = [
    # Hendrick Motorsports (Chevrolet)
    {"number": "5",  "full_name": "Kyle Larson",         "team": "Hendrick Motorsports",  "manufacturer": "Chevrolet", "wins": 5,  "country": "US"},
    {"number": "9",  "full_name": "Chase Elliott",        "team": "Hendrick Motorsports",  "manufacturer": "Chevrolet", "wins": 4,  "country": "US"},
    {"number": "24", "full_name": "William Byron",        "team": "Hendrick Motorsports",  "manufacturer": "Chevrolet", "wins": 3,  "country": "US"},
    {"number": "48", "full_name": "Alex Bowman",          "team": "Hendrick Motorsports",  "manufacturer": "Chevrolet", "wins": 1,  "country": "US"},
    # Joe Gibbs Racing (Toyota)
    {"number": "11", "full_name": "Denny Hamlin",         "team": "Joe Gibbs Racing",      "manufacturer": "Toyota",    "wins": 6,  "country": "US"},
    {"number": "20", "full_name": "Christopher Bell",     "team": "Joe Gibbs Racing",      "manufacturer": "Toyota",    "wins": 3,  "country": "US"},
    {"number": "54", "full_name": "Ty Gibbs",             "team": "Joe Gibbs Racing",      "manufacturer": "Toyota",    "wins": 1,  "country": "US"},
    {"number": "18", "full_name": "Kyle Busch",           "team": "Joe Gibbs Racing",      "manufacturer": "Toyota",    "wins": 2,  "country": "US"},
    # Team Penske (Ford)
    {"number": "12", "full_name": "Ryan Blaney",          "team": "Team Penske",           "manufacturer": "Ford",      "wins": 4,  "country": "US"},
    {"number": "22", "full_name": "Joey Logano",          "team": "Team Penske",           "manufacturer": "Ford",      "wins": 2,  "country": "US"},
    {"number": "2",  "full_name": "Austin Cindric",       "team": "Team Penske",           "manufacturer": "Ford",      "wins": 1,  "country": "US"},
    # 23XI Racing (Toyota)
    {"number": "45", "full_name": "Tyler Reddick",        "team": "23XI Racing",           "manufacturer": "Toyota",    "wins": 2,  "country": "US"},
    {"number": "23", "full_name": "Bubba Wallace",        "team": "23XI Racing",           "manufacturer": "Toyota",    "wins": 1,  "country": "US"},
    # RFK Racing (Ford)
    {"number": "6",  "full_name": "Brad Keselowski",      "team": "RFK Racing",            "manufacturer": "Ford",      "wins": 1,  "country": "US"},
    {"number": "17", "full_name": "Chris Buescher",       "team": "RFK Racing",            "manufacturer": "Ford",      "wins": 1,  "country": "US"},
    # Trackhouse Racing (Chevrolet)
    {"number": "1",  "full_name": "Ross Chastain",        "team": "Trackhouse Racing",     "manufacturer": "Chevrolet", "wins": 2,  "country": "US"},
    {"number": "99", "full_name": "Daniel Suarez",        "team": "Trackhouse Racing",     "manufacturer": "Chevrolet", "wins": 1,  "country": "MX"},
    {"number": "10", "full_name": "Shane van Gisbergen",  "team": "Trackhouse Racing",     "manufacturer": "Chevrolet", "wins": 1,  "country": "NZ"},
    # Richard Childress Racing (Chevrolet)
    {"number": "3",  "full_name": "Austin Dillon",        "team": "Richard Childress Racing","manufacturer": "Chevrolet","wins": 1,  "country": "US"},
    # Kaulig Racing / JTG / others
    {"number": "47", "full_name": "Ricky Stenhouse Jr.",  "team": "JTG Daugherty Racing",  "manufacturer": "Chevrolet", "wins": 0,  "country": "US"},
    {"number": "34", "full_name": "Michael McDowell",     "team": "Front Row Motorsports", "manufacturer": "Ford",      "wins": 0,  "country": "US"},
    {"number": "38", "full_name": "Todd Gilliland",       "team": "Front Row Motorsports", "manufacturer": "Ford",      "wins": 0,  "country": "US"},
    {"number": "21", "full_name": "Harrison Burton",      "team": "Wood Brothers Racing",  "manufacturer": "Ford",      "wins": 0,  "country": "US"},
    {"number": "42", "full_name": "Noah Gragson",         "team": "Legacy Motor Club",     "manufacturer": "Chevrolet", "wins": 0,  "country": "US"},
    {"number": "43", "full_name": "Erik Jones",           "team": "Legacy Motor Club",     "manufacturer": "Chevrolet", "wins": 0,  "country": "US"},
    {"number": "77", "full_name": "Carson Hocevar",       "team": "Spire Motorsports",     "manufacturer": "Chevrolet", "wins": 0,  "country": "US"},
    {"number": "7",  "full_name": "Corey LaJoie",         "team": "Spire Motorsports",     "manufacturer": "Ford",      "wins": 0,  "country": "US"},
]

_SEASONS: dict[int, list[dict]] = {
    2025: _DRIVERS_2025,
}


def get_drivers(year: int = 2025) -> list[dict]:
    drivers = _SEASONS.get(year, _DRIVERS_2025)
    # Sort by wins desc, then name
    drivers = sorted(drivers, key=lambda d: (-d["wins"], d["full_name"]))
    result = []
    for i, d in enumerate(drivers):
        pos = i + 1
        last = d["full_name"].split()[-1]
        code = last[:3].upper()
        result.append({
            "series":       "nascar",
            "category":     "Cup Series",
            "pos":          pos,
            "number":       d["number"],
            "full_name":    d["full_name"],
            "last_name":    last,
            "code":         code,
            "team":         d["team"],
            "manufacturer": d["manufacturer"],
            "color":        MANUFACTURER_COLOR.get(d["manufacturer"], "#888"),
            "country":      d["country"],
            "wins":         d["wins"],
            "points":       max(0, 2000 - (pos - 1) * 50),
            "year":         year,
        })
    return result
