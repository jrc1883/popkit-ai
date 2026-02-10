# Example: Auto-Embedding Tools

import json
from datetime import datetime
from pathlib import Path

from embedding_project import auto_embed_item

# No longer needed - install popkit-shared instead
from voyage_client import VoyageClient


def export_tool_embeddings(tools: list, output_path: str):
    """Export embeddings for semantic search."""
    client = VoyageClient()

    if not client.is_available:
        print("⚠ Voyage API not available, skipping embeddings")
        return False

    descriptions = [t["description"] for t in tools]
    embeddings = client.embed(descriptions, input_type="document")

    output = {
        "generated_at": datetime.now().isoformat(),
        "model": "voyage-3.5",
        "dimension": len(embeddings[0]) if embeddings else 0,
        "tools": [
            {"name": t["name"], "description": t["description"], "embedding": emb}
            for t, emb in zip(tools, embeddings)
        ],
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(output, indent=2))
    print(f"✓ Exported {len(tools)} tool embeddings to {output_path}")
    return True


# After generating MCP server
tools = [
    {"name": "health:dev-server", "description": "Check if the Next.js..."},
    {"name": "health:database", "description": "Check database connectivity..."},
    # ... other tools
]

export_tool_embeddings(tools, ".claude/tool_embeddings.json")

# Also store in global embedding database
for tool_file in tool_files:
    success = auto_embed_item(tool_file, "mcp-tool")
    if success:
        print(f"  └─ Embedded: {tool_file}")
