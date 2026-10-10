import json

def save_features(doc_name, chunks):
    features = {
        "doc_name": doc_name,
        "num_chunks": len(chunks),
        "avg_chunk_length": sum(len(c) for c in chunks) / len(chunks)
    }

    with open("data/features.json", "a") as f:
        json.dump(features, f)