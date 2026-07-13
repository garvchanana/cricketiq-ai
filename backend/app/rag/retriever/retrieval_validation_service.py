import json

from app.database.models.player_mapping import (
    PlayerMapping
)
from app.nlp.canonicalization.player_registry import (
    PLAYER_REGISTRY
)
from app.rag.retriever.retrieval_service import (
    RetrievalService
)


class RetrievalValidationService:

    @staticmethod
    def _result_contains_raw_name(
        result,
        raw_name,
        canonical_name
    ):

        if raw_name == canonical_name:

            return False

        serialized = json.dumps(
            result,
            ensure_ascii=False
        )

        return raw_name in serialized

    @classmethod
    def _validate_case(
        cls,
        db,
        query,
        expected_canonical_name,
        raw_name=None
    ):

        results = (
            RetrievalService
            .retrieve_context(
                query=query,
                top_k=5,
                db=db
            )
        )

        top_result = (
            results[0]
            if results
            else {}
        )

        checks = {

            "has_results":
            bool(results),

            "top_player_is_expected":
            top_result.get(
                "player_name"
            ) == expected_canonical_name,

            "canonical_name_is_expected":
            top_result.get(
                "canonical_name"
            ) == expected_canonical_name,

            "exact_retrieval_first":
            top_result.get(
                "retrieval_source"
            ) == "exact",

            "raw_name_hidden":
            not cls._result_contains_raw_name(
                top_result,
                raw_name or "",
                expected_canonical_name
            )
        }

        return {

            "query":
            query,

            "expected_player":
            expected_canonical_name,

            "actual_player":
            top_result.get(
                "player_name"
            ),

            "retrieval_source":
            top_result.get(
                "retrieval_source"
            ),

            "checks":
            checks,

            "passed":
            all(
                checks.values()
            )
        }

    @staticmethod
    def _core_cases():

        cases = []

        for raw_name, canonical_name in PLAYER_REGISTRY.items():

            cases.append({
                "query": raw_name,
                "raw_name": raw_name,
                "canonical_name": canonical_name
            })

            cases.append({
                "query": canonical_name,
                "raw_name": raw_name,
                "canonical_name": canonical_name
            })

        return cases

    @staticmethod
    def _mapping_cases(
        db,
        limit=None
    ):

        query = (
            db.query(
                PlayerMapping
            )
            .order_by(
                PlayerMapping.raw_name
            )
        )

        if limit:

            query = query.limit(
                limit
            )

        mappings = query.all()

        cases = []

        for mapping in mappings:

            cases.append({
                "query": mapping.raw_name,
                "raw_name": mapping.raw_name,
                "canonical_name": mapping.canonical_name
            })

            cases.append({
                "query": mapping.canonical_name,
                "raw_name": mapping.raw_name,
                "canonical_name": mapping.canonical_name
            })

        return cases

    @classmethod
    def validate(
        cls,
        db,
        include_all_mappings=False,
        mapping_limit=None
    ):

        cases = cls._core_cases()

        if include_all_mappings:

            cases.extend(
                cls._mapping_cases(
                    db=db,
                    limit=mapping_limit
                )
            )

        seen = set()
        unique_cases = []

        for case in cases:

            key = (
                case["query"],
                case["canonical_name"]
            )

            if key not in seen:

                seen.add(
                    key
                )

                unique_cases.append(
                    case
                )

        results = [
            cls._validate_case(
                db=db,
                query=case["query"],
                expected_canonical_name=case[
                    "canonical_name"
                ],
                raw_name=case[
                    "raw_name"
                ]
            )
            for case in unique_cases
        ]

        failed = [
            result
            for result in results
            if not result[
                "passed"
            ]
        ]

        return {

            "total_cases":
            len(results),

            "passed_cases":
            len(results) - len(failed),

            "failed_cases":
            len(failed),

            "passed":
            not failed,

            "failures":
            failed,

            "results":
            results
        }
