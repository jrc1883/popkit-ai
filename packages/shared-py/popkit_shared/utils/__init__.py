#!/usr/bin/env python3
"""
Popkit Hooks Utilities Package

Provides shared utilities for popkit hooks including:
- version: Plugin version checking and update notifications
- github_issues: GitHub issue creation from errors and lessons
"""

from .cloud_config import (
    DEFAULT_API_URL,
    get_cloud_api_key,
    get_cloud_api_url,
    get_cloud_config_paths,
    has_cloud_api_key,
    load_cloud_config,
    resolve_cloud_config,
)
from .cross_model_review import (
    ALTERNATE_PROVIDERS,
    COMMENT_MARKER,
    CrossModelReviewError,
    CrossModelReviewResult,
    PublishMode,
    ReviewFinding,
    ReviewLookup,
    ReviewRequest,
    ReviewScope,
    ReviewVerdict,
    build_review_command,
    build_review_prompt,
    current_head_sha,
    default_base_ref,
    detect_current_provider,
    load_review_status,
    mark_pr_ready,
    normalize_verdict,
    publish_review_comment,
    record_review_skip,
    render_review_markdown,
    resolve_repo_root,
    resolve_review_request,
    resolve_target_provider,
    run_cross_model_review,
    save_review_artifact,
    validate_provider_auth,
    validate_provider_available,
)
from .github_issues import (
    create_issue_from_lesson,
    create_issue_from_validation_failure,
    save_error_locally,
    save_lesson_locally,
)
from .interaction_surface import (
    DecisionSpec,
    InteractionSurface,
    QuestionOption,
    RuntimeCapabilities,
    SelectionMode,
    resolve_runtime_capabilities,
)
from .onboarding import (
    INTRO_HEADER,
    TELEMETRY_HEADER,
    OnboardingManager,
    OnboardingState,
    TelemetryMode,
    is_onboarding_header,
    telemetry_allows_project_identity,
    telemetry_allows_remote,
)

# Plugin data directory resolution (CC 2.1.78+ CLAUDE_PLUGIN_DATA support)
from .plugin_data import (
    get_global_plugin_data_dir,
    get_plugin_data_dir,
    get_plugin_data_subdir,
)

# Version utilities will be imported when available
try:
    from .version import (
        SemanticVersion,
        check_for_updates,
        format_update_notification,
        get_current_version,
    )
except ImportError:
    # version.py not yet created
    pass

__all__ = [
    # Plugin Data Directory
    "get_plugin_data_dir",
    "get_plugin_data_subdir",
    "get_global_plugin_data_dir",
    # Onboarding
    "OnboardingManager",
    "OnboardingState",
    "TelemetryMode",
    "INTRO_HEADER",
    "TELEMETRY_HEADER",
    "is_onboarding_header",
    "telemetry_allows_remote",
    "telemetry_allows_project_identity",
    # Cross-Model Review
    "ALTERNATE_PROVIDERS",
    "COMMENT_MARKER",
    "CrossModelReviewError",
    "CrossModelReviewResult",
    "PublishMode",
    "ReviewFinding",
    "ReviewLookup",
    "ReviewRequest",
    "ReviewScope",
    "ReviewVerdict",
    "build_review_command",
    "build_review_prompt",
    "current_head_sha",
    "default_base_ref",
    "detect_current_provider",
    "load_review_status",
    "mark_pr_ready",
    "normalize_verdict",
    "publish_review_comment",
    "record_review_skip",
    "render_review_markdown",
    "resolve_repo_root",
    "resolve_review_request",
    "resolve_target_provider",
    "run_cross_model_review",
    "save_review_artifact",
    "validate_provider_auth",
    "validate_provider_available",
    # Cloud Config
    "DEFAULT_API_URL",
    "get_cloud_api_key",
    "get_cloud_api_url",
    "get_cloud_config_paths",
    "has_cloud_api_key",
    "load_cloud_config",
    "resolve_cloud_config",
    # Interaction surfaces
    "DecisionSpec",
    "InteractionSurface",
    "QuestionOption",
    "RuntimeCapabilities",
    "SelectionMode",
    "resolve_runtime_capabilities",
    # GitHub Issues
    "create_issue_from_lesson",
    "create_issue_from_validation_failure",
    "save_lesson_locally",
    "save_error_locally",
    # Version (when available)
    "check_for_updates",
    "format_update_notification",
    "get_current_version",
    "SemanticVersion",
]
