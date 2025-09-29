import pytest
from fastapi.testclient import TestClient


# Shared TestClient for API route tests
@pytest.fixture(scope="session")
def client():
    from main import app
    return TestClient(app)


