from app.database.session import SessionLocal

from app.database.models.player_mapping import (
    PlayerMapping
)


mappings = [
    {
        "raw_name": "DA Warner",
        "canonical_name": "David Warner"
    },
    {
        "raw_name": "V Kohli",
        "canonical_name": "Virat Kohli"
    },
    {
        "raw_name": "MS Dhoni",
        "canonical_name": "Mahendra Singh Dhoni"
    },
    {
        "raw_name": "S Dhawan",
        "canonical_name": "Shikhar Dhawan"
    }
]


def seed():

    db = SessionLocal()

    for item in mappings:

        exists = (
            db.query(PlayerMapping)
            .filter(
                PlayerMapping.raw_name
                == item["raw_name"]
            )
            .first()
        )

        if not exists:

            mapping = PlayerMapping(
                raw_name=item["raw_name"],
                canonical_name=item[
                    "canonical_name"
                ]
            )

            db.add(mapping)

    db.commit()

    db.close()


if __name__ == "__main__":
    seed()