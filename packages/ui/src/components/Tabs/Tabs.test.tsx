import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Tabs, TabsList, TabsTrigger, TabsContent } from './Tabs'

describe('Tabs', () => {
  it('renders tabs with triggers and content', () => {
    render(
      <Tabs defaultValue="tab1">
        <TabsList>
          <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          <TabsTrigger value="tab2">Tab 2</TabsTrigger>
        </TabsList>
        <TabsContent value="tab1">Content 1</TabsContent>
        <TabsContent value="tab2">Content 2</TabsContent>
      </Tabs>
    )

    expect(screen.getByText('Tab 1')).toBeInTheDocument()
    expect(screen.getByText('Tab 2')).toBeInTheDocument()
    expect(screen.getByText('Content 1')).toBeInTheDocument()
  })

  it('switches between tabs when clicked', async () => {
    const user = userEvent.setup()
    render(
      <Tabs defaultValue="tab1">
        <TabsList>
          <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          <TabsTrigger value="tab2">Tab 2</TabsTrigger>
        </TabsList>
        <TabsContent value="tab1">Content 1</TabsContent>
        <TabsContent value="tab2">Content 2</TabsContent>
      </Tabs>
    )

    // Tab 1 content should be visible by default
    expect(screen.getByText('Content 1')).toBeInTheDocument()

    // Click Tab 2
    await user.click(screen.getByText('Tab 2'))

    // Tab 2 content should be visible after clicking
    expect(screen.getByText('Content 2')).toBeInTheDocument()
  })

  it('applies custom className to Tabs', () => {
    const { container } = render(
      <Tabs defaultValue="tab1" className="custom-tabs">
        <TabsList>
          <TabsTrigger value="tab1">Tab 1</TabsTrigger>
        </TabsList>
        <TabsContent value="tab1">Content 1</TabsContent>
      </Tabs>
    )
    const tabs = container.firstChild
    expect(tabs).toHaveClass('custom-tabs')
  })

  it('forwards ref to Tabs', () => {
    const ref = { current: null }
    render(
      <Tabs
        ref={ref as React.RefObject<HTMLDivElement>}
        defaultValue="tab1"
      >
        <TabsList>
          <TabsTrigger value="tab1">Tab 1</TabsTrigger>
        </TabsList>
        <TabsContent value="tab1">Content 1</TabsContent>
      </Tabs>
    )
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  describe('data-slot attributes', () => {
    it('Tabs has data-slot attribute', () => {
      const { container } = render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
        </Tabs>
      )
      const tabs = container.firstChild
      expect(tabs).toHaveAttribute('data-slot', 'tabs')
    })

    it('TabsList has data-slot attribute', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList data-testid="list">
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
        </Tabs>
      )
      expect(screen.getByTestId('list')).toHaveAttribute(
        'data-slot',
        'tabs-list'
      )
    })

    it('TabsTrigger has data-slot attribute', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1" data-testid="trigger">
              Tab 1
            </TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
        </Tabs>
      )
      expect(screen.getByTestId('trigger')).toHaveAttribute(
        'data-slot',
        'tabs-trigger'
      )
    })

    it('TabsContent has data-slot attribute', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1" data-testid="content">
            Content 1
          </TabsContent>
        </Tabs>
      )
      expect(screen.getByTestId('content')).toHaveAttribute(
        'data-slot',
        'tabs-content'
      )
    })
  })

  describe('layout and styling', () => {
    it('Tabs uses flex-col layout with gap', () => {
      const { container } = render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
        </Tabs>
      )
      const tabs = container.firstChild
      expect(tabs).toHaveClass('flex', 'flex-col', 'gap-2')
    })

    it('TabsList has proper sizing', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList data-testid="list">
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
        </Tabs>
      )
      const list = screen.getByTestId('list')
      expect(list).toHaveClass('h-9', 'rounded-lg', 'w-fit')
    })

    it('TabsTrigger uses flex-1 and gap', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1" data-testid="trigger">
              Tab 1
            </TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
        </Tabs>
      )
      const trigger = screen.getByTestId('trigger')
      expect(trigger).toHaveClass('flex-1', 'gap-1.5')
    })

    it('TabsContent uses flex-1', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1" data-testid="content">
            Content 1
          </TabsContent>
        </Tabs>
      )
      expect(screen.getByTestId('content')).toHaveClass('flex-1')
    })
  })
})
