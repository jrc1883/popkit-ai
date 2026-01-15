# Example: Cloud API Integration (Enhanced Mode)

import sys
from pathlib import Path

# No longer needed - install popkit-shared instead
from enhancement_detector import check_enhancement

# Check if enhancement is available
result = check_enhancement("knowledge-base")
if not result.has_api_key:
    # Provide basic project analysis (fully functional)
    print("## Project Analysis")
    # ... show detection results without generating MCP
    print("\nFor custom MCP generation: `/popkit:cloud signup` (free)")
    sys.exit(0)

# Call cloud API for generation
result = generate_mcp_server(
    project_name="my-project",
    tech_stack=["nextjs", "typescript", "prisma"],
    dev_port=3000,
    db_port=5432,
    include_embeddings=True,
    include_routines=True,
)

if result.success:
    # Write generated files to disk
    for file in result.files:
        path = Path(f".claude/mcp-servers/{project_name}-dev/{file.path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(file.content)

    print(result.instructions)
    print(f"\nGenerated {len(result.tools)} tools: {', '.join(result.tools)}")
else:
    print(f"Generation failed: {result.error}")
