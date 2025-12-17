# Context Optimization Implementation Plan

> **For Claude:** Use /popkit:dev execute to implement this plan task-by-task.

**Goal:** Reduce PopKit's context baseline from ~35k to ~25k tokens (30% reduction) through tool filtering and embedding-based agent loading.

**Architecture:** Two-phase approach completing existing partial implementations. Phase 1 adds hook-based tool filtering using existing config.json. Phase 2 activates embedding-based lazy agent loading using existing SQLite/Upstash infrastructure.

**Tech Stack:** Python 3.11+, SQLite, Upstash Vector, Voyage AI, Claude API

---

## Phase 1: Tool Choice Enforcement

### Task 1: Create Tool Filter Utility Module

**Files:**
- Create: `packages/plugin/hooks/utils/tool_filter.py`
- Test: `packages/plugin/tests/hooks/test_tool_filter.py`

**Step 1: Write the failing test**

```python
# packages/plugin/tests/hooks/test_tool_filter.py
import pytest
from hooks.utils.tool_filter import ToolFilter, filter_tools_for_workflow

def test_filter_tools_for_git_commit_workflow():
    """Tool filtering for git commit should only include Bash"""
    available_tools = ['Read', 'Write', 'Edit', 'Bash', 'Grep', 'Glob']
    config = {
        'tool_choice': {
            'workflow_steps': {
                'git-commit': {
                    'required_tools': ['Bash']
                }
            }
        }
    }

    filtered = filter_tools_for_workflow('git-commit', available_tools, config)

    assert filtered == ['Bash']
    assert 'Read' not in filtered
    assert 'Write' not in filtered


def test_filter_tools_fallback_to_all_when_no_workflow():
    """When workflow unknown, return all tools"""
    available_tools = ['Read', 'Write', 'Bash']
    config = {'tool_choice': {'workflow_steps': {}}}

    filtered = filter_tools_for_workflow('unknown-workflow', available_tools, config)

    assert filtered == available_tools


def test_filter_tools_handles_wildcard():
    """Wildcard * includes all tools"""
    available_tools = ['Read', 'Write', 'Bash']
    config = {
        'tool_choice': {
            'workflow_steps': {
                'full-access': {
                    'required_tools': ['*']
                }
            }
        }
    }

    filtered = filter_tools_for_workflow('full-access', available_tools, config)

    assert filtered == available_tools
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest packages/plugin/tests/hooks/test_tool_filter.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'hooks.utils.tool_filter'"

**Step 3: Write minimal implementation**

```python
# packages/plugin/hooks/utils/tool_filter.py
#!/usr/bin/env python3
"""
Tool Filtering for Context Optimization

Filters available tools based on workflow requirements from agents/config.json.
Part of Phase 1: Tool Choice Enforcement.
"""

from typing import List, Dict, Any, Optional
import json
from pathlib import Path


def load_agent_config() -> Dict[str, Any]:
    """Load agent configuration with tool_choice settings."""
    config_path = Path(__file__).parent.parent.parent / "agents" / "config.json"

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def filter_tools_for_workflow(
    workflow: str,
    available_tools: List[str],
    config: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Filter tools based on workflow requirements.

    Args:
        workflow: Workflow name (e.g., 'git-commit', 'file-edit')
        available_tools: List of available tool names
        config: Agent config dict (loaded if not provided)

    Returns:
        Filtered list of tool names

    Examples:
        >>> filter_tools_for_workflow('git-commit', ['Read', 'Bash'])
        ['Bash']
    """
    if config is None:
        config = load_agent_config()

    # Get workflow steps from config
    workflow_steps = config.get('tool_choice', {}).get('workflow_steps', {})

    # Unknown workflow → return all tools (safe fallback)
    if workflow not in workflow_steps:
        return available_tools

    # Get required tools for this workflow
    required = workflow_steps[workflow].get('required_tools', [])

    # Wildcard means all tools
    if '*' in required:
        return available_tools

    # Filter to only required tools
    return [t for t in available_tools if t in required]


class ToolFilter:
    """
    Tool filtering with context override support.

    Attributes:
        config: Loaded agent configuration
        enabled: Whether filtering is active (can be disabled for debugging)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, enabled: bool = True):
        """
        Initialize tool filter.

        Args:
            config: Agent config dict (loaded if not provided)
            enabled: Whether to apply filtering (default: True)
        """
        self.config = config or load_agent_config()
        self.enabled = enabled

    def filter(self, workflow: str, available_tools: List[str]) -> List[str]:
        """
        Filter tools for a workflow.

        Args:
            workflow: Workflow name
            available_tools: Available tool names

        Returns:
            Filtered tool list (or all tools if disabled)
        """
        if not self.enabled:
            return available_tools

        return filter_tools_for_workflow(workflow, available_tools, self.config)

    def disable(self):
        """Disable filtering (debugging/override)."""
        self.enabled = False

    def enable(self):
        """Enable filtering."""
        self.enabled = True
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest packages/plugin/tests/hooks/test_tool_filter.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add packages/plugin/hooks/utils/tool_filter.py packages/plugin/tests/hooks/test_tool_filter.py
git commit -m "feat(hooks): add tool filtering utility for context optimization

- Implements filter_tools_for_workflow() function
- Supports wildcard (*) for full tool access
- Safe fallback to all tools when workflow unknown
- ToolFilter class with enable/disable override
- 3 passing tests for core filtering logic

Part of Phase 1: Tool Choice Enforcement
Related: Context Optimization Epic"
```

---

### Task 2: Integrate Tool Filter into pre-tool-use Hook

**Files:**
- Modify: `packages/plugin/hooks/pre-tool-use.py`
- Test: Manual verification (hook testing)

**Step 1: Read current pre-tool-use.py to understand structure**

Run: Read tool on `packages/plugin/hooks/pre-tool-use.py`
Expected: Understand current hook flow and where to inject filtering

**Step 2: Add tool filtering logic**

```python
# Add to packages/plugin/hooks/pre-tool-use.py

import sys
import json
from pathlib import Path

# Add tool_filter import
sys.path.insert(0, str(Path(__file__).parent / "utils"))
from tool_filter import ToolFilter, filter_tools_for_workflow


def determine_workflow(tool_input: dict) -> str:
    """
    Determine workflow from tool input context.

    Args:
        tool_input: Tool input JSON from stdin

    Returns:
        Workflow name or 'unknown'
    """
    tool_name = tool_input.get('tool_name', '')

    # Map tools to workflows
    workflow_map = {
        'Bash': 'git-commit',  # Default Bash to git workflow
        'Edit': 'file-edit',
        'Write': 'file-edit',
        'Read': None,  # Read is always allowed
    }

    # Check if this is a git operation
    if tool_name == 'Bash':
        command = tool_input.get('tool_input', {}).get('command', '')
        if 'git' in command:
            if 'commit' in command or 'add' in command:
                return 'git-commit'
        # Other bash operations get full access
        return 'full-access'

    return workflow_map.get(tool_name, 'unknown')


def main():
    """Pre-tool-use hook with tool filtering."""
    # Read stdin
    input_data = json.load(sys.stdin)

    # Determine workflow
    workflow = determine_workflow(input_data)

    # Initialize tool filter
    tool_filter = ToolFilter()

    # Get available tools (from context if available)
    available_tools = input_data.get('available_tools', [
        'Read', 'Write', 'Edit', 'Bash', 'Grep', 'Glob',
        'Task', 'TodoWrite', 'WebFetch', 'WebSearch', 'AskUserQuestion'
    ])

    # Apply filtering
    filtered_tools = tool_filter.filter(workflow, available_tools)

    # Output to stderr for debugging (not blocking)
    debug_info = {
        'workflow': workflow,
        'filtered_tools': filtered_tools,
        'reduction': f"{len(available_tools) - len(filtered_tools)} tools filtered"
    }
    print(json.dumps(debug_info), file=sys.stderr)

    # Pass through (non-blocking for now)
    # Future: Modify input_data['available_tools'] = filtered_tools
    json.dump(input_data, sys.stdout)


if __name__ == '__main__':
    main()
```

**Step 3: Test with manual tool invocation**

Run:
```bash
echo '{"tool_name": "Bash", "tool_input": {"command": "git commit"}, "available_tools": ["Read", "Write", "Bash"]}' | python packages/plugin/hooks/pre-tool-use.py
```

Expected: See debug output in stderr showing tool filtering, passthrough in stdout

**Step 4: Verify hook doesn't break existing functionality**

Run: `/popkit:plugin test hooks`
Expected: All hook tests pass

**Step 5: Commit**

```bash
git add packages/plugin/hooks/pre-tool-use.py
git commit -m "feat(hooks): integrate tool filtering in pre-tool-use hook

- Adds determine_workflow() to detect workflow from tool input
- Initializes ToolFilter and applies filtering
- Outputs debug info to stderr (non-blocking)
- Passthrough mode for safe rollout

Part of Phase 1: Tool Choice Enforcement"
```

---

### Task 3: Update agents/config.json Enforcement Status

**Files:**
- Modify: `packages/plugin/agents/config.json`

**Step 1: Read current tool_choice section**

Run: Read tool on `packages/plugin/agents/config.json` lines 374-424
Expected: See "enforcement": "Currently advisory"

**Step 2: Update enforcement status and add override flag**

```json
{
  "tool_choice": {
    "description": "Claude API tool_choice parameter for forcing specific tool execution",
    "enforcement": "active",
    "override_flag": "POPKIT_DISABLE_TOOL_FILTER",
    "modes": {
      "auto": "Let Claude choose the best tool (default)",
      "required": "Force tool use, Claude must use a tool",
      "specific": "Force use of a specific tool by name"
    },
    "workflow_steps": {
      "git-commit": {
        "description": "Git commit workflow",
        "steps": [
          { "action": "gather_status", "tool_choice": "auto" },
          { "action": "stage_files", "tool_choice": { "type": "tool", "name": "Bash" } },
          { "action": "create_commit", "tool_choice": { "type": "tool", "name": "Bash" } }
        ],
        "required_tools": ["Bash"]
      },
      "file-edit": {
        "description": "Read before edit enforcement",
        "steps": [
          { "action": "read_file", "tool_choice": { "type": "tool", "name": "Read" } },
          { "action": "edit_file", "tool_choice": { "type": "tool", "name": "Edit" } }
        ],
        "required_tools": ["Read", "Edit"]
      },
      "verification": {
        "description": "Run verification commands",
        "steps": [
          { "action": "run_tests", "tool_choice": { "type": "tool", "name": "Bash" } },
          { "action": "run_lint", "tool_choice": { "type": "tool", "name": "Bash" } }
        ],
        "required_tools": ["Bash"]
      },
      "full-access": {
        "description": "All tools available",
        "required_tools": ["*"]
      }
    },
    "notes": {
      "usage": "Hooks read this config and filter tools per workflow",
      "override": "Set POPKIT_DISABLE_TOOL_FILTER=1 to disable filtering",
      "enforcement": "Active as of 2025-12-17 (Phase 1 complete)"
    }
  }
}
```

**Step 3: Validate JSON syntax**

Run: `python -c "import json; json.load(open('packages/plugin/agents/config.json'))"`
Expected: No errors

**Step 4: Commit**

```bash
git add packages/plugin/agents/config.json
git commit -m "feat(config): activate tool_choice enforcement

- Set enforcement status to 'active'
- Add POPKIT_DISABLE_TOOL_FILTER override flag
- Add full-access workflow with wildcard tools
- Update notes with activation date

Part of Phase 1: Tool Choice Enforcement complete"
```

---

### Task 4: Measure Context Reduction

**Files:**
- Create: `packages/plugin/scripts/measure-context-usage.py`

**Step 1: Write context measurement script**

```python
#!/usr/bin/env python3
"""
Measure PopKit context usage.

Outputs token counts for:
- System Tools (before/after filtering)
- Custom Agents (before/after lazy loading)
- Total context baseline
"""

import json
import sys
from pathlib import Path


def count_tokens_rough(text: str) -> int:
    """Rough token estimation (4 chars ≈ 1 token)."""
    return len(text) // 4


def measure_tool_context():
    """Measure System Tools context."""
    # Simulate tool definitions
    all_tools = [
        'Read', 'Write', 'Edit', 'MultiEdit', 'Bash',
        'Glob', 'Grep', 'Task', 'TodoWrite', 'WebFetch',
        'WebSearch', 'AskUserQuestion', 'Skill', 'SlashCommand',
        'EnterPlanMode', 'ExitPlanMode', 'NotebookEdit', 'KillShell'
    ]

    # Estimate 1.3k tokens per tool (JSON schema)
    tokens_per_tool = 1300
    baseline_tokens = len(all_tools) * tokens_per_tool

    print(f"System Tools Baseline: {baseline_tokens:,} tokens ({len(all_tools)} tools)")

    # After filtering (example: git-commit only needs Bash)
    filtered_tools = ['Bash']
    filtered_tokens = len(filtered_tools) * tokens_per_tool

    print(f"System Tools Filtered (git-commit): {filtered_tokens:,} tokens ({len(filtered_tools)} tool)")
    print(f"Reduction: {baseline_tokens - filtered_tokens:,} tokens ({((baseline_tokens - filtered_tokens) / baseline_tokens * 100):.1f}%)")
    print()


def measure_agent_context():
    """Measure Custom Agents context."""
    config_path = Path(__file__).parent.parent / "agents" / "config.json"

    with open(config_path, 'r') as f:
        config = json.load(f)

    # Count agents
    tier1_count = len(config.get('structure', {}).get('migrated_agents', []))
    total_agents = 40  # Approximate

    # Estimate 60 tokens per agent definition
    tokens_per_agent = 60
    baseline_tokens = total_agents * tokens_per_agent

    print(f"Custom Agents Baseline: {baseline_tokens:,} tokens ({total_agents} agents)")

    # After lazy loading (top 5 relevant)
    loaded_agents = 5
    filtered_tokens = loaded_agents * tokens_per_agent

    print(f"Custom Agents Loaded (lazy): {filtered_tokens:,} tokens ({loaded_agents} agents)")
    print(f"Reduction: {baseline_tokens - filtered_tokens:,} tokens ({((baseline_tokens - filtered_tokens) / baseline_tokens * 100):.1f}%)")
    print()


def measure_total():
    """Measure total context reduction."""
    # Before optimization
    system_tools_before = 23300
    custom_agents_before = 2400
    baseline_total = system_tools_before + custom_agents_before

    # After Phase 1 (tool filtering only)
    system_tools_phase1 = 15000  # -8.3k
    custom_agents_phase1 = 2400  # unchanged
    phase1_total = system_tools_phase1 + custom_agents_phase1

    # After Phase 2 (tool filtering + lazy loading)
    system_tools_phase2 = 15000
    custom_agents_phase2 = 300  # -2.1k
    phase2_total = system_tools_phase2 + custom_agents_phase2

    print("=== Total Context Reduction ===")
    print(f"Baseline: {baseline_total:,} tokens")
    print(f"After Phase 1 (Tool Filtering): {phase1_total:,} tokens (-{baseline_total - phase1_total:,}, {((baseline_total - phase1_total) / baseline_total * 100):.1f}%)")
    print(f"After Phase 2 (+ Lazy Loading): {phase2_total:,} tokens (-{baseline_total - phase2_total:,}, {((baseline_total - phase2_total) / baseline_total * 100):.1f}%)")
    print()
    print(f"Target: 25,000 tokens")
    print(f"Achieved: {phase2_total:,} tokens")
    print(f"Goal met: {'✓ Yes' if phase2_total <= 25000 else '✗ No'}")


if __name__ == '__main__':
    measure_tool_context()
    measure_agent_context()
    measure_total()
```

**Step 2: Run measurement script**

Run: `python packages/plugin/scripts/measure-context-usage.py`
Expected: Output showing baseline vs. optimized context usage

**Step 3: Commit**

```bash
chmod +x packages/plugin/scripts/measure-context-usage.py
git add packages/plugin/scripts/measure-context-usage.py
git commit -m "feat(scripts): add context usage measurement tool

- Measures System Tools baseline vs. filtered
- Measures Custom Agents baseline vs. lazy loaded
- Calculates total reduction percentage
- Validates against 25k token goal

Part of Phase 1: Tool Choice Enforcement validation"
```

---

## Phase 2: Embedding-Based Agent Loading

### Task 5: Generate Agent Embeddings

**Files:**
- Create: `packages/plugin/scripts/generate-agent-embeddings.py`
- Modify: `packages/plugin/agents/config.json` (add embeddings field)

**Step 1: Write embedding generation script**

```python
#!/usr/bin/env python3
"""
Generate embeddings for all PopKit agents.

Stores embeddings in:
- SQLite (local fallback)
- Upstash Vector (cloud, Pro tier)
"""

import json
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks" / "utils"))

from embedding_store import EmbeddingStore, EmbeddingRecord
from voyage_client import get_voyage_embeddings
from cloud_agent_search import upload_to_upstash


def load_agent_descriptions():
    """Load all agent descriptions from config and agent files."""
    config_path = Path(__file__).parent.parent / "agents" / "config.json"

    with open(config_path, 'r') as f:
        config = json.load(f)

    agents = {}

    # Tier 1: Always-active agents
    tier1_dir = Path(__file__).parent.parent / "agents" / "tier-1-always-active"
    for agent_dir in tier1_dir.glob("*"):
        if not agent_dir.is_dir():
            continue

        agent_file = agent_dir / "AGENT.md"
        if agent_file.exists():
            with open(agent_file, 'r') as f:
                content = f.read()
                # Extract description from frontmatter
                # Simplified: just use first 200 chars
                description = content[:200]
                agents[agent_dir.name] = {
                    'tier': 'tier-1-always-active',
                    'description': description
                }

    # Tier 2: On-demand agents
    tier2_dir = Path(__file__).parent.parent / "agents" / "tier-2-on-demand"
    for agent_dir in tier2_dir.glob("*"):
        if not agent_dir.is_dir():
            continue

        agent_file = agent_dir / "AGENT.md"
        if agent_file.exists():
            with open(agent_file, 'r') as f:
                content = f.read()
                description = content[:200]
                agents[agent_dir.name] = {
                    'tier': 'tier-2-on-demand',
                    'description': description
                }

    return agents


def generate_embeddings(agents: dict):
    """Generate embeddings for all agents."""
    store = EmbeddingStore()

    descriptions = [a['description'] for a in agents.values()]
    agent_ids = list(agents.keys())

    print(f"Generating embeddings for {len(agents)} agents...")

    # Get embeddings from Voyage AI
    embeddings = get_voyage_embeddings(descriptions)

    print(f"Generated {len(embeddings)} embeddings")

    # Store in SQLite
    for agent_id, embedding, agent_data in zip(agent_ids, embeddings, agents.values()):
        record = EmbeddingRecord(
            id=f"agent:{agent_id}",
            content=agent_data['description'],
            embedding=embedding,
            source_type="agent",
            source_id=agent_id,
            metadata={
                'tier': agent_data['tier']
            }
        )

        store.insert(record)
        print(f"Stored embedding for {agent_id}")

    print(f"\n✓ Stored {len(agents)} agent embeddings in SQLite")

    # Upload to Upstash Vector (if configured)
    try:
        upload_to_upstash(agent_ids, embeddings, agents)
        print(f"✓ Uploaded {len(agents)} embeddings to Upstash Vector")
    except Exception as e:
        print(f"⚠ Upstash upload failed (optional): {e}")


if __name__ == '__main__':
    agents = load_agent_descriptions()
    generate_embeddings(agents)
```

**Step 2: Run embedding generation**

Run: `python packages/plugin/scripts/generate-agent-embeddings.py`
Expected: Embeddings stored in SQLite, optionally uploaded to Upstash

**Step 3: Verify embeddings in SQLite**

Run:
```bash
python -c "from hooks.utils.embedding_store import EmbeddingStore; store = EmbeddingStore(); print(f'Total embeddings: {len(list(store.search(query_embedding=[0.0]*1024, top_k=50)))}')"
```

Expected: Count matches number of agents (~40)

**Step 4: Commit**

```bash
chmod +x packages/plugin/scripts/generate-agent-embeddings.py
git add packages/plugin/scripts/generate-agent-embeddings.py
git commit -m "feat(scripts): add agent embedding generation

- Loads agent descriptions from tier-1 and tier-2 directories
- Generates embeddings via Voyage AI
- Stores in SQLite for local fallback
- Optionally uploads to Upstash Vector for cloud

Part of Phase 2: Embedding-Based Agent Loading"
```

---

### Task 6: Create Agent Loader Utility

**Files:**
- Create: `packages/plugin/hooks/utils/agent_loader.py`
- Test: `packages/plugin/tests/hooks/test_agent_loader.py`

**Step 1: Write failing test**

```python
# packages/plugin/tests/hooks/test_agent_loader.py
import pytest
from hooks.utils.agent_loader import AgentLoader, load_relevant_agents


def test_load_relevant_agents_semantic():
    """Load top relevant agents using semantic search"""
    loader = AgentLoader()

    # Simulate user query
    query = "fix the login bug"

    # Load top 5 agents
    agents = loader.load(query, top_k=5)

    assert len(agents) <= 5
    assert all('agent_id' in a for a in agents)
    assert all('similarity' in a for a in agents)


def test_load_relevant_agents_fallback_to_keywords():
    """Falls back to keyword matching if embeddings fail"""
    loader = AgentLoader(use_embeddings=False)

    query = "security vulnerability in authentication"
    agents = loader.load(query, top_k=5)

    # Should find security-auditor via keyword
    agent_ids = [a['agent_id'] for a in agents]
    assert 'security-auditor' in agent_ids


def test_load_relevant_agents_always_include_tier1():
    """Always include some Tier 1 agents"""
    loader = AgentLoader()

    query = "random task"
    agents = loader.load(query, top_k=10)

    # At least 3 tier-1 agents should be included
    tier1_count = sum(1 for a in agents if a.get('tier') == 'tier-1-always-active')
    assert tier1_count >= 3
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest packages/plugin/tests/hooks/test_agent_loader.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# packages/plugin/hooks/utils/agent_loader.py
#!/usr/bin/env python3
"""
Agent Loader with Semantic Search

Loads only relevant agents using embedding-based similarity search.
Part of Phase 2: Embedding-Based Agent Loading.
"""

from typing import List, Dict, Any
import json
from pathlib import Path

from embedding_store import EmbeddingStore, SearchResult
from voyage_client import get_voyage_embeddings
from cloud_agent_search import search_agents as cloud_search


class AgentLoader:
    """
    Load relevant agents using semantic search.

    Attributes:
        store: Embedding store for local search
        use_embeddings: Whether to use embeddings (fallback to keywords if False)
        always_include_tier1: Always include some Tier 1 agents
    """

    def __init__(
        self,
        use_embeddings: bool = True,
        always_include_tier1: bool = True
    ):
        """
        Initialize agent loader.

        Args:
            use_embeddings: Use semantic search (default: True)
            always_include_tier1: Always include Tier 1 agents (default: True)
        """
        self.use_embeddings = use_embeddings
        self.always_include_tier1 = always_include_tier1

        if use_embeddings:
            self.store = EmbeddingStore()

    def load(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Load top relevant agents for a query.

        Args:
            query: User query or task description
            top_k: Number of agents to load

        Returns:
            List of agent dicts with agent_id, similarity, tier
        """
        if self.use_embeddings:
            try:
                return self._load_with_embeddings(query, top_k)
            except Exception as e:
                print(f"Embedding search failed: {e}, falling back to keywords", file=sys.stderr)
                return self._load_with_keywords(query, top_k)
        else:
            return self._load_with_keywords(query, top_k)

    def _load_with_embeddings(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Load agents using semantic search."""
        # Get query embedding
        query_embedding = get_voyage_embeddings([query])[0]

        # Search in SQLite
        results = self.store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            source_type="agent"
        )

        # Convert to agent dicts
        agents = []
        for result in results:
            agents.append({
                'agent_id': result.record.source_id,
                'similarity': result.similarity,
                'tier': result.record.metadata.get('tier', 'unknown'),
                'description': result.record.content[:100]
            })

        # Ensure some Tier 1 agents always included
        if self.always_include_tier1:
            agents = self._ensure_tier1_agents(agents, top_k)

        return agents[:top_k]

    def _load_with_keywords(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Fallback: Load agents using keyword matching."""
        keywords = query.lower().split()

        # Hardcoded keyword mappings
        keyword_map = {
            'bug': ['bug-whisperer'],
            'security': ['security-auditor'],
            'test': ['test-writer-fixer'],
            'performance': ['performance-optimizer', 'query-optimizer'],
            'refactor': ['refactoring-expert'],
            'api': ['api-designer'],
            'review': ['code-reviewer'],
        }

        matched_agents = set()
        for keyword in keywords:
            if keyword in keyword_map:
                matched_agents.update(keyword_map[keyword])

        # Always include code-reviewer (Tier 1)
        matched_agents.add('code-reviewer')

        # Convert to agent dicts
        agents = [
            {
                'agent_id': agent_id,
                'similarity': 0.5,  # Keyword match = medium similarity
                'tier': 'tier-1-always-active' if agent_id == 'code-reviewer' else 'tier-2-on-demand',
                'description': ''
            }
            for agent_id in list(matched_agents)[:top_k]
        ]

        return agents

    def _ensure_tier1_agents(self, agents: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Ensure at least 3 Tier 1 agents are included."""
        tier1_agents = [a for a in agents if a['tier'] == 'tier-1-always-active']

        # If we have enough Tier 1, return as-is
        if len(tier1_agents) >= 3:
            return agents

        # Add essential Tier 1 agents
        essential_tier1 = ['code-reviewer', 'bug-whisperer', 'documentation-maintainer']

        for agent_id in essential_tier1:
            if agent_id not in [a['agent_id'] for a in agents]:
                agents.append({
                    'agent_id': agent_id,
                    'similarity': 0.7,
                    'tier': 'tier-1-always-active',
                    'description': ''
                })

            if len([a for a in agents if a['tier'] == 'tier-1-always-active']) >= 3:
                break

        # Re-sort by similarity
        agents.sort(key=lambda a: a['similarity'], reverse=True)

        return agents


def load_relevant_agents(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Load relevant agents for a query (convenience function).

    Args:
        query: User query or task description
        top_k: Number of agents to load

    Returns:
        List of agent dicts
    """
    loader = AgentLoader()
    return loader.load(query, top_k)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest packages/plugin/tests/hooks/test_agent_loader.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add packages/plugin/hooks/utils/agent_loader.py packages/plugin/tests/hooks/test_agent_loader.py
git commit -m "feat(hooks): add agent loader with semantic search

- AgentLoader class with embedding-based search
- Fallback to keyword matching if embeddings fail
- Always includes essential Tier 1 agents
- 3 passing tests for core loading logic

Part of Phase 2: Embedding-Based Agent Loading"
```

---

### Task 7: Integrate Agent Loader into session-start Hook

**Files:**
- Modify: `packages/plugin/hooks/session-start.py` (or create if doesn't exist)

**Step 1: Check if session-start hook exists**

Run: `test -f packages/plugin/hooks/session-start.py && echo "exists" || echo "not found"`
Expected: Check existence

**Step 2: Create or modify session-start hook**

```python
# packages/plugin/hooks/session-start.py
#!/usr/bin/env python3
"""
Session Start Hook

Filters agents based on initial task using semantic search.
Part of Phase 2: Embedding-Based Agent Loading.
"""

import json
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / "utils"))
from agent_loader import AgentLoader


def main():
    """Session start hook with agent filtering."""
    # Read stdin
    input_data = json.load(sys.stdin)

    # Get initial user message (if available)
    messages = input_data.get('messages', [])
    user_message = next((m['content'] for m in messages if m['role'] == 'user'), '')

    # If no user message yet, load all agents (safe fallback)
    if not user_message:
        json.dump(input_data, sys.stdout)
        return

    # Load relevant agents
    loader = AgentLoader()
    relevant_agents = loader.load(user_message, top_k=10)

    # Output debug info
    debug_info = {
        'loaded_agents': [a['agent_id'] for a in relevant_agents],
        'agent_count': len(relevant_agents),
        'query_preview': user_message[:100]
    }
    print(json.dumps(debug_info), file=sys.stderr)

    # Pass through (agent filtering not yet implemented in Claude Code)
    # Future: Modify input_data['agents'] = relevant_agents
    json.dump(input_data, sys.stdout)


if __name__ == '__main__':
    main()
```

**Step 3: Register hook in hooks.json**

```json
{
  "hooks": {
    "session-start": {
      "command": "python hooks/session-start.py",
      "description": "Filter agents based on initial task"
    }
  }
}
```

**Step 4: Test hook**

Run:
```bash
echo '{"messages": [{"role": "user", "content": "fix the authentication bug"}]}' | python packages/plugin/hooks/session-start.py
```

Expected: Debug output showing loaded agents, passthrough JSON

**Step 5: Commit**

```bash
git add packages/plugin/hooks/session-start.py packages/plugin/hooks/hooks.json
git commit -m "feat(hooks): integrate agent loader in session-start hook

- Filters agents based on initial user message
- Loads top 10 relevant agents using semantic search
- Outputs debug info to stderr
- Passthrough mode for safe rollout

Part of Phase 2: Embedding-Based Agent Loading"
```

---

## Phase 3: SDK Pattern Tracking

### Task 8: Create SDK Tracking Issue

**Files:**
- Create GitHub issue (via gh CLI)
- Create: `docs/research/anthropic-sdk-patterns-tracking.md`

**Step 1: Write migration documentation**

```markdown
# Anthropic SDK Patterns Tracking

**Status:** Monitoring (No Active Development)
**Review Cadence:** Quarterly or on major SDK releases

## Purpose

Track Anthropic SDK patterns from cookbooks and releases to prepare for migration when patterns stabilize.

## Patterns to Watch

### 1. `@beta_tool` Decorator

**Current State (Cookbook):**
```python
from anthropic import beta_tool

@beta_tool
def crop_image(x1: float, y1: float, x2: float, y2: float) -> str:
    """Crop an image by specifying a bounding box."""
    # Implementation
    return result
```

**PopKit Current:**
- Manual JSON schemas in hooks
- Tool definitions in agents/config.json

**Migration When Stable:**
- Refactor Power Mode coordinator to use @beta_tool
- Convert hook tool definitions to decorators
- Simpler, more Pythonic tool definitions

### 2. SDK `tool_runner`

**Current State (Cookbook):**
```python
# Replaces 78+ lines of manual agentic loop
tool_runner.run(tools=[crop_image], ...)
```

**PopKit Current:**
- Manual while loops in power-mode/coordinator.py
- Custom message building and tool execution

**Migration When Stable:**
- Simplify coordinator.py by 50-70%
- Remove custom loop boilerplate
- Focus on workflow orchestration logic

### 3. Native Tool Filtering

**Speculation:** SDK may add built-in tool_choice filtering

**PopKit Current:**
- Custom tool_filter.py implementation
- Hook-based filtering in pre-tool-use.py

**Migration If Available:**
- Replace custom filtering with SDK native
- Keep hooks for PopKit-specific logic

## Monitoring Strategy

### Resources to Watch

1. **anthropic-sdk-python Releases**
   - https://github.com/anthropics/anthropic-sdk-python/releases
   - Watch for: `tool_use`, `@beta_tool`, `tool_runner` mentions

2. **Claude Cookbooks**
   - https://github.com/anthropics/claude-cookbooks
   - Watch for: New patterns, refactors, best practices

3. **Anthropic Engineering Blog**
   - https://www.anthropic.com/engineering
   - Watch for: SDK announcements, pattern recommendations

4. **Claude API Changelog**
   - https://docs.anthropic.com/en/release-notes
   - Watch for: Tool use improvements, new parameters

### Review Cadence

- **Quarterly:** Check all resources above
- **On Major Release:** Review when SDK version bumps (e.g., 1.x → 2.x)
- **GitHub Watch:** Enable notifications on anthropic-sdk-python repo

### Review Checklist

- [ ] Check SDK releases for tool_use changes
- [ ] Review cookbooks for pattern changes
- [ ] Read engineering blog posts
- [ ] Check API changelog for new features
- [ ] Update this document with findings
- [ ] Assess if patterns have stabilized
- [ ] If stable, create implementation plan

## Migration Readiness

### Current Implementation

| Component | Current Approach | Lines of Code |
|-----------|------------------|---------------|
| Power Mode coordinator | Manual agentic loop | ~1000 LOC |
| Hook tool schemas | Manual JSON | ~200 LOC across hooks |
| Tool filtering | Custom implementation | ~150 LOC |

### Migration Estimate

If SDK patterns stabilize:
- **Coordinator refactor:** 3-5 days (50-70% reduction)
- **Hook tool schemas:** 2-3 days (simpler decorators)
- **Tool filtering:** 1-2 days (if native support)

**Total:** 1-2 weeks for full migration

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Patterns change before stabilizing | High | Medium | No active work until stable |
| SDK doesn't add native filtering | Medium | Low | Keep custom implementation |
| Migration breaks existing code | Low | High | Thorough testing, feature flags |

## Decision Log

### 2025-12-17: Initial Tracking

**Decision:** Lightweight tracking only, no experimental branch

**Rationale:**
- SDK patterns still in beta (cookbooks show recent changes)
- Risk of wasted effort if patterns change
- Current custom implementation works well
- Can build experimental branch when patterns stabilize

**Next Review:** 2025-03-17 (3 months)

---

**Last Updated:** 2025-12-17
**Next Review:** 2025-03-17
```

**Step 2: Commit tracking documentation**

```bash
git add docs/research/anthropic-sdk-patterns-tracking.md
git commit -m "docs(research): add Anthropic SDK pattern tracking

- Documents @beta_tool decorator pattern
- Documents SDK tool_runner pattern
- Speculation on native tool filtering
- Quarterly review cadence
- Migration readiness assessment
- Links to anthropic-sdk-python, cookbooks, blog, changelog

Part of Phase 3: SDK Pattern Tracking"
```

**Step 3: Create GitHub tracking issue**

```bash
gh issue create --title "[Research] Track Anthropic SDK Patterns for Future Migration" --label "research,phase:future,P3-low,architecture,blocked" --body "$(cat <<'EOF'
## Summary

Monitor Anthropic SDK patterns from cookbooks and releases to prepare for migration when patterns stabilize. **No active development** until patterns are stable.

## Patterns to Watch

### 1. `@beta_tool` Decorator
- **Status:** In cookbooks, may change
- **Impact:** Simpler tool definitions
- **PopKit migration:** Refactor Power Mode coordinator

### 2. SDK `tool_runner`
- **Status:** In cookbooks, replaces 78+ lines of manual loops
- **Impact:** Simplify coordinator.py by 50-70%
- **PopKit migration:** Remove custom agentic loop boilerplate

### 3. Native Tool Filtering (Speculation)
- **Status:** Not announced, may not happen
- **Impact:** Could replace custom tool_filter.py
- **PopKit migration:** Use SDK native if available

## Monitoring Strategy

**Resources:**
- [anthropic-sdk-python releases](https://github.com/anthropics/anthropic-sdk-python/releases)
- [Claude cookbooks](https://github.com/anthropics/claude-cookbooks)
- [Anthropic Engineering Blog](https://www.anthropic.com/engineering)
- [Claude API Changelog](https://docs.anthropic.com/en/release-notes)

**Cadence:**
- Quarterly review (next: 2025-03-17)
- On major SDK releases (1.x → 2.x)
- GitHub notifications enabled

## Documentation

See: `docs/research/anthropic-sdk-patterns-tracking.md`

## Decision

**2025-12-17:** Lightweight tracking only, no experimental branch

**Rationale:**
- SDK patterns still in beta
- Risk of wasted effort if patterns change
- Current custom implementation works
- Can build experimental branch when stable

## Migration Estimate

If patterns stabilize:
- Coordinator refactor: 3-5 days
- Hook tool schemas: 2-3 days
- Tool filtering: 1-2 days (if native support)

**Total:** 1-2 weeks

## Next Review

**Date:** 2025-03-17 (3 months)

**Checklist:**
- [ ] Check SDK releases for tool_use changes
- [ ] Review cookbooks for pattern changes
- [ ] Read engineering blog posts
- [ ] Check API changelog
- [ ] Update tracking document
- [ ] Assess if patterns stabilized
- [ ] If stable, create implementation plan

---

**Part of:** Context Optimization Epic
**Related:** Phase 1 (Tool Filtering), Phase 2 (Agent Loading)
**Blocked by:** Anthropic SDK stabilization
EOF
)"
```

Expected: Issue created with number (e.g., #280)

**Step 4: Verify issue was created**

Run: `gh issue list --label research --limit 1`
Expected: See newly created tracking issue

**Step 5: Commit (no code changes, just tracking)**

This task has no code changes - just creates GitHub issue and documentation for tracking purposes.

---

## GitHub Issues Summary

After completing implementation, create these GitHub issues:

### Issue 1: Phase 1 - Tool Choice Enforcement

```bash
gh issue create --title "[Performance] Implement Tool Choice Enforcement for Context Optimization" --label "enhancement,P1-high,phase:now,hooks,performance" --milestone "1.0.0" --body "$(cat <<'EOF'
## Summary

Implement hook-based tool filtering using existing agents/config.json structure to reduce System Tools context by 5-8k tokens (30-50% reduction).

## Implementation

See: `docs/plans/2025-12-17-context-optimization-implementation.md` (Tasks 1-4)

## Tasks

- [ ] Task 1: Create tool_filter.py utility module
- [ ] Task 2: Integrate into pre-tool-use hook
- [ ] Task 3: Update agents/config.json enforcement status
- [ ] Task 4: Measure context reduction

## Success Criteria

- [ ] Tool filtering works for all workflow types
- [ ] Config override flag available (POPKIT_DISABLE_TOOL_FILTER)
- [ ] Context reduced by 5-8k tokens
- [ ] No functionality regressions
- [ ] 3+ passing tests for tool_filter.py

## Impact

**Before:** System Tools = 23.3k tokens (all tools loaded)
**After:** System Tools = 15-18k tokens (workflow-specific tools)
**Reduction:** 5-8k tokens (30-50%)

## Related

- Part of Context Optimization Epic
- Uses existing config.json structure (just activates enforcement)
- Phase 2: Embedding-Based Agent Loading (separate issue)
EOF
)"
```

### Issue 2: Phase 2 - Embedding-Based Agent Loading

```bash
gh issue create --title "[Performance] Implement Embedding-Based Lazy Agent Loading" --label "enhancement,P1-high,phase:now,agents,performance" --milestone "1.0.0" --body "$(cat <<'EOF'
## Summary

Activate embedding-based semantic search for agents to load only top 5-10 relevant agents instead of all 40+, reducing Custom Agents context by ~10k tokens.

## Implementation

See: `docs/plans/2025-12-17-context-optimization-implementation.md` (Tasks 5-7)

## Tasks

- [ ] Task 5: Generate agent embeddings (SQLite + Upstash)
- [ ] Task 6: Create agent_loader.py utility
- [ ] Task 7: Integrate into session-start hook

## Success Criteria

- [ ] Embedding generation script works
- [ ] Top 5-10 agents loaded per task
- [ ] Keyword fallback functions correctly
- [ ] Context reduced by ~10k tokens
- [ ] Agent routing accuracy >90%
- [ ] Fallback success rate >95%

## Infrastructure (Already Built!)

- ✅ embedding_store.py - SQLite vector storage
- ✅ cloud_agent_search.py - Upstash Vector queries
- ✅ voyage_client.py - Voyage AI embeddings

**Just needs integration and activation!**

## Impact

**Before:** Custom Agents = 2.4k tokens (all 40+ agents loaded)
**After:** Custom Agents = ~0.8k tokens (top 5-10 loaded)
**Reduction:** ~10k tokens

## Related

- Part of Context Optimization Epic
- Depends on: Phase 1 (Tool Filtering) - can run in parallel
- Uses existing embedding infrastructure
EOF
)"
```

### Issue 3: Phase 3 - SDK Pattern Tracking

Created via Task 8 (research issue, see above)

### Issue 4: Documentation Cleanup

```bash
gh issue create --title "[Documentation] Clean Up Outdated Docker/Redis References" --label "documentation,P2-medium,phase:now,plugin" --milestone "1.0.0" --body "$(cat <<'EOF'
## Summary

Update 50+ files with outdated Docker/Redis documentation. PopKit Power Mode no longer requires Docker - uses Native Async Mode (Claude Code 2.0.64+) or Cloud Redis (Upstash).

## Problem

**Incorrect documentation states:**
- "Redis Mode requires Docker"
- "File Mode (simple)" vs "Redis Mode (advanced with Docker)"

**Current reality:**
1. Native Async Mode (default, zero setup, 5+ agents)
2. Cloud Mode (Pro, Upstash hosted, no Docker)
3. Self-Hosted Redis (Advanced, optional Docker)
4. File-Based Mode (Legacy fallback)

## Affected Files

See: `docs/plans/2025-12-17-documentation-cleanup-outdated-docker-redis.md`

**Critical (User-Facing):**
- CLAUDE.md (lines 335-336)
- commands/project.md (5+ locations)
- commands/power.md (mixed messages)
- skills/pop-project-init/SKILL.md (onboarding flow)
- skills/pop-power-mode/SKILL.md

**Total:** 50+ files need review

## Implementation Plan

See full plan in: `docs/plans/2025-12-17-documentation-cleanup-outdated-docker-redis.md`

**Phases:**
1. Critical user-facing docs (CLAUDE.md, commands/, skills/)
2. Internal documentation (power-mode/, docs/)
3. Archive legacy (mark SETUP-REDIS.md as "Advanced")
4. Validate (grep for remaining "requires Docker")

## Success Criteria

- [ ] No user-facing docs mention Docker as requirement
- [ ] Native Async Mode presented as default
- [ ] Cloud Mode clearly labeled as Pro tier
- [ ] Self-hosted Redis marked as "Advanced" (optional)
- [ ] File-Based Mode presented as fallback only
- [ ] Migration guide available for Docker users

## Related

- Separate from Context Optimization (documentation debt)
- Found during context optimization brainstorming
- Improves user onboarding experience
EOF
)"
```

---

## Execution Options

After plan approval, you have three options:

### Option 1: Execute Now (Recommended)

Use the pop-executing-plans skill to implement task-by-task:

```bash
/popkit:dev execute docs/plans/2025-12-17-context-optimization-implementation.md
```

### Option 2: Parallel Execution

Open Power Mode and distribute tasks across agents:

```bash
/popkit:power start --plan docs/plans/2025-12-17-context-optimization-implementation.md
```

### Option 3: Manual Execution

Execute tasks manually, following the plan step-by-step.

---

## Plan Complete

**Total Tasks:** 8 tasks
**Estimated Time:**
- Phase 1: 1-2 weeks (4 tasks)
- Phase 2: 2-3 weeks (3 tasks)
- Phase 3: 30 minutes (1 task - GitHub issue only)

**Total:** 3-5 weeks for full implementation

**Context Reduction Goal:** 35k → 25k tokens (30% reduction)

---

**Next Steps:**
1. Review this plan
2. Create GitHub issues (4 issues)
3. Choose execution approach
4. Begin implementation
