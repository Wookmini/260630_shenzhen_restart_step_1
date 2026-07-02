import json

rules = json.load(open('data/may_learned_rules.json', encoding='utf-8'))
pairs = set()
for k, v in rules.items():
    for item in v:
        pairs.add((item.get('대계정'), item.get('소계정')))

for p in sorted(list(pairs), key=lambda x: (str(x[0]), str(x[1]))):
    print(p)
