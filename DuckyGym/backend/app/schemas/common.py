import re
from decimal import Decimal
from math import ceil
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

T = TypeVar("T")

PHONE_PATTERN = r"^(0|\+84)\d{9,10}$"
USERNAME_PATTERN = r"^[A-Za-z0-9_.]{4,50}$"

PhoneStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=PHONE_PATTERN, max_length=20),
]
UsernameStr = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=USERNAME_PATTERN)
]
NameStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)
]
Money = Annotated[Decimal, Field(max_digits=12, decimal_places=2, ge=0)]
PositiveMoney = Annotated[Decimal, Field(max_digits=12, decimal_places=2, gt=0)]


def validate_password_strength(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Mật khẩu phải có ít nhất 8 ký tự")
    if len(value) > 72:
        raise ValueError("Mật khẩu không được vượt quá 72 ký tự")
    if not re.search(r"[A-Za-z]", value):
        raise ValueError("Mật khẩu phải chứa ít nhất một chữ cái")
    if not re.search(r"\d", value):
        raise ValueError("Mật khẩu phải chứa ít nhất một chữ số")
    return value


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    size: int = Field(ge=1)
    pages: int = Field(ge=0)

    @classmethod
    def create(cls, items: list[T], total: int, params: PageParams) -> "Page[T]":
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=ceil(total / params.size) if total else 0,
        )
