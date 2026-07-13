from app.database.session import engine
from app.database.session import Base

from app.database.models import *


def init_db():
    Base.metadata.create_all(bind=engine)