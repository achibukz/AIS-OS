from unittest.mock import patch
from fastapi.testclient import TestClient
import server

client = TestClient(server.app)


def test_index_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "scribe" in response.text
    assert "yt-form" in response.text


def test_youtube_invalid_url():
    response = client.post("/api/youtube", json={"url": "https://invalid-site.com/video"})
    assert response.status_code == 400


def test_youtube_valid_url_queuing():
    with patch("server.fetch_youtube_metadata") as mock_meta:
        mock_meta.return_value = {
            "title": "Rick Astley - Never Gonna Give You Up",
            "duration": 213.0,
            "uploader": "Rick Astley",
        }
        response = client.post(
            "/api/youtube",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
        assert response.status_code == 200
        jobs = response.json()
        assert len(jobs) > 0
        latest = jobs[-1]
        assert latest["name"] == "Rick Astley - Never Gonna Give You Up"
        assert latest["status"] == "queued"
        assert latest["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
