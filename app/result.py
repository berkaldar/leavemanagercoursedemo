"""Result types shared by the domain packages (docs/conventions.md, Error handling)."""

from dataclasses import dataclass
from enum import StrEnum


class ErrorCode(StrEnum):
    NOT_FOUND = "NOT_FOUND"


@dataclass(frozen=True)
class Ok[T]:
    value: T


@dataclass(frozen=True)
class Err:
    code: ErrorCode


type Result[T] = Ok[T] | Err
