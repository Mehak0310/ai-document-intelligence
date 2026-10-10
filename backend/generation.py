import json
import requests
from .errors import AppError

SCHEMA = {"type": "object", "properties": {"answer": {"type": "string"}, "citations": {"type": "array", "items": {"type": "string"}}, "insufficient_evidence": {"type": "boolean"}}, "required": ["answer", "citations", "insufficient_evidence"], "additionalProperties": False}


class OllamaGenerator:
    def __init__(self, settings):
        self.settings = settings

    def generate(self, prompt, model):
        try:
            response = requests.post(f"{self.settings.ollama_url}/api/generate", json={"model": model, "prompt": prompt, "stream": False, "format": SCHEMA, "options": {"temperature": 0}}, timeout=(5, self.settings.generation_timeout))
            response.raise_for_status()
            result = json.loads(response.json()["response"])
            if not isinstance(result, dict):
                raise ValueError("Expected object.")
            return result
        except requests.exceptions.Timeout as exc:
            raise AppError("Generation timed out. Try again or use a smaller local model.", 504) from exc
        except requests.exceptions.RequestException as exc:
            raise AppError("Ollama is unavailable. Check the service and selected model.", 503) from exc
        except (ValueError, KeyError, TypeError) as exc:
            raise AppError("The model returned an invalid structured response.", 502) from exc
