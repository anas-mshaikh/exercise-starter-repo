# Event Log API

A simple event logging and analytics API built with FastAPI.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`

## Test

```bash
pytest -v
```

## API Endpoints

### POST /events
Create a new event.

### GET /events/{event_id}
Retrieve a single event by ID.

---

*Additional endpoints are planned. See the exercise prompt for details.*
