import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.tiktok_api import TikTokAPI  # noqa: E402
from utils.custom_exceptions import TikTokRecorderError  # noqa: E402
from utils.utils import parse_json  # noqa: E402


class HtmlResponse:
    """What TikTok sends when a request is blocked or rate-limited."""

    text = "<html><body>Please wait...</body></html>"
    status_code = 200

    def json(self):
        raise json.JSONDecodeError("Expecting value", self.text, 0)

    def raise_for_status(self):
        return None


class EmptyResponse:
    text = ""

    def json(self):
        raise json.JSONDecodeError("Expecting value", "", 0)


class ListResponse:
    def json(self):
        return [1, 2, 3]


class FakeHttpClient:
    def __init__(self, response):
        self.response = response
        self.urls = []

    def get(self, url, **kwargs):
        self.urls.append(url)
        return self.response


def build_api(response):
    api = TikTokAPI.__new__(TikTokAPI)
    api.BASE_URL = "https://www.tiktok.com"
    api.WEBCAST_URL = "https://webcast.tiktok.com"
    api.TIKREC_API = "https://tikrec.com"
    api.EULER_API = "https://tiktok.eulerstream.com"
    api.http_client = FakeHttpClient(response)
    return api


def test_parse_json_raises_readable_error_on_html():
    with pytest.raises(TikTokRecorderError) as ctx:
        parse_json(HtmlResponse(), "room info")

    message = str(ctx.value)
    assert "room info" in message
    assert "non-JSON response" in message
    assert "Please wait" in message


def test_parse_json_raises_on_empty_body():
    with pytest.raises(TikTokRecorderError) as ctx:
        parse_json(EmptyResponse(), "check_alive")

    assert "empty body" in str(ctx.value)


def test_parse_json_rejects_non_object_payload():
    with pytest.raises(TikTokRecorderError) as ctx:
        parse_json(ListResponse(), "room info")

    assert "unexpected JSON payload" in str(ctx.value)


def test_is_room_alive_does_not_crash_on_blocked_response():
    api = build_api(HtmlResponse())

    with pytest.raises(TikTokRecorderError):
        api.is_room_alive("1234567890")


def test_get_room_id_from_user_does_not_crash_on_blocked_response():
    api = build_api(HtmlResponse())

    with pytest.raises(TikTokRecorderError):
        api.get_room_id_from_user("someone")
