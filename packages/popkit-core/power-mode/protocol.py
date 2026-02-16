#!/usr/bin/env python3
"""
Power Mode structured messaging protocol.

Issue #268 introduces typed request/response messages with explicit request_id
matching so coordinator and agents can correlate approvals reliably.

This module uses Pydantic for strict validation when available. In environments
without Pydantic, it falls back to lightweight manual validation so runtime
behavior remains compatible.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, ConfigDict, Field, ValidationError

    PYDANTIC_AVAILABLE = True
except ImportError:
    BaseModel = object  # type: ignore[assignment]
    ConfigDict = None  # type: ignore[assignment]
    Field = None  # type: ignore[assignment]
    ValidationError = ValueError
    PYDANTIC_AVAILABLE = False


class ProtocolValidationError(ValueError):
    """Raised when a protocol message fails validation."""


class MessageType(str, Enum):
    """Canonical power-mode message types."""

    PLAN_APPROVAL_REQUEST = "plan:approval_request"
    PLAN_APPROVAL_RESPONSE = "plan:approval_response"
    PERMISSION_REQUEST = "permission:request"
    PERMISSION_RESPONSE = "permission:response"
    AGENT_IDLE = "agent:idle"
    TASK_ASSIGNED = "task:assigned"
    SHUTDOWN_REQUEST = "shutdown_request"
    SHUTDOWN_APPROVED = "shutdown_approved"
    BROADCAST = "broadcast"


RESPONSE_FOR: Dict[MessageType, MessageType] = {
    MessageType.PLAN_APPROVAL_RESPONSE: MessageType.PLAN_APPROVAL_REQUEST,
    MessageType.PERMISSION_RESPONSE: MessageType.PERMISSION_REQUEST,
    MessageType.SHUTDOWN_APPROVED: MessageType.SHUTDOWN_REQUEST,
}

REQUEST_OR_RESPONSE_TYPES = set(RESPONSE_FOR) | set(RESPONSE_FOR.values())


@dataclass
class Objective:
    """Structured objective used for power-mode session initialization."""

    description: str
    success_criteria: List[str] = field(default_factory=list)
    phases: List[str] = field(default_factory=list)
    file_patterns: List[str] = field(default_factory=list)
    restricted_tools: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "success_criteria": self.success_criteria,
            "phases": self.phases,
            "file_patterns": self.file_patterns,
            "restricted_tools": self.restricted_tools,
        }


if PYDANTIC_AVAILABLE:

    class _EnvelopeBase(BaseModel):
        model_config = ConfigDict(extra="forbid")

        type: str
        from_agent: str
        to_agent: Optional[str] = None
        message_id: str
        timestamp: str
        request_id: Optional[str] = None

    class _BroadcastPayload(BaseModel):
        model_config = ConfigDict(extra="forbid")

        content: str
        metadata: Dict[str, Any] = Field(default_factory=dict)

    class _PermissionRequestPayload(BaseModel):
        model_config = ConfigDict(extra="forbid")

        content: str

    class _PermissionResponsePayload(BaseModel):
        model_config = ConfigDict(extra="forbid")

        approved: bool
        reason: str = ""

    class _PlanApprovalRequestPayload(BaseModel):
        model_config = ConfigDict(extra="forbid")

        plan_summary: str
        files: List[str] = Field(default_factory=list)

    class _PlanApprovalResponsePayload(BaseModel):
        model_config = ConfigDict(extra="forbid")

        approved: bool
        comments: str = ""

    class _AgentIdlePayload(BaseModel):
        model_config = ConfigDict(extra="forbid")

        reason: str = ""

    class _TaskAssignedPayload(BaseModel):
        model_config = ConfigDict(extra="forbid")

        task_id: str
        description: str

    class _ShutdownRequestPayload(BaseModel):
        model_config = ConfigDict(extra="forbid")

        reason: str

    class _ShutdownApprovedPayload(BaseModel):
        model_config = ConfigDict(extra="forbid")

        note: str = ""

    class _BroadcastEnvelope(_EnvelopeBase):
        type: str = MessageType.BROADCAST.value
        payload: _BroadcastPayload

    class _PermissionRequestEnvelope(_EnvelopeBase):
        type: str = MessageType.PERMISSION_REQUEST.value
        request_id: str
        payload: _PermissionRequestPayload

    class _PermissionResponseEnvelope(_EnvelopeBase):
        type: str = MessageType.PERMISSION_RESPONSE.value
        request_id: str
        payload: _PermissionResponsePayload

    class _PlanApprovalRequestEnvelope(_EnvelopeBase):
        type: str = MessageType.PLAN_APPROVAL_REQUEST.value
        request_id: str
        payload: _PlanApprovalRequestPayload

    class _PlanApprovalResponseEnvelope(_EnvelopeBase):
        type: str = MessageType.PLAN_APPROVAL_RESPONSE.value
        request_id: str
        payload: _PlanApprovalResponsePayload

    class _AgentIdleEnvelope(_EnvelopeBase):
        type: str = MessageType.AGENT_IDLE.value
        payload: _AgentIdlePayload

    class _TaskAssignedEnvelope(_EnvelopeBase):
        type: str = MessageType.TASK_ASSIGNED.value
        payload: _TaskAssignedPayload

    class _ShutdownRequestEnvelope(_EnvelopeBase):
        type: str = MessageType.SHUTDOWN_REQUEST.value
        request_id: str
        payload: _ShutdownRequestPayload

    class _ShutdownApprovedEnvelope(_EnvelopeBase):
        type: str = MessageType.SHUTDOWN_APPROVED.value
        request_id: str
        payload: _ShutdownApprovedPayload

    PYDANTIC_MODELS = {
        MessageType.BROADCAST: _BroadcastEnvelope,
        MessageType.PERMISSION_REQUEST: _PermissionRequestEnvelope,
        MessageType.PERMISSION_RESPONSE: _PermissionResponseEnvelope,
        MessageType.PLAN_APPROVAL_REQUEST: _PlanApprovalRequestEnvelope,
        MessageType.PLAN_APPROVAL_RESPONSE: _PlanApprovalResponseEnvelope,
        MessageType.AGENT_IDLE: _AgentIdleEnvelope,
        MessageType.TASK_ASSIGNED: _TaskAssignedEnvelope,
        MessageType.SHUTDOWN_REQUEST: _ShutdownRequestEnvelope,
        MessageType.SHUTDOWN_APPROVED: _ShutdownApprovedEnvelope,
    }
else:
    PYDANTIC_MODELS = {}


REQUIRED_PAYLOAD_FIELDS: Dict[MessageType, Dict[str, type]] = {
    MessageType.BROADCAST: {"content": str},
    MessageType.PERMISSION_REQUEST: {"content": str},
    MessageType.PERMISSION_RESPONSE: {"approved": bool},
    MessageType.PLAN_APPROVAL_REQUEST: {"plan_summary": str},
    MessageType.PLAN_APPROVAL_RESPONSE: {"approved": bool},
    MessageType.AGENT_IDLE: {},
    MessageType.TASK_ASSIGNED: {"task_id": str, "description": str},
    MessageType.SHUTDOWN_REQUEST: {"reason": str},
    MessageType.SHUTDOWN_APPROVED: {},
}


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


def _new_request_id() -> str:
    return f"req-{uuid.uuid4()}"


def _require_fields(message: Dict[str, Any], required: List[str]) -> None:
    missing = [field for field in required if field not in message]
    if missing:
        raise ProtocolValidationError(f"Missing required fields: {', '.join(missing)}")


def _validate_timestamp(timestamp: str) -> None:
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProtocolValidationError(f"Invalid ISO timestamp: {timestamp}") from exc


def _validate_manual(message: Dict[str, Any], message_type: MessageType) -> None:
    payload = message.get("payload")
    if not isinstance(payload, dict):
        raise ProtocolValidationError("Field 'payload' must be an object")

    required = REQUIRED_PAYLOAD_FIELDS[message_type]
    for key, expected_type in required.items():
        if key not in payload:
            raise ProtocolValidationError(
                f"Missing payload field '{key}' for {message_type.value}"
            )
        if not isinstance(payload[key], expected_type):
            actual = type(payload[key]).__name__
            expected = expected_type.__name__
            raise ProtocolValidationError(
                f"Payload field '{key}' must be {expected}, got {actual}"
            )


def validate_message_dict(message: Dict[str, Any]) -> MessageType:
    """Validate a protocol message envelope and return parsed MessageType."""

    if not isinstance(message, dict):
        raise ProtocolValidationError("Protocol message must be a JSON object")

    _require_fields(
        message,
        ["type", "from_agent", "message_id", "timestamp", "payload"],
    )

    try:
        message_type = MessageType(message["type"])
    except ValueError as exc:
        raise ProtocolValidationError(
            f"Unknown message type: {message.get('type')}"
        ) from exc

    if message_type in REQUEST_OR_RESPONSE_TYPES and not message.get("request_id"):
        raise ProtocolValidationError(
            f"Message type '{message_type.value}' requires request_id for correlation"
        )

    _validate_timestamp(str(message["timestamp"]))

    if PYDANTIC_AVAILABLE:
        model = PYDANTIC_MODELS[message_type]
        try:
            model.model_validate(message)
        except ValidationError as exc:
            raise ProtocolValidationError(str(exc)) from exc
    else:
        _validate_manual(message, message_type)

    return message_type


@dataclass
class ProtocolMessage:
    """Structured protocol envelope for coordinator/agent communication."""

    type: MessageType
    from_agent: str
    payload: Dict[str, Any] = field(default_factory=dict)
    to_agent: Optional[str] = None
    request_id: Optional[str] = None
    message_id: str = field(default_factory=_new_id)
    timestamp: str = field(default_factory=_utc_timestamp)

    def __post_init__(self) -> None:
        if isinstance(self.type, str):
            self.type = MessageType(self.type)
        validate_message_dict(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "request_id": self.request_id,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)

    @classmethod
    def from_dict(cls, message: Dict[str, Any]) -> "ProtocolMessage":
        message_type = validate_message_dict(message)
        return cls(
            type=message_type,
            from_agent=message["from_agent"],
            to_agent=message.get("to_agent"),
            request_id=message.get("request_id"),
            message_id=message.get("message_id", _new_id()),
            timestamp=message.get("timestamp", _utc_timestamp()),
            payload=message.get("payload", {}),
        )

    @classmethod
    def from_json(cls, raw_json: str) -> "ProtocolMessage":
        try:
            message = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise ProtocolValidationError("Invalid JSON payload") from exc
        return cls.from_dict(message)


class MessageFactory:
    """Factory helpers for canonical protocol messages."""

    @staticmethod
    def create_broadcast(
        sender_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        to_agent: Optional[str] = None,
    ) -> ProtocolMessage:
        payload = {
            "content": content,
            "metadata": metadata or {},
        }
        return ProtocolMessage(
            type=MessageType.BROADCAST,
            from_agent=sender_id,
            to_agent=to_agent,
            payload=payload,
        )

    @staticmethod
    def create_permission_request(
        agent_name: str,
        content: str,
        to_agent: str = "coordinator",
    ) -> ProtocolMessage:
        return ProtocolMessage(
            type=MessageType.PERMISSION_REQUEST,
            from_agent=agent_name,
            to_agent=to_agent,
            request_id=_new_request_id(),
            payload={"content": content},
        )

    @staticmethod
    def create_permission_response(
        agent_name: str,
        request_id: str,
        approved: bool,
        reason: str = "",
        to_agent: Optional[str] = None,
    ) -> ProtocolMessage:
        return ProtocolMessage(
            type=MessageType.PERMISSION_RESPONSE,
            from_agent=agent_name,
            to_agent=to_agent,
            request_id=request_id,
            payload={"approved": approved, "reason": reason},
        )

    @staticmethod
    def create_plan_approval_request(
        agent_name: str,
        plan_summary: str,
        files: Optional[List[str]] = None,
        to_agent: str = "coordinator",
    ) -> ProtocolMessage:
        return ProtocolMessage(
            type=MessageType.PLAN_APPROVAL_REQUEST,
            from_agent=agent_name,
            to_agent=to_agent,
            request_id=_new_request_id(),
            payload={"plan_summary": plan_summary, "files": files or []},
        )

    @staticmethod
    def create_plan_approval_response(
        agent_name: str,
        request_id: str,
        approved: bool,
        comments: str = "",
        to_agent: Optional[str] = None,
    ) -> ProtocolMessage:
        return ProtocolMessage(
            type=MessageType.PLAN_APPROVAL_RESPONSE,
            from_agent=agent_name,
            to_agent=to_agent,
            request_id=request_id,
            payload={"approved": approved, "comments": comments},
        )

    @staticmethod
    def create_agent_idle(
        agent_name: str,
        reason: str = "",
        to_agent: str = "coordinator",
    ) -> ProtocolMessage:
        return ProtocolMessage(
            type=MessageType.AGENT_IDLE,
            from_agent=agent_name,
            to_agent=to_agent,
            payload={"reason": reason},
        )

    @staticmethod
    def create_task_assigned(
        sender_id: str,
        to_agent: str,
        task_id: str,
        description: str,
    ) -> ProtocolMessage:
        return ProtocolMessage(
            type=MessageType.TASK_ASSIGNED,
            from_agent=sender_id,
            to_agent=to_agent,
            payload={"task_id": task_id, "description": description},
        )

    @staticmethod
    def create_shutdown_request(
        sender_id: str,
        reason: str,
        to_agent: Optional[str] = None,
    ) -> ProtocolMessage:
        return ProtocolMessage(
            type=MessageType.SHUTDOWN_REQUEST,
            from_agent=sender_id,
            to_agent=to_agent,
            request_id=_new_request_id(),
            payload={"reason": reason},
        )

    @staticmethod
    def create_shutdown_approved(
        agent_name: str,
        request_id: str,
        note: str = "",
        to_agent: Optional[str] = None,
    ) -> ProtocolMessage:
        return ProtocolMessage(
            type=MessageType.SHUTDOWN_APPROVED,
            from_agent=agent_name,
            to_agent=to_agent,
            request_id=request_id,
            payload={"note": note},
        )


def is_response_for(response: ProtocolMessage, request: ProtocolMessage) -> bool:
    """Check whether a response message is a valid reply to a request message."""

    expected_request_type = RESPONSE_FOR.get(response.type)
    if expected_request_type is None:
        return False
    return (
        expected_request_type == request.type
        and response.request_id == request.request_id
    )


def create_objective(
    description: str,
    success_criteria: Optional[List[str]] = None,
    phases: Optional[List[str]] = None,
    file_patterns: Optional[List[str]] = None,
    restricted_tools: Optional[List[str]] = None,
) -> Objective:
    """Create a structured objective used by power-mode session initialization."""

    return Objective(
        description=description,
        success_criteria=success_criteria or [],
        phases=phases or [],
        file_patterns=file_patterns or [],
        restricted_tools=restricted_tools or [],
    )
