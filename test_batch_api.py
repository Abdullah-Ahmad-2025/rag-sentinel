import requests

payload = {
    "evaluations": [
        {
            "query": "What is the capital of France?",
            "retrieved_docs": ["Paris is the capital of France", "France is in Europe"],
            "answer": "The capital is Paris"
        },
        {
            "query": "What is the capital of Germany?",
            "retrieved_docs": ["Berlin is the capital of Germany", "Germany is in Europe"],
            "answer": "The capital is Berlin"
        },
        {
            "query": "What is the population of France?",
            "retrieved_docs": ["France has 67 million people"],
            "answer": "67 million"
        }
    ]
}

res = requests.post("http://localhost:8000/api/evaluate/batch", json=payload)
print("Status:", res.status_code)
try:
    print(res.json())
except:
    print(res.text)
