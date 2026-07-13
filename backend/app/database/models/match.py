from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import DateTime

from app.database.session import Base


class Match(Base):
    __tablename__ = "matches"

    match_id = Column(String(64), primary_key=True)

    team1 = Column(String(100))
    team2 = Column(String(100))

    venue = Column(String(200))

    match_type = Column(String(20))

    winner = Column(String(100))
    toss_winner = Column(String(100))

    match_date = Column(DateTime)