import datetime
from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel


class PrivilegeHistoryOperationType(Enum):
    FILL_IN_BALANCE = 'FILL_IN_BALANCE'
    DEBIT_THE_ACCOUNT = 'DEBIT_THE_ACCOUNT'


class PrivilegeStatus(Enum):
    BRONZE = 'BRONZE'
    SILVER = 'SILVER'
    GOLD = 'GOLD'


class PrivilegeHistoryItemResponse(BaseModel):
    date: str
    ticketUid: UUID
    balanceDiff: int
    operationType: PrivilegeHistoryOperationType


class PrivilegeResponse(BaseModel):
    balance: int
    status: PrivilegeStatus
    history: List[PrivilegeHistoryItemResponse]


class PushPrivilegeRequest(BaseModel):
    operationType: PrivilegeHistoryOperationType
    price: int
    ticket_uid: UUID
