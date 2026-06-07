import pytest


@pytest.fixture
def sample_payload() -> dict[str, str]:
    return {"id": "item-1", "name": "Sample"}
