#!/usr/bin/env python3
"""
Fix broken imports in packages/shared-py/popkit_shared/utils/
Converts absolute imports to relative imports for package modules.
"""

import re
from pathlib import Path

# Get all Python files in shared utilities
utils_dir = Path("packages/shared-py/popkit_shared/utils")
py_files = list(utils_dir.glob("*.py"))

# Get list of all module names (for detecting internal imports)
module_names = {f.stem for f in py_files if f.stem != "__init__"}

print(f"Found {len(py_files)} Python files")
print(f"Module names: {len(module_names)} modules")

fixed_count = 0
total_import_fixes = 0

for py_file in py_files:
    if py_file.stem == "__init__":
        continue

    content = py_file.read_text(encoding='utf-8')
    original_content = content

    # Fix imports for each module in our utils package
    for module in module_names:
        # Pattern: from module_name import ...
        # Replace with: from .module_name import ...
        pattern = rf'^from {module} import'
        replacement = rf'from .{module} import'
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    # Count how many changes were made
    if content != original_content:
        import_changes = len(re.findall(r'^from \.[a-z_]+ import', content, re.MULTILINE)) - \
                        len(re.findall(r'^from \.[a-z_]+ import', original_content, re.MULTILINE))

        py_file.write_text(content, encoding='utf-8')
        fixed_count += 1
        total_import_fixes += import_changes
        print(f"[OK] Fixed {py_file.name} ({import_changes} imports)")

print(f"\n{'='*60}")
print(f"Fixed {fixed_count} files")
print(f"Total import fixes: {total_import_fixes}")
print(f"{'='*60}")
