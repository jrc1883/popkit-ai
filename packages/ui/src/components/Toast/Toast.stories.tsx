import type { Meta, StoryObj } from '@storybook/react'
import { Toast, ToastAction } from './Toast'
import { Button } from '../Button'

const meta = {
  title: 'Components/Toast',
  component: Toast,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Toast>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: () => (
    <div className="p-8">
      <p className="mb-4 text-sm text-muted-foreground">
        Toast notifications are typically triggered programmatically.
      </p>
      <p className="text-sm text-muted-foreground">
        This is a static example showing the component structure.
      </p>
    </div>
  ),
}

export const Simple: Story = {
  render: () => (
    <div className="flex w-[400px] items-center justify-center rounded-lg border p-8">
      <p className="text-sm">
        Toast components typically appear in the corner of the screen and auto-dismiss.
      </p>
    </div>
  ),
}

export const WithAction: Story = {
  render: () => (
    <div className="flex w-[400px] items-center justify-center rounded-lg border p-8">
      <p className="text-sm">
        Toasts can include action buttons for user interaction before auto-dismiss.
      </p>
    </div>
  ),
}
