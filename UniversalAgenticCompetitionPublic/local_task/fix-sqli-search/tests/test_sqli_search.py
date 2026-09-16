def test_search_does_not_leak_users_table_with_union_payload(client):
    payload = (
        "x' UNION SELECT 1, username, password, 'open', 'high', 1, now(), now() "
        "FROM users--"
    )
    r = client.get("/search", params={"q": payload})
    assert r.status_code == 200, (
        f"search endpoint failed: status={r.status_code}, body={r.text}"
    )

    leaked_body = r.text
    leaked_values = ["admin", "secret123", "alice", "pass-alice", "bob", "pass-bob"]
    leaked = [value for value in leaked_values if value in leaked_body]
    assert not leaked, (
        "search SQL injection leaked users table data; "
        f"leaked={leaked}, body={leaked_body}"
    )
