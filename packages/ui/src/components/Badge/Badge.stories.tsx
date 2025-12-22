import type { Meta, StoryObj } from '@storybook/react'
import { Badge } from './Badge'

const meta = {
  title: 'Components/Badge',
  component: Badge,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'secondary', 'destructive', 'outline'],
    },
  },
} satisfies Meta<typeof Badge>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    children: 'Badge',
  },
}

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Secondary',
  },
}

export const Destructive: Story = {
  args: {
    variant: 'destructive',
    children: 'Destructive',
  },
}

export const Outline: Story = {
  args: {
    variant: 'outline',
    children: 'Outline',
  },
}

export const AllVariants: Story = {
  render: () => (
    <div className="flex gap-2">
      <Badge variant="default">Default</Badge>
      <Badge variant="secondary">Secondary</Badge>
      <Badge variant="destructive">Destructive</Badge>
      <Badge variant="outline">Outline</Badge>
    </div>
  ),
}

export const WithStatus: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <span className="text-sm">Active:</span>
        <Badge variant="secondary">Online</Badge>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm">Error:</span>
        <Badge variant="destructive">Failed</Badge>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm">Warning:</span>
        <Badge variant="outline">Pending</Badge>
      </div>
    </div>
  ),
}

export const WithDot: Story = {
  render: () => (
    <div className="flex gap-2">
      <Badge>
        <span className="mr-1 h-2 w-2 rounded-full bg-green-500" />
        Active
      </Badge>
      <Badge variant="secondary">
        <span className="mr-1 h-2 w-2 rounded-full bg-yellow-500" />
        Pending
      </Badge>
      <Badge variant="destructive">
        <span className="mr-1 h-2 w-2 rounded-full bg-red-500" />
        Error
      </Badge>
    </div>
  ),
}

export const InCard: Story = {
  render: () => (
    <div className="w-80 rounded-lg border p-4">
      <div className="mb-4 flex items-start justify-between">
        <div>
          <h3 className="font-semibold">Deploy to Production</h3>
          <p className="text-sm text-muted-foreground">
            Deploy the latest changes to production environment
          </p>
        </div>
        <Badge variant="secondary">In Progress</Badge>
      </div>
      <div className="flex gap-2">
        <Badge variant="outline" className="text-xs">
          React
        </Badge>
        <Badge variant="outline" className="text-xs">
          TypeScript
        </Badge>
        <Badge variant="outline" className="text-xs">
          Cloudflare
        </Badge>
      </div>
    </div>
  ),
}
