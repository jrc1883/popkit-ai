import type { Meta, StoryObj } from '@storybook/react'
import { RadioGroup, RadioGroupItem } from './RadioGroup'
import { Label } from '../Label'

const meta = {
  title: 'Components/RadioGroup',
  component: RadioGroup,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof RadioGroup>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: () => (
    <RadioGroup defaultValue="option-1">
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-1" id="option-1" />
        <Label htmlFor="option-1">Option 1</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-2" id="option-2" />
        <Label htmlFor="option-2">Option 2</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-3" id="option-3" />
        <Label htmlFor="option-3">Option 3</Label>
      </div>
    </RadioGroup>
  ),
}

export const WithDescriptions: Story = {
  render: () => (
    <RadioGroup defaultValue="comfortable" className="space-y-4">
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="default" id="r1" />
        <div className="grid gap-1.5">
          <Label htmlFor="r1" className="font-medium">
            Default
          </Label>
          <p className="text-sm text-muted-foreground">The default spacing option</p>
        </div>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="comfortable" id="r2" />
        <div className="grid gap-1.5">
          <Label htmlFor="r2" className="font-medium">
            Comfortable
          </Label>
          <p className="text-sm text-muted-foreground">More breathing room between items</p>
        </div>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="compact" id="r3" />
        <div className="grid gap-1.5">
          <Label htmlFor="r3" className="font-medium">
            Compact
          </Label>
          <p className="text-sm text-muted-foreground">Minimal spacing for dense layouts</p>
        </div>
      </div>
    </RadioGroup>
  ),
}

export const PaymentMethod: Story = {
  render: () => (
    <div className="w-80 space-y-6 rounded-lg border p-6">
      <div>
        <h3 className="mb-4 text-lg font-semibold">Payment Method</h3>
        <RadioGroup defaultValue="card" className="space-y-4">
          <div className="flex items-center space-x-2 rounded-lg border p-4">
            <RadioGroupItem value="card" id="card" />
            <Label htmlFor="card" className="flex flex-1 cursor-pointer flex-col">
              <span className="font-medium">Credit Card</span>
              <span className="text-sm text-muted-foreground">
                Pay with Visa, Mastercard, or Amex
              </span>
            </Label>
          </div>
          <div className="flex items-center space-x-2 rounded-lg border p-4">
            <RadioGroupItem value="paypal" id="paypal" />
            <Label htmlFor="paypal" className="flex flex-1 cursor-pointer flex-col">
              <span className="font-medium">PayPal</span>
              <span className="text-sm text-muted-foreground">
                Pay with your PayPal account
              </span>
            </Label>
          </div>
          <div className="flex items-center space-x-2 rounded-lg border p-4">
            <RadioGroupItem value="bank" id="bank" />
            <Label htmlFor="bank" className="flex flex-1 cursor-pointer flex-col">
              <span className="font-medium">Bank Transfer</span>
              <span className="text-sm text-muted-foreground">
                Direct bank transfer (2-3 business days)
              </span>
            </Label>
          </div>
        </RadioGroup>
      </div>
    </div>
  ),
}

export const Disabled: Story = {
  render: () => (
    <RadioGroup defaultValue="option-1" disabled>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-1" id="d1" />
        <Label htmlFor="d1">Disabled selected</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-2" id="d2" />
        <Label htmlFor="d2">Disabled unselected</Label>
      </div>
    </RadioGroup>
  ),
}
