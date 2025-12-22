import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardAction,
  CardContent,
  CardFooter,
} from './Card'

describe('Card', () => {
  it('renders card with all sub-components', () => {
    render(
      <Card data-testid="card">
        <CardHeader>
          <CardTitle>Title</CardTitle>
          <CardDescription>Description</CardDescription>
        </CardHeader>
        <CardContent>Content</CardContent>
        <CardFooter>Footer</CardFooter>
      </Card>
    )

    expect(screen.getByTestId('card')).toBeInTheDocument()
    expect(screen.getByText('Title')).toBeInTheDocument()
    expect(screen.getByText('Description')).toBeInTheDocument()
    expect(screen.getByText('Content')).toBeInTheDocument()
    expect(screen.getByText('Footer')).toBeInTheDocument()
  })

  it('renders card with CardAction', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Title</CardTitle>
          <CardDescription>Description</CardDescription>
          <CardAction data-testid="action">Action</CardAction>
        </CardHeader>
      </Card>
    )

    expect(screen.getByTestId('action')).toBeInTheDocument()
    expect(screen.getByText('Action')).toBeInTheDocument()
  })

  it('applies custom className to Card', () => {
    render(
      <Card className="custom-card" data-testid="card">
        Content
      </Card>
    )
    const card = screen.getByTestId('card')
    expect(card).toHaveClass('custom-card')
    expect(card).toHaveClass('rounded-xl', 'border', 'flex', 'flex-col')
  })

  it('applies custom className to CardHeader', () => {
    render(<CardHeader className="custom-header">Header</CardHeader>)
    const header = screen.getByText('Header')
    expect(header).toHaveClass('custom-header')
    expect(header).toHaveClass('grid')
  })

  it('applies custom className to CardTitle', () => {
    render(<CardTitle className="custom-title">Title</CardTitle>)
    const title = screen.getByText('Title')
    expect(title).toHaveClass('custom-title')
    expect(title).toHaveClass('text-2xl')
  })

  it('applies custom className to CardDescription', () => {
    render(
      <CardDescription className="custom-desc">Description</CardDescription>
    )
    const desc = screen.getByText('Description')
    expect(desc).toHaveClass('custom-desc')
    expect(desc).toHaveClass('text-muted-foreground')
  })

  it('applies custom className to CardAction', () => {
    render(<CardAction className="custom-action">Action</CardAction>)
    const action = screen.getByText('Action')
    expect(action).toHaveClass('custom-action')
    expect(action).toHaveClass('col-start-2', 'row-span-2')
  })

  it('applies custom className to CardContent', () => {
    render(<CardContent className="custom-content">Content</CardContent>)
    const content = screen.getByText('Content')
    expect(content).toHaveClass('custom-content')
    expect(content).toHaveClass('px-6')
  })

  it('applies custom className to CardFooter', () => {
    render(<CardFooter className="custom-footer">Footer</CardFooter>)
    const footer = screen.getByText('Footer')
    expect(footer).toHaveClass('custom-footer')
    expect(footer).toHaveClass('flex')
  })

  it('forwards ref to Card', () => {
    const ref = { current: null }
    render(
      <Card ref={ref as React.RefObject<HTMLDivElement>}>Content</Card>
    )
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  it('forwards ref to CardTitle', () => {
    const ref = { current: null }
    render(
      <CardTitle ref={ref as React.RefObject<HTMLHeadingElement>}>
        Title
      </CardTitle>
    )
    expect(ref.current).toBeInstanceOf(HTMLHeadingElement)
  })

  it('forwards ref to CardDescription', () => {
    const ref = { current: null }
    render(
      <CardDescription ref={ref as React.RefObject<HTMLParagraphElement>}>
        Desc
      </CardDescription>
    )
    expect(ref.current).toBeInstanceOf(HTMLParagraphElement)
  })

  it('forwards ref to CardAction', () => {
    const ref = { current: null }
    render(
      <CardAction ref={ref as React.RefObject<HTMLDivElement>}>
        Action
      </CardAction>
    )
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  describe('data-slot attributes', () => {
    it('Card has data-slot attribute', () => {
      render(<Card data-testid="card">Content</Card>)
      expect(screen.getByTestId('card')).toHaveAttribute(
        'data-slot',
        'card'
      )
    })

    it('CardHeader has data-slot attribute', () => {
      render(<CardHeader data-testid="header">Header</CardHeader>)
      expect(screen.getByTestId('header')).toHaveAttribute(
        'data-slot',
        'card-header'
      )
    })

    it('CardTitle has data-slot attribute', () => {
      render(<CardTitle data-testid="title">Title</CardTitle>)
      expect(screen.getByTestId('title')).toHaveAttribute(
        'data-slot',
        'card-title'
      )
    })

    it('CardDescription has data-slot attribute', () => {
      render(
        <CardDescription data-testid="desc">Description</CardDescription>
      )
      expect(screen.getByTestId('desc')).toHaveAttribute(
        'data-slot',
        'card-description'
      )
    })

    it('CardAction has data-slot attribute', () => {
      render(<CardAction data-testid="action">Action</CardAction>)
      expect(screen.getByTestId('action')).toHaveAttribute(
        'data-slot',
        'card-action'
      )
    })

    it('CardContent has data-slot attribute', () => {
      render(<CardContent data-testid="content">Content</CardContent>)
      expect(screen.getByTestId('content')).toHaveAttribute(
        'data-slot',
        'card-content'
      )
    })

    it('CardFooter has data-slot attribute', () => {
      render(<CardFooter data-testid="footer">Footer</CardFooter>)
      expect(screen.getByTestId('footer')).toHaveAttribute(
        'data-slot',
        'card-footer'
      )
    })
  })

  describe('spacing and layout', () => {
    it('Card uses flex-col gap-6 for spacing', () => {
      render(<Card data-testid="card">Content</Card>)
      const card = screen.getByTestId('card')
      expect(card).toHaveClass('flex', 'flex-col', 'gap-6')
    })

    it('CardHeader uses grid layout', () => {
      render(<CardHeader data-testid="header">Header</CardHeader>)
      const header = screen.getByTestId('header')
      expect(header).toHaveClass('grid', 'auto-rows-min')
    })
  })
})
