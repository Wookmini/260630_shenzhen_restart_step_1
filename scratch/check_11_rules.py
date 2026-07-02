import json

rules = json.load(open('data/may_learned_rules.json', encoding='utf-8'))
print(rules.get('11'))
