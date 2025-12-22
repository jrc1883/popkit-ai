import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from './Accordion'

describe('Accordion', () => {
  it('renders accordion with items', () => {
    render(
      <Accordion type="single" collapsible>
        <AccordionItem value="item-1">
          <AccordionTrigger>Item 1</AccordionTrigger>
          <AccordionContent>Content 1</AccordionContent>
        </AccordionItem>
      </Accordion>
    )

    expect(screen.getByText('Item 1')).toBeInTheDocument()
  })

  it('expands item when trigger is clicked', async () => {
    const user = userEvent.setup()
    render(
      <Accordion type="single" collapsible>
        <AccordionItem value="item-1">
          <AccordionTrigger>Item 1</AccordionTrigger>
          <AccordionContent>Content 1</AccordionContent>
        </AccordionItem>
      </Accordion>
    )

    const trigger = screen.getByText('Item 1')
    await user.click(trigger)

    expect(screen.getByText('Content 1')).toBeInTheDocument()
  })

  it('applies custom className to Accordion', () => {
    const { container } = render(
      <Accordion type="single" className="custom-accordion">
        <AccordionItem value="item-1">
          <AccordionTrigger>Item 1</AccordionTrigger>
          <AccordionContent>Content 1</AccordionContent>
        </AccordionItem>
      </Accordion>
    )
    const accordion = container.firstChild
    expect(accordion).toHaveClass('custom-accordion')
  })

  it('forwards ref to Accordion', () => {
    const ref = { current: null }
    render(
      <Accordion
        ref={ref as React.RefObject<HTMLDivElement>}
        type="single"
      >
        <AccordionItem value="item-1">
          <AccordionTrigger>Item 1</AccordionTrigger>
          <AccordionContent>Content 1</AccordionContent>
        </AccordionItem>
      </Accordion>
    )
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  describe('data-slot attributes', () => {
    it('Accordion has data-slot attribute', () => {
      const { container } = render(
        <Accordion type="single">
          <AccordionItem value="item-1">
            <AccordionTrigger>Item 1</AccordionTrigger>
            <AccordionContent>Content 1</AccordionContent>
          </AccordionItem>
        </Accordion>
      )
      const accordion = container.firstChild
      expect(accordion).toHaveAttribute('data-slot', 'accordion')
    })

    it('AccordionItem has data-slot attribute', () => {
      render(
        <Accordion type="single">
          <AccordionItem value="item-1" data-testid="item">
            <AccordionTrigger>Item 1</AccordionTrigger>
            <AccordionContent>Content 1</AccordionContent>
          </AccordionItem>
        </Accordion>
      )
      expect(screen.getByTestId('item')).toHaveAttribute(
        'data-slot',
        'accordion-item'
      )
    })

    it('AccordionTrigger has data-slot attribute', () => {
      render(
        <Accordion type="single">
          <AccordionItem value="item-1">
            <AccordionTrigger data-testid="trigger">Item 1</AccordionTrigger>
            <AccordionContent>Content 1</AccordionContent>
          </AccordionItem>
        </Accordion>
      )
      expect(screen.getByTestId('trigger')).toHaveAttribute(
        'data-slot',
        'accordion-trigger'
      )
    })

    it('AccordionContent has data-slot attribute', async () => {
      const user = userEvent.setup()
      render(
        <Accordion type="single" collapsible>
          <AccordionItem value="item-1">
            <AccordionTrigger>Item 1</AccordionTrigger>
            <AccordionContent data-testid="content">
              Content 1
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      )
      await user.click(screen.getByText('Item 1'))
      expect(screen.getByTestId('content')).toHaveAttribute(
        'data-slot',
        'accordion-content'
      )
    })
  })

  describe('layout and styling', () => {
    it('AccordionItem has border styling', () => {
      render(
        <Accordion type="single">
          <AccordionItem value="item-1" data-testid="item">
            <AccordionTrigger>Item 1</AccordionTrigger>
            <AccordionContent>Content 1</AccordionContent>
          </AccordionItem>
        </Accordion>
      )
      expect(screen.getByTestId('item')).toHaveClass('border-b', 'border-border')
    })

    it('AccordionTrigger has proper layout classes', () => {
      render(
        <Accordion type="single">
          <AccordionItem value="item-1">
            <AccordionTrigger data-testid="trigger">Item 1</AccordionTrigger>
            <AccordionContent>Content 1</AccordionContent>
          </AccordionItem>
        </Accordion>
      )
      const trigger = screen.getByTestId('trigger')
      expect(trigger).toHaveClass(
        'flex',
        'flex-1',
        'items-center',
        'justify-between',
        'py-4'
      )
    })

    it('AccordionContent has animation classes', async () => {
      const user = userEvent.setup()
      render(
        <Accordion type="single" collapsible>
          <AccordionItem value="item-1">
            <AccordionTrigger>Item 1</AccordionTrigger>
            <AccordionContent data-testid="content">
              Content 1
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      )
      await user.click(screen.getByText('Item 1'))
      expect(screen.getByTestId('content')).toHaveClass(
        'data-[state=open]:animate-accordion-down'
      )
    })
  })

  describe('multiple items', () => {
    it('renders multiple accordion items', () => {
      render(
        <Accordion type="single" collapsible>
          <AccordionItem value="item-1">
            <AccordionTrigger>Item 1</AccordionTrigger>
            <AccordionContent>Content 1</AccordionContent>
          </AccordionItem>
          <AccordionItem value="item-2">
            <AccordionTrigger>Item 2</AccordionTrigger>
            <AccordionContent>Content 2</AccordionContent>
          </AccordionItem>
        </Accordion>
      )

      expect(screen.getByText('Item 1')).toBeInTheDocument()
      expect(screen.getByText('Item 2')).toBeInTheDocument()
    })

    it('allows only one item open at a time with type="single"', async () => {
      const user = userEvent.setup()
      render(
        <Accordion type="single" collapsible>
          <AccordionItem value="item-1">
            <AccordionTrigger>Item 1</AccordionTrigger>
            <AccordionContent>Content 1</AccordionContent>
          </AccordionItem>
          <AccordionItem value="item-2">
            <AccordionTrigger>Item 2</AccordionTrigger>
            <AccordionContent>Content 2</AccordionContent>
          </AccordionItem>
        </Accordion>
      )

      await user.click(screen.getByText('Item 1'))
      expect(screen.getByText('Content 1')).toBeInTheDocument()

      await user.click(screen.getByText('Item 2'))
      expect(screen.getByText('Content 2')).toBeInTheDocument()
    })
  })
})
