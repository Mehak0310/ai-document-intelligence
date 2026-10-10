"""Explicit test doubles, never production model substitutes."""
import json
import re
import numpy as np


class FakeEmbeddings:
    @staticmethod
    def vector(text):
        words = set(re.findall(r'\w+', text.lower()))
        groups = [{'leave', 'days', 'annual'}, {'expense', 'expenses', 'reimbursement', 'receipts'}, {'harbor', 'support', 'hours'}, {'planet', 'mars', 'salary', 'president'}]
        vector = [len(words & group) for group in groups] + [0.01]
        return np.array(vector, dtype='float32')

    def embed_documents(self, texts):
        return np.stack([self.vector(text) for text in texts])

    def embed_query(self, text):
        return self.vector(text)


class FakeGenerator:
    def __init__(self, result=None):
        self.result = result
        self.calls = []

    def generate(self, prompt, model):
        self.calls.append((prompt, model))
        if self.result is not None:
            return self.result
        data = json.loads(prompt.split('DATA:\n')[1])
        evidence = data['evidence']
        question = data['question'].lower()
        if 'leave' in question:
            answer = 'Cedar employees receive 20 days of annual leave.'
        elif 'expense' in question or 'reimbursement' in question:
            answer = 'Expense reimbursement requests must be filed within 14 days.'
        elif 'support' in question:
            answer = 'Harbor support operates Monday to Friday from 09:00 to 17:00 UTC.'
        else:
            return {'answer': '', 'citations': [], 'insufficient_evidence': True}
        return {'answer': answer, 'citations': [evidence[0]['id']], 'insufficient_evidence': False}
