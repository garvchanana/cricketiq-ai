import sys
sys.path.insert(0, ".")
from app.database.session import SessionLocal
from app.analytics.summarization.final_answer_agent import FinalAnswerAgent

db = SessionLocal()

print("=== Test 1: Player Profile ===")
entities = {
    "players": ["MS Dhoni"], "phases": [], "venues": [],
    "teams": [], "is_comparison": False, "is_profile": True,
    "is_ranking": False, "is_team": False, "is_venue": False
}
result = FinalAnswerAgent.answer(
    question="Who is MS Dhoni as a player",
    entities=entities,
    db=db
)
print("Agents:", result["agents_called"])
print("Answer:", result["answer"][:300])
print()

print("=== Test 2: Comparison ===")
entities = {
    "players": ["V Kohli", "RG Sharma"], "phases": [], "venues": [],
    "teams": [], "is_comparison": True, "is_profile": False,
    "is_ranking": False, "is_team": False, "is_venue": False
}
result = FinalAnswerAgent.answer(
    question="Compare Rohit Sharma and Virat Kohli in IPL",
    entities=entities,
    db=db
)
print("Agents:", result["agents_called"])
print("Answer:", result["answer"][:300])
print()

print("=== Test 3: Phase Question ===")
entities = {
    "players": [], "phases": ["death overs"], "venues": [],
    "teams": [], "is_comparison": False, "is_profile": False,
    "is_ranking": True, "is_team": False, "is_venue": False
}
result = FinalAnswerAgent.answer(
    question="How does IPL batting look in death overs",
    entities=entities,
    db=db
)
print("Agents:", result["agents_called"])
print("Answer:", result["answer"][:300])

db.close()