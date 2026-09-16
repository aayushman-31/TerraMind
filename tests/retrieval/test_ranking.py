from app.retrieval.config_loader import load_retrieval_weights


def test_retrieval_weights_are_configurable():
    weights = load_retrieval_weights()
    total = (
        weights.semantic_weight
        + weights.lexical_weight
        + weights.domain_weight
        + weights.geographic_weight
        + weights.metric_weight
    )
    assert abs(total - 1.0) < 1e-6
    assert weights.semantic_weight == 0.40
