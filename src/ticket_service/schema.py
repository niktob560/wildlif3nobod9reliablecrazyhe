from enum import Enum
from typing import TypeVar, Generic, List
from uuid import UUID

from pydantic import BaseModel


class TicketStatus(Enum):
    PAID = 'PAID'
    CANCELED = 'CANCELED'


class TicketCreation(BaseModel):
    flightNumber: str
    price: int
    paidFromBalance: bool


class Ticket(BaseModel):
    ticket_id: int
    ticket_uid: UUID
    username: str
    flight_number: str
    price: int
    status: TicketStatus



class TicketCreationSchema(BaseModel):
    flightNumber: str
    price: int
    paidFromBalance: bool


class TicketCreationResponse(BaseModel):
    ticketUid: UUID
    flightNumber: str
    price: int
    status: TicketStatus


T = TypeVar('T')


class PagedResponse(BaseModel, Generic[T]):
    page: int
    pageSize: int
    totalElements: int
    items: List[T]
