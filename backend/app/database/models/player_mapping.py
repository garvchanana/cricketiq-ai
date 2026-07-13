from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from app.database.session import Base


class PlayerMapping(Base):

    __tablename__ = "player_mappings"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    raw_name = Column(
        String(100),
        unique=True
    )

    canonical_name = Column(
        String(100)
    )