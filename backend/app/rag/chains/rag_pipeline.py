from app.rag.retriever.langchain_retriever import (
    LangChainRetriever
)

from app.rag.chains.context_builder import (
    ContextBuilder
)
from app.nlp.canonicalization.canonicalizer import (
    Canonicalizer
)


class RAGPipeline:

    @staticmethod
    def generate_context(
        query: str,
        db=None
    ):

        retrieved_docs = (

            LangChainRetriever
            .retrieve(
                query=query,
                db=db
            )
        )

        context = (
            ContextBuilder
            .build_context(
                retrieved_docs,
                db=db
            )
        )

        return {

            "query":
            Canonicalizer
            .canonicalize_text(
                query,
                db=db
            ),

            "retrieved_docs":
            retrieved_docs,

            "context":
            context
        }
