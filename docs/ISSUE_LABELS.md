# PopKit Issue Label Taxonomy

Standardized labeling system for PopKit GitHub issues.

---

## Priority Labels (Required)

Every issue must have ONE priority label:

| Label                 | Description                                         | Use When                                                             |
| --------------------- | --------------------------------------------------- | -------------------------------------------------------------------- |
| **priority:critical** | Blockers, security vulnerabilities, data loss risks | Breaks core functionality, affects all users, immediate fix required |
| **priority:high**     | Important features, significant bugs                | Affects many users, needed for milestone, substantial impact         |
| **priority:medium**   | Enhancements, moderate bugs                         | Nice to have, affects some users, can wait for next release          |
| **priority:low**      | Minor improvements, polish                          | Low impact, future consideration, optional improvements              |

---

## Type Labels (Required)

Every issue must have ONE primary type label:

| Label                  | Description                                |
| ---------------------- | ------------------------------------------ |
| **type:bug**           | Something isn't working correctly          |
| **type:feature**       | New functionality request                  |
| **type:enhancement**   | Improvement to existing functionality      |
| **type:documentation** | Documentation additions or fixes           |
| **type:testing**       | Test coverage, test infrastructure         |
| **type:refactor**      | Code restructuring without behavior change |
| **type:performance**   | Speed, efficiency, optimization            |
| **type:security**      | Security vulnerabilities or hardening      |

---

## Component Labels (Optional, Multiple Allowed)

Tag the affected PopKit component(s):

| Label                    | Description              |
| ------------------------ | ------------------------ |
| **component:core**       | popkit-core plugin       |
| **component:dev**        | popkit-dev plugin        |
| **component:ops**        | popkit-ops plugin        |
| **component:research**   | popkit-research plugin   |
| **component:shared**     | Shared utilities         |
| **component:hooks**      | Hook scripts             |
| **component:agents**     | AI agents                |
| **component:skills**     | Reusable skills          |
| **component:commands**   | Slash commands           |
| **component:power-mode** | Power Mode orchestration |

---

## Workstream Labels (Optional)

Group related work:

| Label                       | Description                       |
| --------------------------- | --------------------------------- |
| **workstream:validation**   | Testing and validation work       |
| **workstream:cloud**        | Cloud features and infrastructure |
| **workstream:dx**           | Developer experience improvements |
| **workstream:integration**  | External integrations             |
| **workstream:architecture** | Core architecture changes         |

---

## Status Labels (Optional)

Track issue lifecycle:

| Label                         | Description                    |
| ----------------------------- | ------------------------------ |
| **status:blocked**            | Waiting on external dependency |
| **status:needs-discussion**   | Requires design decision       |
| **status:needs-reproduction** | Bug needs reproduction steps   |
| **status:good-first-issue**   | Suitable for new contributors  |
| **status:help-wanted**        | Looking for contributors       |

---

## Special Labels

| Label               | Description                                 |
| ------------------- | ------------------------------------------- |
| **epic**            | Meta-issue tracking multiple related issues |
| **breaking-change** | Requires major version bump                 |
| **migration**       | Migrated from private repository            |

---

## Label Application Rules

### 1. Every Issue MUST Have:

- ONE priority label (critical/high/medium/low)
- ONE type label (bug/feature/enhancement/etc.)

### 2. Optional Labels:

- Multiple component labels (if affects multiple components)
- One workstream label (if part of larger initiative)
- Status labels as needed

### 3. Label Format:

- Use lowercase
- Use hyphens for multi-word labels
- Use namespace prefixes (priority:, type:, component:, etc.)

### 4. Priority Guidelines:

**priority:critical** - Use sparingly, only for:

- Security vulnerabilities
- Data loss bugs
- Complete feature breakage
- Release blockers

**priority:high** - Important work:

- Major features for next release
- Bugs affecting many users
- Performance issues
- Documentation gaps

**priority:medium** - Standard work:

- Quality improvements
- Minor features
- Bugs affecting few users
- Technical debt

**priority:low** - Future work:

- Nice-to-have features
- Polish and refinements
- Edge case bugs
- Long-term improvements

---

## Examples

### Example 1: Critical Bug

```
Title: "Commands fail to invoke after plugin install"
Labels: priority:critical, type:bug, component:core
```

### Example 2: Feature Request

```
Title: "Add caching system for API calls"
Labels: priority:medium, type:feature, component:core, workstream:cloud
```

### Example 3: Documentation Gap

```
Title: "Missing installation guide for Windows users"
Labels: priority:high, type:documentation
```

### Example 4: Epic

```
Title: "XML Protocol Enhancement Suite"
Labels: priority:high, type:enhancement, epic, workstream:architecture
Component Labels: component:agents, component:hooks, component:power-mode
```

---

## Migration Notes

When applying labels to migrated issues:

1. Re-evaluate priority in context of all issues
2. Add `migration` label
3. Use standardized format (not legacy labels)
4. Update title if needed for clarity

---

**Last Updated:** 2026-01-10
**Version:** 1.0.0
