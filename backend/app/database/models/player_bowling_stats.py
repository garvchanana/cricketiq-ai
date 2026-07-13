from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy import String

from app.database.session import Base


class PlayerBowlingStats(Base):

    __tablename__ = "player_bowling_stats"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    bowler = Column(String(100))

    balls_bowled = Column(Integer)

    runs_conceded = Column(Integer)

    wickets = Column(Integer)

    economy_rate = Column(Float)

    bowling_strike_rate = Column(Float)

    dot_balls = Column(Integer)

    bowling_average = Column(Float)