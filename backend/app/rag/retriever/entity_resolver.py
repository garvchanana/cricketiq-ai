from app.rag.memory.entity_memory import (
    EntityMemory
)


class EntityResolver:

    PRONOUNS = [

        "his",
        "him",

        "her",

        "their",
        "them"
    ]

    @classmethod
    def resolve(
        cls,
        session_id: str,
        query: str
    ):

        lower_query = (
            query.lower()
        )

        last_entity = (
            EntityMemory
            .get_entity(
                session_id
            )
        )

        if not last_entity:

            return query

        for pronoun in cls.PRONOUNS:

            if pronoun in lower_query:

                return query.replace(
                    pronoun,
                    last_entity
                )

        return query