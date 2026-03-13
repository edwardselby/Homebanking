import re
from datetime import date
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field

HTML_TAG_RE = re.compile(r"<[^>]+>")


def _no_html(value: str) -> str:
    if HTML_TAG_RE.search(value):
        raise ValueError("HTML tags are not allowed")
    return value


SafeStr = Annotated[str, AfterValidator(_no_html)]


class Address(BaseModel):
    street: SafeStr
    city: SafeStr
    state: SafeStr | None = None
    postal_code: SafeStr
    country: SafeStr


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class UserCreate(BaseModel):
    first_name: SafeStr = Field(min_length=1)
    last_name: SafeStr = Field(min_length=1)
    date_of_birth: date
    address: Address


class UserUpdate(BaseModel):
    first_name: SafeStr | None = Field(default=None, min_length=1)
    last_name: SafeStr | None = Field(default=None, min_length=1)
    date_of_birth: date | None = None
    address: Address | None = None


class UserResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    date_of_birth: date
    address: Address
    coordinates: Coordinates | None = None
