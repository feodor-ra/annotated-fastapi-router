from collections.abc import Callable
from http import HTTPStatus
from itertools import chain
from typing import Annotated

import pytest
from humps import pascalize
from pydantic import BaseModel

from annotated_fastapi_router import Errors, ResponseError


class MyErrorModel(BaseModel):
    test: str = "testing"


class MyError(ResponseError[MyErrorModel]):
    status = HTTPStatus.EXPECTATION_FAILED
    model = MyErrorModel


class MySecondErrorModel(BaseModel):
    value: int = 42


class MySecondError(ResponseError[MySecondErrorModel]):
    status = HTTPStatus.EXPECTATION_FAILED
    model = MySecondErrorModel


@pytest.fixture(scope="session")
def endpoint_with_raise() -> Callable[[], str]:
    def endpoint() -> Annotated[str, Errors[MyError, MySecondError]]:
        raise MyError

    return endpoint


@pytest.fixture(scope="session")
def endpoint_name() -> str:
    return "my_error_endpoint"


@pytest.fixture(scope="session", autouse=True)
def openapi_schema(app, router, endpoint_with_raise, endpoint_name):
    router.add_api_route("/open_api_schema", endpoint_with_raise, name=endpoint_name)
    app.include_router(router)
    return app.openapi()


def test_errors_instance_create():
    with pytest.raises(TypeError) as exc_info:
        Errors()
    assert exc_info.value.args[0] == "Type Errors cannot be instantiated."


def test_errors_subclass_create():
    with pytest.raises(TypeError) as exc_info:
        type("MyErrors", (Errors,), {})
    assert exc_info.value.args[0] == "Cannot subclass tests.test_errors.Errors"


def test_errors_required_one_arguments():
    error = "Errors[...] should be used with one or more arguments of types ResponseError"

    with pytest.raises(TypeError) as exc_info:
        Errors[()]

    assert exc_info.value.args[0] == error


def test_errors_all_error_must_be_response_error():
    with pytest.raises(TypeError) as exc_info:
        Errors[object]
    assert exc_info.value.args[0] == "Errors[...] all arguments should be type[ResponseError]"


def test_error_class_required_status():
    with pytest.raises(ValueError) as exc_info:
        type("NewError", (ResponseError,), {"model": MyErrorModel})
    assert exc_info.value.args[0] == "ResponseError should has status as HTTPStatus instance"


def test_error_class_required_http_status():
    with pytest.raises(ValueError) as exc_info:
        type("NewError", (ResponseError,), {"status": 200, "model": MyErrorModel})
    assert exc_info.value.args[0] == "ResponseError should has status as HTTPStatus instance"


def test_error_class_required_model():
    with pytest.raises(ValueError) as exc_info:
        type("NewError", (ResponseError,), {"status": HTTPStatus.OK})
    assert exc_info.value.args[0] == "ResponseError should has model as BaseModel type"


def test_error_class_required_model_pydantic():
    with pytest.raises(ValueError) as exc_info:
        type("NewError", (ResponseError,), {"status": HTTPStatus.OK, "model": object})
    assert exc_info.value.args[0] == "ResponseError should has model as BaseModel type"


def test_handling_error(app, client, endpoint_name):
    response = client.get(app.url_path_for(endpoint_name))

    assert response.status_code == MyError.status


def test_openapi_error_schema_name(app, openapi_schema, endpoint_name):
    my_error_model_name = map(
        pascalize,
        chain(
            filter(bool, app.url_path_for(endpoint_name).split("/")), MyError.status.phrase.split()
        ),
    )
    my_error_model_name = "".join(my_error_model_name)

    assert my_error_model_name in openapi_schema["components"]["schemas"]
