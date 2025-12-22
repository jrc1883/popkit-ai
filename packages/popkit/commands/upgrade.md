---
name: upgrade
description: "Get your free API key for enhanced intelligence"
argument-hint: "[options]"
---

# /popkit:upgrade

Get a free API key to enhance PopKit with semantic intelligence.

## What This Does

PopKit works great locally. An API key adds:
- **Smarter agent routing** via embeddings
- **Community pattern learning** from shared knowledge
- **Cloud knowledge base** for cross-project insights
- **Faster skill discovery** with semantic search

**Important:** All core workflows work without an API key. The key just makes them smarter.

## Flags

| Flag | Description |
|------|-------------|
| `--open` | Force open in browser (default behavior) |
| `--url` | Just print the URL without opening |

## Examples

```bash
/popkit:upgrade           # Open signup page
/popkit:upgrade --url     # Print URL without opening
```

## Execution

### Step 1: Determine Target URL

```python
import sys

flags = "$ARGUMENTS".strip().split() if "$ARGUMENTS" else []

# Parse flags
url_only = "--url" in flags

# Build URL
url = "https://popkit.dev/signup"
```

### Step 2: Open URL or Print

If `--url` flag is present, just output the URL.

Otherwise, use AskUserQuestion to confirm and open:

```
Use AskUserQuestion tool with:
- question: "Open PopKit signup page in your browser?"
- header: "Signup"
- options:
  - label: "Yes, open in browser"
    description: "Opens {url}"
  - label: "Just show the URL"
    description: "Copy the URL manually"
- multiSelect: false
```

### Step 3: Open Browser

If user confirms, open the URL:

```bash
# Cross-platform browser open
# macOS
open "{url}"

# Windows
start "{url}"

# Linux
xdg-open "{url}"
```

### Step 4: Show Next Steps

After opening, display:

```markdown
## Next Steps

1. Create your free account at popkit.dev
2. Copy your API key from the dashboard
3. Set it in your environment:

   **macOS/Linux:**
   ```bash
   export POPKIT_API_KEY=pk_live_your_key_here
   ```

   **Windows (PowerShell):**
   ```powershell
   $env:POPKIT_API_KEY = "pk_live_your_key_here"
   ```

4. Restart Claude Code to activate enhancements

Check status with: `/popkit:account status`

## What You Get

**Enhanced Intelligence (with API key):**
- Semantic agent routing via embeddings
- Community pattern learning
- Cloud knowledge base
- Cross-project insights
- Faster skill discovery

**Local Fallbacks (without API key):**
- Keyword-based agent routing
- Local pattern storage
- File-based knowledge
- Single-project mode

**Cost:** Free for now. Usage-based pricing coming soon.

All workflows work perfectly without an API key - it just adds semantic intelligence.
```

## Alternative: Use /popkit:cloud

You can also use `/popkit:cloud signup` which provides an integrated signup experience.

## Related

- `/popkit:cloud signup` - Integrated cloud signup flow
- `/popkit:account status` - Check API key status
- `/popkit:cloud status` - Detailed connection info
