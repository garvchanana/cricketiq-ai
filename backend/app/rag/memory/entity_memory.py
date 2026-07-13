from app.nlp.canonicalization.canonicalizer import (
    Canonicalizer
)
class EntityMemory:

    entities = {}

    @classmethod
    def save_entity(
        cls,
        session_id: str,
        entity_name: str
    ):

        cls.entities[
            session_id
        ] = (

            Canonicalizer
            .canonicalize(
                entity_name
            )
        )

    @classmethod
    def get_entity(
        cls,
        session_id: str
    ):

        return cls.entities.get(
            session_id
        )