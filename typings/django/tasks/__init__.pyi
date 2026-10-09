# Django 6.0 Tasks framework, not in django-types 0.24.0 yet. Only what this project uses.
from collections.abc import Callable
from typing import Generic, ParamSpec, TypeVar, overload

_P = ParamSpec("_P")
_R = TypeVar("_R")

DEFAULT_TASK_BACKEND_ALIAS: str
DEFAULT_TASK_QUEUE_NAME: str

class TaskResult(Generic[_R]):
    id: str

class Task(Generic[_P, _R]):
    def enqueue(self, *args: _P.args, **kwargs: _P.kwargs) -> TaskResult[_R]: ...
    def call(self, *args: _P.args, **kwargs: _P.kwargs) -> _R: ...

@overload
def task(function: Callable[_P, _R], /) -> Task[_P, _R]: ...
@overload
def task(
    *, priority: int = ..., queue_name: str = ..., backend: str = ..., takes_context: bool = ...
) -> Callable[[Callable[_P, _R]], Task[_P, _R]]: ...
