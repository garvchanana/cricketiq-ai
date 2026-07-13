from app.nlp.preprocessing.query_rewriter import QueryRewriter

tests = [
    'Who is the best SR batter for RCB?',
    'Compare hitman and kohli in pp',
    'Top bowlers by econ in death overs',
    'Is thala better than gayle in ipl?',
]

for q in tests:
    result = QueryRewriter.rewrite(q)
    print('IN: ', result['original'])
    print('OUT:', result['rewritten'])
    print('EXP:', result['expansions'])
    print()
