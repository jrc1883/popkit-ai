#!/usr/bin/env python3
"""
Agent Loader with Semantic Search

Loads only relevant agents using embedding-based similarity search,
keyword matching, file pattern matching, and error pattern matching.

Part of Phase 2: Embedding-Based Agent Loading.
Enhanced with file/error pattern routing (Issue #10).
"""

import fnmatch
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .embedding_store import EmbeddingStore
from .voyage_client import embed

# =============================================================================
# ROUTING CONFIG
# =============================================================================

# Path to the routing configuration file (same directory as this module)
_ROUTING_CONFIG_PATH = Path(__file__).parent / "routing_config.json"

# Similarity score constants for each routing method
KEYWORD_SIMILARITY = 0.7
FILE_PATTERN_SIMILARITY = 0.6
ERROR_PATTERN_SIMILARITY = 0.65

# Boost applied to embedding results when file/error patterns also match
PATTERN_BOOST = 0.1

# Hardcoded fallback keyword map (used when routing_config.json is missing)
_FALLBACK_KEYWORD_MAP: Dict[str, List[str]] = {
    "bug": ["bug-whisperer"],
    "debug": ["bug-whisperer"],
    "crash": ["bug-whisperer"],
    "error": ["bug-whisperer"],
    "fix": ["bug-whisperer"],
    "broken": ["bug-whisperer"],
    "security": ["security-auditor"],
    "vulnerability": ["security-auditor"],
    "authentication": ["security-auditor"],
    "auth": ["security-auditor"],
    "test": ["test-writer-fixer"],
    "testing": ["test-writer-fixer"],
    "coverage": ["test-writer-fixer"],
    "performance": ["performance-optimizer"],
    "slow": ["performance-optimizer"],
    "optimize": ["performance-optimizer"],
    "refactor": ["refactoring-expert"],
    "restructure": ["refactoring-expert"],
    "api": ["api-designer"],
    "endpoint": ["api-designer"],
    "review": ["code-reviewer"],
    "lint": ["code-reviewer"],
    "docs": ["documentation-maintainer"],
    "documentation": ["documentation-maintainer"],
    "accessibility": ["accessibility-guardian"],
    "a11y": ["accessibility-guardian"],
    "migrate": ["migration-specialist"],
    "upgrade": ["migration-specialist"],
    "deploy": ["deployment-validator"],
    "bundle": ["bundle-analyzer"],
    "conflict": ["merge-conflict-resolver"],
    "merge": ["merge-conflict-resolver"],
    "prototype": ["rapid-prototyper"],
    "rollback": ["rollback-specialist"],
    "revert": ["rollback-specialist"],
    "research": ["researcher"],
    "explore": ["code-explorer"],
    "architecture": ["code-architect"],
    "design": ["code-architect"],
    "prioritize": ["feature-prioritizer"],
    "prd": ["prd-parser"],
    "requirements": ["prd-parser"],
    "dead code": ["dead-code-eliminator"],
    "unused": ["dead-code-eliminator"],
    "agent": ["meta-agent"],
    "parallel": ["power-coordinator"],
    "power mode": ["power-coordinator"],
}

# Tier assignments for all 23 agents
TIER_MAP: Dict[str, str] = {
    # Tier 1 (always active)
    "accessibility-guardian": "tier-1-always-active",
    "api-designer": "tier-1-always-active",
    "documentation-maintainer": "tier-1-always-active",
    "migration-specialist": "tier-1-always-active",
    "code-reviewer": "tier-1-always-active",
    "refactoring-expert": "tier-1-always-active",
    "bug-whisperer": "tier-1-always-active",
    "performance-optimizer": "tier-1-always-active",
    "security-auditor": "tier-1-always-active",
    "test-writer-fixer": "tier-1-always-active",
    # Tier 2 (on-demand)
    "bundle-analyzer": "tier-2-on-demand",
    "dead-code-eliminator": "tier-2-on-demand",
    "feature-prioritizer": "tier-2-on-demand",
    "meta-agent": "tier-2-on-demand",
    "power-coordinator": "tier-2-on-demand",
    "merge-conflict-resolver": "tier-2-on-demand",
    "prd-parser": "tier-2-on-demand",
    "rapid-prototyper": "tier-2-on-demand",
    "deployment-validator": "tier-2-on-demand",
    "rollback-specialist": "tier-2-on-demand",
    "researcher": "tier-2-on-demand",
    # Feature Workflow
    "code-explorer": "feature-workflow",
    "code-architect": "feature-workflow",
}


def _load_routing_config(config_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Load routing configuration from JSON file.

    Args:
        config_path: Path to config file. Defaults to routing_config.json in same directory.

    Returns:
        Parsed config dict or None if unavailable.
    """
    path = config_path or _ROUTING_CONFIG_PATH
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Failed to load routing config: {e}", file=sys.stderr)
    return None


class AgentLoader:
    """
    Load relevant agents using semantic search, keyword matching,
    file pattern matching, and error pattern matching.

    Routing methods (in order of similarity score):
    - Keyword match: 0.7 similarity
    - Error pattern match: 0.65 similarity
    - File pattern match: 0.6 similarity
    - Embedding search: variable (0.0-1.0)

    Attributes:
        store: Embedding store for local search
        use_embeddings: Whether to use embeddings (fallback to keywords if False)
        always_include_tier1: Always include some Tier 1 agents
        routing_config: Loaded routing configuration
    """

    def __init__(
        self,
        use_embeddings: bool = True,
        always_include_tier1: bool = True,
        config_path: Optional[Path] = None,
    ):
        """
        Initialize agent loader.

        Args:
            use_embeddings: Use semantic search (default: True)
            always_include_tier1: Always include Tier 1 agents (default: True)
            config_path: Optional path to routing config JSON file
        """
        self.use_embeddings = use_embeddings
        self.always_include_tier1 = always_include_tier1
        self.routing_config = _load_routing_config(config_path)

        if use_embeddings:
            self.store = EmbeddingStore()

    def load(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Load top relevant agents for a query.

        Uses a multi-signal approach:
        1. Keyword matching (from config or fallback)
        2. File pattern matching (from config)
        3. Error pattern matching (from config)
        4. Embedding-based semantic search (when available)

        Results from all methods are merged, deduplicated, and
        sorted by the highest similarity score per agent.

        Args:
            query: User query or task description
            top_k: Number of agents to load

        Returns:
            List of agent dicts with agent_id, similarity, tier, match_source
        """
        if self.use_embeddings:
            try:
                return self._load_with_embeddings(query, top_k)
            except Exception as e:
                print(
                    f"Embedding search failed: {e}, falling back to keywords",
                    file=sys.stderr,
                )
                return self._load_with_keywords(query, top_k)
        else:
            return self._load_with_keywords(query, top_k)

    # =========================================================================
    # FILE PATTERN MATCHING
    # =========================================================================

    def _match_file_patterns(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Match file paths against agent file pattern configuration.

        Uses fnmatch glob-style matching against patterns defined in
        routing_config.json. Each matched agent receives a similarity
        score of FILE_PATTERN_SIMILARITY (0.6).

        Args:
            file_paths: List of file paths mentioned in or extracted from the query

        Returns:
            List of agent dicts with agent_id, similarity, tier, match_source
        """
        if not self.routing_config:
            return []

        file_patterns_map = self.routing_config.get("file_patterns", {})
        if not file_patterns_map:
            return []

        matched_agents: Dict[str, Dict[str, Any]] = {}

        for file_path in file_paths:
            # Normalize: use forward slashes and get basename for simple matching
            normalized = file_path.replace("\\", "/")
            basename = Path(normalized).name

            for agent_name, patterns in file_patterns_map.items():
                if not isinstance(patterns, list):
                    patterns = [patterns]

                for pattern in patterns:
                    # Match against full path and basename
                    if fnmatch.fnmatch(basename, pattern) or fnmatch.fnmatch(normalized, pattern):
                        if agent_name not in matched_agents:
                            matched_agents[agent_name] = {
                                "agent_id": agent_name,
                                "similarity": FILE_PATTERN_SIMILARITY,
                                "tier": TIER_MAP.get(agent_name, "unknown"),
                                "description": "",
                                "match_source": "file_pattern",
                            }
                        break  # One match per agent per file is enough

        return list(matched_agents.values())

    # =========================================================================
    # ERROR PATTERN MATCHING
    # =========================================================================

    def _match_error_patterns(self, query: str) -> List[Dict[str, Any]]:
        """
        Scan query text for error patterns that indicate specific agent expertise.

        Uses regex matching against patterns defined in routing_config.json.
        Each matched agent receives a similarity score of
        ERROR_PATTERN_SIMILARITY (0.65).

        Args:
            query: User query or task description text

        Returns:
            List of agent dicts with agent_id, similarity, tier, match_source
        """
        if not self.routing_config:
            return []

        error_patterns_map = self.routing_config.get("error_patterns", {})
        if not error_patterns_map:
            return []

        matched_agents: Dict[str, Dict[str, Any]] = {}

        for agent_name, patterns in error_patterns_map.items():
            if not isinstance(patterns, list):
                patterns = [patterns]

            for pattern in patterns:
                try:
                    if re.search(pattern, query, re.IGNORECASE):
                        if agent_name not in matched_agents:
                            matched_agents[agent_name] = {
                                "agent_id": agent_name,
                                "similarity": ERROR_PATTERN_SIMILARITY,
                                "tier": TIER_MAP.get(agent_name, "unknown"),
                                "description": "",
                                "match_source": "error_pattern",
                            }
                        break  # One match per agent is enough
                except re.error:
                    # Skip invalid regex patterns gracefully
                    continue

        return list(matched_agents.values())

    # =========================================================================
    # FILE PATH EXTRACTION
    # =========================================================================

    @staticmethod
    def _extract_file_paths(query: str) -> List[str]:
        """
        Extract file paths from a query string.

        Looks for patterns that resemble file paths:
        - Paths with extensions (e.g., src/auth.ts, test_user.py)
        - Paths with directory separators (e.g., src/components/Button.tsx)
        - Config file names (e.g., jest.config.js, Dockerfile)

        Args:
            query: User query text

        Returns:
            List of extracted file path strings
        """
        paths: List[str] = []

        # Match paths with extensions (word chars, slashes, dots, hyphens)
        path_pattern = r"(?:[\w./\\-]+\.[\w.]+)"
        for match in re.finditer(path_pattern, query):
            candidate = match.group(0)
            # Filter out common non-path matches (URLs, version numbers)
            if not candidate.startswith("http") and not re.match(r"^\d+\.\d+(\.\d+)?$", candidate):
                paths.append(candidate)

        # Match known config files without extensions
        config_files = [
            "Dockerfile",
            "Procfile",
            "Makefile",
            "Jenkinsfile",
            "Vagrantfile",
        ]
        for config_file in config_files:
            if config_file in query:
                paths.append(config_file)

        return paths

    # =========================================================================
    # KEYWORD MATCHING (ENHANCED)
    # =========================================================================

    def _match_keywords(self, query: str) -> List[Dict[str, Any]]:
        """
        Match query against keyword configuration.

        Uses keywords from routing_config.json if available, otherwise
        falls back to hardcoded _FALLBACK_KEYWORD_MAP.

        Supports both single-word and multi-word keyword matching.

        Args:
            query: User query text

        Returns:
            List of agent dicts with agent_id, similarity, tier, match_source
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Determine keyword source
        if self.routing_config:
            keywords_config = self.routing_config.get("keywords", {})
            # Config format: agent_name -> [keywords]
            # Convert to keyword -> [agents] for matching
            keyword_to_agents: Dict[str, List[str]] = {}
            for agent_name, agent_keywords in keywords_config.items():
                if not isinstance(agent_keywords, list):
                    agent_keywords = [agent_keywords]
                for kw in agent_keywords:
                    kw_lower = kw.lower()
                    if kw_lower not in keyword_to_agents:
                        keyword_to_agents[kw_lower] = []
                    keyword_to_agents[kw_lower].append(agent_name)
        else:
            keyword_to_agents = {}
            for kw, agents in _FALLBACK_KEYWORD_MAP.items():
                keyword_to_agents[kw.lower()] = agents

        matched_agents: Dict[str, Dict[str, Any]] = {}

        for keyword, agents in keyword_to_agents.items():
            # Multi-word keywords: check if phrase appears in query
            if " " in keyword:
                if keyword in query_lower:
                    for agent_name in agents:
                        if agent_name not in matched_agents:
                            matched_agents[agent_name] = {
                                "agent_id": agent_name,
                                "similarity": KEYWORD_SIMILARITY,
                                "tier": TIER_MAP.get(agent_name, "unknown"),
                                "description": "",
                                "match_source": "keyword",
                            }
            else:
                # Single-word keywords: check if word appears in query words
                if keyword in query_words:
                    for agent_name in agents:
                        if agent_name not in matched_agents:
                            matched_agents[agent_name] = {
                                "agent_id": agent_name,
                                "similarity": KEYWORD_SIMILARITY,
                                "tier": TIER_MAP.get(agent_name, "unknown"),
                                "description": "",
                                "match_source": "keyword",
                            }

        return list(matched_agents.values())

    # =========================================================================
    # RESULT MERGING
    # =========================================================================

    @staticmethod
    def _merge_results(
        *result_lists: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Merge multiple result lists, keeping the highest similarity per agent.

        When an agent appears in multiple result lists, the entry with the
        highest similarity score is kept. The match_source is updated to
        indicate all sources that matched.

        Args:
            *result_lists: Variable number of agent result lists

        Returns:
            Merged and deduplicated list, sorted by similarity descending
        """
        merged: Dict[str, Dict[str, Any]] = {}

        for results in result_lists:
            for agent in results:
                agent_id = agent["agent_id"]
                if agent_id not in merged:
                    merged[agent_id] = dict(agent)
                else:
                    existing = merged[agent_id]
                    # Keep highest similarity
                    if agent["similarity"] > existing["similarity"]:
                        new_source = agent.get("match_source", "unknown")
                        old_source = existing.get("match_source", "unknown")
                        merged[agent_id] = dict(agent)
                        merged[agent_id]["match_source"] = f"{old_source}+{new_source}"
                    else:
                        # Append match source for tracking
                        old_source = existing.get("match_source", "unknown")
                        new_source = agent.get("match_source", "unknown")
                        if new_source not in old_source:
                            existing["match_source"] = f"{old_source}+{new_source}"

        result = list(merged.values())
        result.sort(key=lambda a: a["similarity"], reverse=True)
        return result

    # =========================================================================
    # MAIN LOADING METHODS
    # =========================================================================

    def _load_with_embeddings(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        Load agents using semantic search, boosted by pattern matches.

        Combines embedding-based search with file pattern and error pattern
        matching. Agents that match patterns receive a similarity boost
        in the embedding results.
        """
        # Get query embedding
        query_embedding = embed([query], input_type="query")[0]

        # Search in SQLite
        results = self.store.search(
            query_embedding=query_embedding, top_k=top_k * 2, source_type="agent"
        )

        # Convert to agent dicts
        embedding_agents: List[Dict[str, Any]] = []
        for result in results:
            embedding_agents.append(
                {
                    "agent_id": result.record.source_id,
                    "similarity": result.similarity,
                    "tier": result.record.metadata.get("tier", "unknown"),
                    "description": result.record.content[:100],
                    "match_source": "embedding",
                }
            )

        # Get pattern-based matches
        file_paths = self._extract_file_paths(query)
        file_matches = self._match_file_patterns(file_paths)
        error_matches = self._match_error_patterns(query)

        # Apply boost to embedding results that also match patterns
        pattern_agent_ids: Set[str] = set()
        for match in file_matches + error_matches:
            pattern_agent_ids.add(match["agent_id"])

        for agent in embedding_agents:
            if agent["agent_id"] in pattern_agent_ids:
                agent["similarity"] = min(1.0, agent["similarity"] + PATTERN_BOOST)

        # Merge all results
        agents = self._merge_results(embedding_agents, file_matches, error_matches)

        # Ensure some Tier 1 agents always included
        if self.always_include_tier1:
            agents = self._ensure_tier1_agents(agents, top_k)

        return agents[:top_k]

    def _load_with_keywords(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        Fallback: Load agents using keyword, file pattern, and error pattern matching.

        Enhanced from the original keyword-only approach to also check
        file patterns and error patterns from routing_config.json.
        """
        # Get matches from all three methods
        keyword_matches = self._match_keywords(query)

        file_paths = self._extract_file_paths(query)
        file_matches = self._match_file_patterns(file_paths)

        error_matches = self._match_error_patterns(query)

        # Merge results from all methods
        agents = self._merge_results(keyword_matches, file_matches, error_matches)

        # Always include code-reviewer (Tier 1) if no agents matched
        if not agents:
            agents.append(
                {
                    "agent_id": "code-reviewer",
                    "similarity": 0.5,
                    "tier": "tier-1-always-active",
                    "description": "",
                    "match_source": "default",
                }
            )

        return agents[:top_k]

    def _ensure_tier1_agents(
        self, agents: List[Dict[str, Any]], top_k: int
    ) -> List[Dict[str, Any]]:
        """Ensure at least 3 Tier 1 agents are included."""
        tier1_agents = [a for a in agents if a["tier"] == "tier-1-always-active"]

        # If we have enough Tier 1, return as-is
        if len(tier1_agents) >= 3:
            return agents

        # Add essential Tier 1 agents
        essential_tier1 = [
            "code-reviewer",
            "bug-whisperer",
            "documentation-maintainer",
        ]

        for agent_id in essential_tier1:
            if agent_id not in [a["agent_id"] for a in agents]:
                agents.append(
                    {
                        "agent_id": agent_id,
                        "similarity": 0.7,
                        "tier": "tier-1-always-active",
                        "description": "",
                        "match_source": "tier1_default",
                    }
                )

            if len([a for a in agents if a["tier"] == "tier-1-always-active"]) >= 3:
                break

        # Re-sort by similarity
        agents.sort(key=lambda a: a["similarity"], reverse=True)

        return agents


def load_relevant_agents(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Load relevant agents for a query (convenience function).

    Args:
        query: User query or task description
        top_k: Number of agents to load

    Returns:
        List of agent dicts
    """
    loader = AgentLoader()
    return loader.load(query, top_k)
