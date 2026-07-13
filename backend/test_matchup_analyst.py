import sys
sys.path.insert(0, '.')
from app.database.session import SessionLocal
from app.database.models.batter_bowler_matchups import BatterBowlerMatchup
db = SessionLocal()
r = db.query(BatterBowlerMatchup).first()
print('batsman:', r.batsman)
print('bowler:', r.bowler)
db.close()