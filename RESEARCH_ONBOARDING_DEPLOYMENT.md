# PopKit Onboarding & Deployment Research

**Research Date**: December 10, 2025
**Researcher**: Claude Code (Haiku 4.5)
**Status**: Feasibility Analysis Complete
**Model Used**: claude-haiku-4-5-20251001

---

## Executive Summary

This research explores two strategic initiatives:

1. **Onboarding Enhancement**: Making project initialization more interactive and personalized through competency assessment, project type detection, and tier-based feature tailoring
2. **Deployment Expansion**: Creating a universal deployment feature that can manage projects from any state (no GitHub, messy GitHub, or well-managed) to expert-level workflow and support multiple deployment targets

**Finding**: Both ideas are **highly feasible** and build naturally on existing PopKit infrastructure. The deployment concept, in particular, aligns perfectly with the `deployment-validator` and `devops-automator` agents already in the codebase. Onboarding enhancement requires modest additions to the existing `pop-project-init` skill.

---

## Section 1: Current Onboarding Flow Analysis

### Current State

**Location**: `packages/plugin/skills/pop-project-init/SKILL.md`
**Command**: `/popkit:project init`

#### What Currently Happens

1. **Plugin conflict detection** - Prevents installation conflicts
2. **Project type detection** - Identifies Node.js, Rust, Python, Go, or generic projects via file signatures:
   - `package.json` → Node.js
   - `Cargo.toml` → Rust
   - `pyproject.toml` / `requirements.txt` → Python
   - `go.mod` → Go
   - None → Generic

3. **Directory structure creation** - Creates `.claude/` with standard subdirectories
4. **CLAUDE.md surgical update** - Preserves existing content, adds PopKit section via HTML markers
5. **Status/settings files** - Creates `STATUS.json` and `settings.json` with defaults
6. **Power Mode question** - Single AskUserQuestion about Redis vs File-based mode
7. **Post-init guidance** - Offers next steps (analyze, setup, view issues)

#### What's Missing for Personalization

- ❌ No developer competency/experience assessment
- ❌ No project purpose/type understanding beyond tech stack
- ❌ No tier-aware feature tailoring during init
- ❌ No backend validation post-init
- ❌ No use-case flagging (e.g., "we don't have tools for scientific research")
- ❌ Limited customization beyond basic Power Mode choice

### Current Pricing Tiers

**File**: `packages/cloud-docs/pricing.md`

| Tier | Price | Key Differentiators |
|------|-------|-------------------|
| **Free** | $0/mo | File-based Power Mode, basic features, limited pattern access (10/day) |
| **Pro** | $9/mo | Hosted Redis, custom skill/MCP generation, unlimited pattern access, embeddings, 7-day history |
| **Team** | $29/mo/seat | All Pro features + team coordination, private patterns, 90-day history, team analytics |

### Premium Features Currently Gating (`premium_checker.py`)

**Generation Features** (Pro+):
- `pop-mcp-generator` - Custom MCP server generation
- `pop-skill-generator` - Custom skill generation from patterns
- `pop-morning-generator` / `pop-nightly-generator` - Custom routine generation
- `pop-dashboard` - Multi-project viewing

**Infrastructure** (Pro+):
- `pop-power-mode:redis` - Hosted Redis with persistent sessions

**Data Features** (Pro+):
- `pop-pattern-share` - Share patterns with community
- `pop-embed-project` / `pop-embed-content` - Semantic embeddings via Voyage AI

---

## Section 2: Proposed Onboarding Enhancement

### Vision

Transform `/popkit:project init` into an interactive onboarding workflow that:

1. **Assesses developer competency** to tailor future responses and recommendations
2. **Understands project purpose** beyond just tech stack (SaaS, CLI, scientific research, etc.)
3. **Identifies PopKit fit** - flag if the project is a mismatch for current PopKit capabilities
4. **Tier-gates features** - customize available skills/commands based on subscription
5. **Validates backend setup** - run cloud API tests to ensure user has access to their tier
6. **Generates custom resources** - for Pro users, auto-generate project-specific skills/MCPs
7. **Onboards systematically** - structured experience that leaves user confident and setup

### Detailed Proposal

#### Phase 1: Enhanced Project Detection (NEW)

**After** project type detection, ask:

```
question: "What's the primary purpose of this project?"
header: "Project Type"
options:
  - "Web application (SaaS, fullstack, frontend)"
  - "Backend API or service"
  - "CLI tool or utility"
  - "Library or package"
  - "Mobile/cross-platform app"
  - "Scientific computing / Research"
  - "Data pipeline / Analytics"
  - "Game or entertainment"
  - "Other (specify)"
```

**Purpose**: Different project types have different PopKit affordances:
- Web apps → Full feature set works great
- Backend APIs → API design, deployment, monitoring all useful
- Scientific research → Limited PopKit value; flag upfront
- Data pipelines → Data integrity, metrics collection agents valuable
- CLIs → Excellent fit for release management, packaging

#### Phase 2: Developer Competency Assessment (NEW)

**After** project purpose, ask:

```
question: "What's your experience level with AI-assisted development?"
header: "Competency"
options:
  - "New to Claude Code / AI development"
    description: "Want to learn step-by-step"
  - "Familiar with basic Claude workflows"
    description: "Understand prompting and Claude capabilities"
  - "Advanced - using agents and custom skills"
    description: "Comfortable with orchestration and configuration"
  - "Not sure - let Claude recommend"
    description: "Claude will adapt based on your feedback"
```

**Stored in**: `.claude/settings.json` as `"competency_level": "new|familiar|advanced|auto"`

**Used for**:
- Adapt response verbosity in future commands
- Choose simpler vs advanced agents
- Customize output styles (verbose explanations vs terse)
- Offer educational resources for "new" users
- Skip basics for "advanced" users

#### Phase 3: Backend Validation (NEW)

**After** competency assessment, validate:

```python
# Pseudo-code
if user_has_popkit_api_key:
    # Hit /v1/auth/me endpoint
    tier = check_entitlement(api_key)

    # Test Redis access if Pro+
    if tier in [PRO, TEAM]:
        test_redis_connection()

    # Store in .claude/settings.json
    settings["tier"] = tier
    settings["features_available"] = get_available_features(tier)
```

**Benefits**:
- Confirms user is set up in PopKit Cloud
- Establishes their tier early
- Allows immediate feature gating
- Provides clear messaging: "You have Pro - these features are unlocked"

#### Phase 4: Use-Case Flagging (NEW)

**Logic**: Based on `project_purpose` + `project_type`, identify if PopKit is good fit.

**Example Mapping**:

| Purpose | Type | Assessment | Action |
|---------|------|-----------|--------|
| Scientific research | Python | ⚠️ Limited fit | "PopKit specializes in software development. For research, Claude will help using built-in research tools." |
| Web app | Node.js | ✅ Excellent fit | Proceed with full onboarding |
| Data pipeline | Python | ✅ Good fit | "We have agents for data integrity, metrics collection, and automation" |
| Game | Godot/Unity | ⚠️ Partial fit | "Game dev tools limited; code generation works well" |

**Output**: Proactive messaging about what PopKit can/cannot do, setting expectations.

#### Phase 5: Tier-Aware Feature Customization (NEW)

**For Free users**:
- Skip skill/MCP generation section
- Highlight file-based Power Mode limitations
- Suggest pattern discovery features they have access to
- Show upgrade path: "Upgrade to Pro to unlock custom skills"

**For Pro users**:
- Offer: "Generate a custom MCP server for this project?" (via `pop-mcp-generator`)
- Offer: "Generate project-specific skills?" (via `pop-skill-generator`)
- Offer: "Set up Redis Power Mode?" (more powerful than file-based)
- Highlight embeddings for semantic search

**For Team users**:
- All Pro features
- Highlight: "Your team can coordinate on this project"
- Offer: "Set up team collaboration dashboard?"

**Implementation**: Check tier via `premium_checker.py::check_entitlement()` before each offer.

#### Phase 6: Post-Init Recommendations (ENHANCED)

**Current**: Generic "What would you like to do next?"

**Enhanced**: Context-aware recommendations based on:

```python
recommendations = []

if project_type == "node":
    if "next" in package_json.dependencies:
        recommendations.append("Set up Vercel deployment")
    if "jest" in package_json.dev_dependencies:
        recommendations.append("Configure test watching")

if competency_level == "new":
    recommendations.append("Run /popkit:routine morning (5-min health check)")

if tier == "pro":
    recommendations.append("Generate custom MCP server")

if project_purpose == "scientific":
    recommendations.append("Use Claude directly for research (PopKit has limited coverage)")

# Use AskUserQuestion with recommendations
```

### Implementation Notes

**Files to Create/Modify**:
- `packages/plugin/skills/pop-project-init/SKILL.md` - Expand with new phases
- `packages/plugin/hooks/utils/competency_assessor.py` (NEW) - Competency logic
- `packages/plugin/hooks/utils/use_case_matcher.py` (NEW) - Purpose → capabilities mapping
- `.claude/settings.json` - Add `competency_level`, `project_purpose`, `tier`, `features_available`

**No breaking changes**: Current init flow stays, new questions inserted after type detection.

### Feasibility: ✅ HIGH

- Uses existing `AskUserQuestion` pattern (proven, familiar)
- Integrates with existing `premium_checker.py` (tier validation already works)
- Reuses existing agents/skills (no new foundation needed)
- Tier gating already implemented in `premium.ts` cloud route
- Competency tracking is client-side only (simple JSON storage)

---

## Section 3: Deployment Expansion (Universal Deployment Feature)

### Vision

Create a comprehensive deployment feature that:

1. **Analyzes any project's Git state** - from no GitHub, to messy local repo, to professional workflows
2. **Establishes GitHub as source of truth** - if not on GitHub, migrate/setup
3. **Professionalizes Git workflows** - ensures proper branching, commits, PRs
4. **Prepares for deployment** - CI/CD, environment setup, health checks
5. **Supports multiple deployment targets** - Docker, PyPI, npm, Vercel, AWS, etc.
6. **Progressive disclosure** - basic path for beginners, advanced options for experts

### Current Deployment Infrastructure

#### Existing Agents (Tier 2)

**File**: `packages/plugin/agents/tier-2-on-demand/`

1. **deployment-validator** - Pre/post deployment checks, smoke testing, canary analysis, rollback
2. **devops-automator** - CI/CD pipelines, Docker, cloud infrastructure, IaC

**Router triggers** (from `agents/config.json`):
```json
"deploy": ["deployment-validator", "devops-automator"],
"devops": ["devops-automator"]
```

**Current capability**: These agents exist but aren't surfaced via a cohesive `/popkit:deploy` command.

#### Existing GitHub Flow

**File**: `packages/plugin/commands/git.md`

- `commit` - Smart commits with auto-generated messages
- `push` - Safe push with upstream setup
- `pr` - PR creation, listing, viewing, merging
- `review` - Code review with confidence filtering
- `ci` - GitHub Actions workflow management
- `publish` - Plugin publishing to public repo

**Existing plugin publishing flow** (`publish-plugin.yml`):
- Filtered content extraction
- Subtree split to public repo
- Versioned releases
- GitHub Actions orchestration

### Proposed Command Structure

```
/popkit:deploy <subcommand> [options]

Subcommands:
  init        Initialize GitHub (if needed) and set up deploy infrastructure
  analyze     Audit current Git/GitHub state
  setup       Configure CI/CD, environments, deployment targets
  configure   Set deployment strategy (Docker, npm, PyPI, etc.)
  validate    Pre-deployment checks (build, tests, security)
  execute     Run deployment (with rollback on failure)
  monitor     Post-deployment health checks
  rollback    Undo a deployment
```

### Detailed Proposal

#### Subcommand 1: `init` (Setup Phase)

```python
# Pseudo-logic
def deploy_init(project_path):
    status = analyze_git_state()

    if status == "no_git":
        # Initialize Git locally
        run("git init")
        run("git config user.email ...")
        ask_user("Create GitHub repo?", default=True)
        if yes:
            # Create via GitHub API
            create_github_repo()
            setup_remotes()

    elif status == "local_git_only":
        # Has local git but no GitHub
        ask_user("Push to GitHub?")
        if yes:
            create_github_repo()
            push_initial_commit()

    elif status == "github_messy":
        # Has GitHub but workflow is poor
        # Show current state and ask for fixes
        ask_user("Fix branch strategy, commit messages, PR setup?")
        if yes:
            recommend_fixes()

    # Create .github/workflows/ for CI/CD
    # Create deployment configs
```

**Outcome**: Project is GitHub-ready with proper structure.

#### Subcommand 2: `analyze` (Assessment)

Audit and report:
- Git state (initialized, has remote)
- Branch strategy (main/master, feature branches, protection rules)
- Commit hygiene (conventional commits, message quality)
- GitHub configuration (CODEOWNERS, branch protection, CI status checks)
- Deployment config (Docker, env files, CI/CD pipelines)
- Security (secrets exposed, authentication methods)

**Output**: Structured report with actionable recommendations.

#### Subcommand 3: `setup` (Configuration)

Guide user through:

1. **GitHub workflow** - Establish main/staging/dev branches, protection rules
2. **CI/CD selection**:
   ```
   Which CI/CD platform?
   - GitHub Actions (recommended, free for public)
   - GitLab CI
   - CircleCI
   - Other?
   ```
3. **Deployment targets**:
   ```
   Where do you deploy?
   - Docker (on any server)
   - npm / PyPI (package registry)
   - Vercel (frontend)
   - AWS Lambda
   - Railway / Render (simple PaaS)
   - Self-hosted server
   ```

4. **Environment management**:
   - Production secrets setup
   - Staging/dev environment configuration
   - Health check endpoints

**Uses existing agents**: `devops-automator` for infrastructure, `deployment-validator` for checks.

#### Subcommand 4: `configure` (Deployment Strategy)

Create target-specific configurations:

**Docker Path**:
- Generate Dockerfile (multi-stage)
- Create docker-compose.yml
- Set up registry (DockerHub, ECR, etc.)
- Configure build pipeline

**npm/PyPI Path**:
- Configure package metadata
- Set up semantic versioning
- Create release workflow
- Configure auth for package registry

**Vercel Path** (frontend):
- Create vercel.json
- Configure environment variables
- Set up preview deployments
- Domain configuration

**Implemented via**: Call `devops-automator` agent with target-specific prompts.

#### Subcommand 5: `validate` (Pre-Deployment)

Run pre-deployment checks:
- Build successfully
- Tests pass
- Security scans clean
- Dependencies compatible
- Environment variables set
- Secrets configured

**Implemented via**: `deployment-validator` agent.

#### Subcommand 6: `execute` (Deployment)

Orchestrate deployment:
1. Trigger CI/CD pipeline
2. Monitor build progress
3. Run deployment
4. Execute smoke tests
5. Monitor metrics
6. Ready for rollback if needed

**Implemented via**: `deployment-validator` + `devops-automator` coordination.

#### Subcommand 7: `monitor` (Post-Deployment)

Health checks post-deployment:
- Service endpoints responding
- Error rates normal
- Performance acceptable
- Integrations working
- Data integrity verified

#### Subcommand 8: `rollback` (Recovery)

Automated rollback:
- Identify previous stable version
- Reverse deployment
- Verify recovery
- Document incident

### Example User Journey

**User**: "I built a Node.js app but have no idea how to deploy it"

```
/popkit:deploy init
├─ ✓ Initialized Git
├─ ✓ Created GitHub repo
├─ ✓ Set up main branch protection
└─ Ready for CI/CD setup

/popkit:deploy setup
├─ Select deployment target: Docker
├─ ✓ Generated Dockerfile
├─ ✓ Set up Docker Hub auth
├─ ✓ Created GitHub Actions workflow
└─ Ready for deployment

/popkit:deploy configure
├─ Configuring Docker deployment to your VPS
├─ Set up production environment variables
├─ ✓ Configured health check endpoint
└─ Ready to validate

/popkit:deploy validate
├─ ✓ Docker image builds successfully
├─ ✓ Tests pass (95% coverage)
├─ ✓ No security vulnerabilities
└─ Ready to deploy

/popkit:deploy execute
├─ Triggered GitHub Actions
├─ ✓ Build complete
├─ ✓ Pushed image to registry
├─ ✓ Deployed to production
├─ ✓ Smoke tests pass
└─ Deployment complete! Version: v1.0.0
```

### Progressive Disclosure

**Free users**:
- `deploy init/analyze` - Limited to GitHub setup
- `deploy setup` - Recommendations only, no auto-generation
- File-based workflows only

**Pro users**:
- All free features
- `deploy configure` - Generate Dockerfiles, CI/CD
- Custom skill generation for project
- Semantic search for deployment patterns

**Team users**:
- All Pro features
- Collaborative deployment approval workflows
- Team audit logs for deployment
- Custom deployment strategies per team

### Integration Points

1. **With existing git command** (`/popkit:git`):
   - `git push` → suggest `deploy validate` before push
   - `git pr` → validate before merge
   - `git release` → trigger deployment

2. **With existing agents**:
   - `devops-automator` → infrastructure setup
   - `deployment-validator` → validation and monitoring
   - `security-auditor` → pre-deployment security checks

3. **With Cloud API**:
   - `POST /v1/projects/deployment-configs` - Store deployment config
   - `GET /v1/projects/{id}/deployment-history` - Track deployments
   - `POST /v1/projects/{id}/validate-deployment` - Cloud-side validation

### New Files/Components Needed

**Client-side** (plugin):
- `packages/plugin/commands/deploy.md` - Command documentation
- `packages/plugin/skills/pop-deploy-init/SKILL.md` - GitHub setup logic
- `packages/plugin/skills/pop-deploy-configure/SKILL.md` - Target-specific config
- `packages/plugin/hooks/utils/deployment_analyzer.py` - Analyze current state
- `packages/plugin/hooks/utils/target_configurator.py` - Generate configs for targets

**Server-side** (cloud):
- `packages/cloud/src/routes/deployments.ts` - Deployment config API
- `packages/cloud/src/templates/deployment-configs/` - Config templates for targets

### Feasibility: ✅ HIGH

- Agents already exist (`deployment-validator`, `devops-automator`)
- GitHub flow already established (`git.md` command, plugin publishing example)
- Cloud infrastructure ready (project registry, deployment routes feasible)
- Progressive disclosure pattern proven (other commands use this)
- No new architectural patterns required

---

## Section 4: Feature Integration Analysis

### How Onboarding & Deployment Work Together

1. **During init**: User's tier is detected
2. **During deploy setup**: Tier determines what's offered
   - Free: GitHub setup only
   - Pro: + Docker/CI config generation
   - Team: + collaborative workflows

3. **Project metadata**: Stored from onboarding feeds into deployment
   - Project purpose → recommend deployment target
   - Competency level → choose simple vs advanced workflow
   - Tech stack → auto-detect deployment needs

### Unified Status

Both features should feed into `.claude/STATUS.json`:

```json
{
  "project": {
    "purpose": "web-app",
    "type": "node-next",
    "deployed": false
  },
  "developer": {
    "competency": "familiar",
    "tier": "pro"
  },
  "deployment": {
    "git_status": "on-github",
    "workflow_score": 75,
    "ci_configured": true,
    "target": "docker"
  }
}
```

---

## Section 5: Research Gaps (Haiku 4.5 Limitations)

This research was conducted with **claude-haiku-4-5-20251001**, a fast, efficient model. The following areas would benefit from more thorough analysis with **Opus** or **Sonnet**:

### Gap 1: Detailed Implementation Specifications

**What Haiku did**: High-level architecture and feasibility assessment
**What Opus/Sonnet should do**:
- Detailed pseudo-code for each feature
- Exact API signatures and data structures
- Error handling strategies
- Edge case enumeration

**Impact**: Would reduce implementation guesswork and catch issues early.

### Gap 2: Security Implications

**What Haiku did**: Noted secrets exposure and authentication at high level
**What Opus/Sonnet should do**:
- Deep dive into credential management during deployment
- OAuth vs API key strategy for tier validation
- Secrets rotation and audit logging
- OWASP analysis of new deployment surface area
- Permission model for team deployments

**Impact**: Critical for production-ready deployment feature.

### Gap 3: User Research & Behavioral Design

**What Haiku did**: Proposed question structure
**What Opus/Sonnet should do**:
- Interview planning for competency assessment validation
- A/B testing strategy for onboarding flow
- Dropout analysis (where do users abandon?)
- Competency assessment validation (does it predict user success?)
- Accessibility audit (works for all skill levels?)

**Impact**: Ensures onboarding actually improves user outcomes.

### Gap 4: Tier Strategy Fine-Tuning

**What Haiku did**: Accepted current tier definitions
**What Opus/Sonnet should do**:
- Willingness-to-pay analysis
- Feature bundling optimization
- Competitive pricing analysis (vs GitHub Pro, Vercel, etc.)
- Churn prediction based on tier features
- Upgrade path incentives

**Impact**: Could optimize revenue without losing users.

### Gap 5: Deployment Target Ecosystem

**What Haiku did**: Listed common targets (Docker, npm, PyPI, Vercel, AWS)
**What Opus/Sonnet should do**:
- Comprehensive research of deployment landscape (2025 edition)
- Popularity metrics for each target
- Learning curve analysis
- Cost analysis per target
- Integration complexity per target

**Impact**: Ensure the targets selected actually match user distribution.

### Gap 6: Failure Mode Analysis

**What Haiku did**: Noted rollback capability
**What Opus/Sonnet should do**:
- What can go wrong at each deployment phase?
- Actual incident scenarios from production systems
- Recovery procedures for partial failures
- Data consistency under failure conditions
- User communication during failures

**Impact**: Makes deployment feature production-ready.

### Gap 7: Integration with Existing Commands

**What Haiku did**: Mentioned `/popkit:git` and agents
**What Opus/Sonnet should do**:
- Trace exact flow through 5+ commands
- Identify conflicts or redundancies
- Refactor recommendations
- Deprecation strategy for overlapping features
- User migration path if workflows change

**Impact**: Prevents feature bloat and confusing UX.

### Gap 8: Competitive Analysis

**What Haiku did**: Noted GitHub Copilot pricing
**What Opus/Sonnet should do**:
- Comprehensive competitor feature matrix
- PopKit's unique value propositions
- Market positioning
- Messaging strategy
- How to differentiate from GitHub's own deployment tools

**Impact**: Ensures marketing and positioning are sound.

---

## Section 6: Implementation Roadmap

### Phase 1: Onboarding Enhancement (Months 1-2)

**Priority**: Medium (improves UX, builds on existing code)

| Task | Effort | Dependencies |
|------|--------|--------------|
| Competency assessment logic | 1 sprint | None |
| Use-case matcher | 1 sprint | Project purpose data |
| Backend validation | 1 sprint | Premium checker works |
| Tier-aware customization | 1 sprint | Premium checker, billing API |
| Testing & polish | 1 sprint | Above complete |

**Deliverable**: `/popkit:project init` with personalization

### Phase 2: Deployment Feature (Months 2-4)

**Priority**: High (addresses major user need)

| Task | Effort | Dependencies |
|------|--------|--------------|
| `deploy init` skill (GitHub setup) | 1 sprint | GitHub API integration |
| `deploy analyze` skill | 1 sprint | Git analysis utilities |
| `deploy configure` skill | 1 sprint | Target templates |
| Agent coordination | 1 sprint | Power Mode working |
| Cloud API routes | 1 sprint | Hono/Cloudflare setup |
| Testing & docs | 1 sprint | Above complete |

**Deliverable**: `/popkit:deploy` command with 5+ subcommands

### Phase 3: Integration & Polish (Month 4)

**Priority**: Medium

| Task | Effort |
|------|--------|
| Link onboarding → deployment suggestions | 1 sprint |
| STATUS.json unified structure | 0.5 sprint |
| Documentation and guides | 1 sprint |
| User testing and feedback loop | 2 sprints |

**Deliverable**: Cohesive onboarding + deployment experience

---

## Section 7: Risk Analysis

### Onboarding Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Competency assessment doesn't predict outcomes | Medium | High | User research before launch; iterate based on data |
| Too many questions in init flow | High | Medium | A/B test; limit to 3-4 questions |
| Backend validation fails silently | Low | High | Comprehensive error handling; clear messaging |
| Tier gating frustrates free users | Medium | Medium | Offer clear upgrade path; emphasize free value |

### Deployment Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Failed deployment in production | High | Critical | Robust rollback, canary testing, staged rollout |
| Secrets exposure via generated configs | High | Critical | Security review; secrets management best practices |
| Unsupported deployment target requested | Medium | Medium | Graceful fallback; user education on targets |
| Stale deployment configs | Medium | Medium | Version tracking; periodic validation |
| Team coordination failures | Medium | High | Audit logging; approval workflows; clear state |

---

## Section 8: Success Metrics

### Onboarding Enhancement

**Primary**:
- Onboarding completion rate (% who finish init successfully)
- Time to first PopKit command after init
- Competency assessment prediction accuracy (does "new" users ask for more help?)

**Secondary**:
- Feature discovery rate (% using features gated by tier)
- Upgrade rate (% converting from Free to Pro during onboarding)
- User satisfaction (NPS on onboarding experience)

### Deployment Feature

**Primary**:
- Deployment success rate (% deployments complete without rollback)
- Time to first deployment post-feature-launch
- Deployment frequency (how often users ship)

**Secondary**:
- Target distribution (which deployment targets are popular?)
- Incident rate (critical issues post-deployment)
- User confidence (feedback on ease of use)

---

## Section 9: Conclusion & Recommendation

### Summary

Both onboarding enhancement and deployment expansion are **strategically important** and **technically feasible** with existing infrastructure:

1. **Onboarding** leverages existing tier-checking, personalizes via lightweight assessment, sets up project metadata for future customization
2. **Deployment** activates existing agents, adds CLI command structure, provides end-to-end workflow from "no GitHub" to "expert deployment"

### Recommendation

**Pursue both initiatives**, with deployment prioritized slightly higher:

- **Rationale**: Deployment directly addresses bottleneck (users don't know how to ship)
- **Sequencing**: Onboarding → Deployment (builds naturally from project metadata)
- **Timeline**: 4 months for both, parallel work on unblocked phases

### Next Steps

1. **Approval**: Confirm vision aligns with product roadmap
2. **Opus/Sonnet deep-dive**: Address research gaps identified in Section 5
3. **User research**: Validate competency assessment and deployment workflow with real users
4. **Design**: Create mockups/wireframes for both experiences
5. **Implementation**: Begin Phase 1 (onboarding) while design stabilizes Phase 2 (deployment)

---

## Appendix A: Key Files Reference

### Onboarding-Related

| File | Purpose |
|------|---------|
| `packages/plugin/skills/pop-project-init/SKILL.md` | Current init logic; expand with new phases |
| `packages/plugin/hooks/utils/premium_checker.py` | Tier validation; integrate for feature gating |
| `packages/cloud/src/routes/premium.ts` | Premium API endpoint; validate tier in cloud |
| `packages/cloud-docs/pricing.md` | Tier definitions; reference for gating |

### Deployment-Related

| File | Purpose |
|------|---------|
| `packages/plugin/agents/tier-2-on-demand/deployment-validator/` | Validates deployments; integrate into command |
| `packages/plugin/agents/tier-2-on-demand/devops-automator/` | Sets up CI/CD; integrate into command |
| `packages/plugin/commands/git.md` | Existing git flow; align deployment command |
| `.github/workflows/publish-plugin.yml` | Deployment workflow example; reference |
| `packages/cloud/src/routes/projects.ts` | Project registry; store deployment configs |
| `packages/plugin/hooks/utils/power_coordinator.py` | Multi-agent orchestration; coordinate deploy agents |

### Support Infrastructure

| File | Purpose |
|------|---------|
| `packages/plugin/agents/config.json` | Routing config; add deploy keyword routing |
| `packages/plugin/.claude-plugin/plugin.json` | Plugin manifest; version/capability updates |
| `CLAUDE.md` | Project instructions; PopKit development context |

---

## Appendix B: Questions for Product Review

1. **Competency Assessment**: Do we have existing user research on competency levels, or should we discover this?
2. **Tier Strategy**: Are Free/Pro/Team tiers final, or should deployment feature change them?
3. **Deployment Targets**: Which targets matter most to early users? Should we prioritize some?
4. **Team Workflows**: Is multi-user deployment approval needed for v1, or defer to v1.1?
5. **Backward Compatibility**: Does deployment feature change any existing commands/workflows?
6. **Marketing**: How will users discover these new features? Auto-prompt, documentation, or passive?

---

**End of Research Document**
