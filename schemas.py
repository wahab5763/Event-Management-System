"""Request and response schemas for the event management API."""

from datetime import date as DateValue
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


def _clean_required_text(value: str) -> str:
    """Trim text fields and reject values made only of whitespace."""
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("This field must not be empty.")
    return cleaned


class EventCreate(BaseModel):
    """Fields required to create an event."""

    title: str = Field(min_length=1, max_length=150, examples=["Python Community Meetup"])
    description: str | None = Field(
        default=None,
        max_length=2000,
        examples=["An evening of talks and networking."],
    )
    date: DateValue = Field(examples=["2026-12-10"])
    location: str = Field(min_length=1, max_length=200, examples=["City Conference Hall"])
    max_capacity: int = Field(gt=0, examples=[80])

    @field_validator("title", "location")
    @classmethod
    def clean_required_text(cls, value: str) -> str:
        """Normalize required text before saving it."""
        return _clean_required_text(value)

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str | None) -> str | None:
        """Trim a description while preserving an omitted description."""
        if value is None:
            return None
        return value.strip() or None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Python Community Meetup",
                    "description": "An evening of talks and networking.",
                    "date": "2026-12-10",
                    "location": "City Conference Hall",
                    "max_capacity": 80,
                }
            ]
        }
    )


class EventUpdate(BaseModel):
    """Optional fields that can be changed on an existing event."""

    title: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    date: DateValue | None = None
    location: str | None = Field(default=None, min_length=1, max_length=200)
    max_capacity: int | None = Field(default=None, gt=0)

    @field_validator("title", "location")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        """Normalize optional text when a value is supplied."""
        if value is None:
            return None
        return _clean_required_text(value)

    @field_validator("description")
    @classmethod
    def clean_optional_description(cls, value: str | None) -> str | None:
        """Trim a supplied description."""
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def require_a_change(self) -> "EventUpdate":
        """Reject empty updates and nulls for fields that cannot be cleared."""
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        for field in ("title", "date", "location", "max_capacity"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null.")
        return self


class EventResponse(BaseModel):
    """Public event representation."""

    id: int
    title: str
    description: str | None
    date: DateValue
    location: str
    max_capacity: int

    model_config = ConfigDict(from_attributes=True)


class RegistrationCreate(BaseModel):
    """Attendee details used to register for an event."""

    attendee_name: str = Field(min_length=1, max_length=120, examples=["Jordan Lee"])
    email: EmailStr = Field(examples=["jordan@example.com"])

    @field_validator("attendee_name")
    @classmethod
    def clean_attendee_name(cls, value: str) -> str:
        """Normalize attendee names."""
        return _clean_required_text(value)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        """Store email addresses in a consistent case."""
        return str(value).strip().lower()

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"attendee_name": "Jordan Lee", "email": "jordan@example.com"}
            ]
        }
    )


class RegistrationResponse(BaseModel):
    """Public registration representation."""

    id: int
    event_id: int
    attendee_name: str
    email: EmailStr
    registered_at: datetime

    model_config = ConfigDict(from_attributes=True)


