# VHS Tape Files

These `.tape` files generate animated GIF demos using [VHS](https://github.com/charmbracelet/vhs).

## Available Demos

- `quick-start.tape` - Installation and first command
- `morning-routine.tape` - Daily health check demo
- `feature-workflow.tape` - 7-phase feature development
- `power-mode.tape` - Multi-agent orchestration

## Generating GIFs

**Install VHS:**
```bash
# Windows
scoop install vhs
# OR
choco install vhs
```

**Generate a single demo:**
```bash
cd packages/popkit-core/assets/tapes
vhs quick-start.tape
```

**Generate all demos:**
```bash
cd packages/popkit-core/assets/tapes
for tape in *.tape; do vhs "$tape"; done
```

Generated GIFs will appear in `../images/`

## Usage in README

Embed in README:
```markdown
![Quick Start](packages/popkit-core/assets/images/quick-start.gif)
```
