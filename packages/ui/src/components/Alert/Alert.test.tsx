import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Alert, AlertTitle, AlertDescription } from './Alert'

describe('Alert', () => {
  it('renders alert with title and description', () => {
    render(
      <Alert>
        <AlertTitle>Alert Title</AlertTitle>
        <AlertDescription>Alert description text</AlertDescription>
      </Alert>
    )

    expect(screen.getByText('Alert Title')).toBeInTheDocument()
    expect(screen.getByText('Alert description text')).toBeInTheDocument()
  })

  it('has role="alert"', () => {
    render(
      <Alert>
        <AlertTitle>Title</AlertTitle>
      </Alert>
    )

    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('applies custom className to Alert', () => {
    render(
      <Alert className="custom-alert">
        <AlertTitle>Title</AlertTitle>
      </Alert>
    )

    expect(screen.getByRole('alert')).toHaveClass('custom-alert')
  })

  it('forwards ref to Alert', () => {
    const ref = { current: null }
    render(
      <Alert ref={ref as React.RefObject<HTMLDivElement>}>
        <AlertTitle>Title</AlertTitle>
      </Alert>
    )
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  describe('variants', () => {
    it('renders default variant', () => {
      render(
        <Alert>
          <AlertTitle>Title</AlertTitle>
        </Alert>
      )

      const alert = screen.getByRole('alert')
      expect(alert).toHaveClass('bg-background', 'text-foreground')
    })

    it('renders destructive variant', () => {
      render(
        <Alert variant="destructive">
          <AlertTitle>Title</AlertTitle>
        </Alert>
      )

      const alert = screen.getByRole('alert')
      expect(alert).toHaveClass(
        'border-destructive/50',
        'text-destructive',
        'dark:border-destructive'
      )
    })
  })

  describe('data-slot attributes', () => {
    it('Alert has data-slot attribute', () => {
      render(
        <Alert>
          <AlertTitle>Title</AlertTitle>
        </Alert>
      )
      expect(screen.getByRole('alert')).toHaveAttribute('data-slot', 'alert')
    })

    it('AlertTitle has data-slot attribute', () => {
      render(
        <Alert>
          <AlertTitle data-testid="title">Title</AlertTitle>
        </Alert>
      )
      expect(screen.getByTestId('title')).toHaveAttribute(
        'data-slot',
        'alert-title'
      )
    })

    it('AlertDescription has data-slot attribute', () => {
      render(
        <Alert>
          <AlertDescription data-testid="description">
            Description
          </AlertDescription>
        </Alert>
      )
      expect(screen.getByTestId('description')).toHaveAttribute(
        'data-slot',
        'alert-description'
      )
    })
  })

  describe('layout and styling', () => {
    it('Alert has proper styling', () => {
      render(
        <Alert>
          <AlertTitle>Title</AlertTitle>
        </Alert>
      )
      const alert = screen.getByRole('alert')
      expect(alert).toHaveClass(
        'relative',
        'w-full',
        'rounded-lg',
        'border',
        'p-4'
      )
    })

    it('AlertTitle has proper styling', () => {
      render(
        <Alert>
          <AlertTitle data-testid="title">Title</AlertTitle>
        </Alert>
      )
      expect(screen.getByTestId('title')).toHaveClass(
        'mb-1',
        'font-medium',
        'leading-none',
        'tracking-tight'
      )
    })

    it('AlertDescription has proper styling', () => {
      render(
        <Alert>
          <AlertDescription data-testid="description">
            Description
          </AlertDescription>
        </Alert>
      )
      expect(screen.getByTestId('description')).toHaveClass('text-sm')
    })
  })
})
