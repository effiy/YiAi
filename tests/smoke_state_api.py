"""
Gate A MVP Smoke Test for session-state-infrastructure
Uses FastAPI TestClient as context manager to keep event loop alive.
"""
import sys
sys.path.insert(0, "/var/www/YiAi/src")

from fastapi.testclient import TestClient
from main import create_app

def test_create_and_query():
    app = create_app(init_db=False, init_rss=False, enable_auth=False)

    with TestClient(app) as client:
        # Create a state record
        resp = client.post("/state/records", json={
            "record_type": "test_smoke",
            "title": "Gate A MVP",
            "payload": {"key": "value"},
            "tags": ["smoke"]
        })
        assert resp.status_code == 201, f"Create failed: {resp.text}"
        data = resp.json()
        assert "key" in data, f"Missing key in response: {data}"
        record_key = data["key"]
        print(f"[PASS] Created record with key={record_key}")

        # Query the record
        resp = client.get("/state/records", params={"record_type": "test_smoke"})
        assert resp.status_code == 200, f"Query failed: {resp.text}"
        data = resp.json()
        assert "list" in data, f"Missing list in response: {data}"
        assert any(r["key"] == record_key for r in data["list"]), "Created record not found in query"
        print(f"[PASS] Queried record, total={data.get('total')}")

        # Get by key
        resp = client.get(f"/state/records/{record_key}")
        assert resp.status_code == 200, f"Get failed: {resp.text}"
        data = resp.json()
        assert data["key"] == record_key
        print(f"[PASS] Get record by key")

        # Update
        resp = client.put(f"/state/records/{record_key}", json={
            "record_type": "test_smoke",
            "title": "Updated title",
            "payload": {"updated": True},
            "tags": ["smoke", "updated"]
        })
        assert resp.status_code == 200, f"Update failed: {resp.text}"
        print(f"[PASS] Updated record")

        # Delete
        resp = client.delete(f"/state/records/{record_key}")
        assert resp.status_code == 200, f"Delete failed: {resp.text}"
        print(f"[PASS] Deleted record")

    print("\n[GATE A PASSED] MVP smoke test successful.")

if __name__ == "__main__":
    try:
        test_create_and_query()
    except AssertionError as e:
        print(f"\n[GATE A FAILED] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[GATE A ERROR] {e}")
        sys.exit(1)
