"""Business rules and database operations for events and registrations."""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Event, Registration
from schemas import EventCreate, EventUpdate, RegistrationCreate


def create_event(session: Session, data: EventCreate) -> Event:
    """Create and return an event."""
    event = Event(**data.model_dump())
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def list_events(session: Session) -> list[Event]:
    """Return all events ordered by date."""
    statement = select(Event).order_by(Event.date, Event.id)
    result = session.scalars(statement)
    return list(result.all())


def get_event(session: Session, event_id: int) -> Event:
    """Find an event or raise a readable not-found response."""
    event = session.get(Event, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} was not found.",
        )
    return event


def update_event(
    session: Session,
    event_id: int,
    data: EventUpdate,
) -> Event:
    """Apply an event update while preserving registration capacity."""
    event = session.scalar(
        select(Event).where(Event.id == event_id).with_for_update()
    )
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} was not found.",
        )
    changes = data.model_dump(exclude_unset=True)

    new_capacity = changes.get("max_capacity")
    if new_capacity is not None:
        registration_count = session.scalar(
            select(func.count(Registration.id)).where(
                Registration.event_id == event_id
            )
        )
        if new_capacity < (registration_count or 0):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Capacity cannot be lower than the current number of registrations.",
            )

    for field, value in changes.items():
        setattr(event, field, value)
    session.commit()
    session.refresh(event)
    return event


def delete_event(session: Session, event_id: int) -> None:
    """Delete an event and its registrations."""
    event = get_event(session, event_id)
    session.delete(event)
    session.commit()


def create_registration(
    session: Session,
    event_id: int,
    data: RegistrationCreate,
) -> Registration:
    """Register an attendee if the event exists, has space, and is not a duplicate."""
    event = session.scalar(
        select(Event).where(Event.id == event_id).with_for_update()
    )
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} was not found.",
        )

    existing = session.scalar(
        select(Registration.id).where(
            Registration.event_id == event_id,
            Registration.email == str(data.email),
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This attendee is already registered for the event.",
        )

    count = session.scalar(
        select(func.count(Registration.id)).where(
            Registration.event_id == event_id
        )
    )
    if (count or 0) >= event.max_capacity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This event has reached its registration capacity.",
        )

    registration = Registration(
        event_id=event_id,
        attendee_name=data.attendee_name,
        email=str(data.email),
    )
    session.add(registration)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This attendee is already registered for the event.",
        ) from None
    session.refresh(registration)
    return registration


def list_registrations(session: Session, event_id: int) -> list[Registration]:
    """Return all registrations for an existing event."""
    get_event(session, event_id)
    result = session.scalars(
        select(Registration)
        .where(Registration.event_id == event_id)
        .order_by(Registration.id)
    )
    return list(result.all())


def delete_registration(session: Session, registration_id: int) -> None:
    """Delete a registration or raise a not-found response."""
    registration = session.get(Registration, registration_id)
    if registration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registration {registration_id} was not found.",
        )
    session.delete(registration)
    session.commit()
