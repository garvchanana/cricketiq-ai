import sys
sys.path.insert(0, ".")
from app.database.session import SessionLocal
from app.analytics.player_analysis.player_analyst import PlayerAnalyst

db = SessionLocal()

print("=== Single Player Profile ===")
profile = PlayerAnalyst.get_player_profile("MS Dhoni", db=db)
print("Found:    ", profile["found"])
print("Canonical:", profile["canonical_name"])
print("Role:     ", profile["role"])
print("Batting:  ", profile["batting"])
print("Ranking:  ", profile["ranking"])
print("Narrative:", profile["narrative"])
print()

print("=== Player Comparison ===")
comparison = PlayerAnalyst.compare_players("Rohit Sharma", "Virat Kohli", db=db)
print("Both found:", comparison["both_found"])
print("Narrative: ", comparison["comparison_narrative"])
print()

print("=== Top 5 Players ===")
top = PlayerAnalyst.get_top_players(limit=5, db=db)
for p in top["players"]:
    print(f"  {p['player_name']} | {p['role']} | Rating: {p['ranking_score']}")

db.close()