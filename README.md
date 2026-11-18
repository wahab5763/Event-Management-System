# Event Management API

A simple FastAPI and PostgreSQL API for managing events and attendee
registrations.

## Setup

1. Install Python 3.10 or newer and PostgreSQL.
2. Install the project dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set your PostgreSQL password. The default
   database name is `ems_db`.
4. Start the API:

   ```powershell
   python -m uvicorn main:app --reload
   ```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to use Swagger.
The root URL redirects to `/docs`. Tables are created automatically when the
app starts.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/events` | Create an event |
| `GET` | `/events` | List all events |
| `GET` | `/events/{event_id}` | Get an event |
| `PUT` | `/events/{event_id}` | Update an event |
| `DELETE` | `/events/{event_id}` | Delete an event |
| `POST` | `/events/{event_id}/registrations` | Register an attendee |
| `GET` | `/events/{event_id}/registrations` | List event registrations |
| `DELETE` | `/registrations/{registration_id}` | Cancel a registration |

Registration rejects missing events, duplicate attendee emails, and events at
capacity. Invalid request data returns `422`; missing records return `404`;
duplicate or full registrations return `409`.

## Project files

- `db.py` — PostgreSQL connection and database sessions.
- `models.py` — event and registration database models.
- `schemas.py` — request validation and response schemas.
- `services.py` — database operations and business rules.
- `main.py` — API routes and Swagger documentation.

