from scripts.evaluate import evaluate, fact_match, summarize


def test_metrics_and_synthetic_harness(tmp_path):
    assert fact_match('Five business days', [['five','5'],['business']])
    assert not fact_match('unsupported', [['20']])
    assert summarize([])['citation_id_integrity']['rate'] is None
    report = evaluate('deterministic',tmp_path/'result.json')
    assert report['mode']=='deterministic' and len(report['experiments'])==2
    assert all(e['metrics']['errors']==0 for e in report['experiments'])
    assert report['embedding_model']=='explicit test double'
