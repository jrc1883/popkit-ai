---
description: "quarterly | yearly | stale | duplicates | health | ip-leak [--verbose, --fix]"
argument-hint: "<type> [options]"
---

# /popkit-ops:audit - Project Audit & Review

Perform periodic audits to review project health, find stale issues, detect duplicates, scan for IP leaks, and generate actionable recommendations.

## Subcommands

| Subcommand | Description |
|------------|-------------|
| quarterly (default) | Q1/Q2/Q3/Q4 audit report |
| yearly | Full year audit |
| stale | Find stale issues |
| duplicates | Find potential duplicate issues |
| health | Overall project health check |
| ip-leak | Scan for intellectual property leaks |

---

## quarterly (default)

Generate quarterly audit report with metrics and recommendations.

**Metrics:** Issues created/closed, close rate, avg time to close, milestone progress, issue distribution (type/priority), stale issues.

**Output:** Markdown report with summary table, recommendations, health score.

**Options:** --verbose (detailed breakdown), --json

---

## yearly

Annual audit with year-over-year comparison.

**Includes:** All quarterly metrics aggregated, trend analysis, annual goals review.

**Options:** --year <YYYY>, --json

---

## stale

Find stale issues (no activity >30 days).

**Process:** Query GitHub Issues API → Filter by last activity → Group by staleness (30-60d, 60-90d, 90+d) → Generate recommendations.

**Output:** Table of stale issues with ID, title, days inactive, last activity date.

**Options:** --days <N> (threshold), --fix (close after confirmation), --json

---

## duplicates

Find potential duplicate issues using semantic similarity.

**Process:** Fetch all open issues → Embed titles/descriptions → Calculate similarity → Report pairs above 0.8 threshold.

**Output:** Pairs of potentially duplicate issues with similarity scores.

**Options:** --threshold <0.0-1.0>, --merge (link duplicates), --json

---

## health

Overall project health check across multiple dimensions.

**Checks:** Git status, test coverage, dependency vulnerabilities, documentation drift, code smells, CI/CD status.

**Output:** Health score (0-100) with breakdown by category.

**Options:** --quick (skip deep analysis), --json

---

## ip-leak

Scan for intellectual property leaks (API keys, secrets, proprietary code).

**Process:** Scan codebase → Detect patterns (API keys, tokens, hardcoded credentials, proprietary algorithms) → Report findings by severity.

**Integration:** Runs automatically in `/popkit-dev:git publish` and `/popkit-dev:routine nightly`.

**Options:** --path <dir>, --pre-publish (strict mode), --json, --severity <critical|high|medium|low>

---

## Architecture

| Component | Integration |
|-----------|-------------|
| Quarterly | GitHub Issues API, milestone tracking |
| Stale | GitHub Issues API, last activity filter |
| Duplicates | Voyage AI embeddings, similarity scoring |
| Health | Multiple skills + tests + lint + security |
| IP Scanner | `hooks/utils/ip_protection.py` |
| Reports | Markdown formatting |

**Related:** `/popkit-dev:milestone`, `/popkit-dev:issue`, `/popkit-core:stats`, `/popkit-dev:git publish`, `/popkit-dev:routine nightly`
