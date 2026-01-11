#!/usr/bin/env python3
"""
Test suite for tool_filter.py

Tests workflow-based tool filtering with security focus on preventing bypass attacks.
Critical for security boundary enforcement and tool access control.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.tool_filter import (
    load_agent_config,
    filter_tools_for_workflow,
    ToolFilter
)


class TestLoadAgentConfig:
    """Test agent configuration loading"""

    def test_load_agent_config_success(self):
        """Test successful config loading"""
        mock_config = {
            "tool_choice": {
                "workflow_steps": {
                    "git-commit": {
                        "required_tools": ["Bash", "Read"]
                    }
                }
            }
        }

        with patch("builtins.open", mock_open(read_data='{"tool_choice": {"workflow_steps": {"git-commit": {"required_tools": ["Bash", "Read"]}}}}')) as mock_file:
            with patch("json.load", return_value=mock_config):
                result = load_agent_config()
                assert isinstance(result, dict)
                assert "tool_choice" in result

    def test_load_agent_config_file_not_found(self):
        """Test handling of missing config file"""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            with pytest.raises(FileNotFoundError):
                load_agent_config()

    def test_load_agent_config_invalid_json(self):
        """Test handling of invalid JSON"""
        with patch("builtins.open", mock_open(read_data='invalid json')):
            with pytest.raises(Exception):  # json.JSONDecodeError in Python 3.5+
                load_agent_config()

    def test_load_agent_config_path_construction(self):
        """Test config path is constructed correctly"""
        # The path should be: tool_filter.py's parent/parent/parent/agents/config.json
        # Which resolves to: packages/shared-py/agents/config.json
        with patch("builtins.open", mock_open(read_data='{}')) as mock_file:
            with patch("json.load", return_value={}):
                load_agent_config()
                # Verify the path ends with agents/config.json
                call_args = str(mock_file.call_args)
                assert "config.json" in call_args


class TestFilterToolsForWorkflow:
    """Test workflow-based tool filtering"""

    def test_filter_with_known_workflow(self):
        """Test filtering with a known workflow"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "git-commit": {
                        "required_tools": ["Bash"]
                    }
                }
            }
        }
        available = ["Bash", "Read", "Write"]
        result = filter_tools_for_workflow("git-commit", available, config)
        assert result == ["Bash"]

    def test_filter_with_unknown_workflow_returns_all(self):
        """Test unknown workflow returns all tools (safe fallback)"""
        config = {
            "tool_choice": {
                "workflow_steps": {}
            }
        }
        available = ["Bash", "Read", "Write"]
        result = filter_tools_for_workflow("unknown-workflow", available, config)
        assert result == available

    def test_filter_with_wildcard_returns_all(self):
        """Test wildcard '*' in required tools returns all"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "full-access": {
                        "required_tools": ["*"]
                    }
                }
            }
        }
        available = ["Bash", "Read", "Write", "Task"]
        result = filter_tools_for_workflow("full-access", available, config)
        assert result == available

    def test_filter_with_multiple_required_tools(self):
        """Test filtering with multiple required tools"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "file-edit": {
                        "required_tools": ["Read", "Write", "Edit"]
                    }
                }
            }
        }
        available = ["Bash", "Read", "Write", "Edit", "Task"]
        result = filter_tools_for_workflow("file-edit", available, config)
        assert set(result) == {"Read", "Write", "Edit"}

    def test_filter_with_no_required_tools(self):
        """Test filtering when no tools are required"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "read-only": {
                        "required_tools": []
                    }
                }
            }
        }
        available = ["Bash", "Read", "Write"]
        result = filter_tools_for_workflow("read-only", available, config)
        assert result == []

    def test_filter_preserves_tool_order(self):
        """Test that filtering preserves original tool order"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "ordered": {
                        "required_tools": ["Tool1", "Tool2", "Tool3"]
                    }
                }
            }
        }
        available = ["Tool3", "Tool2", "Tool1"]
        result = filter_tools_for_workflow("ordered", available, config)
        # Result should maintain the order from available_tools
        assert result == ["Tool3", "Tool2", "Tool1"]

    def test_filter_with_missing_tool_choice_key(self):
        """Test handling of missing tool_choice in config"""
        config = {}
        available = ["Bash", "Read"]
        result = filter_tools_for_workflow("any", available, config)
        # Should return all tools as safe fallback
        assert result == available

    def test_filter_with_missing_workflow_steps_key(self):
        """Test handling of missing workflow_steps in config"""
        config = {
            "tool_choice": {}
        }
        available = ["Bash", "Read"]
        result = filter_tools_for_workflow("any", available, config)
        # Should return all tools as safe fallback
        assert result == available

    def test_filter_loads_config_when_none_provided(self):
        """Test that config is loaded when not provided"""
        mock_config = {
            "tool_choice": {
                "workflow_steps": {
                    "test": {
                        "required_tools": ["Bash"]
                    }
                }
            }
        }
        with patch("popkit_shared.utils.tool_filter.load_agent_config", return_value=mock_config):
            available = ["Bash", "Read"]
            result = filter_tools_for_workflow("test", available, config=None)
            assert result == ["Bash"]


class TestToolFilterClass:
    """Test ToolFilter class"""

    def test_init_with_config(self):
        """Test initialization with provided config"""
        config = {"tool_choice": {"workflow_steps": {}}}
        filter_obj = ToolFilter(config=config)
        assert filter_obj.config == config
        assert filter_obj.enabled is True

    def test_init_without_config_loads_default(self):
        """Test initialization without config loads from file"""
        mock_config = {"tool_choice": {"workflow_steps": {}}}
        with patch("popkit_shared.utils.tool_filter.load_agent_config", return_value=mock_config):
            filter_obj = ToolFilter()
            assert filter_obj.config == mock_config

    def test_init_with_enabled_false(self):
        """Test initialization with filtering disabled"""
        config = {"tool_choice": {"workflow_steps": {}}}
        filter_obj = ToolFilter(config=config, enabled=False)
        assert filter_obj.enabled is False

    def test_filter_when_enabled(self):
        """Test filtering when enabled"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "test": {
                        "required_tools": ["Bash"]
                    }
                }
            }
        }
        filter_obj = ToolFilter(config=config)
        available = ["Bash", "Read", "Write"]
        result = filter_obj.filter("test", available)
        assert result == ["Bash"]

    def test_filter_when_disabled_returns_all(self):
        """Test filtering when disabled returns all tools"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "test": {
                        "required_tools": ["Bash"]
                    }
                }
            }
        }
        filter_obj = ToolFilter(config=config, enabled=False)
        available = ["Bash", "Read", "Write"]
        result = filter_obj.filter("test", available)
        assert result == available

    def test_disable_method(self):
        """Test disable() method"""
        config = {"tool_choice": {"workflow_steps": {}}}
        filter_obj = ToolFilter(config=config)
        assert filter_obj.enabled is True
        filter_obj.disable()
        assert filter_obj.enabled is False

    def test_enable_method(self):
        """Test enable() method"""
        config = {"tool_choice": {"workflow_steps": {}}}
        filter_obj = ToolFilter(config=config, enabled=False)
        assert filter_obj.enabled is False
        filter_obj.enable()
        assert filter_obj.enabled is True

    def test_toggle_enabled_state(self):
        """Test toggling enabled state multiple times"""
        config = {"tool_choice": {"workflow_steps": {}}}
        filter_obj = ToolFilter(config=config)

        assert filter_obj.enabled is True
        filter_obj.disable()
        assert filter_obj.enabled is False
        filter_obj.enable()
        assert filter_obj.enabled is True
        filter_obj.disable()
        assert filter_obj.enabled is False


class TestSecurityScenarios:
    """Test security boundary enforcement"""

    def test_prevents_unauthorized_tool_access(self):
        """Test that restricted workflow cannot access unauthorized tools"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "restricted": {
                        "required_tools": ["Read"]
                    }
                }
            }
        }
        available = ["Read", "Write", "Bash", "Task"]
        result = filter_tools_for_workflow("restricted", available, config)

        # Should only have Read, not dangerous tools
        assert "Read" in result
        assert "Write" not in result
        assert "Bash" not in result
        assert "Task" not in result

    def test_wildcard_bypass_requires_explicit_config(self):
        """Test that wildcard access requires explicit configuration"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "explicit-wildcard": {
                        "required_tools": ["*"]
                    },
                    "no-wildcard": {
                        "required_tools": ["Read"]
                    }
                }
            }
        }
        available = ["Read", "Write", "Bash"]

        # Explicit wildcard should give full access
        result1 = filter_tools_for_workflow("explicit-wildcard", available, config)
        assert result1 == available

        # Without wildcard, should be restricted
        result2 = filter_tools_for_workflow("no-wildcard", available, config)
        assert result2 == ["Read"]

    def test_case_sensitive_tool_names(self):
        """Test that tool filtering is case-sensitive (security)"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "case-test": {
                        "required_tools": ["Bash"]
                    }
                }
            }
        }
        available = ["bash", "Bash", "BASH"]
        result = filter_tools_for_workflow("case-test", available, config)

        # Should only match exact case
        assert result == ["Bash"]
        assert "bash" not in result
        assert "BASH" not in result


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_available_tools(self):
        """Test filtering with empty available tools list"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "test": {
                        "required_tools": ["Bash"]
                    }
                }
            }
        }
        available = []
        result = filter_tools_for_workflow("test", available, config)
        assert result == []

    def test_empty_required_tools(self):
        """Test filtering with empty required tools list"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "test": {
                        "required_tools": []
                    }
                }
            }
        }
        available = ["Bash", "Read"]
        result = filter_tools_for_workflow("test", available, config)
        assert result == []

    def test_required_tool_not_available(self):
        """Test when required tool is not in available list"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "test": {
                        "required_tools": ["NonExistent"]
                    }
                }
            }
        }
        available = ["Bash", "Read"]
        result = filter_tools_for_workflow("test", available, config)
        assert result == []

    def test_mixed_available_and_required(self):
        """Test with some tools available and some not"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "test": {
                        "required_tools": ["Bash", "NonExistent", "Read"]
                    }
                }
            }
        }
        available = ["Bash", "Read", "Write"]
        result = filter_tools_for_workflow("test", available, config)
        # Should only return tools that are both required AND available
        assert set(result) == {"Bash", "Read"}

    def test_none_config_parameter(self):
        """Test explicitly passing None as config"""
        mock_config = {
            "tool_choice": {
                "workflow_steps": {
                    "test": {
                        "required_tools": ["Bash"]
                    }
                }
            }
        }
        with patch("popkit_shared.utils.tool_filter.load_agent_config", return_value=mock_config):
            available = ["Bash", "Read"]
            result = filter_tools_for_workflow("test", available, None)
            assert result == ["Bash"]


class TestRealWorldWorkflows:
    """Test real-world workflow scenarios"""

    def test_git_commit_workflow(self):
        """Test git commit workflow (Bash only)"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "git-commit": {
                        "required_tools": ["Bash"]
                    }
                }
            }
        }
        available = ["Bash", "Read", "Write", "Edit"]
        result = filter_tools_for_workflow("git-commit", available, config)
        assert result == ["Bash"]

    def test_file_edit_workflow(self):
        """Test file editing workflow (Read, Write, Edit)"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "file-edit": {
                        "required_tools": ["Read", "Write", "Edit"]
                    }
                }
            }
        }
        available = ["Bash", "Read", "Write", "Edit", "Grep"]
        result = filter_tools_for_workflow("file-edit", available, config)
        assert set(result) == {"Read", "Write", "Edit"}

    def test_read_only_workflow(self):
        """Test read-only analysis workflow"""
        config = {
            "tool_choice": {
                "workflow_steps": {
                    "code-review": {
                        "required_tools": ["Read", "Grep", "Glob"]
                    }
                }
            }
        }
        available = ["Bash", "Read", "Write", "Grep", "Glob"]
        result = filter_tools_for_workflow("code-review", available, config)
        assert set(result) == {"Read", "Grep", "Glob"}
        # Verify no write capabilities
        assert "Bash" not in result
        assert "Write" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
