# v1.0 Gist Quick Wins - Implementation Guide

**Status**: Ready for Implementation
**Date**: 2025-12-16
**Timeline**: Week 1-2 of v1.0 Quick Wins Phase (Phase 4A)
**Branch**: `claude/explore-gist-integration-URSHW`
**Target Release**: v0.3.0 (December 2025)
**Effort**: 12-14 hours total

---

## Overview

This guide details how to implement **three simple, high-value Gist skills** for v1.0 without cloud backend complexity. These skills showcase PopKit's ability to enhance GitHub workflows and can be published to the public plugin repo immediately.

**Key Principle**: Local-first, GitHub API only, no Upstash backend. Perfect for v1.0 launch. Cloud features deferred to v2.0.

---

## Why These Three Skills for v1.0?

| Skill | User Value | Implementation | Effort | Cloud Needed? | Public Friendly? |
|-------|-----------|----------------|--------|---------------|-----------------|
| **`/popkit:gist create`** | "Save this code as a snippet" | GitHub API | 4-6h | NO | YES ✅ |
| **`/popkit:gist list`** | "Show my recent gists" | Local file | 2-3h | NO | YES ✅ |
| **`/popkit:gist share`** | "Get shareable URL" | GitHub API | 3-4h | NO | YES ✅ |

**Why not search/sync?** Too much complexity for v1.0. These three hit the 80/20 rule.

---

## Skill 1: `/popkit:gist create`

### Purpose
Save current file selection (or entire file) as a GitHub gist.

### User Flow

```
User selects code in editor
  ↓
Runs: /popkit:gist create
  ↓
PopKit prompts:
  - Visibility: Public / Secret
  - Description: [optional]
  - File name: [auto-filled]
  ↓
Creates gist via GitHub API
  ↓
Stores metadata locally
  ↓
Outputs: "✅ Gist created: https://gist.github.com/..."
  ↓
(Optional) Copy link to clipboard
```

### Implementation: Skill Definition

**File**: `packages/plugin/skills/pop-gist-create.md`

```yaml
---
title: Create GitHub Gist
description: Save code selection as a GitHub gist
icon: 📌
tags:
  - github
  - snippet
  - sharing
params:
  - name: visibility
    type: choice
    description: Make gist public or secret
    options:
      - public
      - secret
    default: secret
  - name: description
    type: string
    description: Gist description (optional)
    placeholder: "e.g., React Hook Pattern"
flags:
  - name: clipboard
    description: Copy link to clipboard after creation
    short: -c
---

# Create GitHub Gist

Save your current file or selection as a GitHub gist.

## Quick Start

```
/popkit:gist create --visibility public --description "My pattern"
```

## Options

- **--visibility**: `public` or `secret` (default: secret)
- **--description**: Brief description of the gist
- **--clipboard**: Auto-copy gist link (default: on)

## What Happens

1. Saves your code to GitHub Gists
2. Stores metadata locally for quick reference
3. Outputs shareable link + markdown embed code

## Examples

### Save current file
```
/popkit:gist create
```

### Public gist with description
```
/popkit:gist create --visibility public --description "React custom hook"
```

### Without auto-clipboard
```
/popkit:gist create --clipboard false
```

## Privacy

- **Secret gists**: Only accessible via direct URL
- **Public gists**: Listed on your GitHub profile
- **Authentication**: Uses your GitHub token from Claude Code

---

status_line: "Creating gist..." → "✅ Gist created"
```

### Implementation: Hook/Utility

**File**: `packages/plugin/hooks/utils/gist_client.py`

```python
#!/usr/bin/env python3
"""
GitHub Gist API client for PopKit
Handles gist creation, listing, and metadata storage
"""

import json
import os
import hashlib
import subprocess
from datetime import datetime
from typing import Optional, Dict, List

class GistClient:
    def __init__(self, github_token: str):
        """Initialize with GitHub token from Claude Code"""
        self.token = github_token
        self.api_base = "https://api.github.com"
        self.home = os.path.expanduser("~")
        self.gists_file = f"{self.home}/.popkit/gists.json"
        self._ensure_gists_file()

    def _ensure_gists_file(self):
        """Create ~/.popkit/gists.json if it doesn't exist"""
        os.makedirs(f"{self.home}/.popkit", exist_ok=True)
        if not os.path.exists(self.gists_file):
            with open(self.gists_file, "w") as f:
                json.dump([], f, indent=2)

    def create_gist(
        self,
        content: str,
        filename: str,
        description: str = "",
        visibility: str = "secret",
        file_language: Optional[str] = None
    ) -> Dict:
        """
        Create a gist on GitHub

        Args:
            content: File content
            filename: File name (e.g., "hook.ts")
            description: Gist description
            visibility: "public" or "secret"
            file_language: Language for syntax highlighting (auto-detected)

        Returns:
            {
                "gistId": "abc123",
                "url": "https://gist.github.com/...",
                "rawUrl": "https://gist.githubusercontent.com/...",
                "success": True
            }
        """
        # Auto-detect language from extension
        if not file_language and "." in filename:
            ext = filename.split(".")[-1]
            file_language = self._extension_to_language(ext)

        # Prepare payload
        payload = {
            "files": {
                filename: {
                    "content": content,
                    "language": file_language
                }
            },
            "public": visibility == "public",
            "description": description or f"Code snippet from PopKit"
        }

        # Call GitHub API
        response = subprocess.run(
            [
                "curl",
                "-X", "POST",
                f"{self.api_base}/gists",
                "-H", f"Authorization: Bearer {self.token}",
                "-H", "Accept: application/vnd.github+json",
                "-d", json.dumps(payload)
            ],
            capture_output=True,
            text=True
        )

        if response.returncode != 0:
            return {
                "success": False,
                "error": response.stderr,
                "message": "Failed to create gist"
            }

        try:
            gist_data = json.loads(response.stdout)
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": response.stdout,
                "message": "Invalid GitHub API response"
            }

        if "id" not in gist_data:
            return {
                "success": False,
                "error": gist_data.get("message", "Unknown error"),
                "message": "GitHub API error"
            }

        gist_id = gist_data["id"]
        gist_url = gist_data["html_url"]
        raw_url = gist_data["files"][filename]["raw_url"]

        # Store metadata locally
        self._save_gist_metadata({
            "gistId": gist_id,
            "filename": filename,
            "description": description,
            "visibility": visibility,
            "language": file_language,
            "url": gist_url,
            "rawUrl": raw_url,
            "createdAt": datetime.now().isoformat(),
            "contentHash": hashlib.sha256(content.encode()).hexdigest()
        })

        return {
            "success": True,
            "gistId": gist_id,
            "url": gist_url,
            "rawUrl": raw_url,
            "filename": filename,
            "description": description,
            "visibility": visibility,
            "message": f"✅ Gist created: {gist_url}"
        }

    def list_gists(
        self,
        limit: int = 10,
        filter_visibility: Optional[str] = None
    ) -> List[Dict]:
        """
        List user's gists from local cache

        Returns:
            [{
                "gistId": "abc123",
                "filename": "hook.ts",
                "description": "Custom hook",
                "visibility": "secret",
                "createdAt": "2025-12-16T...",
                "url": "https://gist.github.com/..."
            }]
        """
        with open(self.gists_file) as f:
            gists = json.load(f)

        # Filter by visibility if requested
        if filter_visibility:
            gists = [g for g in gists if g.get("visibility") == filter_visibility]

        # Sort by creation date (newest first)
        gists = sorted(gists, key=lambda g: g["createdAt"], reverse=True)

        return gists[:limit]

    def get_gist_raw_url(self, gist_id: str, filename: str) -> str:
        """Get raw content URL for a gist"""
        # Fetch gist metadata from GitHub
        response = subprocess.run(
            [
                "curl",
                "-s",
                f"{self.api_base}/gists/{gist_id}",
                "-H", f"Authorization: Bearer {self.token}"
            ],
            capture_output=True,
            text=True
        )

        try:
            gist_data = json.loads(response.stdout)
            return gist_data["files"][filename]["raw_url"]
        except (json.JSONDecodeError, KeyError):
            return f"https://gist.githubusercontent.com/{gist_id}/raw/{filename}"

    def _save_gist_metadata(self, metadata: Dict):
        """Append gist metadata to local file"""
        with open(self.gists_file) as f:
            gists = json.load(f)

        gists.append(metadata)

        with open(self.gists_file, "w") as f:
            json.dump(gists, f, indent=2)

    @staticmethod
    def _extension_to_language(ext: str) -> str:
        """Map file extension to GitHub language name"""
        mapping = {
            "ts": "TypeScript",
            "tsx": "TypeScript",
            "js": "JavaScript",
            "jsx": "JavaScript",
            "py": "Python",
            "rb": "Ruby",
            "go": "Go",
            "rs": "Rust",
            "java": "Java",
            "cpp": "C++",
            "c": "C",
            "cs": "C#",
            "swift": "Swift",
            "kt": "Kotlin",
            "sh": "Shell",
            "bash": "Shell",
            "yaml": "YAML",
            "yml": "YAML",
            "json": "JSON",
            "md": "Markdown",
            "html": "HTML",
            "css": "CSS",
            "sql": "SQL",
        }
        return mapping.get(ext.lower(), "Text")
```

### Implementation: Skill Handler

**File**: `packages/plugin/skills/pop-gist-create.py`

```python
#!/usr/bin/env python3
"""
/popkit:gist create skill handler
Creates a GitHub gist from current file/selection
"""

import json
import sys
import os
from gist_client import GistClient

def handle_gist_create(params):
    """Main skill handler"""

    # 1. Get GitHub token from environment
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        return {
            "error": "GitHub token not found",
            "message": "Please configure GITHUB_TOKEN in Claude Code",
            "instructions": "Set via: /settings configure GITHUB_TOKEN"
        }

    # 2. Initialize gist client
    client = GistClient(github_token)

    # 3. Get parameters from Claude Code
    visibility = params.get("visibility", "secret")
    description = params.get("description", "")
    file_content = params.get("content", "")  # Current file/selection
    filename = params.get("filename", "snippet.txt")  # Auto-fill
    file_language = params.get("language")  # Auto-detect

    if not file_content:
        return {
            "error": "No content provided",
            "message": "Please select code or open a file first"
        }

    # 4. Create gist
    result = client.create_gist(
        content=file_content,
        filename=filename,
        description=description,
        visibility=visibility,
        file_language=file_language
    )

    if not result["success"]:
        return {
            "error": result.get("message"),
            "details": result.get("error")
        }

    # 5. Return success with metadata
    return {
        "success": True,
        "gistId": result["gistId"],
        "url": result["url"],
        "message": result["message"],
        "description": description,
        "visibility": visibility,
        "filename": filename,
        "actions": [
            {
                "title": "Open in Browser",
                "url": result["url"],
                "icon": "🔗"
            },
            {
                "title": "Copy Raw URL",
                "command": f"/popkit:gist share {result['gistId']} --raw",
                "icon": "📋"
            }
        ]
    }

# Main entry point
if __name__ == "__main__":
    try:
        stdin_data = json.load(sys.stdin)
        result = handle_gist_create(stdin_data.get("params", {}))
        json.dump(result, sys.stdout)
    except Exception as e:
        json.dump({
            "error": str(e),
            "message": "Internal error creating gist"
        }, sys.stdout)
```

---

## Skill 2: `/popkit:gist list`

### Purpose
Show user's recent gists with metadata.

### User Flow

```
Runs: /popkit:gist list
  ↓
PopKit reads ~/.popkit/gists.json
  ↓
Displays:
  📌 React Hook Pattern (secret)
     • Created: 2 days ago
     • Link: https://gist.github.com/...
  ↓
Offers: Open | Share | Delete
```

### Implementation: Skill Definition

**File**: `packages/plugin/skills/pop-gist-list.md`

```yaml
---
title: List GitHub Gists
description: Show your saved gists
icon: 📋
tags:
  - github
  - snippet
  - list
params:
  - name: limit
    type: number
    description: How many gists to show
    default: 10
  - name: filter
    type: choice
    description: Filter by visibility
    options:
      - all
      - public
      - secret
    default: all
flags:
  - name: recent
    description: Sort by most recent (default)
    short: -r
  - name: popular
    description: Sort by usage count
    short: -p
---

# List GitHub Gists

View your saved gists with quick actions.

## Quick Start

```
/popkit:gist list
```

## Options

- **--limit**: How many to show (default: 10)
- **--filter**: `all`, `public`, or `secret` (default: all)
- **--recent**: Sort by creation date (default)
- **--popular**: Sort by times used

## Output

```
📌 React Hook Pattern (secret)
   • Created: 2 days ago
   • URL: https://gist.github.com/abc123
   • Open | Share | Delete
```

---

status_line: "Loading gists..." → "Showing 10 gists"
```

### Implementation: Handler

```python
#!/usr/bin/env python3
"""
/popkit:gist list skill handler
Lists user's gists from local cache
"""

import json
import sys
from datetime import datetime
from gist_client import GistClient

def handle_gist_list(params):
    """Main skill handler"""

    # 1. Initialize gist client
    client = GistClient(os.getenv("GITHUB_TOKEN"))

    # 2. Get parameters
    limit = params.get("limit", 10)
    filter_visibility = params.get("filter", None)
    if filter_visibility == "all":
        filter_visibility = None

    sort_by = params.get("sort", "recent")

    # 3. List gists
    gists = client.list_gists(limit=limit, filter_visibility=filter_visibility)

    if not gists:
        return {
            "message": "No gists found",
            "hint": "Create one with: /popkit:gist create"
        }

    # 4. Format for display
    formatted = []
    for gist in gists:
        created = datetime.fromisoformat(gist["createdAt"])
        days_ago = (datetime.now() - created).days
        time_str = f"{days_ago} days ago" if days_ago > 0 else "today"

        formatted.append({
            "icon": "📌",
            "title": gist["filename"],
            "description": gist.get("description", "No description"),
            "meta": f"{gist['visibility'].capitalize()} • {time_str}",
            "url": gist["url"],
            "gistId": gist["gistId"]
        })

    return {
        "success": True,
        "count": len(formatted),
        "gists": formatted,
        "actions": [
            {
                "title": "Open All",
                "command": f"/popkit:gist open-all",
                "icon": "🔗"
            }
        ]
    }
```

---

## Skill 3: `/popkit:gist share`

### Purpose
Get various shareable formats for a gist (link, raw URL, markdown embed).

### User Flow

```
Runs: /popkit:gist share
  ↓
PopKit prompts: Which format?
  - Link only
  - Markdown embed
  - Raw content URL
  ↓
Outputs formatted text
  ↓
(Optional) Copy to clipboard
```

### Implementation: Skill Definition

**File**: `packages/plugin/skills/pop-gist-share.md`

```yaml
---
title: Share GitHub Gist
description: Get shareable gist formats
icon: 🔗
tags:
  - github
  - snippet
  - share
params:
  - name: gist_id
    type: string
    description: Gist ID (auto-detected if current file is a gist)
    required: false
  - name: format
    type: choice
    description: Share format
    options:
      - link
      - raw
      - markdown
      - html
    default: link
flags:
  - name: clipboard
    description: Copy result to clipboard
    short: -c
  - name: open
    description: Open in browser
    short: -o
---

# Share GitHub Gist

Get various shareable formats for your gist.

## Quick Start

```
/popkit:gist share --format markdown
```

## Options

- **--gist-id**: Gist ID (auto-detected if possible)
- **--format**: `link`, `raw`, `markdown`, or `html`
- **--clipboard**: Copy to clipboard (default: on)
- **--open**: Open in browser

## Formats

### Link (default)
```
https://gist.github.com/user/abc123
```

### Raw
```
https://gist.githubusercontent.com/user/abc123/raw/...
```

### Markdown
```markdown
[My Pattern](https://gist.github.com/user/abc123)
```

### HTML
```html
<script src="https://gist.github.com/user/abc123.js"></script>
```

---

status_line: "Generating share link..." → "Link ready"
```

### Implementation: Handler

```python
#!/usr/bin/env python3
"""
/popkit:gist share skill handler
Generates shareable formats for gists
"""

import json
import sys
import os
from gist_client import GistClient

def handle_gist_share(params):
    """Main skill handler"""

    # 1. Initialize gist client
    client = GistClient(os.getenv("GITHUB_TOKEN"))

    # 2. Get gist ID
    gist_id = params.get("gist_id")
    format = params.get("format", "link")
    clipboard = params.get("clipboard", True)

    if not gist_id:
        return {
            "error": "Gist ID not provided",
            "hint": "Use: /popkit:gist share --gist-id abc123"
        }

    # 3. Get gist metadata
    gists = client.list_gists(limit=1000)
    gist = next((g for g in gists if g["gistId"] == gist_id), None)

    if not gist:
        return {
            "error": "Gist not found",
            "hint": f"List gists with: /popkit:gist list"
        }

    # 4. Generate share formats
    url = gist["url"]
    raw_url = gist["rawUrl"]
    filename = gist["filename"]

    formats = {
        "link": url,
        "raw": raw_url,
        "markdown": f"[{gist['description'] or filename}]({url})",
        "html": f'<script src="{url}.js"></script>'
    }

    share_text = formats.get(format, formats["link"])

    # 5. Copy to clipboard if requested
    if clipboard:
        os.system(f'echo "{share_text}" | pbcopy 2>/dev/null || echo "{share_text}" | xclip -selection clipboard')

    return {
        "success": True,
        "gistId": gist_id,
        "format": format,
        "share": share_text,
        "url": url,
        "rawUrl": raw_url,
        "message": f"✅ {format.capitalize()} link ready",
        "copied": clipboard
    }
```

---

## Integration: Local Metadata Storage

### File Structure

```
~/.popkit/
├── gists.json          # All gist metadata
└── gist-settings.json  # User preferences (optional)
```

### gists.json Schema

```json
[
  {
    "gistId": "abc123def456",
    "filename": "useDataFetch.ts",
    "description": "Custom React hook for fetching data with caching",
    "visibility": "secret",
    "language": "TypeScript",
    "url": "https://gist.github.com/user/abc123def456",
    "rawUrl": "https://gist.githubusercontent.com/user/abc123def456/raw/...",
    "createdAt": "2025-12-16T10:30:00Z",
    "contentHash": "sha256-abc123...",
    "tags": ["react", "hooks", "fetch"],
    "synced": false,
    "syncedAt": null
  }
]
```

---

## Testing Checklist

### Manual Testing

- [ ] Test `/popkit:gist create` with selection
- [ ] Test `/popkit:gist create` with entire file
- [ ] Test public vs secret visibility
- [ ] Test with/without description
- [ ] Verify local metadata storage
- [ ] Test `/popkit:gist list` shows recent
- [ ] Test `/popkit:gist list --filter secret`
- [ ] Test `/popkit:gist list --filter public`
- [ ] Test `/popkit:gist share --format link`
- [ ] Test `/popkit:gist share --format markdown`
- [ ] Test `/popkit:gist share --format raw`
- [ ] Test clipboard copy
- [ ] Test on Windows/Mac/Linux

### Error Handling

- [ ] No GitHub token → helpful error message
- [ ] No content selected → helpful error
- [ ] Network error → graceful fallback
- [ ] Invalid gist ID → clear error

### UI/UX

- [ ] Status line updates during operations
- [ ] Outputs are colorized and readable
- [ ] Links are clickable in terminal
- [ ] Actions are discoverable (Open, Copy, etc.)
- [ ] Help text is clear and concise

---

## Integration with Public Repo

### What to Publish

**jrc1883/popkit-claude** (public repo):

```
packages/plugin/
├── skills/
│   ├── pop-gist-create.md         ← Publish (spec only)
│   ├── pop-gist-list.md           ← Publish (spec only)
│   └── pop-gist-share.md          ← Publish (spec only)
└── agents/
    └── gist-agent.yaml            ← Publish (routing)
```

**jrc1883/popkit** (private repo):

```
packages/plugin/
├── hooks/utils/
│   └── gist_client.py             ← Keep private (implementation)
└── skills/
    ├── pop-gist-create.py         ← Keep private (implementation)
    ├── pop-gist-list.py           ← Keep private (implementation)
    └── pop-gist-share.py          ← Keep private (implementation)
```

### Publishing Steps

1. Implement in private repo
2. Test thoroughly
3. Publish markdown specs to public repo:
   ```bash
   git subtree push --prefix=packages/plugin popkit-public main
   ```
4. Users get updated skills via `/plugin update popkit@popkit-claude`

---

## v1.0 Roadmap Integration

### Phase 4A: Quick Wins (Week 1-2)

| Feature | File | Effort | Status |
|---------|------|--------|--------|
| `gist create` skill | `pop-gist-create.md` + `.py` | 4-6h | 🟢 Planned |
| `gist list` skill | `pop-gist-list.md` + `.py` | 2-3h | 🟢 Planned |
| `gist share` skill | `pop-gist-share.md` + `.py` | 3-4h | 🟢 Planned |
| Local metadata storage | `gist_client.py` | 2h | 🟢 Planned |
| Testing & docs | Various | 1-2h | 🟢 Planned |
| **Total** | | **12-14h** | |

### Phase 4B: Documentation (Week 3-6)

- Add "GitHub Gist" section to docs.popkit.dev
- Link to gist management guide
- Screenshot examples
- Best practices article

---

## Success Metrics (v1.0)

- ✅ All 3 skills working without errors
- ✅ 0 bugs reported in first month
- ✅ At least 100 users create gists
- ✅ Gist feature highlighted in marketplace listing
- ✅ Documented in official PopKit docs
- ✅ Public repo has updated skills

---

## Summary

These three simple skills provide:

1. **Quick Entry Point**: Users can save code with one command
2. **Marketplace Appeal**: Shows PopKit enhances GitHub workflows
3. **Foundation for v2.0**: Local metadata enables cloud sync later
4. **Zero Complexity**: No cloud backend, GitHub API only
5. **High Value**: Solves real user problems (saving, organizing, sharing)

**Next Steps:**
1. Create skill files in `packages/plugin/skills/`
2. Implement Python handlers
3. Test locally
4. Publish to public repo
5. Include in v0.3.0 release notes

