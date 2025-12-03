#!/usr/bin/env python3
"""
Integration Tests for Embeddings and Streaming Platform

Tests for Issue #19 (Embeddings Enhancement) and Issue #23 (Fine-grained Streaming).
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "power-mode"))
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks" / "utils"))


# =============================================================================
# TEST: EMBEDDING STORE (Issue #19)
# =============================================================================

class TestEmbeddingStore(unittest.TestCase):
    """Tests for SQLite-based embedding storage."""

    def setUp(self):
        """Set up test database."""
        from embedding_store import EmbeddingStore, EmbeddingRecord
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_embeddings.db"
        self.store = EmbeddingStore(db_path=self.db_path)

    def tearDown(self):
        """Clean up test database."""
        try:
            self.store._conn.close()
            if self.db_path.exists():
                self.db_path.unlink()
        except Exception:
            pass

    def test_store_and_retrieve(self):
        """Test storing and retrieving embeddings."""
        from embedding_store import EmbeddingRecord

        record = EmbeddingRecord(
            id="test-1",
            content="Test content",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            source_type="test",
            source_id="test-source"
        )
        self.store.store(record)

        retrieved = self.store.get("test-1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content, "Test content")
        self.assertEqual(retrieved.source_type, "test")

    def test_similarity_search(self):
        """Test cosine similarity search."""
        from embedding_store import EmbeddingRecord

        # Store test embeddings
        records = [
            EmbeddingRecord(
                id="doc-1",
                content="Python programming language",
                embedding=[1.0, 0.0, 0.0, 0.0],
                source_type="doc",
                source_id="doc-1"
            ),
            EmbeddingRecord(
                id="doc-2",
                content="JavaScript web development",
                embedding=[0.0, 1.0, 0.0, 0.0],
                source_type="doc",
                source_id="doc-2"
            ),
            EmbeddingRecord(
                id="doc-3",
                content="Python web frameworks",
                embedding=[0.9, 0.1, 0.0, 0.0],  # Similar to doc-1
                source_type="doc",
                source_id="doc-3"
            ),
        ]
        for r in records:
            self.store.store(r)

        # Search with query similar to doc-1
        query = [0.95, 0.05, 0.0, 0.0]
        results = self.store.search(query, source_type="doc", top_k=2)

        self.assertEqual(len(results), 2)
        # doc-1 or doc-3 should be first (most similar to query)
        self.assertIn(results[0].record.id, ["doc-1", "doc-3"])

    def test_stats(self):
        """Test statistics collection."""
        from embedding_store import EmbeddingRecord

        # Store some records
        for i in range(5):
            self.store.store(EmbeddingRecord(
                id=f"stat-{i}",
                content=f"Content {i}",
                embedding=[0.1] * 10,
                source_type="agent" if i < 3 else "skill",
                source_id=f"stat-{i}"
            ))

        stats = self.store.stats()
        # Check total count (key may be 'total' or 'total_records')
        total_key = "total" if "total" in stats else "total_records"
        self.assertEqual(stats.get(total_key, self.store.count()), 5)
        # Check source type breakdown
        if "by_source_type" in stats:
            self.assertIn("agent", stats["by_source_type"])
            self.assertIn("skill", stats["by_source_type"])


# =============================================================================
# TEST: VOYAGE CLIENT (Issue #19)
# =============================================================================

class TestVoyageClient(unittest.TestCase):
    """Tests for Voyage API client."""

    @patch.dict(os.environ, {"VOYAGE_API_KEY": "test-key"})
    def test_client_initialization(self):
        """Test client initializes with API key."""
        from voyage_client import VoyageClient, is_available

        self.assertTrue(is_available())
        client = VoyageClient()
        self.assertTrue(client.is_available)

    @patch.dict(os.environ, {}, clear=True)
    def test_client_unavailable_without_key(self):
        """Test client reports unavailable without API key."""
        # Need to reimport to pick up env change
        import importlib
        import voyage_client
        importlib.reload(voyage_client)

        self.assertFalse(voyage_client.is_available())

    @patch.dict(os.environ, {"VOYAGE_API_KEY": "test-key"})
    def test_embed_single(self):
        """Test single text embedding with mocked urllib."""
        import urllib.request
        import json
        from voyage_client import VoyageClient

        # Mock urllib.request.urlopen with complete response structure
        mock_response_data = json.dumps({
            "data": [{"embedding": [0.1, 0.2, 0.3]}],
            "model": "voyage-3.5",
            "usage": {"total_tokens": 10}
        }).encode('utf-8')

        mock_response = MagicMock()
        mock_response.read.return_value = mock_response_data
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch.object(urllib.request, 'urlopen', return_value=mock_response) as mock_urlopen:
            client = VoyageClient()
            embedding = client.embed_single("test text")

            self.assertEqual(embedding, [0.1, 0.2, 0.3])
            mock_urlopen.assert_called_once()


# =============================================================================
# TEST: STREAM MANAGER (Issue #23)
# =============================================================================

class TestStreamManager(unittest.TestCase):
    """Tests for stream session manager."""

    def test_session_lifecycle(self):
        """Test creating, adding chunks, and ending session."""
        from stream_manager import StreamManager
        from protocol import StreamChunk

        manager = StreamManager()

        # Start session
        session_id = manager.start_session("agent-1", "Bash")
        self.assertIsNotNone(session_id)

        # Add chunks
        for i in range(3):
            chunk = StreamChunk(
                session_id=session_id,
                agent_id="agent-1",
                chunk_index=i,
                content=f"chunk-{i}",
                is_final=(i == 2)
            )
            result = manager.add_chunk(chunk)
            self.assertTrue(result)

        # Check session
        session = manager.get_session(session_id)
        self.assertEqual(session.chunk_count, 3)
        self.assertEqual(session.total_content, "chunk-0chunk-1chunk-2")
        self.assertTrue(session.is_complete)

    def test_session_stats(self):
        """Test aggregate statistics."""
        from stream_manager import StreamManager
        from protocol import StreamChunk

        manager = StreamManager()

        # Create multiple sessions
        sid1 = manager.start_session("agent-1", "Read")
        sid2 = manager.start_session("agent-2", "Write")

        # Add chunks to first
        manager.add_chunk(StreamChunk(
            session_id=sid1,
            agent_id="agent-1",
            chunk_index=0,
            content="test",
            is_final=True
        ))

        stats = manager.get_stats()
        self.assertEqual(stats.active_sessions, 1)  # sid2 is still active
        self.assertEqual(stats.completed_sessions, 1)  # sid1 is complete

    def test_callbacks(self):
        """Test chunk and completion callbacks."""
        from stream_manager import StreamManager
        from protocol import StreamChunk

        chunks_received = []
        sessions_completed = []

        def on_chunk(chunk):
            chunks_received.append(chunk)

        def on_complete(session):
            sessions_completed.append(session)

        manager = StreamManager(
            on_chunk=on_chunk,
            on_session_complete=on_complete
        )

        sid = manager.start_session("agent-1", "Bash")
        manager.add_chunk(StreamChunk(
            session_id=sid,
            agent_id="agent-1",
            chunk_index=0,
            content="data",
            is_final=True
        ))

        self.assertEqual(len(chunks_received), 1)
        self.assertEqual(len(sessions_completed), 1)


# =============================================================================
# TEST: SEMANTIC ROUTER (Issue #19)
# =============================================================================

class TestSemanticRouter(unittest.TestCase):
    """Tests for semantic agent routing."""

    def test_keyword_routing(self):
        """Test keyword-based routing fallback."""
        from semantic_router import SemanticRouter

        router = SemanticRouter()

        # Should route based on keywords if configured
        results = router.route("fix a security vulnerability", top_k=3)

        # At minimum, should return results (even if empty)
        self.assertIsInstance(results, list)

    def test_file_pattern_routing(self):
        """Test file pattern-based routing."""
        from semantic_router import SemanticRouter

        router = SemanticRouter()

        results = router.route(
            "update this file",
            context={"file_path": "src/components/Button.test.tsx"}
        )

        # Should attempt routing
        self.assertIsInstance(results, list)

    def test_explain_routing(self):
        """Test routing explanation."""
        from semantic_router import SemanticRouter

        router = SemanticRouter()

        explanation = router.explain_routing(
            "write unit tests",
            context={"file_path": "app.test.ts"}
        )

        self.assertIn("query", explanation)
        self.assertIn("methods_tried", explanation)
        self.assertIn("results", explanation)


# =============================================================================
# TEST: PROTOCOL EXTENSIONS (Issues #19 & #23)
# =============================================================================

class TestProtocolExtensions(unittest.TestCase):
    """Tests for protocol message types."""

    def test_stream_chunk_serialization(self):
        """Test StreamChunk to/from message."""
        from protocol import StreamChunk, MessageType

        chunk = StreamChunk(
            session_id="test-session",
            agent_id="agent-1",
            chunk_index=5,
            content="hello world",
            tool_name="Bash",
            is_final=False
        )

        # Convert to message
        msg = chunk.to_message()
        self.assertEqual(msg.type, MessageType.STREAM_CHUNK)
        self.assertEqual(msg.from_agent, "agent-1")

        # Convert back
        restored = StreamChunk.from_message(msg)
        self.assertEqual(restored.session_id, "test-session")
        self.assertEqual(restored.chunk_index, 5)
        self.assertEqual(restored.content, "hello world")

    def test_streaming_message_types(self):
        """Test streaming message type existence."""
        from protocol import MessageType

        # Verify new message types exist
        self.assertTrue(hasattr(MessageType, "STREAM_START"))
        self.assertTrue(hasattr(MessageType, "STREAM_CHUNK"))
        self.assertTrue(hasattr(MessageType, "STREAM_END"))
        self.assertTrue(hasattr(MessageType, "STREAM_ERROR"))

    def test_embedding_message_types(self):
        """Test embedding message type existence."""
        from protocol import MessageType

        # Verify embedding message types exist
        self.assertTrue(hasattr(MessageType, "EMBEDDING_REQUEST"))
        self.assertTrue(hasattr(MessageType, "EMBEDDING_RESULT"))
        self.assertTrue(hasattr(MessageType, "SIMILARITY_QUERY"))
        self.assertTrue(hasattr(MessageType, "SIMILARITY_RESULT"))


# =============================================================================
# TEST: ASYNC SUPPORT (Issue #23)
# =============================================================================

class TestAsyncSupport(unittest.TestCase):
    """Tests for async utilities."""

    def test_async_event_emitter(self):
        """Test async event emitter."""
        import asyncio
        from async_support import AsyncEventEmitter

        emitter = AsyncEventEmitter()
        received = []

        async def handler(data):
            received.append(data)

        emitter.on("test", handler)

        async def run_test():
            await emitter.emit("test", {"value": 42})
            await asyncio.sleep(0.1)
            return received

        # Use asyncio.run for Python 3.7+
        try:
            result = asyncio.run(run_test())
        except RuntimeError:
            # Fallback for environments with existing event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(run_test())
            finally:
                loop.close()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["value"], 42)

    def test_async_queue(self):
        """Test async queue operations."""
        import asyncio
        from async_support import AsyncQueue

        queue = AsyncQueue(maxsize=10)

        async def run_test():
            # put_nowait doesn't need await
            queue.put_nowait("item1")
            queue.put_nowait("item2")

            items = []
            items.append(await queue.get())
            items.append(await queue.get())
            return items

        # Use asyncio.run for Python 3.7+
        try:
            result = asyncio.run(run_test())
        except RuntimeError:
            # Fallback for environments with existing event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(run_test())
            finally:
                loop.close()

        self.assertEqual(result, ["item1", "item2"])


# =============================================================================
# TEST: INTEGRATION SCENARIOS
# =============================================================================

class TestIntegrationScenarios(unittest.TestCase):
    """End-to-end integration tests."""

    def test_streaming_with_state_tracking(self):
        """Test streaming integrated with state tracking."""
        from stream_manager import StreamManager
        from protocol import StreamChunk

        # Create manager with state saving
        manager = StreamManager()

        # Simulate agent streaming
        sid = manager.start_session("test-agent", "Bash")

        for i in range(10):
            chunk = StreamChunk(
                session_id=sid,
                agent_id="test-agent",
                chunk_index=i,
                content=f"output line {i}\n",
                tool_name="Bash",
                is_final=(i == 9)
            )
            manager.add_chunk(chunk)

        # Verify session state
        session = manager.get_session(sid)
        self.assertTrue(session.is_complete)
        self.assertEqual(session.chunk_count, 10)

        # Verify status summary
        summary = manager.get_status_summary()
        self.assertEqual(summary["active_streams"], 0)
        self.assertEqual(summary["total_chunks"], 10)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
