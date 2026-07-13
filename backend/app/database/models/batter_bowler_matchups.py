from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy import String

from app.database.session import Base


class BatterBowlerMatchup(Base):

    __tablename__ = "batter_bowler_matchups"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    batsman = Column(
        String(100)
    )

    bowler = Column(
        String(100)
    )

    total_runs = Column(
        Integer
    )

    balls_faced = Column(
        Integer
    )

    dismissals = Column(
        Integer
    )

    strike_rate = Column(
        Float
    )

    dot_ball_percentage = Column(
        Float
    )

    dominance_index = Column(
        Float
    )