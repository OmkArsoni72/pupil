import pytest
from fastapi.testclient import TestClient
import asyncio
import inspect


# Shared TestClient for API route tests
@pytest.fixture(scope="session")
def client():
    from main import app
    return TestClient(app)



# Allow async test functions to run without external plugins
def pytest_pyfunc_call(pyfuncitem):
    testfunc = pyfuncitem.obj
    if inspect.iscoroutinefunction(testfunc):
        asyncio.run(testfunc(**pyfuncitem.funcargs))
        return True
    return None
