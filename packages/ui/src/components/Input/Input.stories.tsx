import type { Meta, StoryObj } from '@storybook/react'
import { Input } from './Input'
import { Mail, Search, Lock } from 'lucide-react'

const meta = {
  title: 'Components/Input',
  component: Input,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    type: {
      control: 'select',
      options: ['text', 'email', 'password', 'number', 'tel', 'url', 'search'],
    },
    size: {
      control: 'select',
      options: ['sm', 'default', 'lg'],
    },
    error: {
      control: 'boolean',
    },
    success: {
      control: 'boolean',
    },
    disabled: {
      control: 'boolean',
    },
  },
} satisfies Meta<typeof Input>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    placeholder: 'Enter text...',
  },
}

export const Email: Story = {
  args: {
    type: 'email',
    placeholder: 'you@example.com',
  },
}

export const Password: Story = {
  args: {
    type: 'password',
    placeholder: 'Enter password',
  },
}

export const WithError: Story = {
  args: {
    placeholder: 'Enter email',
    error: true,
  },
}

export const WithSuccess: Story = {
  args: {
    placeholder: 'Enter email',
    success: true,
  },
}

export const Small: Story = {
  args: {
    size: 'sm',
    placeholder: 'Small input',
  },
}

export const Large: Story = {
  args: {
    size: 'lg',
    placeholder: 'Large input',
  },
}

export const Disabled: Story = {
  args: {
    placeholder: 'Disabled input',
    disabled: true,
  },
}

export const WithLeftIcon: Story = {
  render: () => (
    <div className="relative w-80">
      <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input className="pl-10" placeholder="Email with icon" type="email" />
    </div>
  ),
}

export const WithRightIcon: Story = {
  render: () => (
    <div className="relative w-80">
      <Input className="pr-10" placeholder="Search..." type="search" />
      <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
    </div>
  ),
}

export const AllStates: Story = {
  render: () => (
    <div className="flex w-80 flex-col gap-4">
      <Input placeholder="Default state" />
      <Input placeholder="Error state" error />
      <Input placeholder="Success state" success />
      <Input placeholder="Disabled state" disabled />
    </div>
  ),
}

export const AllSizes: Story = {
  render: () => (
    <div className="flex w-80 flex-col gap-4">
      <Input size="sm" placeholder="Small input" />
      <Input size="default" placeholder="Default input" />
      <Input size="lg" placeholder="Large input" />
    </div>
  ),
}
