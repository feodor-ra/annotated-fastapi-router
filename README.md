# Annotated FastAPI router

Этот пакет содержит улучшенный `fastapi.APIRouter`, который содержит шорт-каты для удобной аннотации
эндпоинтов через `typing.Annotated`, что бы задавать значения `status_code` или модели ответов в `responses`.

- [примеры](#примеры)
  - [статус-код](#статус-код)
  - [модели ошибок](#модель-ответов-для-ошибок)

Warning *the English part of README.md is translated via ChatGPT and may not be accurate*

This package contains an enhanced `fastapi.APIRouter` that includes shortcuts for annotating endpoints conveniently using `typing.Annotated`, allowing you to set values like `status_code` or response models in `responses`.

- [examples](#examples)
  - [status code](#status-code)
  - [responses](#responses)

## Примеры

### Статус-код

Указывать `status_code` у эндпоинта можно следующим образом:

```python
from http import HTTPStatus
from typing import Annotated

from fastapi import FastAPI
from pydantic import BaseModel

from annotated_fastapi_router import AnnotatedAPIRouter, Status


class ResponseModel(BaseModel):
    message: str


router = AnnotatedAPIRouter()


@router.get("/my_endpoint")
async def my_endpoint() -> Annotated[ResponseModel, Status[HTTPStatus.ACCEPTED]]:
    return ResponseModel(message="hello")


router.add_api_route("/my_endpoint", my_endpoint, methods=["POST"])
```

В результате swagger будет содержать следующую OpenAPI-схему:

![GET request swagger](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/use_status_get.png)
![POST request swagger](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/use_status_post.png)

При запросе статус код так же будет проставлен в ответ:

![POST response swagger](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/use_status_get_response.png)

Однако если статус код будет указан явно в декораторе или при добавлении в роутер, `Status` в аннотации будет проигнорирован.

```python
@router.get("/my_endpoint")
@router.get("/my_endpoint_too", status_code=HTTPStatus.CREATED)
async def my_endpoint() -> Annotated[ResponseModel, Status[HTTPStatus.ACCEPTED]]:
    return ResponseModel(message="hello")


router.add_api_route("/my_endpoint", my_endpoint, methods=["POST"])
router.add_api_route("/my_endpoint_too", my_endpoint, status_code=HTTPStatus.CREATED, methods=["POST"])
```

![GET request swagger keep](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/keep_status_get_swagger.png)
![POST request swagger keep](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/keep_status_post_swagger.png)

**Важно:** `Status` принимает в себя только перечисления из `HTTPStatus`,
на любые другие объекты будет подыматься ошибка `TypeError`.

### Модель ответов для ошибок

Для автоматического построения моделей для `responses` используется тип ошибок `ResponseError`.
В его наследниках обязательно нужно указывать переменную типа `status` и `model`.

`status` указывает для каких кодов ошибок нужно будет построить модель, если будет передано несколько
типов ошибок для одного и того же `HTTPStatus`, то полученная модель будет объединять в себе все модели `model`.

```python
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
async def endpoint(how_iam: str) -> Annotated[ResponseModel, Errors[MyError, OtherError]]:
    if how_iam == "me":
        return ResponseModel(message="hello")
    if how_iam.isdigit():
        raise OtherError
    raise MyError("I don't know you")
```

Таким образом будет построены две модели ошибок – `MyEndpointPOSTBadRequest` и `MyEndpointGETBadRequest`.

![Build error model GET](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/build_error_model_get.png)
![Build error model POST](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/build_error_model_post.png)

Имя модели генерируется из пути, методов (если указаны) роута и phrase статус-кода ошибки.
Делается это потому что для `fastapi<=0.95.0` требуется что бы все названия моделей (если они отличаются) имели уникальные имена.
Если модель ошибки состоит только из одной модели – тогда будет использовано имя оригинальной модели (что бы избегать баг в OpenAPI-схеме с некорректным определением компонента).

Логику построения имени модели можно изменить наследованием от `AnnotatedAPIRouter` и переопределением метода `response_model_name`.

Так же для построение экземпляра модели ошибки по умолчанию использует атрибуты экземпляра ошибки (через `__dict__`),
но если это поведение необходимо изменить можно реализовать метод `entity` (как в примере в класса `OtherError`).

Если `responses` уже определяется в декораторе роута или при явном добавлении в него и содержит описание для ошибки,
которая указана в `Annotated`, то она не будет перезаписывать данные переданные в `responses`.

```python
@router.get("/my_endpoint_too", responses={HTTPStatus.BAD_REQUEST: {"model": dict[str, str]}})
async def endpoint(how_iam: str) -> Annotated[ResponseModel, Errors[MyError, OtherError]]:
    if how_iam == "me":
        return ResponseModel(message="hello")
    if how_iam.isdigit():
        raise OtherError
    raise MyError("I don't know you")
```

![Keep responses data model](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/keep_build_error_model.png)

Для того что бы автоматически отлавливать ошибки из эндпоинтов и указывать в ответе тот статус-код, который в указан в них,
необходимо добавить в `FastAPI` приложение обработчик ошибок `ResponseError.handler`.

```python
app.add_exception_handler(ResponseError, ResponseError.handler)
```

![Handle MyError](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/handle_my_error.png)
![Handle OtherError](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/handle_other_error.png)

## Examples

### Status-code

To specify the status_code of the endpoint, you can do it as follows:

```python
from http import HTTPStatus
from typing import Annotated

from fastapi import FastAPI
from pydantic import BaseModel

from annotated_fastapi_router import AnnotatedAPIRouter, Status


class ResponseModel(BaseModel):
    message: str


router = AnnotatedAPIRouter()


@router.get("/my_endpoint")
async def my_endpoint() -> Annotated[ResponseModel, Status[HTTPStatus.ACCEPTED]]:
    return ResponseModel(message="hello")


router.add_api_route("/my_endpoint", my_endpoint, methods=["POST"])
```

As a result, the swagger will contain the following OpenAPI schema:

![GET request swagger](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/use_status_get.png)
![POST request swagger](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/use_status_post.png)

When the endpoint is requested, the status code will also be included in the response:

![POST response swagger](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/use_status_get_response.png)

However, if the status code is explicitly provided in the decorator or when adding it to the router, the `Status` in the annotation will be ignored.

```python
@router.get("/my_endpoint")
@router.get("/my_endpoint_too", status_code=HTTPStatus.CREATED)
async def my_endpoint() -> Annotated[ResponseModel, Status[HTTPStatus.ACCEPTED]]:
    return ResponseModel(message="hello")


router.add_api_route("/my_endpoint", my_endpoint, methods=["POST"])
router.add_api_route("/my_endpoint_too", my_endpoint, status_code=HTTPStatus.CREATED, methods=["POST"])
```

![GET request swagger keep](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/keep_status_get_swagger.png)
![POST request swagger keep](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/keep_status_post_swagger.png)

**Important**: `Status` only accepts enumerations from `HTTPStatus`; any other objects will raise a `TypeError`

### Responses

To automatically build models for `responses`, the error type `ResponseError` is used.
In its subclasses, it is necessary to specify variables of type `status` and `model`.

`status` indicates for which error codes the model will need to be constructed.
If multiple error types are provided for the same HTTPStatus, the resulting model will combine all model models.

```python
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
async def endpoint(how_iam: str) -> Annotated[ResponseModel, Errors[MyError, OtherError]]:
    if how_iam == "me":
        return ResponseModel(message="hello")
    if how_iam.isdigit():
        raise OtherError
    raise MyError("I don't know you")
```

In this way, two error models will be built - `MyEndpointPOSTBadRequest` and `MyEndpointGETBadRequest`.

![Build error model GET](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/build_error_model_get.png)
![Build error model POST](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/build_error_model_post.png)

The model name is generated from the path, methods (if specified) of the route, and the status code error phrase.
This is done because for `fastapi<=0.95.0`, all model names (if they differ) must have unique names.
If the error model consists of only one model, the name of the original model will be used (to avoid a bug in the OpenAPI schema with an incorrect component definition).

The logic for naming the model can be changed by inheriting from `AnnotatedAPIRouter`
and overriding the `response_model_name` method.

Also, to build an instance of the error model by default, it uses the error instance attributes (via `__dict__`),
but if this behavior needs to be changed, you can implement the `entity` method
(as shown in the example in the `OtherError` class).

If `responses` are already defined in the route decorator or explicitly added to it and contain
a description for an error specified in `Annotated`, it will not overwrite the data passed to `responses`.

```python
@router.get("/my_endpoint_too", responses={HTTPStatus.BAD_REQUEST: {"model": dict[str, str]}})
async def endpoint(how_iam: str) -> Annotated[ResponseModel, Errors[MyError, OtherError]]:
    if how_iam == "me":
        return ResponseModel(message="hello")
    if how_iam.isdigit():
        raise OtherError
    raise MyError("I don't know you")
```

![Keep responses data model](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/keep_build_error_model.png)

To automatically catch errors from endpoints and include the status code specified in them in the response, you need to add the error handler `ResponseError.handler` to the `FastAPI` application.

```python
app.add_exception_handler(ResponseError, ResponseError.handler)
```

![Handle MyError](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/handle_my_error.png)
![Handle OtherError](https://github.com/feodor-ra/annotated-fastapi-router/blob/f4a0b2028ba5ceedca76de6af491f9ef6e312c3a/docs/handle_other_error.png)
