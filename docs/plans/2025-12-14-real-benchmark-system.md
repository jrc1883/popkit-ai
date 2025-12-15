# Real Benchmark System Design

**Date:** 2025-12-14
**Status:** Design Phase
**Goal:** Build a system to compare Claude Code performance: Vanilla vs PopKit vs PopKit Pro

---

## The Problem

Current "tests" are mock tests that just check if files exist. We need **real end-to-end benchmarks** that:
1. Actually run Claude Code sessions
2. Capture everything (tool calls, errors, time, tokens)
3. Compare across configurations (vanilla/popkit/pro)
4. Store results for analysis and visualization

---

## What We Learned from websitebuild-popkit-test-beta.txt

Real session data we can extract:

| Metric | Example Value | How to Capture |
|--------|---------------|----------------|
| Tool calls by type | Bash: 48, Read: 18 | Parse transcript |
| Total tool calls | 84 | Count tool invocations |
| Errors | 15 | Count "Error:" occurrences |
| Error types | File modified, Dangerous blocked | Categorize errors |
| PopKit commands used | /popkit:dev, /popkit:project | Track slash commands |
| Hook executions | 62 | Count hook logs |
| Session duration | ~30 min | Timestamps |
| Final outcome | Website built (with issues) | Manual or automated check |

---

## System Architecture

```
packages/
  benchmarks/
    tasks/                    # Test scenario definitions
      standard/
        bouncing-ball.md
        todo-app.md
      real-world/
        portfolio-website.md
        auth-system.md
      novel/
        research-assistant.md

    runners/
      claude-runner.py        # Invoke Claude Code CLI
      session-recorder.py     # Capture full transcript
      config-switcher.py      # Enable/disable PopKit

    analysis/
      transcript-parser.py    # Extract metrics from transcripts
      comparator.py           # Compare vanilla vs popkit vs pro
      reporter.py             # Generate reports

    results/
      sessions/               # Raw session transcripts
        {date}-{task}-{config}/
          transcript.txt
          metrics.json
          artifacts/
      comparisons/            # A/B/C comparison reports
      dashboard/              # Static HTML dashboard
```

---

## 1. Test Scenario Format (Markdown)

Each benchmark task is defined in markdown:

```markdown
---
id: portfolio-website
name: Personal Portfolio Website
category: real-world
difficulty: medium
estimated_time: 30-60min
---

# Portfolio Website Benchmark

## Objective
Build a personal portfolio website similar to maximelbv.com with:
- Dark theme
- Bento grid layout
- Projects section
- Blog/articles section
- About page
- Deployed to Cloudflare Pages

## Initial Prompt
```
Build me a personal portfolio website like https://www.maximelbv.com/
I want:
- Dark theme with modern design
- Bento grid layout for the homepage
- Projects showcase
- Blog section
- About page
- Deploy to Cloudflare Pages (I have an account)
- Domain: example.com
```

## Success Criteria
- [ ] Website builds without errors
- [ ] Homepage has bento grid layout
- [ ] Projects page lists at least 3 projects
- [ ] Blog has sample posts
- [ ] Deploys to Cloudflare Pages
- [ ] Responsive on mobile

## Quality Checks
- [ ] Lighthouse score > 90
- [ ] No accessibility errors
- [ ] No TypeScript errors
- [ ] Git repo initialized with meaningful commits

## Baseline Expectations
| Config | Est. Tool Calls | Est. Errors | Est. Time |
|--------|-----------------|-------------|-----------|
| Vanilla | 100+ | 10-20 | 45min |
| PopKit | 70-90 | 5-10 | 35min |
| PopKit Pro | 50-70 | 2-5 | 25min |
```

---

## 2. Claude Code Runner

The runner needs to:
1. Start Claude Code with specific configuration
2. Send the initial prompt
3. Capture all output
4. Let it run to completion or timeout
5. Extract artifacts

### Challenge: How to Invoke Claude Code Programmatically

Options:
1. **CLI with input redirection** - `echo "prompt" | claude`
2. **Expect/pexpect script** - Automate terminal interaction
3. **Claude Code SDK** - If available
4. **Headless mode** - If Claude Code supports it

```python
# Pseudo-code for runner
import subprocess
import time

class ClaudeRunner:
    def __init__(self, config: str = "vanilla"):
        self.config = config  # vanilla, popkit, popkit-pro

    def setup_environment(self):
        """Configure environment for this run"""
        if self.config == "vanilla":
            # Disable PopKit plugin
            self._disable_popkit()
        elif self.config == "popkit":
            # Enable PopKit free tier
            self._enable_popkit(pro=False)
        elif self.config == "popkit-pro":
            # Enable PopKit with pro features
            self._enable_popkit(pro=True)

    def run_task(self, task_file: str, timeout: int = 3600):
        """Execute a benchmark task"""
        task = load_task(task_file)

        # Start recording
        recorder = SessionRecorder()
        recorder.start()

        # Run Claude Code with prompt
        process = subprocess.Popen(
            ["claude", "--print", task.prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=task.working_dir
        )

        # Wait for completion or timeout
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()

        # Stop recording
        transcript = recorder.stop()

        return BenchmarkResult(
            task_id=task.id,
            config=self.config,
            transcript=transcript,
            exit_code=process.returncode,
            artifacts=self._collect_artifacts()
        )
```

---

## 3. Session Recording Format

Store everything in structured format:

```
results/sessions/2025-12-14-portfolio-website-vanilla/
├── transcript.txt          # Full Claude Code output
├── metrics.json            # Extracted metrics
├── artifacts/              # Generated files
│   ├── website/
│   └── screenshots/
└── metadata.json           # Run configuration
```

### metrics.json
```json
{
  "task_id": "portfolio-website",
  "config": "vanilla",
  "timestamp": "2025-12-14T10:30:00Z",
  "duration_seconds": 2847,

  "tool_calls": {
    "total": 84,
    "by_type": {
      "Bash": 48,
      "Read": 18,
      "Write": 8,
      "Edit": 7,
      "WebFetch": 1,
      "Task": 2
    }
  },

  "errors": {
    "total": 15,
    "by_type": {
      "file_modified": 7,
      "write_failed": 4,
      "timeout": 2,
      "dangerous_blocked": 1,
      "other": 1
    }
  },

  "popkit": {
    "commands_used": ["/popkit:dev", "/popkit:project"],
    "hooks_executed": 62,
    "agents_invoked": ["code-explorer", "ui-designer"]
  },

  "outcome": {
    "success": true,
    "partial": false,
    "success_criteria_met": 5,
    "success_criteria_total": 6,
    "notes": "Deployed but missing mobile responsiveness"
  },

  "quality": {
    "lighthouse_score": 87,
    "typescript_errors": 0,
    "lint_errors": 3,
    "accessibility_issues": 2
  }
}
```

---

## 4. Comparison Dashboard

Static HTML dashboard showing results:

```
┌──────────────────────────────────────────────────────────────────┐
│           PopKit Benchmark Results - Portfolio Website           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Configuration Comparison                                        │
│  ═══════════════════════════════════════════════════════════════ │
│                                                                  │
│  │ Metric          │ Vanilla │ PopKit │ PopKit Pro │ Winner    │ │
│  ├─────────────────┼─────────┼────────┼────────────┼───────────┤ │
│  │ Tool Calls      │   84    │   62   │     48     │ Pro -43%  │ │
│  │ Errors          │   15    │    8   │      3     │ Pro -80%  │ │
│  │ Duration (min)  │   47    │   35   │     28     │ Pro -40%  │ │
│  │ Success Rate    │  83%    │   92%  │    100%    │ Pro       │ │
│  │ Quality Score   │   87    │   91   │     95     │ Pro +9%   │ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Error Distribution                       │  │
│  │                                                            │  │
│  │  Vanilla:  ████████████████████████████████  15 errors    │  │
│  │  PopKit:   ████████████████                   8 errors    │  │
│  │  Pro:      ██████                             3 errors    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Key Insights:                                                   │
│  • PopKit reduced errors by 47% vs vanilla                       │
│  • Pro tier eliminated file sync issues (OneDrive workaround)    │
│  • PopKit hooks caught dangerous command (rm -rf)                │
│  • Time savings: 12-19 minutes per task                          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Test Configurations

### How to Switch Between Configs

```python
class ConfigSwitcher:
    POPKIT_PLUGIN_DIR = "~/.claude/plugins/marketplaces/popkit-marketplace"

    def set_vanilla(self):
        """Disable PopKit entirely"""
        # Rename plugin directory to disable
        if os.path.exists(self.POPKIT_PLUGIN_DIR):
            os.rename(self.POPKIT_PLUGIN_DIR, self.POPKIT_PLUGIN_DIR + ".disabled")

    def set_popkit_free(self):
        """Enable PopKit without pro features"""
        self._restore_plugin()
        self._clear_pro_credentials()

    def set_popkit_pro(self):
        """Enable PopKit with pro features"""
        self._restore_plugin()
        self._set_pro_credentials()

    def _restore_plugin(self):
        disabled = self.POPKIT_PLUGIN_DIR + ".disabled"
        if os.path.exists(disabled):
            os.rename(disabled, self.POPKIT_PLUGIN_DIR)
```

---

## 6. Metrics We'll Track

### Efficiency Metrics
- **Tool Call Count** - Fewer = more efficient
- **Token Usage** - If we can capture (may need API logs)
- **Time to Completion** - Wall clock time
- **Iterations Needed** - How many back-and-forths

### Reliability Metrics
- **Error Count** - Fewer = more reliable
- **Error Types** - Categorize (file sync, permission, logic)
- **Recovery Success** - Did it recover from errors?
- **Dangerous Blocks** - Safety system activations

### Quality Metrics
- **Success Criteria Met** - % of criteria passed
- **Lighthouse Score** - For web projects
- **Test Coverage** - If tests are generated
- **Code Quality** - Lint errors, type errors

### PopKit-Specific Metrics
- **Commands Used** - Which /popkit: commands
- **Agents Invoked** - Which agents helped
- **Hooks Executed** - How active was monitoring
- **Patterns Applied** - Did it use learned patterns

---

## 7. Running a Benchmark

### Manual Process (Phase 1)
```bash
# 1. Set configuration
python config-switcher.py --config vanilla

# 2. Create fresh working directory
mkdir -p ~/benchmarks/2025-12-14/portfolio-website-vanilla
cd ~/benchmarks/2025-12-14/portfolio-website-vanilla

# 3. Start recording (in another terminal)
script -q transcript.txt

# 4. Run Claude Code
claude

# 5. Paste the benchmark prompt and let it run

# 6. When done, exit and stop recording
exit

# 7. Parse results
python transcript-parser.py transcript.txt > metrics.json
```

### Automated Process (Phase 2)
```bash
# Run full benchmark suite
python benchmark-runner.py \
  --task portfolio-website \
  --configs vanilla,popkit,popkit-pro \
  --output results/2025-12-14/
```

---

## 8. Implementation Phases

### Phase 1: Manual Benchmarking (Now)
- [ ] Create 3-5 task definitions in markdown
- [ ] Document manual recording process
- [ ] Build transcript parser to extract metrics
- [ ] Create comparison spreadsheet template

### Phase 2: Semi-Automated (Next Week)
- [ ] Build config switcher script
- [ ] Build session recorder wrapper
- [ ] Create metrics.json generator
- [ ] Build basic HTML dashboard

### Phase 3: Fully Automated (Next Month)
- [ ] Claude Code CLI automation (if possible)
- [ ] E2B integration for isolated runs
- [ ] CI/CD for nightly benchmarks
- [ ] Public results page

---

## 9. First Benchmark Tasks

1. **Bouncing Ball** (Standard) - Simple canvas animation
2. **Portfolio Website** (Real-World) - Like maximelbv.com
3. **Todo App with Auth** (Real-World) - Full-stack CRUD
4. **Bug Fix Challenge** (Standard) - Given broken code, fix it
5. **Refactor Module** (Real-World) - Improve existing code

---

## 10. Questions to Answer

From your websitebuild experience:

| Question | How We'll Answer |
|----------|------------------|
| Is PopKit using less context? | Compare token counts (if available) |
| Is it faster? | Compare wall-clock time |
| Is it more reliable? | Compare error counts |
| Does "slower but fewer errors" = faster ship? | Compare time-to-working-product |
| Is the PopKit way actually better? | Compare quality scores |
| Does Pro justify the cost? | Calculate time/error savings vs price |

---

**Next Step:** Create the first task definitions and run manual benchmarks to validate the approach.
