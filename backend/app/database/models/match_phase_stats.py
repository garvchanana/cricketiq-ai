from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy import String

from app.database.session import Base


class MatchPhaseStats(Base):

    __tablename__ = "match_phase_stats"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    phase = Column(String(50))

    total_runs = Column(Integer)

    total_balls = Column(Integer)

    run_rate = Column(Float)

    wickets = Column(Integer)

    dot_balls = Column(Integer)

    boundaries = Column(Integer)