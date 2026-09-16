def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200


def test_login_valid(client):
    r = client.post("/login", json={"username": "admin", "password": "secret123"})
    assert r.status_code == 200
    assert "token" in r.json()


def test_login_wrong_password(client):
    r = client.post("/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


# --- Items / Search Tests ---


def test_search_returns_results(client):
    r = client.get("/search?q=timeout")
    assert r.status_code == 200
    names = [item["name"] for item in r.json()]
    assert "Fix login timeout" in names


def test_search_empty_query(client):
    r = client.get("/search?q=")
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_list_items_with_filter(client):
    r = client.get("/items?status=open")
    assert r.status_code == 200
    for item in r.json():
        assert item["status"] == "open"


def test_create_update_delete_item(client):
    # Create
    r = client.post(
        "/items",
        json={
            "name": "Test Item",
            "description": "Test Desc",
            "status": "open",
            "priority": "high",
            "owner_id": 1,
        },
    )
    assert r.status_code == 200
    item_id = r.json()["id"]

    # Update
    r = client.put(f"/items/{item_id}", json={"status": "closed"})
    assert r.status_code == 200
    assert r.json()["status"] == "closed"

    # Delete
    r = client.delete(f"/items/{item_id}")
    assert r.status_code == 200

    # Verify deleted
    r = client.get(f"/items/{item_id}")
    assert r.status_code == 404


def test_get_item_not_found(client):
    r = client.get("/items/99999")
    assert r.status_code == 404


# --- Comments Tests ---


def test_list_comments(client):
    r = client.get("/items/1/comments")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_comment(client):
    r = client.post(
        "/items/1/comments", json={"author_id": 1, "body": "New test comment"}
    )
    assert r.status_code == 200
    assert r.json()["body"] == "New test comment"


# --- Tags Tests ---


def test_list_tags(client):
    r = client.get("/tags")
    assert r.status_code == 200
    names = [t["name"] for t in r.json()]
    assert "bug" in names


def test_create_tag(client):
    r = client.post("/tags", json={"name": "test-tag"})
    assert r.status_code == 200
    assert r.json()["name"] == "test-tag"


def test_add_remove_item_tag(client):
    # Add
    r = client.post("/items/2/tags", json={"tag_id": 1})
    assert r.status_code == 200

    # Remove
    r = client.delete("/items/2/tags/1")
    assert r.status_code == 200


# --- Users Tests ---


def test_list_users(client):
    r = client.get("/users")
    assert r.status_code == 200
    assert len(r.json()) >= 3


def test_get_user(client):
    r = client.get("/users/1")
    assert r.status_code == 200
    assert r.json()["username"] == "admin"
