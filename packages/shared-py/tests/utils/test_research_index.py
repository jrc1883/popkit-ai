#!/usr/bin/env python3
"""
Test suite for research_index.py

Tests research entry CRUD, keyword/tag search, semantic search
with mocked Voyage client, and verifies the embed_text→embed_query/embed_document fix.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.research_index import (
    IndexEntry,
    ResearchEntry,
    ResearchIndex,
    ResearchIndexManager,
    extract_keywords,
    get_research_manager,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def manager(tmp_path):
    """Create a ResearchIndexManager with a temp directory."""
    return ResearchIndexManager(str(tmp_path))


@pytest.fixture
def sample_entry():
    """Create a sample research entry."""
    return ResearchEntry(
        id="",
        type="decision",
        title="Use Redis for caching",
        content="We decided to use Redis for application-level caching.",
        context="Evaluating caching strategies for API responses",
        rationale="Redis provides TTL support and fast key-value lookups",
        alternatives=["Memcached", "In-memory LRU"],
        tags=["redis", "caching", "infrastructure"],
        project="popkit",
    )


@pytest.fixture
def populated_manager(manager, sample_entry):
    """Manager with several entries."""
    entries = [
        ResearchEntry(
            id="",
            type="decision",
            title="Use Redis for caching",
            content="Redis for caching layer",
            tags=["redis", "caching"],
            project="popkit",
        ),
        ResearchEntry(
            id="",
            type="finding",
            title="React 19 performance improvements",
            content="React 19 improves hydration speed by 30%",
            tags=["react", "performance"],
            project="frontend",
        ),
        ResearchEntry(
            id="",
            type="learning",
            title="SQLite WAL mode for concurrency",
            content="WAL mode allows concurrent reads and writes",
            tags=["sqlite", "database"],
            project="popkit",
        ),
    ]
    for e in entries:
        manager.create(e)
    return manager


# =============================================================================
# ResearchEntry Tests
# =============================================================================


class TestResearchEntry:
    """Test ResearchEntry dataclass."""

    def test_creation(self, sample_entry):
        assert sample_entry.type == "decision"
        assert "Redis" in sample_entry.title
        assert len(sample_entry.tags) == 3

    def test_to_dict(self, sample_entry):
        d = sample_entry.to_dict()
        assert d["type"] == "decision"
        assert d["alternatives"] == ["Memcached", "In-memory LRU"]

    def test_from_dict(self):
        d = {
            "id": "r001",
            "type": "finding",
            "title": "Test",
            "content": "Content",
            "tags": ["a"],
            "project": "p",
        }
        entry = ResearchEntry.from_dict(d)
        assert entry.id == "r001"
        assert entry.type == "finding"

    def test_from_dict_camelcase(self):
        d = {
            "id": "r001",
            "type": "decision",
            "title": "T",
            "content": "C",
            "createdAt": "2026-01-01",
            "updatedAt": "2026-01-02",
            "embeddingId": "emb-1",
            "relatedEntries": ["r002"],
        }
        entry = ResearchEntry.from_dict(d)
        assert entry.created_at == "2026-01-01"
        assert entry.embedding_id == "emb-1"
        assert entry.related_entries == ["r002"]

    def test_searchable_text(self, sample_entry):
        text = sample_entry.searchable_text
        assert "Redis" in text
        assert "TTL" in text
        assert "Memcached" in text


class TestIndexEntry:
    """Test IndexEntry dataclass."""

    def test_from_dict_camelcase(self):
        d = {
            "id": "r001",
            "type": "decision",
            "title": "T",
            "tags": [],
            "project": "p",
            "createdAt": "2026-01-01",
            "embeddingId": "e1",
        }
        entry = IndexEntry.from_dict(d)
        assert entry.created_at == "2026-01-01"
        assert entry.embedding_id == "e1"


class TestResearchIndex:
    """Test ResearchIndex dataclass."""

    def test_to_dict(self):
        idx = ResearchIndex()
        d = idx.to_dict()
        assert "version" in d
        assert "lastUpdated" in d
        assert "entries" in d

    def test_from_dict(self):
        d = {
            "version": "1.0.0",
            "lastUpdated": "2026-01-01",
            "entries": [],
            "tagIndex": {},
            "projectIndex": {},
        }
        idx = ResearchIndex.from_dict(d)
        assert idx.version == "1.0.0"


# =============================================================================
# CRUD Tests
# =============================================================================


class TestCRUD:
    """Test create, read, update, delete."""

    def test_create(self, manager, sample_entry):
        entry_id = manager.create(sample_entry)
        assert entry_id == "r001"
        assert len(manager.list()) == 1

    def test_create_generates_sequential_ids(self, manager):
        for i in range(3):
            e = ResearchEntry(id="", type="finding", title=f"Entry {i}", content=f"C{i}")
            manager.create(e)
        entries = manager.list()
        ids = {e.id for e in entries}
        assert ids == {"r001", "r002", "r003"}

    def test_get(self, manager, sample_entry):
        eid = manager.create(sample_entry)
        retrieved = manager.get(eid)
        assert retrieved is not None
        assert retrieved.title == sample_entry.title

    def test_get_nonexistent(self, manager):
        assert manager.get("r999") is None

    def test_update(self, manager, sample_entry):
        eid = manager.create(sample_entry)
        entry = manager.get(eid)
        entry.title = "Updated Title"
        assert manager.update(entry) is True
        assert manager.get(eid).title == "Updated Title"

    def test_update_nonexistent(self, manager):
        entry = ResearchEntry(id="r999", type="finding", title="X", content="X")
        assert manager.update(entry) is False

    def test_delete(self, manager, sample_entry):
        eid = manager.create(sample_entry)
        assert manager.delete(eid) is True
        assert manager.get(eid) is None
        assert len(manager.list()) == 0

    def test_delete_nonexistent(self, manager):
        assert manager.delete("r999") is False

    def test_delete_cleans_indexes(self, manager, sample_entry):
        eid = manager.create(sample_entry)
        assert "redis" in manager.list_tags()
        manager.delete(eid)
        assert "redis" not in manager.list_tags()


# =============================================================================
# Listing and Filtering
# =============================================================================


class TestListingFiltering:
    """Test list with filters."""

    def test_list_all(self, populated_manager):
        entries = populated_manager.list()
        assert len(entries) == 3

    def test_list_by_type(self, populated_manager):
        entries = populated_manager.list(entry_type="decision")
        assert len(entries) == 1
        assert entries[0].type == "decision"

    def test_list_by_project(self, populated_manager):
        entries = populated_manager.list(project="popkit")
        assert len(entries) == 2

    def test_list_by_tag(self, populated_manager):
        entries = populated_manager.list(tag="redis")
        assert len(entries) == 1

    def test_list_limit(self, populated_manager):
        entries = populated_manager.list(limit=2)
        assert len(entries) == 2

    def test_list_tags(self, populated_manager):
        tags = populated_manager.list_tags()
        assert "redis" in tags
        assert "performance" in tags

    def test_list_projects(self, populated_manager):
        projects = populated_manager.list_projects()
        assert "popkit" in projects
        assert "frontend" in projects


# =============================================================================
# Keyword Search
# =============================================================================


class TestKeywordSearch:
    """Test keyword-based search."""

    def test_basic_keyword_search(self, populated_manager):
        results = populated_manager.search_keywords("Redis caching")
        assert len(results) > 0
        assert results[0].entry.title == "Use Redis for caching"

    def test_keyword_search_tag_boost(self, populated_manager):
        results = populated_manager.search_keywords("redis")
        assert results[0].entry.tags[0] == "redis" or "redis" in results[0].entry.tags

    def test_keyword_search_no_match(self, populated_manager):
        results = populated_manager.search_keywords("nonexistent unicorn rainbow")
        assert len(results) == 0

    def test_keyword_search_with_type_filter(self, populated_manager):
        results = populated_manager.search_keywords("redis", entry_type="finding")
        assert len(results) == 0

    def test_keyword_search_with_project_filter(self, populated_manager):
        results = populated_manager.search_keywords("redis", project="frontend")
        assert len(results) == 0

    def test_keyword_search_ranking(self, populated_manager):
        results = populated_manager.search_keywords("caching", limit=5)
        for i, r in enumerate(results):
            assert r.rank == i + 1


# =============================================================================
# Tag Search
# =============================================================================


class TestTagSearch:
    """Test tag-based search."""

    def test_single_tag(self, populated_manager):
        results = populated_manager.search_tags(["redis"])
        assert len(results) == 1

    def test_multiple_tags(self, populated_manager):
        results = populated_manager.search_tags(["redis", "caching"])
        assert len(results) == 1
        assert results[0].similarity == 1.0  # Both tags match

    def test_partial_tag_match(self, populated_manager):
        results = populated_manager.search_tags(["redis", "performance"])
        assert len(results) == 2  # Each has one matching tag

    def test_tag_search_with_filters(self, populated_manager):
        results = populated_manager.search_tags(["redis"], entry_type="finding")
        assert len(results) == 0

    def test_tag_search_no_match(self, populated_manager):
        results = populated_manager.search_tags(["nonexistent"])
        assert len(results) == 0


# =============================================================================
# Semantic Search — Verifies Bug Fix
# =============================================================================


class TestSemanticSearch:
    """Test semantic search with mocked Voyage, verifying embed_text bug fix."""

    def test_semantic_search_uses_embed_query(self, populated_manager):
        """Verify that search_semantic calls embed_query (not embed_text)."""
        mock_client = MagicMock()
        mock_client.embed_query.return_value = [0.1, 0.2, 0.3]

        mock_store = MagicMock()
        mock_store.search.return_value = []

        # Patch at source modules since research_index uses lazy imports
        with (
            patch(
                "popkit_shared.utils.voyage_client.VoyageClient",
                return_value=mock_client,
            ),
            patch(
                "popkit_shared.utils.embedding_store.EmbeddingStore",
                return_value=mock_store,
            ),
            patch.dict("os.environ", {"VOYAGE_API_KEY": "test-key"}),
        ):
            populated_manager.search_semantic("test query")
            mock_client.embed_query.assert_called_once_with("test query")
            # embed_text should NOT exist / NOT be called
            assert not hasattr(mock_client, "embed_text") or not mock_client.embed_text.called

    def test_semantic_search_fallback_no_key(self, populated_manager):
        """Without API key, falls back to keyword search."""
        with patch.dict("os.environ", {}, clear=True):
            results = populated_manager.search_semantic("Redis caching")
            assert len(results) > 0
            assert results[0].match_type == "keyword"

    def test_semantic_search_fallback_on_import_error(self, populated_manager):
        """If imports fail, falls back to keyword search."""
        with patch.dict(
            "sys.modules",
            {"popkit_shared.utils.embedding_store": None},
        ):
            results = populated_manager.search_semantic("Redis")
            assert all(r.match_type == "keyword" for r in results)


# =============================================================================
# Embedding — Verifies Bug Fix
# =============================================================================


class TestEmbedEntry:
    """Test embed_entry uses embed_document (not embed_text)."""

    def test_embed_entry_uses_embed_document(self, manager, sample_entry):
        """Verify that embed_entry calls embed_document (not embed_text)."""
        eid = manager.create(sample_entry)

        mock_client = MagicMock()
        mock_client.embed_document.return_value = [0.1, 0.2, 0.3]

        mock_store = MagicMock()

        # Patch at source modules since embed_entry uses lazy imports
        with (
            patch(
                "popkit_shared.utils.voyage_client.VoyageClient",
                return_value=mock_client,
            ),
            patch(
                "popkit_shared.utils.embedding_store.EmbeddingStore",
                return_value=mock_store,
            ),
            patch(
                "popkit_shared.utils.embedding_store.EmbeddingRecord",
            ),
            patch.dict("os.environ", {"VOYAGE_API_KEY": "test-key"}),
        ):
            result = manager.embed_entry(eid, force=True)
            mock_client.embed_document.assert_called_once()
            assert not hasattr(mock_client, "embed_text") or not mock_client.embed_text.called

    def test_embed_entry_no_api_key(self, manager, sample_entry):
        """Without API key, embed_entry returns None."""
        eid = manager.create(sample_entry)
        with patch.dict("os.environ", {}, clear=True):
            assert manager.embed_entry(eid) is None

    def test_embed_entry_skip_if_exists(self, manager, sample_entry):
        """If entry already has embedding_id and force=False, skip."""
        eid = manager.create(sample_entry)
        entry = manager.get(eid)
        entry.embedding_id = "existing-id"
        manager.update(entry)
        assert manager.embed_entry(eid, force=False) == "existing-id"


# =============================================================================
# Tag Management
# =============================================================================


class TestTagManagement:
    """Test tag add/remove/set operations."""

    def test_add_tags(self, manager, sample_entry):
        eid = manager.create(sample_entry)
        manager.add_tags(eid, ["new-tag"])
        entry = manager.get(eid)
        assert "new-tag" in entry.tags

    def test_remove_tags(self, manager, sample_entry):
        eid = manager.create(sample_entry)
        manager.remove_tags(eid, ["redis"])
        entry = manager.get(eid)
        assert "redis" not in entry.tags

    def test_set_tags(self, manager, sample_entry):
        eid = manager.create(sample_entry)
        manager.set_tags(eid, ["only-this"])
        entry = manager.get(eid)
        assert entry.tags == ["only-this"]


# =============================================================================
# Statistics
# =============================================================================


class TestStats:
    """Test statistics."""

    def test_stats(self, populated_manager):
        stats = populated_manager.stats()
        assert stats["total"] == 3
        assert stats["by_type"]["decision"] == 1
        assert stats["by_type"]["finding"] == 1
        assert stats["by_type"]["learning"] == 1
        assert stats["tags"] > 0
        assert stats["projects"] > 0


# =============================================================================
# Helper Functions
# =============================================================================


class TestHelpers:
    """Test helper functions."""

    def test_extract_keywords(self):
        text = "We use Redis for caching and PostgreSQL for persistence"
        keywords = extract_keywords(text)
        assert "redis" in keywords
        assert "postgres" in keywords
        assert "caching" in keywords

    def test_extract_keywords_limit(self):
        text = "redis postgres mysql mongodb docker kubernetes aws python node react vue angular"
        keywords = extract_keywords(text)
        assert len(keywords) <= 5

    def test_get_research_manager(self, tmp_path):
        mgr = get_research_manager(str(tmp_path))
        assert mgr is not None
        assert mgr.project_root == tmp_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
