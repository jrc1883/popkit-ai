import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Label } from './Label'

describe('Label', () => {
  it('renders label text', () => {
    render(<Label>Username</Label>)
    expect(screen.getByText('Username')).toBeInTheDocument()
  })

  it('associates with input via htmlFor', () => {
    render(
      <div>
        <Label htmlFor="username">Username</Label>
        <input id="username" />
      </div>
    )
    const label = screen.getByText('Username')
    expect(label).toHaveAttribute('for', 'username')
  })

  it('forwards ref correctly', () => {
    const ref = { current: null }
    render(
      <Label ref={ref as React.RefObject<HTMLLabelElement>}>Label</Label>
    )
    expect(ref.current).toBeInstanceOf(HTMLLabelElement)
  })

  it('applies custom className', () => {
    render(<Label className="custom-class">Label</Label>)
    const label = screen.getByText('Label')
    expect(label).toHaveClass('custom-class')
  })

  it('passes through additional props', () => {
    render(<Label data-testid="test-label">Label</Label>)
    expect(screen.getByTestId('test-label')).toBeInTheDocument()
  })

  it('applies peer-disabled styles', () => {
    render(<Label>Label</Label>)
    const label = screen.getByText('Label')
    expect(label).toHaveClass('peer-disabled:cursor-not-allowed')
    expect(label).toHaveClass('peer-disabled:opacity-50')
  })

  it('has data-slot attribute', () => {
    render(<Label data-testid="label">Label</Label>)
    expect(screen.getByTestId('label')).toHaveAttribute('data-slot', 'label')
  })

  describe('layout and styling', () => {
    it('uses flex layout with gap', () => {
      render(<Label data-testid="label">Label</Label>)
      const label = screen.getByTestId('label')
      expect(label).toHaveClass('flex', 'items-center', 'gap-2')
    })

    it('prevents text selection', () => {
      render(<Label data-testid="label">Label</Label>)
      const label = screen.getByTestId('label')
      expect(label).toHaveClass('select-none')
    })

    it('applies group disabled state classes', () => {
      render(<Label data-testid="label">Label</Label>)
      const label = screen.getByTestId('label')
      expect(label).toHaveClass('group-data-[disabled=true]:pointer-events-none')
      expect(label).toHaveClass('group-data-[disabled=true]:opacity-50')
    })
  })
})
