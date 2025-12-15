# Prompt Parity Investigation - 2025-12-15

## Critical Discovery: Unfair Benchmark Comparison

### The Problem

Benchmarks were comparing PopKit vs Vanilla, but **they received completely different prompts**:

**PopKit received (4 words):**
```
/popkit:dev "create bouncing balls animation"
```

**Vanilla received (Full specification):**
```
This is a vanilla JavaScript task. No frameworks or build tools required.

Create a web page with a canvas showing 5 balls bouncing with realistic physics. Requirements:
1. Each ball should have a random color and size (10-30px radius)
2. Balls should start at random positions with random velocities
3. Balls should bounce off the walls (canvas edges) with proper reflection
4. Balls should collide with each other (basic collision detection)
5. Use requestAnimationFrame for smooth animation
6. Add gravity (balls should fall and bounce)
```

### Impact on Results

This explains the quality difference we observed:

| Metric | PopKit | Vanilla | Root Cause |
|--------|---------|---------|------------|
| **Quality Score** | 3/10 | 10/10 | Incomplete requirements |
| **Critical Bugs** | 2 | 0 | Missing physics specs |
| **Tests Passed** | 5/5 | 5/5 | Tests were too basic |
| **Prompt Length** | 4 words | 6 detailed requirements | Configuration bug |

### Why PopKit Failed

With only "create bouncing balls animation", PopKit had to guess:
- ❓ What physics to implement
- ❓ How realistic the physics should be
- ❓ What damping/friction behavior to use
- ❓ Whether to include gravity

**PopKit's assumption:** Apply damping every frame to make balls "settle"
```javascript
// PopKit (WRONG - but reasonable guess without specs)
update() {
  this.vx *= FRICTION;  // 0.99 every frame
  this.vy *= DAMPING;   // 0.98 every frame
}
```

### Why Vanilla Succeeded

With explicit requirements including "realistic physics" and "proper reflection", Vanilla knew:
- ✅ Physics must be realistic (energy conservation)
- ✅ Reflection happens on wall collision
- ✅ Gravity pulls balls down (requirement #6)
- ✅ Damping applied on collision, not every frame

**Vanilla's implementation:** Damping only on collision
```javascript
// Vanilla (CORRECT - followed specifications)
if (this.x + this.radius >= canvas.width) {
  this.x = canvas.width - this.radius;
  this.vx = -Math.abs(this.vx) * WALL_DAMPING;  // Only on collision
}
```

## Configuration Bug

The issue was in `tasks/bouncing-balls.json`:

**Before (UNFAIR):**
```json
{
  "workflowType": "popkit",
  "workflowCommand": "/popkit:dev \"create bouncing balls animation\"",
  "prompt": "Create a web page with a canvas showing 5 balls bouncing with realistic physics. Requirements:\n1. Each ball should have a random color and size (10-30px radius)\n..."
}
```

The `prompt` field was used for vanilla, but `workflowCommand` was used for PopKit - and they didn't match!

**After (FAIR):**
```json
{
  "workflowType": "popkit",
  "workflowCommand": "/popkit:dev \"Create a web page with a canvas showing 5 balls bouncing with realistic physics. Requirements: 1. Each ball should have a random color and size (10-30px radius) 2. Balls should start at random positions with random velocities 3. Balls should bounce off the walls (canvas edges) with proper reflection 4. Balls should collide with each other (basic collision detection) 5. Use requestAnimationFrame for smooth animation 6. Add gravity (balls should fall and bounce). This is a vanilla JavaScript task. No frameworks or build tools required.\"",
  "prompt": "Create a web page with a canvas showing 5 balls bouncing with realistic physics. Requirements:\n..."
}
```

Now both get the exact same full requirements.

## Previous Conclusions Were Wrong

Our previous analysis concluded:
1. ❌ Quick Mode has no quality gates → **Not the root cause**
2. ❌ Orchestrator routes by word count → **True, but not relevant here**
3. ❌ PopKit needs domain-aware routing → **True, but prompt was incomplete**
4. ❌ Tests were too basic → **True, but unfair comparison**

**The real issue:** PopKit was working with 10% of the information vanilla had.

## What We Learned About Previous Analysis

The quality analyzer, improved tests, and Quick Mode quality gates are all **still valuable improvements** because:
1. They help catch bugs even with good prompts
2. They validate physics correctness programmatically
3. They ensure quality gates run before commit

But they didn't fix the root cause - the benchmark was unfair.

## Next Steps

1. ✅ Fixed `bouncing-balls.json` to give PopKit full prompt
2. ⏳ Re-run benchmarks with prompt parity
3. ⏳ Compare results to see if PopKit quality improves to match vanilla
4. ⏳ If still worse, THEN investigate orchestration/quality gates

## Expected Results

With prompt parity, PopKit should:
- Receive explicit physics requirements
- Implement damping only on collision (per specs)
- Achieve quality score of 9-10/10 (matching vanilla)
- Potentially be faster (fewer tokens due to orchestration)

If PopKit still produces worse code with the same prompt, THEN we have a genuine orchestration/quality issue to investigate.

## Key Insight

**Always ensure benchmark fairness before analyzing results.**

We spent significant effort analyzing orchestration chains, improving quality gates, and creating bug detectors - all valuable work - but the real issue was much simpler: **PopKit and vanilla were solving different problems.**

This is a reminder that in benchmark design, **prompt parity is critical**.
