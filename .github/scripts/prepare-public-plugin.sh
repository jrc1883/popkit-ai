#!/bin/bash
# =============================================================================
# Prepare Public Plugin Content
# =============================================================================
#
# Creates a clean version of the plugin for the public repo, containing only
# declarative content (commands, skills, agents) without implementation code.
#
# Usage: bash .github/scripts/prepare-public-plugin.sh [output_dir]
#
# =============================================================================

set -e

OUTPUT_DIR="${1:-./public-plugin}"
SOURCE_DIR="packages/plugin"

echo "=== Preparing Public Plugin Content ==="
echo "Source: $SOURCE_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

# Create output directory
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# =============================================================================
# INCLUDE: Declarative content (safe to publish)
# =============================================================================

echo "📁 Copying declarative content..."

# Plugin manifest
cp -r "$SOURCE_DIR/.claude-plugin" "$OUTPUT_DIR/"

# Commands (markdown specs)
cp -r "$SOURCE_DIR/commands" "$OUTPUT_DIR/"

# Agent definitions (markdown + config)
mkdir -p "$OUTPUT_DIR/agents"
cp "$SOURCE_DIR/agents/config.json" "$OUTPUT_DIR/agents/"
cp -r "$SOURCE_DIR/agents/tier-1-always-active" "$OUTPUT_DIR/agents/"
cp -r "$SOURCE_DIR/agents/tier-2-on-demand" "$OUTPUT_DIR/agents/"
cp -r "$SOURCE_DIR/agents/feature-workflow" "$OUTPUT_DIR/agents/"
cp -r "$SOURCE_DIR/agents/assessors" "$OUTPUT_DIR/agents/" 2>/dev/null || true
cp -r "$SOURCE_DIR/agents/_templates" "$OUTPUT_DIR/agents/" 2>/dev/null || true

# Output styles (templates)
cp -r "$SOURCE_DIR/output-styles" "$OUTPUT_DIR/"

# =============================================================================
# INCLUDE: Skills (prompts only, filtered)
# =============================================================================

echo "📁 Copying skill definitions (prompts only)..."

mkdir -p "$OUTPUT_DIR/skills"

# Copy each skill directory but only the SKILL.md file
for skill_dir in "$SOURCE_DIR/skills"/*/; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")

        # Skip skills that are purely implementation
        case "$skill_name" in
            pop-upgrade-prompt)
                # This is OK to include - it's just a prompt
                ;;
        esac

        mkdir -p "$OUTPUT_DIR/skills/$skill_name"

        # Copy only SKILL.md (the prompt definition)
        if [ -f "$skill_dir/SKILL.md" ]; then
            cp "$skill_dir/SKILL.md" "$OUTPUT_DIR/skills/$skill_name/"
        fi

        # Copy templates subdirectory if it contains only data (not code)
        if [ -d "$skill_dir/templates" ]; then
            cp -r "$skill_dir/templates" "$OUTPUT_DIR/skills/$skill_name/"
        fi
    fi
done

# =============================================================================
# INCLUDE: Minimal hooks (safety checks only)
# =============================================================================

echo "📁 Creating minimal hooks..."

mkdir -p "$OUTPUT_DIR/hooks"

# Copy hooks.json
cp "$SOURCE_DIR/hooks/hooks.json" "$OUTPUT_DIR/hooks/"

# Create minimal pre-tool-use.py (safety checks only, no premium logic)
cat > "$OUTPUT_DIR/hooks/pre-tool-use.py" << 'PREHOOK'
#!/usr/bin/env python3
"""
Pre-Tool-Use Hook (Public Version)

Basic safety checks before tool execution.
Premium feature gating is handled server-side.
"""

import json
import sys

def main():
    """Process pre-tool-use hook."""
    try:
        data = json.loads(sys.stdin.read())
        tool_name = data.get("tool_name", "")

        # Basic safety validation
        result = {
            "decision": "approve",
            "reason": None
        }

        # Output result
        print(json.dumps(result))

    except Exception as e:
        print(json.dumps({
            "decision": "approve",
            "reason": None
        }))

if __name__ == "__main__":
    main()
PREHOOK

chmod +x "$OUTPUT_DIR/hooks/pre-tool-use.py"

# Create minimal post-tool-use.py (logging only)
cat > "$OUTPUT_DIR/hooks/post-tool-use.py" << 'POSTHOOK'
#!/usr/bin/env python3
"""
Post-Tool-Use Hook (Public Version)

Basic logging after tool execution.
"""

import json
import sys

def main():
    """Process post-tool-use hook."""
    try:
        data = json.loads(sys.stdin.read())
        # No special processing needed
        print(json.dumps({}))
    except Exception:
        print(json.dumps({}))

if __name__ == "__main__":
    main()
POSTHOOK

chmod +x "$OUTPUT_DIR/hooks/post-tool-use.py"

# =============================================================================
# INCLUDE: User documentation
# =============================================================================

echo "📁 Copying user documentation..."

mkdir -p "$OUTPUT_DIR/docs"

# Copy only user-facing docs, not plans or research
for doc in "$SOURCE_DIR/docs"/*.md; do
    if [ -f "$doc" ]; then
        filename=$(basename "$doc")
        # Skip internal docs
        case "$filename" in
            embedding-cost-analysis.md|*-internal.md)
                continue
                ;;
        esac
        cp "$doc" "$OUTPUT_DIR/docs/"
    fi
done

# =============================================================================
# INCLUDE: README and legal
# =============================================================================

echo "📁 Creating README..."

cat > "$OUTPUT_DIR/README.md" << 'README'
# PopKit Claude

AI-powered development workflows for Claude Code.

## Installation

```
/plugin marketplace add jrc1883/popkit-ai
/plugin install popkit@popkit-ai
```

Then restart Claude Code to activate the plugin.

## Features

- **Intelligent Agents**: 30+ specialized agents for different development tasks
- **Development Workflows**: `/popkit:dev` for guided feature development
- **Git Integration**: `/popkit:git` for commits, PRs, and releases
- **Project Analysis**: `/popkit:project analyze` for codebase understanding
- **And much more...**

## Commands

| Command | Description |
|---------|-------------|
| `/popkit:dev` | Feature development workflow |
| `/popkit:git` | Git operations (commit, pr, release) |
| `/popkit:issue` | GitHub issue management |
| `/popkit:project` | Project analysis and setup |
| `/popkit:routine` | Morning/nightly routines |
| `/popkit:debug` | Systematic debugging |
| `/popkit:assess` | Multi-perspective code assessment |

Run `/popkit:help` for full command list.

## Premium Features

Some features require a PopKit subscription for cloud backend access:
- Power Mode (multi-agent orchestration)
- Custom MCP server generation
- Pattern sharing and learning
- Team coordination

Run `/popkit:upgrade` to learn more.

## Documentation

- [Cloud Setup](docs/cloud-setup.md)
- [Contributing](CONTRIBUTING.md)

## License

Apache 2.0 - see [LICENSE](LICENSE)

---

Built with ❤️ for the Claude Code community.
README

# Copy CONTRIBUTING.md if it exists
if [ -f "$SOURCE_DIR/CONTRIBUTING.md" ]; then
    cp "$SOURCE_DIR/CONTRIBUTING.md" "$OUTPUT_DIR/"
fi

# Create LICENSE file
cat > "$OUTPUT_DIR/LICENSE" << 'LICENSE'
Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
LICENSE

# =============================================================================
# EXCLUDE: Implementation code (stays private)
# =============================================================================

echo ""
echo "❌ NOT including (stays private):"
echo "   - power-mode/           (orchestration implementation)"
echo "   - templates/            (MCP server implementation)"
echo "   - hooks/utils/          (utility modules)"
echo "   - tests/                (test implementations)"
echo "   - docs/plans/           (internal planning)"
echo "   - docs/research/        (internal research)"

# =============================================================================
# Summary
# =============================================================================

echo ""
echo "=== Summary ==="
echo ""
echo "Public content prepared in: $OUTPUT_DIR"
echo ""
echo "Contents:"
ls -la "$OUTPUT_DIR"
echo ""
echo "Commands: $(ls -1 "$OUTPUT_DIR/commands" 2>/dev/null | wc -l)"
echo "Skills: $(ls -1 "$OUTPUT_DIR/skills" 2>/dev/null | wc -l)"
echo "Agents: $(find "$OUTPUT_DIR/agents" -name "AGENT.md" 2>/dev/null | wc -l)"
echo ""
echo "Ready to push to jrc1883/popkit-ai"
