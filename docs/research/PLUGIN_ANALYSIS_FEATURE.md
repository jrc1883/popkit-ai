# PopKit Plugin Analysis Feature - Research & Implementation Guide

**Document Version**: 1.0
**Date**: December 19, 2025
**Status**: Research Phase
**Objective**: Design a feature to analyze Claude Code marketplace plugins (38 total) and recommend which ones could benefit the current project PopKit is managing.

---

## 1. Feature Overview

### Problem Statement
PopKit helps developers manage complex projects using AI-powered orchestration. When developers work with PopKit, they should be able to discover and evaluate which Claude Code plugins from the 38-plugin marketplace could enhance their project's development workflow.

**Current Limitation**: No automated way to analyze whether marketplace plugins align with or complement a project's tech stack, architecture, and development patterns.

### Solution: Plugin Analysis Feature

A new PopKit feature that:
1. **Scans** the Claude Code marketplace (38 plugins)
2. **Analyzes** each plugin's capabilities, requirements, and use cases
3. **Compares** against the current project's analysis (from `pop-analyze-project`)
4. **Recommends** compatible plugins with confidence scores
5. **Integrates** recommendations into existing PopKit workflows

### Acceptance Criteria
- ✅ Discovers all 38 marketplace plugins via Claude Code API or cached registry
- ✅ Extracts plugin metadata (name, description, tags, dependencies, compatibility)
- ✅ Generates semantic embeddings for plugin capabilities
- ✅ Cross-references against project's tech stack, frameworks, and patterns
- ✅ Produces ranked recommendations (80+ confidence = recommended)
- ✅ Integrates with `/popkit:plugin` command suite
- ✅ Stores results in `.claude/plugin_recommendations.json`
- ✅ Provides visualization in CLI and web dashboard

---

## 2. Architecture & Integration Points

### 2.1 Where It Fits in PopKit

```
PopKit Plugin Analysis Feature
├── Input: Project Analysis
│   ├── .claude/analysis.json          (Project tech stack, patterns)
│   ├── .claude/tool_embeddings.json   (Project tools/patterns)
│   └── .claude/STATUS.json            (Project context)
│
├── Processing: Plugin Analysis Skills
│   ├── pop-plugin-discover            (Discover marketplace plugins)
│   ├── pop-plugin-evaluate            (Analyze plugin compatibility)
│   ├── pop-plugin-compare             (Match against project)
│   └── pop-plugin-embed               (Generate embeddings)
│
├── Storage: Local & Cloud
│   ├── .claude/plugin_recommendations.json  (Local results)
│   ├── .claude/plugin_ratings.json          (User ratings)
│   └── Upstash Redis/Vector                 (Cloud storage)
│
├── Output: Display & Integration
│   ├── /popkit:plugin recommend       (CLI command)
│   ├── /popkit:plugin evaluate <name> (Evaluate single plugin)
│   ├── /popkit:plugin install <name>  (Install recommended plugin)
│   └── Dashboard widget               (Web UI recommendations)
│
└── Agents: Decision Making
    ├── code-reviewer: Evaluate plugin quality
    ├── security-auditor: Check plugin permissions
    ├── performance-optimizer: Assess performance impact
    └── meta-agent: Aggregate recommendations
```

### 2.2 New Commands to Create

#### `/popkit:plugin recommend`
Analyze marketplace plugins and recommend those matching the project.

```bash
/popkit:plugin recommend
# Output:
# 🎯 Plugin Recommendations for [Project]
#
# ✅ HIGH CONFIDENCE (90+)
# 1. rust-analyzer-lsp (92%) - Rust language support
# 2. security-guidance (88%) - Security scanning
#
# ⚠️  MEDIUM CONFIDENCE (70-89%)
# 3. sentry (75%) - Error monitoring
#
# 💡 EXPLORE (50-69%)
# 4. userpilot (60%) - User onboarding
#
# Next: /popkit:plugin evaluate <name> for details
# Or: /popkit:plugin install <name> to add
```

#### `/popkit:plugin evaluate <name>`
Detailed analysis of a specific plugin.

```bash
/popkit:plugin evaluate security-guidance
# Output:
# 📋 Plugin Details: security-guidance
#
# Compatibility Score: 88/100
#
# ✅ Aligned Features:
# - TypeScript security analysis
# - CI/CD integration
# - Pre-commit hooks
#
# ⚠️  Considerations:
# - Requires .env configuration
# - Adds 5MB to plugin bundle
#
# 🔗 Dependencies:
# - Node.js 18+
# - ESLint 8.0+
#
# Use: /popkit:plugin install security-guidance
```

#### `/popkit:plugin compare <name1> <name2>`
Compare two plugins for specific use cases.

```bash
/popkit:plugin compare security-guidance sentry
# Helps users choose between competing plugins
```

### 2.3 New Skills to Create

Following PopKit's SKILL.md format, create 4 new skills:

#### Skill 1: `pop-plugin-discover`

```yaml
---
name: pop-plugin-discover
description: "Use when you need to discover all available Claude Code marketplace plugins, fetch their metadata, and build a registry for analysis."
inputs:
  - from: context
    field: popkit_api_key
    required: true
outputs:
  - field: marketplace_registry
    type: file_path
    description: ".claude/plugin_registry.json"
next_skills:
  - pop-plugin-evaluate
workflow:
  id: plugin-discovery
  steps:
    - "Fetch plugin list from Claude Code API or marketplace"
    - "Extract: name, description, author, tags, compatibility"
    - "Cache metadata to .claude/plugin_registry.json"
    - "Note: Each plugin has capabilities profile (see Appendix A)"
---

# Plugin Discovery Skill

## Overview
Discovers all 38 Claude Code marketplace plugins by:
1. Querying Claude Code API endpoint: `/api/marketplace/plugins`
2. Alternatively, parsing marketplace HTML/JSON if API unavailable
3. Caching results to avoid rate limits

## Execution Steps

### Step 1: Fetch Plugin List
```python
# Pseudo-code
plugins = fetch_from_api("https://api.claude-code.com/plugins")
# or
plugins = parse_marketplace_registry()
```

### Step 2: Extract Metadata
For each plugin, extract:
```json
{
  "id": "plugin-id",
  "name": "Plugin Name",
  "author": "Author Name",
  "version": "1.0.0",
  "description": "What it does",
  "tags": ["typescript", "testing", "security"],
  "categories": ["Development", "Testing"],
  "compatibility": {
    "min_claude_code_version": "2.0.0",
    "platforms": ["web", "desktop"],
    "requires_api_keys": ["github", "stripe"]
  },
  "dependencies": {
    "languages": ["typescript", "python"],
    "frameworks": ["react", "nextjs"]
  },
  "features": [
    "code-review",
    "bug-detection",
    "test-generation"
  ],
  "marketplace_url": "https://...",
  "github_url": "https://..."
}
```

### Step 3: Cache Results
Save to `.claude/plugin_registry.json` with timestamp for cache validity (24h).

## Output Structure
```json
{
  "version": "1.0",
  "last_updated": "2025-12-19T10:30:00Z",
  "total_plugins": 38,
  "plugins": [...]
}
```
```

#### Skill 2: `pop-plugin-evaluate`

```yaml
---
name: pop-plugin-evaluate
description: "Use when you need to analyze a specific marketplace plugin's capabilities, permissions, performance impact, and quality metrics."
inputs:
  - from: file_path
    field: plugin_registry
    required: true
  - from: parameter
    field: plugin_name
    required: true
outputs:
  - field: plugin_analysis
    type: file_path
    description: ".claude/analysis/plugins/<name>.json"
next_skills:
  - pop-plugin-compare
  - pop-plugin-recommend-match
workflow:
  id: plugin-evaluation
  steps:
    - "Load plugin metadata from registry"
    - "Fetch detailed documentation from marketplace"
    - "Analyze code quality (GitHub if available)"
    - "Check security permissions required"
    - "Generate semantic embeddings for capabilities"
    - "Store analysis results"
---

# Plugin Evaluation Skill

## Overview
Performs deep analysis on individual plugins:
1. Code quality assessment
2. Security permission audit
3. Performance impact prediction
4. Feature compatibility mapping
5. Embedding generation for semantic search

## Analysis Dimensions

### 1. Quality Metrics
- GitHub stars (popularity)
- Last update date (maintenance status)
- Issue/PR response time (community health)
- Code coverage (if available)
- TypeScript/type safety adoption

### 2. Security Audit
- Required permissions (API keys, file access)
- Sandbox level (isolated vs. full access)
- Data transmission (local vs. cloud)
- Dependency security (npm audit equivalent)

### 3. Compatibility Analysis
- Supported frameworks (React, Vue, etc.)
- Language requirements (TypeScript, Python)
- Version constraints
- Conflicts with other plugins

### 4. Performance Impact
- Bundle size increase
- Startup time overhead
- Memory usage
- Hook execution time

### Output: Plugin Analysis Document
```json
{
  "plugin_name": "security-guidance",
  "version": "1.0.0",
  "quality_score": 85,
  "quality_breakdown": {
    "github_stars": 450,
    "last_updated_days_ago": 5,
    "maintenance_status": "active",
    "type_safety": 90
  },
  "security_score": 92,
  "security_breakdown": {
    "permissions_required": ["file_read", "env_vars"],
    "sandbox_level": "restricted",
    "external_api_calls": 1,
    "data_local_only": true
  },
  "performance_score": 78,
  "performance_breakdown": {
    "bundle_size_mb": 2.5,
    "startup_time_ms": 150,
    "memory_usage_mb": 45
  },
  "capabilities": [
    "security-analysis",
    "vulnerability-detection",
    "best-practice-recommendations"
  ],
  "compatible_frameworks": ["nextjs", "react", "node"],
  "overall_score": 85
}
```
```

#### Skill 3: `pop-plugin-recommend-match`

```yaml
---
name: pop-plugin-recommend-match
description: "Use when you need to compare project's tech stack and patterns against plugin capabilities, generating compatibility scores and recommendations."
inputs:
  - from: file_path
    field: project_analysis
    required: true
    description: ".claude/analysis.json from pop-analyze-project"
  - from: file_path
    field: plugin_registry
    required: true
    description: ".claude/plugin_registry.json from pop-plugin-discover"
outputs:
  - field: recommendations
    type: file_path
    description: ".claude/plugin_recommendations.json"
next_skills:
  - pop-plugin-embed
workflow:
  id: plugin-matching
  steps:
    - "Load project analysis (frameworks, patterns, architecture)"
    - "Load plugin registry with evaluation scores"
    - "Calculate semantic similarity (embeddings)"
    - "Score each plugin against project needs"
    - "Rank by confidence score"
    - "Generate recommendation summary"
---

# Plugin Recommendation Matching Skill

## Overview
Matches project profile against 38 plugins using:
1. Keyword/tag alignment
2. Semantic similarity (embeddings)
3. Framework compatibility
4. Architecture pattern matching
5. Team skill alignment

## Scoring Algorithm

### 1. Framework Match (30% weight)
```
score = plugins_framework_support / project_frameworks_count
```
- Next.js project + plugin supports Next.js = +30 points

### 2. Feature Alignment (25% weight)
```
score = plugin_features_matching_project_needs / total_plugin_features
```
- Project needs "testing" + plugin offers "test generation" = +25 points

### 3. Tech Stack Compatibility (20% weight)
```
score = compatible_languages_count / required_languages
```
- Project uses TypeScript + plugin supports TypeScript = +20 points

### 4. Quality & Maturity (15% weight)
```
score = (github_stars / 1000) * (maintenance_status) * type_safety_score
```
- Well-maintained + high quality = +15 points

### 5. Security & Performance (10% weight)
```
score = (security_score / 100) * (performance_score / 100) * 10
```
- No security concerns + good performance = +10 points

## Output: Recommendations Document

```json
{
  "project": "MyNextJsApp",
  "analysis_date": "2025-12-19T10:45:00Z",
  "recommendations": [
    {
      "rank": 1,
      "plugin_name": "security-guidance",
      "confidence_score": 92,
      "reasons": [
        "Matches TypeScript requirement",
        "Supports Next.js framework",
        "Provides security analysis (project need)",
        "Well-maintained (last update 5 days ago)",
        "No permission conflicts"
      ],
      "benefits": [
        "Automated security scanning in CI/CD",
        "Best practice recommendations",
        "Vulnerability detection"
      ],
      "considerations": [
        "Requires .env setup",
        "Adds 2.5MB to bundle"
      ]
    },
    {
      "rank": 2,
      "plugin_name": "sentry",
      "confidence_score": 78,
      "reasons": [
        "Error monitoring capability",
        "Supports JavaScript/TypeScript",
        "Popular (1200 stars)",
        "Low performance overhead"
      ],
      "benefits": [
        "Production error tracking",
        "Real-time alerts",
        "Stack trace analysis"
      ],
      "considerations": [
        "Requires Sentry account",
        "Sends errors to external service"
      ]
    }
  ],
  "not_recommended": [
    {
      "plugin_name": "fish-speech",
      "confidence_score": 12,
      "reason": "Voice/ML plugin incompatible with web project"
    }
  ],
  "summary": "Found 8 highly recommended plugins for your Next.js + TypeScript project"
}
```
```

#### Skill 4: `pop-plugin-embed`

```yaml
---
name: pop-plugin-embed
description: "Use when you need to generate semantic embeddings for all plugins and enable semantic search for plugin discovery."
inputs:
  - from: file_path
    field: plugin_registry
    required: true
  - from: file_path
    field: recommendations
    required: true
outputs:
  - field: plugin_embeddings
    type: file_path
    description: ".claude/plugin_embeddings.json"
next_skills: []
workflow:
  id: plugin-embeddings
  steps:
    - "Extract plugin descriptions, features, tags"
    - "Call Voyage API to generate embeddings"
    - "Store embeddings locally"
    - "Upload to Upstash Vector for cloud search"
---

# Plugin Embeddings Skill

## Overview
Generates semantic embeddings for:
1. Plugin descriptions and capabilities
2. Project analysis and needs
3. Enables semantic similarity search
4. Powers fuzzy plugin discovery

## Implementation Details

### Embedding Generation
```python
from voyageai import Client

# Embed all plugin descriptions
plugin_descriptions = [plugin["description"] for plugin in plugins]
embeddings = voyage_client.embed(
    texts=plugin_descriptions,
    model="voyage-3",
    input_type="document"
)

# Embed project capabilities
project_needs = extract_from_analysis(project_analysis)
project_embeddings = voyage_client.embed(
    texts=project_needs,
    model="voyage-3",
    input_type="query"
)
```

### Similarity Scoring
```python
from sklearn.metrics.pairwise import cosine_similarity

# Calculate similarity matrix
similarities = cosine_similarity(project_embeddings, plugin_embeddings)

# Normalize to 0-100 scale
scores = (similarities * 100).round(0)
```

### Storage
```json
{
  "version": "1.0",
  "generated": "2025-12-19T10:50:00Z",
  "embeddings": [
    {
      "plugin_id": "security-guidance",
      "description_embedding": [0.125, 0.234, ...],
      "features_embedding": [0.456, 0.789, ...],
      "dimensions": 1024
    }
  ],
  "project_embeddings": {
    "needs_embedding": [0.111, 0.222, ...],
    "tech_stack_embedding": [0.333, 0.444, ...]
  }
}
```
```

### 2.4 New Agents to Activate

Activate existing agents to evaluate plugins:

| Agent | Role | Task |
|-------|------|------|
| `code-reviewer` | Quality assessment | Evaluate plugin code quality and best practices |
| `security-auditor` | Permission audit | Check plugin permissions and sandbox level |
| `performance-optimizer` | Bundle analysis | Assess performance impact (bundle size, startup) |
| `meta-agent` | Aggregation | Synthesize recommendations from all agents |

Invoke these agents from `pop-plugin-evaluate` when deep assessment needed.

### 2.5 New Commands to Register

Add to `packages/plugin/commands/plugin.md`:

```markdown
---
name: plugin-recommend
description: "Show recommended marketplace plugins for your project"
inputs:
  - analysis_file: .claude/analysis.json
  - registry_file: .claude/plugin_registry.json
  - recommendations_file: .claude/plugin_recommendations.json
outputs:
  - text: Ranked list of compatible plugins
  - action_buttons:
    - /popkit:plugin evaluate <name>
    - /popkit:plugin install <name>
---

# /popkit:plugin recommend

Analyzes your project and recommends the best plugins from the 38-plugin marketplace.

## Usage
```bash
/popkit:plugin recommend
/popkit:plugin recommend --filter="testing"
/popkit:plugin recommend --min-confidence=80
```

## Output
Ranked recommendations with confidence scores, alignment reasons, and next steps.
```

---

## 3. Data Storage & Persistence

### 3.1 Local Storage (`.claude/` directory)

New files to create:

| File | Purpose | Format | Size |
|------|---------|--------|------|
| `plugin_registry.json` | Cached list of all 38 plugins | JSON | ~500KB |
| `plugin_recommendations.json` | Ranked recommendations for project | JSON | ~50KB |
| `plugin_embeddings.json` | Semantic embeddings for search | JSON | ~1MB |
| `plugin_ratings.json` | User ratings/feedback on plugins | JSON | ~10KB |
| `analysis/plugins/` | Individual plugin analyses | JSON per file | ~2MB total |

### 3.2 Cloud Storage (Upstash Redis + Vector)

**Keys to store:**

```
popkit:plugins:registry:<timestamp>          # Full plugin registry
popkit:plugins:recommendations:<project_id>  # Project-specific recommendations
popkit:plugins:ratings:<plugin_id>           # Aggregate user ratings
popkit:plugins:vectors:<plugin_id>           # Embedding vectors
```

**Upstash Vector setup:**

```
Index: "popkit-plugins"
Dimensions: 1024 (Voyage API)
Metadata: {
  plugin_id: string,
  plugin_name: string,
  confidence_score: number,
  categories: string[]
}
```

### 3.3 Cache Strategy

```python
# 24-hour cache for plugin registry (stable, infrequently changes)
plugin_registry_ttl = 86400  # seconds

# 30-minute cache for recommendations (can change as project evolves)
recommendations_ttl = 1800

# On-demand cache invalidation
/popkit:plugin recommend --no-cache  # Force refresh
```

---

## 4. Implementation Roadmap

### Phase 1: Plugin Discovery (Week 1)
- [ ] Implement `pop-plugin-discover` skill
- [ ] Fetch all 38 plugins from marketplace
- [ ] Cache to `.claude/plugin_registry.json`
- [ ] Create `/popkit:plugin list` command

### Phase 2: Plugin Evaluation (Week 2)
- [ ] Implement `pop-plugin-evaluate` skill
- [ ] Quality metrics (GitHub stars, updates)
- [ ] Security audit (permissions, sandbox)
- [ ] Performance analysis
- [ ] Create `/popkit:plugin evaluate <name>` command

### Phase 3: Recommendation Matching (Week 3)
- [ ] Implement `pop-plugin-recommend-match` skill
- [ ] Scoring algorithm (5 dimensions)
- [ ] Framework compatibility analysis
- [ ] Feature alignment matching
- [ ] Create `/popkit:plugin recommend` command

### Phase 4: Semantic Search (Week 4)
- [ ] Implement `pop-plugin-embed` skill
- [ ] Voyage API integration
- [ ] Semantic similarity scoring
- [ ] Cloud sync to Upstash Vector
- [ ] Enable `/popkit:plugin search <query>` command

### Phase 5: Integration & Polish (Week 5)
- [ ] Integrate with agents (code-reviewer, security-auditor, etc.)
- [ ] Web dashboard widget for recommendations
- [ ] User rating/feedback collection
- [ ] Performance optimization
- [ ] Documentation and user guide

---

## 5. API Integration Requirements

### 5.1 Claude Code Marketplace API

**Assumption**: Claude Code exposes a marketplace API. If not available, implement fallback:

```python
# Option A: Official API (preferred)
GET https://api.claude-code.com/v1/marketplace/plugins
Response: { plugins: [...], total: 38 }

# Option B: Web scraping fallback
GET https://claude-code.io/marketplace/
Parse HTML to extract plugin list

# Option C: Community registry (if Option A/B fail)
# Maintain manual JSON registry in PopKit repo
```

### 5.2 Voyage API for Embeddings

Already integrated in PopKit via `pop-embed-project` skill.

```python
from voyageai import Client

client = Client(api_key=os.getenv("VOYAGE_API_KEY"))
result = client.embed(
    texts=["text1", "text2"],
    model="voyage-3",
    input_type="document"
)
# Returns: embeddings (list of 1024-dim vectors)
```

**Rate limits**: 3 requests per minute (from CLAUDE.md)

### 5.3 Upstash Vector Integration

Store embeddings for cloud-based semantic search.

```python
from upstash_vector import Index

index = Index(
    url=os.getenv("UPSTASH_VECTOR_URL"),
    token=os.getenv("UPSTASH_VECTOR_TOKEN")
)

# Upsert plugin embeddings
for plugin in plugins:
    index.upsert(
        vectors=[
            (
                plugin["id"],
                plugin_embedding,
                {"plugin_name": plugin["name"], "score": score}
            )
        ]
    )

# Query for similar plugins
results = index.query(
    vector=project_embedding,
    top_k=10,
    include_metadata=True
)
```

---

## 6. User Workflows

### Workflow 1: Discover & Install Recommended Plugins

```bash
# 1. User runs PopKit analysis
cd my-nextjs-project
/popkit:project analyze

# 2. User discovers plugins
/popkit:plugin recommend
# Output:
# 🎯 Top Recommendations for MyProject
# 1. security-guidance (92%)
# 2. sentry (78%)
# ...

# 3. User evaluates specific plugin
/popkit:plugin evaluate security-guidance
# Output: Detailed analysis, permissions, performance impact

# 4. User installs plugin
/popkit:plugin install security-guidance
# Output: Installation steps, integration guide
```

### Workflow 2: Search for Plugins by Capability

```bash
# User wants testing tools
/popkit:plugin search testing

# Output: Ranked list of testing-related plugins
# 1. test-generator (89%)
# 2. jest-helper (76%)
# ...
```

### Workflow 3: Compare Alternative Plugins

```bash
# User choosing between options
/popkit:plugin compare sentry datadog

# Output: Side-by-side comparison
# Feature                 | Sentry | Datadog
# Real-time alerts        | ✅     | ✅
# Custom metrics          | ❌     | ✅
# Free tier               | ✅     | ❌
# ...
```

### Workflow 4: Manage Plugin Ratings

```bash
# User rates plugin after using it
/popkit:plugin rate security-guidance 5 "Excellent security analysis, easy setup"

# Feedback stored to .claude/plugin_ratings.json
# Aggregated ratings inform recommendations for future projects
```

---

## 7. Testing Strategy

### Unit Tests
- Plugin discovery parsing
- Scoring algorithm (verify 100-point scale)
- Embedding similarity calculations
- Framework matching logic

### Integration Tests
- End-to-end discovery → recommendation flow
- Marketplace API fallback chains
- Upstash Vector storage/retrieval
- Cloud sync reliability

### User Acceptance Testing
- Recommendation accuracy (manual verification)
- Performance (query time < 2s)
- Cache effectiveness
- Edge cases (empty project, no matches, etc.)

---

## 8. Success Metrics

### Adoption Metrics
- % of PopKit users running `/popkit:plugin recommend`
- Average plugins installed per project
- Plugin discovery sessions per month

### Quality Metrics
- Recommendation accuracy (user feedback)
- Plugin compatibility success rate
- Bounce rate (users abandon after viewing)

### Performance Metrics
- Recommendation query time (target: < 2s)
- Plugin discovery API latency
- Embedding generation time
- Cache hit rate (target: > 80%)

---

## 9. Risk Mitigation

### Risk 1: Marketplace API Unavailable
**Mitigation**: Implement web scraping fallback + maintain manual registry

### Risk 2: Inaccurate Recommendations
**Mitigation**: Feedback loop to refine scoring algorithm + user ratings

### Risk 3: Embedding Cost (Voyage API)
**Mitigation**: Cache embeddings, batch generation, limit to 38 plugins only

### Risk 4: Plugin Data Quality
**Mitigation**: Validation + manual curation for edge cases

### Risk 5: Security Concerns
**Mitigation**: Sandbox analysis environment, no plugin installation without approval

---

## 10. Appendix A: Plugin Profiles Template

Each of the 38 plugins will have a profile structure:

```json
{
  "id": "unique-plugin-id",
  "name": "Plugin Name",
  "author": "Author Name",
  "version": "1.0.0",
  "marketplace_url": "https://claude-code.io/plugins/...",
  "github_url": "https://github.com/...",
  "tags": ["typescript", "testing", "automation"],
  "categories": [
    "Development Tools",
    "Testing",
    "CI/CD"
  ],
  "description": "Short description of what plugin does",
  "long_description": "Detailed explanation with features and use cases",
  "features": [
    "Automated test generation",
    "Code analysis",
    "Performance profiling"
  ],
  "requirements": {
    "min_claude_code_version": "2.0.0",
    "supported_platforms": ["web", "desktop", "cli"],
    "supported_languages": ["typescript", "javascript", "python"],
    "requires_api_keys": ["github", "stripe"],
    "requires_external_services": ["github-actions", "ci-cd"]
  },
  "compatibility": {
    "frameworks": ["next.js", "react", "vue"],
    "runtimes": ["node.js", "browser"],
    "os": ["macos", "linux", "windows"]
  },
  "metadata": {
    "github_stars": 450,
    "last_updated": "2025-12-15",
    "maintenance_status": "active",
    "type_safety_score": 90,
    "bundle_size_mb": 2.5,
    "startup_time_ms": 150,
    "memory_usage_mb": 45,
    "install_count": 1250
  },
  "quality_score": 85,
  "security_score": 92,
  "performance_score": 78,
  "overall_score": 85
}
```

---

## 11. Next Steps

### Immediate Actions
1. **Verify marketplace API availability** - Check if Claude Code publishes plugin API
2. **Prepare plugin registry** - Manually document all 38 plugins if API unavailable
3. **Design skill templates** - Finalize SKILL.md formats for discovery, evaluation, matching
4. **Set up embeddings** - Confirm Voyage API credentials and rate limits

### Communication
- [ ] Present feature design to PopKit team
- [ ] Get approval on scoring algorithm
- [ ] Plan implementation sprint
- [ ] Create GitHub issues for each phase

### Documentation
- [ ] User guide: How to discover plugins
- [ ] Developer guide: How to extend scoring algorithm
- [ ] API guide: Marketplace plugin format specification
- [ ] Troubleshooting: Common recommendation issues

---

## 12. References

### PopKit Documentation
- `popkit/CLAUDE.md` - PopKit architecture
- `popkit/packages/plugin/agents/config.json` - Agent routing
- `popkit/packages/plugin/skills/` - Skill implementations
- `popkit/packages/cloud/src/routes/embeddings.ts` - Embedding API

### External Resources
- Claude Code Marketplace - https://claude-code.io/marketplace/
- Voyage API Docs - https://docs.voyage.ai/
- Upstash Vector Docs - https://upstash.com/docs/vector/

---

**Document Status**: Ready for Team Review
**Next Milestone**: Implementation Planning (Phase 1 kickoff)
**Owner**: PopKit Development Team
