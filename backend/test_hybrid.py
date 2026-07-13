import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.agents.hybrid_composer import HybridComposer

db = SessionLocal()

result = HybridComposer.compose(
    question="Is Rohit Sharma better than Virat Kohli overall in IPL",
    players=["Rohit Sharma", "Virat Kohli"],
    db=db
)

print("ROUTE:      ", result["route"])
print("SQL ANSWER: ", result["sql_answer"])
print("RAG ERROR:  ", result["rag_error"])
print("SQL ERROR:  ", result["sql_error"])
print()
print("FINAL ANSWER:")
print(result["answer"])
db.close()
