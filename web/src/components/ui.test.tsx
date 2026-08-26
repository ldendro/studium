import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Button, EmptyState, Progress } from './ui'

describe('Button', () => {
  it('disables the control while a request is in flight', () => {
    render(
      <Button loading variant="primary">
        Save
      </Button>,
    )
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()
  })
})

describe('EmptyState', () => {
  it('explains the empty surface and optional next action', () => {
    render(
      <EmptyState
        title="Nothing here yet"
        description="Open a vault to start searching."
        action={<button type="button">Open vault</button>}
      />,
    )
    expect(screen.getByRole('heading', { name: 'Nothing here yet' })).toBeVisible()
    expect(screen.getByText('Open a vault to start searching.')).toBeVisible()
    expect(screen.getByRole('button', { name: 'Open vault' })).toBeVisible()
  })
})

describe('Progress', () => {
  it('exposes a named progressbar with a rounded percentage', () => {
    render(<Progress value={0.42} label="Embedding sources" />)
    const bar = screen.getByRole('progressbar', { name: 'Embedding sources' })
    expect(bar).toHaveAttribute('aria-valuenow', '42')
    expect(bar).toHaveAttribute('aria-valuemin', '0')
    expect(bar).toHaveAttribute('aria-valuemax', '100')
  })
})
