from app.nlp.preprocessing.query_rewriter import QueryRewriter

tests = [
    "Who is MS Dhoni as a player",
    "Is Rohit Sharma better than Virat Kohli in IPL",
    "Compare Rohit Sharma and Virat Kohli in powerplay",
    "How is Virat Kohli performing",
]

for q in tests:
    r = QueryRewriter.rewrite(q)
    status = "OK" if r["rewritten"].count("Sharma") <= 1 and r["rewritten"].count("Kohli") <= 1 else "FAIL"
    print(f"[{status}] IN:  {q}")
    print(f"       OUT: {r['rewritten']}")
    print()
