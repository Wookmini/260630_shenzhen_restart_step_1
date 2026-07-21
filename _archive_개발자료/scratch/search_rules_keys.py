import json

rules = json.load(open('data/may_learned_rules.json', encoding='utf-8'))
for k in rules:
    if '61' in k or '62' in k or '7' in k or '07' in k:
        print(f"Key: {k} -> {rules[k]}")
