#! /usr/bin/env python
from typing import Any, List

from typing_extensions import TypedDict


class MetaDataType(TypedDict):
    """Defines a type for the metadata in the response of the API."""

    count: int
    page: int
    per_page: int


class ResultType(TypedDict):
    """Defines a response type of the API."""

    data: List[Any]
    metadata: MetaDataType
