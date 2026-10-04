import pytest

from app.main import create_app, is_valid_url


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_health_endpoint_returns_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


def test_index_reports_serving_instance(client):
    res = client.get("/")
    assert res.status_code == 200
    body = res.get_json()
    assert body["service"] == "url-shortener"
    assert body["served_by"]  # container / host id is present


def test_shorten_creates_code(client):
    res = client.post("/shorten", json={"url": "https://example.com/page"})
    assert res.status_code == 201
    body = res.get_json()
    assert len(body["code"]) == 6
    assert body["original_url"] == "https://example.com/page"


def test_redirect_to_original_url(client):
    code = client.post("/shorten", json={"url": "https://example.com"}).get_json()["code"]
    res = client.get(f"/{code}")
    assert res.status_code == 302
    assert res.headers["Location"] == "https://example.com"


def test_shorten_rejects_invalid_url(client):
    for bad in ["not-a-url", "ftp://example.com", "", None, 123]:
        res = client.post("/shorten", json={"url": bad})
        assert res.status_code == 400


def test_shorten_rejects_missing_body(client):
    res = client.post("/shorten")
    assert res.status_code == 400


def test_unknown_code_returns_404(client):
    res = client.get("/abc123")
    assert res.status_code == 404


def test_stats_counts_links(client):
    assert client.get("/stats").get_json()["total_links"] == 0
    client.post("/shorten", json={"url": "https://example.com"})
    assert client.get("/stats").get_json()["total_links"] == 1


def test_is_valid_url_helper():
    assert is_valid_url("https://example.com")
    assert is_valid_url("http://example.com/a?b=1")
    assert not is_valid_url("example.com")
    assert not is_valid_url("javascript:alert(1)")
