from test_scenarios.feat.src.features.search_engine import SearchEngine


def test_search_engine_returns_matching_document() -> None:
    engine = SearchEngine()
    engine.add_document("doc-1", "classifier validation")
    assert engine.search("validation") == ["doc-1"]
