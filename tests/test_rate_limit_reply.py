from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from phoboi.api import ApiHandler
from phoboi.providers.errors import RATE_LIMIT_MESSAGE, is_rate_limit_error
from phoboi.providers.gemini import ProviderError


@pytest.mark.parametrize("attribute", ["code", "status_code", "response"])
def test_wrapped_sdk_rate_limit_becomes_friendly_api_reply(monkeypatch, attribute):
    sdk_error = RuntimeError("private provider diagnostic")
    setattr(sdk_error, attribute, SimpleNamespace(status_code=429) if attribute == "response" else 429)
    wrapped = ProviderError("provider request failed")
    wrapped.__cause__ = sdk_error
    monkeypatch.setattr("phoboi.api.Settings.from_env", lambda: SimpleNamespace(source_mode="test", app_env="test"))
    monkeypatch.setattr("phoboi.api.source_store_for_mode", lambda *args, **kwargs: None)
    monkeypatch.setattr("phoboi.api.create_provider", Mock(side_effect=wrapped))
    handler = object.__new__(ApiHandler)
    body = b'{"message": "hello"}'
    handler.path = "/api/chat"
    handler.headers = {"Content-Length": str(len(body))}
    handler.rfile = BytesIO(body)
    handler._send_json = Mock()

    handler.do_POST()

    handler._send_json.assert_called_once_with(
        429, {"error": RATE_LIMIT_MESSAGE, "code": "MODEL_RATE_LIMITED"}
    )


@pytest.mark.parametrize("status", [400, 401, 403, 500, 503])
def test_other_errors_are_not_mislabeled_as_quota(status):
    error = RuntimeError("request failed; model name includes 429")
    error.status_code = status
    assert not is_rate_limit_error(error)


def test_exception_chain_cycle_does_not_loop():
    error = RuntimeError("failure")
    error.__cause__ = error
    assert not is_rate_limit_error(error)
