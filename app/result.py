"""Result types shared by the domain packages (docs/conventions.md, Error handling)."""

from dataclasses import dataclass
from enum import StrEnum


class ErrorCode(StrEnum):
    NOT_FOUND = "NOT_FOUND"
    END_BEFORE_START = "END_BEFORE_START"
    NO_WORKING_DAYS = "NO_WORKING_DAYS"
    START_IN_PAST = "START_IN_PAST"
    SPANS_YEARS = "SPANS_YEARS"
    OVERLAP = "OVERLAP"


@dataclass(frozen=True)
class Ok[T]:
    value: T


@dataclass(frozen=True)
class Err:
    code: ErrorCode


type Result[T] = Ok[T] | Err
