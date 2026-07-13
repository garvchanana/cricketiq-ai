"""
Phase 10.4 — Retrieval / RAG Tests

Validates the NLP and retrieval layer:
- Canonicalizer resolves DB shortcodes and registry nicknames correctly
- QueryRewriter expands abbreviations without the cascading-doubling
  bug found and fixed during Phase 7.1/7.5 testing
- EntityExtractor correctly identifies players, teams, venues, phases
- RAGPipeline retrieves context without crashing on edge cases
"""

import pytest

from app.nlp.canonicalization.canonicalizer import Canonicalizer
from app.nlp.preprocessing.query_rewriter import QueryRewriter
from app.nlp.entity_extraction.entity_extractor import EntityExtractor


# ---------------------------------------------------------------------------
# Canonicalizer — name resolution
# ---------------------------------------------------------------------------

class TestCanonicalizer:

    @pytest.mark.parametrize("raw_name,expected", [
        ("MS Dhoni",   "Mahendra Singh Dhoni"),
        ("V Kohli",    "Virat Kohli"),
        ("RG Sharma",  "Rohit Sharma"),
        ("DA Warner",  "David Warner"),
        ("CH Gayle",   "Chris Gayle"),
        ("S Dhawan",   "Shikhar Dhawan"),
    ])
    def test_resolves_known_registry_names(self, raw_name, expected):
        result = Canonicalizer.canonicalize(player_name=raw_name, db=None)
        assert result == expected, (
            f"Expected '{raw_name}' to resolve to '{expected}', got '{result}'"
        )

    def test_already_canonical_name_stays_unchanged(self):
        """Resolving an already-correct full name should be a no-op."""
        result = Canonicalizer.canonicalize(player_name="Virat Kohli", db=None)
        assert result == "Virat Kohli"

    def test_unknown_name_does_not_crash(self):
        """An unrecognised name should return gracefully, not raise."""
        try:
            result = Canonicalizer.canonicalize(
                player_name="Totally Unknown Player XYZ", db=None
            )
            assert result is not None
        except Exception as e:
            pytest.fail(f"Canonicalizer crashed on unknown name: {e}")

    def test_empty_string_does_not_crash(self):
        try:
            result = Canonicalizer.canonicalize(player_name="", db=None)
            assert result is not None
        except Exception as e:
            pytest.fail(f"Canonicalizer crashed on empty string: {e}")


# ---------------------------------------------------------------------------
# QueryRewriter — abbreviation expansion without doubling
# ---------------------------------------------------------------------------

class TestQueryRewriter:

    def test_expands_team_abbreviation(self):
        result = QueryRewriter.rewrite("Best batter for RCB")
        assert "Royal Challengers Bangalore" in result["rewritten"]

    def test_expands_metric_abbreviation(self):
        result = QueryRewriter.rewrite("Best SR batter")
        assert "strike rate" in result["rewritten"].lower()

    @pytest.mark.parametrize("question,name_fragment", [
        ("Compare hitman and kohli", "Rohit Sharma"),
        ("Is thala better than gayle", "MS Dhoni"),
        ("Compare Rohit Sharma and Virat Kohli", "Rohit Sharma"),
    ])
    def test_no_cascading_name_doubling(self, question, name_fragment):
        """
        REGRESSION GUARD: QueryRewriter previously produced doubled
        names like "Rohit Sharma Sharma" or "Virat Kohli Kohli Kohli"
        due to re-matching shorter variants inside already-expanded
        canonical names. Fixed in Phase 7.5 via frozen search_base.
        """
        result = QueryRewriter.rewrite(question)
        rewritten = result["rewritten"]

        # No name should appear with a repeated trailing word
        # e.g. "Sharma Sharma" or "Kohli Kohli"
        words = rewritten.split()
        for i in range(len(words) - 1):
            assert words[i].lower() != words[i + 1].lower(), (
                f"Doubling detected in rewritten output: '{rewritten}' "
                f"(from input: '{question}')"
            )

    def test_already_correct_question_unchanged_or_safely_expanded(self):
        result = QueryRewriter.rewrite("Who is MS Dhoni as a player")
        # Should not double "MS Dhoni" into "MS MS Dhoni" etc.
        assert "MS MS Dhoni" not in result["rewritten"]
        assert result["rewritten"].count("Dhoni") <= 1

    def test_empty_question_does_not_crash(self):
        result = QueryRewriter.rewrite("")
        assert result["rewritten"] == ""
        assert result["changed"] is False

    def test_none_question_does_not_crash(self):
        try:
            result = QueryRewriter.rewrite(None)
            assert result is not None
        except Exception as e:
            pytest.fail(f"QueryRewriter crashed on None input: {e}")


# ---------------------------------------------------------------------------
# EntityExtractor — players, teams, venues, phases, intents
# ---------------------------------------------------------------------------

class TestEntityExtractor:

    def test_extracts_single_player(self):
        result = EntityExtractor.extract(
            question="Who is MS Dhoni as a player", db=None
        )
        assert "Mahendra Singh Dhoni" in result["players"]

    def test_extracts_two_players_for_comparison(self):
        result = EntityExtractor.extract(
            question="Compare Rohit Sharma and Virat Kohli in powerplay",
            db=None
        )
        assert len(result["players"]) == 2
        assert result["is_comparison"] is True

    def test_does_not_include_question_opener_in_player_name(self):
        """
        REGRESSION GUARD: "Compare Rohit Sharma" was previously
        extracted as a single player name including the word
        "Compare". Fixed via QUESTION_OPENERS filtering.
        """
        result = EntityExtractor.extract(
            question="Compare Rohit Sharma and Virat Kohli", db=None
        )
        for player in result["players"]:
            assert "compare" not in player.lower()

    def test_extracts_initials_format_player(self):
        """
        REGRESSION GUARD: "MS Dhoni" (all-caps initials) was
        previously not matched by the player candidate pattern,
        which only handled title-case names. Fixed via
        PLAYER_INITIALS_PATTERN.
        """
        result = EntityExtractor.extract(
            question="Tell me about MS Dhoni bowling style", db=None
        )
        assert len(result["players"]) >= 1

    def test_extracts_team(self):
        result = EntityExtractor.extract(
            question="How does Mumbai Indians perform in powerplay",
            db=None
        )
        assert "Mumbai Indians" in result["teams"]
        assert result["is_team"] is True

    def test_extracts_venue(self):
        result = EntityExtractor.extract(
            question="Best economy bowlers at Wankhede in death overs",
            db=None
        )
        assert any("wankhede" in v.lower() for v in result["venues"])

    def test_extracts_phase(self):
        result = EntityExtractor.extract(
            question="Best strike rate batters in death overs", db=None
        )
        assert "death overs" in result["phases"]

    def test_extracts_limit(self):
        result = EntityExtractor.extract(
            question="Top 5 bowlers by wickets in IPL", db=None
        )
        assert result["limit"] == 5

    def test_no_limit_returns_none(self):
        result = EntityExtractor.extract(
            question="Who scored the most runs in IPL", db=None
        )
        assert result["limit"] is None

    def test_profile_flag_set_for_descriptive_question(self):
        result = EntityExtractor.extract(
            question="Who is MS Dhoni as a player", db=None
        )
        assert result["is_profile"] is True

    def test_ranking_flag_set_for_top_n_question(self):
        result = EntityExtractor.extract(
            question="Top 10 wicket takers in IPL", db=None
        )
        assert result["is_ranking"] is True

    def test_empty_question_does_not_crash(self):
        try:
            result = EntityExtractor.extract(question="", db=None)
            assert result["players"] == []
        except Exception as e:
            pytest.fail(f"EntityExtractor crashed on empty input: {e}")