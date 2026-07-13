from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import DateTime
 
from datetime import datetime
 
from app.database.session import Base
 
 
class Player(Base):
 
    __tablename__ = "players"
 
    player_uuid       = Column(String(64), primary_key=True)
    api_player_id     = Column(String(64))
 
    player_name       = Column(String(100))
    standardized_name = Column(String(100))
 
    country           = Column(String(50))
    role              = Column(String(50))
 
    batting_style     = Column(String(50))
    bowling_style     = Column(String(50))
 
    created_at        = Column(DateTime, default=datetime.utcnow)