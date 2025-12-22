import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
} from './Table'

describe('Table', () => {
  it('renders a complete table structure', () => {
    render(
      <Table>
        <TableCaption>Test Table</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>Header 1</TableHead>
            <TableHead>Header 2</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Cell 1</TableCell>
            <TableCell>Cell 2</TableCell>
          </TableRow>
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell>Footer 1</TableCell>
            <TableCell>Footer 2</TableCell>
          </TableRow>
        </TableFooter>
      </Table>
    )

    expect(screen.getByText('Test Table')).toBeInTheDocument()
    expect(screen.getByText('Header 1')).toBeInTheDocument()
    expect(screen.getByText('Cell 1')).toBeInTheDocument()
    expect(screen.getByText('Footer 1')).toBeInTheDocument()
  })

  it('applies custom className to Table', () => {
    const { container } = render(
      <Table className="custom-table">
        <TableBody>
          <TableRow>
            <TableCell>Cell</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    )
    const table = container.querySelector('table')
    expect(table).toHaveClass('custom-table')
  })

  it('forwards ref to Table', () => {
    const ref = { current: null }
    render(
      <Table ref={ref as React.RefObject<HTMLTableElement>}>
        <TableBody>
          <TableRow>
            <TableCell>Cell</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    )
    expect(ref.current).toBeInstanceOf(HTMLTableElement)
  })

  describe('data-slot attributes', () => {
    it('Table container has data-slot attribute', () => {
      const { container } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )
      const wrapper = container.firstChild
      expect(wrapper).toHaveAttribute('data-slot', 'table-container')
    })

    it('Table has data-slot attribute', () => {
      const { container } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )
      const table = container.querySelector('table')
      expect(table).toHaveAttribute('data-slot', 'table')
    })

    it('TableHeader has data-slot attribute', () => {
      render(
        <Table>
          <TableHeader data-testid="header">
            <TableRow>
              <TableHead>Head</TableHead>
            </TableRow>
          </TableHeader>
        </Table>
      )
      expect(screen.getByTestId('header')).toHaveAttribute(
        'data-slot',
        'table-header'
      )
    })

    it('TableBody has data-slot attribute', () => {
      render(
        <Table>
          <TableBody data-testid="body">
            <TableRow>
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )
      expect(screen.getByTestId('body')).toHaveAttribute(
        'data-slot',
        'table-body'
      )
    })

    it('TableFooter has data-slot attribute', () => {
      render(
        <Table>
          <TableFooter data-testid="footer">
            <TableRow>
              <TableCell>Footer</TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      )
      expect(screen.getByTestId('footer')).toHaveAttribute(
        'data-slot',
        'table-footer'
      )
    })

    it('TableRow has data-slot attribute', () => {
      render(
        <Table>
          <TableBody>
            <TableRow data-testid="row">
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )
      expect(screen.getByTestId('row')).toHaveAttribute(
        'data-slot',
        'table-row'
      )
    })

    it('TableHead has data-slot attribute', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead data-testid="head">Head</TableHead>
            </TableRow>
          </TableHeader>
        </Table>
      )
      expect(screen.getByTestId('head')).toHaveAttribute(
        'data-slot',
        'table-head'
      )
    })

    it('TableCell has data-slot attribute', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell data-testid="cell">Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )
      expect(screen.getByTestId('cell')).toHaveAttribute(
        'data-slot',
        'table-cell'
      )
    })

    it('TableCaption has data-slot attribute', () => {
      render(
        <Table>
          <TableCaption data-testid="caption">Caption</TableCaption>
        </Table>
      )
      expect(screen.getByTestId('caption')).toHaveAttribute(
        'data-slot',
        'table-caption'
      )
    })
  })

  describe('layout and styling', () => {
    it('TableHead uses tight spacing', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead data-testid="head">Head</TableHead>
            </TableRow>
          </TableHeader>
        </Table>
      )
      const head = screen.getByTestId('head')
      expect(head).toHaveClass('h-10', 'px-2')
    })

    it('TableCell uses tight spacing', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell data-testid="cell">Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )
      const cell = screen.getByTestId('cell')
      expect(cell).toHaveClass('p-2')
    })

    it('TableHead uses whitespace-nowrap', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead data-testid="head">Head</TableHead>
            </TableRow>
          </TableHeader>
        </Table>
      )
      expect(screen.getByTestId('head')).toHaveClass('whitespace-nowrap')
    })

    it('TableCell uses whitespace-nowrap', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell data-testid="cell">Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )
      expect(screen.getByTestId('cell')).toHaveClass('whitespace-nowrap')
    })

    it('Table container uses overflow-x-auto', () => {
      const { container } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )
      const wrapper = container.firstChild
      expect(wrapper).toHaveClass('overflow-x-auto')
    })
  })
})
