## Purpose
This file gives immediate, actionable context for an AI coding agent to be productive in this repository.

## Big picture (what this repo runs)
- A FastAPI-based REST service that exposes the API under `/api/event-manager/` (see `app/main.py`).
- Primary data is stored in two places:
  - Relational: Peewee models (defined in `app/main.py`) — used for `Evenimente`, `Pachete`, `Bilete`, `Join_PE`, `Utilizatori`.
  - Document DB: MongoDB used for `clients` collection (`pymongo` client created in `app/main.py` and an alternative initializer in `app/databases/mongo_db.py`).
- There is also a gRPC IDM service dependency: the FastAPI app creates a stub at `localhost:50051` using `IDM_pb2_grpc` and `IDM_pb2` (generated files are present under `app/`).
- Docker-compose defines `fastapi`, `mongodb`, and `nginx` services (see `docker-compose.yml`). The FastAPI Docker image runs `uvicorn main:app` inside the `app/` directory.

## Key files and what to look at first
- `app/main.py` — canonical source of the HTTP API, models, DB connections and auth logic. Read this file to understand endpoints and validation patterns.
- `app/databases/dbs.py` — default Peewee `SqliteDatabase("event_manager.db")` (but `main.py` overrides with a MySQLDatabase instance).
- `app/databases/mongo_db.py` — helper that returns a `mongo_db` client (used by the app in some places, although `main.py` also creates a `MongoClient` directly).
- `app/IDM.proto`, `app/IDM_pb2.py`, `app/IDM_pb2_grpc.py` — gRPC proto and generated code for the IAM/IDM service.
- `app/Dockerfile`, `docker-compose.yml` — container run configuration and environment variables.
- `logging.yaml` — uvicorn/uvlog configuration used by the container.

## Important runtime details and developer workflows
- Local dev (fast): run FastAPI with uvicorn from repo root:
  - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
  - The Dockerfile expects to run inside `app/` with `CMD ["uvicorn", "main:app", ...]`.
- Containerized: `docker-compose up --build` (uses `mongodb` service and maps `27017:27017`). Ensure `.env` or environment contains the Mongo credentials referenced in `docker-compose.yml` (e.g. `MONGO_INITDB_ROOT_USERNAME`, `MONGO_INITDB_ROOT_PASSWORD`, plus any `MONGO_*` variables the app expects).
- OpenAPI: the app exposes OpenAPI under `/api/event-manager/openapi.json` and standard docs will be available if running uvicorn with default FastAPI docs.

## Observed conventions and patterns (project-specific)
- Endpoint prefix: All API routes start with `/api/event-manager/`.
- Models are defined inline in `app/main.py` as Peewee `Model` subclasses (not in a separate `models/` package).
- Mongo access is direct (`dbmongo = client['event_manager']` then `collection = dbmongo['clients']`) and uses Pydantic models for request validation (`ClientModel` in `main.py`).
- Content-type checks: handlers commonly check `request.headers.get('content-type') == 'application/json'` and return `415` when missing.
- Pagination pattern: many endpoints accept `page` and `items_per_page` and slice Python lists after querying Peewee or Mongo.
- Authentication: JWTs created with `secrets.token_hex(64)` at module import time and used with the `Authorization` header. Note: `SECRET_KEY` is generated at runtime in `main.py` (not read from env), so the token will change on restart.

## Integration points and external dependencies
- MongoDB: the app expects a Mongo server at `mongodb:27017` inside Docker (or `localhost:27017` when run locally). Docker-compose maps ports.
- MySQL: `main.py` instantiates a `MySQLDatabase('event_manager', user='root', password='root', host='localhost', port=3306)`; the repo does not provide a MySQL service in `docker-compose.yml` — take care when running in containers (either provide a MySQL service or switch to the `SqliteDatabase` in `app/databases/dbs.py`).
- gRPC IDM: the app opens an insecure channel to `localhost:50051` and uses `IDM_pb2_grpc.IDMServiceStub`. Make sure the IDM service is available at that host/port during integration tests.

## Common pitfalls to watch for
- Hardcoded secrets and credentials: `SECRET_KEY` is generated on import — for repeatable tokens and tests, replace with a stable secret via env var.
- Mixed DB configs: `app/databases/dbs.py` uses SQLite by default; `app/main.py` constructs a MySQLDatabase directly. Search for `db =` in the repo to see which is in use.
- `main.py` is large; small changes can have broad effects. Prefer focused edits and run the app to verify behavior.
- Some endpoints reference variables (like `clients` vs `client`) that may be bugs — run linting / tests after making changes.

## Examples (useful snippets)
- Create event (curl):
  - `curl -X POST "http://localhost:8000/api/event-manager/events" -H "Content-Type: application/json" -d '{"ID_OWNER":1,"nume":"Concert","locatie":"Sala","descriere":"rock","numarLocuri":100}'`
- Create client (requires `x-user` header):
  - `curl -X POST "http://localhost:8000/api/event-manager/clients" -H "Content-Type: application/json" -H "x-user: admin" -d '{"email":"a@b.com","lista_bilete":[],"prenume_nume":{"value":"Ana"}}'`

## Where to change things safely
- Small API changes: edit `app/main.py` and add unit tests (no tests found in repo). Run locally with `uvicorn` to validate.
- DB migration or model moves: consider extracting Peewee models from `main.py` into `app/models.py` and updating imports to keep `main.py` focused on routing.

## If you need more info
- Ask for the desired target environment (local dev vs composed containers) and whether you want secrets moved to environment variables.
- Tell me if you want me to add a note to convert `SECRET_KEY`, centralize DB config, or scaffold tests — I can draft follow-up PRs.

-- End of instructions
