# README Overhaul Research

Issue #184 preparation document.

## 1. Research Sources

### Awesome-README Patterns

Key patterns from the curated list:
- **Logo + tagline** in hero section
- **Badges** for social proof (stars, downloads, build status)
- **GIFs/Screenshots** for immediate visual understanding
- **Progressive disclosure** - brief README, detailed docs linked
- **Table of contents** for navigation
- **Clear installation** with multiple platform options
- **Philosophy section** to explain design decisions

### Competitor Analysis

| Project | Hero | Visual | Install | Features | Unique |
|---------|------|--------|---------|----------|--------|
| **Aider** | Logo + tagline | Screencast SVG | Multi-LLM examples | Icon + paragraph pairs | 30+ testimonials |
| **Claude Code** | Title + badges | Demo GIF | 4 platform methods | Minimal (→ docs) | Strategic minimalism |
| **Continue** | Logo + tagline | 3 use-case GIFs | npm one-liner | GIF demos | Three agent types shown |
| **Fiber** | Logo + badges | Benchmark charts | Go commands | Progressive examples | Philosophy section |

### Key Insights

1. **Show, don't tell** - Demo GIFs > feature lists
2. **Multiple installation paths** - npm, homebrew, curl, platform-specific
3. **Scope management** - Brief README, link to comprehensive docs
4. **Social proof** - Badges, testimonials, community links
5. **Philosophy section** - Justify design decisions emotionally

## 2. Current PopKit README Analysis

### Strengths

- Good command table organization
- Version stats in header (commands, agents, skills)
- Workflow examples are practical
- Covers all major features

### Weaknesses

| Issue | Impact | Fix |
|-------|--------|-----|
| No visual hero (logo/banner) | Weak first impression | Create logo + banner |
| No demo GIF | Users don't see product | Record animated demo |
| No badges | Missing social proof | Add stars, version, license |
| Feature-dense | Overwhelming for beginners | Progressive disclosure |
| No testimonials | Missing credibility | Collect user feedback |
| Power Mode outdated | Shows Docker (removed) | Update to Upstash/file-based |
| Monorepo focus | Users care about plugin | Focus on plugin first |

### Critical Finding

The README still references "Redis/Docker" for Power Mode, but Issue #191 removed this entirely. **Immediate fix needed.**

## 3. PopKit's Core Vision (from CLAUDE.md)

> "PopKit exists to **orchestrate Claude Code's full power** for real-world development workflows. Claude Code provides raw tools; PopKit chains them together programmatically."

### Key Principles to Communicate

1. **Full Orchestration** - Uses ALL Claude Code capabilities
2. **Non-Linear Development** - Adapts to any project path
3. **Programmatic Chaining** - Simple tasks → sophisticated workflows
4. **Tiered Loading** - Don't load all tools at once
5. **Project Customization** - Generate project-specific tools
6. **Power Mode** - Multi-agent parallel collaboration

### Philosophy Statement (draft)

> PopKit turns Claude Code into a workflow engine. Instead of individual commands, you get composable building blocks that chain together for real development—from idea to shipped feature.

## 4. Proposed README Structure

### New Structure (Progressive Disclosure)

```
1. Hero Section
   - Logo/Banner
   - Tagline: "AI-powered development workflows for Claude Code"
   - Badges: version, license, stars, Discord

2. Demo GIF
   - 15-30 second recording of /popkit:feature-dev

3. One-Liner + Philosophy
   - What it is (one paragraph)
   - Why it exists (one paragraph)

4. Quick Install
   - Single command (marketplace)
   - Note: Restart required

5. First Commands (3 examples)
   - /popkit:morning (health check)
   - /popkit:next (recommendations)
   - /popkit:issue work 42 (real workflow)

6. Features Overview (brief)
   - Commands (→ link to full list)
   - Agents (→ link to full list)
   - Skills (→ link to full list)
   - Power Mode (→ link to guide)

7. Architecture (simple diagram)
   - Tier 1 → Tier 2 → Tier 3 visual

8. Power Mode (updated)
   - Pro: Upstash cloud
   - Free: File-based
   - NO Docker mentioned

9. Links
   - Full Documentation
   - Contributing
   - Discord Community

10. License + Author
```

### Content Length Target

- Current: ~230 lines
- Target: ~150 lines (35% reduction)
- Achieved by: Moving feature lists to separate docs

## 5. Visual Assets Needed

| Asset | Purpose | Tool |
|-------|---------|------|
| Logo | Brand identity | Design (or text-based) |
| Banner | Hero section | Canva/Figma |
| Demo GIF | Immediate understanding | asciinema/ScreenToGif |
| Architecture diagram | Tier system | Mermaid/ASCII |
| Badges | Social proof | shields.io |

## 6. Recommended Next Steps

1. **Fix Power Mode section** - Remove Docker references (Critical)
2. **Create logo/banner** - Simple text-based acceptable
3. **Record demo GIF** - /popkit:feature-dev workflow
4. **Rewrite README** - New structure above
5. **Create skills/` pop-readme-builder`** - For future use

## 7. References

- [awesome-readme](https://github.com/matiassingers/awesome-readme)
- [Aider README](https://github.com/aider-ai/aider)
- [Claude Code README](https://github.com/anthropics/claude-code)
- [Continue README](https://github.com/continuedev/continue)
- [Fiber README](https://github.com/gofiber/fiber)
