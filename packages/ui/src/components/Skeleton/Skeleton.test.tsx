import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Skeleton } from './Skeleton'

describe('Skeleton', () => {
  it('renders skeleton', () => {
    render(<Skeleton data-testid="skeleton" />)

    expect(screen.getByTestId('skeleton')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<Skeleton className="custom-skeleton" data-testid="skeleton" />)

    expect(screen.getByTestId('skeleton')).toHaveClass('custom-skeleton')
  })

  it('forwards ref', () => {
    const ref = { current: null }
    render(<Skeleton ref={ref as React.RefObject<HTMLDivElement>} data-testid="skeleton" />)

    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  describe('data-slot attributes', () => {
    it('has data-slot attribute', () => {
      render(<Skeleton data-testid="skeleton" />)

      expect(screen.getByTestId('skeleton')).toHaveAttribute('data-slot', 'skeleton')
    })
  })

  describe('layout and styling', () => {
    it('has proper styling', () => {
      render(<Skeleton data-testid="skeleton" />)

      expect(screen.getByTestId('skeleton')).toHaveClass(
        'animate-pulse',
        'rounded-md',
        'bg-muted'
      )
    })

    it('can override default styles', () => {
      render(<Skeleton className="h-10 w-10 rounded-full" data-testid="skeleton" />)

      expect(screen.getByTestId('skeleton')).toHaveClass('h-10', 'w-10', 'rounded-full')
    })
  })

  describe('props passing', () => {
    it('accepts custom HTML attributes', () => {
      render(<Skeleton aria-label="Loading content" data-testid="skeleton" />)

      expect(screen.getByTestId('skeleton')).toHaveAttribute('aria-label', 'Loading content')
    })

    it('accepts custom data attributes', () => {
      render(<Skeleton data-custom="value" data-testid="skeleton" />)

      expect(screen.getByTestId('skeleton')).toHaveAttribute('data-custom', 'value')
    })
  })

  describe('usage patterns', () => {
    it('works as avatar skeleton', () => {
      render(<Skeleton className="h-12 w-12 rounded-full" data-testid="skeleton" />)

      const skeleton = screen.getByTestId('skeleton')
      expect(skeleton).toHaveClass('h-12', 'w-12', 'rounded-full')
    })

    it('works as text skeleton', () => {
      render(<Skeleton className="h-4 w-[250px]" data-testid="skeleton" />)

      const skeleton = screen.getByTestId('skeleton')
      expect(skeleton).toHaveClass('h-4', 'w-[250px]')
    })

    it('works as card skeleton', () => {
      render(<Skeleton className="h-32 w-full" data-testid="skeleton" />)

      const skeleton = screen.getByTestId('skeleton')
      expect(skeleton).toHaveClass('h-32', 'w-full')
    })
  })
})
