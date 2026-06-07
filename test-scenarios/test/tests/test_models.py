from test_scenarios.refactor.src.models.user import restructure_user_model


def test_restructure_user_model_prefers_display_name() -> None:
    assert restructure_user_model({"id": "u1", "display_name": "Ada"}) == {"id": "u1", "name": "Ada"}
