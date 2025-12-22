import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Spinner } from './Spinner'

describe('Spinner', () => {
  it('renders spinner', () => {
    render(<Spinner aria-label="Loading" />)
    expect(screen.getByLabelText('Loading')).toBeInTheDocument()
  })

  it('applies default size styles', () => {
    render(<Spinner data-testid="spinner" />)
    const spinner = screen.getByTestId('spinner')
    expect(spinner).toHaveClass('h-8', 'w-8')
  })

  it('applies small size styles', () => {
    render(<Spinner size="sm" data-testid="spinner" />)
    const spinner = screen.getByTestId('spinner')
    expect(spinner).toHaveClass('h-4', 'w-4')
  })

  it('applies large size styles', () => {
    render(<Spinner size="lg" data-testid="spinner" />)
    const spinner = screen.getByTestId('spinner')
    expect(spinner).toHaveClass('h-12', 'w-12')
  })

  it('has animation classes', () => {
    render(<Spinner data-testid="spinner" />)
    const spinner = screen.getByTestId('spinner')
    expect(spinner).toHaveClass('animate-spin')
  })

  it('applies custom className', () => {
    render(<Spinner className="custom-spinner" data-testid="spinner" />)
    const spinner = screen.getByTestId('spinner')
    expect(spinner).toHaveClass('custom-spinner')
    expect(spinner).toHaveClass('animate-spin') // Still has default classes
  })

  it('passes through additional props', () => {
    render(<Spinner data-testid="test-spinner" role="status" />)
    const spinner = screen.getByTestId('test-spinner')
    expect(spinner).toHaveAttribute('role', 'status')
  })

  it('renders as a div element', () => {
    render(<Spinner data-testid="spinner" />)
    const spinner = screen.getByTestId('spinner')
    expect(spinner.tagName).toBe('DIV')
  })
})
