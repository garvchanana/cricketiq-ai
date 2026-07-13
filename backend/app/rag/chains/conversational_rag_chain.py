from app.rag.chains.rag_pipeline import (
    RAGPipeline
)

from app.rag.memory.conversation_memory import (
    ConversationMemory
)

from app.rag.chains.conversation_context_builder import (
    ConversationContextBuilder
)

from app.llm.prompt_builder import (
    PromptBuilder
)

from app.llm.response_parser import (
    ResponseGenerator
)
from app.rag.memory.entity_memory import (
    EntityMemory
)

from app.rag.retriever.entity_resolver import (
    EntityResolver
)
from app.nlp.canonicalization.canonicalizer import (
    Canonicalizer
)

class ConversationalRAGChain:

    @staticmethod
    def chat(
        session_id: str,
        query: str,
        db=None
    ):
        query = (
            EntityResolver
            .resolve(
                session_id=session_id,
                query=query
            )
        )

        display_query = (
            Canonicalizer
            .canonicalize_text(
                query,
                db=db
            )
        )

        history = (
            ConversationMemory
            .get_history(
                session_id
            )
        )

        conversation_context = (

            ConversationContextBuilder
            .build_conversation_context(
                history
            )
        )

        rag_result = (
            RAGPipeline
            .generate_context(
                query=query,
                db=db
            )
        )

        retrieved_context = (
            rag_result.get(
                "context",
                ""
            )
        )

        prompt = (
            PromptBuilder
            .build_cricket_prompt(

                query=display_query,

                context=retrieved_context,

                conversation_history=
                conversation_context
            )
        )

        answer = (
            ResponseGenerator
            .generate_response(
                prompt
            )
        )

        retrieved_docs = (
            rag_result.get(
                "retrieved_docs",
                []
            )
        )

        if (
            retrieved_docs
            and
            "not contain enough information"
            not in answer.lower()
        ):

            top_player = (
                retrieved_docs[0]
                .get(
                    "player_name",
                    ""
                )
            )


            if top_player:

                EntityMemory.save_entity(

                    session_id=session_id,

                    entity_name=top_player
                )

        ConversationMemory.add_message(

            session_id=session_id,

            role="user",

            content=display_query
        )

        ConversationMemory.add_message(

            session_id=session_id,

            role="assistant",

            content=answer
        )

        return {

            "session_id":
            session_id,

            "query":
            display_query,
            "resolved_query":
            display_query,

            "answer":
            answer,

            "conversation_history":
            ConversationMemory
            .get_history(
                session_id
            )
        }
