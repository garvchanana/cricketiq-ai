import re

class QueryRewriter:
    """
    Phase 7.1 — Query Rewriter
 
    Cleans and normalises raw user questions before they reach
    the intent router, entity extractor, or SQL generator.
 
    Three responsibilities:
    1. Expand cricket abbreviations into full forms
    2. Standardise player name variants into canonical spellings
    3. Clean whitespace, punctuation, and casing
    """
 
    # ---------------------------------------------------------------------------
    # Cricket abbreviations → full forms
    # ---------------------------------------------------------------------------
 
    ABBREVIATIONS = {
 
        # Teams
        "rcb":   "Royal Challengers Bangalore",
        "csk":   "Chennai Super Kings",
        "mi":    "Mumbai Indians",
        "kkr":   "Kolkata Knight Riders",
        "srh":   "Sunrisers Hyderabad",
        "dc":    "Delhi Capitals",
        "dd":    "Delhi Daredevils",
        "pbks":  "Punjab Kings",
        "kxip":  "Kings XI Punjab",
        "rr":    "Rajasthan Royals",
        "lsg":   "Lucknow Super Giants",
        "gt":    "Gujarat Titans",
        "rps":   "Rising Pune Supergiant",
        "gl":    "Gujarat Lions",
        "pwi":   "Pune Warriors India",
        "kochi": "Kochi Tuskers Kerala",
 
        # Metrics
        "sr":    "strike rate",
        "avg":   "average",
        "econ":  "economy rate",
        "eco":   "economy rate",
        "wkts":  "wickets",
        "wkt":   "wicket",
        "rpo":   "runs per over",
 
        # Phases
        "pp":    "powerplay",
 
        # Formats
        "t20":   "T20",
        "ipl":   "IPL",
        "odi":   "ODI",
    }
 
    # ---------------------------------------------------------------------------
    # Player name variants → canonical spelling
    # These are common informal names, nicknames, and misspellings
    # Full resolution still goes through Canonicalizer + DB
    # ---------------------------------------------------------------------------
 
    PLAYER_VARIANTS = {
 
        # Virat Kohli
        "kohli":          "Virat Kohli",
        "virat":          "Virat Kohli",
        "king kohli":     "Virat Kohli",
        "chase master":   "Virat Kohli",
 
        # Rohit Sharma
        "rohit":          "Rohit Sharma",
        "hitman":         "Rohit Sharma",
        "ro":             "Rohit Sharma",
 
        # MS Dhoni
        "dhoni":          "MS Dhoni",
        "msd":            "MS Dhoni",
        "mahi":           "MS Dhoni",
        "captain cool":   "MS Dhoni",
        "thala":          "MS Dhoni",
 
        # Sachin Tendulkar
        "sachin":         "Sachin Tendulkar",
        "tendulkar":      "Sachin Tendulkar",
        "little master":  "Sachin Tendulkar",
        "master blaster": "Sachin Tendulkar",
 
        # Jasprit Bumrah
        "bumrah":         "Jasprit Bumrah",
        "jassi":          "Jasprit Bumrah",
 
        # KL Rahul
        "kl rahul":       "KL Rahul",
        "rahul":          "KL Rahul",
 
        # Shikhar Dhawan
        "dhawan":         "Shikhar Dhawan",
        "gabbar":         "Shikhar Dhawan",
 
        # Hardik Pandya
        "hardik":         "Hardik Pandya",
        "pandya":         "Hardik Pandya",
 
        # Suryakumar Yadav
        "surya":          "Suryakumar Yadav",
        "sky":            "Suryakumar Yadav",
        "suryakumar":     "Suryakumar Yadav",
 
        # AB de Villiers
        "ab":             "AB de Villiers",
        "abv":            "AB de Villiers",
        "mr 360":         "AB de Villiers",
 
        # Ravindra Jadeja
        "jadeja":         "Ravindra Jadeja",
        "sir jadeja":     "Ravindra Jadeja",
        "jaddu":          "Ravindra Jadeja",
 
        # Yuzvendra Chahal
        "chahal":         "Yuzvendra Chahal",
 
        # Bhuvneshwar Kumar
        "bhuvi":          "Bhuvneshwar Kumar",
        "bhuvneshwar":    "Bhuvneshwar Kumar",
 
        # Sunil Narine
        "narine":         "Sunil Narine",
 
        # Gautam Gambhir
        "gambhir":        "Gautam Gambhir",
        "gauti":          "Gautam Gambhir",
 
        # David Warner
        "warner":         "David Warner",
 
        # Chris Gayle
        "gayle":          "Chris Gayle",
        "universe boss":  "Chris Gayle",
 
        # Andre Russell
        "russell":        "Andre Russell",
        "dre russ":       "Andre Russell",
    }
 
    # ---------------------------------------------------------------------------
    # Phrase normalisations — common question patterns
    # ---------------------------------------------------------------------------
 
    PHRASE_NORMALIZATIONS = {
        "best performing":    "best",
        "most successful":    "best",
        "highest scoring":    "top",
        "top scoring":        "top",
        "leading":            "top",
        "death overs":        "death overs",
        "slog overs":         "death overs",
        "last 4 overs":       "death overs",
        "last four overs":    "death overs",
        "final overs":        "death overs",
        "first 6 overs":      "powerplay",
        "first six overs":    "powerplay",
        "opening overs":      "powerplay",
        "middle overs":       "middle overs",
        "in the ipl":         "in IPL",
        "across ipl":         "in IPL",
        "overall in ipl":     "in IPL",
    }
 
    # ---------------------------------------------------------------------------
    # Public rewrite method
    # ---------------------------------------------------------------------------
 
    @classmethod
    def rewrite(cls, question: str) -> dict:
        """
        Rewrite a raw user question into a clean, normalised form.
 
        Parameters
        ----------
        question : raw user question string
 
        Returns
        -------
        {
            "original":    str,   original question unchanged
            "rewritten":   str,   cleaned and normalised question
            "expansions":  list,  list of expansions applied
            "changed":     bool   whether any change was made
        }
        """
 
        if not question or not question.strip():
            return cls._result(
                original=question or "",
                rewritten=question or "",
                expansions=[],
                changed=False
            )
 
        original  = question.strip()
        rewritten = original
        expansions = []
 
        # ── Step 1: Normalise whitespace and strip punctuation edges ─────────
        rewritten = re.sub(r"\s+", " ", rewritten).strip()
        rewritten = rewritten.strip("?!.,;:")
 
        # ── Step 2: Expand phrase normalisations (multi-word first) ─────────
        lower = rewritten.lower()
        for phrase, replacement in sorted(
            cls.PHRASE_NORMALIZATIONS.items(),
            key=lambda x: len(x[0]),
            reverse=True
        ):
            if phrase in lower:
                pattern   = re.compile(re.escape(phrase), re.IGNORECASE)
                rewritten = pattern.sub(replacement, rewritten)
                lower     = rewritten.lower()
                expansions.append(f"'{phrase}' → '{replacement}'")
 
        # ── Step 3: Expand player nicknames and variants ─────────────────────
        # Two guards against doubling:
        # 1. Skip if canonical name already present in question (full match)
        # 2. Freeze search_base after each replacement so sub-strings
        #    inside already-expanded names cannot re-match on later passes
        search_base = rewritten.lower()
        for variant, canonical in sorted(
            cls.PLAYER_VARIANTS.items(),
            key=lambda x: len(x[0]),
            reverse=True
        ):
            # Guard 1 — skip if canonical already fully present
            if canonical.lower() in search_base:
                continue
 
            pattern = re.compile(
                rf"\b{re.escape(variant)}\b",
                re.IGNORECASE
            )
            if pattern.search(search_base):
                rewritten   = pattern.sub(canonical, rewritten)
                search_base = pattern.sub(
                    # Guard 2 — blank matched span so it cannot re-match
                    " " * len(canonical),
                    search_base
                )
                expansions.append(f"'{variant}' → '{canonical}'")
 
        # ── Step 4: Expand abbreviations (whole words only) ──────────────────
        # Use frozen search base — same technique as Step 3
        # Prevents already-expanded player names re-matching abbreviations
        # e.g. "MS" in "MS Dhoni" must not expand after Dhoni is resolved
        abbr_search_base = rewritten.lower()
 
        for abbr, expansion in sorted(
            cls.ABBREVIATIONS.items(),
            key=lambda x: len(x[0]),
            reverse=True
        ):
            pattern = re.compile(
                rf"\b{re.escape(abbr)}\b",
                re.IGNORECASE
            )
            if pattern.search(abbr_search_base):
                rewritten        = pattern.sub(expansion, rewritten)
                abbr_search_base = pattern.sub(
                    " " * len(expansion),
                    abbr_search_base
                )
                expansions.append(f"'{abbr}' → '{expansion}'")
 
        # ── Step 5: Final whitespace cleanup ─────────────────────────────────
        rewritten = re.sub(r"\s+", " ", rewritten).strip()
 
        changed = rewritten.lower() != original.lower()
 
        return cls._result(
            original=original,
            rewritten=rewritten,
            expansions=expansions,
            changed=changed
        )
 
    # ---------------------------------------------------------------------------
    # Result builder
    # ---------------------------------------------------------------------------
 
    @staticmethod
    def _result(
        original:   str,
        rewritten:  str,
        expansions: list,
        changed:    bool
    ) -> dict:
 
        return {
            "original":   original,
            "rewritten":  rewritten,
            "expansions": expansions,
            "changed":    changed
        }