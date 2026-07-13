import sys
sys.path.insert(0, ".")
from app.database.session import SessionLocal
from app.analytics.match_analysis.match_analyst import MatchAnalyst

db = SessionLocal()

print("=== Team Record — Mumbai Indians ===")
result = MatchAnalyst.get_team_record("Mumbai Indians", db=db)
print("Found:    ", result["found"])
print("Narrative:", result.get("narrative", ""))
print()

print("=== Team Record — Chennai ===")
result = MatchAnalyst.get_team_record("Chennai", db=db)
print("Found:    ", result["found"])
print("Narrative:", result.get("narrative", ""))

db.close()