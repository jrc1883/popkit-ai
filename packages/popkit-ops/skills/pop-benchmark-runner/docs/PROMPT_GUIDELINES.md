# Writing Question-Free Benchmark Prompts

**Goal**: Design prompts that don't require user interaction during automated benchmarks

**Why**: Unattended execution requires prompts that provide ALL necessary context upfront

## Core Principle

**❌ Bad**: "Add authentication"
**✅ Good**: "Add JWT authentication using jsonwebtoken library with HS256 algorithm and 24-hour expiration"

## Guidelines

### 1. Be Extremely Specific

**❌ Vague**:

```
Add user authentication to the application
```

**✅ Specific**:

```
Add JWT authentication using the jsonwebtoken library (^9.0.0).

Implementation requirements:
- Algorithm: HS256
- Secret: Load from JWT_SECRET environment variable
- Token expiration: 24 hours
- Claims: { userId, email, role }
- Login endpoint: POST /auth/login (accepts email, password)
- Middleware: createAuthMiddleware() function
- Protected routes: All /api/* endpoints
- Error handling: 401 Unauthorized with {error: "message"} JSON

Do NOT ask for implementation preferences. Use these exact specifications.
```

### 2. Provide All Technical Details

**Include**:

- Library names and versions
- Configuration values
- File paths and locations
- Function/variable names
- Error handling requirements
- Testing requirements

**Example**:

```
Fix the race condition in src/services/payment-processor.js line 45.

Problem: Multiple concurrent payment requests can double-charge users.

Solution approach:
- Add Redis-based distributed lock using ioredis library
- Lock key format: payment:lock:{userId}:{orderId}
- Lock TTL: 30 seconds
- Retry logic: 3 attempts with 100ms exponential backoff
- If lock acquisition fails after retries, return 409 Conflict

Test coverage:
- Add test: concurrent_payments_should_not_double_charge
- Verify lock is released on success and failure
```

### 3. Specify "Do NOT Ask" Explicitly

Add a clear directive at the end of every prompt:

```
Do NOT ask me questions about:
- Implementation details
- Library choices
- Coding style
- Architecture decisions

Proceed immediately with the implementation using the specifications above.
```

### 4. Provide Defaults for Common Choices

**Common decision points**:

- Framework/library choices
- Database schema details
- API endpoint paths
- Configuration values
- Error handling approach
- Testing strategy

**Example**:

```
Add real-time notifications using WebSocket.

Defaults (use these without asking):
- Library: ws (npm package)
- Port: 8081
- Path: /ws
- Authentication: JWT token in connection query string
- Message format: JSON with {type, payload} structure
- Reconnection: Client-side with exponential backoff
- Testing: Use ws library's test client
```

### 5. Structure for Clarity

Use clear sections:

```markdown
# Task: [Brief title]

## Problem

[What needs to be fixed/added]

## Implementation Requirements

- Requirement 1
- Requirement 2
- ...

## Technical Specifications

- Library: [name]
- Configuration: [details]
- File locations: [paths]

## Success Criteria

- [Criterion 1]
- [Criterion 2]

## DO NOT ASK

Proceed immediately without asking about implementation choices.
Use the specifications above.
```

## Real-World Examples

### Example 1: Feature Addition

**❌ Bad**:

```
Add caching to the API
```

**✅ Good**:

```
Add Redis caching to the REST API to reduce database load.

Implementation:
- Install ioredis (^5.3.0)
- Create src/lib/redis-client.js with connection logic
- Connection: redis://localhost:6379 (configurable via REDIS_URL env)
- Middleware: cacheMiddleware(ttlSeconds) function
- Apply to: GET /api/users, GET /api/posts, GET /api/comments
- Cache key format: api:{method}:{path}:{queryString}
- TTL: 300 seconds (5 minutes)
- Invalidation: On POST/PUT/DELETE to same resource
- Error handling: If Redis unavailable, log warning and proceed without cache

Tests:
- cache_hit_returns_cached_data
- cache_miss_queries_database
- cache_invalidated_on_update

Do NOT ask about caching strategy, TTL values, or Redis configuration.
Proceed with these specifications.
```

### Example 2: Bug Fix

**❌ Bad**:

```
Fix the memory leak in the server
```

**✅ Good**:

```
Fix memory leak in src/server.js caused by unclosed WebSocket connections.

Root cause:
- Line 78: WebSocket 'close' event listener never removes connection from
  activeConnections Map
- Results in memory growth of ~50MB per 1000 connections

Solution:
- Add cleanup in 'close' event handler:
  ws.on('close', () => {
    activeConnections.delete(connectionId);
    logger.debug(`Connection ${connectionId} cleaned up`);
  });

Verification:
- Run memory profiler: node --inspect src/server.js
- Simulate 10,000 connections: npm run test:stress
- Verify activeConnections.size returns to 0 after all close
- Memory should stabilize below 200MB

Test:
- Add: websocket_connections_cleaned_up_on_close
- Check activeConnections Map size before and after

Do NOT ask about alternative cleanup approaches. Use the solution above.
```

### Example 3: Refactoring

**❌ Bad**:

```
Refactor the authentication code
```

**✅ Good**:

```
Refactor authentication code in src/auth/ directory to use dependency injection.

Current structure (bad):
- auth/login.js directly imports db, redis, logger
- Hard to test, tightly coupled

Target structure:
- Create auth/AuthService.js class
- Constructor accepts: { db, redis, logger }
- Methods: login(), logout(), verifyToken()
- auth/login.js uses AuthService instance

Specific changes:
1. Create src/auth/AuthService.js with constructor and methods
2. Update src/auth/login.js to accept authService parameter
3. Update src/server.js to instantiate AuthService and inject
4. Keep same function signatures (no breaking changes)
5. Tests: Update to pass mock dependencies to AuthService

Files to modify:
- src/auth/AuthService.js (new)
- src/auth/login.js (refactor)
- src/auth/logout.js (refactor)
- src/auth/verify.js (refactor)
- src/server.js (DI setup)
- tests/auth/*.test.js (update mocks)

Do NOT ask about DI patterns or architecture preferences.
Follow the structure above exactly.
```

### Example 4: Performance Optimization

**❌ Bad**:

```
Optimize the database queries
```

**✅ Good**:

```
Optimize slow database query in src/api/users.js line 45.

Current problem:
- Query: SELECT * FROM users LEFT JOIN posts LEFT JOIN comments
- Takes 2.5s for 10,000 users
- N+1 query pattern in loop

Solution:
1. Add database index:
   CREATE INDEX idx_posts_user_id ON posts(user_id);
   CREATE INDEX idx_comments_post_id ON comments(post_id);

2. Replace with single query using proper JOINs:
   SELECT u.*, p.*, c.*
   FROM users u
   LEFT JOIN posts p ON u.id = p.user_id
   LEFT JOIN comments c ON p.id = c.post_id
   WHERE u.created_at > $1

3. Implement pagination:
   - Limit: 50 users per page
   - Offset: (page - 1) * 50
   - Add &page=N to API endpoint

4. Add query result caching (5 minutes TTL)

Performance target:
- Query execution: < 100ms
- API response: < 200ms
- Memory usage: < 50MB

Verification:
- Run: npm run benchmark:db
- Check: Query execution time logged
- Test: Load 10,000 users scenario

Do NOT ask about optimization strategy. Implement the solution above.
```

## Common Pitfalls

### Pitfall 1: Assuming Context

**❌ Wrong**:

```
Fix the bug we discussed earlier
```

**✅ Right**:

```
Fix the race condition in payment-processor.js line 45 where concurrent
requests can double-charge users. Use Redis distributed locks.
```

### Pitfall 2: Open-Ended Requirements

**❌ Wrong**:

```
Add better error handling
```

**✅ Right**:

```
Add error handling to API routes:
- Wrap all async route handlers with asyncHandler() middleware
- Return 400 for validation errors with {error, fields} JSON
- Return 500 for uncaught errors with {error} JSON (hide stack in prod)
- Log all errors to console.error() with request ID
```

### Pitfall 3: Missing Technical Details

**❌ Wrong**:

```
Add unit tests
```

**✅ Right**:

```
Add unit tests for src/services/payment-processor.js:
- Framework: Jest (already installed)
- Coverage target: 90%
- Test file: tests/services/payment-processor.test.js
- Mock: database using jest.mock('../db')
- Test cases:
  - successful_payment_processing
  - invalid_card_returns_error
  - network_timeout_retries_3_times
  - concurrent_payments_use_locks
```

## Template

Use this template for all benchmark tasks:

```
# [Task Title]

## Objective
[One-sentence description]

## Problem/Context
[What needs to be done and why]

## Implementation Requirements

### Technical Specifications
- Library/Framework: [name + version]
- Files to modify: [paths]
- Configuration: [details]
- Dependencies: [npm packages]

### Code Details
- Function names: [exact names]
- Variable names: [exact names]
- File structure: [paths]
- Error handling: [approach]

### Success Criteria
- [Measurable criterion 1]
- [Measurable criterion 2]

### Testing
- Test file: [path]
- Test cases: [list]
- Coverage target: [percentage]

## DO NOT ASK
Proceed immediately without questions. Use the specifications above.
```

## Validation Checklist

Before using a prompt in benchmarks, verify:

- [ ] All library names and versions specified
- [ ] All configuration values provided
- [ ] All file paths explicitly stated
- [ ] All function/variable names given
- [ ] Error handling approach detailed
- [ ] Testing requirements clear
- [ ] "Do NOT ask" directive included
- [ ] No open-ended choices left
- [ ] No assumptions about context
- [ ] Prompt tested with and without PopKit

## Testing Your Prompt

### Test 1: Read Aloud

Read the prompt out loud. Can someone implement it without asking ANY clarifying questions?

### Test 2: Give to Another Developer

Have a colleague read it. What would they ask? Add those answers to the prompt.

### Test 3: Run Without PopKit

```bash
claude plugin disable popkit-core popkit-dev popkit-ops
claude -p "$(cat tasks/my-task/task.yml | yq .user_prompt)"
```

Did it block on any questions? If yes, revise prompt.

### Test 4: Run With Benchmark Mode

```bash
export POPKIT_BENCHMARK_MODE=true
export POPKIT_BENCHMARK_RESPONSES=tasks/my-task/responses.json
/popkit-ops:benchmark run my-task --trials 1 --verbose
```

Check logs - were any questions auto-answered? Those should be in the prompt instead.

## See Also

- `RESPONSE_FILE_SCHEMA.md` - Automated responses format
- `TASK_DEFINITION_SCHEMA.md` - Complete task YAML reference
- Example tasks in `tasks/` directory
