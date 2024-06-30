from collections.abc import Callable
from http import HTTPStatus
from typing import Annotated, Any

import pytest

from annotated_fastapi_router import Status


@pytest.fixture(scope="session")
def status() -> HTTPStatus:
    return HTTPStatus.IM_USED


@pytest.fixture(scope="session")
def endpoint(status) -> Callable[[], Any]:
    def endpoint() -> Annotated[str, Status[status]]:
        return "test"

    return endpoint


def test_setup_status(app, router, client, status, endpoint):
    router.add_api_route("/setup_status", endpoint, name="setup_status")
    app.include_router(router)

    response = client.get(app.url_path_for("setup_status"))

    assert response.status_code == status


def test_keep_status(app, router, client, status, endpoint):
    router.add_api_route("/hold_status", endpoint, name="hold_status", status_code=HTTPStatus.OK)
    app.include_router(router)

    response = client.get(app.url_path_for("hold_status"))

    assert response.status_code != status


def test_status_instance_create():
    with pytest.raises(TypeError) as exc_info:
        Status()
    assert exc_info.value.args[0] == "Type Status cannot be instantiated."


def test_status_subclass_create():
    with pytest.raises(TypeError) as exc_info:
        type("MyStatus", (Status,), {})

    assert exc_info.value.args[0] == "Cannot subclass tests.test_status.Status"


def test_status_http_status():
    with pytest.raises(TypeError) as exc_info:
        _ = Annotated[int, Status[200]]
    assert exc_info.value.args[0] == "Status[...] should be used with argument http.HTTPStatus"
