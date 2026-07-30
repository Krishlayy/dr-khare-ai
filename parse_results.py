import json

data = json.load(open('benchmark_results.json'))

for idx, r in enumerate(data):
    if not r['passed']:
        print(f"\nQ{idx+1}: {r['question']}")
        print(f"Conf: {r['retrieval']['confidence']}")
        sources = r['retrieval']['sources']
        print(f"Sources: {', '.join(sources)}")
        print(f"Response: {r['response']}")
        print(f"Failure Reason: {r['failure_reason']}")
