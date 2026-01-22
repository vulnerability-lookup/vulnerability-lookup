from typing import TypeVar, Callable, cast

# Generic helper to cast untyped decorators (e.g. flask-restx) so mypy preserves
# the decorated function signature. Usage:
#
# @typed(ns.doc(...))
# def get(...):
#     ...

F = TypeVar("F", bound=Callable[..., object])


def typed(decorator: object) -> Callable[[F], F]:
    return cast(Callable[[F], F], decorator)
