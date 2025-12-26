#!/usr/bin/env python3
"""Quick script to verify exemption logic on real file paths."""

import re

EXEMPT_PATHS = [
    r"(?:^|/)docs/",          # docs/ at start or after /
    r"(?:^|/)examples/",      # examples/ at start or after /
    r"(?:^|/)standards/",     # standards/ at start or after /
    r"(?:^|/)templates/",     # templates/ at start or after /
    r"(?:^|/)test",           # /test or test at start
    r"\.test\.",              # .test. anywhere
    r"_test\.",               # _test. anywhere
    r"^test_",                # test_ at start of filename
    r"(?:^|/)sample",         # /sample or sample at start
    r"\.sample\.",            # .sample. anywhere
    r"\.example\.",           # .example. anywhere
    r"\.template\.",          # .template. anywhere
    r"(?:^|/)fixtures/",      # fixtures/ at start or after /
    r"README\.md$",           # README.md at end
    r"CHANGELOG\.md$",        # CHANGELOG.md at end
]

test_files = [
    'packages/popkit-ops/skills/pop-assessment-security/standards/secret-patterns.md',
    'packages/popkit-core/examples/plugin/test-examples.md',
    'packages/popkit-dev/skills/pop-routine-measure/test_measurement.py',
    'packages/cloud/src/templates/mcp-generator/templates/index-template.ts',
    'README.md',
    'docs/plans/2025-12-15-v1-execution-plan.md',
    'src/auth.py',  # Should NOT be exempt
    'config.sample.json',  # Should be exempt
    'test_runner.py',  # Should be exempt
]

print('File Exemption Check:')
print('='*80)
for file in test_files:
    path_normalized = file.replace('\\', '/')
    is_exempt = any(re.search(p, path_normalized) for p in EXEMPT_PATHS)

    # Find which pattern matched
    matched_pattern = None
    if is_exempt:
        for p in EXEMPT_PATHS:
            if re.search(p, path_normalized):
                matched_pattern = p
                break

    if is_exempt:
        print(f'[EXEMPT]     {file}')
        print(f'             Reason: {matched_pattern}')
    else:
        print(f'[NOT EXEMPT] {file}')
    print()
