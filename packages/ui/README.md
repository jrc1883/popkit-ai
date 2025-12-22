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

### Tier 1 (Essential) - ✅ Complete

All 11 Tier 1 components are implemented with comprehensive variants:

- ✅ **Button** - 12 variants (default, secondary, destructive, ghost, outline, link, success, warning, flat, flat-destructive, flat-outline, flat-secondary) + loading state + 7 sizes
- ✅ **Input** - All HTML input types + error/success states + left/right icons + 3 sizes (sm, default, lg) + enhanced focus states
- ✅ **Card** - Compound component (Header, Title, Description, Action, Content, Footer) + auto spacing with gap-6 + grid header layout + data-slot attributes + rounded-xl
- ✅ **Label** - Form labels with accessibility + flex layout for icons + data-slot attribute + select-none + group disabled states
- ✅ **Dialog** - Modal with overlay, header, footer + data-slot attributes + gap-2 spacing + rounded-xs close button + mobile-optimized width
- ✅ **DropdownMenu** - Full menu system with checkboxes, radio groups, sub-menus + data-slot attributes + destructive variant + gap-2 spacing + scrollable content + enhanced icon handling
- ✅ **Select** - Dropdown select with groups, labels, scroll buttons
- ✅ **Checkbox** - Boolean input with visual indicator
- ✅ **RadioGroup** - Single selection from multiple options
- ✅ **Badge** - 4 variants (default, secondary, destructive, outline)
- ✅ **Spinner** - 3 sizes (sm, default, lg)

### Tier 2 (Common) - ✅ Complete

- ✅ **Table** - Compound table component (Header, Body, Footer, Row, Head, Cell, Caption) + data-slot attributes + tight spacing + whitespace-nowrap + checkbox positioning + horizontal scroll
- ✅ **Tabs** - Tab navigation (Root, List, Trigger, Content) + data-slot attributes + flex layout + gap-1.5 + enhanced focus states + dark mode + icon sizing
- ✅ **Accordion** - Expandable sections (Root, Item, Trigger, Content) + data-slot attributes + ChevronDown icon + smooth animations + border styling
- ✅ **Alert** - Notification banners (Alert, Title, Description) + data-slot attributes + 2 variants (default, destructive) + icon support + role="alert"
- ✅ **Toast** - Radix UI toast notifications (Toast, Provider, Viewport, Title, Description, Close, Action) + data-slot attributes + 2 variants + swipe gestures + animations
- ✅ **Tooltip** - Radix UI tooltips (Tooltip, Provider, Trigger, Content) + data-slot attributes + Portal + animations + configurable sideOffset
- ✅ **Avatar** - Radix UI avatars (Avatar, Image, Fallback) + data-slot attributes + forwardRef + rounded-full + image fallback support
- ✅ **Progress** - Radix UI progress bar + data-slot attributes + smooth transitions + value-based fill + accessibility (role, aria-attributes)
- ✅ **Skeleton** - Loading placeholders + data-slot attributes + forwardRef + animate-pulse + customizable shapes (avatar, text, card)

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

# Storybook (component documentation and testing)
pnpm storybook        # Start Storybook dev server at localhost:6006
pnpm build-storybook  # Build static Storybook site
```

## Storybook

This package includes comprehensive Storybook documentation for all components. Storybook provides:
- **Interactive component playground** - Test components with different props and states
- **Visual documentation** - See all component variants and use cases
- **Accessibility testing** - Built-in a11y addon for accessibility checks
- **Responsive preview** - Test components at different viewport sizes

### Running Storybook

```bash
pnpm storybook
```

Then open [http://localhost:6006](http://localhost:6006) in your browser.

### Component Stories

All 20 components have complete story files covering:
- **Default states** - Basic component usage
- **All variants** - Every variant and size option
- **Interactive examples** - Real-world use cases
- **Edge cases** - Error states, disabled states, loading states

Stories are located in `src/components/[ComponentName]/[ComponentName].stories.tsx`

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
