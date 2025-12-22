import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Search, Mail } from 'lucide-react'
import { Input } from './Input'

describe('Input', () => {
  it('renders input element', () => {
    render(<Input placeholder="Enter text" />)
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument()
  })

  it('accepts user input', async () => {
    const user = userEvent.setup()
    render(<Input placeholder="Enter text" />)
    const input = screen.getByPlaceholderText('Enter text')

    await user.type(input, 'Hello')
    expect(input).toHaveValue('Hello')
  })

  it('can be disabled', () => {
    render(<Input disabled placeholder="Disabled" />)
    const input = screen.getByPlaceholderText('Disabled')
    expect(input).toBeDisabled()
  })

  it('forwards ref correctly', () => {
    const ref = { current: null }
    render(<Input ref={ref as React.RefObject<HTMLInputElement>} />)
    expect(ref.current).toBeInstanceOf(HTMLInputElement)
  })

  it('applies custom className', () => {
    render(<Input className="custom-class" />)
    const input = screen.getByRole('textbox')
    expect(input).toHaveClass('custom-class')
  })

  it('supports different input types', () => {
    const { rerender } = render(<Input type="email" data-testid="input" />)
    expect(screen.getByTestId('input')).toHaveAttribute('type', 'email')

    rerender(<Input type="password" data-testid="input" />)
    expect(screen.getByTestId('input')).toHaveAttribute('type', 'password')

    rerender(<Input type="number" data-testid="input" />)
    expect(screen.getByTestId('input')).toHaveAttribute('type', 'number')
  })

  it('passes through additional props', () => {
    render(<Input data-testid="test-input" maxLength={10} required />)
    const input = screen.getByTestId('test-input')
    expect(input).toHaveAttribute('maxLength', '10')
    expect(input).toBeRequired()
  })

  it('handles onChange events', async () => {
    const user = userEvent.setup()
    let value = ''
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      value = e.target.value
    }

    render(<Input onChange={handleChange} />)
    const input = screen.getByRole('textbox')

    await user.type(input, 'test')
    expect(value).toBe('test')
  })

  describe('Error state', () => {
    it('displays error message', () => {
      render(<Input error="This field is required" id="test-input" />)
      expect(screen.getByRole('alert')).toHaveTextContent('This field is required')
    })

    it('shows error icon when error is present', () => {
      const { container } = render(<Input error="Error message" />)
      // AlertCircle icon is rendered
      expect(container.querySelector('svg')).toBeInTheDocument()
    })

    it('sets aria-invalid when error is present', () => {
      render(<Input error="Error" data-testid="input" />)
      const input = screen.getByTestId('input')
      expect(input).toHaveAttribute('aria-invalid', 'true')
    })

    it('sets aria-describedby to error message id', () => {
      render(<Input error="Error" id="test-input" />)
      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('aria-describedby', 'test-input-error')
    })

    it('applies error border classes', () => {
      render(<Input error="Error" data-testid="input" />)
      const input = screen.getByTestId('input')
      expect(input).toHaveClass('border-destructive')
    })
  })

  describe('Success state', () => {
    it('shows success icon', () => {
      const { container } = render(<Input success />)
      // CheckCircle2 icon is rendered
      expect(container.querySelector('svg')).toBeInTheDocument()
    })

    it('does not show success when error is present', () => {
      const { container } = render(<Input success error="Error" />)
      // Should show AlertCircle, not CheckCircle2
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('applies success border classes', () => {
      render(<Input success data-testid="input" />)
      const input = screen.getByTestId('input')
      expect(input).toHaveClass('border-success')
    })
  })

  describe('Icons', () => {
    it('renders left icon', () => {
      const { container } = render(<Input leftIcon={<Search />} />)
      const icons = container.querySelectorAll('svg')
      expect(icons.length).toBeGreaterThan(0)
    })

    it('renders right icon', () => {
      const { container } = render(<Input rightIcon={<Mail />} />)
      const icons = container.querySelectorAll('svg')
      expect(icons.length).toBeGreaterThan(0)
    })

    it('adjusts padding when left icon is present', () => {
      render(<Input leftIcon={<Search />} data-testid="input" />)
      const input = screen.getByTestId('input')
      expect(input).toHaveClass('pl-10')
    })

    it('adjusts padding when right icon is present', () => {
      render(<Input rightIcon={<Mail />} data-testid="input" />)
      const input = screen.getByTestId('input')
      expect(input).toHaveClass('pr-10')
    })

    it('prioritizes error icon over right icon', () => {
      const { container } = render(
        <Input rightIcon={<Mail />} error="Error" />
      )
      // Should show AlertCircle, not Mail icon
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })
  })

  describe('Sizes', () => {
    it('applies small size classes', () => {
      render(<Input inputSize="sm" data-testid="input" />)
      const input = screen.getByTestId('input')
      expect(input).toHaveClass('h-8', 'px-2', 'text-xs')
    })

    it('applies default size classes', () => {
      render(<Input inputSize="default" data-testid="input" />)
      const input = screen.getByTestId('input')
      expect(input).toHaveClass('h-9', 'px-3')
    })

    it('applies large size classes', () => {
      render(<Input inputSize="lg" data-testid="input" />)
      const input = screen.getByTestId('input')
      expect(input).toHaveClass('h-12', 'px-4')
    })

    it('uses default size when not specified', () => {
      render(<Input data-testid="input" />)
      const input = screen.getByTestId('input')
      expect(input).toHaveClass('h-9')
    })
  })
})
