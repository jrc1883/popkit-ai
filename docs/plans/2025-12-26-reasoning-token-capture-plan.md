# Reasoning & Token Capture Plan

**Date**: 2025-12-26
**Goal**: Capture Claude's reasoning process, token usage, and generate narrative reports
**Status**: Investigation & Design

## Problem Statement

Current session recording captures:
- ✅ Tool calls (start + complete)
- ✅ Tool parameters and results
- ✅ Sub-agent execution (via SubagentStop hook)
- ❌ Claude's reasoning before tool calls
- ❌ Token usage per tool call
- ❌ Narrative explanation of decision flow

**Why this matters:**
- Users want to understand WHY Claude made each decision
- Token usage is critical for cost tracking and optimization
- Narrative reports help non-technical stakeholders understand sessions

## Root Cause Analysis

### Why conversation_history is Empty

**Finding**: Hook `conversation_history` parameter is **always empty** for regular tool calls.

```python
# From hook test:
tool_name=Bash, conversation_history length=0
```

**Reason**: Claude Code's hook protocol doesn't provide full conversation history to PreToolUse hooks for performance/security reasons. Only certain hook events receive conversation context.

### What We Actually Receive

Hook stdin provides:
```json
{
  "session_id": "...",
  "transcript_path": "...",
  "cwd": "...",
  "permission_mode": "...",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {...},
  "tool_use_id": "..."
}
```

**Missing**:
- `conversation_history` (empty array)
- Token usage metadata
- Claude's reasoning text
- Extended thinking content (if -T flag used)

## Alternative Approaches

### Option 1: Transcript File Parsing (RECOMMENDED)

**How it works:**
1. Hooks receive `transcript_path` parameter
2. Parse JSONL transcript file for current session
3. Extract assistant messages, tool uses, and token metadata
4. Correlate with hook events by `tool_use_id`

**Pros:**
- ✅ Complete conversation history available
- ✅ Token usage in transcript metadata
- ✅ Extended thinking captured (if enabled)
- ✅ No API changes needed
- ✅ Works immediately

**Cons:**
- ⚠️ File I/O overhead (mitigated by reading only new lines)
- ⚠️ Parsing JSONL format
- ⚠️ Need to handle compaction events

**Implementation:**
```python
# In pre-tool-use.py
def get_recent_assistant_messages(transcript_path, tool_use_id):
    """Extract assistant reasoning before this tool call"""
    messages = []

    with open(transcript_path) as f:
        lines = f.readlines()

    # Parse JSONL backwards until we find this tool_use
    for line in reversed(lines):
        entry = json.loads(line)

        # Found our tool use - stop
        if entry.get('tool_use_id') == tool_use_id:
            break

        # Collect assistant messages
        if entry.get('type') == 'message' and entry.get('role') == 'assistant':
            for block in entry.get('content', []):
                if block.get('type') == 'text':
                    messages.insert(0, block.get('text'))
                elif block.get('type') == 'thinking':
                    # Extended thinking
                    messages.insert(0, f"[THINKING] {block.get('thinking')}")

    return messages

def get_token_usage(transcript_path, tool_use_id):
    """Extract token usage for this tool call"""
    # Token metadata is in message blocks
    # Parse and extract usage stats
    pass
```

**Example transcript entry:**
```json
{
  "type": "message",
  "role": "assistant",
  "content": [
    {"type": "text", "text": "I'll check git status first..."},
    {"type": "thinking", "thinking": "Need to see uncommitted changes..."},
    {"type": "tool_use", "id": "abc123", "name": "Bash", "input": {...}}
  ],
  "usage": {
    "input_tokens": 1234,
    "output_tokens": 567,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 890
  }
}
```

### Option 2: Post-Session Analysis

**How it works:**
1. Record only tool calls during session (current approach)
2. After session ends, run analysis script
3. Parse full transcript file
4. Generate narrative report with reasoning + tokens

**Pros:**
- ✅ Zero performance impact during session
- ✅ Can use AI to generate narrative
- ✅ More sophisticated analysis possible

**Cons:**
- ❌ Delayed insights (not real-time)
- ❌ Requires separate processing step

**Use case:**
- Weekly/monthly session reviews
- Cost analysis across multiple sessions
- Training data generation

### Option 3: Claude Code API Integration (FUTURE)

**How it works:**
1. Hook into Claude Code's streaming response handler
2. Capture responses before tool execution
3. Extract token metadata from API responses

**Pros:**
- ✅ Real-time token tracking
- ✅ Access to raw API responses
- ✅ No file parsing needed

**Cons:**
- ❌ Requires Claude Code plugin API extension
- ❌ Not currently available
- ❌ Maintenance burden

**Status**: Feature request for future Claude Code version

### Option 4: Hybrid Approach (BEST)

**Combine Option 1 + 2:**

1. **During session** (lightweight):
   - Record tool calls only (current)
   - Store `tool_use_id` for correlation

2. **On /popkit:record stop** (comprehensive):
   - Parse transcript file
   - Extract reasoning for each tool call
   - Calculate token usage
   - Generate narrative HTML report

**Benefits:**
- ✅ No performance impact during recording
- ✅ Complete data in final report
- ✅ Token usage analysis
- ✅ Narrative generation

## Proposed Implementation

### Phase 1: Transcript Parser (1-2 hours)

Create `packages/shared-py/popkit_shared/utils/transcript_parser.py`:

```python
class TranscriptParser:
    def __init__(self, transcript_path):
        self.transcript_path = Path(transcript_path)
        self.entries = []
        self._parse()

    def _parse(self):
        """Parse JSONL transcript file"""
        with open(self.transcript_path) as f:
            for line in f:
                self.entries.append(json.loads(line))

    def get_assistant_reasoning(self, tool_use_id):
        """Get reasoning before tool call"""
        reasoning = []
        found = False

        for entry in self.entries:
            if entry.get('type') == 'message' and entry.get('role') == 'assistant':
                for block in entry.get('content', []):
                    if block.get('type') == 'tool_use' and block.get('id') == tool_use_id:
                        found = True
                        break
                    elif block.get('type') == 'text':
                        reasoning.append(block['text'])
                    elif block.get('type') == 'thinking':
                        reasoning.append(f"[Extended Thinking]\n{block['thinking']}")

                if found:
                    break

        return '\n\n'.join(reasoning)

    def get_token_usage(self, tool_use_id):
        """Get token usage for tool call"""
        for entry in self.entries:
            if entry.get('type') == 'message':
                for block in entry.get('content', []):
                    if block.get('type') == 'tool_use' and block.get('id') == tool_use_id:
                        return entry.get('usage', {})
        return {}

    def get_total_tokens(self):
        """Calculate total session tokens"""
        total = {
            'input_tokens': 0,
            'output_tokens': 0,
            'cache_creation_input_tokens': 0,
            'cache_read_input_tokens': 0
        }

        for entry in self.entries:
            if entry.get('type') == 'message' and 'usage' in entry:
                for key in total:
                    total[key] += entry.get('usage', {}).get(key, 0)

        return total
```

### Phase 2: Enhanced Recording (30 min)

Update `session_recorder.py` to store `tool_use_id`:

```python
recorder.record_event({
    "type": "tool_call_start",
    "timestamp": datetime.now().isoformat(),
    "tool_name": tool_name,
    "tool_use_id": input_data.get("tool_use_id"),  # NEW
    "parameters": tool_args
})
```

### Phase 3: Report Enhancement (2 hours)

Update `html_report_generator_v9.py`:

1. **On report generation**, parse transcript file
2. **For each tool_call_start event**:
   - Look up reasoning by `tool_use_id`
   - Look up token usage
3. **Add new sections**:
   - "Claude's Reasoning" expandable for each tool
   - Token usage breakdown
   - Cost estimates (Sonnet 4.5 pricing)
4. **Generate narrative summary**:
   - Use AI (Claude via API) to create natural language explanation
   - "This session focused on fixing recording bugs. Claude first diagnosed..."

### Phase 4: Narrative Generation (3 hours)

Create `packages/shared-py/popkit_shared/utils/narrative_generator.py`:

```python
def generate_session_narrative(recording_file, transcript_file):
    """Generate natural language explanation of session"""

    # Load recording events
    with open(recording_file) as f:
        recording = json.load(f)

    # Parse transcript
    parser = TranscriptParser(transcript_file)

    # Build timeline with reasoning
    timeline = []
    for event in recording['events']:
        if event['type'] == 'tool_call_start':
            reasoning = parser.get_assistant_reasoning(event['tool_use_id'])
            tokens = parser.get_token_usage(event['tool_use_id'])

            timeline.append({
                'tool': event['tool_name'],
                'reasoning': reasoning,
                'tokens': tokens,
                'timestamp': event['timestamp']
            })

    # Generate narrative with AI
    prompt = f"""
    Generate a natural language narrative explaining this development session.

    Timeline:
    {json.dumps(timeline, indent=2)}

    Create a story that explains:
    1. What was the goal
    2. How Claude approached it (decision-making)
    3. What tools were used and why
    4. What was discovered/fixed
    5. Final outcome

    Use present tense. Be concise but insightful.
    """

    # Call Claude API
    narrative = call_claude_api(prompt)

    return narrative
```

### Phase 5: Cost Analysis (1 hour)

Add token cost calculator:

```python
# Pricing (Sonnet 4.5 as of Dec 2025)
PRICING = {
    'input_tokens': 3.00 / 1_000_000,      # $3 per million
    'output_tokens': 15.00 / 1_000_000,    # $15 per million
    'cache_write': 3.75 / 1_000_000,       # $3.75 per million
    'cache_read': 0.30 / 1_000_000         # $0.30 per million
}

def calculate_cost(token_usage):
    cost = 0
    cost += token_usage['input_tokens'] * PRICING['input_tokens']
    cost += token_usage['output_tokens'] * PRICING['output_tokens']
    cost += token_usage.get('cache_creation_input_tokens', 0) * PRICING['cache_write']
    cost += token_usage.get('cache_read_input_tokens', 0) * PRICING['cache_read']
    return cost
```

## Enhanced HTML Report Mockup

```html
<div class="session-summary">
  <h2>Session Narrative</h2>
  <div class="narrative">
    This session focused on fixing critical bugs in PopKit's session recording system.
    Claude first diagnosed the problem by examining the recording output, discovering
    that tool_call_start events were missing. Through systematic debugging, two root
    causes were identified: an incorrect import path and a duplicate json import.
    The fixes were committed and validated with a new recording session.
  </div>

  <h3>Token Usage & Cost</h3>
  <table>
    <tr>
      <td>Input tokens:</td>
      <td>95,000</td>
      <td>$0.285</td>
    </tr>
    <tr>
      <td>Output tokens:</td>
      <td>8,500</td>
      <td>$0.128</td>
    </tr>
    <tr>
      <td>Cache reads:</td>
      <td>45,000</td>
      <td>$0.014</td>
    </tr>
    <tr class="total">
      <td><strong>Total</strong></td>
      <td>148,500 tokens</td>
      <td><strong>$0.427</strong></td>
    </tr>
  </table>
</div>

<div class="event" id="event-5">
  <div class="event-header">
    <span class="event-type">TOOL_CALL_START</span>
    <span class="tool-name">Bash</span>
    <span class="timestamp">18:50:12</span>
  </div>

  <div class="reasoning" style="display:none">
    <h4>Claude's Reasoning</h4>
    <p>
      I need to test if the hook is now executing after fixing the import path.
      Running a simple echo command will trigger the pre-tool-use hook and allow
      us to verify the fix worked.
    </p>
    <details>
      <summary>Extended Thinking (click to expand)</summary>
      <pre>
The import path was going up 4 levels (parent.parent.parent.parent) when it
should only go up 3 levels. This is a classic off-by-one error. Let me trace
the path structure:
- pre-tool-use.py is in packages/popkit-core/hooks/
- shared-py is in packages/shared-py/
- So we need: hooks/ -> popkit-core/ -> packages/ -> shared-py/
That's 3 levels up, not 4.
      </pre>
    </details>
    <div class="tokens">
      <span>Input: 1,234 tokens</span>
      <span>Output: 89 tokens</span>
      <span>Cost: $0.005</span>
    </div>
  </div>

  <button onclick="toggleReasoning('event-5')">Show Reasoning</button>
</div>
```

## Timeline

| Phase | Effort | Priority | Deliverable |
|-------|--------|----------|-------------|
| Phase 1: Transcript Parser | 2h | P0 | Working parser with tests |
| Phase 2: Enhanced Recording | 30m | P0 | tool_use_id stored |
| Phase 3: Report Enhancement | 2h | P1 | Reasoning + tokens in HTML |
| Phase 4: Narrative Generation | 3h | P2 | AI-generated summary |
| Phase 5: Cost Analysis | 1h | P1 | Token cost calculator |

**Total**: ~8.5 hours of implementation

## Success Metrics

1. ✅ Every tool call shows Claude's reasoning
2. ✅ Token usage visible per tool and total
3. ✅ Cost estimates accurate (within 5%)
4. ✅ Narrative summary helps non-technical users understand sessions
5. ✅ No performance degradation during recording

## Next Steps

1. **Immediate** (today):
   - Validate transcript file format
   - Prototype parser for one tool call
   - Test token extraction

2. **Short-term** (this week):
   - Implement Phases 1-2
   - Create enhanced HTML report template
   - Add reasoning toggle UI

3. **Medium-term** (next week):
   - Implement narrative generation
   - Add cost analysis
   - Create user documentation

## Questions to Resolve

1. **Transcript file location**: Where is `transcript_path` pointing?
2. **JSONL format**: Confirm structure matches expected format
3. **Compaction events**: How to handle when transcript is summarized?
4. **API quota**: Do we have API key for narrative generation?
5. **Extended thinking**: Is `-T` flag commonly used? Should we highlight it?

## References

- Issue #603: SubagentStop recording (resolved)
- Session recording documentation: `packages/popkit-core/commands/record.md`
- Transcript parser will be similar to subagent transcript parsing
- Claude API pricing: https://www.anthropic.com/pricing
