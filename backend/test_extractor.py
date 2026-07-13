from app.nlp.entity_extraction.entity_extractor import EntityExtractor
 
tests = [
    # Basic cases
    "Compare Rohit Sharma and Virat Kohli in powerplay",
    "Top 5 bowlers by wickets in IPL",
    "Who is MS Dhoni as a player",
    "Best economy bowlers at Wankhede in death overs",
    "How does Mumbai Indians perform in powerplay",
 
    # Registry name resolution
    "How many runs did V Kohli score in IPL",
    "What is DA Warner strike rate in powerplay",
    "Compare RG Sharma and CH Gayle",
 
    # Venue questions
    "Which venue has the highest average score in IPL",
    "Best batting venue at Eden Gardens",
 
    # Team questions
    "How does Chennai Super Kings perform in death overs",
    "Which team wins most powerplay battles",
 
    # Phase + metric
    "Best strike rate batters in death overs",
    "Top economy bowlers in powerplay",
 
    # Profile
    "Tell me about Jasprit Bumrah bowling style",
    "Explain Virat Kohli batting technique",
 
    # Hybrid — needs both RAG and SQL
    "Is Rohit Sharma better than Virat Kohli overall in IPL",
    "Why is MS Dhoni so effective in death overs",
]
 
SEP = "-" * 60
 
for q in tests:
    result = EntityExtractor.extract(question=q, db=None)
    print(SEP)
    print("Q:       ", q)
    print("Players: ", result["players"])
    print("Teams:   ", result["teams"])
    print("Venues:  ", result["venues"])
    print("Phases:  ", result["phases"])
    print("Metrics: ", result["metrics"])
    print("Intents: ", result["intents"])
    print("Limit:   ", result["limit"])
    print("Flags:   ",
          "comparison=" + str(result["is_comparison"]),
          "| profile=" + str(result["is_profile"]),
          "| ranking=" + str(result["is_ranking"]),
          "| is_team=" + str(result["is_team"]),
          "| is_venue=" + str(result["is_venue"]),
    )
 
print(SEP)