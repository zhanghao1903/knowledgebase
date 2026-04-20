"""Unit tests for Embedding client (app/services/embedding.py).

All HTTP calls are mocked — no real API requests.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.unit


def _mock_response(json_data, status_code=200):
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


def _embedding_response(vectors, start_index=0):
    """Build OpenAI-format embedding response."""
    return {
        "data": [
            {"embedding": vec, "index": start_index + i}
            for i, vec in enumerate(vectors)
        ],
        "model": "text-embedding-ada-002",
        "usage": {"prompt_tokens": 5, "total_tokens": 5},
    }


def _patch_httpx():
    mock_client = AsyncMock()
    ctx = AsyncMock()
    ctx.__aenter__.return_value = mock_client
    patcher = patch("app.services.embedding.httpx.AsyncClient", return_value=ctx)
    return patcher, mock_client


class TestGetEmbeddings:
    @pytest.mark.asyncio
    async def test_empty_input(self):
        from app.services.embedding import get_embeddings
        result = await get_embeddings([])
        assert result == []

    @pytest.mark.asyncio
    async def test_single_text(self):
        patcher, mock_client = _patch_httpx()
        vec = [0.1, 0.2, 0.3]
        mock_client.post.return_value = _mock_response(_embedding_response([vec]))

        with patcher:
            from app.services.embedding import get_embeddings
            result = await get_embeddings(["hello"])

        assert len(result) == 1
        assert result[0] == vec

    @pytest.mark.asyncio
    async def test_multiple_texts_single_batch(self):
        patcher, mock_client = _patch_httpx()
        vecs = [[0.1 * i] * 3 for i in range(5)]
        mock_client.post.return_value = _mock_response(_embedding_response(vecs))

        with patcher:
            from app.services.embedding import get_embeddings
            result = await get_embeddings(["t1", "t2", "t3", "t4", "t5"])

        assert len(result) == 5
        assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_batch_splitting(self):
        """More than BATCH_SIZE (64) texts should trigger multiple API calls."""
        patcher, mock_client = _patch_httpx()

        def side_effect(*args, **kwargs):
            texts = kwargs.get("json", {}).get("input", args[1]["input"] if len(args) > 1 else [])
            vecs = [[float(i)] * 3 for i in range(len(texts))]
            return _mock_response(_embedding_response(vecs))

        mock_client.post.side_effect = side_effect

        texts = [f"text_{i}" for i in range(100)]
        with patcher:
            from app.services.embedding import get_embeddings
            result = await get_embeddings(texts)

        assert len(result) == 100
        assert mock_client.post.call_count == 2  # 64 + 36

    @pytest.mark.asyncio
    async def test_response_sorted_by_index(self):
        """API may return items out of order; embeddings should match input order."""
        patcher, mock_client = _patch_httpx()
        # Return items in reverse order
        resp_data = {
            "data": [
                {"embedding": [0.3], "index": 2},
                {"embedding": [0.1], "index": 0},
                {"embedding": [0.2], "index": 1},
            ],
            "model": "test",
            "usage": {"prompt_tokens": 3, "total_tokens": 3},
        }
        mock_client.post.return_value = _mock_response(resp_data)

        with patcher:
            from app.services.embedding import get_embeddings
            result = await get_embeddings(["a", "b", "c"])

        assert result[0] == [0.1]
        assert result[1] == [0.2]
        assert result[2] == [0.3]

    @pytest.mark.asyncio
    async def test_request_payload_structure(self):
        patcher, mock_client = _patch_httpx()
        mock_client.post.return_value = _mock_response(_embedding_response([[0.1]]))

        with patcher:
            from app.services.embedding import get_embeddings
            await get_embeddings(["test text"])

        call_kwargs = mock_client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["input"] == ["test text"]
        assert "model" in payload

    @pytest.mark.asyncio
    async def test_authorization_uses_effective_key(self):
        patcher, mock_client = _patch_httpx()
        mock_client.post.return_value = _mock_response(_embedding_response([[0.1]]))

        with patcher:
            from app.services.embedding import get_embeddings
            await get_embeddings(["x"])

        call_kwargs = mock_client.post.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")

    @pytest.mark.asyncio
    async def test_http_error_raises(self):
        patcher, mock_client = _patch_httpx()
        mock_client.post.return_value = _mock_response({}, status_code=401)

        with patcher:
            import httpx
            from app.services.embedding import get_embeddings
            with pytest.raises(httpx.HTTPStatusError):
                await get_embeddings(["fail"])

    @pytest.mark.asyncio
    async def test_batch_boundary_exactly_64(self):
        """Exactly BATCH_SIZE texts should be one batch, not two."""
        patcher, mock_client = _patch_httpx()
        vecs = [[float(i)] for i in range(64)]
        mock_client.post.return_value = _mock_response(_embedding_response(vecs))

        with patcher:
            from app.services.embedding import get_embeddings
            result = await get_embeddings([f"t{i}" for i in range(64)])

        assert len(result) == 64
        assert mock_client.post.call_count == 1
