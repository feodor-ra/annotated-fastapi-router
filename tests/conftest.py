import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from annotated_fastapi_router import AnnotatedAPIRouter, ResponseError


@pytest.fixture(scope="session")
def app() -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(ResponseError, ResponseError.handler)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="session")
def router() -> AnnotatedAPIRouter:
    return AnnotatedAPIRouter()
