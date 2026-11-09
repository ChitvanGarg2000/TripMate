import os
import re
import certifi
import requests
import airportsdata
import pycountry
from Settings import settings
import constants

os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()


class FlightTool:
    def __init__(self):
        self.base_url = settings.AVIATION_STACK_BASE_URL
        self.api_key = settings.AVIATION_STACK_API_KEY

        # Cache airports at instantiation to avoid repeated loading
        self._airports = None

        # Derive the default origin IATA from DEFAULT_ORIGIN_IATA (a country code like "IN")
        default_country = (settings.DEFAULT_ORIGIN_IATA or "IN").strip().upper()
        preferred = constants.COUNTRY_MAIN_AIRPORT.get(default_country)
        self.default_origin_iata = preferred or "DEL"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_airports(self) -> dict:
        """Load and cache the IATA airports database."""
        if self._airports is None:
            try:
                self._airports = airportsdata.load("iata")
            except Exception as e:
                print(f"Error loading airports data: {e}")
                self._airports = {}
        return self._airports

        # Cache airports at instantiation to avoid repeated loading
        self._airports = None

        # Derive the default origin IATA from DEFAULT_ORIGIN_IATA (a country code like "IN")
        default_country = (settings.DEFAULT_ORIGIN_IATA or "IN").strip().upper()
        preferred = constants.COUNTRY_MAIN_AIRPORT.get(default_country)
        self.default_origin_iata = preferred or "DEL"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_airports(self) -> dict:
        """Load and cache the IATA airports database."""
        if self._airports is None:
            try:
                self._airports = airportsdata.load("iata")
            except Exception as e:
                print(f"Error loading airports data: {e}")
                self._airports = {}
        return self._airports

    def clean_text(self, text: str) -> str:
        """Lowercase, strip punctuation, and remove travel-related stop words."""
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        stop_words = {
            "flight", "flights", "ticket", "tickets", "trip", "travel",
            "plan", "complete", "days", "day", "including", "hotel",
            "hotels", "sightseeing", "under", "budget", "info", "information",
            "show", "me", "find", "get", "book", "please", "want",
        }
        words = [w for w in text.split() if w not in stop_words]
        return " ".join(words).strip()

    def country_name_to_code(self, text: str):
        """
        Convert a country name / alias to an ISO-3166-1 alpha-2 code.

        Fixes over the original:
        - Uses word-boundary regex instead of substring `in` to avoid
          "mali" matching inside "somalia", "oman" inside "romania", etc.
        - Sorts candidates by name length (longest first) so "united states"
          wins over "united" / "states".
        """
        text = self.clean_text(text)
        if not text:
            return None

        # 1. Exact alias match
        if text in constants.COUNTRY_ALIASES:
            return constants.COUNTRY_ALIASES[text]

        # 2. pycountry direct lookup (handles official names and ISO codes)
        try:
            country = pycountry.countries.lookup(text)
            return country.alpha_2
        except LookupError:
            pass

        # 3. Word-boundary alias scan (longest alias first to avoid early exits)
        for alias, code in sorted(
            constants.COUNTRY_ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True
        ):
            if re.search(rf"\b{re.escape(alias)}\b", text):
                return code

        # 4. Word-boundary pycountry scan (longest country name first)
        for country in sorted(
            pycountry.countries, key=lambda c: len(c.name), reverse=True
        ):
            cname = country.name.lower()
            if len(cname) >= 4 and re.search(rf"\b{re.escape(cname)}\b", text):
                return country.alpha_2

        return None

    def airport_country_matches(self, airport: dict, country_code: str) -> bool:
        """Check whether an airport record belongs to the given country code."""
        airport_country = str(airport.get("country", "") or "").upper().strip()
        if airport_country == country_code:
            return True
        try:
            country = pycountry.countries.get(alpha_2=country_code)
            if country and airport_country.lower() == country.name.lower():
                return True
        except Exception:
            pass
        return False

    def get_best_airport_for_country(self, country_code: str):
        """
        Return the most prominent IATA airport for a country.

        Checks the COUNTRY_MAIN_AIRPORT preference table first; falls back to
        a heuristic score based on the airport name.
        """
        airports = self._load_airports()
        preferred = constants.COUNTRY_MAIN_AIRPORT.get(country_code)
        if preferred and preferred in airports:
            return preferred

        candidates = []
        for iata, airport in airports.items():
            if not iata:
                continue
            if self.airport_country_matches(airport, country_code):
                name = str(airport.get("name", "") or "").lower()
                city = str(airport.get("city", "") or "").lower()
                score = 0
                if "international" in name:
                    score += 50
                if "intl" in name:
                    score += 40
                if "capital" in name:
                    score += 20
                if city:
                    score += 5
                candidates.append((score, iata))

        if not candidates:
            return None
        candidates.sort(reverse=True)
        return candidates[0][1]

    # ------------------------------------------------------------------
    # Location → IATA resolution
    # ------------------------------------------------------------------

    def resolve_location_to_iata(self, location: str):
        """
        Converts a free-form location string (country, city, airport name, or
        IATA code) into an IATA airport code.

        Fixes over the original (which was a bare module-level function that
        referenced undefined names):
        - Now a proper instance method using self._load_airports(), etc.
        - Airport name search scores exact name match higher than substring.
        - `international` bonus only applied when the base score > 0.
        """
        if not location:
            return None

        airports = self._load_airports()
        raw_location = location.strip()

        # 1. Direct 3-letter IATA code
        if re.fullmatch(r"[A-Za-z]{3}", raw_location):
            code = raw_location.upper()
            if code in airports:
                return code

        location_clean = self.clean_text(raw_location)
        if not location_clean:
            return None

        # 2. City preference table
        if location_clean in constants.CITY_MAIN_AIRPORT:
            return constants.CITY_MAIN_AIRPORT[location_clean]

        # 3. Country lookup
        country_code = self.country_name_to_code(location_clean)
        if country_code:
            airport = self.get_best_airport_for_country(country_code)
            if airport:
                return airport

        # 4. Fuzzy match against the airports database
        city_matches = []
        for iata, airport in airports.items():
            city = str(airport.get("city", "") or "").lower().strip()
            name = str(airport.get("name", "") or "").lower().strip()
            score = 0

            if city == location_clean:
                score += 100
            elif location_clean in city:
                score += 70

            if name == location_clean:
                score += 120
            elif location_clean in name:
                score += 50

            if score > 0 and "international" in name:
                score += 10

            if score > 0:
                city_matches.append((score, iata))

        if city_matches:
            city_matches.sort(reverse=True)
            return city_matches[0][1]

        return None

    # ------------------------------------------------------------------
    # Query parsing helpers
    # ------------------------------------------------------------------

    def find_location_mentions(self, query: str) -> list:
        """
        Find country / city mentions in a natural-language query in the order
        they appear in the string.

        Fixes over the original (bare function referencing undefined dicts):
        - Collects (start, end, text) tuples, sorts by position, then filters
          out overlapping matches — so "new delhi" beats "delhi" and insertion
          order reflects query order, not dict iteration order.
        """
        q = query.lower()
        matches = []  # list of (start, end, text)

        for city in constants.CITY_MAIN_AIRPORT:
            for m in re.finditer(rf"\b{re.escape(city)}\b", q):
                matches.append((m.start(), m.end(), city))

        for alias in constants.COUNTRY_ALIASES:
            for m in re.finditer(rf"\b{re.escape(alias)}\b", q):
                matches.append((m.start(), m.end(), alias))

        for country in pycountry.countries:
            name = country.name.lower()
            if len(name) >= 4:
                for m in re.finditer(rf"\b{re.escape(name)}\b", q):
                    matches.append((m.start(), m.end(), name))

        # Sort by start position; prefer longer matches at same position
        matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))

        # Remove overlapping spans (keep the first / longer match)
        filtered = []
        last_end = -1
        for start, end, text in matches:
            if start >= last_end:
                filtered.append(text)
                last_end = end

        # Deduplicate while preserving order
        unique: list = []
        for item in filtered:
            if item not in unique:
                unique.append(item)
        return unique

    def parse_route(self, query: str):
        """
        Parse a natural-language flight query and return (dep_iata, arr_iata).

        Returns:
            (None, None)   – global / all-flights query
            ('DEL', 'BOM') – specific route
            ('DEL', None)  – all departures from DEL
            (None, 'BOM')  – all arrivals to BOM

        Fixes over the original (bare function referencing undefined names):
        - Now an instance method.
        - Added "X to Y" positional pattern so "Delhi to Mumbai" works without
          an explicit "from / to" prefix.
        - Added "between X and Y" pattern.
        - Guards results so a pattern that resolves to (None, None) falls
          through to the next pattern rather than returning prematurely.
        - Uses self.default_origin_iata instead of the undefined constant
          DEFAULT_ORIGIN_IATA.
        """
        q = query.strip()
        q_lower = q.lower()

        global_keywords = [
            "all country", "all countries",
            "global flight", "global flights",
            "all flight", "all flights",
            "worldwide flight", "worldwide flights",
        ]
        if any(kw in q_lower for kw in global_keywords):
            return None, None

        # --- 1. Direct IATA pair (e.g. "DAC to NRT", "DEL-BOM") ----------
        airports = self._load_airports()
        iata_match = re.search(
            r"\b([A-Za-z]{3})\s*(?:to|->|--?)\s*([A-Za-z]{3})\b", q
        )
        if iata_match:
            c1 = iata_match.group(1).upper()
            c2 = iata_match.group(2).upper()
            if c1 in airports and c2 in airports:
                return c1, c2

        # --- 2. "between X and Y" -----------------------------------------
        match = re.search(
            r"\bbetween\s+(.+?)\s+\band\s+(.+?)"
            r"(?:\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
            q_lower,
        )
        if match:
            dep = self.resolve_location_to_iata(match.group(1))
            arr = self.resolve_location_to_iata(match.group(2))
            if dep or arr:
                return dep, arr

        # --- 3. "from X to Y" ---------------------------------------------
        match = re.search(
            r"\bfrom\s+(.+?)\s+\bto\s+(.+?)"
            r"(?:\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
            q_lower,
        )
        if match:
            dep = self.resolve_location_to_iata(match.group(1))
            arr = self.resolve_location_to_iata(match.group(2))
            if dep or arr:
                return dep, arr

        # --- 4. "to Y from X" ---------------------------------------------
        match = re.search(
            r"\bto\s+(.+?)\s+\bfrom\s+(.+?)"
            r"(?:\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
            q_lower,
        )
        if match:
            arr = self.resolve_location_to_iata(match.group(1))
            dep = self.resolve_location_to_iata(match.group(2))
            if dep or arr:
                return dep, arr

        # --- 5. Positional "X to Y" (e.g. "Delhi to Mumbai") --------------
        match = re.search(
            r"(?:^|(?:flights?|tickets?)\s+)(.+?)\s+\bto\s+(.+?)"
            r"(?:\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
            q_lower,
        )
        if match:
            dep = self.resolve_location_to_iata(match.group(1).strip())
            arr = self.resolve_location_to_iata(match.group(2).strip())
            if dep and arr:
                return dep, arr
            if arr:
                return self.default_origin_iata, arr

        # --- 6. "flights from X" ------------------------------------------
        match = re.search(
            r"\bfrom\s+(.+?)"
            r"(?:\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
            q_lower,
        )
        if match:
            dep = self.resolve_location_to_iata(match.group(1))
            if dep:
                return dep, None

        # --- 7. "flights to X" --------------------------------------------
        match = re.search(
            r"\bto\s+(.+?)"
            r"(?:\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
            q_lower,
        )
        if match:
            arr = self.resolve_location_to_iata(match.group(1))
            if arr:
                return self.default_origin_iata, arr

        # --- 8. Fallback: scan for any location mentions ------------------
        mentions = self.find_location_mentions(q)
        if len(mentions) >= 2:
            dep = self.resolve_location_to_iata(mentions[0])
            arr = self.resolve_location_to_iata(mentions[1])
            return dep, arr
        if len(mentions) == 1:
            arr = self.resolve_location_to_iata(mentions[0])
            return self.default_origin_iata, arr

        return None, None

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    @staticmethod
    def format_flight(flight: dict) -> str:
        """Format a single flight record from the AviationStack API."""
        airline = flight.get("airline", {}).get("name") or "Unknown airline"
        flight_number = flight.get("flight", {}).get("iata") or "Unknown flight number"
        status = flight.get("flight_status") or "Unknown"

        dep = flight.get("departure", {}) or {}
        arr = flight.get("arrival", {}) or {}

        dep_airport  = dep.get("airport")  or "Unknown departure airport"
        dep_iata     = dep.get("iata")     or "Unknown"
        dep_terminal = dep.get("terminal") or "N/A"
        dep_gate     = dep.get("gate")     or "N/A"
        dep_scheduled = dep.get("scheduled") or "Unknown"
        dep_delay    = dep.get("delay")
        dep_delay_text = f"{dep_delay} minutes" if dep_delay is not None else "N/A"

        arr_airport  = arr.get("airport")  or "Unknown arrival airport"
        arr_iata     = arr.get("iata")     or "Unknown"
        arr_terminal = arr.get("terminal") or "N/A"
        arr_gate     = arr.get("gate")     or "N/A"
        arr_scheduled = arr.get("scheduled") or "Unknown"
        arr_delay    = arr.get("delay")
        arr_delay_text = f"{arr_delay} minutes" if arr_delay is not None else "N/A"

        return f"""\
Airline: {airline}
Flight: {flight_number}
Status: {status}

Departure:
- Airport: {dep_airport}
- IATA: {dep_iata}
- Terminal: {dep_terminal}
- Gate: {dep_gate}
- Scheduled: {dep_scheduled}
- Delay: {dep_delay_text}

Arrival:
- Airport: {arr_airport}
- IATA: {arr_iata}
- Terminal: {arr_terminal}
- Gate: {arr_gate}
- Scheduled: {arr_scheduled}
- Delay: {arr_delay_text}""".strip()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_flights(self, query: str, limit: int = 10) -> str:
        """
        Main entry point: parse *query*, call the AviationStack API, and
        return a human-readable summary of live flight data.
        """
        if not self.api_key:
            return (
                "Flight API error: AVIATION_STACK_API_KEY is missing.\n"
                "Please add this to your .env file:\n"
                "AVIATION_STACK_API_KEY=your_api_key_here"
            )

        dep_iata, arr_iata = self.parse_route(query)

        params: dict = {
            "access_key": self.api_key,
            "limit": min(limit, 100),
        }
        if dep_iata:
            params["dep_iata"] = dep_iata
        if arr_iata:
            params["arr_iata"] = arr_iata

        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            data = response.json()
        except requests.exceptions.RequestException as e:
            return f"Flight API request failed: {e}"
        except ValueError:
            return "Flight API returned invalid JSON."

        if "error" in data:
            error = data["error"]
            return (
                "Flight API error:\n"
                f"Code: {error.get('code', 'Unknown')}\n"
                f"Message: {error.get('message', 'Unknown error')}"
            )

        flight_data = data.get("data", [])

        if not flight_data:
            route_text = ""
            if dep_iata and arr_iata:
                route_text = f" for route {dep_iata} to {arr_iata}"
            elif dep_iata:
                route_text = f" from {dep_iata}"
            elif arr_iata:
                route_text = f" to {arr_iata}"
            return (
                f"No live flight data found{route_text}.\n\n"
                "Note: AviationStack provides live/status flight data, not ticket prices. "
                "For actual fare prices, use a flight-pricing API such as Amadeus."
            )

        route_info = "Global live flights"
        if dep_iata and arr_iata:
            route_info = f"Live flights from {dep_iata} to {arr_iata}"
        elif dep_iata:
            route_info = f"Live flights from {dep_iata}"
        elif arr_iata:
            route_info = f"Live flights to {arr_iata}"

        formatted = [self.format_flight(f) for f in flight_data[:limit]]
        return f"{route_info}\n\n" + "\n\n---\n\n".join(formatted)
