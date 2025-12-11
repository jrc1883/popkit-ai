# PopKit Audio Feedback Hooks: Research & Implementation Strategy

**Research Date:** December 11, 2025
**Status:** Research Proposal
**Target Version:** 1.3.0 or 1.4.0
**Effort Level:** Medium

---

## Executive Summary

This document proposes integrating audio feedback into PopKit via a new hook system that announces key events (tool execution, AskUserQuestion prompts, completions) using text-to-speech (TTS). The implementation would:

- **Enable voice announcements** for important events without blocking tool execution
- **Support multiple TTS providers** (ElevenLabs, Google Cloud, OpenAI, edge-tts) with fallback strategy
- **Allow granular event control** via configuration (toggle speech on/off per event type)
- **Integrate seamlessly** with existing hook architecture (minimal disruption)
- **Preserve performance** with async, non-blocking TTS calls and aggressive timeouts

### Key Finding
Audio feedback is **feasible and valuable** for development workflows. The PopKit hook architecture supports it, but requires a new dedicated `notification-audio.py` hook + cloud integration.

---

## 1. Current State: Audio Feedback in Development Tools

### Existing Implementations in Development Environment

1. **PopKit's Current Audio**
   - `notification.py` hook has Windows-only PowerShell TTS
   - No cross-platform support
   - No voice customization
   - No event-driven audio

2. **IDE Integrations (Research)**
   - VS Code: Has terminal bells, no audio notifications
   - Cursor: Building native audio feedback (custom integration)
   - JetBrains: Plugin ecosystem supports audio but no native implementation
   - Claude Code: Notification system supports audio (non-functional currently)

3. **DevOps/Monitoring Tools**
   - GitHub Actions: No audio notifications
   - CI/CD pipelines: Often include audio alerts (Jenkins plugins, custom scripts)
   - Error monitoring (Sentry, DataDog): Desktop notifications + audio

### Why Audio Matters for Development Workflows

1. **Context Switching**: Audio feedback breaks attention burden of checking status
2. **AskUserQuestion UX**: Voice reading options + confirmation prevents missed questions
3. **Long-Running Tasks**: Announces completion while developer works on other tasks
4. **Accessibility**: Screen reader integration for visually impaired developers
5. **Focused Work**: Gentle audio notifications maintain flow state better than visual popups

### Design Pattern: When to Use Audio

✅ **Good Use Cases:**
- User decisions required (AskUserQuestion prompts)
- Task completion announcements (long-running operations >10s)
- Error/warning conditions
- Session start/stop events
- Agent transitions in Power Mode

❌ **Poor Use Cases:**
- Every tool execution (Too noisy)
- Real-time streaming status updates (Spam)
- Verbose explanations (Use text instead)

---

## 2. Text-to-Speech Service Comparison

### Evaluation Criteria
| Criteria | Weight | Importance |
|----------|--------|-----------|
| Cost per request | 25% | Free tier critical for open-source adoption |
| Voice quality | 20% | Natural-sounding for professional context |
| Latency | 20% | <2s for notifications; <0.5s streaming |
| Languages/voices | 15% | Global developer audience |
| API simplicity | 10% | Minimal dependencies, JSON REST API |
| Streaming support | 10% | For long announcements |

### TTS Service Options

#### 1. **ElevenLabs** (Highest Quality)
**Pricing Model:** Credit-based
**Free Tier:** 10,000 credits/month = ~20,000 characters TTS
**Paid Plans:** Starter ($5/mo, 30K credits) → Business (custom)

**Pros:**
- Highest voice quality (natural, emotional)
- 32 languages, 100+ voices, voice cloning available
- Streaming support (ChunkedStream, streaming WebSocket)
- Vision-aligned: Used by OpenAI ChatGPT voice feature
- API simplicity: 2-3 HTTP calls only
- Rate limiting: Generous (100-1000 req/min depending on tier)

**Cons:**
- Paid after free tier exhaustion
- Commercial use requires Business plan ($99+/mo)
- Streaming adds latency (need buffering)

**Recommendation:** ⭐⭐⭐⭐⭐ **PRIMARY CHOICE** for PopKit
*Rationale: Quality + free tier alignment with open-source model*

**API Example:**
```python
import requests

response = requests.post(
    f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream",
    headers={"xi-api-key": API_KEY},
    json={"text": "PopKit is asking you a question", "model_id": "eleven_turbo_v2"},
    stream=True
)

# Stream audio chunks for playback
for chunk in response.iter_content(chunk_size=1024):
    audio_player.play(chunk)
```

#### 2. **Google Cloud Text-to-Speech**
**Pricing:** $16 per 1M characters (after free tier)
**Free Tier:** 500K characters/month

**Pros:**
- Reliable, enterprise-grade
- SSML support for advanced control
- Low latency (<500ms)
- Many voices + languages

**Cons:**
- Premium pricing
- Less "natural" voice quality than ElevenLabs
- Requires Google Cloud account setup
- No streaming WebSocket

**Recommendation:** ⭐⭐⭐ **SECONDARY OPTION**
*Rationale: Good fallback if ElevenLabs fails*

#### 3. **OpenAI TTS** (New)
**Pricing:** $15 per 1M characters
**Free Tier:** None (requires API key + payment method)

**Pros:**
- High quality (comparable to ElevenLabs)
- Simple REST API
- 2 voice quality options
- Streaming endpoints available

**Cons:**
- No free tier (barrier for open-source)
- Limited voice selection (6 voices)
- Requires paid OpenAI account

**Recommendation:** ⭐⭐ **AVOID FOR NOW**
*Rationale: No free tier conflicts with open-source accessibility*

#### 4. **Microsoft Edge TTS (Free/Open)**
**Pricing:** FREE
**Free Tier:** Unlimited (uses Edge's cloud API)

**Pros:**
- Completely free
- No API key required
- Python library available (`edge-tts`)
- Acceptable voice quality for notifications
- Streaming support

**Cons:**
- Voice quality < ElevenLabs (more robotic)
- Rate limiting enforced by Microsoft
- No official API support
- Language/voice selection limited

**Recommendation:** ⭐⭐⭐ **FALLBACK OPTION**
*Rationale: Emergency backup when ElevenLabs quota exhausted*

#### 5. **Picovoice Orca** (On-Device)
**Pricing:** FREE (open-source)
**Free Tier:** Unlimited local processing

**Pros:**
- On-device (zero latency, no internet required)
- No rate limiting
- Privacy-first (local execution only)
- Open-source

**Cons:**
- Voice quality: low-medium (robotic, synthesized)
- Single voice option per language
- Models require download (~10-20MB)
- Setup complexity

**Recommendation:** ⭐⭐ **EXPERIMENTAL OPTION**
*Rationale: Good for offline scenarios; setup complexity makes it secondary*

### Recommended Multi-Tier Strategy

```
Tier 1: ElevenLabs (Primary)
  └─ Fall back to: Google Cloud (Backup)
      └─ Fall back to: Edge TTS (Free fallback)
          └─ Fall back to: Picovoice (Offline-only)
              └─ Fall back to: Silent mode (No TTS available)
```

**Cost Analysis for PopKit:**
- Typical PopKit session: 5-10 audio notifications
- ~100 characters per notification
- ElevenLabs free tier: 10,000 credits = 20,000 characters = **200 sessions/month**
- **Result: Free tier covers typical usage; no cost for core open-source users**

---

## 3. PopKit Hook Architecture: Audio Integration Points

### Current Hook Execution Flow
```
User Input
    ↓
[PreToolUse Hook] → Tool Execution → [PostToolUse Hook]
                                         ↓
                                    User Sees Result
```

### Proposed Audio Hook Addition
```
User Input
    ↓
[PreToolUse Hook] + [PreToolUse Audio Hook]  → Tool Execution
    ↓ (async, non-blocking)
[Announce Tool Start] (optional)
    ↓
[PostToolUse Hook] + [PostToolUse Audio Hook]
    ↓ (async, non-blocking)
[Announce Result/Warning]
    ↓
User Sees Result + Hears Announcement
```

### New Hook Files Required

#### File 1: `packages/plugin/hooks/audio-feedback.py`
**Purpose:** Core audio feedback hook for all events
**Event Triggers:** PostToolUse (all tools) + UserPromptSubmit (AskUserQuestion detection)
**Timeout:** 3000ms (async, non-blocking)

**Responsibilities:**
1. Detect if audio should play for this event
2. Select TTS provider (ElevenLabs → Google → Edge → Silent)
3. Build announcement text (context-specific)
4. Make async HTTP call to TTS API
5. Queue audio for playback (OS-specific)
6. Never block tool execution (fire-and-forget)

**Pseudocode:**
```python
class AudioFeedbackHook(StatelessHook):
    def process(self, ctx: HookContext) -> HookContext:
        # Check if audio enabled for this event type
        if not self.should_play_audio(ctx):
            return ctx

        # Determine announcement text
        announcement = self.build_announcement(ctx)

        # Get TTS audio (with fallback strategy)
        try:
            audio_bytes = self.synthesize_speech(
                announcement,
                provider="elevenlabs"
            )
        except RateLimitError:
            audio_bytes = self.synthesize_speech(
                announcement,
                provider="google_cloud"
            )
        except Exception:
            audio_bytes = self.synthesize_speech(
                announcement,
                provider="edge_tts"
            )

        # Queue for playback (non-blocking)
        self.queue_audio_playback(audio_bytes)

        return ctx
```

#### File 2: `packages/plugin/hooks/utils/audio_synthesizer.py`
**Purpose:** Abstraction layer for TTS providers
**Responsibility:**
- Multi-provider TTS abstraction
- Fallback logic + error handling
- API key management
- Caching of common announcements

**Interface:**
```python
class AudioSynthesizer:
    def synthesize(self, text: str, provider: str = "auto") -> bytes:
        """Convert text to audio bytes with fallback strategy."""
        providers = [provider] if provider != "auto" else self.FALLBACK_ORDER

        for prov in providers:
            try:
                return getattr(self, f"_synthesize_{prov}")(text)
            except Exception as e:
                logger.debug(f"Provider {prov} failed: {e}, trying next...")

        return self.silent_audio()

    def _synthesize_elevenlabs(self, text: str) -> bytes:
        """ElevenLabs API call with streaming."""
        ...

    def _synthesize_google_cloud(self, text: str) -> bytes:
        """Google Cloud TTS API call."""
        ...

    def _synthesize_edge_tts(self, text: str) -> bytes:
        """Microsoft Edge TTS via edge-tts library."""
        ...
```

#### File 3: `packages/plugin/hooks/utils/audio_player.py`
**Purpose:** Cross-platform audio playback
**Responsibility:**
- Detect OS (macOS/Linux/Windows)
- Select appropriate audio player (`afplay`, `paplay`, `powershell`)
- Queue audio for non-blocking playback
- Handle audio file cleanup

**Cross-Platform Support:**
```python
class AudioPlayer:
    def play(self, audio_bytes: bytes, block=False):
        """Play audio across platforms."""
        platform = sys.platform

        if platform == "darwin":
            # macOS: use afplay
            subprocess.Popen(["afplay", "-"], stdin=PIPE).communicate(audio_bytes)
        elif platform == "linux":
            # Linux: use paplay (PulseAudio)
            subprocess.Popen(["paplay"], stdin=PIPE).communicate(audio_bytes)
        elif platform == "win32":
            # Windows: use powershell
            import winsound
            winsound.PlaySound(audio_bytes, winsound.SND_MEMORY)

        if not block:
            # Fire-and-forget async playback
            threading.Thread(target=self._play_async, args=(audio_bytes,)).start()
```

### Event-Specific Announcements

#### AskUserQuestion Detection
```python
def build_announcement_for_ask_user_question(question: str, options: list) -> str:
    return f"""
    PopKit is asking you a question.
    {question}
    Your options are:
    {', or '.join([opt['label'] for opt in options])}
    """
```

**Example Audio Output:**
> "PopKit is asking you a question. Would you like to set up Power Mode for multi-agent orchestration? Your options are Redis Mode, File Mode, or Skip for now."

#### Tool Completion Announcement
```python
def build_announcement_for_tool_completion(tool_name: str, status: str) -> str:
    if status == "success":
        return f"{tool_name} completed successfully."
    elif status == "warning":
        return f"{tool_name} completed with warnings. Check the output."
    else:
        return f"{tool_name} encountered an error."
```

#### Multi-Agent Phase Transitions (Power Mode)
```python
def build_announcement_for_agent_transition(from_agent: str, to_agent: str) -> str:
    return f"Transitioning from {from_agent} to {to_agent}."
```

### Configuration: `packages/plugin/hooks/utils/audio_config.py`

```python
AUDIO_CONFIG = {
    "enabled": True,
    "events": {
        "ask_user_question": {
            "enabled": True,
            "voice_options": True,  # Read option list aloud
            "playback_speed": 1.0,
        },
        "tool_completion": {
            "enabled": True,
            "only_on_error": False,  # Play for all completions or errors only?
            "playback_speed": 1.0,
        },
        "agent_transition": {
            "enabled": False,  # Verbose; off by default
            "playback_speed": 1.0,
        },
        "session_start": {
            "enabled": False,  # Quiet startup
            "announcement": "PopKit is ready.",
        },
        "session_end": {
            "enabled": True,
            "announcement": "PopKit session complete.",
        },
    },
    "providers": {
        "elevenlabs": {
            "api_key": "${ELEVENLABS_API_KEY}",
            "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel (default)
            "model_id": "eleven_turbo_v2",  # Lowest latency
        },
        "google_cloud": {
            "api_key": "${GOOGLE_CLOUD_API_KEY}",
            "voice_code": "en-US-Neural2-A",  # Amira
        },
        "edge_tts": {
            "voice": "en-US-AriaNeural",  # Free
        },
    },
    "fallback_order": ["elevenlabs", "google_cloud", "edge_tts", "silent"],
    "cache": {
        "enabled": True,
        "ttl_hours": 24,
        "storage": "~/.claude/audio-cache/",
    },
}
```

---

## 4. Implementation Architecture

### Phase 1: Core Audio System (v1.3.0)
**Scope:** Basic TTS integration for AskUserQuestion events
**Effort:** 1-2 weeks
**Files:**
- `packages/plugin/hooks/audio-feedback.py` (150 lines)
- `packages/plugin/hooks/utils/audio_synthesizer.py` (300 lines)
- `packages/plugin/hooks/utils/audio_player.py` (150 lines)
- `packages/plugin/hooks/utils/audio_config.py` (80 lines)
- Update `packages/plugin/hooks/hooks.json` to register audio hook
- Tests: 40-50 test cases

**Key Features:**
- ✅ AskUserQuestion announcements
- ✅ ElevenLabs + fallback support
- ✅ Cross-platform playback (Mac/Linux/Windows)
- ✅ Non-blocking async execution
- ✅ Configuration file for enable/disable

**Deliverables:**
- Audio announcement plays when AskUserQuestion is detected
- Voice customization via config
- Fallback to silent mode on API errors

### Phase 2: Event Expansion (v1.4.0)
**Scope:** Extend audio feedback to more events
**Effort:** 1-2 weeks
**Additions:**
- Tool completion announcements
- Error/warning alerts
- Session start/end events
- Agent transition notifications (Power Mode)

**Configuration Enhancement:**
- Per-event enable/disable toggles
- Voice customization per event
- Playback speed control

### Phase 3: Voice Customization & Premium (v1.5.0)
**Scope:** Advanced voice features for premium users
**Effort:** 2-3 weeks
**Features:**
- Voice cloning (ElevenLabs premium)
- Multiple voice personas
- Emotional tone selection
- Audio visualization (waveform display)
- Recording + voice input for confirmation

### Phase 4: Power Mode Integration (v1.6.0)
**Scope:** Multi-agent audio coordination
**Effort:** 2 weeks
**Features:**
- Agent phase announcements with voice transitions
- Parallel agent status updates
- Conflict resolution notifications
- Real-time agent mesh status in audio

---

## 5. Data Flow & Sequence Diagrams

### Sequence: AskUserQuestion Audio Feedback

```
User Input
    │
    ├─→ [AskUserQuestion Tool Invoked]
    │        │
    │        ├─→ Claude renders question to user
    │        │
    │        └─→ [PostToolUse Hook Triggered]
    │             │
    │             ├─→ [Audio Feedback Hook Detected]
    │             │        │
    │             │        ├─→ Check: Is AskUserQuestion event?
    │             │        │    ✓ YES → Continue
    │             │        │
    │             │        ├─→ Check: Audio enabled?
    │             │        │    ✓ YES → Continue
    │             │        │
    │             │        ├─→ Build announcement text:
    │             │        │    "PopKit is asking you a question.
    │             │        │     Would you like to set up Power Mode?
    │             │        │     Your options are Redis Mode,
    │             │        │     File Mode, or Skip for now."
    │             │        │
    │             │        ├─→ Call ElevenLabs API
    │             │        │    POST /v1/text-to-speech/{voice_id}
    │             │        │    Response: audio_bytes (MP3 stream)
    │             │        │
    │             │        ├─→ Queue audio playback
    │             │        │    Thread.start() → Play audio in background
    │             │        │    (Non-blocking, timeout 2s)
    │             │        │
    │             │        └─→ Return context (unmodified)
    │             │
    │             └─→ [Other PostToolUse Hooks Continue]
    │
    └─→ User sees question + hears announcement
        (User can interact with AskUserQuestion while audio plays)
```

### Timing & Non-Blocking Guarantees

```
Timeline (milliseconds):
0ms   ┌─────────────────────────────────────────────┐
      │ PostToolUse Hook Triggered                  │
      │ (Tool execution just completed)             │
10ms  ├─ Audio Feedback Hook Starts                 │
      │  (All other hooks run in parallel)          │
20ms  │                                             │
      │  ┌─────────────────────────────────────┐   │
      │  │ Audio Synthesis Task Spawned        │   │
30ms  │  │ (Thread #42)                        │   │
      │  ├─ API Call to ElevenLabs            │   │
      │  │  (Network request, 500-1000ms)     │   │
40ms  │  │                                     │   │
      │  │  ┌─────────────────────────────┐   │   │
      │  │  │ ElevenLabs Responds         │   │   │
50ms  │  │  │ (Audio bytes arrive)        │   │   │
      │  │  └─────────────────────────────┘   │   │
      │  │                                     │   │
      │  │  Audio Playback Started            │   │
60ms  │  │  (Background thread)               │   │
      │  │                                     │   │
      │  └─────────────────────────────────┘   │
70ms  │                                             │
      │ Hook Return (Hook function completes)      │
      │ ✅ User never blocked                      │
      │ ✅ Audio still playing in background       │
      │ ✅ Total hook time: 1-2ms                  │
80ms  ├─────────────────────────────────────────────┤
      │ [Other hooks continue]                      │
      │ Audio still playing (~4s for announcement)  │
      │ User can interact while audio plays         │
      └─────────────────────────────────────────────┘
```

### Error Handling Flow

```
[Audio Feedback Hook Start]
    │
    ├─ Check ElevenLabs API Key Available?
    │  └─ NO? → Try next provider (Google Cloud)
    │
    ├─ Make API Call to ElevenLabs
    │  ├─ Network timeout? → Fallback to Google Cloud
    │  ├─ Rate limit (429)? → Fallback to Google Cloud
    │  ├─ Auth error (401)? → Log, try next provider
    │  ├─ Invalid text (400)? → Log, try sanitized version
    │  └─ Success? → Queue audio playback
    │
    ├─ If Google Cloud fails?
    │  └─ Try edge-tts (Free alternative)
    │
    ├─ If edge-tts fails?
    │  └─ Silent mode (No audio, but log error)
    │
    └─ Return context (Hook always succeeds, never blocks)
```

---

## 6. Implementation: Code Examples

### Example 1: Audio Feedback Hook Main Loop

```python
#!/usr/bin/env python3
"""
audio-feedback.py: Announce important events with text-to-speech.

Hook Event: PostToolUse
Triggered by: All tools (Bash, Read, Write, Edit, Task, etc.)
Timeout: 3000ms (async, non-blocking)
"""

import json
import sys
import threading
from typing import Optional

from utils.stateless_hook import StatelessHook, HookContext
from utils.audio_synthesizer import AudioSynthesizer
from utils.audio_player import AudioPlayer
from utils.audio_config import AUDIO_CONFIG


class AudioFeedbackHook(StatelessHook):
    def __init__(self):
        super().__init__()
        self.synthesizer = AudioSynthesizer()
        self.player = AudioPlayer()
        self.config = AUDIO_CONFIG

    def process(self, ctx: HookContext) -> HookContext:
        """Process hook and queue audio announcement if applicable."""

        # Detect event type
        event_type = self._detect_event_type(ctx)
        if not event_type:
            return ctx  # Not an event we handle

        # Check if audio is enabled for this event
        if not self._should_play_audio(event_type):
            return ctx

        # Build announcement text based on event
        announcement = self._build_announcement(event_type, ctx)
        if not announcement:
            return ctx

        # Spawn async audio playback thread
        # (Never block hook execution)
        thread = threading.Thread(
            target=self._play_audio_async,
            args=(announcement,),
            daemon=True
        )
        thread.start()

        return ctx

    def _detect_event_type(self, ctx: HookContext) -> Optional[str]:
        """Detect what type of event triggered this hook."""

        # Check for AskUserQuestion tool
        if ctx.tool_name == "AskUserQuestion":
            return "ask_user_question"

        # Check for tool completion
        if ctx.tool_response and "completed" in ctx.tool_response.lower():
            return "tool_completion"

        # More event types in Phase 2
        return None

    def _should_play_audio(self, event_type: str) -> bool:
        """Check if audio is enabled for this event type."""
        return self.config["enabled"] and \
               self.config["events"].get(event_type, {}).get("enabled", False)

    def _build_announcement(self, event_type: str, ctx: HookContext) -> Optional[str]:
        """Build announcement text for this event."""

        if event_type == "ask_user_question":
            # Extract question and options from tool input
            question = ctx.tool_input.get("question", "Unknown question")
            options = ctx.tool_input.get("options", [])

            announcement = f"PopKit is asking you a question. {question}"

            # Add options if configured
            if self.config["events"]["ask_user_question"].get("voice_options"):
                option_labels = [opt.get("label") for opt in options]
                announcement += f" Your options are {', or '.join(option_labels)}."

            return announcement

        elif event_type == "tool_completion":
            tool_name = ctx.tool_name
            return f"{tool_name} completed successfully."

        return None

    def _play_audio_async(self, announcement: str):
        """Synthesize and play audio asynchronously."""
        try:
            # Synthesize speech (with fallback)
            audio_bytes = self.synthesizer.synthesize(announcement)

            # Play audio (non-blocking)
            self.player.play(audio_bytes, block=False)

        except Exception as e:
            # Log error but never raise (never block hook)
            print(f"Audio feedback error: {e}", file=sys.stderr)


def main():
    """Hook entry point."""
    try:
        input_data = json.loads(sys.stdin.read())
        ctx = HookContext.from_dict(input_data)

        hook = AudioFeedbackHook()
        result_ctx = hook.process(ctx)

        # Output result as JSON
        print(json.dumps(result_ctx.to_dict()))

    except Exception as e:
        # Never raise from hook; always output valid JSON
        print(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    main()
```

### Example 2: Audio Synthesizer with Multi-Provider Fallback

```python
"""
audio_synthesizer.py: Multi-provider TTS with intelligent fallback.
"""

import os
import requests
import logging
from typing import Optional
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioSynthesizer:
    """Synthesize speech with multi-provider fallback strategy."""

    FALLBACK_ORDER = ["elevenlabs", "google_cloud", "edge_tts", "silent"]

    def __init__(self, config: dict):
        self.config = config
        self.cache_dir = Path(config["cache"]["storage"]).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def synthesize(self, text: str, provider: str = "auto") -> bytes:
        """
        Synthesize text to speech with fallback strategy.

        Args:
            text: Text to synthesize
            provider: Provider to use ("auto" for fallback chain)

        Returns:
            Audio bytes (MP3 format)
        """

        # Check cache first
        cached = self._get_cached_audio(text)
        if cached:
            return cached

        # Try each provider in fallback order
        providers = [provider] if provider != "auto" else self.FALLBACK_ORDER

        for prov in providers:
            try:
                logger.debug(f"Trying TTS provider: {prov}")
                audio_bytes = self._synthesize_with_provider(text, prov)

                # Cache for future use
                self._cache_audio(text, audio_bytes)

                logger.info(f"TTS synthesis succeeded with {prov}")
                return audio_bytes

            except Exception as e:
                logger.warning(f"Provider {prov} failed: {e}")
                continue

        # If all providers fail, return silent audio
        logger.error("All TTS providers failed, returning silent audio")
        return self._silent_audio()

    def _synthesize_with_provider(self, text: str, provider: str) -> bytes:
        """Synthesize with specific provider."""

        if provider == "elevenlabs":
            return self._synthesize_elevenlabs(text)
        elif provider == "google_cloud":
            return self._synthesize_google_cloud(text)
        elif provider == "edge_tts":
            return self._synthesize_edge_tts(text)
        elif provider == "silent":
            return self._silent_audio()
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _synthesize_elevenlabs(self, text: str) -> bytes:
        """ElevenLabs TTS API call."""

        api_key = os.environ.get(
            "ELEVENLABS_API_KEY",
            self.config.get("providers", {}).get("elevenlabs", {}).get("api_key")
        )

        if not api_key:
            raise ValueError("ElevenLabs API key not configured")

        voice_id = self.config["providers"]["elevenlabs"]["voice_id"]
        model_id = self.config["providers"]["elevenlabs"]["model_id"]

        # Call ElevenLabs API with streaming
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream",
            headers={"xi-api-key": api_key},
            json={
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                }
            },
            timeout=5,  # 5 second timeout
            stream=True
        )

        response.raise_for_status()

        # Collect audio bytes from stream
        return b"".join(response.iter_content(chunk_size=1024))

    def _synthesize_google_cloud(self, text: str) -> bytes:
        """Google Cloud TTS API call."""

        from google.cloud import texttospeech

        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-A",
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        return response.audio_content

    def _synthesize_edge_tts(self, text: str) -> bytes:
        """Microsoft Edge TTS (free alternative)."""

        import edge_tts
        import asyncio

        async def _synthesize():
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.config["providers"]["edge_tts"]["voice"]
            )

            audio_chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])

            return b"".join(audio_chunks)

        return asyncio.run(_synthesize())

    def _silent_audio(self) -> bytes:
        """Return silent audio (1 second of silence)."""
        # MP3 frame of silence (LAME codec)
        return b"\xff\xfb\x10\x00" + (b"\x00" * 100)  # Minimal silent MP3

    def _get_cached_audio(self, text: str) -> Optional[bytes]:
        """Retrieve cached audio if available."""

        if not self.config["cache"]["enabled"]:
            return None

        cache_file = self.cache_dir / self._hash_text(text)

        if cache_file.exists():
            return cache_file.read_bytes()

        return None

    def _cache_audio(self, text: str, audio_bytes: bytes):
        """Cache audio bytes for future use."""

        if not self.config["cache"]["enabled"]:
            return

        cache_file = self.cache_dir / self._hash_text(text)
        cache_file.write_bytes(audio_bytes)

    @staticmethod
    def _hash_text(text: str) -> str:
        """Hash text for cache key."""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()
```

---

## 7. Configuration & User Control

### Configuration File: `.claude/audio-feedback.json`

```json
{
  "enabled": true,
  "events": {
    "ask_user_question": {
      "enabled": true,
      "voice_options": true,
      "playback_speed": 1.0,
      "voice_id": "21m00Tcm4TlvDq8ikWAM"
    },
    "tool_completion": {
      "enabled": false,
      "only_on_error": true,
      "playback_speed": 1.0
    },
    "agent_transition": {
      "enabled": false,
      "playback_speed": 1.0
    },
    "session_start": {
      "enabled": false,
      "announcement": "PopKit is ready"
    },
    "session_end": {
      "enabled": true,
      "announcement": "PopKit session complete"
    }
  },
  "providers": {
    "elevenlabs": {
      "api_key": "${ELEVENLABS_API_KEY}",
      "voice_id": "21m00Tcm4TlvDq8ikWAM",
      "model_id": "eleven_turbo_v2"
    },
    "google_cloud": {
      "api_key": "${GOOGLE_CLOUD_API_KEY}",
      "voice_code": "en-US-Neural2-A"
    },
    "edge_tts": {
      "voice": "en-US-AriaNeural"
    }
  },
  "fallback_order": ["elevenlabs", "google_cloud", "edge_tts", "silent"],
  "cache": {
    "enabled": true,
    "ttl_hours": 24,
    "storage": "~/.claude/audio-cache/"
  }
}
```

### CLI Commands for Configuration

```bash
# Enable/disable audio for specific event
/popkit:audio config set ask_user_question.enabled true
/popkit:audio config set tool_completion.enabled true

# Set voice
/popkit:audio voice list                    # Show available voices
/popkit:audio voice set "Rachel"            # Set voice by name
/popkit:audio voice test "This is a test"   # Test current voice

# Manage providers
/popkit:audio provider set elevenlabs       # Set primary provider
/popkit:audio provider test                 # Test all providers

# Test audio playback
/popkit:audio test                          # Play test announcement
```

---

## 8. Risk Analysis & Mitigation

### Risk 1: API Cost & Quota Exhaustion
**Severity:** Medium
**Impact:** Audio announcements stop working if quota exceeded

**Mitigation:**
- ElevenLabs free tier: 10,000 credits/month = 200 sessions
- Implement cache to avoid re-synthesizing same text
- Add rate limiting (max 3 audio requests per minute)
- Fallback chain ensures graceful degradation

### Risk 2: Network Latency & Blocking
**Severity:** High
**Impact:** Hook timeout causes tool failure

**Mitigation:**
- **All TTS calls are async/non-blocking** (spawned in background thread)
- Hook returns immediately (1-2ms), audio plays in parallel
- 3-second hook timeout never blocks actual tool execution
- Silent fallback if network unavailable

### Risk 3: Audio Spam & User Annoyance
**Severity:** Medium
**Impact:** Users disable feature or get distracted

**Mitigation:**
- Off by default for most events
- Only enable for high-value events (AskUserQuestion)
- Configurable per-event
- Volume/playback speed control
- User can disable anytime

### Risk 4: Accessibility Issues
**Severity:** Medium
**Impact:** Audio may conflict with screen readers

**Mitigation:**
- Audio is secondary to text output
- All text is displayed regardless of audio status
- Screen reader compatibility testing needed (Phase 2)
- ARIA labels for AskUserQuestion options

### Risk 5: Platform Compatibility
**Severity:** Low
**Impact:** Audio doesn't work on some systems

**Mitigation:**
- Cross-platform playback tested on Mac/Linux/Windows
- Graceful fallback if audio system unavailable
- Silent mode as last resort
- Clear error messages in logs

### Risk 6: API Key Security
**Severity:** Medium
**Impact:** TTS API keys exposed in config

**Mitigation:**
- Read API keys from environment variables first
- Config file templates use `${ELEVENLABS_API_KEY}` syntax
- Never log API keys
- Recommend git-ignoring config with sensitive data
- Cloud integration (future) uses secure token management

---

## 9. Testing Strategy

### Unit Tests (40-50 test cases)

```python
# tests/hooks/test_audio_feedback.py

def test_audio_feedback_disabled_no_synthesis():
    """If audio disabled, no synthesis attempt."""
    hook = AudioFeedbackHook(enabled=False)
    ctx = create_mock_context("ask_user_question")
    result = hook.process(ctx)
    assert synthesizer.synthesize.call_count == 0

def test_ask_user_question_triggers_announcement():
    """AskUserQuestion event triggers audio announcement."""
    hook = AudioFeedbackHook()
    ctx = create_mock_context(
        tool_name="AskUserQuestion",
        question="Set up Power Mode?",
        options=[{"label": "Yes"}, {"label": "No"}]
    )
    hook.process(ctx)
    synthesizer.synthesize.assert_called_once()
    assert "Power Mode" in synthesizer.synthesize.call_args[0][0]

def test_fallback_to_google_cloud_on_elevenlabs_failure():
    """If ElevenLabs fails, try Google Cloud."""
    synthesizer.synthesize_elevenlabs.side_effect = Exception("Rate limit")
    audio = synthesizer.synthesize("test", provider="auto")
    assert synthesizer.synthesize_google_cloud.called

def test_silent_fallback_on_all_providers_failure():
    """If all providers fail, return silent audio."""
    for provider in ["elevenlabs", "google_cloud", "edge_tts"]:
        synthesizer.__dict__[f"_synthesize_{provider}"].side_effect = Exception()

    audio = synthesizer.synthesize("test")
    assert audio == synthesizer._silent_audio()

def test_audio_cached_on_repeat():
    """Repeated announcements use cached audio."""
    text = "Set up Power Mode?"
    audio1 = synthesizer.synthesize(text)
    audio2 = synthesizer.synthesize(text)

    # Should be cached; only one API call
    assert synthesizer.synthesize_elevenlabs.call_count == 1
    assert audio1 == audio2

def test_hook_never_blocks_execution():
    """Hook returns in <10ms despite async TTS."""
    import time
    ctx = create_mock_context("ask_user_question")

    start = time.time()
    hook.process(ctx)
    elapsed = time.time() - start

    assert elapsed < 0.01  # <10ms
    # But audio is still playing in background thread
```

### Integration Tests

```python
# tests/hooks/test_audio_integration.py

def test_audio_feedback_with_real_elevenlabs_api():
    """End-to-end test with real ElevenLabs API (requires API key)."""
    if not os.environ.get("ELEVENLABS_API_KEY"):
        pytest.skip("ElevenLabs API key not set")

    synthesizer = AudioSynthesizer(load_config())
    audio = synthesizer.synthesize("Hello, this is PopKit")

    assert len(audio) > 0
    assert audio.startswith(b"\xff\xfb")  # MP3 header

def test_cross_platform_audio_playback():
    """Test audio playback on current platform."""
    player = AudioPlayer()
    test_audio = load_test_audio_file("test.mp3")

    # Should not raise exception
    player.play(test_audio, block=False)

def test_audio_feedback_with_ask_user_question():
    """Integration test: AskUserQuestion triggers audio."""
    # Simulate full hook flow
    ctx = create_full_hook_context(tool_name="AskUserQuestion")
    hook = AudioFeedbackHook()
    result = hook.process(ctx)

    # Audio should have been queued
    assert audio_player.play.called
```

### Manual Testing Checklist

- [ ] Enable audio for AskUserQuestion
- [ ] Trigger AskUserQuestion from `/popkit:power init`
- [ ] Verify announcement plays (no blocking)
- [ ] Test with ElevenLabs API key set
- [ ] Test with API key unset (fallback to silent)
- [ ] Test rate limiting (exceed 3 requests/min)
- [ ] Test on Mac (afplay), Linux (paplay), Windows (winsound)
- [ ] Verify config file loaded correctly
- [ ] Test cache behavior (repeated announcements)
- [ ] Check stderr for error messages (no exceptions)

---

## 10. Version & Milestone Roadmap

### Version 1.3.0: Audio Feedback MVP
**Status:** Recommended as NEXT FEATURE
**Timeline:** 2-3 weeks
**Priority:** P2 (Medium)
**Effort:** Medium (80-120 hours)

**Rationale:**
- Non-intrusive feature (off by default)
- High user value (AskUserQuestion UX improvement)
- Leverages existing hook infrastructure
- No breaking changes

**Milestones:**
- ✅ Week 1: Core implementation (audio synthesis, playback)
- ✅ Week 2: Integration & testing
- ✅ Week 3: Documentation & beta release

### Version 1.4.0: Event Expansion & Advanced Features
**Status:** Recommended as FOLLOW-UP
**Timeline:** 3-4 weeks
**Priority:** P3 (Medium-Low)
**Effort:** Medium (100-150 hours)

**Additions:**
- Tool completion announcements
- Error/warning alerts
- Session start/end events
- Agent transition notifications
- Voice customization UI

### Phase 2 Timeline (Combined)
```
NOW                                           2-3 months
├─ v1.3.0 (2-3 weeks)
│  ├─ Audio Feedback MVP
│  ├─ AskUserQuestion support
│  └─ Release
│
├─ v1.4.0 (3-4 weeks)
│  ├─ Event expansion
│  ├─ Voice customization
│  └─ Release
│
└─ v1.5.0 (Premium features, optional)
   ├─ Voice cloning
   ├─ Emotional tones
   └─ Advanced customization
```

### Feature Gate Strategy

For v1.3.0, use feature flags to gate audio features:

```python
FEATURE_FLAGS = {
    "audio_feedback": {
        "enabled": True,
        "version_min": "1.3.0",
        "plan": "free",  # Available on free plan
    },
    "voice_cloning": {
        "enabled": False,
        "version_min": "1.5.0",
        "plan": "premium",  # Premium feature (future)
    },
}
```

---

## 11. Competitive Analysis

### Existing Audio Feedback in Development Tools

| Tool | Audio Support | Quality | Implementation |
|------|---------------|---------|-----------------|
| **VS Code** | ❌ No | N/A | N/A |
| **Cursor** | 🟡 Building | Unknown | Custom integration |
| **Windsurf** | ❌ No | N/A | N/A |
| **GitHub Copilot** | ❌ No | N/A | N/A |
| **PopKit (Current)** | 🟡 Windows-only | Robotic | PowerShell TTS |
| **PopKit (Proposed)** | ✅ Cross-platform | Natural | ElevenLabs |

**Opportunity:** PopKit could be **first development IDE plugin with natural-sounding audio feedback** across all platforms.

---

## 12. Recommendation Summary

### Should PopKit Implement Audio Feedback?

**Answer: YES, strongly recommended.**

**Rationale:**
1. **User Value:** High impact on AskUserQuestion UX (clear voice announcements)
2. **Feasibility:** Straightforward implementation using existing hook infrastructure
3. **Cost:** Free tier covers typical usage; no cost impact
4. **Adoption:** Feature can be off by default; non-disruptive
5. **Competitive Advantage:** First AI IDE plugin with cross-platform natural audio feedback
6. **Accessibility:** Improves experience for developers with visual impairments

### Recommended Approach

1. **Start with v1.3.0 MVP**: Focus on AskUserQuestion events only
2. **Use ElevenLabs** as primary provider (best voice quality + free tier alignment)
3. **Implement fallback chain** (Google Cloud → Edge TTS → Silent) for robustness
4. **Make it configurable** (per-event enable/disable toggles)
5. **Plan Phase 2** (v1.4.0) for event expansion and advanced features
6. **Gather user feedback** before investing in premium features

### Success Metrics

Track these metrics after v1.3.0 release:
- % of users who enable audio feedback
- Audio announcement completion rate (no failures)
- User satisfaction survey scores
- TTS API cost (should stay in free tier)
- Performance impact (hook should add <5ms overhead)

---

## 13. References & Resources

### Official Documentation

- **ElevenLabs API Docs:** https://elevenlabs.io/docs/api
- **ElevenLabs Pricing:** https://elevenlabs.io/pricing/api
- **Google Cloud TTS:** https://cloud.google.com/text-to-speech
- **Azure Speech Services:** https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/
- **OpenAI TTS:** https://platform.openai.com/docs/guides/text-to-speech

### Open Source Libraries

- **RealtimeTTS** (Python): Real-time speech synthesis - https://github.com/KoljaB/RealtimeTTS
- **edge-tts** (Python): Microsoft Edge TTS API - https://github.com/rany2/edge-tts
- **pyttsx3** (Python): Offline TTS - https://github.com/nateshmbhat/pyttsx3
- **Picovoice Orca** (On-device): https://picovoice.ai/

### Best Practices

- **Audio UX:** https://medium.com/@fernando1lins/lessons-learned-in-audio-feedback-for-game-and-app-design-e4818c9b72fd
- **Notification Patterns:** https://www.interaction-design.org/literature/article/talk-to-me-feedback-and-notifications-in-mobile-design
- **Claude Code Hooks:** [Claude Code Audio Feedback Hooks Blog](https://www.pascal-poredda.com/blog/claude-code-audio-feedback-with-hooks)

### Related PopKit Issues/Features

- Issue #159: AskUserQuestion enforcement via hooks
- Power Mode: Multi-agent orchestration (audio feedback could enhance this)
- Session continuity: Audio announcements for session transitions

---

## 14. Appendix: Quick Reference

### TTS Service Comparison Matrix

```
╔══════════════════╦═══════════╦═══════════╦═════════╦═════════════╗
║ Feature          ║ ElevenLabs║ Google    ║ OpenAI  ║ Edge TTS    ║
╠══════════════════╬═══════════╬═══════════╬═════════╬═════════════╣
║ Cost             ║ Free tier ║ Paid only ║ Paid    ║ Free        ║
║ Voice quality    ║ ⭐⭐⭐⭐⭐  ║ ⭐⭐⭐⭐  ║ ⭐⭐⭐⭐ ║ ⭐⭐       ║
║ Latency          ║ 500-1000ms║ <500ms    ║ 500ms   ║ 1000-2000ms ║
║ Voices           ║ 100+      ║ 30+       ║ 6       ║ 10+         ║
║ Streaming        ║ ✅        ║ ❌        ║ ✅      ║ ✅          ║
║ Setup complexity ║ Easy      ║ Moderate  ║ Easy    ║ Very Easy   ║
║ Rate limits      ║ Generous  ║ TBD       ║ TBD     ║ Strict      ║
╚══════════════════╩═══════════╩═══════════╩═════════╩═════════════╝
```

### Audio Event Decision Tree

```
Event occurs
    │
    ├─ Is audio enabled globally?
    │  ├─ NO → Silent
    │  └─ YES → Continue
    │
    ├─ What event type?
    │  ├─ AskUserQuestion? → Check if enabled for event
    │  ├─ Tool completion? → Check if enabled for event
    │  ├─ Agent transition? → Check if enabled for event
    │  └─ Other? → Silent
    │
    ├─ Is event type enabled?
    │  ├─ NO → Silent
    │  └─ YES → Continue
    │
    ├─ Build announcement text
    │
    ├─ Synthesize speech
    │  ├─ Try ElevenLabs
    │  ├─ Fallback to Google Cloud
    │  ├─ Fallback to Edge TTS
    │  └─ Fallback to Silent
    │
    └─ Play audio asynchronously (non-blocking)
```

---

## 15. Next Steps for Implementation

1. **Review & Approval**
   - [ ] Get feedback from PopKit core team
   - [ ] Validate architecture with hook maintainers
   - [ ] Approve ElevenLabs as primary provider

2. **Create Implementation Tasks**
   - [ ] Create GitHub issues for v1.3.0 epic
   - [ ] Break into 2-3 week sprints
   - [ ] Assign developers

3. **Set Up Infrastructure**
   - [ ] Obtain ElevenLabs API key
   - [ ] Set up Google Cloud secondary provider
   - [ ] Configure testing environment

4. **Begin Development**
   - [ ] Start with `audio_synthesizer.py` (core logic)
   - [ ] Implement `audio_player.py` (cross-platform playback)
   - [ ] Create `audio-feedback.py` hook
   - [ ] Write comprehensive tests

5. **Beta Testing**
   - [ ] Release to internal PopKit users
   - [ ] Gather feedback on UX
   - [ ] Iterate on voice/announcement quality
   - [ ] Test on Mac/Linux/Windows

6. **General Release**
   - [ ] Release v1.3.0 with audio feedback MVP
   - [ ] Update documentation
   - [ ] Announce feature in release notes
   - [ ] Plan Phase 2 improvements

---

**Report Prepared For:** PopKit Main Agent
**Recommended Action:** Approve for v1.3.0 development cycle
**Questions/Feedback:** Reach out to PopKit core team

