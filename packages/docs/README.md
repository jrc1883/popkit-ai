# PopKit Documentation

This package contains the PopKit documentation website built with [Astro](https://astro.build) and [Starlight](https://starlight.astro.build).

## Development

```bash
# From repository root
npm run docs:dev

# Or from this directory
npm run dev
```

The site will be available at `http://localhost:4321`.

## Building

```bash
# From repository root
npm run docs:build

# Or from this directory
npm run build
```

## Preview Production Build

```bash
# From repository root
npm run docs:preview

# Or from this directory
npm run preview
```

## Structure

```
src/
├── content/
│   └── docs/           # Documentation content (MDX files)
│       ├── index.mdx   # Landing page
│       ├── getting-started/
│       ├── concepts/
│       ├── features/
│       ├── guides/
│       └── reference/
└── styles/
    └── custom.css      # Custom styling
```

## Writing Documentation

Documentation is written in MDX (Markdown with JSX support). Place new documentation files in the appropriate subdirectory under `src/content/docs/`.

See the [Starlight documentation](https://starlight.astro.build) for more information on available features and components.
