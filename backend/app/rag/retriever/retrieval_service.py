"""
Phase 12.3 (final fix) — retrieval_service.py

Fixed: VectorIndexingService.vector_store.similarity_search(...)
       -> VectorIndexingService.get_store().search(...)

Root cause: Phase 11.5 rewrote FAISSStore/VectorIndexingService with
a module-level singleton pattern (get_store() accessor, search()
method) but this file was never updated to match, causing a production
AttributeError crash on every RAG-routed question.
"""

from app.nlp.embeddings.embedding_service import EmbeddingService
from app.rag.vectorstore.vector_indexing_service import VectorIndexingService
from app.rag.retriever.reliability_filter import ReliabilityFilter
from app.nlp.preprocessing.query_rewriter import QueryRewriter
from app.rag.retriever.hybrid_ranker import HybridRanker
from app.rag.retriever.query_intent_detector import QueryIntentDetector
from app.rag.retriever.semantic_reranker import SemanticReranker
from app.rag.retriever.confidence_scorer import ConfidenceScorer
from app.nlp.canonicalization.canonicalizer import Canonicalizer
from app.rag.retriever.entity_retriever import EntityRetriever


class RetrievalService:

    @staticmethod
    def _strip_private_fields(results):

        public_results = []

        for result in results:
            public_result = result.copy()
            public_result.pop("raw_player_name", None)
            public_results.append(public_result)

        return public_results

    @staticmethod
    def _build_exact_result(player, db=None):

        canonical_name = Canonicalizer.canonicalize(
            player.player_name,
            db=db
        )

        chunk = f"""
        Player Name:
        {canonical_name}

        Canonical Name:
        {canonical_name}

        Role:
        {player.role}

        Batting Summary:
        {player.batting_summary}

        Bowling Summary:
        {player.bowling_summary}

        Intelligence Summary:
        {player.intelligence_summary}
        """

        chunk = Canonicalizer.canonicalize_text(chunk, db=db)

        return {
            "raw_player_name":   player.player_name,
            "player_name":       canonical_name,
            "canonical_name":    canonical_name,
            "role":              player.role,
            "overall_rating":    float(player.overall_rating or 0),
            "chunk":             chunk,
            "retrieval_rank":    1,
            "distance":          0.0,
            "retrieval_source":  "exact",
            "reliability_score": 999.0,
            "hybrid_score":      999.0,
            "semantic_score":    999.0,
            "confidence_score":  999.0,
            "confidence_label":  "High"
        }

    @staticmethod
    def retrieve_context(
        query: str,
        top_k=5,
        db=None
    ):

        exact_result = None

        if db is not None:
            exact_player = EntityRetriever.find_player_for_query(
                db=db,
                query=query
            )

            if exact_player:
                exact_result = RetrievalService._build_exact_result(
                    exact_player,
                    db=db
                )

        rewritten_query = QueryRewriter.rewrite(query)

        query_embedding = EmbeddingService.generate_embedding(
            rewritten_query["rewritten"]
        )

        semantic_top_k = (
            top_k if exact_result is None else top_k + 3
        )

        # ── Phase 12.3 fix — corrected FAISSStore access pattern ──────────
        results = VectorIndexingService.get_store().search(
            query_embedding=query_embedding,
            top_k=semantic_top_k
        )

        for result in results:

            raw_player_name = (
                result.get("raw_player_name")
                or result.get("player_name")
            )

            result["canonical_name"] = Canonicalizer.canonicalize(
                raw_player_name,
                db=db
            )

            result["raw_player_name"] = raw_player_name
            result["player_name"] = result["canonical_name"]

            chunk = result.get("chunk", "")

            if raw_player_name and raw_player_name != result["canonical_name"]:
                chunk = chunk.replace(
                    raw_player_name,
                    result["canonical_name"]
                )

            result["chunk"] = Canonicalizer.canonicalize_text(chunk, db=db)

            result["retrieval_source"] = result.get(
                "retrieval_source", "semantic"
            )

            result["reliability_score"] = (
                ReliabilityFilter.calculate_reliability_score(result)
            )

        for result in results:
            result["hybrid_score"] = HybridRanker.calculate_hybrid_score(result)

        results.sort(key=lambda x: x["hybrid_score"], reverse=True)

        intent = QueryIntentDetector.detect_intent(query)

        results = SemanticReranker.rerank(results=results, intent=intent)

        for result in results:
            confidence = ConfidenceScorer.calculate_confidence(result)
            result["confidence_score"] = confidence
            result["confidence_label"] = ConfidenceScorer.confidence_label(
                confidence
            )

        if exact_result is not None:
            filtered_results = [
                result for result in results
                if result.get("raw_player_name") != exact_result.get("raw_player_name")
            ]
            results = [exact_result] + filtered_results

        return RetrievalService._strip_private_fields(results[:top_k])