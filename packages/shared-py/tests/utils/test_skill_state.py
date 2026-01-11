#!/usr/bin/env python3
"""
Test suite for skill_state.py

Tests skill state tracking for AskUserQuestion enforcement and activity ledger.
Critical for The PopKit Way - ensures skills end with user interaction.
"""

import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.skill_state import (
    SkillState,
    SkillStateTracker,
    get_tracker
)


class TestSkillState:
    """Test SkillState dataclass"""

    def test_skill_state_creation(self):
        """Test creating SkillState instance"""
        state = SkillState(skill_name="test-skill", workflow_id="wf-123")
        assert state.skill_name == "test-skill"
        assert state.workflow_id == "wf-123"
        assert len(state.decisions_made) == 0
        assert state.tool_calls == 0
        assert state.error_occurred is False
        assert state.last_error is None
        assert state.activity_id is None

    def test_skill_state_with_defaults(self):
        """Test SkillState with default values"""
        state = SkillState(skill_name="test-skill")
        assert state.workflow_id is None
        assert isinstance(state.decisions_made, set)
        assert state.tool_calls == 0

    def test_decisions_made_set(self):
        """Test decisions_made is a set"""
        state = SkillState(skill_name="test-skill")
        state.decisions_made.add("decision1")
        state.decisions_made.add("decision2")
        state.decisions_made.add("decision1")  # Duplicate
        assert len(state.decisions_made) == 2


class TestSkillStateTrackerSingleton:
    """Test singleton pattern"""

    def test_get_instance_returns_singleton(self):
        """Test get_instance returns same instance"""
        tracker1 = SkillStateTracker.get_instance()
        tracker2 = SkillStateTracker.get_instance()
        assert tracker1 is tracker2

    def test_get_tracker_convenience_function(self):
        """Test get_tracker() convenience function"""
        tracker = get_tracker()
        assert isinstance(tracker, SkillStateTracker)
        assert tracker is SkillStateTracker.get_instance()


class TestConfigurationLoading:
    """Test configuration loading"""

    def test_load_config_success(self):
        """Test successful config loading"""
        mock_config = {
            "skill_decisions": {
                "skills": {
                    "test-skill": {
                        "completion_decisions": []
                    }
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                config = tracker.config

                assert "skills" in config
                assert "test-skill" in config["skills"]

    def test_load_config_file_not_found(self):
        """Test config loading when file doesn't exist"""
        with patch("pathlib.Path.exists", return_value=False):
            tracker = SkillStateTracker()
            config = tracker.config
            assert config == {}

    def test_load_config_invalid_json(self):
        """Test config loading with invalid JSON"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value="invalid json"):
                tracker = SkillStateTracker()
                config = tracker.config
                assert config == {}

    def test_load_config_missing_skill_decisions_key(self):
        """Test config loading when skill_decisions key is missing"""
        mock_config = {"other_key": "value"}

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                config = tracker.config
                assert config == {}

    def test_config_lazy_loading(self):
        """Test config is loaded lazily"""
        tracker = SkillStateTracker()
        assert tracker._config is None

        # Access config property
        _ = tracker.config
        assert tracker._config is not None

    def test_get_skill_config_exact_match(self):
        """Test getting skill config with exact name match"""
        mock_config = {
            "skill_decisions": {
                "skills": {
                    "test-skill": {"id": "123"}
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                config = tracker.get_skill_config("test-skill")
                assert config == {"id": "123"}

    def test_get_skill_config_with_pop_prefix(self):
        """Test getting skill config with pop- prefix"""
        mock_config = {
            "skill_decisions": {
                "skills": {
                    "pop-test-skill": {"id": "456"}
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                # Query without prefix, should find with prefix
                config = tracker.get_skill_config("test-skill")
                assert config == {"id": "456"}

    def test_get_skill_config_without_pop_prefix(self):
        """Test getting skill config when querying with pop- prefix"""
        mock_config = {
            "skill_decisions": {
                "skills": {
                    "test-skill": {"id": "789"}
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                # Query with prefix, should find without prefix
                config = tracker.get_skill_config("pop-test-skill")
                assert config == {"id": "789"}

    def test_get_skill_config_namespace_normalization(self):
        """Test skill config with popkit: namespace"""
        mock_config = {
            "skill_decisions": {
                "skills": {
                    "test-skill": {"id": "abc"}
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                config = tracker.get_skill_config("popkit:test-skill")
                assert config == {"id": "abc"}

    def test_get_skill_config_not_found(self):
        """Test getting config for non-existent skill"""
        mock_config = {
            "skill_decisions": {
                "skills": {}
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                config = tracker.get_skill_config("nonexistent-skill")
                assert config == {}


class TestSkillLifecycle:
    """Test skill lifecycle tracking"""

    def test_start_skill(self):
        """Test starting a skill"""
        tracker = SkillStateTracker()
        with patch.object(tracker, '_publish_activity', return_value="activity-123"):
            tracker.start_skill("test-skill", workflow_id="wf-456")

        assert tracker.is_skill_active()
        assert tracker.get_active_skill() == "test-skill"
        assert tracker.state.workflow_id == "wf-456"
        assert tracker.state.activity_id == "activity-123"

    def test_end_skill(self):
        """Test ending a skill"""
        tracker = SkillStateTracker()
        with patch.object(tracker, '_publish_activity', return_value="activity-123"):
            tracker.start_skill("test-skill")
            assert tracker.is_skill_active()

            tracker.end_skill(status="complete")
            assert not tracker.is_skill_active()
            assert tracker.get_active_skill() is None

    def test_end_skill_with_error(self):
        """Test ending a skill that had an error"""
        tracker = SkillStateTracker()
        with patch.object(tracker, '_publish_activity', return_value="activity-123"):
            tracker.start_skill("test-skill")
            tracker.record_error("Test error")

            with patch.object(tracker, '_publish_activity') as mock_publish:
                tracker.end_skill(status="complete")

                # Should publish error status, not complete
                call_args = mock_publish.call_args
                assert call_args[0][0] == "error"
                assert call_args[0][1]["error"] == "Test error"

    def test_is_skill_active(self):
        """Test is_skill_active()"""
        tracker = SkillStateTracker()
        assert not tracker.is_skill_active()

        with patch.object(tracker, '_publish_activity'):
            tracker.start_skill("test-skill")
        assert tracker.is_skill_active()

        with patch.object(tracker, '_publish_activity'):
            tracker.end_skill()
        assert not tracker.is_skill_active()

    def test_get_active_skill_when_none(self):
        """Test get_active_skill when no skill is active"""
        tracker = SkillStateTracker()
        assert tracker.get_active_skill() is None


class TestDecisionTracking:
    """Test decision tracking"""

    def test_record_decision(self):
        """Test recording a decision"""
        tracker = SkillStateTracker()
        with patch.object(tracker, '_publish_activity'):
            tracker.start_skill("test-skill")
            tracker.record_decision("decision-123")

        assert "decision-123" in tracker.state.decisions_made

    def test_record_decision_no_active_skill(self):
        """Test recording decision when no skill is active"""
        tracker = SkillStateTracker()
        # Should not raise error
        tracker.record_decision("decision-123")

    def test_record_decision_by_header_exact_match(self):
        """Test recording decision by matching header"""
        mock_config = {
            "skill_decisions": {
                "skills": {
                    "test-skill": {
                        "completion_decisions": [
                            {"id": "dec-1", "header": "Next Action", "question": "What to do next?"}
                        ]
                    }
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                with patch.object(tracker, '_publish_activity'):
                    tracker.start_skill("test-skill")
                    tracker.record_decision_by_header("Next Action")

                assert "dec-1" in tracker.state.decisions_made

    def test_record_decision_by_header_case_insensitive(self):
        """Test header matching is case-insensitive"""
        mock_config = {
            "skill_decisions": {
                "skills": {
                    "test-skill": {
                        "completion_decisions": [
                            {"id": "dec-1", "header": "Next Action", "question": "What to do?"}
                        ]
                    }
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                with patch.object(tracker, '_publish_activity'):
                    tracker.start_skill("test-skill")
                    tracker.record_decision_by_header("next action")

                assert "dec-1" in tracker.state.decisions_made

    def test_record_decision_by_header_normalizes_separators(self):
        """Test header matching normalizes spaces and hyphens"""
        mock_config = {
            "skill_decisions": {
                "skills": {
                    "test-skill": {
                        "completion_decisions": [
                            {"id": "dec-1", "header": "Next-Action", "question": "What to do?"}
                        ]
                    }
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                with patch.object(tracker, '_publish_activity'):
                    tracker.start_skill("test-skill")
                    tracker.record_decision_by_header("Next Action")

                assert "dec-1" in tracker.state.decisions_made

    def test_record_decision_by_header_question_substring_match(self):
        """Test matching by question substring"""
        mock_config = {
            "skill_decisions": {
                "skills": {
                    "test-skill": {
                        "completion_decisions": [
                            {"id": "dec-1", "header": "Action", "question": "What would you like to do next?"}
                        ]
                    }
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                with patch.object(tracker, '_publish_activity'):
                    tracker.start_skill("test-skill")
                    tracker.record_decision_by_header("like to do")

                assert "dec-1" in tracker.state.decisions_made


class TestToolCallTracking:
    """Test tool call tracking"""

    def test_record_tool_use(self):
        """Test recording tool use"""
        tracker = SkillStateTracker()
        with patch.object(tracker, '_publish_activity'):
            tracker.start_skill("test-skill")
            tracker.record_tool_use("Read")

        assert tracker.state.tool_calls == 1

    def test_record_tool_use_increments(self):
        """Test tool calls increment correctly"""
        tracker = SkillStateTracker()
        with patch.object(tracker, '_publish_activity'):
            tracker.start_skill("test-skill")
            tracker.record_tool_use("Read")
            tracker.record_tool_use("Write")
            tracker.record_tool_use("Bash")

        assert tracker.state.tool_calls == 3

    def test_record_tool_use_publishes_progress(self):
        """Test tool use publishes progress at intervals"""
        tracker = SkillStateTracker()
        with patch.object(tracker, '_publish_activity') as mock_publish:
            tracker.start_skill("test-skill")

            # First 4 calls shouldn't publish progress
            for i in range(4):
                tracker.record_tool_use("Read")

            # 5th call should publish progress (every 5th call)
            tracker.record_tool_use("Read")

        # Should have start + progress events
        progress_calls = [call for call in mock_publish.call_args_list if call[0][0] == "progress"]
        assert len(progress_calls) == 1

    def test_record_tool_use_with_explicit_publish(self):
        """Test tool use with explicit publish_progress flag"""
        tracker = SkillStateTracker()
        with patch.object(tracker, '_publish_activity') as mock_publish:
            tracker.start_skill("test-skill")
            tracker.record_tool_use("Read", publish_progress=True)

        progress_calls = [call for call in mock_publish.call_args_list if call[0][0] == "progress"]
        assert len(progress_calls) == 1


class TestErrorHandling:
    """Test error handling"""

    def test_record_error(self):
        """Test recording an error"""
        tracker = SkillStateTracker()
        with patch.object(tracker, '_publish_activity'):
            tracker.start_skill("test-skill")
            tracker.record_error("Test error occurred")

        assert tracker.has_error()
        assert tracker.state.error_occurred is True
        assert tracker.state.last_error == "Test error occurred"

    def test_has_error_when_no_skill(self):
        """Test has_error when no skill is active"""
        tracker = SkillStateTracker()
        assert tracker.has_error() is False

    def test_has_error_when_no_error(self):
        """Test has_error when no error occurred"""
        tracker = SkillStateTracker()
        with patch.object(tracker, '_publish_activity'):
            tracker.start_skill("test-skill")
        assert tracker.has_error() is False

    def test_get_error_recovery_decisions(self):
        """Test getting error recovery decisions"""
        mock_config = {
            "skill_decisions": {
                "skills": {
                    "test-skill": {
                        "completion_decisions": [
                            {"id": "dec-1", "on_error": True, "header": "Retry"},
                            {"id": "dec-2", "on_error": False, "header": "Continue"}
                        ]
                    }
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                with patch.object(tracker, '_publish_activity'):
                    tracker.start_skill("test-skill")
                    tracker.record_error("Something failed")

                recovery_decisions = tracker.get_error_recovery_decisions()
                assert len(recovery_decisions) == 1
                assert recovery_decisions[0]["id"] == "dec-1"

    def test_get_error_recovery_decisions_no_error(self):
        """Test getting error recovery decisions when no error occurred"""
        tracker = SkillStateTracker()
        with patch.object(tracker, '_publish_activity'):
            tracker.start_skill("test-skill")

        recovery_decisions = tracker.get_error_recovery_decisions()
        assert len(recovery_decisions) == 0


class TestPendingDecisions:
    """Test pending decision tracking"""

    def test_get_pending_completion_decisions(self):
        """Test getting pending completion decisions"""
        mock_config = {
            "skill_decisions": {
                "skills": {
                    "test-skill": {
                        "completion_decisions": [
                            {"id": "dec-1", "header": "Action 1"},
                            {"id": "dec-2", "header": "Action 2"}
                        ]
                    }
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                with patch.object(tracker, '_publish_activity'):
                    tracker.start_skill("test-skill")

                pending = tracker.get_pending_completion_decisions()
                assert len(pending) == 2

                tracker.record_decision("dec-1")
                pending = tracker.get_pending_completion_decisions()
                assert len(pending) == 1
                assert pending[0]["id"] == "dec-2"

    def test_get_pending_completion_decisions_excludes_on_error_by_default(self):
        """Test pending decisions excludes on_error decisions when no error"""
        mock_config = {
            "skill_decisions": {
                "skills": {
                    "test-skill": {
                        "completion_decisions": [
                            {"id": "dec-1", "on_error": False, "header": "Normal"},
                            {"id": "dec-2", "on_error": True, "header": "Error"}
                        ]
                    }
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                with patch.object(tracker, '_publish_activity'):
                    tracker.start_skill("test-skill")

                pending = tracker.get_pending_completion_decisions()
                assert len(pending) == 1
                assert pending[0]["id"] == "dec-1"

    def test_get_pending_completion_decisions_includes_on_error_when_error(self):
        """Test pending decisions includes on_error decisions when error occurred"""
        mock_config = {
            "skill_decisions": {
                "skills": {
                    "test-skill": {
                        "completion_decisions": [
                            {"id": "dec-1", "on_error": False, "header": "Normal"},
                            {"id": "dec-2", "on_error": True, "header": "Error"}
                        ]
                    }
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                with patch.object(tracker, '_publish_activity'):
                    tracker.start_skill("test-skill")
                    tracker.record_error("Test error")

                pending = tracker.get_pending_completion_decisions()
                assert len(pending) == 2

    def test_get_required_decisions(self):
        """Test getting required decisions"""
        mock_config = {
            "skill_decisions": {
                "skills": {
                    "test-skill": {
                        "completion_decisions": [
                            {"id": "dec-1", "required": True, "header": "Required"},
                            {"id": "dec-2", "required": False, "header": "Optional"}
                        ]
                    }
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                with patch.object(tracker, '_publish_activity'):
                    tracker.start_skill("test-skill")

                required = tracker.get_required_decisions()
                assert len(required) == 1
                assert required[0]["id"] == "dec-1"

    def test_has_pending_decisions(self):
        """Test has_pending_decisions()"""
        mock_config = {
            "skill_decisions": {
                "skills": {
                    "test-skill": {
                        "completion_decisions": [
                            {"id": "dec-1", "header": "Action"}
                        ]
                    }
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                with patch.object(tracker, '_publish_activity'):
                    tracker.start_skill("test-skill")

                assert tracker.has_pending_decisions() is True

                tracker.record_decision("dec-1")
                assert tracker.has_pending_decisions() is False

    def test_has_required_pending(self):
        """Test has_required_pending()"""
        mock_config = {
            "skill_decisions": {
                "skills": {
                    "test-skill": {
                        "completion_decisions": [
                            {"id": "dec-1", "required": True, "header": "Required"}
                        ]
                    }
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=json.dumps(mock_config)):
                tracker = SkillStateTracker()
                with patch.object(tracker, '_publish_activity'):
                    tracker.start_skill("test-skill")

                assert tracker.has_required_pending() is True

                tracker.record_decision("dec-1")
                assert tracker.has_required_pending() is False


class TestActivityPublishing:
    """Test activity publishing"""

    def test_publish_activity_success(self):
        """Test successful activity publishing"""
        # Patch the import inside _publish_activity
        with patch("builtins.__import__") as mock_import:
            mock_context_storage = MagicMock()
            mock_get_storage = MagicMock()
            mock_storage = MagicMock()
            mock_storage.publish_activity.return_value = "activity-123"
            mock_get_storage.return_value = mock_storage
            mock_context_storage.get_context_storage = mock_get_storage

            # Make __import__ return our mock module
            def import_side_effect(name, *args, **kwargs):
                if name == "context_storage":
                    return mock_context_storage
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            tracker = SkillStateTracker()
            result = tracker._publish_activity("start", {"skill": "test-skill"})

            assert result == "activity-123"
            mock_storage.publish_activity.assert_called_once()

    def test_publish_activity_import_error(self):
        """Test activity publishing when context_storage not available"""
        # Patch the import to raise ImportError
        with patch("builtins.__import__", side_effect=ImportError("No module named 'context_storage'")):
            tracker = SkillStateTracker()
            result = tracker._publish_activity("start", {"skill": "test-skill"})
            # Should not crash, returns None
            assert result is None

    def test_publish_activity_exception(self):
        """Test activity publishing handles exceptions gracefully"""
        with patch("builtins.__import__") as mock_import:
            mock_context_storage = MagicMock()
            mock_get_storage = MagicMock()
            mock_storage = MagicMock()
            mock_storage.publish_activity.side_effect = Exception("Storage error")
            mock_get_storage.return_value = mock_storage
            mock_context_storage.get_context_storage = mock_get_storage

            # Make __import__ return our mock module
            def import_side_effect(name, *args, **kwargs):
                if name == "context_storage":
                    return mock_context_storage
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            tracker = SkillStateTracker()
            result = tracker._publish_activity("start", {"skill": "test-skill"})
            # Should handle exception gracefully
            assert result is None


class TestPhaseTracking:
    """Test phase change tracking"""

    def test_record_phase_change(self):
        """Test recording a phase change"""
        tracker = SkillStateTracker()
        with patch.object(tracker, '_publish_activity'):
            with patch.object(tracker, '_emit_telemetry_event') as mock_emit:
                tracker.start_skill("test-skill")
                tracker.record_phase_change("exploration", {"detail": "searching codebase"})

                # Should emit telemetry event
                mock_emit.assert_called()
                call_args = mock_emit.call_args
                assert call_args[0][0] == "phase_change"
                assert call_args[0][1]["phase"] == "exploration"

    def test_record_phase_change_no_active_skill(self):
        """Test recording phase change when no skill active"""
        tracker = SkillStateTracker()
        # Should not raise error
        tracker.record_phase_change("exploration")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
