import re

from app.nlp.canonicalization.canonicalizer import Canonicalizer


class EntityExtractor:
    """
    Phase 7.2 — Entity Extractor

    Extracts structured cricket entities from a rewritten question.
    Feeds the intent router (Phase 7.3) with precise, resolved entities.

    Extracts:
    - players      : resolved canonical player names
    - teams        : IPL team names
    - venues       : stadium / ground names
    - phases       : powerplay / middle overs / death overs
    - metrics      : runs / wickets / economy / strike rate etc.
    - intents      : comparison / ranking / profile / venue / team / performance
    - limit        : how many results the user wants (top 5, top 10)
    - is_comparison: two or more players OR comparison keyword present
    - is_profile   : descriptive question about a player or team
    - is_ranking   : top-N / best / leaderboard question
    - is_team      : question is about a team not a player
    - is_venue     : question is about a venue
    """

    # ---------------------------------------------------------------------------
    # Known IPL teams — full names and common short forms
    # ---------------------------------------------------------------------------

    TEAMS = {
        "mumbai indians",
        "chennai super kings",
        "royal challengers bangalore",
        "royal challengers bengaluru",
        "kolkata knight riders",
        "sunrisers hyderabad",
        "delhi capitals",
        "delhi daredevils",
        "rajasthan royals",
        "punjab kings",
        "kings xi punjab",
        "lucknow super giants",
        "gujarat titans",
        "rising pune supergiant",
        "gujarat lions",
        "pune warriors india",
        "kochi tuskers kerala",
    }

    # ---------------------------------------------------------------------------
    # Known IPL venues
    # ---------------------------------------------------------------------------

    VENUES = {
        "wankhede stadium",
        "wankhede",
        "eden gardens",
        "m chinnaswamy stadium",
        "chinnaswamy",
        "ma chidambaram stadium",
        "chepauk",
        "arun jaitley stadium",
        "feroz shah kotla",
        "narendra modi stadium",
        "motera",
        "rajiv gandhi international stadium",
        "rajiv gandhi stadium",
        "uppal",
        "sawai mansingh stadium",
        "punjab cricket association stadium",
        "is bindra stadium",
        "ekana cricket stadium",
        "brabourne stadium",
        "sharjah cricket stadium",
        "dubai international cricket stadium",
        "sheikh zayed stadium",
    }

    # ---------------------------------------------------------------------------
    # Phase keywords
    # ---------------------------------------------------------------------------

    PHASE_PATTERNS = {
        "powerplay": re.compile(
            r"\b(powerplay|power play|pp|first 6 overs|"
            r"first six overs|opening overs|initial overs)\b",
            re.IGNORECASE
        ),
        "death overs": re.compile(
            r"\b(death overs|death over|slog overs|last 4 overs|"
            r"last four overs|final overs|last overs)\b",
            re.IGNORECASE
        ),
        "middle overs": re.compile(
            r"\b(middle overs|middle over|overs 7|overs 8|"
            r"between overs|mid overs)\b",
            re.IGNORECASE
        ),
    }

    # ---------------------------------------------------------------------------
    # Metric keywords
    # ---------------------------------------------------------------------------

    METRIC_PATTERNS = {
        "runs":        re.compile(
            r"\b(runs|run scorer|run scoring|scored|"
            r"centuries|fifties|hundreds|batting)\b",
            re.IGNORECASE
        ),
        "wickets":     re.compile(
            r"\b(wickets|wicket taker|wicket taking|"
            r"dismissals|scalps|bowling figures)\b",
            re.IGNORECASE
        ),
        "economy":     re.compile(
            r"\b(economy|economy rate|econ|runs per over|rpo|conceding)\b",
            re.IGNORECASE
        ),
        "strike_rate": re.compile(
            r"\b(strike rate|sr|hitting rate|scoring rate)\b",
            re.IGNORECASE
        ),
        "average":     re.compile(
            r"\b(average|batting average|bowling average|avg)\b",
            re.IGNORECASE
        ),
        "sixes":       re.compile(
            r"\b(sixes|six|maximums|six hitter|over the boundary)\b",
            re.IGNORECASE
        ),
        "fours":       re.compile(
            r"\b(fours|four|boundaries|boundary hitter)\b",
            re.IGNORECASE
        ),
    }

    # ---------------------------------------------------------------------------
    # Intent signal patterns — expanded for broader real-world coverage
    # ---------------------------------------------------------------------------

    INTENT_PATTERNS = {
        "comparison": re.compile(
            r"\b(compare|vs|versus|better than|difference between|"
            r"who is better|against each other|more effective|"
            r"superior|outperform|head to head|head-to-head)\b",
            re.IGNORECASE
        ),
        "ranking": re.compile(
            r"\b(top|best|most|highest|lowest|worst|leading|"
            r"rank|ranking|leaderboard|list|who has|who scored|"
            r"who took|who bowled|greatest|dominant)\b",
            re.IGNORECASE
        ),
        "profile": re.compile(
            r"\b(who is|tell me about|describe|explain|profile of|"
            r"what kind of player|playing style|career of|"
            r"about the player|strengths|weaknesses|known for|"
            r"batting style|bowling style|what type of)\b",
            re.IGNORECASE
        ),
        "performance": re.compile(
            r"\b(perform|performs|performance|how does|how did|"
            r"how well|how good|effective|impact|contribution|"
            r"record|stats|statistics|numbers|figures|average|"
            r"how many|how much|what is|what are|what was|"
            r"score|scored|took|taken|bowled|conceded)\b",
            re.IGNORECASE
        ),
        "venue": re.compile(
            r"\b(venue|ground|stadium|pitch|surface|at which ground|"
            r"best ground|highest scoring venue|best venue|"
            r"which stadium|which ground|which venue|"
            r"highest average|best pitch|batting friendly)\b",
            re.IGNORECASE
        ),
        "team": re.compile(
            r"\b(team|franchise|squad|side|playing for|represents|"
            r"plays for|which team|which franchise|wins most|"
            r"most wins|team performance|franchise performance)\b",
            re.IGNORECASE
        ),
    }

    # ---------------------------------------------------------------------------
    # Limit extractor — "top 5", "top 10", "best 3"
    # ---------------------------------------------------------------------------

    LIMIT_PATTERN = re.compile(
        r"\b(?:top|best|first|leading)\s+(\d+)\b",
        re.IGNORECASE
    )

    # ---------------------------------------------------------------------------
    # Question-opening words to strip before player extraction
    # These appear capitalised at sentence start and bleed into name matches
    # ---------------------------------------------------------------------------

    QUESTION_OPENERS = {
        "compare", "who", "which", "what", "where", "when", "how",
        "tell", "show", "list", "give", "find", "explain", "describe",
        "is", "are", "was", "were", "does", "did", "do", "best",
        "top", "worst", "most", "least", "can", "could", "would",
        "should", "will", "name", "get", "fetch", "provide",
    }

    # ---------------------------------------------------------------------------
    # Player name candidate patterns
    # Pattern A — standard title case:  "Virat Kohli", "Rohit Sharma"
    # Pattern B — initials + surname:   "MS Dhoni", "AB de Villiers", "KL Rahul"
    # ---------------------------------------------------------------------------

    PLAYER_CANDIDATE_PATTERN = re.compile(
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
    )

    PLAYER_INITIALS_PATTERN = re.compile(
        r"\b([A-Z]{1,3}(?:\s+[A-Z][a-z]+)+)\b"
    )

    # ---------------------------------------------------------------------------
    # Core extract method
    # ---------------------------------------------------------------------------

    @classmethod
    def extract(
        cls,
        question: str,
        db=None
    ) -> dict:
        """
        Extract all cricket entities from a rewritten question.

        Parameters
        ----------
        question : rewritten question string from QueryRewriter
        db       : SQLAlchemy session for canonicalization (optional)

        Returns
        -------
        {
            "players":       list[str],
            "teams":         list[str],
            "venues":        list[str],
            "phases":        list[str],
            "metrics":       list[str],
            "intents":       list[str],
            "limit":         int | None,
            "is_comparison": bool,
            "is_profile":    bool,
            "is_ranking":    bool,
            "is_team":       bool,
            "is_venue":      bool,
        }
        """

        lower = (question or "").lower()

        players = cls._extract_players(question=question, db=db)
        teams   = cls._extract_teams(lower=lower)
        venues  = cls._extract_venues(lower=lower)
        phases  = cls._extract_phases(lower=lower)
        metrics = cls._extract_metrics(lower=lower)
        intents = cls._extract_intents(lower=lower)
        limit   = cls._extract_limit(question=question)

        # ── Derived boolean flags ─────────────────────────────────────────────

        is_comparison = (
            len(players) >= 2
            or "comparison" in intents
        )

        is_profile = (
            "profile" in intents
            or (len(players) == 1 and "performance" in intents)
            or (len(players) == 1 and len(metrics) == 0 and len(phases) == 0)
        )

        is_ranking = (
            "ranking" in intents
            and not is_comparison
            and len(players) <= 1
        )

        # is_team: named team found OR team intent with no players/venues
        is_team = (
            (len(teams) > 0 and len(players) == 0)
            or ("team" in intents and len(players) == 0 and len(venues) == 0)
        )

        # is_venue: named venue found OR venue intent with no players/teams
        is_venue = (
            (len(venues) > 0 and len(players) == 0 and len(teams) == 0)
            or ("venue" in intents and len(players) == 0 and len(teams) == 0)
        )

        return {
            "players":       players,
            "teams":         teams,
            "venues":        venues,
            "phases":        phases,
            "metrics":       metrics,
            "intents":       intents,
            "limit":         limit,
            "is_comparison": is_comparison,
            "is_profile":    is_profile,
            "is_ranking":    is_ranking,
            "is_team":       is_team,
            "is_venue":      is_venue,
        }

    # ---------------------------------------------------------------------------
    # Player extraction
    # ---------------------------------------------------------------------------

    @classmethod
    def _extract_players(
        cls,
        question: str,
        db=None
    ) -> list:

        # Collect candidates from both patterns
        raw_candidates = (
            cls.PLAYER_CANDIDATE_PATTERN.findall(question)
            + cls.PLAYER_INITIALS_PATTERN.findall(question)
        )

        # Deduplicate while preserving order
        seen_raw  = set()
        candidates = []
        for c in raw_candidates:
            if c not in seen_raw:
                seen_raw.add(c)
                candidates.append(c)

        if not candidates:
            return []

        resolved = []
        seen     = set()

        for candidate in candidates:

            # Trim question-opener from start of candidate
            words      = candidate.split()
            first_word = words[0].lower()

            if first_word in cls.QUESTION_OPENERS:
                words = words[1:]
                if not words:
                    continue
                candidate = " ".join(words)

            # Skip if matches a known team
            if candidate.lower() in cls.TEAMS:
                continue

            # Skip if matches a known venue
            if candidate.lower() in cls.VENUES:
                continue

            # Try canonicalizer
            # NOTE: DB fuzzy resolution disabled — players table contains
            # non-IPL data from terminated Cric API. Resolution uses
            # PLAYER_REGISTRY (29 entries) and PlayerMapping (exact matches).
            # When players table is cleaned up, remove db=None override.
            canonical = Canonicalizer.canonicalize(
                player_name=candidate,
                db=None
            )

            # Accept only multi-word resolved names
            if (
                canonical
                and canonical not in seen
                and len(canonical.split()) >= 2
            ):
                seen.add(canonical)
                resolved.append(canonical)

        return resolved

    # ---------------------------------------------------------------------------
    # Team extraction
    # ---------------------------------------------------------------------------

    @classmethod
    def _extract_teams(cls, lower: str) -> list:

        found = []
        # Longest match first to avoid "Kings" matching before "Punjab Kings"
        for team in sorted(cls.TEAMS, key=len, reverse=True):
            if team in lower:
                found.append(team.title())
                lower = lower.replace(team, "")

        return found

    # ---------------------------------------------------------------------------
    # Venue extraction
    # ---------------------------------------------------------------------------

    @classmethod
    def _extract_venues(cls, lower: str) -> list:

        found = []
        for venue in sorted(cls.VENUES, key=len, reverse=True):
            if venue in lower:
                found.append(venue.title())
                lower = lower.replace(venue, "")

        return found

    # ---------------------------------------------------------------------------
    # Phase extraction
    # ---------------------------------------------------------------------------

    @classmethod
    def _extract_phases(cls, lower: str) -> list:

        return [
            phase
            for phase, pattern in cls.PHASE_PATTERNS.items()
            if pattern.search(lower)
        ]

    # ---------------------------------------------------------------------------
    # Metric extraction
    # ---------------------------------------------------------------------------

    @classmethod
    def _extract_metrics(cls, lower: str) -> list:

        return [
            metric
            for metric, pattern in cls.METRIC_PATTERNS.items()
            if pattern.search(lower)
        ]

    # ---------------------------------------------------------------------------
    # Intent extraction
    # ---------------------------------------------------------------------------

    @classmethod
    def _extract_intents(cls, lower: str) -> list:

        return [
            intent
            for intent, pattern in cls.INTENT_PATTERNS.items()
            if pattern.search(lower)
        ]

    # ---------------------------------------------------------------------------
    # Limit extraction
    # ---------------------------------------------------------------------------

    @classmethod
    def _extract_limit(cls, question: str) -> int | None:

        match = cls.LIMIT_PATTERN.search(question)
        return int(match.group(1)) if match else None