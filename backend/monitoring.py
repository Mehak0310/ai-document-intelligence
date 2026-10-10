import json
import time

def log_event(query, response, model, latency):
    log = {
        "query": query,
        "model": model,
        "latency": latency
    }

    with open("data/logs.json", "a") as f:
        json.dump(log, f)
        f.write("\n")