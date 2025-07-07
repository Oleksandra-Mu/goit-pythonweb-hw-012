from pydantic import BaseModel, EmailStr, field_validator, Field
from datetime import date
import re


class ContactModel(BaseModel):
    name: str
    email: EmailStr
    phone_number: str
    date_of_birth: date
    additional_info: str | None = None
    user_id: int = Field(1, gt=0)

    @field_validator("phone_number")
    def validate_phone_number(cls, v):

        pattern = r"^\+\d{10,15}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid phone number format (e.g., +1234567890)")
        return v


class ContactCreate(ContactModel):
    pass


class ContactUpdate(ContactModel):
    pass


class Contact(ContactModel):
    id: int

    class Config:
        from_attributes = True
