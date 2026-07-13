from fastapi import APIRouter

from app.nlp.embeddings.embedding_service import (
    EmbeddingService
)

from app.rag.chains.chunk_generation_service import (
    ChunkGenerationService
)

from fastapi import Depends

from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db

from app.rag.vectorstore.vector_indexing_service import (
    VectorIndexingService
)

from app.rag.retriever.retrieval_service import (
    RetrievalService
)

from app.rag.chains.rag_pipeline import (
    RAGPipeline
)

from app.rag.chains.full_rag_chain import (
    FullRAGChain
)

from app.rag.chains.conversational_rag_chain import (
    ConversationalRAGChain
)
from app.nlp.preprocessing.query_rewriter import (
    QueryRewriter
)
from app.rag.retriever.query_intent_detector import (
    QueryIntentDetector
)
from app.nlp.canonicalization.canonicalizer import (
    Canonicalizer
)
from app.rag.retriever.retrieval_validation_service import (
    RetrievalValidationService
)

router = APIRouter(
    prefix="/rag",
    tags=["RAG"]
)


@router.get("/health")
def rag_health():

    return {
        "message": "RAG Running"
    }


@router.post("/embedding-test")
def embedding_test():

    sample_text = (
        "Virat Kohli is one of the best IPL batters."
    )

    embedding = (
        EmbeddingService
        .generate_embedding(
            sample_text
        )
    )

    return {
        "embedding_dimension": len(
            embedding
        ),
        "sample_values": embedding[:5]
    }

@router.post("/generate-player-chunks")
def generate_player_chunks(
    db: Session = Depends(get_db)
):

    result = (
        ChunkGenerationService
        .generate_player_chunks(
            db=db
        )
    )

    return result

@router.post("/build-player-index")
def build_player_index(
    db: Session = Depends(get_db)
):

    result = (
        VectorIndexingService
        .build_player_index(
            db=db
        )
    )

    return result
@router.get("/search")
def semantic_search(
    query: str,
    db: Session = Depends(get_db)
):

    rewritten_query = (
        Canonicalizer
        .canonicalize_text(
            QueryRewriter.rewrite(
                query or ""
            ),
            db=db
        )
    )
    intent = (
        QueryIntentDetector
        .detect_intent(
            query
        )
    )

    results = (
        RetrievalService
        .retrieve_context(
            query=query,
            db=db
        )
    )

    return {

        "original_query":
        query,

        "rewritten_query":
        rewritten_query,

        "intent":
        intent,

        "results":
        results
    }

@router.get("/rag-context")
def generate_rag_context(
    query: str,
    db: Session = Depends(get_db)
):

    result = (
        RAGPipeline
        .generate_context(
            query=query,
            db=db
        )
    )

    return result

@router.get("/ask")
def ask_cricket_ai(
    query: str,
    db: Session = Depends(get_db)
):

    result = (
        FullRAGChain
        .ask_cricket_ai(
            query=query,
            db=db
        )
    )

    return result

@router.get("/chat")
def cricket_chatbot(
    session_id: str,
    query: str,
    db: Session = Depends(get_db)
):

    result = (
        ConversationalRAGChain
        .chat(
            session_id=session_id,
            query=query,
            db=db
        )
    )

    return result


@router.get("/validate-retrieval")
def validate_retrieval(
    include_all_mappings: bool = False,
    mapping_limit: int | None = None,
    db: Session = Depends(get_db)
):

    return (
        RetrievalValidationService
        .validate(
            db=db,
            include_all_mappings=include_all_mappings,
            mapping_limit=mapping_limit
        )
    )