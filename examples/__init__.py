from uvicorn import run

from .use_errors import app as errors_app
from .use_status import app as status_app


def status() -> None:
    run(status_app)


def errors() -> None:
    run(errors_app)
