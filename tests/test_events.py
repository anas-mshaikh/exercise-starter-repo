"""
Tests for event endpoints.

Naming convention: test_<action>_<condition>
Use fixtures from conftest.py for test data setup.
"""


# --- POST /events ---


class TestCreateEvent:
    """Tests for the POST /events endpoint."""

    def test_create_event_with_all_fields(self, client, sample_event):
        response = client.post("/events", json=sample_event)
        assert response.status_code == 201

        data = response.json()
        assert data["id"] is not None
        assert data["category"] == "page_view"
        assert data["payload"] == {"page": "/home", "referrer": "google.com"}
        assert data["user_id"] == "user_123"
        assert data["timestamp"] is not None

    def test_create_event_without_optional_fields(self, client):
        response = client.post("/events", json={
            "category": "click",
            "payload": {"button": "signup"},
        })
        assert response.status_code == 201

        data = response.json()
        assert data["user_id"] is None
        assert data["timestamp"] is not None

    def test_create_event_with_custom_timestamp(self, client):
        response = client.post("/events", json={
            "category": "purchase",
            "payload": {"item": "widget", "amount": 29.99},
            "timestamp": "2026-03-01T12:00:00-05:00",
        })
        assert response.status_code == 201

        data = response.json()
        # Timestamp should be normalized to UTC
        assert "17:00:00" in data["timestamp"]
        assert "+00:00" in data["timestamp"]

    def test_create_event_invalid_category(self, client):
        response = client.post("/events", json={
            "category": "invalid_category",
            "payload": {"key": "value"},
        })
        assert response.status_code == 422

    def test_create_event_missing_payload(self, client):
        response = client.post("/events", json={
            "category": "click",
        })
        assert response.status_code == 422

    def test_create_event_invalid_timestamp(self, client):
        response = client.post("/events", json={
            "category": "click",
            "payload": {"key": "value"},
            "timestamp": "not-a-timestamp",
        })
        assert response.status_code == 400

        data = response.json()
        assert data["error"]["code"] == "invalid_input"
        assert "timestamp" in data["error"]["message"].lower()


# --- GET /events/{event_id} ---


class TestGetEvent:
    """Tests for the GET /events/{event_id} endpoint."""

    def test_get_existing_event(self, client, create_event, sample_event):
        created = create_event(sample_event)

        response = client.get(f"/events/{created['id']}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == created["id"]
        assert data["category"] == "page_view"
        assert data["payload"] == sample_event["payload"]

    def test_get_nonexistent_event(self, client):
        response = client.get("/events/99999")
        assert response.status_code == 404

        data = response.json()
        assert data["error"]["code"] == "not_found"
        assert "99999" in data["error"]["message"]
