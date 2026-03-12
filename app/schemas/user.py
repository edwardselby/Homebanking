from datetime import date

from pydantic import BaseModel, Field


class Address(BaseModel):
    street: str
    city: str
    state: str | None = None
    postal_code: str
    country: str


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    date_of_birth: date
    address: Address


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1)
    last_name: str | None = Field(default=None, min_length=1)
    date_of_birth: date | None = None
    address: Address | None = None


class UserResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    date_of_birth: date
    address: Address
    coordinates: Coordinates | None = None
