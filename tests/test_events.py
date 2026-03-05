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

    def test_create_event_timestamp_z_normalized_to_utc(self, client):
        response = client.post("/events", json={
            "category": "purchase",
            "payload": {"item": "widget", "amount": 29.99},
            "timestamp": "2026-03-01T12:00:00Z",
        })
        assert response.status_code == 201

        data = response.json()
        assert data["timestamp"] == "2026-03-01T12:00:00+00:00"

    def test_create_event_invalid_category(self, client):
        response = client.post("/events", json={
            "category": "invalid_category",
            "payload": {"key": "value"},
        })
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "invalid_input"
        assert "category" in data["error"]["message"].lower()

    def test_create_event_missing_payload(self, client):
        response = client.post("/events", json={
            "category": "click",
        })
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "invalid_input"
        assert "payload" in data["error"]["message"].lower()

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

    def test_get_event_invalid_id_returns_standard_error(self, client):
        response = client.get("/events/not-an-int")
        assert response.status_code == 422

        data = response.json()
        assert data["error"]["code"] == "invalid_input"
        assert "event_id" in data["error"]["message"].lower()


# --- GET /events ---


class TestListEvents:
    """Tests for the GET /events endpoint."""

    def test_list_events_empty_returns_200_and_empty_list(self, client):
        response = client.get("/events")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_events_sorted_by_timestamp_desc(self, client, create_event):
        e1 = create_event({
            "category": "click",
            "payload": {"n": 1},
            "user_id": "user_a",
            "timestamp": "2026-03-01T10:00:00Z",
        })
        e2 = create_event({
            "category": "page_view",
            "payload": {"n": 2},
            "user_id": "user_a",
            "timestamp": "2026-03-01T11:00:00+00:00",
        })
        e3 = create_event({
            "category": "error",
            "payload": {"n": 3},
            "user_id": "user_b",
            "timestamp": "2026-03-01T12:00:00+00:00",
        })

        response = client.get("/events")
        assert response.status_code == 200

        data = response.json()
        assert [row["id"] for row in data] == [e3["id"], e2["id"], e1["id"]]

    def test_list_events_combined_filters(self, client, create_event):
        e1 = create_event({
            "category": "click",
            "payload": {"n": 1},
            "user_id": "user_1",
            "timestamp": "2026-03-01T10:00:00Z",
        })
        create_event({
            "category": "click",
            "payload": {"n": 2},
            "user_id": "user_1",
            "timestamp": "2026-03-01T11:00:00Z",
        })
        create_event({
            "category": "click",
            "payload": {"n": 3},
            "user_id": "user_2",
            "timestamp": "2026-03-01T10:30:00Z",
        })
        create_event({
            "category": "page_view",
            "payload": {"n": 4},
            "user_id": "user_1",
            "timestamp": "2026-03-01T10:00:00Z",
        })

        response = client.get("/events", params={
            "category": "click",
            "user_id": "user_1",
            "start": "2026-03-01T10:00:00Z",
            "end": "2026-03-01T10:00:00Z",
        })
        assert response.status_code == 200
        assert response.json() == [e1]

    def test_list_events_invalid_timestamp_returns_standard_error(self, client):
        response = client.get("/events", params={"start": "not-a-timestamp"})
        assert response.status_code == 400

        data = response.json()
        assert data["error"]["code"] == "invalid_input"
        assert "timestamp" in data["error"]["message"].lower()

    def test_list_events_user_id_injection_returns_empty(self, client, create_event):
        create_event({
            "category": "click",
            "payload": {"n": 1},
            "user_id": "user_123",
        })
        create_event({
            "category": "click",
            "payload": {"n": 2},
            "user_id": "user_456",
        })

        response = client.get("/events", params={"user_id": "user_123' OR 1=1 --"})
        assert response.status_code == 200
        assert response.json() == []

    def test_list_events_invalid_category_returns_standard_error(self, client):
        response = client.get("/events", params={"category": "nope"})
        assert response.status_code == 400

        data = response.json()
        assert data["error"]["code"] == "invalid_input"
        assert "category" in data["error"]["message"].lower()

    def test_list_events_start_after_end_returns_standard_error(self, client):
        response = client.get("/events", params={
            "start": "2026-03-02T00:00:00Z",
            "end": "2026-03-01T00:00:00Z",
        })
        assert response.status_code == 400

        data = response.json()
        assert data["error"]["code"] == "invalid_input"
        assert "start" in data["error"]["message"].lower()


# --- DELETE /events/{event_id} ---


class TestDeleteEvent:
    """Tests for the DELETE /events/{event_id} endpoint."""

    def test_delete_event_returns_204_and_empty_body(self, client, create_event):
        created = create_event({
            "category": "click",
            "payload": {"n": 1},
        })

        response = client.delete(f"/events/{created['id']}")
        assert response.status_code == 204
        assert response.content == b""

        get_response = client.get(f"/events/{created['id']}")
        assert get_response.status_code == 404
        data = get_response.json()
        assert data["error"]["code"] == "not_found"

    def test_delete_nonexistent_event_returns_404_standard_error(self, client):
        response = client.delete("/events/99999")
        assert response.status_code == 404

        data = response.json()
        assert data["error"]["code"] == "not_found"
        assert "99999" in data["error"]["message"]


# --- GET /stats ---


class TestStats:
    """Tests for the GET /stats endpoint."""

    def test_stats_empty_returns_zeros_and_nulls(self, client):
        response = client.get("/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["total_events"] == 0
        assert data["events_by_category"] == {}
        assert data["unique_users"] == 0
        assert data["first_event"] is None
        assert data["last_event"] is None

    def test_stats_reflects_filters_and_category_counts(self, client, create_event):
        create_event({
            "category": "click",
            "payload": {"n": 1},
            "user_id": "user_1",
            "timestamp": "2026-03-01T10:00:00Z",
        })
        e2 = create_event({
            "category": "click",
            "payload": {"n": 2},
            "user_id": "user_2",
            "timestamp": "2026-03-01T11:00:00Z",
        })
        e3 = create_event({
            "category": "page_view",
            "payload": {"n": 3},
            "user_id": "user_2",
            "timestamp": "2026-03-01T12:00:00Z",
        })
        create_event({
            "category": "error",
            "payload": {"n": 4},
            "user_id": None,
            "timestamp": "2026-03-01T13:00:00Z",
        })

        response = client.get("/stats", params={
            "user_id": "user_2",
            "start": "2026-03-01T10:30:00Z",
            "end": "2026-03-01T12:30:00Z",
        })
        assert response.status_code == 200

        data = response.json()
        assert data["total_events"] == 2
        assert data["events_by_category"] == {"click": 1, "page_view": 1}
        assert data["unique_users"] == 1
        assert data["first_event"] == e2["timestamp"]
        assert data["last_event"] == e3["timestamp"]

    def test_stats_invalid_timestamp_returns_standard_error(self, client):
        response = client.get("/stats", params={"start": "not-a-timestamp"})
        assert response.status_code == 400

        data = response.json()
        assert data["error"]["code"] == "invalid_input"
        assert "timestamp" in data["error"]["message"].lower()

    def test_stats_start_after_end_returns_standard_error(self, client):
        response = client.get("/stats", params={
            "start": "2026-03-02T00:00:00Z",
            "end": "2026-03-01T00:00:00Z",
        })
        assert response.status_code == 400

        data = response.json()
        assert data["error"]["code"] == "invalid_input"
        assert "start" in data["error"]["message"].lower()
