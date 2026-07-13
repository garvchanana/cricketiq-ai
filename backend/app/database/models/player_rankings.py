from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy import String

from app.database.session import Base


class PlayerRankings(Base):

    __tablename__ = "player_rankings"

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

    ranking_score = Column(
        Float
    )

    total_runs = Column(
        Integer
    )

    strike_rate = Column(
        Float
    )

    total_wickets = Column(
        Integer
    )

    economy_rate = Column(
        Float
    )