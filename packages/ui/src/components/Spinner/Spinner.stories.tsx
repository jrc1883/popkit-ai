import type { Meta, StoryObj } from '@storybook/react'
import { Spinner } from './Spinner'
import { Button } from '../Button'

const meta = {
  title: 'Components/Spinner',
  component: Spinner,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: 'select',
      options: ['sm', 'default', 'lg'],
    },
  },
} satisfies Meta<typeof Spinner>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {},
}

export const Small: Story = {
  args: {
    size: 'sm',
  },
}

export const Large: Story = {
  args: {
    size: 'lg',
  },
}

export const AllSizes: Story = {
  render: () => (
    <div className="flex items-center gap-4">
      <Spinner size="sm" />
      <Spinner size="default" />
      <Spinner size="lg" />
    </div>
  ),
}

export const InButton: Story = {
  render: () => (
    <Button disabled>
      <Spinner size="sm" className="mr-2" />
      Loading...
    </Button>
  ),
}

export const LoadingStates: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      <Button disabled>
        <Spinner size="sm" className="mr-2" />
        Saving...
      </Button>
      <Button variant="secondary" disabled>
        <Spinner size="sm" className="mr-2" />
        Processing...
      </Button>
      <Button variant="outline" disabled>
        <Spinner size="sm" className="mr-2" />
        Please wait...
      </Button>
    </div>
  ),
}

export const Centered: Story = {
  render: () => (
    <div className="flex h-64 w-96 items-center justify-center rounded-lg border">
      <div className="text-center">
        <Spinner className="mx-auto" />
        <p className="mt-2 text-sm text-muted-foreground">Loading content...</p>
      </div>
    </div>
  ),
}

export const WithText: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <Spinner />
      <span className="text-sm">Loading...</span>
    </div>
  ),
}
