import csv, re

def check_correctness(expected, actual):
    expected_lower = expected.lower()
    actual_lower = actual.lower()
    if expected_lower in actual_lower: return True
    stopwords = {'is','a','an','the','and','or','to','of','in','on','for','with','as','by','at','yes','no','he','she','it','dr','khare'}
    exp_t = set(re.findall(r'\b\w+\b', expected_lower)) - stopwords
    act_t = set(re.findall(r'\b\w+\b', actual_lower))
    if not exp_t: return True
    return len(exp_t.intersection(act_t)) / len(exp_t) >= 0.75

cats = {'Formatting/Close Match': 0, 'Missing KB Fact (Correct Refusal)': 0, 'Wrong Info': 0}
examples = {k: [] for k in cats}

with open('benchmark_results.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        if len(row) < 5: continue
        q_id, q, expected, actual, passed = row
        if passed == 'True': continue
        
        actual_lower = actual.lower()
        if ('not available' in actual_lower or 'not stated' in actual_lower or 
            'does not contain' in actual_lower or 'does not have any information' in actual_lower or
            'no information' in actual_lower):
            key = 'Missing KB Fact (Correct Refusal)'
        elif check_correctness(actual[:30], expected) or any(kw in actual_lower for kw in expected.lower().split()[:3]):
            key = 'Formatting/Close Match'
        else:
            key = 'Wrong Info'
        cats[key] += 1
        if len(examples[key]) < 5:
            examples[key].append((q_id, q[:60], expected[:50], actual[:60]))

print('Failure Classification:')
for k, v in cats.items():
    print(f'  {k}: {v}')
total_fails = sum(cats.values())
print(f'Total fails: {total_fails}')
print()
for k, exs in examples.items():
    print(f'--- {k} Examples ---')
    for q_id, q, exp, act in exs:
        print(f'  Q{q_id}: {q}')
        print(f'  Expected: {exp}')
        print(f'  Actual: {act}')
        print()
