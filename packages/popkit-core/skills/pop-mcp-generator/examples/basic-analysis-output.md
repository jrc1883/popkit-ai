# Example: Basic Project Analysis Output (No API Key)

## Project Analysis

Here's what I found about your project:

### Tech Stack Detected
- **Framework:** Next.js 14
- **Language:** TypeScript
- **Database:** PostgreSQL (via Prisma)
- **Testing:** Jest + React Testing Library

### Recommended Checks
Based on your stack, these health checks would be useful:
- [ ] Next.js dev server on port 3000
- [ ] PostgreSQL on port 5432
- [ ] Redis on port 6379 (if using caching)

### Project Structure
```
src/
├── app/           # Next.js App Router
├── components/    # React components
├── lib/           # Utilities
└── prisma/        # Database schema
```

### What Custom MCP Server Adds

With an API key, you get enhanced MCP generation:
- ✨ **Semantic tool search** - Find tools by description
- 🔍 **Project-specific health checks** - Monitor your services
- ⚡ **Custom quality tools** - Typecheck, lint, test commands
- 📊 **Embeddings** - Vector search across tools

Get a free API key: `/popkit:cloud signup`
