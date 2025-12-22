import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  Toast,
  ToastProvider,
  ToastViewport,
  ToastTitle,
  ToastDescription,
  ToastClose,
  ToastAction,
} from './Toast'

describe('Toast', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders toast with title and description', () => {
    render(
      <ToastProvider>
        <Toast open>
          <ToastTitle>Toast Title</ToastTitle>
          <ToastDescription>Toast description text</ToastDescription>
        </Toast>
        <ToastViewport />
      </ToastProvider>
    )

    expect(screen.getByText('Toast Title')).toBeInTheDocument()
    expect(screen.getByText('Toast description text')).toBeInTheDocument()
  })

  it('renders ToastViewport', () => {
    const { container } = render(
      <ToastProvider>
        <ToastViewport data-testid="viewport" />
      </ToastProvider>
    )

    expect(screen.getByTestId('viewport')).toBeInTheDocument()
  })

  it('applies custom className to Toast', () => {
    render(
      <ToastProvider>
        <Toast open className="custom-toast" data-testid="toast">
          <ToastTitle>Title</ToastTitle>
        </Toast>
        <ToastViewport />
      </ToastProvider>
    )

    expect(screen.getByTestId('toast')).toHaveClass('custom-toast')
  })

  it('forwards ref to Toast', () => {
    const ref = { current: null }
    render(
      <ToastProvider>
        <Toast
          open
          ref={ref as React.RefObject<HTMLLIElement>}
          data-testid="toast"
        >
          <ToastTitle>Title</ToastTitle>
        </Toast>
        <ToastViewport />
      </ToastProvider>
    )
    expect(ref.current).toBeInstanceOf(HTMLLIElement)
  })

  describe('variants', () => {
    it('renders default variant', () => {
      render(
        <ToastProvider>
          <Toast open data-testid="toast">
            <ToastTitle>Title</ToastTitle>
          </Toast>
          <ToastViewport />
        </ToastProvider>
      )

      const toast = screen.getByTestId('toast')
      expect(toast).toHaveClass('border', 'bg-background', 'text-foreground')
    })

    it('renders destructive variant', () => {
      render(
        <ToastProvider>
          <Toast open variant="destructive" data-testid="toast">
            <ToastTitle>Title</ToastTitle>
          </Toast>
          <ToastViewport />
        </ToastProvider>
      )

      const toast = screen.getByTestId('toast')
      expect(toast).toHaveClass('destructive', 'border-destructive')
    })
  })

  describe('data-slot attributes', () => {
    it('Toast has data-slot attribute', () => {
      render(
        <ToastProvider>
          <Toast open data-testid="toast">
            <ToastTitle>Title</ToastTitle>
          </Toast>
          <ToastViewport />
        </ToastProvider>
      )
      expect(screen.getByTestId('toast')).toHaveAttribute('data-slot', 'toast')
    })

    it('ToastViewport has data-slot attribute', () => {
      render(
        <ToastProvider>
          <ToastViewport data-testid="viewport" />
        </ToastProvider>
      )
      expect(screen.getByTestId('viewport')).toHaveAttribute(
        'data-slot',
        'toast-viewport'
      )
    })

    it('ToastTitle has data-slot attribute', () => {
      render(
        <ToastProvider>
          <Toast open>
            <ToastTitle data-testid="title">Title</ToastTitle>
          </Toast>
          <ToastViewport />
        </ToastProvider>
      )
      expect(screen.getByTestId('title')).toHaveAttribute(
        'data-slot',
        'toast-title'
      )
    })

    it('ToastDescription has data-slot attribute', () => {
      render(
        <ToastProvider>
          <Toast open>
            <ToastDescription data-testid="description">
              Description
            </ToastDescription>
          </Toast>
          <ToastViewport />
        </ToastProvider>
      )
      expect(screen.getByTestId('description')).toHaveAttribute(
        'data-slot',
        'toast-description'
      )
    })

    it('ToastClose has data-slot attribute', () => {
      render(
        <ToastProvider>
          <Toast open>
            <ToastTitle>Title</ToastTitle>
            <ToastClose data-testid="close" />
          </Toast>
          <ToastViewport />
        </ToastProvider>
      )
      expect(screen.getByTestId('close')).toHaveAttribute(
        'data-slot',
        'toast-close'
      )
    })

    it('ToastAction has data-slot attribute', () => {
      render(
        <ToastProvider>
          <Toast open>
            <ToastTitle>Title</ToastTitle>
            <ToastAction altText="Action" data-testid="action">
              Action
            </ToastAction>
          </Toast>
          <ToastViewport />
        </ToastProvider>
      )
      expect(screen.getByTestId('action')).toHaveAttribute(
        'data-slot',
        'toast-action'
      )
    })
  })

  describe('layout and styling', () => {
    it('Toast has proper styling', () => {
      render(
        <ToastProvider>
          <Toast open data-testid="toast">
            <ToastTitle>Title</ToastTitle>
          </Toast>
          <ToastViewport />
        </ToastProvider>
      )
      const toast = screen.getByTestId('toast')
      expect(toast).toHaveClass(
        'pointer-events-auto',
        'relative',
        'flex',
        'w-full',
        'rounded-md',
        'border',
        'p-6'
      )
    })

    it('ToastViewport has proper layout', () => {
      render(
        <ToastProvider>
          <ToastViewport data-testid="viewport" />
        </ToastProvider>
      )
      expect(screen.getByTestId('viewport')).toHaveClass(
        'fixed',
        'top-0',
        'z-[100]',
        'flex',
        'max-h-screen',
        'w-full'
      )
    })

    it('ToastTitle has proper styling', () => {
      render(
        <ToastProvider>
          <Toast open>
            <ToastTitle data-testid="title">Title</ToastTitle>
          </Toast>
          <ToastViewport />
        </ToastProvider>
      )
      expect(screen.getByTestId('title')).toHaveClass(
        'text-sm',
        'font-semibold'
      )
    })

    it('ToastDescription has proper styling', () => {
      render(
        <ToastProvider>
          <Toast open>
            <ToastDescription data-testid="description">
              Description
            </ToastDescription>
          </Toast>
          <ToastViewport />
        </ToastProvider>
      )
      expect(screen.getByTestId('description')).toHaveClass(
        'text-sm',
        'opacity-90'
      )
    })
  })

  describe('interactions', () => {
    it('renders close button with X icon', () => {
      render(
        <ToastProvider>
          <Toast open>
            <ToastTitle>Title</ToastTitle>
            <ToastClose />
          </Toast>
          <ToastViewport />
        </ToastProvider>
      )
      const closeButton = screen.getByRole('button')
      expect(closeButton).toBeInTheDocument()
      expect(closeButton.querySelector('svg')).toBeInTheDocument()
    })

    it('renders action button', () => {
      render(
        <ToastProvider>
          <Toast open>
            <ToastTitle>Title</ToastTitle>
            <ToastAction altText="Undo">Undo</ToastAction>
          </Toast>
          <ToastViewport />
        </ToastProvider>
      )
      expect(screen.getByText('Undo')).toBeInTheDocument()
    })
  })
})
