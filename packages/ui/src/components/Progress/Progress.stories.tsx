import type { Meta, StoryObj } from '@storybook/react'
import { Progress } from './Progress'

const meta = {
  title: 'Components/Progress',
  component: Progress,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    value: {
      control: { type: 'range', min: 0, max: 100, step: 1 },
    },
  },
} satisfies Meta<typeof Progress>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    value: 50,
    className: 'w-[400px]',
  },
}

export const Zero: Story = {
  args: {
    value: 0,
    className: 'w-[400px]',
  },
}

export const Complete: Story = {
  args: {
    value: 100,
    className: 'w-[400px]',
  },
}

export const AllStates: Story = {
  render: () => (
    <div className="w-[400px] space-y-4">
      <div>
        <div className="mb-2 flex justify-between text-sm">
          <span>0%</span>
        </div>
        <Progress value={0} />
      </div>
      <div>
        <div className="mb-2 flex justify-between text-sm">
          <span>25%</span>
        </div>
        <Progress value={25} />
      </div>
      <div>
        <div className="mb-2 flex justify-between text-sm">
          <span>50%</span>
        </div>
        <Progress value={50} />
      </div>
      <div>
        <div className="mb-2 flex justify-between text-sm">
          <span>75%</span>
        </div>
        <Progress value={75} />
      </div>
      <div>
        <div className="mb-2 flex justify-between text-sm">
          <span>100%</span>
        </div>
        <Progress value={100} />
      </div>
    </div>
  ),
}

export const WithLabel: Story = {
  render: () => (
    <div className="w-[400px] space-y-4">
      <div>
        <div className="mb-2 flex justify-between text-sm">
          <span className="text-muted-foreground">Uploading file...</span>
          <span className="font-medium">33%</span>
        </div>
        <Progress value={33} />
      </div>
      <div>
        <div className="mb-2 flex justify-between text-sm">
          <span className="text-muted-foreground">Processing data...</span>
          <span className="font-medium">67%</span>
        </div>
        <Progress value={67} />
      </div>
      <div>
        <div className="mb-2 flex justify-between text-sm">
          <span className="text-muted-foreground">Installation complete</span>
          <span className="font-medium">100%</span>
        </div>
        <Progress value={100} />
      </div>
    </div>
  ),
}

export const Indeterminate: Story = {
  render: () => (
    <div className="w-[400px] space-y-4">
      <div>
        <div className="mb-2 text-sm text-muted-foreground">Loading...</div>
        <Progress />
      </div>
    </div>
  ),
}

export const CustomColor: Story = {
  render: () => (
    <div className="w-[400px] space-y-4">
      <div>
        <div className="mb-2 text-sm">Success (green)</div>
        <Progress
          value={75}
          className="[&>[data-slot=progress-indicator]]:bg-green-500"
        />
      </div>
      <div>
        <div className="mb-2 text-sm">Warning (yellow)</div>
        <Progress
          value={50}
          className="[&>[data-slot=progress-indicator]]:bg-yellow-500"
        />
      </div>
      <div>
        <div className="mb-2 text-sm">Error (red)</div>
        <Progress
          value={25}
          className="[&>[data-slot=progress-indicator]]:bg-red-500"
        />
      </div>
    </div>
  ),
}
