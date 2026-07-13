"""Best-effort country inference from free-text location strings.

Neither RemoteOK nor Arbeitnow gives a structured country field - just a
human-typed location string ("Berlin", "Greater Chicago Area", "São Paulo,
São Paulo, Brasil"). This does substring/alias matching against a static
country name list, then a small set of well-known city fallbacks. It is
explicitly best-effort: ambiguous or obscure locations return None rather
than guess, and the UI should present results as approximate.
"""
import re

# Canonical country name -> aliases seen in job postings (non-English
# names, common abbreviations, old/alternate spellings).
_COUNTRY_ALIASES: dict[str, list[str]] = {
    "United States": ["united states", "usa", "u.s.a", "u.s.", "america"],
    "United Kingdom": ["united kingdom", "uk", "u.k.", "england", "scotland", "wales"],
    "Brazil": ["brazil", "brasil"],
    "Spain": ["spain", "españa", "espana"],
    "Mexico": ["mexico", "méxico"],
    "Peru": ["peru", "perú"],
    "Germany": ["germany", "deutschland"],
    "India": ["india"],
    "Canada": ["canada"],
    "Australia": ["australia"],
    "France": ["france"],
    "Italy": ["italy", "italia"],
    "Netherlands": ["netherlands", "the netherlands", "holland"],
    "Portugal": ["portugal"],
    "Poland": ["poland", "polska"],
    "Ireland": ["ireland"],
    "Switzerland": ["switzerland", "schweiz", "suisse"],
    "Austria": ["austria", "österreich", "osterreich"],
    "Belgium": ["belgium", "belgique", "belgië"],
    "Sweden": ["sweden", "sverige"],
    "Norway": ["norway", "norge"],
    "Denmark": ["denmark", "danmark"],
    "Finland": ["finland", "suomi"],
    "Colombia": ["colombia"],
    "Argentina": ["argentina"],
    "Chile": ["chile"],
    "Philippines": ["philippines"],
    "Indonesia": ["indonesia"],
    "Pakistan": ["pakistan"],
    "Bangladesh": ["bangladesh"],
    "Nigeria": ["nigeria"],
    "South Africa": ["south africa"],
    "Egypt": ["egypt"],
    "United Arab Emirates": ["united arab emirates", "uae", "u.a.e."],
    "Saudi Arabia": ["saudi arabia"],
    "Israel": ["israel"],
    "Turkey": ["turkey", "türkiye", "turkiye"],
    "Russia": ["russia"],
    "Ukraine": ["ukraine"],
    "Romania": ["romania"],
    "Greece": ["greece"],
    "Czech Republic": ["czech republic", "czechia"],
    "Hungary": ["hungary"],
    "Vietnam": ["vietnam", "viet nam"],
    "Thailand": ["thailand"],
    "Malaysia": ["malaysia"],
    "Singapore": ["singapore"],
    "China": ["china"],
    "Japan": ["japan"],
    "South Korea": ["south korea", "korea"],
    "New Zealand": ["new zealand"],
}

# Well-known cities that commonly appear without a country suffix.
_CITY_TO_COUNTRY: dict[str, str] = {
    "berlin": "Germany", "munich": "Germany", "hamburg": "Germany", "frankfurt": "Germany",
    "london": "United Kingdom", "manchester": "United Kingdom",
    "paris": "France", "lyon": "France",
    "madrid": "Spain", "barcelona": "Spain",
    "rome": "Italy", "milan": "Italy",
    "amsterdam": "Netherlands", "rotterdam": "Netherlands",
    "lisbon": "Portugal",
    "dublin": "Ireland",
    "warsaw": "Poland",
    "vienna": "Austria",
    "zurich": "Switzerland", "geneva": "Switzerland",
    "stockholm": "Sweden",
    "oslo": "Norway",
    "copenhagen": "Denmark",
    "helsinki": "Finland",
    "toronto": "Canada", "vancouver": "Canada", "montreal": "Canada",
    "sydney": "Australia", "melbourne": "Australia",
    "singapore": "Singapore",
    "tokyo": "Japan",
    "seoul": "South Korea",
    "beijing": "China", "shanghai": "China",
    "mumbai": "India", "bangalore": "India", "bengaluru": "India", "hyderabad": "India",
    "delhi": "India", "chennai": "India", "pune": "India", "mangaluru": "India",
    "chicago": "United States", "new york": "United States", "san francisco": "United States",
    "los angeles": "United States", "seattle": "United States", "austin": "United States",
    "boston": "United States", "atlanta": "United States", "miami": "United States",
    "denver": "United States", "dallas": "United States", "houston": "United States",
    "mexico city": "Mexico", "ciudad de mexico": "Mexico",
    "sao paulo": "Brazil", "rio de janeiro": "Brazil",
    "buenos aires": "Argentina",
    "santiago": "Chile",
    "bogota": "Colombia", "bogotá": "Colombia",
    "lima": "Peru",
    "dubai": "United Arab Emirates",
    "tel aviv": "Israel",
    "istanbul": "Turkey",
}

_COUNTRY_LOOKUP: dict[str, str] = {
    alias: canonical for canonical, aliases in _COUNTRY_ALIASES.items() for alias in aliases
}


def infer_country(location: str | None) -> str | None:
    """Returns a best-effort canonical country name, or None if nothing
    in `location` matches a known country or city."""
    if not location:
        return None

    normalized = re.sub(r"[^\w\s,]", " ", location.lower())

    for alias, canonical in _COUNTRY_LOOKUP.items():
        if re.search(rf"\b{re.escape(alias)}\b", normalized):
            return canonical

    for segment in (s.strip() for s in normalized.split(",")):
        if segment in _CITY_TO_COUNTRY:
            return _CITY_TO_COUNTRY[segment]

    return None
