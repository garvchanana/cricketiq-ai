from app.agents.intent_router import IntentRouter

tests = [
    ("Who is MS Dhoni as a player",                    "RAG"),
    ("Top 5 bowlers by wickets in IPL",                "SQL"),
    ("Best economy bowlers at Wankhede in death overs","SQL"),
    ("How does Mumbai Indians perform in powerplay",   "SQL"),
    ("How many runs did V Kohli score in IPL",         "SQL"),
    ("Compare Rohit Sharma and Virat Kohli in powerplay", "SQL"),
    ("Is Rohit Sharma better than Virat Kohli overall","HYBRID"),
    ("Why is MS Dhoni so effective in death overs",    "HYBRID"),
    ("Tell me about Jasprit Bumrah bowling style",     "RAG"),
    ("Which venue has the highest average score",      "SQL"),
    ("Which team wins most powerplay battles",         "SQL"),
    ("Explain Virat Kohli batting technique",          "RAG"),
]

SEP = "-" * 65
passed = 0
failed = 0

for question, expected in tests:
    result = IntentRouter.route(question=question, db=None)
    actual = result["route"]
    status = "PASS" if actual == expected else "FAIL"
    if status == "PASS":
        passed += 1
    else:
        failed += 1
    print(SEP)
    print(f"[{status}] {question}")
    print(f"  Expected : {expected}")
    print(f"  Got      : {actual}")
    print(f"  Reason   : {result['reasoning']}")

print(SEP)
print(f"Results: {passed} passed / {failed} failed / {len(tests)} total")
print(SEP)
