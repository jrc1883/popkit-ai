# Use Cases

## Cross-Project Integration

```
User: "Load context from the genesis project"
→ Invoke pop-project-reference with argument "genesis"
→ Display CLAUDE.md, dependencies, README
→ User can now understand genesis APIs and integrate
```

## API Discovery

```
User: "What APIs does the optimus service expose?"
→ Invoke pop-project-reference with "optimus"
→ User reads API documentation from README/CLAUDE.md
→ Discovers REST endpoints, GraphQL schema, etc.
```

## Dependency Analysis

```
User: "Show me what matrix-engine depends on"
→ Invoke pop-project-reference with "matrix-engine"
→ Display package.json dependencies section
→ User can see all dependencies and versions
```

## Cross-Project Status Check

```
User: "What's the status of the auth-service project?"
→ Invoke pop-project-reference with "auth-service"
→ Read STATUS.json section
→ Shows last commit, current branch, outstanding work
```

## Architecture Understanding

```
User: "How does the gateway service work?"
→ Invoke pop-project-reference with "gateway"
→ Display CLAUDE.md with architecture notes
→ Display README with implementation details
→ User gains full context without manual file reading
```
