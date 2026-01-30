# Output Formats

## List Projects Output

```
Found 13 projects in workspace:

| Name          | Type | Path                  |
|---------------|------|-----------------------|
| genesis       | app  | apps/genesis          |
| optimus       | app  | apps/optimus          |
| matrix-engine | pkg  | packages/matrix       |
| ...

Usage: /popkit:project reference <project-name>
```

## Project Context Display

```
===================================================================
                         Project: genesis
===================================================================

Path: /workspace/apps/genesis

## Overview
{package.json description}

## Instructions (CLAUDE.md)
{Full CLAUDE.md content}

## Dependencies (package.json)
{dependencies section from package.json}

## Current Status (.claude/STATUS.json)
{STATUS.json if exists}

## README
{README.md content}
```

## Missing Files

If a file doesn't exist, skip gracefully:

```
## Instructions (CLAUDE.md)
(No CLAUDE.md found in this project)

## Current Status (.claude/STATUS.json)
(No STATUS.json found in this project)
```
