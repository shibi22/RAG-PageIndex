import requests
import json
import os

API_URL = "http://127.0.0.1:8000/api/v1"

def run_test():
    print("Testing /upload...")
    with open("Preparing-for-an-Interview.pdf", "rb") as f:
        res = requests.post(f"{API_URL}/upload", files={"file": f})
    
    if res.status_code != 200:
        print("Upload failed:", res.text)
        return
    
    doc_id = res.json().get("doc_id")
    print(f"Upload successful. doc_id: {doc_id}")
    
    print("\nTesting /chat...")
    res = requests.post(f"{API_URL}/chat", json={"doc_id": doc_id, "prompt": "What should I not wear?"}, stream=True)
    for line in res.iter_lines():
        if line:
            print(line.decode('utf-8'))

if __name__ == "__main__":
    run_test()
