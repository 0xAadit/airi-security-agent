def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_valid(client):
    r = client.post("/login", json={"username": "admin", "password": "secret123"})
    assert r.status_code == 200
    assert "token" in r.json()


def test_login_wrong_password(client):
    r = client.post("/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


def test_search_returns_results(client):
    r = client.get("/search", params={"q": "timeout"})
    assert r.status_code == 200
    names = [item["name"] for item in r.json()]
    assert "Fix login timeout" in names


def test_list_items_with_filter(client):
    r = client.get("/items", params={"status": "open"})
    assert r.status_code == 200
    assert r.json()
    for item in r.json():
        assert item["status"] == "open"


def test_create_update_delete_item(client):
    r = client.post(
        "/items",
        json={
            "name": "Verifier Item",
            "description": "Created by hidden verifier tests",
            "status": "open",
            "priority": "high",
            "owner_id": 1,
        },
    )
    assert r.status_code == 200
    item_id = r.json()["id"]

    r = client.put(f"/items/{item_id}", json={"status": "closed"})
    assert r.status_code == 200
    assert r.json()["status"] == "closed"

    r = client.delete(f"/items/{item_id}")
    assert r.status_code == 200

    r = client.get(f"/items/{item_id}")
    assert r.status_code == 404


def test_comments_tags_and_users(client):
    r = client.get("/items/1/comments")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    r = client.post(
        "/items/1/comments", json={"author_id": 1, "body": "Verifier comment"}
    )
    assert r.status_code == 200
    assert r.json()["body"] == "Verifier comment"

    r = client.get("/tags")
    assert r.status_code == 200
    tag_names = [tag["name"] for tag in r.json()]
    assert "bug" in tag_names

    r = client.get("/users")
    assert r.status_code == 200
    users = r.json()
    assert len(users) >= 3
    assert all("password" not in user for user in users)
