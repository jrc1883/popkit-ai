# Power Mode - Archived Files

This directory contains archived test and benchmark files from the Power Mode simplification effort.

## What is this?

These files were part of the original Power Mode implementation and have been archived during the simplification process (Phase 1-2 cleanup on 2025-12-29).

## Directory Structure

- `tests/` - Test files for coordination, handoff, and interleaved execution patterns
- `benchmarks/` - Benchmark files for measuring coordinator performance

## Archived Files

### Tests (4 files, 1668 LOC)
- `test_coordination.py` (345 LOC) - Multi-agent coordination tests
- `test_handoff.py` (355 LOC) - Agent handoff protocol tests
- `test_interleaved.py` (417 LOC) - Interleaved execution pattern tests
- `test_puzzle_coordination.py` (551 LOC) - Complex puzzle coordination tests

### Benchmarks (2 files, 846 LOC)
- `benchmark.py` (478 LOC) - Power Mode performance benchmarks
- `benchmark_coordinator.py` (368 LOC) - Coordinator-specific benchmarks

**Total:** 6 files, 2514 lines of code

## Why were these archived?

As part of the Power Mode simplification effort, these experimental test and benchmark files were moved out of the active codebase to reduce complexity. They represent earlier iterations of multi-agent coordination patterns.

## Can I still use these?

These files are preserved for reference and can be restored if needed. However, they may depend on code that has been removed or refactored during the simplification process.

## Related Changes

This archive is part of the broader Power Mode simplification:
- Phase 1: Archive tests and benchmarks (this directory)
- Phase 2: Delete experimental consensus protocol
- Phase 3+: Consolidate coordinators and simplify architecture

See the main Power Mode documentation for the current, simplified implementation.
