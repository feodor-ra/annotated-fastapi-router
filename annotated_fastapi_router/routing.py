from __future__ import annotations

from itertools import chain, groupby
from typing import (
    TYPE_CHECKING,
    Any,
    Self,
    Union,
    get_args,
    get_type_hints,
)

from fastapi import APIRouter, Response, _compat, params
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from humps import pascalize
from pydantic import BaseModel, create_model
from starlette.responses import JSONResponse
from starlette.routing import BaseRoute

from .types import _ErrorsAlias, _StatusAlias

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from enum import Enum
    from http import HTTPStatus

    from fastapi.routing import APIRoute
    from fastapi.types import IncEx
    from starlette.routing import BaseRoute

    from .error import ResponseError


class AnnotatedAPIRouter(APIRouter):
    def add_api_route(
        self: Self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        response_model: Any = Default(None),
        status_code: int | None = None,
        tags: list[str | Enum] | None = None,
        dependencies: Sequence[params.Depends] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        responses: dict[int | str, dict[str, Any]] | None = None,
        deprecated: bool | None = None,
        methods: set[str] | list[str] | None = None,
        operation_id: str | None = None,
        response_model_include: IncEx | None = None,
        response_model_exclude: IncEx | None = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        include_in_schema: bool = True,
        response_class: type[Response] | DefaultPlaceholder = Default(JSONResponse),
        name: str | None = None,
        route_class_override: type[APIRoute] | None = None,
        callbacks: list[BaseRoute] | None = None,
        openapi_extra: dict[str, Any] | None = None,
        generate_unique_id_function: Callable[[APIRoute], str] | DefaultPlaceholder = Default(
            generate_unique_id,
        ),
    ) -> None:
        easy_status, easy_responses = None, None
        match get_type_hints(endpoint, include_extras=True):
            case {"return": return_type}:
                for arg in get_args(return_type):
                    if isinstance(arg, _StatusAlias):
                        easy_status = arg.status
                    if isinstance(arg, _ErrorsAlias):
                        easy_responses = self.build_responses(path, methods, *set(arg.errors))
        if not status_code:
            status_code = easy_status

        if responses and easy_responses:
            responses = easy_responses | responses
        else:
            responses = easy_responses or responses

        return super().add_api_route(
            path,
            endpoint,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            responses=responses,
            deprecated=deprecated,
            methods=methods,
            operation_id=operation_id,
            response_model_include=response_model_include,
            response_model_exclude=response_model_exclude,
            response_model_by_alias=response_model_by_alias,
            response_model_exclude_unset=response_model_exclude_unset,
            response_model_exclude_defaults=response_model_exclude_defaults,
            response_model_exclude_none=response_model_exclude_none,
            include_in_schema=include_in_schema,
            response_class=response_class,
            name=name,
            route_class_override=route_class_override,
            callbacks=callbacks,
            openapi_extra=openapi_extra,
            generate_unique_id_function=generate_unique_id_function,
        )

    def build_responses(
        self: Self,
        path: str,
        methods: set[str] | list[str] | None,
        *errors: type[ResponseError[BaseModel]],
    ) -> dict[int | str, dict[str, Any]] | None:
        def key(error: type[ResponseError[BaseModel]]) -> HTTPStatus:
            return error.status

        return {
            status_code.value: {
                "model": self.build_response_model(path, methods, status_code, *group),
                "description": status_code.phrase,
            }
            for status_code, group in groupby(sorted(errors, key=key), key=key)
        }

    def build_response_model(
        self: Self,
        path: str,
        methods: set[str] | list[str] | None,
        status_code: HTTPStatus,
        *errors: type[ResponseError[BaseModel]],
    ) -> type[BaseModel]:
        if len(errors) == 1:
            return errors[0].model

        type_ = Union[tuple(error.model for error in errors)]  # type: ignore reportGeneralTypeIssues # noqa: UP007
        name = self.response_model_name(path, methods, status_code, *errors)
        if _compat.PYDANTIC_V2:
            from pydantic import RootModel  # type: ignore reportAttributeAccessIssue

            return create_model(name, __base__=RootModel[type_])
        return create_model(name, __base__=BaseModel, __root__=(type_, ...))

    def response_model_name(
        self: Self,
        path: str,
        methods: set[str] | list[str] | None,
        status_code: HTTPStatus,
        *errors: type[ResponseError[BaseModel]],  # noqa: ARG002
    ) -> str:
        return "".join(
            map(
                pascalize,
                chain(filter(bool, path.split("/")), methods or [], status_code.phrase.split()),
            )
        )
