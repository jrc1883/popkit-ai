# Deploy Configuration Schema

**File Location:** `.claude/popkit/deploy.json`

**Purpose:** Central configuration file for PopKit deployment orchestration. Created by `/popkit:deploy init` and consumed by all deploy subcommands.

**Version:** 1.0

---

## Full Schema (TypeScript)

```typescript
interface DeployConfig {
  // Schema metadata
  version: string;              // Config schema version (currently "1.0")

  // Project identification
  project_type: ProjectType;    // User-selected project type
  language: Language;           // Auto-detected language
  framework: Framework;         // Auto-detected framework

  // Deployment configuration
  targets: DeployTarget[];      // User-selected deployment targets
  state: ProjectState;          // User-selected initial state

  // Initialization metadata
  initialized_at: string;       // ISO 8601 timestamp
  initialized_by: string;       // PopKit version string (e.g., "popkit-1.0.0")

  // GitHub integration
  github: GitHubConfig;

  // CI/CD detection
  cicd: CICDConfig;

  // Gap analysis
  gaps: GapAnalysis;

  // Audit trail
  history: HistoryEntry[];

  // Target-specific configs (populated by setup)
  target_configs?: TargetConfigs;
}

// Enums and nested types

type ProjectType =
  | "web-app"
  | "backend-api"
  | "cli-tool"
  | "library"
  | "other";

type Language =
  | "javascript"
  | "typescript"
  | "python"
  | "rust"
  | "go"
  | "java"
  | "csharp"
  | "unknown";

type Framework =
  | "nextjs"
  | "react"
  | "vite"
  | "vue"
  | "nuxt"
  | "svelte"
  | "django"
  | "flask"
  | "fastapi"
  | "express"
  | "nestjs"
  | "cargo"
  | "go"
  | "generic";

type DeployTarget =
  | "docker"
  | "vercel"
  | "netlify"
  | "npm"
  | "pypi"
  | "github-releases";

type ProjectState =
  | "fresh"           // No GitHub, no CI/CD
  | "needs-cicd"      // Has GitHub, needs CI/CD
  | "needs-targets"   // Has CI/CD, needs target configs
  | "ready";          // Everything configured

interface GitHubConfig {
  initialized: boolean;         // Is git repository initialized?
  repo: string | null;          // "owner/repo" format, or null if no remote
  default_branch: string | null; // Usually "main" or "master"
  has_actions: boolean;         // .github/workflows/ directory exists?
}

interface CICDConfig {
  detected: boolean;            // Any CI/CD platform detected?
  platform: CICDPlatform | null;
  workflow_count: number;       // Number of workflow files found
}

type CICDPlatform =
  | "github-actions"
  | "gitlab-ci"
  | "circleci"
  | "azure-pipelines"
  | "jenkins"
  | "unknown";

interface GapAnalysis {
  needs_github: boolean;        // True if no GitHub repo configured
  needs_cicd: boolean;          // True if no CI/CD pipelines found
  needs_target_configs: boolean; // True if selected targets not configured
}

interface HistoryEntry {
  action: DeployAction;         // Type of action performed
  timestamp: string;            // ISO 8601 timestamp
  user: string;                 // Git user.name who performed action
  version: string;              // PopKit version at time of action
  details?: Record<string, any>; // Optional action-specific details
}

type DeployAction =
  | "init"
  | "setup"
  | "validate"
  | "deploy"
  | "rollback";

interface TargetConfigs {
  docker?: DockerConfig;
  vercel?: VercelConfig;
  netlify?: NetlifyConfig;
  npm?: NPMConfig;
  pypi?: PyPIConfig;
  "github-releases"?: GitHubReleasesConfig;
}

interface DockerConfig {
  dockerfile_path: string;      // Relative path to Dockerfile
  image_name: string;           // Docker image name
  registry: string;             // Registry URL (e.g., "ghcr.io")
  workflow_file: string;        // GitHub Actions workflow file path
}

interface VercelConfig {
  project_id: string;           // Vercel project ID
  org_id: string;               // Vercel organization ID
  config_file: string;          // Path to vercel.json
  workflow_file: string;        // GitHub Actions workflow file path
}

interface NetlifyConfig {
  site_id: string;              // Netlify site ID
  config_file: string;          // Path to netlify.toml
  workflow_file: string;        // GitHub Actions workflow file path
}

interface NPMConfig {
  package_name: string;         // Package name from package.json
  registry: string;             // Registry URL (default: registry.npmjs.org)
  workflow_file: string;        // GitHub Actions workflow file path
  access: "public" | "restricted"; // Package access level
}

interface PyPIConfig {
  package_name: string;         // Package name from pyproject.toml
  repository: string;           // Repository URL (default: pypi.org)
  workflow_file: string;        // GitHub Actions workflow file path
}

interface GitHubReleasesConfig {
  workflow_file: string;        // GitHub Actions workflow file path
  asset_patterns: string[];     // Glob patterns for release assets
  draft: boolean;               // Create as draft release?
  prerelease: boolean;          // Mark as prerelease?
}
```

---

## Example Configurations

### Example 1: Fresh Next.js Project

```json
{
  "version": "1.0",
  "project_type": "web-app",
  "language": "javascript",
  "framework": "nextjs",
  "targets": ["vercel", "docker"],
  "state": "fresh",
  "initialized_at": "2025-12-15T10:30:00Z",
  "initialized_by": "popkit-1.0.0",
  "github": {
    "initialized": false,
    "repo": null,
    "default_branch": null,
    "has_actions": false
  },
  "cicd": {
    "detected": false,
    "platform": null,
    "workflow_count": 0
  },
  "gaps": {
    "needs_github": true,
    "needs_cicd": true,
    "needs_target_configs": true
  },
  "history": [
    {
      "action": "init",
      "timestamp": "2025-12-15T10:30:00Z",
      "user": "John Doe",
      "version": "popkit-1.0.0"
    }
  ]
}
```

### Example 2: Existing Python API with GitHub

```json
{
  "version": "1.0",
  "project_type": "backend-api",
  "language": "python",
  "framework": "fastapi",
  "targets": ["docker", "pypi"],
  "state": "needs-cicd",
  "initialized_at": "2025-12-15T11:00:00Z",
  "initialized_by": "popkit-1.0.0",
  "github": {
    "initialized": true,
    "repo": "jdoe/my-api",
    "default_branch": "main",
    "has_actions": false
  },
  "cicd": {
    "detected": false,
    "platform": null,
    "workflow_count": 0
  },
  "gaps": {
    "needs_github": false,
    "needs_cicd": true,
    "needs_target_configs": true
  },
  "history": [
    {
      "action": "init",
      "timestamp": "2025-12-15T11:00:00Z",
      "user": "Jane Doe",
      "version": "popkit-1.0.0"
    }
  ]
}
```

### Example 3: Production-Ready React Library

```json
{
  "version": "1.0",
  "project_type": "library",
  "language": "typescript",
  "framework": "react",
  "targets": ["npm", "github-releases"],
  "state": "ready",
  "initialized_at": "2025-12-15T12:00:00Z",
  "initialized_by": "popkit-1.0.0",
  "github": {
    "initialized": true,
    "repo": "acme/ui-components",
    "default_branch": "main",
    "has_actions": true
  },
  "cicd": {
    "detected": true,
    "platform": "github-actions",
    "workflow_count": 3
  },
  "gaps": {
    "needs_github": false,
    "needs_cicd": false,
    "needs_target_configs": false
  },
  "history": [
    {
      "action": "init",
      "timestamp": "2025-12-15T12:00:00Z",
      "user": "Alice Smith",
      "version": "popkit-1.0.0"
    },
    {
      "action": "setup",
      "timestamp": "2025-12-15T12:05:00Z",
      "user": "Alice Smith",
      "version": "popkit-1.0.0",
      "details": {
        "targets": ["npm", "github-releases"],
        "files_created": 4
      }
    }
  ],
  "target_configs": {
    "npm": {
      "package_name": "@acme/ui-components",
      "registry": "https://registry.npmjs.org",
      "workflow_file": ".github/workflows/npm-publish.yml",
      "access": "public"
    },
    "github-releases": {
      "workflow_file": ".github/workflows/release.yml",
      "asset_patterns": ["dist/*.tar.gz", "dist/*.zip"],
      "draft": false,
      "prerelease": false
    }
  }
}
```

---

## Field Descriptions

### Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Schema version (currently "1.0") |
| `project_type` | ProjectType | Yes | User-selected project classification |
| `language` | Language | Yes | Auto-detected primary language |
| `framework` | Framework | Yes | Auto-detected framework/runtime |
| `targets` | DeployTarget[] | Yes | User-selected deployment destinations |
| `state` | ProjectState | Yes | Current project state |
| `initialized_at` | string | Yes | ISO 8601 timestamp of initialization |
| `initialized_by` | string | Yes | PopKit version that created config |
| `github` | GitHubConfig | Yes | GitHub integration status |
| `cicd` | CICDConfig | Yes | CI/CD detection results |
| `gaps` | GapAnalysis | Yes | Missing infrastructure components |
| `history` | HistoryEntry[] | Yes | Audit trail of all actions |
| `target_configs` | TargetConfigs | No | Populated by `/popkit:deploy setup` |

### GitHub Config Fields

| Field | Type | Description |
|-------|------|-------------|
| `initialized` | boolean | Is git initialized in project? |
| `repo` | string \| null | GitHub repo in "owner/repo" format |
| `default_branch` | string \| null | Usually "main" or "master" |
| `has_actions` | boolean | Does `.github/workflows/` exist? |

### CI/CD Config Fields

| Field | Type | Description |
|-------|------|-------------|
| `detected` | boolean | Was any CI/CD platform found? |
| `platform` | CICDPlatform \| null | Which platform detected |
| `workflow_count` | number | Number of workflow files found |

### Gap Analysis Fields

| Field | Type | Description |
|-------|------|-------------|
| `needs_github` | boolean | True if no GitHub repo configured |
| `needs_cicd` | boolean | True if no CI/CD pipelines exist |
| `needs_target_configs` | boolean | True if targets not set up |

---

## Validation Rules

### Required Fields

All configs MUST have these fields:
- `version`
- `project_type`
- `language`
- `framework`
- `targets` (array with at least 1 target)
- `state`
- `initialized_at` (valid ISO 8601)
- `initialized_by`
- `github` (object with all required nested fields)
- `cicd` (object with all required nested fields)
- `gaps` (object with all required nested fields)
- `history` (array with at least 1 entry)

### Constraints

- `version` must be "1.0" (only supported version)
- `targets` must be non-empty array
- `history` must have at least one entry with `action: "init"`
- If `github.repo` is non-null, must match format "owner/repo"
- If `cicd.detected` is true, `cicd.platform` must be non-null
- `timestamp` fields must be valid ISO 8601 strings

### Gap Logic

Gap detection follows these rules:

```typescript
// GitHub gap
needs_github = !github.initialized || github.repo === null

// CI/CD gap
needs_cicd = !cicd.detected

// Target configs gap
needs_target_configs = targets.some(target => !target_configs?.[target])
```

---

## File Operations

### Reading Config

```bash
# Load config
config=$(cat .claude/popkit/deploy.json)

# Parse with jq
project_type=$(echo "$config" | jq -r '.project_type')
targets=$(echo "$config" | jq -r '.targets[]')
```

### Updating Config

Always append to history when modifying:

```bash
# Add history entry
jq '.history += [{
  "action": "setup",
  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
  "user": "'$(git config user.name)'",
  "version": "popkit-1.0.0"
}]' .claude/popkit/deploy.json > tmp.json && mv tmp.json .claude/popkit/deploy.json
```

### Validating Schema

Use JSON Schema validator or implement checks:

```typescript
function validateDeployConfig(config: any): boolean {
  // Check required fields
  const required = ['version', 'project_type', 'language', 'framework',
                    'targets', 'state', 'initialized_at', 'initialized_by',
                    'github', 'cicd', 'gaps', 'history'];

  for (const field of required) {
    if (!(field in config)) {
      console.error(`Missing required field: ${field}`);
      return false;
    }
  }

  // Check version
  if (config.version !== '1.0') {
    console.error(`Unsupported schema version: ${config.version}`);
    return false;
  }

  // Check targets non-empty
  if (!Array.isArray(config.targets) || config.targets.length === 0) {
    console.error('Targets must be non-empty array');
    return false;
  }

  // Check history has init entry
  const hasInit = config.history.some((entry: any) => entry.action === 'init');
  if (!hasInit) {
    console.error('History must contain at least one "init" entry');
    return false;
  }

  return true;
}
```

---

## Migration

### From No Config to v1.0

First-time initialization - no migration needed. Run `/popkit:deploy init`.

### Future Version Migrations

When schema changes in future versions (e.g., v2.0), migrations will be documented here.

**Example future migration:**

```typescript
function migrateV1ToV2(configV1: DeployConfigV1): DeployConfigV2 {
  return {
    ...configV1,
    version: "2.0",
    // Add new v2 fields with defaults
    environments: ["production"],
    // Transform changed fields
    // ...
  };
}
```

---

## Integration with Commands

### `/popkit:deploy init`

**Creates:** Initial config with detected values
**Updates:** Nothing (errors if config exists)
**Reads:** Project files for detection

### `/popkit:deploy setup`

**Creates:** `target_configs` section
**Updates:** `history` array with setup action
**Reads:** Entire config to know what to setup

### `/popkit:deploy validate`

**Creates:** Nothing
**Updates:** Nothing
**Reads:** Config to determine validation targets

### `/popkit:deploy execute`

**Creates:** Nothing
**Updates:** `history` array with deploy action
**Reads:** Config to determine deployment targets

### `/popkit:deploy rollback`

**Creates:** Nothing
**Updates:** `history` array with rollback action
**Reads:** Config and history to determine rollback target

---

## Security Considerations

### Sensitive Data

**Do NOT store sensitive data in deploy.json:**

❌ **Never include:**
- API keys
- Access tokens
- Passwords
- Private keys
- Database connection strings

✅ **Safe to store:**
- Project IDs (public identifiers)
- Registry URLs (public endpoints)
- Workflow file paths (code locations)
- Package names (public metadata)

Sensitive credentials should be stored as:
- GitHub Secrets (for CI/CD)
- Environment variables (for local dev)
- Secret management services (for production)

### File Permissions

Config file should be:
- ✅ Committed to git (it's project config, not secrets)
- ✅ Readable by team (shared configuration)
- ✅ Included in documentation (aids onboarding)

---

## Troubleshooting

### Config File Corrupted

```bash
# Validate JSON syntax
jq . .claude/popkit/deploy.json

# Re-initialize (loses history)
/popkit:deploy init --force
```

### Missing Required Fields

```bash
# Check for missing fields
jq 'keys' .claude/popkit/deploy.json

# Manually add missing field
jq '.github.repo = "owner/repo"' .claude/popkit/deploy.json > tmp.json
mv tmp.json .claude/popkit/deploy.json
```

### Invalid Timestamp Format

```bash
# Fix timestamp to ISO 8601
jq '.initialized_at = "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"' \
  .claude/popkit/deploy.json > tmp.json
mv tmp.json .claude/popkit/deploy.json
```

---

**Created:** 2025-12-15
**Author:** PopKit Deploy Team
**Status:** Active - v1.0 schema
