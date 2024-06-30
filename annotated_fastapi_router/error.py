from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, ClassVar, Generic, Self, TypeVar

from pydantic import BaseModel
from starlette.responses import JSONResponse

if TYPE_CHECKING:
    from fastapi import Request

Model = TypeVar("Model", bound=BaseModel)


class ResponseError(Generic[Model], Exception):
    status: ClassVar[HTTPStatus]
    model: ClassVar[type[Model]]  # type: ignore reportGeneralTypeIssues

    def __init_subclass__(cls: type[Self]) -> None:
        if cls is RecursionError:
            return None
        if not hasattr(cls, "status") or not isinstance(cls.status, HTTPStatus):
            raise ValueError("ResponseError should has status as HTTPStatus instance")
        if not hasattr(cls, "model") or not issubclass(cls.model, BaseModel):
            raise ValueError("ResponseError should has model as BaseModel type")
        return super().__init_subclass__()

    async def entity(self: Self) -> Model:
        return self.model.parse_obj(self.__dict__)

    @classmethod
    async def handler(
        cls: type[Self],
        request: Request,  # noqa: ARG003
        exception: ResponseError[BaseModel],
    ) -> JSONResponse:
        entity = await exception.entity()
        return JSONResponse(entity.dict(), exception.status)
