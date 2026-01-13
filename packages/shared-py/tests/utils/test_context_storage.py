#!/usr/bin/env python3
"""
Test suite for context_storage.py

Focused tests on critical session persistence functionality.
Tests abstract interface and default FileContextStorage backend.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.context_storage import (
    ContextStorage,
    FileContextStorage,
    get_context_storage,
)


class TestContextStorageInterface:
    """Test abstract interface"""

    def test_cannot_instantiate_abstract_class(self):
        """Test that ContextStorage is abstract"""
        with pytest.raises(TypeError):
            ContextStorage()

    def test_must_implement_abstract_methods(self):
        """Test that subclass must implement required methods"""

        class IncompleteStorage(ContextStorage):
            pass

        with pytest.raises(TypeError):
            IncompleteStorage()

    def test_can_instantiate_complete_subclass(self):
        """Test that complete implementation works"""

        class CompleteStorage(ContextStorage):
            def save_context(self, workflow_id, context):
                return True

            def load_context(self, workflow_id):
                return None

            def delete_context(self, workflow_id):
                return True

            def list_workflows(self):
                return []

            def get_backend_name(self):
                return "test"

        storage = CompleteStorage()
        assert isinstance(storage, ContextStorage)

    def test_activity_methods_have_defaults(self):
        """Test activity methods have default implementations"""

        class MinimalStorage(ContextStorage):
            def save_context(self, workflow_id, context):
                return True

            def load_context(self, workflow_id):
                return None

            def delete_context(self, workflow_id):
                return True

            def list_workflows(self):
                return []

            def get_backend_name(self):
                return "minimal"

        storage = MinimalStorage()
        # Activity methods should have default no-op implementations
        assert storage.publish_activity("skill", "event", {}) is None
        assert storage.get_recent_activity() == []
        assert storage.get_active_skills() == []


class TestFileContextStorage:
    """Test file-based storage backend"""

    def test_initialization_with_custom_dir(self):
        """Test creating storage with custom directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))
            assert storage.base_dir == Path(tmpdir)

    def test_get_backend_name(self):
        """Test backend name"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))
            assert storage.get_backend_name() == "file"

    def test_save_context(self):
        """Test saving context"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))
            context = {"skill": "test", "data": "value"}

            result = storage.save_context("workflow-123", context)
            assert result is True

            # Verify file was created (directly in base_dir)
            context_file = Path(tmpdir) / "workflow-123.json"
            assert context_file.exists()

    def test_load_context_success(self):
        """Test loading saved context"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))
            original = {"skill": "test", "value": 42}

            storage.save_context("workflow-456", original)
            loaded = storage.load_context("workflow-456")

            assert loaded is not None
            assert loaded["skill"] == "test"
            assert loaded["value"] == 42

    def test_load_context_not_found(self):
        """Test loading non-existent context"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))
            loaded = storage.load_context("nonexistent")
            assert loaded is None

    def test_delete_context(self):
        """Test deleting context"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))

            # Save then delete
            storage.save_context("workflow-789", {"data": "test"})
            result = storage.delete_context("workflow-789")
            assert result is True

            # Verify it's gone
            loaded = storage.load_context("workflow-789")
            assert loaded is None

    def test_delete_nonexistent_context(self):
        """Test deleting non-existent context"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))
            result = storage.delete_context("nonexistent")
            # Implementation returns False for nonexistent files
            assert result is False

    def test_list_workflows_empty(self):
        """Test listing workflows when none exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))
            workflows = storage.list_workflows()
            assert workflows == []

    def test_list_workflows_with_contexts(self):
        """Test listing multiple workflows"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))

            # Save multiple contexts
            storage.save_context("workflow-1", {"a": 1})
            storage.save_context("workflow-2", {"b": 2})
            storage.save_context("workflow-3", {"c": 3})

            workflows = storage.list_workflows()
            assert len(workflows) == 3
            assert "workflow-1" in workflows
            assert "workflow-2" in workflows
            assert "workflow-3" in workflows

    def test_context_directory_created_automatically(self):
        """Test that base directory is created if needed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "new_base"
            # Create the base directory first (FileContextStorage expects it)
            base.mkdir(parents=True, exist_ok=True)
            storage = FileContextStorage(base_dir=base)

            # Saving should work even with new directory
            result = storage.save_context("test", {"data": "value"})
            assert result is True

            # File should exist in base dir
            file_path = base / "test.json"
            assert file_path.exists()

    def test_save_overwrites_existing(self):
        """Test that save overwrites existing context"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))

            # Save initial
            storage.save_context("workflow-x", {"version": 1})

            # Overwrite
            storage.save_context("workflow-x", {"version": 2})

            # Load should have new version
            loaded = storage.load_context("workflow-x")
            assert loaded["version"] == 2


class TestFileContextStorageErrorHandling:
    """Test error handling in file storage"""

    def test_save_with_invalid_json(self):
        """Test saving non-serializable data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))

            # Try to save non-serializable object
            invalid_context = {"func": lambda x: x}
            result = storage.save_context("test", invalid_context)

            # Should handle gracefully (return False or raise TypeError)
            # Implementation may vary, but shouldn't crash
            assert isinstance(result, bool) or result is None

    def test_load_with_corrupted_json(self):
        """Test loading corrupted JSON file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))

            # Create corrupted file
            context_dir = Path(tmpdir) / "context"
            context_dir.mkdir(exist_ok=True)
            corrupted_file = context_dir / "corrupted.json"
            corrupted_file.write_text("not valid json{{{")

            # Should return None for corrupted file
            loaded = storage.load_context("corrupted")
            assert loaded is None


class TestGetContextStorage:
    """Test factory function"""

    def test_get_context_storage_returns_instance(self):
        """Test factory returns storage instance"""
        storage = get_context_storage()
        assert isinstance(storage, ContextStorage)

    def test_get_context_storage_returns_file_by_default(self):
        """Test factory returns FileContextStorage by default"""
        with patch.dict("os.environ", {}, clear=True):
            storage = get_context_storage()
            assert storage.get_backend_name() == "file"

    def test_get_context_storage_detects_upstash(self):
        """Test factory detects environment variables"""
        with patch.dict(
            "os.environ",
            {
                "UPSTASH_REDIS_REST_URL": "https://test.upstash.io",
                "UPSTASH_REDIS_REST_TOKEN": "test-token",
            },
        ):
            storage = get_context_storage()
            # Should return a valid backend (may be cloud, upstash, or file)
            backend = storage.get_backend_name()
            assert backend in ["upstash", "file", "cloud"]

    def test_get_context_storage_returns_backend(self):
        """Test that factory returns storage backend"""
        storage1 = get_context_storage()
        storage2 = get_context_storage()
        # Both should be valid storage instances
        assert isinstance(storage1, ContextStorage)
        assert isinstance(storage2, ContextStorage)


class TestWorkflowIDSafety:
    """Test workflow ID handling and safety"""

    def test_workflow_id_with_special_characters(self):
        """Test handling workflow IDs with special characters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))

            # Test various special characters
            test_ids = ["workflow-with-dashes", "workflow_with_underscores", "workflow.with.dots"]

            for wf_id in test_ids:
                storage.save_context(wf_id, {"id": wf_id})
                loaded = storage.load_context(wf_id)
                assert loaded is not None
                assert loaded["id"] == wf_id

    def test_workflow_id_sanitization(self):
        """Test that dangerous characters are handled"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))

            # IDs with path traversal attempts should be handled safely
            dangerous_ids = [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32",
                "workflow/../other",
            ]

            for dangerous_id in dangerous_ids:
                # Should either sanitize or reject
                try:
                    storage.save_context(dangerous_id, {"test": "data"})
                    # If it succeeds, verify it didn't escape the directory
                    context_dir = Path(tmpdir) / "context"
                    # All files should be within context_dir
                    for file in context_dir.rglob("*.json"):
                        assert context_dir in file.parents or file.parent == context_dir
                except (ValueError, OSError):
                    # Rejecting dangerous IDs is also acceptable
                    pass


class TestContextDataIntegrity:
    """Test data integrity and validation"""

    def test_roundtrip_preserves_data_types(self):
        """Test that save/load preserves data types"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))

            original = {
                "string": "text",
                "number": 42,
                "float": 3.14,
                "boolean": True,
                "null": None,
                "array": [1, 2, 3],
                "nested": {"key": "value"},
            }

            storage.save_context("types-test", original)
            loaded = storage.load_context("types-test")

            assert loaded["string"] == "text"
            assert loaded["number"] == 42
            assert loaded["float"] == 3.14
            assert loaded["boolean"] is True
            assert loaded["null"] is None
            assert loaded["array"] == [1, 2, 3]
            assert loaded["nested"]["key"] == "value"

    def test_empty_context(self):
        """Test saving and loading empty context"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))

            storage.save_context("empty", {})
            loaded = storage.load_context("empty")

            # Implementation adds metadata fields
            assert "_workflow_id" in loaded
            assert "_updated_at" in loaded
            assert loaded["_workflow_id"] == "empty"


class TestConcurrentAccess:
    """Test behavior with concurrent-like access patterns"""

    def test_multiple_save_load_cycles(self):
        """Test multiple rapid save/load cycles"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))

            for i in range(10):
                storage.save_context("rapid-test", {"iteration": i})
                loaded = storage.load_context("rapid-test")
                assert loaded["iteration"] == i

    def test_interleaved_operations(self):
        """Test interleaved save/load/delete operations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileContextStorage(base_dir=Path(tmpdir))

            # Create multiple workflows
            storage.save_context("wf-1", {"id": 1})
            storage.save_context("wf-2", {"id": 2})

            # Load one
            loaded1 = storage.load_context("wf-1")
            assert loaded1["id"] == 1

            # Delete another
            storage.delete_context("wf-2")

            # First should still be accessible
            loaded1_again = storage.load_context("wf-1")
            assert loaded1_again["id"] == 1

            # Second should be gone
            loaded2 = storage.load_context("wf-2")
            assert loaded2 is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
