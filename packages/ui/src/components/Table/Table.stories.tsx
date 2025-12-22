import type { Meta, StoryObj } from '@storybook/react'
import {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableRow,
  TableHead,
  TableCell,
  TableCaption,
} from './Table'
import { Checkbox } from '../Checkbox'
import { Badge } from '../Badge'

const meta = {
  title: 'Components/Table',
  component: Table,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Table>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: () => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Role</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell>John Doe</TableCell>
          <TableCell>john@example.com</TableCell>
          <TableCell>Admin</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>Jane Smith</TableCell>
          <TableCell>jane@example.com</TableCell>
          <TableCell>Editor</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>Bob Johnson</TableCell>
          <TableCell>bob@example.com</TableCell>
          <TableCell>Viewer</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  ),
}

export const WithCaption: Story = {
  render: () => (
    <Table>
      <TableCaption>A list of recent team members</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Joined</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell>Alice Williams</TableCell>
          <TableCell>
            <Badge variant="secondary">Active</Badge>
          </TableCell>
          <TableCell className="text-right">2024-01-15</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>Bob Chen</TableCell>
          <TableCell>
            <Badge variant="secondary">Active</Badge>
          </TableCell>
          <TableCell className="text-right">2024-02-03</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>Carol Martinez</TableCell>
          <TableCell>
            <Badge variant="outline">Pending</Badge>
          </TableCell>
          <TableCell className="text-right">2024-03-10</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  ),
}

export const WithCheckboxes: Story = {
  render: () => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-12">
            <Checkbox />
          </TableHead>
          <TableHead>Task</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Priority</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell>
            <Checkbox />
          </TableCell>
          <TableCell>Complete documentation</TableCell>
          <TableCell>
            <Badge variant="secondary">In Progress</Badge>
          </TableCell>
          <TableCell>High</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>
            <Checkbox defaultChecked />
          </TableCell>
          <TableCell>Review pull requests</TableCell>
          <TableCell>
            <Badge variant="secondary">Done</Badge>
          </TableCell>
          <TableCell>Medium</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>
            <Checkbox />
          </TableCell>
          <TableCell>Update dependencies</TableCell>
          <TableCell>
            <Badge variant="outline">Todo</Badge>
          </TableCell>
          <TableCell>Low</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  ),
}

export const WithFooter: Story = {
  render: () => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Product</TableHead>
          <TableHead className="text-right">Quantity</TableHead>
          <TableHead className="text-right">Price</TableHead>
          <TableHead className="text-right">Total</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell>Widget A</TableCell>
          <TableCell className="text-right">2</TableCell>
          <TableCell className="text-right">$10.00</TableCell>
          <TableCell className="text-right">$20.00</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>Widget B</TableCell>
          <TableCell className="text-right">1</TableCell>
          <TableCell className="text-right">$15.00</TableCell>
          <TableCell className="text-right">$15.00</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>Widget C</TableCell>
          <TableCell className="text-right">3</TableCell>
          <TableCell className="text-right">$8.00</TableCell>
          <TableCell className="text-right">$24.00</TableCell>
        </TableRow>
      </TableBody>
      <TableFooter>
        <TableRow>
          <TableCell colSpan={3}>Total</TableCell>
          <TableCell className="text-right">$59.00</TableCell>
        </TableRow>
      </TableFooter>
    </Table>
  ),
}

export const ComplexExample: Story = {
  render: () => (
    <div className="w-full">
      <Table>
        <TableCaption>Recent transactions and their status</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">
              <Checkbox />
            </TableHead>
            <TableHead>ID</TableHead>
            <TableHead>Customer</TableHead>
            <TableHead>Date</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Amount</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>
              <Checkbox />
            </TableCell>
            <TableCell className="font-medium">#3210</TableCell>
            <TableCell>John Doe</TableCell>
            <TableCell>2024-03-15</TableCell>
            <TableCell>
              <Badge variant="secondary">Completed</Badge>
            </TableCell>
            <TableCell className="text-right">$350.00</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Checkbox />
            </TableCell>
            <TableCell className="font-medium">#3211</TableCell>
            <TableCell>Jane Smith</TableCell>
            <TableCell>2024-03-16</TableCell>
            <TableCell>
              <Badge variant="outline">Pending</Badge>
            </TableCell>
            <TableCell className="text-right">$125.50</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Checkbox />
            </TableCell>
            <TableCell className="font-medium">#3212</TableCell>
            <TableCell>Bob Johnson</TableCell>
            <TableCell>2024-03-17</TableCell>
            <TableCell>
              <Badge variant="destructive">Failed</Badge>
            </TableCell>
            <TableCell className="text-right">$89.99</TableCell>
          </TableRow>
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell colSpan={5}>Total Revenue</TableCell>
            <TableCell className="text-right">$565.49</TableCell>
          </TableRow>
        </TableFooter>
      </Table>
    </div>
  ),
}
