import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Progress } from './Progress'

describe('Progress', () => {
  it('renders progress bar', () => {
    render(<Progress value={50} data-testid="progress" />)

    expect(screen.getByTestId('progress')).toBeInTheDocument()
  })

  it('applies custom className to Progress', () => {
    render(<Progress value={50} className="custom-progress" data-testid="progress" />)

    expect(screen.getByTestId('progress')).toHaveClass('custom-progress')
  })

  it('forwards ref to Progress', () => {
    const ref = { current: null }
    render(
      <Progress
        value={50}
        ref={ref as React.RefObject<HTMLDivElement>}
        data-testid="progress"
      />
    )
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  describe('data-slot attributes', () => {
    it('Progress has data-slot attribute', () => {
      render(<Progress value={50} data-testid="progress" />)
      expect(screen.getByTestId('progress')).toHaveAttribute(
        'data-slot',
        'progress'
      )
    })

    it('ProgressIndicator has data-slot attribute', () => {
      const { container } = render(<Progress value={50} />)
      const indicator = container.querySelector('[data-slot="progress-indicator"]')
      expect(indicator).toBeInTheDocument()
    })
  })

  describe('layout and styling', () => {
    it('Progress has proper styling', () => {
      render(<Progress value={50} data-testid="progress" />)
      expect(screen.getByTestId('progress')).toHaveClass(
        'relative',
        'h-4',
        'w-full',
        'overflow-hidden',
        'rounded-full',
        'bg-secondary'
      )
    })

    it('ProgressIndicator has proper styling', () => {
      const { container } = render(<Progress value={50} />)
      const indicator = container.querySelector('[data-slot="progress-indicator"]')
      expect(indicator).toHaveClass(
        'h-full',
        'w-full',
        'flex-1',
        'bg-primary',
        'transition-all'
      )
    })
  })

  describe('value prop', () => {
    it('sets progress to 0%', () => {
      const { container } = render(<Progress value={0} />)
      const indicator = container.querySelector('[data-slot="progress-indicator"]')
      expect(indicator).toHaveStyle({ transform: 'translateX(-100%)' })
    })

    it('sets progress to 50%', () => {
      const { container } = render(<Progress value={50} />)
      const indicator = container.querySelector('[data-slot="progress-indicator"]')
      expect(indicator).toHaveStyle({ transform: 'translateX(-50%)' })
    })

    it('sets progress to 100%', () => {
      const { container } = render(<Progress value={100} />)
      const indicator = container.querySelector('[data-slot="progress-indicator"]')
      expect(indicator).toHaveStyle({ transform: 'translateX(-0%)' })
    })

    it('handles undefined value as 0', () => {
      const { container } = render(<Progress />)
      const indicator = container.querySelector('[data-slot="progress-indicator"]')
      expect(indicator).toHaveStyle({ transform: 'translateX(-100%)' })
    })
  })

  describe('accessibility', () => {
    it('has progressbar role', () => {
      render(<Progress value={50} data-testid="progress" />)
      expect(screen.getByTestId('progress')).toHaveAttribute('role', 'progressbar')
    })

    it('sets aria-valuemax to 100 by default', () => {
      render(<Progress value={50} data-testid="progress" />)
      expect(screen.getByTestId('progress')).toHaveAttribute('aria-valuemax', '100')
    })

    it('sets aria-valuemin to 0 by default', () => {
      render(<Progress value={50} data-testid="progress" />)
      expect(screen.getByTestId('progress')).toHaveAttribute('aria-valuemin', '0')
    })

    it('accepts value prop', () => {
      render(<Progress value={75} data-testid="progress" />)
      // Progress component should render with value prop
      expect(screen.getByTestId('progress')).toBeInTheDocument()
    })
  })
})
