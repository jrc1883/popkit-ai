import type { Meta, StoryObj } from '@storybook/react'
import { Checkbox } from './Checkbox'
import { Label } from '../Label'

const meta = {
  title: 'Components/Checkbox',
  component: Checkbox,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    disabled: {
      control: 'boolean',
    },
  },
} satisfies Meta<typeof Checkbox>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {},
}

export const Checked: Story = {
  args: {
    defaultChecked: true,
  },
}

export const Disabled: Story = {
  args: {
    disabled: true,
  },
}

export const DisabledChecked: Story = {
  args: {
    disabled: true,
    defaultChecked: true,
  },
}

export const WithLabel: Story = {
  render: () => (
    <div className="flex items-center space-x-2">
      <Checkbox id="terms" />
      <Label htmlFor="terms">Accept terms and conditions</Label>
    </div>
  ),
}

export const MultipleOptions: Story = {
  render: () => (
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <Checkbox id="option1" defaultChecked />
        <Label htmlFor="option1">Option 1</Label>
      </div>
      <div className="flex items-center space-x-2">
        <Checkbox id="option2" />
        <Label htmlFor="option2">Option 2</Label>
      </div>
      <div className="flex items-center space-x-2">
        <Checkbox id="option3" />
        <Label htmlFor="option3">Option 3</Label>
      </div>
    </div>
  ),
}

export const FormExample: Story = {
  render: () => (
    <div className="w-80 space-y-6 rounded-lg border p-6">
      <div>
        <h3 className="mb-4 text-lg font-semibold">Notification Preferences</h3>
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Checkbox id="email" defaultChecked />
            <div className="grid gap-1.5 leading-none">
              <Label htmlFor="email" className="text-sm font-medium">
                Email notifications
              </Label>
              <p className="text-sm text-muted-foreground">
                Receive emails about your account activity
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="marketing" />
            <div className="grid gap-1.5 leading-none">
              <Label htmlFor="marketing" className="text-sm font-medium">
                Marketing emails
              </Label>
              <p className="text-sm text-muted-foreground">
                Receive emails about new products and features
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="social" defaultChecked />
            <div className="grid gap-1.5 leading-none">
              <Label htmlFor="social" className="text-sm font-medium">
                Social notifications
              </Label>
              <p className="text-sm text-muted-foreground">
                Receive notifications about comments and likes
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  ),
}
