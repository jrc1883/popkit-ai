# E2B.dev Integration Research

**Date:** 2025-12-09
**Issue:** #122
**Status:** Research Complete

---

## Executive Summary

E2B.dev provides cloud sandboxes ideal for running isolated, reproducible benchmarks. The free tier ($100 credit) is sufficient for initial development. For sustained benchmarking, the Pro tier ($150/month) provides longer sessions and more concurrent sandboxes.

**Recommendation:** Use E2B for automated benchmark execution, starting with manual testing on the Hobby tier.

---

## 1. Pricing Analysis

### Tiers

| Tier | Cost | Session Limit | Concurrent Sandboxes | Credit Card |
|------|------|---------------|----------------------|-------------|
| **Hobby** | Free ($100 credit) | 1 hour | 20 | Not required |
| **Pro** | $150/month | 24 hours | 100 | Required |
| **Ultimate** | Custom | Custom | Custom | Enterprise |

### Usage Costs (per second)

| Resource | Cost |
|----------|------|
| CPU (1 vCPU) | $0.000014/sec |
| CPU (8 vCPU) | $0.000112/sec |
| RAM | $0.0000045/GiB/sec |
| Storage | 10 GiB free (Hobby), 20 GiB free (Pro) |

### Cost Estimation

For a typical benchmark run (5 minutes, 1 vCPU, 1 GiB RAM):
- CPU: 300 sec × $0.000014 = $0.0042
- RAM: 300 sec × $0.0000045 = $0.00135
- **Total per run:** ~$0.006

With $100 free credit: **~16,000 benchmark runs**

For sustained benchmarking (1000 runs/month):
- Monthly cost: ~$6 in usage
- Pro tier adds $150/month (for 24h sessions, 100 concurrent)

### Conclusion

**Hobby tier is sufficient for development and initial benchmarking.**
Pro tier needed only for:
- Benchmarks lasting >1 hour
- Running 20+ benchmarks concurrently
- Production/CI integration

---

## 2. API Capabilities

### Sandbox Management

```typescript
import { Sandbox } from '@e2b/code-interpreter';

// Create sandbox (default 5 min timeout)
const sbx = await Sandbox.create();

// Create with custom timeout
const sbx = await Sandbox.create({ timeout: 600 }); // 10 minutes

// Close sandbox
await sbx.close();
```

### File System Operations

```typescript
// Write file
await sbx.files.write('/path/to/file.ts', 'content');

// Read file
const content = await sbx.files.read('/path/to/file.ts');

// List directory
const files = await sbx.files.list('/');

// Delete file
await sbx.files.remove('/path/to/file.ts');
```

### Code Execution

```typescript
// Run code directly
const result = await sbx.runCode('print("hello")');
console.log(result.logs);   // stdout/stderr
console.log(result.error);  // any errors
console.log(result.results); // execution results

// Run terminal commands
const proc = await sbx.commands.run('npm install');
console.log(proc.stdout);
console.log(proc.stderr);
console.log(proc.exitCode);
```

### Network & Environment

```typescript
// Sandbox has internet access by default
// Can install packages
await sbx.commands.run('pip install requests');
await sbx.commands.run('npm install typescript');

// Environment variables
const sbx = await Sandbox.create({
  envs: {
    API_KEY: 'xxx',
  },
});
```

### Supported Languages

| Language | Support | Notes |
|----------|---------|-------|
| Python | ✅ Full | Native code interpreter |
| JavaScript | ✅ Full | Via Node.js |
| TypeScript | ✅ Full | Via tsx/ts-node |
| Bash | ✅ Full | Native shell |
| R | ✅ Basic | Requires custom template |
| Java | ✅ Basic | Requires custom template |

---

## 3. Integration Challenges

### Challenge 1: Running AI Tools Inside Sandbox

**Problem:** We need to run Claude/Cursor/Codex inside the sandbox, but these tools require:
- API keys (security concern)
- Interactive CLI sessions
- Complex setup

**Solutions:**

1. **API-based approach** (Recommended)
   - Sandbox provides isolated execution environment only
   - AI tool runs externally, sends code to sandbox
   - Sandbox executes and returns results

2. **CLI installation approach**
   - Install Claude Code CLI in sandbox
   - Pass API key as environment variable
   - Run full benchmark inside sandbox

3. **Hybrid approach**
   - Sandbox prepares environment
   - External script orchestrates AI interaction
   - Sandbox verifies results

**Recommended:** API-based approach - AI tool runs locally/externally, sandbox provides clean execution environment.

### Challenge 2: Token Counting

**Problem:** E2B doesn't track AI API token usage.

**Solution:** Use our MetricsCollector externally. E2B only handles code execution, not AI interaction.

### Challenge 3: Timeout Management

**Problem:** Complex benchmarks may exceed limits.

**Solution:**
- Hobby: 1 hour max (sufficient for most benchmarks)
- Pro: 24 hours for complex scenarios
- Implement checkpoint/resume for very long tasks

---

## 4. Architecture Decision

### Option A: Full E2B Integration
```
┌─────────────────────────────────────────────────┐
│                 Benchmark Runner                 │
├─────────────────────────────────────────────────┤
│  1. Create E2B Sandbox                          │
│  2. Upload initial files                        │
│  3. Call AI tool API with task prompt           │
│  4. AI generates code, sends to sandbox         │
│  5. Execute code in sandbox                     │
│  6. Run tests in sandbox                        │
│  7. Extract results, close sandbox              │
└─────────────────────────────────────────────────┘
```

**Pros:** Fully isolated, reproducible, automated
**Cons:** More complex, requires E2B account/credits

### Option B: Manual Testing with E2B
```
┌─────────────────────────────────────────────────┐
│              Manual Benchmark Flow               │
├─────────────────────────────────────────────────┤
│  1. Researcher creates E2B sandbox manually     │
│  2. Runs AI tool locally with task prompt       │
│  3. Copies generated code to sandbox            │
│  4. Runs tests in sandbox                       │
│  5. Records results manually                    │
└─────────────────────────────────────────────────┘
```

**Pros:** Simple, no integration code needed
**Cons:** Not automated, harder to reproduce

### Option C: Local Docker (No E2B)
```
┌─────────────────────────────────────────────────┐
│               Local Docker Flow                  │
├─────────────────────────────────────────────────┤
│  1. Spin up local Docker container              │
│  2. Run AI tool with task prompt                │
│  3. Execute in container                        │
│  4. Record results                              │
└─────────────────────────────────────────────────┘
```

**Pros:** Free, no external dependencies
**Cons:** Less isolated, harder to standardize across machines

### Recommendation: Hybrid (Option A for CI, Option C for local dev)

- **Local development:** Docker containers for quick iteration
- **CI/Production:** E2B for standardized, reproducible benchmarks
- **Keep E2B integration optional:** Not everyone needs cloud sandboxes

---

## 5. Proof of Concept

### E2B POC Script

Located at: `packages/benchmarks/src/e2b/poc.ts`

```typescript
// Proof of concept for E2B integration
// Run with: E2B_API_KEY=xxx npx tsx packages/benchmarks/src/e2b/poc.ts

import { Sandbox } from '@e2b/code-interpreter';

async function runBenchmarkPOC() {
  console.log('Creating E2B sandbox...');
  const sbx = await Sandbox.create({ timeout: 300 });

  try {
    // Write a simple task file
    await sbx.files.write('/task/index.js', `
      function add(a, b) {
        return a + b;
      }
      console.log('Testing add function...');
      console.log('2 + 3 =', add(2, 3));
      console.log('Test passed:', add(2, 3) === 5);
    `);

    // Execute the code
    const result = await sbx.commands.run('node /task/index.js');

    console.log('Output:', result.stdout);
    console.log('Exit code:', result.exitCode);
    console.log('Success:', result.exitCode === 0);

  } finally {
    await sbx.close();
    console.log('Sandbox closed.');
  }
}

runBenchmarkPOC().catch(console.error);
```

### Running the POC

1. Get E2B API key from https://e2b.dev/dashboard
2. Run: `E2B_API_KEY=xxx npx tsx packages/benchmarks/src/e2b/poc.ts`

---

## 6. Implementation Roadmap

### Phase 1: Foundation (Current)
- [x] Research E2B capabilities
- [x] Document findings
- [x] Create POC script
- [ ] Test POC with real E2B account

### Phase 2: Basic Integration
- [ ] Create `E2BRunner` class
- [ ] Integrate with `BenchmarkTask` schema
- [ ] Add E2B as optional dependency

### Phase 3: Full Integration
- [ ] Docker fallback for local dev
- [ ] CI pipeline integration
- [ ] Automated benchmark scheduling

---

## 7. Conclusion

### Decision: Proceed with E2B Integration

**Rationale:**
1. Free tier sufficient for development
2. API is well-documented and easy to use
3. Provides reproducible, isolated execution
4. Not required for basic usage (Docker fallback)

### Next Steps

1. Create `packages/benchmarks/src/e2b/` module
2. Implement optional E2B runner
3. Keep Docker-based runner as fallback
4. Document setup requirements

---

## References

- E2B Documentation: https://e2b.dev/docs
- E2B Pricing: https://e2b.dev/pricing
- E2B GitHub: https://github.com/e2b-dev/e2b
- E2B SDK: `@e2b/code-interpreter`
