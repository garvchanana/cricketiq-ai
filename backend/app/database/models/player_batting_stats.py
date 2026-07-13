from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy import String

from app.database.session import Base


class PlayerBattingStats(Base):

    __tablename__ = "player_batting_stats"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    batsman = Column(String(100))

    total_runs = Column(Integer)

    balls_faced = Column(Integer)

    strike_rate = Column(Float)

    total_fours = Column(Integer)

    total_sixes = Column(Integer)

    dot_balls = Column(Integer)

    batting_average = Column(Float)