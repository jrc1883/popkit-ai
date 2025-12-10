# Claude Task Master - Technical Research Notes

**Author:** PopKit Research Team
**Date:** December 2025
**Repository:** https://github.com/eyaltoledano/claude-task-master (v0.37.1)

---

## Architecture Layers

### Layer 1: Core Business Logic (@tm/core)

The entire business logic is isolated in `packages/tm-core/src/modules/`. This package is the **single source of truth** for all operations.

**16 Domain Modules:**

1. **ai/** - Provider abstraction layer
   - Unified interface across 20+ LLM providers
   - Vercel AI SDK wrapper
   - Model configuration management
   - Request/response normalization

2. **auth/** - Authentication system
   - OAuth flows (Google, GitHub)
   - Supabase integration
   - Session management
   - Team access control

3. **tasks/** - Core task domain
   - Task CRUD operations
   - Task ID parsing (supports "1", "1.2", "HAM-123")
   - Subtask management
   - Status transitions
   - Task filtering and search

4. **dependencies/** - Dependency resolution
   - Circular dependency detection
   - Critical path analysis
   - Dependency validation
   - Transitive closure calculation

5. **workflow/** - Workflow orchestration
   - 7-phase workflow execution
   - Phase state management
   - Checkpoint management
   - Workflow resumption

6. **config/** - Configuration management
   - Model configuration loading
   - Merge strategy (defaults + overrides)
   - Validation with Zod
   - Type-safe config access

7. **storage/** - Data persistence
   - FileStorage adapter (JSON)
   - Supabase adapter (cloud)
   - Abstract storage interface
   - Tag-based task organization

8. **git/** - Git integration
   - Commit message generation
   - Branch context detection
   - Repository status checking
   - Staged changes analysis

9. **integration/** - External integrations
   - Hamster brief export/import
   - Task → Brief reverse engineering
   - Cloud synchronization
   - Cross-platform export

10. **reports/** - Reporting system
    - Complexity analysis
    - Report generation
    - Metrics calculation
    - Export to JSON

11. **execution/** - Task execution
    - Task lifecycle management
    - Status transitions
    - Dependency blocking
    - Execution hooks

12. **briefs/** - Team collaboration
    - Hamster brief management
    - Team member invitations
    - Shared context creation
    - Real-time sync

13. **prompts/** - Prompt engineering
    - Upgrade prompt management
    - Contextual suggestions
    - Trigger-based evaluation
    - A/B testing support

14. **commands/** - Command definition
    - Command schema
    - Argument parsing
    - Validation
    - Routing

15. **ui/** - Terminal UI utilities
    - Color formatting with chalk
    - Table rendering
    - Progress indicators
    - Error formatting

16. **common/** - Shared utilities
    - Error codes and handling
    - Logger setup
    - Type interfaces
    - Constants

### Layer 2: Presentation (@tm/cli, @tm/mcp)

**CLI (`apps/cli/src`):**
- Thin presentation layer
- Commander.js for argument parsing
- Calls @tm/core methods
- Formats output for terminal display
- NO business logic

**MCP Server (`apps/mcp/src`):**
- FastMCP-based stdio server
- Tool schema definition
- Parameter validation
- Response formatting
- NO business logic

**Key Principle:** If logic appears in CLI or MCP, it belongs in @tm/core.

---

## Critical Architectural Patterns

### 1. Domain Module Pattern

Each domain has a consistent structure:

```
modules/<domain>/
├── <domain>-domain.ts      # Public facade class
├── services/               # Business logic
│   ├── <feature>-service.ts
│   └── <feature>-service.spec.ts
├── repositories/          # Data access (if needed)
├── interfaces/            # Domain types
└── index.ts              # Exports
```

**Example: TasksDomain**
```typescript
export class TasksDomain {
  // Public methods - CLI/MCP call these
  async get(taskId: string): Promise<Task>
  async list(options?: FilterOptions): Promise<Task[]>
  async create(task: CreateTaskInput): Promise<Task>
  async update(taskId: string, updates: Partial<Task>): Promise<Task>
  // ... more methods
}
```

### 2. Dependency Injection Pattern

Core domains are composed in `tm-core.ts`:

```typescript
export class TmCore {
  auth: AuthDomain
  config: ConfigDomain
  tasks: TasksDomain
  workflow: WorkflowDomain
  // ... all domains
}

// Usage in CLI/MCP:
const tmcore = await createTmCore({ projectPath })
const tasks = await tmcore.tasks.list()
```

### 3. Storage Adapter Pattern

```typescript
interface IStorage {
  getTasks(tag: string): Promise<Task[]>
  saveTasks(tag: string, tasks: Task[]): Promise<void>
}

class FileStorage implements IStorage { ... }
class SupabaseStorage implements IStorage { ... }

// Switched at runtime based on config
```

### 4. Error Handling Pattern

```typescript
enum ERROR_CODES {
  TASK_NOT_FOUND = 'TASK_NOT_FOUND',
  CIRCULAR_DEPENDENCY = 'CIRCULAR_DEPENDENCY',
  // ...
}

throw new TaskMasterError(
  'Task not found',
  ERROR_CODES.TASK_NOT_FOUND,
  { taskId }
)
```

---

## Multi-Model Integration Architecture

### Provider Registry

Claude Task Master uses **Vercel AI SDK** as the abstraction layer over 20+ providers.

```typescript
// Available providers
const providers = {
  'anthropic': claude(),           // Claude 3.5+
  'openai': openai(),              // GPT-4o, o3
  'google': google(),              // Gemini
  'groq': groq(),                  // LLaMA, Mixtral
  'perplexity': perplexity(),      // Sonar, web search
  'mistral': mistral(),            // Mistral models
  'openrouter': openRouter(),      // Proxy to 100+ models
  'ollama': ollama(),              // Local models
  'bedrock': bedrock(),            // AWS Claude
  'azure-openai': azureOpenai(),   // Azure deployment
  // ... 10+ more
}
```

### Model Selection Flow

```
1. User configures models via: task-master models --setup
2. Config saved to: .taskmasterconfig + .env

3. At runtime:
   - Load configuration
   - Select provider from config
   - Instantiate model: language = provider.model(config)
   - Execute: generateText(language, prompt)

4. On failure:
   - Try main model
   - If fails, try research model
   - If fails, try fallback model
   - If all fail, throw error
```

### Configuration Structure

```json
{
  "models": {
    "main": {
      "provider": "anthropic",
      "modelId": "claude-opus-4-5",
      "maxTokens": 64000,
      "temperature": 0.2,
      "topP": 1.0,
      "topK": 40
    },
    "research": {
      "provider": "perplexity",
      "modelId": "sonar-pro",
      "maxTokens": 8700,
      "temperature": 0.3
    },
    "fallback": {
      "provider": "anthropic",
      "modelId": "claude-3-5-sonnet",
      "maxTokens": 16000
    }
  }
}
```

---

## Task Management System Deep Dive

### Task ID Parsing

Task Master supports multiple ID formats:

```typescript
// Format 1: Simple numeric
"1"           → { taskId: 1 }

// Format 2: Subtask notation
"1.2"         → { taskId: 1, subtaskId: 2 }
"1.2.3"       → { taskId: 1, subtaskId: 2, subSubtaskId: 3 }

// Format 3: Custom ID format (future)
"HAM-123"     → { customId: "HAM-123" }
"HAM-123.2"   → { customId: "HAM-123", subtaskId: 2 }
```

### Task Status State Machine

```
       ┌─────────────┐
       │   pending   │
       └──────┬──────┘
              │
              ▼
       ┌─────────────────┐
       │   in-progress   │
       └────────┬────────┘
                │
       ┌────────┴─────────┐
       ▼                  ▼
   ┌────────┐        ┌─────────┐
   │  done  │        │  review │
   └────────┘        └────┬────┘
                          │
                     ┌────┴─────┐
                     ▼          ▼
                   done    deferred

Special statuses: cancelled (any → cancelled)
```

### Complexity Analysis Algorithm

```
Input: Task title + description
↓
Analyze with AI using complexity prompt
↓
Dimensions evaluated:
  - Technical effort (1-10)
  - Testing complexity (1-10)
  - Integration risk (1-10)
  - Interdependencies (1-10)
↓
Aggregate to single 1-10 score
↓
Recommend subtask count:
  - Score 1-3: 0-1 subtasks
  - Score 4-6: 2-3 subtasks
  - Score 7-10: 4-5+ subtasks
↓
Generate customized expansion prompt
↓
Output: JSON report with recommendations
```

### Subtask Generation

**Standard Mode:**
```
Main Model Process:
1. Load task context (title, description, parent details)
2. Prompt: "Break down task X into N subtasks"
3. Generate subtasks with details and test strategy
4. Save to task.subtasks[]
```

**Research Mode:**
```
Dual Model Process:
1. Use Research Model (Perplexity):
   "Research best practices for: [task context]"
2. Use Main Model:
   "Generate subtasks informed by research: [research results]"
3. Merge findings into subtasks
4. Save to task.subtasks[]
```

---

## Multi-Tag Task Organization

### Tag System Architecture

```
tasks.json (new format):
{
  "master": {
    "tasks": [...],
    "metadata": {
      "createdAt": "2025-01-01",
      "description": "Main development"
    }
  },
  "feature-auth": {
    "tasks": [...],
    "metadata": { ... }
  },
  "v2-redesign": {
    "tasks": [...],
    "metadata": { ... }
  }
}
```

### Tag Use Cases

1. **Branch Tracking:** One tag per git branch
   - feature-auth (auth branch)
   - fix-performance (perf branch)
   - main (production branch)

2. **Milestone Tracking:** One tag per milestone
   - v1.0
   - v1.1
   - v2.0

3. **Context Isolation:** Different project contexts
   - project-a
   - project-b
   - experimental

### Tag Operations

```bash
# Switch current tag
task-master context set feature-auth

# List all tags
task-master context list

# Move task across tags
task-master move --id=5 --from=main --to=feature-auth

# Cross-tag dependencies (with validation)
task-master add-dependency --id=5 --depends-on=main:3
```

---

## Workflow Orchestration

### 7-Phase Workflow Model

```
Phase 1: DISCOVERY
├── Understand requirements
├── Ask clarifying questions
└── Output: Requirements summary

Phase 2: EXPLORATION
├── Analyze codebase
├── Identify affected areas
└── Output: Impact analysis

Phase 3: QUESTIONS
├── Clarify ambiguities
├── Validate assumptions
└── Output: Decision matrix

Phase 4: ARCHITECTURE
├── Design solution
├── Identify risks
└── Output: Architecture document

Phase 5: IMPLEMENTATION
├── Code development
├── Unit testing
└── Output: Implementation

Phase 6: REVIEW
├── Code review
├── Integration testing
└── Output: Review comments

Phase 7: SUMMARY
├── Documentation
├── Release notes
└── Output: Summary
```

### Workflow State Management

```json
{
  "currentTag": "feature-auth",
  "session": {
    "phase": 2,
    "phaseName": "exploration",
    "taskId": 5,
    "startedAt": "2025-01-15T10:30:00Z",
    "completedPhases": [1],
    "checkpoint": {
      "analysis": "...",
      "findings": ["...", "..."]
    }
  }
}
```

---

## LLM Integration Patterns

### AI Module Architecture

```
ai/
├── providers/
│   ├── anthropic-provider.ts
│   ├── openai-provider.ts
│   ├── perplexity-provider.ts
│   └── ... (17 more)
├── services/
│   ├── ai-orchestrator.ts        # Main coordinator
│   ├── model-selector.ts          # Choose right model
│   ├── token-calculator.ts        # Count tokens
│   └── fallback-handler.ts        # Graceful degradation
└── index.ts
```

### Prompt Engineering

**Prompt Template Structure:**
```json
{
  "id": "parse-prd",
  "name": "Parse PRD into Tasks",
  "version": "1.0",
  "schema": {
    "input": {
      "prd": "string",
      "numTasks": "number",
      "format": "structured"
    },
    "output": {
      "tasks": [
        {
          "id": "number",
          "title": "string",
          "description": "string",
          "dependencies": ["number"],
          "priority": "enum"
        }
      ]
    }
  },
  "instructions": "...",
  "examples": [...]
}
```

### Token Optimization

```typescript
// Estimated token usage
const tokenEstimate = (
  promptTokens +          // Prompt tokens
  estimatedOutputTokens +  // Expected response (using gpt-tokens)
  bufferTokens            // Safety buffer (10%)
)

// If exceeds limit, fallback to research model with summarization
if (tokenEstimate > model.maxTokens) {
  return fallbackModel.generate(summarizedPrompt)
}
```

---

## CLI Command Architecture

### Command Structure

```
apps/cli/src/commands/
├── index.ts              # Command factory
├── init.ts               # Initialize project
├── parse-prd.ts          # Parse requirements
├── list.ts               # List tasks
├── show.ts               # Show task details
├── set-status.ts         # Update task status
├── expand.ts             # Generate subtasks
├── analyze-complexity.ts # Analyze task complexity
├── complexity-report.ts  # Display report
├── add-dependency.ts     # Add task dependency
├── remove-dependency.ts  # Remove dependency
├── validate-dependencies # Validate dependencies
├── fix-dependencies.ts   # Auto-repair dependencies
├── add-task.ts           # Create new task
├── update-task.ts        # Modify task
├── models.ts             # Configure models
├── workflow/             # Workflow commands
│   ├── start.ts
│   ├── status.ts
│   ├── resume.ts
│   ├── complete.ts
│   └── abort.ts
└── team/                 # Team commands
    ├── export.ts
    ├── briefs.ts
    └── context.ts
```

### Command Execution Flow

```
User: task-master expand --id=5 --num=3
  ↓
Commander.js parses arguments
  ↓
ValidationService validates:
  - Task exists
  - Task not already expanded
  - Num is valid (1-10)
  ↓
ComplexityService (if needed):
  - Load complexity report
  - Get recommended prompt
  ↓
ExpansionService:
  - Select model (main or research)
  - Generate subtasks
  - Validate output
  ↓
TasksDomain.update():
  - Merge subtasks into task
  - Save to storage
  ↓
Output results to CLI
  ↓
Exit with success code
```

---

## MCP Server Integration

### Tool Schema Design

**Tool Definition:**
```json
{
  "name": "expand_task",
  "description": "Generate subtasks for a task",
  "inputSchema": {
    "type": "object",
    "properties": {
      "taskId": {
        "type": "string",
        "description": "Task ID (e.g., '5' or '5.2')"
      },
      "numSubtasks": {
        "type": "integer",
        "description": "Number of subtasks (1-10)",
        "minimum": 1,
        "maximum": 10
      },
      "research": {
        "type": "boolean",
        "description": "Use research model (Perplexity)"
      }
    },
    "required": ["taskId"]
  }
}
```

### Tool Execution Pipeline

```
IDE User Input
  ↓
FastMCP receives tool call
  ↓
ValidateInputSchema using Zod
  ↓
CheckAuthorization (if Supabase user)
  ↓
Call corresponding TmCore method
  ↓
Format response (JSON/text)
  ↓
Return to IDE
```

### Tool Set Configuration

```bash
# Environment variable in MCP config
TASK_MASTER_TOOLS=core        # 7 tools, ~5k tokens
TASK_MASTER_TOOLS=standard    # 15 tools, ~10k tokens
TASK_MASTER_TOOLS=all         # 36 tools, ~21k tokens
```

---

## Storage & Persistence

### File Storage Adapter

```typescript
class FileStorage implements IStorage {
  async getTasks(tag: string): Promise<Task[]> {
    // 1. Load tasks.json
    // 2. Extract tasks[tag]
    // 3. Parse and validate with Zod
    // 4. Return
  }

  async saveTasks(tag: string, tasks: Task[]): Promise<void> {
    // 1. Load existing tasks.json
    // 2. Merge new tasks[tag]
    // 3. Validate entire structure
    // 4. Write back (atomic)
    // 5. Create backup (git commit)
  }
}
```

### Supabase Storage Adapter

```typescript
class SupabaseStorage implements IStorage {
  async getTasks(tag: string): Promise<Task[]> {
    // 1. Query Supabase tasks table
    // 2. Filter by:
    //    - user_id = authenticated user
    //    - tag = requested tag
    // 3. Return
  }

  async saveTasks(tag: string, tasks: Task[]): Promise<void> {
    // 1. Begin transaction
    // 2. Delete existing tasks for tag
    // 3. Insert new tasks
    // 4. Update updated_at timestamp
    // 5. Commit transaction
  }
}
```

---

## Testing Architecture

### Test Organization

```
tests/
├── unit/                  # Isolated unit tests
│   ├── modules/
│   │   ├── tasks/
│   │   │   ├── tasks-domain.spec.ts
│   │   │   └── services/
│   │   │       └── task-service.spec.ts
│   │   └── ai/
│   │       └── ai-orchestrator.spec.ts
│   └── common/
│       └── logger.spec.ts
├── integration/          # Multi-unit tests
│   ├── workflow/
│   │   └── full-workflow.test.ts
│   └── storage/
│       └── file-storage.test.ts
└── e2e/                 # End-to-end tests
    ├── cli/
    │   └── parse-prd-e2e.test.ts
    └── mcp/
        └── expand-task-e2e.test.ts
```

### Test Strategy

**Unit Tests:**
- Mock @tm/core services
- Test CLI/MCP I/O only
- Test prompt validation
- Test option parsing

**Integration Tests:**
- Use real tm-core
- Mock external APIs (Supabase, Perplexity)
- Test domain interactions
- Test storage persistence

**E2E Tests:**
- Full CLI commands
- Real file I/O
- Mocked external APIs
- Bash-based for CLI

---

## Version & Dependencies

### Key Dependencies

**Core Frameworks:**
- TypeScript 5.9+ (strict mode)
- Node.js 20+
- ESM modules only
- Turbo for monorepo orchestration

**AI & LLM:**
- @ai-sdk/anthropic (Claude)
- @ai-sdk/openai (GPT)
- @ai-sdk/google (Gemini)
- @ai-sdk/perplexity (Sonar)
- @ai-sdk/provider (base abstractions)
- 15+ other provider SDKs

**CLI & UI:**
- Commander.js (argument parsing)
- Inquirer.js (interactive prompts)
- Chalk (colors)
- Ora (spinners)
- CLI-Table3 (tables)
- Marked (markdown parsing)

**Storage:**
- Supabase (cloud storage)
- fs-extra (file operations)
- Steno (atomic writes)
- Simple-git (Git operations)

**Utilities:**
- Zod (validation)
- uuid (ID generation)
- date-fns (dates)
- Lru-cache (caching)
- gpt-tokens (token counting)

### Monorepo Structure

```
Workspaces:
├── packages/tm-core       # Core business logic (@tm/core)
├── packages/tm-bridge     # Cloud integration (@tm/bridge)
├── packages/build-config  # Shared build config (@tm/build-config)
├── apps/cli               # CLI application (@tm/cli)
├── apps/mcp               # MCP server (@tm/mcp)
├── apps/docs              # Documentation (Mintlify)
└── apps/extension         # VS Code extension (future)
```

---

## Conclusion

Claude Task Master demonstrates:

1. **Clean Architecture:** Strict separation of business logic, presentation, and data layers
2. **Scalability:** Domain-driven design with 16 independent modules
3. **Flexibility:** Support for 20+ LLM providers through abstraction layer
4. **Sophistication:** Advanced features (complexity analysis, research integration, team collaboration)
5. **Maturity:** Production-ready with comprehensive testing and documentation

**Key Learning for PopKit:** Task Master's architecture provides a blueprint for how to structure multi-domain systems while maintaining clean separation of concerns.
