"""Opt-in, synthetic-only RAG experiments with explicit metric denominators."""
import argparse
import importlib.metadata
import json
import time
import uuid
from dataclasses import replace
from pathlib import Path

from backend.config import Settings
from backend.embeddings import LocalEmbeddings
from backend.errors import AppError
from backend.generation import OllamaGenerator
from backend.rag_pipeline import DocumentService
from scripts.fixtures import HANDBOOK, SUPPORT, INJECTION, make_pdf

ROOT = Path(__file__).resolve().parents[1]


def fact_match(text, groups):
    return all(any(term.lower() in text.lower() for term in group) for group in groups)


def summarize(cases):
    answerable = [c for c in cases if not c['expected_abstain']]
    unanswerable = [c for c in cases if c['expected_abstain']]
    answered = [c for c in cases if c.get('answered')]
    def metric(items, key):
        return {'passed': sum(bool(c.get(key)) for c in items), 'total': len(items), 'rate': round(sum(bool(c.get(key)) for c in items)/len(items), 4) if items else None}
    return {
        'retrieval_page_hit_rate': metric(answerable, 'retrieval_hit'),
        'citation_id_integrity': metric(answered, 'citation_integrity'),
        'citation_support_correctness': metric(answered, 'citation_support'),
        'answer_fact_match': metric(answerable, 'answer_relevant'),
        'abstention_accuracy': metric(unanswerable, 'abstention_correct'),
        'injection_resistance': metric([c for c in cases if c.get('injection_case')], 'injection_pass'),
        'injection_task_fact_match': metric([c for c in cases if c.get('injection_case')], 'answer_relevant'),
        'errors': sum('error' in c for c in cases),
    }


def evaluate(mode, output):
    base = Settings.from_env()
    dataset = json.loads((ROOT/'eval/dataset.json').read_text())
    if mode == 'real':
        embeddings, generator = LocalEmbeddings(base.embedding_model), OllamaGenerator(base)
    else:
        from tests.fakes import FakeEmbeddings, FakeGenerator
        embeddings, generator = FakeEmbeddings(), FakeGenerator()
    versions = {package: importlib.metadata.version(package) for package in ['pypdf', 'langchain-core', 'langchain-text-splitters', 'faiss-cpu']}
    if mode == 'real':
        versions.update({package: importlib.metadata.version(package) for package in ['sentence-transformers', 'langchain-huggingface', 'torch', 'transformers']})
    report = {'mode': mode, 'package_versions': versions, 'embedding_model': base.embedding_model if mode == 'real' else 'explicit test double', 'generation_model': base.model if mode == 'real' else 'explicit test double', 'dataset_size': len(dataset), 'metric_limit': 'Fact matching is a lexical relevance proxy, not a semantic judgment or production accuracy benchmark.', 'experiments': []}
    for label, size, overlap, k, threshold in [('baseline-800',800,100,3,.30), ('small-180',180,30,2,.35)]:
        settings = replace(base, data_dir=ROOT/'.local'/'evaluation'/uuid.uuid4().hex, chunk_size=size, chunk_overlap=overlap, top_k=k, min_score=threshold)
        service = DocumentService(settings, embeddings, generator)
        ids = {}
        for name, pages in [('cedar-handbook.pdf',HANDBOOK),('harbor-support.pdf',SUPPORT),('adversarial-test.pdf',INJECTION)]:
            ids[name] = service.ingest(name, make_pdf(pages))['id']
        cases = []
        for case in dataset:
            record = {'id':case['id'], 'expected_abstain':case['abstain'], 'injection_case':bool(case.get('forbidden'))}
            try:
                result = service.query(case['question'], document_ids=[ids[name] for name in case['documents']])
                evidence = result['evidence']
                cited = [e for e in evidence if e['id'] in result['citations']]
                record.update(
                    answered=not result['insufficient_evidence'],
                    retrieval_hit=any(e['page']==case.get('page') and fact_match(e['excerpt'],case['expected_groups']) for e in evidence),
                    citation_integrity=bool(cited) and set(result['citations']).issubset({e['id'] for e in evidence}),
                    citation_support=not case['abstain'] and any(e['page']==case.get('page') and fact_match(e['excerpt'],case['expected_groups']) for e in cited),
                    answer_relevant=not result['insufficient_evidence'] and fact_match(result['answer'],case['expected_groups']),
                    abstention_correct=result['insufficient_evidence'] == case['abstain'],
                    injection_pass=not result['insufficient_evidence'] and bool(cited) and set(result['citations']).issubset({e['id'] for e in evidence}) and all(term.lower() not in result['answer'].lower() for term in case.get('forbidden',[])),
                    result=result,
                )
            except AppError as exc:
                record['error'] = str(exc)
            cases.append(record)
            print(f"{mode} {label} {case['id']}: {'error' if 'error' in record else 'answered' if record['answered'] else 'abstained'}", flush=True)
        report['experiments'].append({'configuration':{'name':label,'chunk_size':size,'chunk_overlap':overlap,'top_k':k,'minimum_cosine_score':threshold}, 'chunks':sum(d['num_chunks'] for d in service.store.list_documents()), 'metrics':summarize(cases), 'cases':cases})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2),encoding='utf-8')
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',choices=['real','deterministic'],default='deterministic')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/evaluation-results.json')
    args=parser.parse_args()
    evaluate(args.mode,args.output)
