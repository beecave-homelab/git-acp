from test_scenarios.fix.src.api.handler import fix_error_handling_in_api_response


def test_api_handler_returns_error_for_missing_data() -> None:
    assert fix_error_handling_in_api_response({}) == {"ok": False, "error": "missing data"}
