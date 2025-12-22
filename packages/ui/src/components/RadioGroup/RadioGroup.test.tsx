import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RadioGroup, RadioGroupItem } from './RadioGroup'
import { Label } from '../Label'

describe('RadioGroup', () => {
  it('renders radio group with items', () => {
    render(
      <RadioGroup>
        <div>
          <RadioGroupItem value="option1" id="option1" />
          <Label htmlFor="option1">Option 1</Label>
        </div>
        <div>
          <RadioGroupItem value="option2" id="option2" />
          <Label htmlFor="option2">Option 2</Label>
        </div>
      </RadioGroup>
    )

    expect(screen.getByRole('radiogroup')).toBeInTheDocument()
    expect(screen.getByLabelText('Option 1')).toBeInTheDocument()
    expect(screen.getByLabelText('Option 2')).toBeInTheDocument()
  })

  it('allows selecting a radio item', async () => {
    const user = userEvent.setup()
    render(
      <RadioGroup>
        <div>
          <RadioGroupItem value="option1" id="option1" />
          <Label htmlFor="option1">Option 1</Label>
        </div>
        <div>
          <RadioGroupItem value="option2" id="option2" />
          <Label htmlFor="option2">Option 2</Label>
        </div>
      </RadioGroup>
    )

    const option1 = screen.getByLabelText('Option 1')
    const option2 = screen.getByLabelText('Option 2')

    await user.click(option1)
    expect(option1).toHaveAttribute('data-state', 'checked')
    expect(option2).toHaveAttribute('data-state', 'unchecked')

    await user.click(option2)
    expect(option1).toHaveAttribute('data-state', 'unchecked')
    expect(option2).toHaveAttribute('data-state', 'checked')
  })

  it('handles defaultValue prop', () => {
    render(
      <RadioGroup defaultValue="option2">
        <RadioGroupItem value="option1" id="option1" aria-label="Option 1" />
        <RadioGroupItem value="option2" id="option2" aria-label="Option 2" />
      </RadioGroup>
    )

    const option1 = screen.getByRole('radio', { name: 'Option 1' })
    const option2 = screen.getByRole('radio', { name: 'Option 2' })

    expect(option1).toHaveAttribute('data-state', 'unchecked')
    expect(option2).toHaveAttribute('data-state', 'checked')
  })

  it('handles controlled value prop', () => {
    const { rerender } = render(
      <RadioGroup value="option1">
        <RadioGroupItem value="option1" id="option1" aria-label="Option 1" />
        <RadioGroupItem value="option2" id="option2" aria-label="Option 2" />
      </RadioGroup>
    )

    const option1 = screen.getByRole('radio', { name: 'Option 1' })
    const option2 = screen.getByRole('radio', { name: 'Option 2' })

    expect(option1).toHaveAttribute('data-state', 'checked')
    expect(option2).toHaveAttribute('data-state', 'unchecked')

    rerender(
      <RadioGroup value="option2">
        <RadioGroupItem value="option1" id="option1" aria-label="Option 1" />
        <RadioGroupItem value="option2" id="option2" aria-label="Option 2" />
      </RadioGroup>
    )

    expect(option1).toHaveAttribute('data-state', 'unchecked')
    expect(option2).toHaveAttribute('data-state', 'checked')
  })

  it('calls onValueChange when selection changes', async () => {
    const user = userEvent.setup()
    let selectedValue = ''
    const handleValueChange = (value: string) => {
      selectedValue = value
    }

    render(
      <RadioGroup onValueChange={handleValueChange}>
        <div>
          <RadioGroupItem value="option1" id="option1" />
          <Label htmlFor="option1">Option 1</Label>
        </div>
        <div>
          <RadioGroupItem value="option2" id="option2" />
          <Label htmlFor="option2">Option 2</Label>
        </div>
      </RadioGroup>
    )

    await user.click(screen.getByLabelText('Option 1'))
    expect(selectedValue).toBe('option1')

    await user.click(screen.getByLabelText('Option 2'))
    expect(selectedValue).toBe('option2')
  })

  it('can be disabled', () => {
    render(
      <RadioGroup disabled>
        <RadioGroupItem value="option1" id="option1" />
      </RadioGroup>
    )

    const radioItem = screen.getByRole('radio')
    expect(radioItem).toBeDisabled()
  })

  it('forwards ref to RadioGroup', () => {
    const ref = { current: null }
    render(
      <RadioGroup ref={ref as React.RefObject<HTMLDivElement>}>
        <RadioGroupItem value="option1" />
      </RadioGroup>
    )

    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  it('forwards ref to RadioGroupItem', () => {
    const ref = { current: null }
    render(
      <RadioGroup>
        <RadioGroupItem value="option1" ref={ref as React.RefObject<HTMLButtonElement>} />
      </RadioGroup>
    )

    expect(ref.current).toBeInstanceOf(HTMLButtonElement)
  })

  it('applies custom className to RadioGroup', () => {
    render(
      <RadioGroup className="custom-group" data-testid="radio-group">
        <RadioGroupItem value="option1" />
      </RadioGroup>
    )

    const group = screen.getByTestId('radio-group')
    expect(group).toHaveClass('custom-group')
    expect(group).toHaveClass('grid') // Default class
  })

  it('applies custom className to RadioGroupItem', () => {
    render(
      <RadioGroup>
        <RadioGroupItem value="option1" className="custom-item" />
      </RadioGroup>
    )

    const item = screen.getByRole('radio')
    expect(item).toHaveClass('custom-item')
  })
})
