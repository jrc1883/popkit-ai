---
name: pop-api-key-prompt
description: "Shows information about API key enhancements when a user could benefit from semantic intelligence features. Uses AskUserQuestion for interactive selection. NOT for feature gating - all features work without API key."
---

# API Key Enhancement Prompt Skill

## Overview

Shows helpful information about how an API key enhances workflows with semantic intelligence. This is NOT feature gating - all workflows work perfectly without an API key.

**Core principle:** Be informative, not restrictive. Show users what intelligence enhancements are available without blocking their workflow.

**Trigger:** Optionally called when a workflow could benefit from semantic enhancements (agent routing, pattern learning, etc.)

## Arguments

| Argument | Description |
|----------|-------------|
| `enhancement_type` | What could be enhanced (routing, patterns, knowledge, etc.) |
| `current_mode` | Current mode (keyword-based, file-based, etc.) |
| `enhanced_mode` | Enhanced mode with API key (semantic, cloud-based, etc.) |
| `workflow_name` | Name of the workflow being used |

## Execution

### Step 1: Build Enhancement Message

```markdown
## 💡 Enhancement Available

**{workflow_name}**

Currently using: {current_mode}
Enhanced with API key: {enhanced_mode}

### What's the Difference?

**Without API key (current):**
- {current_mode} - Works perfectly, fully functional
- Local fallbacks for all features
- No dependencies

**With API key (enhanced):**
- {enhanced_mode} - Smarter via semantic intelligence
- Community pattern learning
- Cross-project insights
- Cloud knowledge base

**Important:** Your workflow works great either way. The API key just makes it smarter.
```

### Step 2: Show Interactive Options

Use AskUserQuestion for selection:

```
Use AskUserQuestion tool with:
- question: "Would you like to get an API key for enhanced intelligence?"
- header: "Enhancement"
- options:
  - label: "Get free API key"
    description: "Enable semantic enhancements (free for now)"
  - label: "Continue without enhancements"
    description: "Keep using local mode (fully functional)"
  - label: "Learn more"
    description: "Show details about enhancements"
- multiSelect: false
```

### Step 3: Handle Selection

**If "Get free API key":**
```
Execute /popkit:cloud signup
```

**If "Continue without enhancements":**
```markdown
Continuing with local mode. All workflows work perfectly!

You can get an API key anytime via:
- /popkit:cloud signup
- /popkit:upgrade

**Cost:** Free for now, usage-based pricing coming soon
```

**If "Learn more":**
```markdown
## API Key Enhancements

PopKit works great locally. An API key adds semantic intelligence:

### Enhanced Intelligence Features

**Semantic Agent Routing:**
- Without: Keyword-based matching
- With: Embedding-based similarity search
- Benefit: Smarter agent selection

**Community Pattern Learning:**
- Without: Local pattern storage
- With: Cloud-backed shared knowledge
- Benefit: Learn from community patterns

**Cloud Knowledge Base:**
- Without: File-based knowledge
- With: Vector database with semantic search
- Benefit: Cross-project insights

**Cross-Project Insights:**
- Without: Single-project mode
- With: Knowledge sharing across projects
- Benefit: Faster discovery and reuse

### Cost

**Free for now** - Usage-based pricing coming soon

All workflows work without API key. The key just adds intelligence.

Get started: /popkit:cloud signup
```

## Enhancement Types Reference

| Enhancement Type | Current Mode | Enhanced Mode |
|------------------|--------------|---------------|
| Agent Routing | Keyword matching | Semantic embeddings |
| Pattern Learning | File-based storage | Cloud shared knowledge |
| Knowledge Base | Local files | Vector DB with semantic search |
| Skill Discovery | Text search | Semantic similarity |
| Project Insights | Single project | Cross-project learning |

## Example Flow

**User runs:** `/popkit:project analyze`

**Optional enhancement prompt (if no API key):**

```
## 💡 Enhancement Available

**Project Analysis**

Currently using: Keyword-based analysis
Enhanced with API key: Semantic pattern matching

### What's the Difference?

**Without API key (current):**
- Keyword-based analysis - Works perfectly
- Local pattern storage
- Fast and reliable

**With API key (enhanced):**
- Semantic pattern matching - Smarter insights
- Community pattern learning
- Cross-project knowledge

**Important:** Your analysis works great either way. The API key just makes it smarter.

[AskUserQuestion appears with options]
```

**User selects:** "Continue without enhancements"

**Result:**
```markdown
Continuing with local mode. All workflows work perfectly!

[Proceeds with keyword-based analysis]
```

---

## When to Use This Skill

**Use sparingly** - Don't nag users. Only show when:
- First time using a feature that could be enhanced
- User explicitly asks about enhancements
- After 10+ sessions without API key (gentle reminder)

**Don't use** when:
- User already has API key configured
- During critical workflows (don't interrupt)
- User has explicitly disabled cloud features

---

## Related

- `/popkit:cloud signup` - Get free API key
- `/popkit:upgrade` - Alternative signup flow
- `/popkit:account status` - Check API key status
- `/popkit:cloud status` - See what's enhanced
