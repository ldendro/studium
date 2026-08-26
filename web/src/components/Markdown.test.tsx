import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Markdown } from './Markdown'

describe('Markdown', () => {
  it('renders safe formatting and strips executable markup', () => {
    const { container } = render(
      <Markdown
        value={[
          '**Gradient descent** is iterative.',
          '<script>window.__xss = true</script>',
          '<img src="x" onerror="window.__xss = true" alt="payload" />',
          '<a href="javascript:alert(1)">unsafe</a>',
        ].join('\n\n')}
      />,
    )

    expect(screen.getByText('Gradient descent', { exact: false })).toBeVisible()
    expect(container.querySelector('script')).toBeNull()
    expect(container.querySelector('img')?.getAttribute('onerror')).toBeNull()
    expect(container.querySelector('a')?.getAttribute('href') ?? '').not.toMatch(/javascript:/i)
    expect((window as Window & { __xss?: boolean }).__xss).toBeUndefined()
  })
})
