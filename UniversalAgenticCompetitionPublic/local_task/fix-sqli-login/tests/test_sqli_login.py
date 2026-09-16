def test_login_rejects_comment_bypass_payload(client):
    r = client.post("/login", json={"username": "admin'--", "password": "x"})
    assert r.status_code != 200, (
        "login SQL injection bypass still works for comment payload; "
        f"status={r.status_code}, body={r.text}"
    )


def test_login_rejects_or_bypass_payload(client):
    r = client.post(
        "/login",
        json={"username": "admin' OR '1'='1", "password": "x"},
    )
    assert r.status_code != 200, (
        "login SQL injection bypass still works for OR payload; "
        f"status={r.status_code}, body={r.text}"
    )
