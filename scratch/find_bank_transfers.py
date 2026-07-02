import json

rules = json.load(open('data/may_learned_rules.json', encoding='utf-8'))
targets = ['25', '30', '37', '45', '57', '60', '61-62', '07', '20', '21', '52', '56']

for t in targets:
    if t in rules:
        print(f"File {t}.pdf: {rules[t]}")
    else:
        print(f"File {t}.pdf: Not in rules")
