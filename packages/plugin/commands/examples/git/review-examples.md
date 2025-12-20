# Code Review Examples

## Basic Usage

```bash
/popkit:git review                    # Review uncommitted changes
/popkit:git review --staged           # Review staged changes only
/popkit:git review --branch feature/auth
/popkit:git review --pr 67            # Review PR changes
/popkit:git review --file src/auth.ts # Review specific file
```

## Review Process

1. **Gather Changes**
   ```bash
   git diff HEAD~1...HEAD         # For branch review
   git diff --cached              # For staged
   git diff                       # For uncommitted
   ```

2. **Analyze Categories**
   - **Simplicity/DRY/Elegance** - Duplication, complexity, abstractions
   - **Bugs/Correctness** - Logic errors, edge cases, type safety
   - **Conventions** - Project patterns, naming, organization

3. **Score and Filter**
   Each issue gets confidence score (0-100):
   - 0-49: Ignored (likely false positive)
   - 50-79: Noted but not reported
   - 80-89: Important (should fix)
   - 90-100: Critical (must fix)

   **Threshold: 80+** only reported.

4. **Report** (see sample output below)

## Sample Output

```markdown
## Code Review: Feature Auth

### Summary
Clean implementation with good test coverage. Two issues found.

### Critical Issues (Must Fix)

#### Issue 1: Missing null check
- **File**: `src/auth.ts:45`
- **Confidence**: 95/100
- **Category**: Bug/Correctness
- **Description**: `user.email` accessed without null check
- **Fix**: Add optional chaining or null check

### Important Issues (Should Fix)

#### Issue 2: Duplicate validation logic
- **File**: `src/auth.ts:60-75`
- **Confidence**: 82/100
- **Category**: Simplicity/DRY
- **Description**: Email validation duplicated from utils
- **Fix**: Import and use existing validateEmail()

### Assessment

**Ready to merge?** With fixes
**Quality Score: 7/10**
```

## Review Options

```bash
/popkit:git review --focus simplicity     # Focus on DRY/elegance
/popkit:git review --focus correctness    # Focus on bugs
/popkit:git review --focus conventions    # Focus on patterns
/popkit:git review --threshold 70         # Lower confidence threshold
/popkit:git review --verbose              # Include lower-confidence issues
```
