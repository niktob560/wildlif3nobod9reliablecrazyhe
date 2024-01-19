from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, List, Annotated

from pydantic import BaseModel


class Airport(BaseModel):
    id: Annotated[int, 'id']
    name: str
    city: str
    country: str


class Flight(BaseModel):
    id: int
    flightNumber: str
    date: str
    fromAirport: str
    toAirport: str
    price: int


T = TypeVar('T')


class PagedResponse(BaseModel, Generic[T]):
    page: int
    pageSize: int
    totalElements: int
    items: List[T]
