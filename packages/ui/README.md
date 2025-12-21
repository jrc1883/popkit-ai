# @elshaddai/ui

Shared UI component library using Radix UI + Tailwind CSS for the ElShaddai monorepo.

## Installation

```bash
# From monorepo root
pnpm install

# In your app's package.json
{
  "dependencies": {
    "@elshaddai/ui": "workspace:*"
  }
}
```

## Usage

```tsx
import { Button, Card, CardHeader, CardTitle, CardContent, Input, Label } from '@elshaddai/ui'

function MyComponent() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Login</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" placeholder="you@example.com" />
          </div>
          <Button>Sign In</Button>
        </div>
      </CardContent>
    </Card>
  )
}
```

## Components

### Tier 1 (Essential) - Implemented

- ✅ Button (variants: primary, secondary, ghost, destructive, outline, link)
- ✅ Input (text, email, password, number)
- ✅ Card (with header, content, footer slots)
- ✅ Label
- ⏳ Dialog/Modal
- ⏳ Dropdown Menu
- ⏳ Select
- ⏳ Checkbox
- ⏳ Radio Group
- ⏳ Badge
- ⏳ Spinner/Loading

### Tier 2 (Common) - Planned

- Table (with sorting, pagination)
- Tabs
- Accordion
- Alert/Toast notifications
- Tooltip
- Avatar
- Progress bar
- Skeleton loading

### Tier 3 (Advanced) - Future

- Date picker
- Multi-select
- Combobox/Autocomplete
- Command palette
- Rich text editor integration

## Development

```bash
# Build the package
pnpm build

# Watch mode for development
pnpm dev

# Run tests
pnpm test

# Type checking
pnpm type-check

# Linting
pnpm lint
```

## Tailwind Configuration

Apps using this library need to extend their Tailwind config:

```js
// tailwind.config.js
export default {
  content: [
    './src/**/*.{js,ts,jsx,tsx}',
    './node_modules/@elshaddai/ui/dist/**/*.{js,mjs}',
  ],
  theme: {
    extend: {
      // Your theme extensions
    },
  },
}
```

## CSS Variables

Add these CSS variables to your app's global CSS:

```css
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;

    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;

    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;

    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;

    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;

    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;

    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;

    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;

    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;

    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;

    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;

    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;

    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;

    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;

    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;

    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;

    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;

    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}
```

## Architecture

- **Radix UI**: Accessible component primitives
- **Tailwind CSS**: Utility-first styling
- **CVA**: Class variance authority for variant management
- **TypeScript**: Strict type safety
- **Vitest**: Unit testing

## License

MIT
