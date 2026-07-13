from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Boolean
from sqlalchemy import Text

from app.database.session import Base


class BallByBall(Base):

    __tablename__ = "ball_by_ball"

    id = Column(Integer, primary_key=True, index=True)

    match_id = Column(String(64))

    innings = Column(Integer)

    over_number = Column(Float)

    batting_team = Column(String(100))

    venue = Column(String(200))

    batsman = Column(String(100))

    bowler = Column(String(100))

    non_striker = Column(String(100))

    runs_scored = Column(Integer)

    extras = Column(Integer)

    wicket = Column(Boolean)

    dismissal_type = Column(String(100))

    commentary = Column(Text)