#!/bin/bash
# Create standardized PopKit labels

echo "Creating PopKit standardized labels..."

# Priority Labels (Red shades)
gh label create "priority:critical" --description "Blockers, security, data loss - immediate action" --color "b60205" --force
gh label create "priority:high" --description "Important features, significant bugs - next milestone" --color "d93f0b" --force
gh label create "priority:medium" --description "Enhancements, moderate bugs - standard priority" --color "fbca04" --force
gh label create "priority:low" --description "Minor improvements, future consideration" --color "0e8a16" --force

# Type Labels (Blue shades)
gh label create "type:bug" --description "Something isn't working" --color "d73a4a" --force
gh label create "type:feature" --description "New functionality" --color "a2eeef" --force
gh label create "type:enhancement" --description "Improvement to existing feature" --color "84b6eb" --force
gh label create "type:documentation" --description "Documentation additions or fixes" --color "0075ca" --force
gh label create "type:testing" --description "Test coverage and infrastructure" --color "1d76db" --force
gh label create "type:refactor" --description "Code restructuring" --color "5319e7" --force
gh label create "type:performance" --description "Speed and optimization" --color "f9d0c4" --force
gh label create "type:security" --description "Security vulnerabilities or hardening" --color "ee0701" --force

# Component Labels (Purple shades)
gh label create "component:core" --description "popkit-core plugin" --color "5319e7" --force
gh label create "component:dev" --description "popkit-dev plugin" --color "7057ff" --force
gh label create "component:ops" --description "popkit-ops plugin" --color "8b7dff" --force
gh label create "component:research" --description "popkit-research plugin" --color "a799ff" --force
gh label create "component:shared" --description "Shared utilities" --color "c2b3ff" --force
gh label create "component:hooks" --description "Hook scripts" --color "d4c5ff" --force
gh label create "component:agents" --description "AI agents" --color "e5d9ff" --force
gh label create "component:skills" --description "Reusable skills" --color "f3ecff" --force
gh label create "component:commands" --description "Slash commands" --color "bfdadc" --force
gh label create "component:power-mode" --description "Power Mode orchestration" --color "c5def5" --force

# Workstream Labels (Green shades)
gh label create "workstream:validation" --description "Testing and validation work" --color "0e8a16" --force
gh label create "workstream:cloud" --description "Cloud features and infrastructure" --color "1a7f37" --force
gh label create "workstream:dx" --description "Developer experience improvements" --color "2da44e" --force
gh label create "workstream:integration" --description "External integrations" --color "4ac26b" --force
gh label create "workstream:architecture" --description "Core architecture changes" --color "6fdd8b" --force

# Status Labels (Yellow/Orange shades)
gh label create "status:blocked" --description "Waiting on external dependency" --color "d4c5f9" --force
gh label create "status:needs-discussion" --description "Requires design decision" --color "d876e3" --force
gh label create "status:needs-reproduction" --description "Bug needs reproduction steps" --color "e99695" --force
gh label create "status:good-first-issue" --description "Suitable for new contributors" --color "7057ff" --force
gh label create "status:help-wanted" --description "Looking for contributors" --color "008672" --force

# Special Labels
gh label create "epic" --description "Meta-issue tracking multiple issues" --color "3e4b9e" --force
gh label create "breaking-change" --description "Requires major version bump" --color "b60205" --force
gh label create "migration" --description "Migrated from private repository" --color "ededed" --force

echo "✓ Labels created successfully!"
