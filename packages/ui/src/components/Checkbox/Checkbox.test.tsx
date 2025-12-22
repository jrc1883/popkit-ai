import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Checkbox } from './Checkbox'

describe('Checkbox', () => {
  it('renders checkbox', () => {
    render(<Checkbox aria-label="Accept terms" />)
    expect(screen.getByRole('checkbox')).toBeInTheDocument()
  })

  it('can be checked and unchecked', async () => {
    const user = userEvent.setup()
    render(<Checkbox aria-label="Accept terms" />)
    const checkbox = screen.getByRole('checkbox')

    expect(checkbox).toHaveAttribute('data-state', 'unchecked')

    await user.click(checkbox)
    expect(checkbox).toHaveAttribute('data-state', 'checked')

    await user.click(checkbox)
    expect(checkbox).toHaveAttribute('data-state', 'unchecked')
  })

  it('can be disabled', () => {
    render(<Checkbox disabled aria-label="Disabled checkbox" />)
    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).toBeDisabled()
  })

  it('handles checked prop', () => {
    const { rerender } = render(<Checkbox checked={false} aria-label="Controlled" />)
    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).toHaveAttribute('data-state', 'unchecked')

    rerender(<Checkbox checked={true} aria-label="Controlled" />)
    expect(checkbox).toHaveAttribute('data-state', 'checked')
  })

  it('forwards ref correctly', () => {
    const ref = { current: null }
    render(<Checkbox ref={ref as React.RefObject<HTMLButtonElement>} />)
    expect(ref.current).toBeInstanceOf(HTMLButtonElement)
  })

  it('applies custom className', () => {
    render(<Checkbox className="custom-checkbox" aria-label="Custom" />)
    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).toHaveClass('custom-checkbox')
  })

  it('handles onCheckedChange callback', async () => {
    const user = userEvent.setup()
    let checked = false
    const handleChange = (value: boolean) => {
      checked = value
    }

    render(<Checkbox onCheckedChange={handleChange} aria-label="Test" />)
    const checkbox = screen.getByRole('checkbox')

    await user.click(checkbox)
    expect(checked).toBe(true)
  })

  it('passes through additional props', () => {
    render(<Checkbox data-testid="test-checkbox" value="terms" />)
    const checkbox = screen.getByTestId('test-checkbox')
    expect(checkbox).toHaveAttribute('value', 'terms')
  })
})
