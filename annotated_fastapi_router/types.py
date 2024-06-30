from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Final, Self, TypeGuard

from .error import ResponseError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pydantic import BaseModel

MINIMUM_PARAMS: Final[int] = 1


class Status:
    def __new__(cls: type[Self]) -> Status:
        raise TypeError("Type Status cannot be instantiated.")

    def __init_subclass__(cls: type[Self]) -> None:
        raise TypeError(f"Cannot subclass {cls.__module__}.Status")

    def __class_getitem__(cls: type[Self], status: HTTPStatus) -> _StatusAlias:
        if not isinstance(status, HTTPStatus):
            raise TypeError("Status[...] should be used with argument http.HTTPStatus")
        return _StatusAlias(status)


class Errors:
    def __new__(cls: type[Self]) -> Errors:
        raise TypeError("Type Errors cannot be instantiated.")

    def __init_subclass__(cls: type[Self]) -> None:
        raise TypeError(f"Cannot subclass {cls.__module__}.Errors")

    def __class_getitem__(cls: type[Self], params: tuple[Any] | type) -> _ErrorsAlias:
        if not isinstance(params, tuple):
            params = tuple[Any]((params,))
        if len(params) < MINIMUM_PARAMS:
            raise TypeError(
                "Errors[...] should be used with one or more arguments of types ResponseError",
            )
        if not cls.is_response_errors(params):
            raise TypeError("Errors[...] all arguments should be type[ResponseError]")
        return _ErrorsAlias(*params)

    @staticmethod
    def is_response_errors(
        errors: Iterable[Any],
    ) -> TypeGuard[Iterable[type[ResponseError[BaseModel]]]]:
        return all(isinstance(error, type) and issubclass(error, ResponseError) for error in errors)


class _ErrorsAlias:
    def __init__(self: _ErrorsAlias, *errors: type[ResponseError[BaseModel]]) -> None:
        self.errors = errors


class _StatusAlias:
    def __init__(self: _StatusAlias, status: HTTPStatus) -> None:
        self.status = status
