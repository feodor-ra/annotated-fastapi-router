from http import HTTPStatus
from typing import Annotated, Self

from fastapi import FastAPI
from pydantic import BaseModel

from annotated_fastapi_router import AnnotatedAPIRouter, Errors, ResponseError


class ResponseModel(BaseModel):
    message: str


class ErrorMessageModel(BaseModel):
    message: str


class OtherErrorModel(BaseModel):
    code: int


class MyError(ResponseError[ErrorMessageModel]):
    status = HTTPStatus.BAD_REQUEST
    model = ErrorMessageModel

    def __init__(self: "MyError", msg: str) -> None:
        self.message = msg


class OtherError(ResponseError[OtherErrorModel]):
    status = HTTPStatus.BAD_REQUEST
    model = OtherErrorModel

    async def entity(self: Self) -> OtherErrorModel:
        return self.model(code=self.status)


router = AnnotatedAPIRouter()


@router.get("/my_endpoint")
@router.post("/my_endpoint")
@router.get("/my_endpoint_too", responses={HTTPStatus.BAD_REQUEST: {"model": dict[str, str]}})
async def endpoint(how_iam: str) -> Annotated[ResponseModel, Errors[MyError, OtherError]]:
    if how_iam == "me":
        return ResponseModel(message="hello")
    if how_iam.isdigit():
        raise OtherError
    raise MyError("I don't know you")


app = FastAPI()
app.include_router(router)
app.add_exception_handler(ResponseError, ResponseError.handler)
