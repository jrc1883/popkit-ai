#!/usr/bin/env python3
"""
Performance measurement for modular PopKit architecture.
Counts tokens for each plugin to compare against monolithic baseline.

Baseline (v0.2.5 monolithic): 279,577 tokens
Target (modular): ≤251,619 tokens (90% of baseline)
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

def estimate_tokens(text: str) -> int:
    """
    Estimate token count using GPT-4 approximation (1 token ≈ 4 characters).
    This is conservative; actual tokenization might differ slightly.
    """
    return len(text) // 4

def count_file_tokens(file_path: Path) -> int:
    """Count tokens in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return estimate_tokens(content)
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
        return 0

def count_directory_tokens(directory: Path, extensions: List[str] = ['.md', '.json']) -> Dict[str, int]:
    """Count tokens in all matching files in a directory."""
    counts = {
        'commands': 0,
        'skills': 0,
        'agents': 0,
        'config': 0,
        'total': 0
    }

    if not directory.exists():
        return counts

    for file_path in directory.rglob('*'):
        if not file_path.is_file():
            continue

        if file_path.suffix not in extensions:
            continue

        tokens = count_file_tokens(file_path)

        # Categorize by directory
        path_str = str(file_path)
        if '/commands/' in path_str or '\\commands\\' in path_str:
            counts['commands'] += tokens
        elif '/skills/' in path_str or '\\skills\\' in path_str:
            counts['skills'] += tokens
        elif '/agents/' in path_str or '\\agents\\' in path_str:
            counts['agents'] += tokens
        elif file_path.name in ['plugin.json', 'marketplace.json', 'config.json']:
            counts['config'] += tokens

        counts['total'] += tokens

    return counts

def measure_plugin(plugin_name: str, plugin_dir: Path) -> Dict[str, int]:
    """Measure token count for a single plugin."""
    print(f"\nMeasuring {plugin_name}...")

    counts = count_directory_tokens(plugin_dir)

    print(f"  Commands: {counts['commands']:,} tokens")
    print(f"  Skills:   {counts['skills']:,} tokens")
    print(f"  Agents:   {counts['agents']:,} tokens")
    print(f"  Config:   {counts['config']:,} tokens")
    print(f"  Total:    {counts['total']:,} tokens")

    return counts

def main():
    """Main measurement routine."""
    print("=" * 60)
    print("PopKit Modular Architecture - Performance Measurement")
    print("=" * 60)

    # Baseline from comprehensive assessment
    baseline_total = 279_577
    target_total = int(baseline_total * 0.90)  # 90% of baseline

    print(f"\nBaseline (v0.2.5 monolithic): {baseline_total:,} tokens")
    print(f"Target (modular): <={target_total:,} tokens (90% of baseline)")

    # Measure each plugin
    repo_root = Path(__file__).parent
    packages_dir = repo_root / "packages"

    plugins = [
        "popkit-dev",
        "popkit-github",
        "popkit-quality",
        "popkit-deploy",
        "popkit-research",
        "popkit-core"
    ]

    plugin_results = {}
    total_tokens = 0

    for plugin in plugins:
        plugin_dir = packages_dir / plugin
        counts = measure_plugin(plugin, plugin_dir)
        plugin_results[plugin] = counts
        total_tokens += counts['total']

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(f"\nTotal modular tokens: {total_tokens:,}")
    print(f"Baseline (monolithic): {baseline_total:,}")
    print(f"Difference: {total_tokens - baseline_total:+,} tokens")

    reduction_pct = ((baseline_total - total_tokens) / baseline_total) * 100
    print(f"Reduction: {reduction_pct:.1f}%")

    # Check target
    if total_tokens <= target_total:
        status = "PASS"
    else:
        status = "FAIL"

    print(f"\nTarget: <={target_total:,} tokens")
    print(f"Status: {status}")

    # Per-plugin breakdown
    print("\n" + "-" * 60)
    print("PER-PLUGIN BREAKDOWN")
    print("-" * 60)

    for plugin in plugins:
        counts = plugin_results[plugin]
        pct = (counts['total'] / total_tokens) * 100
        print(f"{plugin:20s} {counts['total']:8,} tokens ({pct:4.1f}%)")

    # Category breakdown
    print("\n" + "-" * 60)
    print("CATEGORY BREAKDOWN")
    print("-" * 60)

    total_commands = sum(p['commands'] for p in plugin_results.values())
    total_skills = sum(p['skills'] for p in plugin_results.values())
    total_agents = sum(p['agents'] for p in plugin_results.values())
    total_config = sum(p['config'] for p in plugin_results.values())

    print(f"Commands: {total_commands:,} tokens ({(total_commands/total_tokens)*100:.1f}%)")
    print(f"Skills:   {total_skills:,} tokens ({(total_skills/total_tokens)*100:.1f}%)")
    print(f"Agents:   {total_agents:,} tokens ({(total_agents/total_tokens)*100:.1f}%)")
    print(f"Config:   {total_config:,} tokens ({(total_config/total_tokens)*100:.1f}%)")

    # Comparison to baseline categories
    print("\n" + "-" * 60)
    print("COMPARISON TO BASELINE")
    print("-" * 60)

    baseline_skills = 149_868
    baseline_commands = 127_309
    baseline_agents = 2_400

    print(f"Skills:   {total_skills:,} vs {baseline_skills:,} ({total_skills - baseline_skills:+,})")
    print(f"Commands: {total_commands:,} vs {baseline_commands:,} ({total_commands - baseline_commands:+,})")
    print(f"Agents:   {total_agents:,} vs {baseline_agents:,} ({total_agents - baseline_agents:+,})")

    print("\n" + "=" * 60)

    # Return exit code
    return 0 if total_tokens <= target_total else 1

if __name__ == "__main__":
    sys.exit(main())
