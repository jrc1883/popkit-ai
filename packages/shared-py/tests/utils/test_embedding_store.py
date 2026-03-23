#!/usr/bin/env python3
"""
Test suite for embedding_store.py

Tests SQLite-based vector storage with cosine similarity search,
project-scoped operations, batch ops, and content hash dedup.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.embedding_store import (
    DEFAULT_EMBEDDING_MODEL,
    EmbeddingRecord,
    EmbeddingStore,
    SearchResult,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def store(tmp_path):
    """Create a fresh EmbeddingStore with a temp database."""
    db_path = tmp_path / "test_embeddings.db"
    return EmbeddingStore(db_path)


@pytest.fixture
def sample_record():
    """Create a sample embedding record."""
    return EmbeddingRecord(
        id="test-1",
        content="A skill for debugging Python code",
        embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
        source_type="skill",
        source_id="debug-python",
        metadata={"tier": "tier-1"},
    )


@pytest.fixture
def sample_records():
    """Create multiple sample records with different embeddings."""
    return [
        EmbeddingRecord(
            id="agent-1",
            content="Code review agent for TypeScript",
            embedding=[0.9, 0.1, 0.0, 0.0, 0.0],
            source_type="agent",
            source_id="code-reviewer",
            metadata={"tier": "tier-1"},
        ),
        EmbeddingRecord(
            id="agent-2",
            content="Security auditing agent",
            embedding=[0.0, 0.9, 0.1, 0.0, 0.0],
            source_type="agent",
            source_id="security-auditor",
            metadata={"tier": "tier-1"},
        ),
        EmbeddingRecord(
            id="skill-1",
            content="Performance optimization skill",
            embedding=[0.0, 0.0, 0.9, 0.1, 0.0],
            source_type="skill",
            source_id="perf-optimizer",
            metadata={"tier": "tier-2"},
        ),
        EmbeddingRecord(
            id="cmd-1",
            content="Deploy command for staging",
            embedding=[0.0, 0.0, 0.0, 0.9, 0.1],
            source_type="command",
            source_id="deploy",
            metadata={},
        ),
    ]


# =============================================================================
# EmbeddingRecord Tests
# =============================================================================


class TestEmbeddingRecord:
    """Test EmbeddingRecord dataclass."""

    def test_creation(self, sample_record):
        assert sample_record.id == "test-1"
        assert sample_record.source_type == "skill"
        assert len(sample_record.embedding) == 5

    def test_dimension_property(self, sample_record):
        assert sample_record.dimension == 5

    def test_to_dict(self, sample_record):
        d = sample_record.to_dict()
        assert d["id"] == "test-1"
        assert d["content"] == "A skill for debugging Python code"
        assert d["source_type"] == "skill"

    def test_from_dict(self):
        d = {
            "id": "x",
            "content": "test",
            "embedding": [0.1],
            "source_type": "agent",
            "source_id": "a",
            "metadata": {},
            "created_at": "2026-01-01",
            "embedding_model": "voyage-3.5",
        }
        record = EmbeddingRecord.from_dict(d)
        assert record.id == "x"
        assert record.embedding == [0.1]

    def test_default_model(self, sample_record):
        assert sample_record.embedding_model == DEFAULT_EMBEDDING_MODEL

    def test_default_project_path_none(self, sample_record):
        assert sample_record.project_path is None


class TestSearchResult:
    """Test SearchResult dataclass."""

    def test_to_dict(self, sample_record):
        sr = SearchResult(record=sample_record, similarity=0.85, rank=1)
        d = sr.to_dict()
        assert d["similarity"] == 0.85
        assert d["rank"] == 1
        assert d["record"]["id"] == "test-1"


# =============================================================================
# CRUD Tests
# =============================================================================


class TestEmbeddingStoreCRUD:
    """Test CRUD operations."""

    def test_store_and_get(self, store, sample_record):
        store.store(sample_record)
        retrieved = store.get("test-1")
        assert retrieved is not None
        assert retrieved.id == "test-1"
        assert retrieved.content == sample_record.content
        assert retrieved.embedding == sample_record.embedding

    def test_get_nonexistent(self, store):
        assert store.get("nonexistent") is None

    def test_store_replace(self, store, sample_record):
        store.store(sample_record)
        sample_record.content = "Updated content"
        store.store(sample_record)
        retrieved = store.get("test-1")
        assert retrieved.content == "Updated content"

    def test_get_by_source(self, store, sample_record):
        store.store(sample_record)
        retrieved = store.get_by_source("skill", "debug-python")
        assert retrieved is not None
        assert retrieved.id == "test-1"

    def test_get_by_source_not_found(self, store):
        assert store.get_by_source("skill", "nonexistent") is None

    def test_delete(self, store, sample_record):
        store.store(sample_record)
        deleted = store.delete("test-1")
        assert deleted is True
        assert store.get("test-1") is None

    def test_delete_nonexistent(self, store):
        deleted = store.delete("nonexistent")
        assert deleted is False

    def test_delete_by_source_type(self, store, sample_records):
        for r in sample_records:
            store.store(r)
        deleted = store.delete_by_source("agent")
        assert deleted == 2
        assert store.count("agent") == 0
        assert store.count("skill") == 1

    def test_delete_by_source_type_and_id(self, store, sample_records):
        for r in sample_records:
            store.store(r)
        deleted = store.delete_by_source("agent", "code-reviewer")
        assert deleted == 1
        assert store.count("agent") == 1

    def test_exists(self, store, sample_record):
        assert store.exists("test-1") is False
        store.store(sample_record)
        assert store.exists("test-1") is True

    def test_clear_all(self, store, sample_records):
        for r in sample_records:
            store.store(r)
        cleared = store.clear()
        assert cleared == 4
        assert store.count() == 0

    def test_clear_by_type(self, store, sample_records):
        for r in sample_records:
            store.store(r)
        cleared = store.clear("agent")
        assert cleared == 2
        assert store.count() == 2


# =============================================================================
# Batch Operations
# =============================================================================


class TestBatchOperations:
    """Test batch store operations."""

    def test_store_batch(self, store, sample_records):
        count = store.store_batch(sample_records)
        assert count == 4
        assert store.count() == 4

    def test_store_batch_empty(self, store):
        assert store.store_batch([]) == 0

    def test_store_batch_replaces(self, store, sample_records):
        store.store_batch(sample_records)
        sample_records[0].content = "Updated"
        store.store_batch(sample_records)
        assert store.count() == 4
        retrieved = store.get("agent-1")
        assert retrieved.content == "Updated"


# =============================================================================
# Cosine Similarity Search
# =============================================================================


class TestCosineSimilaritySearch:
    """Test search with cosine similarity."""

    def test_search_exact_match(self, store, sample_records):
        store.store_batch(sample_records)
        results = store.search(
            query_embedding=[0.9, 0.1, 0.0, 0.0, 0.0],
            top_k=1,
        )
        assert len(results) == 1
        assert results[0].record.source_id == "code-reviewer"
        assert results[0].similarity > 0.99

    def test_search_with_source_type_filter(self, store, sample_records):
        store.store_batch(sample_records)
        results = store.search(
            query_embedding=[0.9, 0.1, 0.0, 0.0, 0.0],
            source_type="skill",
            top_k=5,
        )
        assert all(r.record.source_type == "skill" for r in results)

    def test_search_min_similarity(self, store, sample_records):
        store.store_batch(sample_records)
        results = store.search(
            query_embedding=[0.9, 0.1, 0.0, 0.0, 0.0],
            min_similarity=0.9,
        )
        # Only the exact match should pass 0.9 threshold
        assert len(results) == 1

    def test_search_top_k(self, store, sample_records):
        store.store_batch(sample_records)
        results = store.search(
            query_embedding=[0.5, 0.5, 0.5, 0.5, 0.0],
            top_k=2,
        )
        assert len(results) == 2

    def test_search_ranked(self, store, sample_records):
        store.store_batch(sample_records)
        results = store.search(
            query_embedding=[0.5, 0.5, 0.0, 0.0, 0.0],
            top_k=4,
        )
        assert results[0].rank == 1
        assert results[1].rank == 2
        # Descending similarity
        assert results[0].similarity >= results[1].similarity

    def test_search_exclude_ids(self, store, sample_records):
        store.store_batch(sample_records)
        results = store.search(
            query_embedding=[0.9, 0.1, 0.0, 0.0, 0.0],
            exclude_ids=["agent-1"],
        )
        assert all(r.record.id != "agent-1" for r in results)

    def test_search_empty_store(self, store):
        results = store.search(query_embedding=[0.1, 0.2])
        assert results == []

    def test_cosine_similarity_identical_vectors(self, store):
        sim = store._cosine_similarity([1, 0, 0], [1, 0, 0])
        assert abs(sim - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal_vectors(self, store):
        sim = store._cosine_similarity([1, 0, 0], [0, 1, 0])
        assert abs(sim) < 1e-6

    def test_cosine_similarity_different_lengths(self, store):
        sim = store._cosine_similarity([1, 0], [1, 0, 0])
        assert sim == 0.0

    def test_cosine_similarity_zero_vector(self, store):
        sim = store._cosine_similarity([0, 0, 0], [1, 0, 0])
        assert sim == 0.0


# =============================================================================
# Project-Scoped Search
# =============================================================================


class TestProjectScopedSearch:
    """Test project-scoped operations."""

    def test_store_with_project_path(self, store):
        record = EmbeddingRecord(
            id="proj-1",
            content="Project-local skill",
            embedding=[0.5, 0.5, 0.0],
            source_type="project-skill",
            source_id="custom-lint",
            project_path="/home/user/myproject",
        )
        store.store(record)
        retrieved = store.get("proj-1")
        assert retrieved.project_path == "/home/user/myproject"

    def test_search_project(self, store):
        global_rec = EmbeddingRecord(
            id="g1",
            content="Global agent",
            embedding=[0.8, 0.2, 0.0],
            source_type="agent",
            source_id="global-agent",
        )
        project_rec = EmbeddingRecord(
            id="p1",
            content="Project agent",
            embedding=[0.7, 0.3, 0.0],
            source_type="project-agent",
            source_id="project-agent",
            project_path="/myproject",
        )
        store.store(global_rec)
        store.store(project_rec)

        results = store.search_project(
            query_embedding=[0.8, 0.2, 0.0],
            project_path="/myproject",
            include_global=True,
        )
        assert len(results) == 2

    def test_search_project_exclude_global(self, store):
        global_rec = EmbeddingRecord(
            id="g1",
            content="Global",
            embedding=[0.8, 0.2, 0.0],
            source_type="agent",
            source_id="ga",
        )
        project_rec = EmbeddingRecord(
            id="p1",
            content="Project",
            embedding=[0.7, 0.3, 0.0],
            source_type="project-agent",
            source_id="pa",
            project_path="/myproject",
        )
        store.store(global_rec)
        store.store(project_rec)

        results = store.search_project(
            query_embedding=[0.8, 0.2, 0.0],
            project_path="/myproject",
            include_global=False,
        )
        assert len(results) == 1
        assert results[0].record.project_path == "/myproject"

    def test_count_project(self, store):
        for i in range(3):
            store.store(
                EmbeddingRecord(
                    id=f"p{i}",
                    content=f"item {i}",
                    embedding=[float(i)],
                    source_type="project-skill",
                    source_id=f"s{i}",
                    project_path="/proj",
                )
            )
        assert store.count_project("/proj") == 3
        assert store.count_project("/other") == 0

    def test_clear_project(self, store):
        for i in range(3):
            store.store(
                EmbeddingRecord(
                    id=f"p{i}",
                    content=f"item {i}",
                    embedding=[float(i)],
                    source_type="project-skill",
                    source_id=f"s{i}",
                    project_path="/proj",
                )
            )
        store.store(
            EmbeddingRecord(
                id="g1",
                content="global",
                embedding=[0.1],
                source_type="agent",
                source_id="ga",
            )
        )
        cleared = store.clear_project("/proj")
        assert cleared == 3
        assert store.count() == 1

    def test_list_projects(self, store):
        store.store(
            EmbeddingRecord(
                id="p1",
                content="x",
                embedding=[0.1],
                source_type="project-skill",
                source_id="s1",
                project_path="/proj1",
            )
        )
        store.store(
            EmbeddingRecord(
                id="p2",
                content="y",
                embedding=[0.2],
                source_type="project-agent",
                source_id="a1",
                project_path="/proj2",
            )
        )
        projects = store.list_projects()
        assert len(projects) == 2
        paths = {p["project_path"] for p in projects}
        assert "/proj1" in paths
        assert "/proj2" in paths


# =============================================================================
# Content Hash Dedup
# =============================================================================


class TestContentHashDedup:
    """Test content hash deduplication."""

    def test_content_exists(self, store, sample_record):
        store.store(sample_record)
        result = store.content_exists(sample_record.content)
        assert result == "test-1"

    def test_content_not_exists(self, store):
        assert store.content_exists("no such content") is None

    def test_needs_update_new_content(self, store):
        assert store.needs_update("nonexistent", "new content") is True

    def test_needs_update_same_content(self, store, sample_record):
        store.store(sample_record)
        assert store.needs_update("test-1", sample_record.content) is False

    def test_needs_update_changed_content(self, store, sample_record):
        store.store(sample_record)
        assert store.needs_update("test-1", "completely different content") is True


# =============================================================================
# Statistics
# =============================================================================


class TestStatistics:
    """Test statistics and listing."""

    def test_count(self, store, sample_records):
        assert store.count() == 0
        store.store_batch(sample_records)
        assert store.count() == 4

    def test_count_by_type(self, store, sample_records):
        store.store_batch(sample_records)
        assert store.count("agent") == 2
        assert store.count("skill") == 1
        assert store.count("command") == 1

    def test_stats(self, store, sample_records):
        store.store_batch(sample_records)
        stats = store.stats()
        assert stats["total"] == 4
        assert stats["by_type"]["agent"] == 2
        assert stats["by_type"]["skill"] == 1
        assert "db_path" in stats

    def test_list_sources(self, store, sample_records):
        store.store_batch(sample_records)
        sources = store.list_sources()
        assert len(sources) == 4

    def test_list_sources_filtered(self, store, sample_records):
        store.store_batch(sample_records)
        sources = store.list_sources("agent")
        assert len(sources) == 2
        assert all(s["source_type"] == "agent" for s in sources)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
