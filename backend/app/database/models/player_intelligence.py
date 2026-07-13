from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy import String
from sqlalchemy import Text

from app.database.session import Base


class PlayerIntelligence(Base):

    __tablename__ = "player_intelligence"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    player_name = Column(
        String(100)
    )

    role = Column(
        String(50)
    )

    batting_summary = Column(
        Text
    )

    bowling_summary = Column(
        Text
    )

    overall_rating = Column(
        Float
    )

    intelligence_summary = Column(
        Text
    )