"""FastAPI application and HTTP routes."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from db import create_tables, get_db
from schemas import (
    EventCreate,
    EventResponse,
    EventUpdate,
    RegistrationCreate,
    RegistrationResponse,
)
from services import (
    create_event,
    create_registration,
    delete_event,
    delete_registration,
    get_event,
    list_events,
    list_registrations,
    update_event,
)

DbSession = Annotated[Session, Depends(get_db)]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Create missing database tables when the application starts."""
    create_tables()
    yield


app = FastAPI(
    title="Event Management API",
    description="Manage company events and attendee registrations.",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Events", "description": "Create and manage events."},
        {"name": "Registrations", "description": "Register attendees for events."},
    ],
)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """Send browser visitors to the API documentation."""
    return RedirectResponse(
        url="/docs",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )


@app.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Events"],
    summary="Create an event",
    responses={409: {"description": "Event could not be created"}},
)
def create_event_route(data: EventCreate, session: DbSession) -> EventResponse:
    """Create an event."""
    return create_event(session, data)


@app.get(
    "/events",
    response_model=list[EventResponse],
    tags=["Events"],
    summary="List all events",
)
def list_events_route(session: DbSession) -> list[EventResponse]:
    """Return all events."""
    return list_events(session)


@app.get(
    "/events/{event_id}",
    response_model=EventResponse,
    tags=["Events"],
    summary="Get an event",
    responses={404: {"description": "Event not found"}},
)
def get_event_route(event_id: int, session: DbSession) -> EventResponse:
    """Return one event."""
    return get_event(session, event_id)


@app.put(
    "/events/{event_id}",
    response_model=EventResponse,
    tags=["Events"],
    summary="Update an event",
    responses={
        404: {"description": "Event not found"},
        409: {"description": "Capacity is below the registration count"},
    },
)
def update_event_route(
    event_id: int,
    data: EventUpdate,
    session: DbSession,
) -> EventResponse:
    """Update an event."""
    return update_event(session, event_id, data)


@app.delete(
    "/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    tags=["Events"],
    summary="Delete an event",
    responses={404: {"description": "Event not found"}},
)
def delete_event_route(event_id: int, session: DbSession) -> Response:
    """Delete an event and its registrations."""
    delete_event(session, event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/events/{event_id}/registrations",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Registrations"],
    summary="Register an attendee",
    responses={
        404: {"description": "Event not found"},
        409: {"description": "Duplicate registration or event at capacity"},
    },
)
def create_registration_route(
    event_id: int,
    data: RegistrationCreate,
    session: DbSession,
) -> RegistrationResponse:
    """Register an attendee for an event."""
    return create_registration(session, event_id, data)


@app.get(
    "/events/{event_id}/registrations",
    response_model=list[RegistrationResponse],
    tags=["Registrations"],
    summary="List event registrations",
    responses={404: {"description": "Event not found"}},
)
def list_registrations_route(
    event_id: int,
    session: DbSession,
) -> list[RegistrationResponse]:
    """Return all registrations for an event."""
    return list_registrations(session, event_id)


@app.delete(
    "/registrations/{registration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    tags=["Registrations"],
    summary="Cancel a registration",
    responses={404: {"description": "Registration not found"}},
)
def delete_registration_route(
    registration_id: int,
    session: DbSession,
) -> Response:
    """Delete a registration."""
    delete_registration(session, registration_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
