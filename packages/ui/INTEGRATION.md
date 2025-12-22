# @elshaddai/ui Integration Guide

This guide walks you through integrating the shared UI component library into your ElShaddai monorepo application.

## Prerequisites

- Your app is in the ElShaddai monorepo workspace
- Your app uses React 18+ or React 19
- Your app uses Tailwind CSS

## Quick Start

### 1. Add the Dependency

From your app's directory:

```bash
pnpm add @elshaddai/ui@workspace:*
```

### 2. Configure Tailwind CSS

The UI library uses Tailwind CSS with custom design tokens. You need to extend your Tailwind config to include the UI library's styles.

**Option A: Import the UI config (Recommended)**

```js
// tailwind.config.js
import { join } from 'path'

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './src/**/*.{ts,tsx}',
    // Include UI library components
    join(__dirname, '../../packages/ui/src/**/*.{ts,tsx}')
  ],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        success: {
          DEFAULT: 'hsl(var(--success))',
          foreground: 'hsl(var(--success-foreground))',
        },
        warning: {
          DEFAULT: 'hsl(var(--warning))',
          foreground: 'hsl(var(--warning-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [],
}
```

**Option B: Copy from example (if you have custom config)**

See `packages/ui/tailwind.config.js` for the full configuration and adapt to your needs.

### 3. Add CSS Variables

Add these CSS variables to your global CSS file (e.g., `globals.css` or `app.css`):

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

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
    --success: 142.1 76.2% 36.3%;
    --success-foreground: 355.7 100% 97.3%;
    --warning: 32.1 94.6% 43.7%;
    --warning-foreground: 0 0% 100%;
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
    --success: 142.1 70.6% 45.3%;
    --success-foreground: 144.9 80.4% 10%;
    --warning: 32.1 94.6% 43.7%;
    --warning-foreground: 20 14.3% 4.1%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

### 4. Add lucide-react Dependency

The UI library uses lucide-react for icons:

```bash
pnpm add lucide-react
```

### 5. Import and Use Components

```typescript
import { Button, Input, Card, CardHeader, CardTitle } from '@elshaddai/ui'

export function MyComponent() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Hello World</CardTitle>
      </CardHeader>
      <div className="p-6">
        <Input placeholder="Enter text..." />
        <Button className="mt-4">Submit</Button>
      </div>
    </Card>
  )
}
```

## Available Components

### Tier 1 Components (Current)

- **Button** - Primary action component with 6 variants
- **Input** - Form input with validation support
- **Label** - Form labels with accessibility
- **Card** - Container with header, content, footer
- **Badge** - Status indicators
- **Checkbox** - Boolean input
- **Dialog** - Modal dialogs
- **Spinner** - Loading indicators
- **Select** - Dropdown selection
- **DropdownMenu** - Context menus
- **RadioGroup** - Single selection from multiple options

### Component Examples

#### Button

```typescript
<Button variant="default">Default</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="link">Link</Button>

<Button size="sm">Small</Button>
<Button size="default">Default</Button>
<Button size="lg">Large</Button>
<Button size="icon">X</Button>
```

#### Input

```typescript
<Input type="email" placeholder="Email" />
<Input type="password" placeholder="Password" />
<Input disabled placeholder="Disabled" />
```

#### Card

```typescript
<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Card description goes here</CardDescription>
  </CardHeader>
  <CardContent>
    <p>Card content</p>
  </CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

#### Dialog

```typescript
<Dialog>
  <DialogTrigger asChild>
    <Button>Open Dialog</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Dialog Title</DialogTitle>
      <DialogDescription>Dialog description</DialogDescription>
    </DialogHeader>
    <div>Dialog content</div>
    <DialogFooter>
      <Button variant="outline">Cancel</Button>
      <Button>Confirm</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

#### Select

```typescript
<Select onValueChange={(value) => console.log(value)}>
  <SelectTrigger>
    <SelectValue placeholder="Choose option" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="option1">Option 1</SelectItem>
    <SelectItem value="option2">Option 2</SelectItem>
  </SelectContent>
</Select>
```

## Migration from Existing Components

If your app has existing UI components, follow these steps:

### 1. Audit Your Components

Create a list of all UI components in your app:

```bash
# Find all component files
find src -name "*.tsx" -o -name "*.ts" | grep -i "component\|ui" > component-audit.txt
```

### 2. Identify Duplicates

Compare your components with @elshaddai/ui:
- ✅ Button → Use `<Button>` from @elshaddai/ui
- ✅ Input → Use `<Input>` from @elshaddai/ui
- ✅ Card → Use `<Card>` from @elshaddai/ui
- ⚠️ CustomButton with special logic → Keep or extend Button
- ❌ DataTable → Not in Tier 1, keep custom

### 3. Replace Imports

**Before:**
```typescript
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
```

**After:**
```typescript
import { Button, Input } from '@elshaddai/ui'
```

### 4. Handle Custom Variants

If you have custom variants, you can extend the components:

```typescript
import { Button, type ButtonProps } from '@elshaddai/ui'
import { cva } from 'class-variance-authority'

const customButtonVariants = cva('', {
  variants: {
    variant: {
      premium: 'bg-gradient-to-r from-purple-500 to-pink-500',
    },
  },
})

export function PremiumButton(props: ButtonProps) {
  return <Button className={customButtonVariants({ variant: 'premium' })} {...props} />
}
```

### 5. Remove Old Files

After confirming everything works:

```bash
# Back up first!
git add .
git commit -m "backup before removing old components"

# Remove old component files
rm -rf src/components/ui/button.tsx
rm -rf src/components/ui/input.tsx
# ... etc
```

## Testing Integration

### Visual Testing Checklist

- [ ] Light mode renders correctly
- [ ] Dark mode renders correctly
- [ ] All variants display properly
- [ ] Hover states work
- [ ] Focus states are visible
- [ ] Disabled states look correct

### Accessibility Testing

- [ ] Keyboard navigation works
- [ ] Screen reader announces correctly
- [ ] Focus trap works in dialogs
- [ ] ARIA attributes are present

### Functional Testing

- [ ] Forms submit correctly
- [ ] Validation displays errors
- [ ] Dialogs open and close
- [ ] Selects update state

## Troubleshooting

### Styles not applying

**Problem:** Components render but don't have correct styles

**Solution:**
1. Verify Tailwind content paths include `packages/ui/src`
2. Check CSS variables are defined in global CSS
3. Ensure `@tailwind` directives are at the top of CSS file
4. Rebuild your app

### Type errors

**Problem:** TypeScript can't find component types

**Solution:**
1. Verify `@elshaddai/ui` is in dependencies
2. Run `pnpm install` from monorepo root
3. Check `node_modules/@elshaddai/ui/dist/index.d.ts` exists
4. Restart your TypeScript server

### Dark mode not working

**Problem:** Dark mode variables don't apply

**Solution:**
1. Ensure `.dark` class is on `<html>` or `<body>`
2. Check CSS variables are defined for both `:root` and `.dark`
3. Verify your dark mode toggle sets the class correctly

### lucide-react icons missing

**Problem:** Icons don't render or throw errors

**Solution:**
```bash
pnpm add lucide-react
```

### Build fails with "Cannot find module"

**Problem:** Build can't resolve @elshaddai/ui

**Solution:**
1. Ensure package is built: `cd packages/ui && pnpm build`
2. Check workspace protocol: `"@elshaddai/ui": "workspace:*"`
3. Run `pnpm install` from monorepo root

## Next Steps

After successful integration:

1. **Test thoroughly** - Ensure all components work in your app
2. **Update documentation** - Document any app-specific patterns
3. **Share findings** - Update this guide with learnings
4. **Help others** - Assist other apps with integration

## Support

- **Issues:** Create a GitHub issue with the `@elshaddai/ui` label
- **Questions:** Ask in team chat or create a discussion
- **Contributing:** See `packages/ui/README.md` for component guidelines
