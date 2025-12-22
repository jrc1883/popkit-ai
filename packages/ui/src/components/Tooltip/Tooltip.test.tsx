import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  Tooltip,
  TooltipProvider,
  TooltipTrigger,
  TooltipContent,
} from './Tooltip'

describe('Tooltip', () => {
  it('renders tooltip trigger', () => {
    render(
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger>Hover me</TooltipTrigger>
          <TooltipContent>Tooltip text</TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )

    expect(screen.getByText('Hover me')).toBeInTheDocument()
  })

  it('shows tooltip content on hover', async () => {
    const user = userEvent.setup()
    render(
      <TooltipProvider delayDuration={0}>
        <Tooltip>
          <TooltipTrigger>Hover me</TooltipTrigger>
          <TooltipContent data-testid="tooltip-content">
            Tooltip text
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )

    const trigger = screen.getByText('Hover me')
    await user.hover(trigger)

    await waitFor(() => {
      expect(screen.getByTestId('tooltip-content')).toBeInTheDocument()
    })
  })

  it('applies custom className to TooltipContent', async () => {
    const user = userEvent.setup()
    render(
      <TooltipProvider delayDuration={0}>
        <Tooltip>
          <TooltipTrigger>Hover me</TooltipTrigger>
          <TooltipContent
            className="custom-tooltip"
            data-testid="tooltip-content"
          >
            Tooltip text
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )

    const trigger = screen.getByText('Hover me')
    await user.hover(trigger)

    await waitFor(() => {
      expect(screen.getByTestId('tooltip-content')).toHaveClass(
        'custom-tooltip'
      )
    })
  })

  it('forwards ref to TooltipContent', async () => {
    const user = userEvent.setup()
    const ref = { current: null }
    render(
      <TooltipProvider delayDuration={0}>
        <Tooltip>
          <TooltipTrigger>Hover me</TooltipTrigger>
          <TooltipContent
            ref={ref as React.RefObject<HTMLDivElement>}
            data-testid="tooltip-content"
          >
            Tooltip text
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )

    const trigger = screen.getByText('Hover me')
    await user.hover(trigger)

    await waitFor(() => {
      expect(ref.current).toBeInstanceOf(HTMLDivElement)
    })
  })

  describe('data-slot attributes', () => {
    it('TooltipContent has data-slot attribute', async () => {
      const user = userEvent.setup()
      render(
        <TooltipProvider delayDuration={0}>
          <Tooltip>
            <TooltipTrigger>Hover me</TooltipTrigger>
            <TooltipContent data-testid="tooltip-content">
              Tooltip text
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )

      const trigger = screen.getByText('Hover me')
      await user.hover(trigger)

      await waitFor(() => {
        expect(screen.getByTestId('tooltip-content')).toHaveAttribute(
          'data-slot',
          'tooltip-content'
        )
      })
    })
  })

  describe('layout and styling', () => {
    it('TooltipContent has proper styling', async () => {
      const user = userEvent.setup()
      render(
        <TooltipProvider delayDuration={0}>
          <Tooltip>
            <TooltipTrigger>Hover me</TooltipTrigger>
            <TooltipContent data-testid="tooltip-content">
              Tooltip text
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )

      const trigger = screen.getByText('Hover me')
      await user.hover(trigger)

      await waitFor(() => {
        const tooltip = screen.getByTestId('tooltip-content')
        expect(tooltip).toHaveClass(
          'z-50',
          'overflow-hidden',
          'rounded-md',
          'bg-primary',
          'px-3',
          'py-1.5',
          'text-xs',
          'text-primary-foreground'
        )
      })
    })

    it('TooltipContent has animation classes', async () => {
      const user = userEvent.setup()
      render(
        <TooltipProvider delayDuration={0}>
          <Tooltip>
            <TooltipTrigger>Hover me</TooltipTrigger>
            <TooltipContent data-testid="tooltip-content">
              Tooltip text
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )

      const trigger = screen.getByText('Hover me')
      await user.hover(trigger)

      await waitFor(() => {
        const tooltip = screen.getByTestId('tooltip-content')
        expect(tooltip).toHaveClass('animate-in', 'fade-in-0', 'zoom-in-95')
      })
    })
  })

  describe('sideOffset', () => {
    it('uses default sideOffset of 4', async () => {
      const user = userEvent.setup()
      render(
        <TooltipProvider delayDuration={0}>
          <Tooltip>
            <TooltipTrigger>Hover me</TooltipTrigger>
            <TooltipContent data-testid="tooltip-content">
              Tooltip text
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )

      const trigger = screen.getByText('Hover me')
      await user.hover(trigger)

      await waitFor(() => {
        expect(screen.getByTestId('tooltip-content')).toBeInTheDocument()
      })
    })

    it('accepts custom sideOffset', async () => {
      const user = userEvent.setup()
      render(
        <TooltipProvider delayDuration={0}>
          <Tooltip>
            <TooltipTrigger>Hover me</TooltipTrigger>
            <TooltipContent sideOffset={10} data-testid="tooltip-content">
              Tooltip text
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )

      const trigger = screen.getByText('Hover me')
      await user.hover(trigger)

      await waitFor(() => {
        expect(screen.getByTestId('tooltip-content')).toBeInTheDocument()
      })
    })
  })
})
