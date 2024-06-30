from http import HTTPStatus
from typing import Annotated

from fastapi import FastAPI
from pydantic import BaseModel

from annotated_fastapi_router import AnnotatedAPIRouter, Status


class ResponseModel(BaseModel):
    message: str


router = AnnotatedAPIRouter()


@router.get("/my_endpoint")
@router.get("/my_endpoint_too", status_code=HTTPStatus.CREATED)
async def my_endpoint() -> Annotated[ResponseModel, Status[HTTPStatus.ACCEPTED]]:
    return ResponseModel(message="hello")


router.add_api_route("/my_endpoint", my_endpoint, methods=["POST"])
router.add_api_route(
    "/my_endpoint_too", my_endpoint, status_code=HTTPStatus.CREATED, methods=["POST"]
)


app = FastAPI()
app.include_router(router)
