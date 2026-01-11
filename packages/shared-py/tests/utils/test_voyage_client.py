#!/usr/bin/env python3
"""
Test suite for voyage_client.py

Tests Voyage AI embedding API client with caching and rate limiting.
Critical for semantic search and embeddings functionality.
"""

import sys
import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import urllib.error

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.voyage_client import (
    EmbeddingResponse,
    EmbeddingUsage,
    VoyageClient,
    get_client,
    embed,
    embed_single,
    embed_query,
    embed_document,
    is_available,
    VOYAGE_MODEL,
    EMBEDDING_DIM,
    MAX_REQUESTS_PER_MINUTE,
    MAX_TOKENS_PER_MINUTE,
    BATCH_SIZE
)


class TestEmbeddingResponseDataClass:
    """Test EmbeddingResponse dataclass"""

    def test_embedding_response_creation(self):
        """Test creating an embedding response"""
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        response = EmbeddingResponse(
            embeddings=embeddings,
            model="voyage-3.5",
            usage={"total_tokens": 10}
        )

        assert response.embeddings == embeddings
        assert response.model == "voyage-3.5"
        assert response.usage["total_tokens"] == 10

    def test_embedding_response_default_usage(self):
        """Test default usage dict"""
        response = EmbeddingResponse(
            embeddings=[[0.1]],
            model="test"
        )

        assert response.usage == {}


class TestEmbeddingUsageDataClass:
    """Test EmbeddingUsage dataclass"""

    def test_usage_creation(self):
        """Test creating usage tracker"""
        usage = EmbeddingUsage()

        assert usage.total_tokens == 0
        assert usage.total_requests == 0
        assert usage.last_reset > 0

    def test_add_usage(self):
        """Test adding usage"""
        usage = EmbeddingUsage()

        usage.add(100)
        assert usage.total_tokens == 100
        assert usage.total_requests == 1

        usage.add(50)
        assert usage.total_tokens == 150
        assert usage.total_requests == 2

    def test_can_request_allowed(self):
        """Test request allowed when under limits"""
        usage = EmbeddingUsage()

        allowed, wait = usage.can_request(100)
        assert allowed is True
        assert wait == 0

    def test_can_request_request_limit(self):
        """Test request blocked when at request limit"""
        usage = EmbeddingUsage()

        # Add max requests
        for _ in range(MAX_REQUESTS_PER_MINUTE):
            usage.add(10)

        allowed, wait = usage.can_request(10)
        assert allowed is False
        assert wait > 0

    def test_can_request_token_limit(self):
        """Test request blocked when at token limit"""
        usage = EmbeddingUsage()

        # Add tokens close to limit
        usage.add(MAX_TOKENS_PER_MINUTE - 100)

        # Request that would exceed limit
        allowed, wait = usage.can_request(200)
        assert allowed is False
        assert wait > 0

    def test_usage_reset_after_minute(self):
        """Test usage resets after minute"""
        usage = EmbeddingUsage()

        # Add usage
        usage.add(1000)
        assert usage.total_tokens == 1000

        # Simulate time passing
        usage.last_reset = time.time() - 61

        # Next add should reset
        usage.add(100)
        assert usage.total_tokens == 100
        assert usage.total_requests == 1


class TestVoyageClientInit:
    """Test VoyageClient initialization"""

    def test_init_with_api_key(self):
        """Test initialization with API key"""
        client = VoyageClient(api_key="test-key-123")

        assert client.api_key == "test-key-123"
        assert client.model == VOYAGE_MODEL
        assert client.cache_enabled is True

    def test_init_from_env(self):
        """Test initialization from environment"""
        with patch.dict("os.environ", {"VOYAGE_API_KEY": "env-key-123"}):
            client = VoyageClient()

            assert client.api_key == "env-key-123"

    def test_init_no_api_key(self):
        """Test initialization without API key"""
        with patch.dict("os.environ", {}, clear=True):
            client = VoyageClient()

            assert client.api_key is None

    def test_init_custom_model(self):
        """Test initialization with custom model"""
        client = VoyageClient(api_key="test", model="custom-model")

        assert client.model == "custom-model"

    def test_init_cache_disabled(self):
        """Test initialization with caching disabled"""
        client = VoyageClient(api_key="test", cache_enabled=False)

        assert client.cache_enabled is False


class TestVoyageClientProperties:
    """Test VoyageClient properties"""

    def test_is_available_true(self):
        """Test is_available when API key set"""
        client = VoyageClient(api_key="test-key")

        assert client.is_available is True

    def test_is_available_false(self):
        """Test is_available when no API key"""
        with patch.dict("os.environ", {}, clear=True):
            client = VoyageClient()

            assert client.is_available is False

    def test_cache_size(self):
        """Test cache_size property"""
        client = VoyageClient(api_key="test")

        assert client.cache_size == 0

        # Manually add to cache
        client._cache["key1"] = [0.1, 0.2]
        client._cache["key2"] = [0.3, 0.4]

        assert client.cache_size == 2

    def test_usage_property(self):
        """Test usage property"""
        client = VoyageClient(api_key="test")

        usage = client.usage
        assert usage["total_tokens"] == 0
        assert usage["total_requests"] == 0

        # Add usage
        client._usage.add(100)

        usage = client.usage
        assert usage["total_tokens"] == 100
        assert usage["total_requests"] == 1


class TestVoyageClientCaching:
    """Test caching functionality"""

    def test_cache_key_generation(self):
        """Test cache key generation"""
        client = VoyageClient(api_key="test")

        key1 = client._cache_key("Hello, world!", "document")
        key2 = client._cache_key("Hello, world!", "query")
        key3 = client._cache_key("Different text", "document")

        # Same text, different type
        assert key1 != key2

        # Different text
        assert key1 != key3

        # Consistent
        assert key1 == client._cache_key("Hello, world!", "document")

    def test_clear_cache(self):
        """Test clearing cache"""
        client = VoyageClient(api_key="test")

        # Add to cache
        client._cache["key1"] = [0.1, 0.2]
        client._cache["key2"] = [0.3, 0.4]

        assert client.cache_size == 2

        count = client.clear_cache()

        assert count == 2
        assert client.cache_size == 0

    def test_clear_empty_cache(self):
        """Test clearing empty cache"""
        client = VoyageClient(api_key="test")

        count = client.clear_cache()
        assert count == 0


class TestVoyageClientEmbed:
    """Test embedding methods"""

    def test_embed_no_api_key(self):
        """Test embed raises error without API key"""
        with patch.dict("os.environ", {}, clear=True):
            client = VoyageClient()

            with pytest.raises(ValueError, match="VOYAGE_API_KEY not set"):
                client.embed(["test"])

    def test_embed_empty_list(self):
        """Test embed with empty list"""
        client = VoyageClient(api_key="test")

        result = client.embed([])
        assert result == []

    def test_embed_success(self):
        """Test successful embedding"""
        client = VoyageClient(api_key="test")

        # Mock API response
        mock_response = EmbeddingResponse(
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
            model="voyage-3.5",
            usage={"total_tokens": 10}
        )

        with patch.object(client, "_call_api_with_retry", return_value=mock_response):
            result = client.embed(["text1", "text2"])

        assert len(result) == 2
        assert result[0] == [0.1, 0.2]
        assert result[1] == [0.3, 0.4]

    def test_embed_uses_cache(self):
        """Test embed uses cache for repeated texts"""
        client = VoyageClient(api_key="test")

        # Pre-populate cache
        cache_key = client._cache_key("cached text", "document")
        client._cache[cache_key] = [0.1, 0.2, 0.3]

        # Mock API (should not be called for cached text)
        mock_response = EmbeddingResponse(
            embeddings=[[0.5, 0.6, 0.7]],
            model="voyage-3.5",
            usage={"total_tokens": 5}
        )

        with patch.object(client, "_call_api_with_retry", return_value=mock_response) as mock_call:
            result = client.embed(["cached text", "new text"])

            # Should only call API once (for new text)
            assert mock_call.call_count == 1

        assert result[0] == [0.1, 0.2, 0.3]  # From cache
        assert result[1] == [0.5, 0.6, 0.7]  # From API

    def test_embed_cache_disabled(self):
        """Test embed with cache disabled"""
        client = VoyageClient(api_key="test", cache_enabled=False)

        mock_response = EmbeddingResponse(
            embeddings=[[0.1, 0.2]],
            model="voyage-3.5",
            usage={"total_tokens": 5}
        )

        with patch.object(client, "_call_api_with_retry", return_value=mock_response) as mock_call:
            client.embed(["text1"])
            client.embed(["text1"])  # Should call API again

            assert mock_call.call_count == 2

    def test_embed_batch_processing(self):
        """Test embed handles batching"""
        client = VoyageClient(api_key="test")

        # Create texts that exceed batch size
        texts = [f"text{i}" for i in range(BATCH_SIZE + 10)]

        # Mock responses for each batch
        def mock_response_side_effect(batch_texts, input_type):
            # Return embeddings matching the batch size
            return EmbeddingResponse(
                embeddings=[[0.1, 0.2] for _ in range(len(batch_texts))],
                model="voyage-3.5",
                usage={"total_tokens": len(batch_texts) * 2}
            )

        with patch.object(client, "_call_api_with_retry", side_effect=mock_response_side_effect) as mock_call:
            result = client.embed(texts)

            # Should make 2 API calls (one full batch, one partial)
            assert mock_call.call_count == 2

        assert len(result) == len(texts)

    def test_embed_single(self):
        """Test embed_single method"""
        client = VoyageClient(api_key="test")

        mock_response = EmbeddingResponse(
            embeddings=[[0.1, 0.2, 0.3]],
            model="voyage-3.5",
            usage={"total_tokens": 5}
        )

        with patch.object(client, "_call_api_with_retry", return_value=mock_response):
            result = client.embed_single("test text")

        assert result == [0.1, 0.2, 0.3]
        assert isinstance(result, list)

    def test_embed_query(self):
        """Test embed_query method"""
        client = VoyageClient(api_key="test")

        mock_response = EmbeddingResponse(
            embeddings=[[0.1, 0.2]],
            model="voyage-3.5",
            usage={"total_tokens": 5}
        )

        with patch.object(client, "_call_api_with_retry", return_value=mock_response) as mock_call:
            result = client.embed_query("search query")

            # Verify input_type is "query"
            call_args = mock_call.call_args
            assert call_args[0][1] == "query"

        assert result == [0.1, 0.2]

    def test_embed_document(self):
        """Test embed_document method"""
        client = VoyageClient(api_key="test")

        mock_response = EmbeddingResponse(
            embeddings=[[0.1, 0.2]],
            model="voyage-3.5",
            usage={"total_tokens": 5}
        )

        with patch.object(client, "_call_api_with_retry", return_value=mock_response) as mock_call:
            result = client.embed_document("document text")

            # Verify input_type is "document"
            call_args = mock_call.call_args
            assert call_args[0][1] == "document"

        assert result == [0.1, 0.2]


class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_wait_for_rate_limit_allowed(self):
        """Test no wait when under limit"""
        client = VoyageClient(api_key="test")

        # Should not wait
        with patch("time.sleep") as mock_sleep:
            client._wait_for_rate_limit(100)
            mock_sleep.assert_not_called()

    def test_wait_for_rate_limit_blocked(self):
        """Test wait when rate limit would be exceeded"""
        client = VoyageClient(api_key="test")

        # Exhaust rate limit
        client._usage.total_requests = MAX_REQUESTS_PER_MINUTE

        with patch("time.sleep") as mock_sleep:
            client._wait_for_rate_limit(100)
            mock_sleep.assert_called_once()


class TestAPIRetry:
    """Test API retry functionality"""

    def test_call_api_with_retry_success_first_try(self):
        """Test successful API call on first try"""
        client = VoyageClient(api_key="test")

        mock_response = EmbeddingResponse(
            embeddings=[[0.1]],
            model="test",
            usage={}
        )

        with patch.object(client, "_call_api", return_value=mock_response) as mock_call:
            result = client._call_api_with_retry(["text"], "document")

            assert mock_call.call_count == 1
            assert result == mock_response

    def test_call_api_with_retry_success_after_retry(self):
        """Test successful API call after retry"""
        client = VoyageClient(api_key="test")

        mock_response = EmbeddingResponse(
            embeddings=[[0.1]],
            model="test",
            usage={}
        )

        # Fail first, succeed second
        with patch.object(client, "_call_api") as mock_call:
            mock_call.side_effect = [
                RuntimeError("500: Server error"),
                mock_response
            ]

            with patch("time.sleep"):
                result = client._call_api_with_retry(["text"], "document")

            assert mock_call.call_count == 2
            assert result == mock_response

    def test_call_api_with_retry_auth_error_no_retry(self):
        """Test auth errors are not retried"""
        client = VoyageClient(api_key="test")

        with patch.object(client, "_call_api") as mock_call:
            mock_call.side_effect = RuntimeError("401: Unauthorized")

            with pytest.raises(RuntimeError, match="401"):
                client._call_api_with_retry(["text"], "document")

            # Should not retry auth errors
            assert mock_call.call_count == 1

    def test_call_api_with_retry_bad_request_no_retry(self):
        """Test bad requests are not retried"""
        client = VoyageClient(api_key="test")

        with patch.object(client, "_call_api") as mock_call:
            mock_call.side_effect = RuntimeError("400: Bad request")

            with pytest.raises(RuntimeError, match="400"):
                client._call_api_with_retry(["text"], "document")

            # Should not retry bad requests
            assert mock_call.call_count == 1

    def test_call_api_with_retry_max_attempts(self):
        """Test max retry attempts"""
        client = VoyageClient(api_key="test")

        with patch.object(client, "_call_api") as mock_call:
            mock_call.side_effect = RuntimeError("500: Server error")

            with patch("time.sleep"):
                with pytest.raises(RuntimeError):
                    client._call_api_with_retry(["text"], "document", max_attempts=3)

            assert mock_call.call_count == 3

    def test_call_api_with_retry_exponential_backoff(self):
        """Test exponential backoff delay"""
        client = VoyageClient(api_key="test")

        with patch.object(client, "_call_api") as mock_call:
            mock_call.side_effect = RuntimeError("500: Server error")

            with patch("time.sleep") as mock_sleep:
                with pytest.raises(RuntimeError):
                    client._call_api_with_retry(["text"], "document", max_attempts=3, initial_delay=1.0)

            # Should have delays: 1.0, 2.0
            assert mock_sleep.call_count == 2
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert sleep_calls[0] == 1.0
            assert sleep_calls[1] == 2.0


class TestCallAPI:
    """Test _call_api method"""

    def test_call_api_success(self):
        """Test successful API call"""
        client = VoyageClient(api_key="test-key")

        mock_response_data = {
            "data": [
                {"embedding": [0.1, 0.2, 0.3]},
                {"embedding": [0.4, 0.5, 0.6]}
            ],
            "model": "voyage-3.5",
            "usage": {"total_tokens": 10}
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = client._call_api(["text1", "text2"], "document")

        assert len(result.embeddings) == 2
        assert result.embeddings[0] == [0.1, 0.2, 0.3]
        assert result.model == "voyage-3.5"
        assert result.usage["total_tokens"] == 10

    def test_call_api_http_error(self):
        """Test HTTP error handling"""
        client = VoyageClient(api_key="test-key")

        http_error = urllib.error.HTTPError(
            "https://api.voyageai.com",
            401,
            "Unauthorized",
            {},
            None
        )

        with patch("urllib.request.urlopen", side_effect=http_error):
            with pytest.raises(RuntimeError, match="401"):
                client._call_api(["text"], "document")

    def test_call_api_network_error(self):
        """Test network error handling"""
        client = VoyageClient(api_key="test-key")

        url_error = urllib.error.URLError("Network unreachable")

        with patch("urllib.request.urlopen", side_effect=url_error):
            with pytest.raises(RuntimeError, match="Network error"):
                client._call_api(["text"], "document")


class TestModuleFunctions:
    """Test module-level convenience functions"""

    def test_get_client_singleton(self):
        """Test get_client returns singleton"""
        # Reset singleton
        import popkit_shared.utils.voyage_client as vc
        vc._client = None

        client1 = get_client()
        client2 = get_client()

        assert client1 is client2

    def test_embed_convenience(self):
        """Test embed convenience function"""
        with patch("popkit_shared.utils.voyage_client.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.embed.return_value = [[0.1, 0.2]]
            mock_get.return_value = mock_client

            result = embed(["text"], "document")

            mock_client.embed.assert_called_once_with(["text"], "document")
            assert result == [[0.1, 0.2]]

    def test_embed_single_convenience(self):
        """Test embed_single convenience function"""
        with patch("popkit_shared.utils.voyage_client.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.embed_single.return_value = [0.1, 0.2]
            mock_get.return_value = mock_client

            result = embed_single("text")

            mock_client.embed_single.assert_called_once_with("text", "document")
            assert result == [0.1, 0.2]

    def test_embed_query_convenience(self):
        """Test embed_query convenience function"""
        with patch("popkit_shared.utils.voyage_client.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.embed_query.return_value = [0.1, 0.2]
            mock_get.return_value = mock_client

            result = embed_query("query")

            mock_client.embed_query.assert_called_once_with("query")
            assert result == [0.1, 0.2]

    def test_embed_document_convenience(self):
        """Test embed_document convenience function"""
        with patch("popkit_shared.utils.voyage_client.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.embed_document.return_value = [0.1, 0.2]
            mock_get.return_value = mock_client

            result = embed_document("document")

            mock_client.embed_document.assert_called_once_with("document")
            assert result == [0.1, 0.2]

    def test_is_available_convenience(self):
        """Test is_available convenience function"""
        with patch("popkit_shared.utils.voyage_client.get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.is_available = True
            mock_get.return_value = mock_client

            result = is_available()

            assert result is True


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_embed_with_none_in_results(self):
        """Test embed handles None in results correctly"""
        client = VoyageClient(api_key="test")

        # This tests the internal logic - all results start as None
        # and are filled in by cache or API
        mock_response = EmbeddingResponse(
            embeddings=[[0.1]],
            model="test",
            usage={}
        )

        with patch.object(client, "_call_api_with_retry", return_value=mock_response):
            result = client.embed(["text"])

            # Should have replaced None with embedding
            assert result[0] is not None

    def test_usage_tracking_updates(self):
        """Test usage is tracked across requests"""
        client = VoyageClient(api_key="test")

        mock_response = EmbeddingResponse(
            embeddings=[[0.1]],
            model="test",
            usage={"total_tokens": 50}
        )

        with patch.object(client, "_call_api_with_retry", return_value=mock_response):
            client.embed(["text1"])

            usage = client.usage
            assert usage["total_tokens"] == 50
            assert usage["total_requests"] == 1

            client.embed(["text2"])

            usage = client.usage
            assert usage["total_tokens"] == 100
            assert usage["total_requests"] == 2

    def test_cache_key_length(self):
        """Test cache key is truncated to reasonable length"""
        client = VoyageClient(api_key="test")

        # Very long text
        long_text = "a" * 10000

        key = client._cache_key(long_text, "document")

        # Should be truncated to 24 chars (sha256 hexdigest[:24])
        assert len(key) == 24

    def test_embed_preserves_order(self):
        """Test embed preserves text order"""
        client = VoyageClient(api_key="test")

        texts = [f"text{i}" for i in range(5)]

        mock_response = EmbeddingResponse(
            embeddings=[[float(i)] for i in range(5)],
            model="test",
            usage={}
        )

        with patch.object(client, "_call_api_with_retry", return_value=mock_response):
            result = client.embed(texts)

        # Results should be in same order as input
        for i, embedding in enumerate(result):
            assert embedding == [float(i)]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
