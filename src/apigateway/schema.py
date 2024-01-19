from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Any, List

import validator


@dataclass
class PersonResponse:
    _id: int
    name: str
    age: Optional[int]
    address: Optional[str]
    work: Optional[str]

    @staticmethod
    def from_request(person_id: int, req: PersonRequest):
        return PersonResponse(person_id, *req.__dict__.values())

    def to_json(self) -> dict[str, Any]:
        ret = self.__dict__
        ret['id'] = self._id
        del (ret['_id'])
        return ret


@dataclass
class PersonRequest:
    name: str
    age: Optional[int]
    address: Optional[str]
    work: Optional[str]

    @staticmethod
    def from_raw(data: dict) -> PersonRequest | ValidationErrorResponse:
        errs = validator.validate_person_request(data)
        if len(errs) > 0:
            raise ValidationErrorResponse.from_validation_errors('Invalid person request', errs)

        return PersonRequest(data['name'], data.get('age'), data.get('address'), data.get('work'))

    def to_json(self) -> dict[str, Any]:
        return self.__dict__


@dataclass
class ErrorResponse(Exception):
    message: Optional[str]
    status = 400

    def to_json(self):
        return {'message': self.message}


@dataclass
class ErrorNotFound(ErrorResponse):
    def __init__(self):
        self.message = 'Not found'
        self.status = 404


@dataclass
class ValidationErrorResponse(ErrorResponse):
    message: Optional[str]
    errors: Optional[dict[Any, str]]
    status = 400

    @staticmethod
    def from_validation_errors(message, errs: List[validator.ValidationError]) -> ValidationErrorResponse:
        err_dict = {}
        for err in errs:
            err_dict[err.field] = err.err
        return ValidationErrorResponse(message, err_dict)

    def to_json(self):
        return {
            'message': self.message,
            'errors': self.errors
        }
