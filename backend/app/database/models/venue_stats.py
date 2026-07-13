from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy import String

from app.database.session import Base


class VenueStats(Base):

    __tablename__ = "venue_stats"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    venue = Column(
        String(200)
    )

    total_matches = Column(
        Integer
    )

    total_runs = Column(
        Integer
    )

    total_balls = Column(
        Integer
    )

    average_run_rate = Column(
        Float
    )

    total_boundaries = Column(
        Integer
    )

    dot_ball_percentage = Column(
        Float
    )

    venue_type = Column(
        String(50)
    )