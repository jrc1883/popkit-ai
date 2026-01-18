# Benchmark Orchestrator Architecture (Option B)

**Goal**: User runs one command, watches trials in separate windows, gets results automatically

## User Experience Flow

```
You (in Claude Code): /popkit-ops:benchmark run jwt-authentication --trials 3

Claude (orchestrator session):
┌────────────────────────────────────────────────────────────────┐
│ 🚀 PopKit Benchmark Suite                                      │
│                                                                 │
│ Task: jwt-authentication                                        │
│ Trials: 3 per configuration                                    │
│ Total sessions: 6 (3 WITH PopKit + 3 BASELINE)                 │
│                                                                 │
│ ✓ Task definition loaded                                       │
│ ✓ Response file found: responses.json                          │
│ ✓ Worktrees ready                                              │
│                                                                 │
│ ▶ Trial 1/3 WITH PopKit - Launching window...                  │
│   [Window opens - you see Claude working with PopKit]          │
│                                                                 │
│ ▶ Trial 1/3 BASELINE - Launching window...                     │
│   [Window opens - you see vanilla Claude working]              │
│                                                                 │
│ ⏳ Running trials... (watch the windows work)                  │
│   ├─ WITH PopKit: 15 tool calls, 1,250 tokens used             │
│   └─ BASELINE: 23 tool calls, 1,850 tokens used                │
│                                                                 │
│ ✓ Trial 1 WITH PopKit completed (45s)                          │
│ ✓ Trial 1 BASELINE completed (68s)                             │
│                                                                 │
│ ▶ Trial 2/3 WITH PopKit - Launching window...                  │
│ ...                                                             │
│                                                                 │
│ ✓ All 6 trials completed!                                      │
│                                                                 │
│ 📊 Analyzing results...                                        │
│   ├─ WITH PopKit: 3/3 successful                               │
│   ├─ BASELINE: 3/3 successful                                  │
│   ├─ Context usage: -34% improvement (p=0.001, large effect)   │
│   └─ Tool calls: -35% improvement (p=0.002, large effect)      │
│                                                                 │
│ 📈 Generating HTML report...                                   │
│ ✓ Report saved: benchmark-results/jwt-auth-2026-01-16.html     │
│                                                                 │
│ 🎉 Opening report in browser...                                │
└────────────────────────────────────────────────────────────────┘

[Your browser opens showing the interactive HTML report]
```

## Architecture Components

### 1. Orchestrator Script

**Location**: `scripts/benchmark_orchestrator.py`

**Responsibilities**:
- Parse command arguments (task_id, trials, verbose)
- Load task definition and responses
- Spawn trial windows in parallel
- Monitor trial completion via recording files
- Collect recordings after completion
- Trigger analysis and reporting
- Open HTML report in browser

**Flow**:
```python
def run_orchestrator(task_id: str, trials: int):
    # 1. Load task
    task_def = load_task_definition(task_id)

    # 2. For each trial
    for trial_num in range(1, trials + 1):
        # Spawn both configurations in parallel
        with_popkit_session = spawn_trial(trial_num, with_popkit=True)
        baseline_session = spawn_trial(trial_num, with_popkit=False)

        # Monitor until both complete
        wait_for_completion([with_popkit_session, baseline_session])

        # Collect recordings
        recordings = collect_recordings([with_popkit_session, baseline_session])

    # 3. Analyze
    results = analyze_recordings(all_recordings)

    # 4. Generate report
    report_path = generate_html_report(results)

    # 5. Open in browser
    open_in_browser(report_path)
```

### 2. Window Spawning

**Cross-platform support**:

```python
def spawn_trial_window(trial_num: int, with_popkit: bool, task_def: dict) -> str:
    """Spawn new Claude Code window for trial.

    Returns:
        session_id for tracking
    """
    session_id = f"{task_def['id']}-{'with' if with_popkit else 'base'}-{trial_num}"

    # Build environment
    env = os.environ.copy()
    env["POPKIT_RECORD"] = "true"
    env["POPKIT_RECORD_ID"] = session_id
    env["POPKIT_BENCHMARK_MODE"] = "true"
    env["POPKIT_BENCHMARK_RESPONSES"] = str(response_file_path)

    if not with_popkit:
        env["CLAUDE_DISABLE_PLUGINS"] = "popkit-core,popkit-dev,popkit-ops,popkit-research"

    # Get user prompt
    prompt = task_def["user_prompt"]

    # Spawn based on platform
    if platform.system() == "Windows":
        # Windows: Use 'start' to open new terminal
        cmd = ["start", "cmd", "/k", "claude", prompt]
        subprocess.Popen(cmd, env=env, shell=True)

    elif platform.system() == "Darwin":
        # Mac: Use osascript to open new Terminal window
        script = f'''
        tell application "Terminal"
            do script "cd {worktree_path} && claude '{prompt}'"
            activate
        end tell
        '''
        subprocess.Popen(["osascript", "-e", script], env=env)

    else:
        # Linux: Use gnome-terminal or xterm
        cmd = ["gnome-terminal", "--", "bash", "-c", f"cd {worktree_path} && claude '{prompt}'; exec bash"]
        subprocess.Popen(cmd, env=env)

    return session_id
```

### 3. Completion Monitoring

**Poll recording files**:

```python
def wait_for_completion(session_ids: List[str], timeout: int = 3600):
    """Wait for all trials to complete.

    Monitors:
    - WITH PopKit: ~/.claude/popkit/recordings/<session_id>.json
    - BASELINE: ~/.claude/projects/*/<session_id>.jsonl

    Looks for completion indicators:
    - PopKit JSON: "session_end" event
    - Claude JSONL: Last entry with assistant message
    """
    start_time = time.time()
    completed = set()

    while len(completed) < len(session_ids):
        for session_id in session_ids:
            if session_id in completed:
                continue

            # Check if recording exists and is complete
            recording = find_recording(session_id)
            if recording and is_complete(recording):
                completed.add(session_id)
                log(f"✓ Trial {session_id} completed")

        # Timeout check
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Trials timed out after {timeout}s")

        # Poll every 2 seconds
        time.sleep(2)
```

### 4. Progress Display

**Real-time updates**:

```python
class ProgressDisplay:
    """Display progress in orchestrator terminal."""

    def __init__(self, total_trials: int):
        self.total_trials = total_trials
        self.completed_with_popkit = 0
        self.completed_baseline = 0

    def update(self, trial_type: str):
        if trial_type == "with_popkit":
            self.completed_with_popkit += 1
        else:
            self.completed_baseline += 1

        # Print progress bar
        total = self.total_trials * 2
        completed = self.completed_with_popkit + self.completed_baseline
        percent = (completed / total) * 100

        print(f"\r[{'█' * completed}{'░' * (total - completed)}] {percent:.0f}% ({completed}/{total} trials)", end="")
```

## Command Integration

### Slash Command

**File**: `packages/popkit-ops/commands/benchmark.md`

```markdown
## run

Run benchmark trials with orchestration.

Usage:
```bash
/popkit-ops:benchmark run <task-id> [--trials N] [--parallel]
```

Options:
- `--trials N`: Number of trials per configuration (default: 3)
- `--parallel`: Run WITH PopKit and BASELINE in parallel (default: true)
- `--sequential`: Run trials one at a time
- `--verbose`: Show detailed progress

Examples:
```bash
/popkit-ops:benchmark run jwt-authentication
/popkit-ops:benchmark run jwt-authentication --trials 5
/popkit-ops:benchmark run jwt-authentication --trials 3 --verbose
```

This will:
1. Load task definition and responses
2. Spawn separate Claude Code windows for each trial
3. Monitor progress in orchestrator window
4. Generate and open HTML report when complete
```

### Skill Hook

**File**: `packages/popkit-ops/skills/pop-benchmark-runner/SKILL.md`

Add section:

```markdown
## Orchestrated Execution

The benchmark runner uses an orchestrator pattern for side-by-side trial viewing:

1. **Main session** (current Claude) becomes orchestrator
2. **Trial sessions** spawn in new windows (you watch them work)
3. **Orchestrator** monitors via recording files
4. **Results** automatically analyzed and displayed

This allows you to see WITH PopKit vs BASELINE working side-by-side in real-time.
```

## Implementation Files

### Core Files

1. **`scripts/benchmark_orchestrator.py`** (NEW)
   - Main orchestration logic
   - Window spawning
   - Progress monitoring
   - Result aggregation

2. **`scripts/benchmark_runner.py`** (UPDATE)
   - Keep for direct API use
   - Orchestrator calls this for single trials

3. **`scripts/window_spawner.py`** (NEW)
   - Cross-platform window spawning
   - Environment variable setup
   - Session ID generation

4. **`scripts/completion_monitor.py`** (NEW)
   - Poll recording files
   - Detect completion
   - Extract metrics during execution

### Integration Points

```python
# From slash command:
from benchmark_orchestrator import BenchmarkOrchestrator

orchestrator = BenchmarkOrchestrator(task_id="jwt-authentication", trials=3)
orchestrator.run()  # Spawns windows, monitors, reports
```

## Error Handling

### Window Spawn Failure

```python
try:
    session_id = spawn_trial_window(...)
except WindowSpawnError:
    log("[ERROR] Failed to spawn trial window")
    log("[INFO] Falling back to sequential execution in current window")
    # Use existing benchmark_runner.py directly
```

### Trial Timeout

```python
if trial_timeout:
    log(f"[WARN] Trial {session_id} timed out after {timeout}s")
    log("[INFO] Continuing with remaining trials")
    # Mark as failed, continue with others
```

### Recording Not Found

```python
if not recording_found:
    log(f"[WARN] Recording not found for {session_id}")
    log("[INFO] Trial may have failed or recording was not created")
    # Skip this trial in analysis
```

## Testing

### Manual Testing

```bash
# Test orchestrator with 1 trial
/popkit-ops:benchmark run jwt-authentication --trials 1 --verbose

# Should see:
# 1. Two new windows open
# 2. Both run the same task
# 3. Orchestrator shows progress
# 4. HTML report opens automatically
```

### Unit Testing

```python
# Test window spawning
def test_spawn_window():
    session_id = spawn_trial_window(1, True, task_def)
    assert session_id is not None
    # Verify window opened (manual observation)

# Test monitoring
def test_monitor_completion():
    # Create mock recording
    recording = create_mock_recording(session_id)
    assert is_complete(recording)
```

## Benefits

1. **Visual Comparison**: Watch both trials work side-by-side
2. **No Manual Steps**: One command does everything
3. **Automatic Results**: HTML report opens automatically
4. **Progress Visibility**: See trials complete in real-time
5. **Error Transparency**: See if trials fail immediately

## Limitations

1. **Window Management**: Can't programmatically tile windows (user does this)
2. **Platform Differences**: Spawning works differently on Windows/Mac/Linux
3. **Terminal Requirements**: Requires terminal that supports new windows
4. **Resource Usage**: Multiple Claude sessions = higher memory/CPU

## Next Steps

1. Implement `benchmark_orchestrator.py`
2. Implement `window_spawner.py` with cross-platform support
3. Implement `completion_monitor.py`
4. Update `/popkit-ops:benchmark run` command
5. Test end-to-end on Windows/Mac/Linux
