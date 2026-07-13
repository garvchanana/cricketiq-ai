from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy import String

from app.database.session import Base


class MatchMomentumStats(Base):

    __tablename__ = "match_momentum_stats"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    match_id = Column(String(64))

    innings = Column(Integer)

    over_number = Column(Float)

    total_runs = Column(Integer)

    wickets = Column(Integer)

    boundaries = Column(Integer)

    dot_balls = Column(Integer)

    momentum_score = Column(Float)

    pressure_score = Column(Float)