#!/usr/bin/env python3
"""Unit tests for pop-next-action decision-spec output."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "pop-next-action"
    / "scripts"
    / "recommend_action.py"
)
SPEC = spec_from_file_location("pop_next_action_recommend_action", SCRIPT_PATH)
assert SPEC and SPEC.loader
recommend_action = module_from_spec(SPEC)
SPEC.loader.exec_module(recommend_action)


def _sample_state() -> dict:
    return {
        "git": {"uncommitted_count": 4, "ahead_count": 0, "urgency": "HIGH"},
        "code": {"typescript_errors": 0, "urgency": "LOW"},
        "issues": {
            "open_count": 1,
            "issues": [
                {
                    "number": 42,
                    "title": "Add auth guard",
                    "labels": [{"name": "p1-high"}],
                }
            ],
            "urgency": "MEDIUM",
        },
        "research": {
            "has_research_branches": True,
            "branches": ["research/office-hours-notes"],
            "urgency": "HIGH",
        },
    }


def test_generate_report_includes_stable_decision_spec_fields(tmp_path):
    state = _sample_state()

    ranked = recommend_action.rank_actions(recommend_action.calculate_action_scores(state))
    report = recommend_action.generate_report(
        ranked,
        state,
        runtime="both",
        repo_root=tmp_path,
    )

    spec = report["decision_spec"]

    assert spec["header"] == "Next Action"
    assert spec["question"] == "What should PopKit do next in this repository?"
    assert spec["selection_mode"] == "single"
    assert spec["source_command"] == "/popkit-dev:next"
    assert spec["follow_up"] == "Invoke pop-research-merge skill"


def test_decision_spec_marks_top_option_recommended_and_limits_to_three(tmp_path):
    state = _sample_state()
    state["branches"] = {
        "has_feature_branches": True,
        "branches": [
            {
                "name": "feat/mcp-gateway-routing",
                "commits_ahead": 6,
                "issue_number": 128,
                "last_commit": "Continue host-owned launch contract",
                "age": "2 days ago",
            }
        ],
        "stale_branches": [],
    }

    ranked = recommend_action.rank_actions(recommend_action.calculate_action_scores(state))
    report = recommend_action.generate_report(
        ranked,
        state,
        runtime="both",
        repo_root=tmp_path,
    )

    options = report["decision_spec"]["options"]

    assert len(options) == 3
    assert options[0]["id"] == "process_research"
    assert options[0]["recommended"] is True
    assert all(option["recommended"] is False for option in options[1:])
    assert [option["id"] for option in options] == [
        "process_research",
        "commit_work",
        "continue_feature_branch",
    ]


def test_decision_spec_uses_runtime_specific_follow_up_commands(tmp_path):
    state = _sample_state()

    ranked = recommend_action.rank_actions(recommend_action.calculate_action_scores(state))
    report = recommend_action.generate_report(
        ranked,
        state,
        runtime="codex",
        repo_root=tmp_path,
    )

    first_option = report["decision_spec"]["options"][0]

    assert first_option["follow_up"].endswith('detect_conflicts.py" --help')
    assert report["decision_spec"]["follow_up"] == first_option["follow_up"]
    assert "request_user_input" not in report["decision_spec"]["question"]
    assert "AskUserQuestion" not in first_option["description"]
