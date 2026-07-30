import csv
import re
import json

total = 0
passed = 0
failed = 0
failures = []

with open('benchmark_results.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        total += 1
        if row['Pass'] == 'True':
            passed += 1
        else:
            failed += 1
            failures.append(row)

correct_refusals = []
formatting_mismatches = []
retrieval_failures = []
missing_facts = []
hallucinations = []

for r in failures:
    q = r['Question']
    exp = r['Expected Answer']
    act = r['Actual Answer']
    act_lower = act.lower()
    
    if any(phrase in act_lower for phrase in ['cannot find that information', 'do not contain any information', 'not provided', 'not explicitly mentioned', 'no information provided', 'does not provide', 'not mentioned', 'not stated']):
        correct_refusals.append(r)
        continue
        
    def clean(t): return re.sub(r'[^a-z0-9]', '', t.lower())
    c_exp = clean(exp)
    c_act = clean(act)
    if c_exp in c_act or c_act in c_exp or (len(set(c_act.split()) & set(c_exp.split())) > 2):
        formatting_mismatches.append(r)
        continue
        
    if 'date' in q.lower() or 'when' in q.lower():
        retrieval_failures.append(r)
    elif 'where' in q.lower() or 'who' in q.lower():
        missing_facts.append(r)
    else:
        hallucinations.append(r)

out = {
    'total': total,
    'passed': passed,
    'failed': failed,
    'correct_refusals_count': len(correct_refusals),
    'formatting_mismatches_count': len(formatting_mismatches),
    'retrieval_failures_count': len(retrieval_failures),
    'missing_facts_count': len(missing_facts),
    'hallucinations_count': len(hallucinations),
    'correct_refusals': correct_refusals[:5],
    'formatting_mismatches': formatting_mismatches[:5],
    'retrieval_failures': retrieval_failures[:10],
    'missing_facts': missing_facts[:5],
    'hallucinations': hallucinations[:5]
}
with open('stats.json', 'w') as f:
    json.dump(out, f, indent=2)
print("Done")
