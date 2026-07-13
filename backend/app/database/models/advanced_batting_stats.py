from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy import String

from app.database.session import Base


class AdvancedBattingStats(Base):

    __tablename__ = "advanced_batting_stats"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    batsman = Column(String(100))

    total_boundaries = Column(Integer)

    boundary_percentage = Column(Float)

    dot_ball_percentage = Column(Float)

    aggression_index = Column(Float)

    pressure_release_index = Column(Float)