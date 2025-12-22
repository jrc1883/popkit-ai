import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Badge } from './Badge'

describe('Badge', () => {
  it('renders badge text', () => {
    render(<Badge>New</Badge>)
    expect(screen.getByText('New')).toBeInTheDocument()
  })

  it('applies default variant styles', () => {
    render(<Badge>Default</Badge>)
    const badge = screen.getByText('Default')
    expect(badge).toHaveClass('bg-primary')
  })

  it('applies secondary variant styles', () => {
    render(<Badge variant="secondary">Secondary</Badge>)
    const badge = screen.getByText('Secondary')
    expect(badge).toHaveClass('bg-secondary')
  })

  it('applies destructive variant styles', () => {
    render(<Badge variant="destructive">Error</Badge>)
    const badge = screen.getByText('Error')
    expect(badge).toHaveClass('bg-destructive')
  })

  it('applies outline variant styles', () => {
    render(<Badge variant="outline">Outline</Badge>)
    const badge = screen.getByText('Outline')
    expect(badge).toHaveClass('text-foreground')
  })

  it('applies custom className', () => {
    render(<Badge className="custom-badge">Badge</Badge>)
    const badge = screen.getByText('Badge')
    expect(badge).toHaveClass('custom-badge')
    expect(badge).toHaveClass('bg-primary') // Still has default classes
  })

  it('passes through additional props', () => {
    render(<Badge data-testid="test-badge">Badge</Badge>)
    expect(screen.getByTestId('test-badge')).toBeInTheDocument()
  })

  it('renders as inline element', () => {
    render(<Badge>Badge</Badge>)
    const badge = screen.getByText('Badge')
    expect(badge).toHaveClass('inline-flex')
  })

  it('has correct base styles', () => {
    render(<Badge>Badge</Badge>)
    const badge = screen.getByText('Badge')
    expect(badge).toHaveClass('items-center', 'rounded-full', 'px-2.5', 'py-0.5')
  })
})
