"""Unit tests for LLM client (app/services/llm.py).

All HTTP calls are mocked — no real API requests.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.unit


def _mock_response(json_data, status_code=200):
    """Build a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        import httpx
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=resp
        )
    return resp


def _openai_chat_response(content="Hello from LLM"):
    return {
        "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }


def _patch_httpx():
    """Patch httpx.AsyncClient so that async-with yields a mock client."""
    mock_client = AsyncMock()
    ctx = AsyncMock()
    ctx.__aenter__.return_value = mock_client
    patcher = patch("app.services.llm.httpx.AsyncClient", return_value=ctx)
    return patcher, mock_client


class TestChatCompletion:
    @pytest.mark.asyncio
    async def test_success(self):
        patcher, mock_client = _patch_httpx()
        mock_client.post.return_value = _mock_response(_openai_chat_response("回答内容"))

        with patcher:
            from app.services.llm import chat_completion
            result = await chat_completion("system", "user msg")

        assert result == "回答内容"

    @pytest.mark.asyncio
    async def test_request_payload_structure(self):
        """Verify the JSON payload sent to the LLM API."""
        patcher, mock_client = _patch_httpx()
        mock_client.post.return_value = _mock_response(_openai_chat_response())

        with patcher:
            from app.services.llm import chat_completion
            await chat_completion("sys prompt", "user question", temperature=0.7, max_tokens=512)

        call_kwargs = mock_client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["messages"][0] == {"role": "system", "content": "sys prompt"}
        assert payload["messages"][1] == {"role": "user", "content": "user question"}
        assert payload["temperature"] == 0.7
        assert payload["max_tokens"] == 512
        assert "model" in payload

    @pytest.mark.asyncio
    async def test_authorization_header(self):
        """Verify Authorization header uses OPENROUTER_API_KEY."""
        patcher, mock_client = _patch_httpx()
        mock_client.post.return_value = _mock_response(_openai_chat_response())

        with patcher:
            from app.services.llm import chat_completion
            await chat_completion("s", "u")

        call_kwargs = mock_client.post.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")

    @pytest.mark.asyncio
    async def test_default_temperature_and_max_tokens(self):
        patcher, mock_client = _patch_httpx()
        mock_client.post.return_value = _mock_response(_openai_chat_response())

        with patcher:
            from app.services.llm import chat_completion
            await chat_completion("s", "u")

        payload = mock_client.post.call_args.kwargs.get("json") or mock_client.post.call_args[1].get("json")
        assert payload["temperature"] == 0.3
        assert payload["max_tokens"] == 1024

    @pytest.mark.asyncio
    async def test_http_error_raises(self):
        patcher, mock_client = _patch_httpx()
        mock_client.post.return_value = _mock_response({}, status_code=429)

        with patcher:
            import httpx
            from app.services.llm import chat_completion
            with pytest.raises(httpx.HTTPStatusError):
                await chat_completion("s", "u")

    @pytest.mark.asyncio
    async def test_malformed_response_raises(self):
        """Missing 'choices' key should raise KeyError."""
        patcher, mock_client = _patch_httpx()
        mock_client.post.return_value = _mock_response({"error": "bad"})

        with patcher:
            from app.services.llm import chat_completion
            with pytest.raises(KeyError):
                await chat_completion("s", "u")

    @pytest.mark.asyncio
    async def test_empty_content_returned(self):
        patcher, mock_client = _patch_httpx()
        mock_client.post.return_value = _mock_response(_openai_chat_response(""))

        with patcher:
            from app.services.llm import chat_completion
            result = await chat_completion("s", "u")

        assert result == ""
