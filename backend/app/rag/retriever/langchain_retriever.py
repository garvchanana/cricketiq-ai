from app.rag.retriever.retrieval_service import (
    RetrievalService
)


class LangChainRetriever:

    @staticmethod
    def retrieve(
        query: str,
        top_k=5,
        db=None
    ):

        results = (
            RetrievalService
            .retrieve_context(
                query=query,
                top_k=top_k,
                db=db
            )
        )

        return results
