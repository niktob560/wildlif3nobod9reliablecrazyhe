import dataclasses
from typing import Optional, Any, List


@dataclasses.dataclass
class ValidationError:
    field: str
    err: str


def validate_name(name: Optional[str]) -> List[ValidationError]:
    if name is None:
        return [ValidationError('name', 'Name must be not null')]
    if len(name) == 0:
        return [ValidationError('name', 'Name must have len gt than 0')]
    return []


def validate_age(age: Any) -> List[ValidationError]:
    if age is None:
        return []
    if not isinstance(age, int):
        return [ValidationError('age', 'Age must be integer')]
    if age <= 0:
        return [ValidationError('age', 'Age must be gt than 0')]
    return []


def validate_optional_field(field_name: str, field: Any) -> List[ValidationError]:
    if field is not None and isinstance(field, str) and len(field) == 0:
        return [ValidationError(field_name, f'Field {field_name} must be null or have len gt 0')]
    return []


def validate_person_request(raw_data: dict) -> List[ValidationError]:
    ret = []
    ret += validate_name(raw_data.get('name'))
    ret += validate_age(raw_data.get('age'))
    ret += validate_optional_field('work', raw_data.get('work'))
    ret += validate_optional_field('address', raw_data.get('address'))

    return ret
