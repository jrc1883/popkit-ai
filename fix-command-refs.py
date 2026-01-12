#!/usr/bin/env python3
"""
Systematic command reference fixer for PopKit documentation.
Fixes all incorrect /popkit: references to use correct plugin namespaces.
"""

import re
from pathlib import Path
from typing import Tuple

# Mapping of command names to their correct plugin namespaces
COMMAND_MAPPING = {
    # popkit-core commands
    'account': 'popkit-core',
    'bug': 'popkit-core',
    'dashboard': 'popkit-core',
    'plugin': 'popkit-core',
    'power': 'popkit-core',
    'privacy': 'popkit-core',
    'project': 'popkit-core',
    'record': 'popkit-core',
    'stats': 'popkit-core',

    # popkit-dev commands
    'dev': 'popkit-dev',
    'git': 'popkit-dev',
    'issue': 'popkit-dev',
    'milestone': 'popkit-dev',
    'next': 'popkit-dev',
    'routine': 'popkit-dev',
    'worktree': 'popkit-dev',

    # popkit-ops commands
    'assess': 'popkit-ops',
    'audit': 'popkit-ops',
    'debug': 'popkit-ops',
    'deploy': 'popkit-ops',
    'security': 'popkit-ops',

    # popkit-research commands
    'knowledge': 'popkit-research',
    'research': 'popkit-research',
}

def fix_command_references(content: str) -> Tuple[str, int]:
    """
    Fix all /popkit:command references to use correct plugin namespaces.
    Returns (fixed_content, num_fixes)
    """
    fixes = 0

    # Pattern: /popkit:COMMAND (with optional arguments after)
    # Matches: /popkit:routine, /popkit:git commit, /popkit:issue create, etc.
    pattern = r'/popkit:(\w+)'

    def replace_match(match):
        nonlocal fixes
        command = match.group(1)

        if command in COMMAND_MAPPING:
            plugin = COMMAND_MAPPING[command]
            fixes += 1
            return f'/{plugin}:{command}'
        else:
            # Unknown command, leave as-is
            return match.group(0)

    fixed_content = re.sub(pattern, replace_match, content)
    return fixed_content, fixes

def process_file(file_path: Path) -> int:
    """Process a single file and return number of fixes made."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        fixed_content, fixes = fix_command_references(content)

        if fixes > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"[OK] {file_path.name}: {fixes} fixes")
        else:
            print(f"  {file_path.name}: no changes needed")

        return fixes
    except Exception as e:
        print(f"[ERR] {file_path.name}: ERROR - {e}")
        return 0

def main():
    """Main entry point."""
    print("=" * 60)
    print("PopKit Command Reference Fixer")
    print("=" * 60)
    print()

    # Files to process (high-priority documentation)
    files_to_fix = [
        # Root documentation
        Path('README.md'),
        Path('CLAUDE.md'),
        Path('CONTRIBUTING.md'),
        Path('CHANGELOG.md'),

        # Package READMEs
        Path('packages/popkit-core/README.md'),
        Path('packages/popkit-dev/README.md'),
        Path('packages/popkit-ops/README.md'),
        Path('packages/popkit-research/README.md'),

        # Architecture docs
        Path('docs/AGENT_ROUTING_GUIDE.md'),
        Path('docs/POWER_MODE_ASYNC.md'),
        Path('docs/PROGRAMMATIC_ASK_USER_QUESTION.md'),
    ]

    total_fixes = 0

    for file_path in files_to_fix:
        if file_path.exists():
            fixes = process_file(file_path)
            total_fixes += fixes
        else:
            print(f"  {file_path}: SKIPPED (not found)")

    print()
    print("=" * 60)
    print(f"Total fixes: {total_fixes}")
    print("=" * 60)

if __name__ == '__main__':
    main()
