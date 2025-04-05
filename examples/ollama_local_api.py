"""
This example demonstrates how to use the OLLAMA API locally.
Install it by following the instructions :

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
# Pull the models you want to use
ollama pull deepseek-r1:8b
ollama pull deepseek-r1:1.5b
ollama pull llama3.2:3b
ollama pull llama3.1:8b
```
"""

import json
import re

import requests

from codecarbon import EmissionsTracker

OLLAMA_URL = "http://localhost:11434"

# MODEL = "deepseek-r1:1.5b"
# MODEL = "deepseek-r1:8b"
# MODEL = "llama3.2:3b"
MODEL = "llama3.1:8b"


def extract_text_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        cleaned_text = re.sub(r"<[^>]+>", "", response.text)
        return cleaned_text
    else:
        response.raise_for_status()


url = "https://www.assemblee-nationale.fr/dyn/opendata/CRCANR5L17S2025PO59046N030.html"
extracted_text = extract_text_from_url(url)
# print(extracted_text)

prompt = (
    """
 Merci de me faire un compte rendu des différents points discutés lors de cette réunion.
"""
    + extracted_text
)


def call_ollama_api(endpoint, payload):
    url = f"{OLLAMA_URL}/{endpoint}"
    headers = {
        "Content-Type": "application/json",
    }
    answer = []

    response = requests.post(url, json=payload, headers=headers)
    try:
        for line in response.iter_lines():
            if line:
                # print(line)
                answer.append(line.decode("utf-8"))
                # print(answer)
        raw_answer = "".join([json.loads(line).get("response") for line in answer])
        think_start = raw_answer.find("<think>") + len("<think>")
        think_end = raw_answer.find("</think>")
        if think_end == -1:
            think = ""
            final_answer = raw_answer
        else:
            think = raw_answer[think_start:think_end]
            final_answer = raw_answer[think_end + len("</think>") :]
        answer_dict = {"think": think, "answer": final_answer}
        return answer_dict
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"think": f"An error occurred: {e}", "answer": response.text}
    finally:
        response.close()


if __name__ == "__main__":
    endpoint = "api/generate"
    payload = {
        "model": MODEL,
        "prompt": prompt,
    }
    tracker = EmissionsTracker()
    tracker.start()
    try:
        response = call_ollama_api(endpoint, payload)
        print(response.get("think"))
        print("-" * 50)
        print(response.get("answer"))
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    finally:
        tracker.stop()

    emissions: float = tracker.stop()
    print(f"Emissions: {emissions * 1000:.2f} g.co2.eq")
