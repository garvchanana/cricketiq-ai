from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy import String

from app.database.session import Base


class TeamStats(Base):

    __tablename__ = "team_stats"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    team_name = Column(
        String(100)
    )

    total_runs = Column(
        Integer
    )

    total_balls = Column(
        Integer
    )

    run_rate = Column(
        Float
    )

    total_boundaries = Column(
        Integer
    )

    dot_balls = Column(
        Integer
    )

    aggression_index = Column(
        Float
    )

    pressure_index = Column(
        Float
    )