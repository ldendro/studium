import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

async function expectNoSeriousAxeViolations(page: Page) {
  const results = await new AxeBuilder({ page }).analyze()
  const blocking = results.violations.filter((violation) =>
    ['critical', 'serious'].includes(violation.impact ?? ''),
  )
  expect(
    blocking,
    blocking
      .map(
        (violation) =>
          `${violation.id} (${violation.impact}): ${violation.help} — ${violation.nodes
            .map((node) => node.target.join(' '))
            .join(', ')}`,
      )
      .join('\n'),
  ).toEqual([])
}

test('onboarding, demo search, settings, and accessibility', async ({ page }) => {
  const vault = path.join(mkdtempSync(path.join(tmpdir(), 'studium-e2e-vault-')), 'vault')

  await page.goto('/')
  await expect(page.getByRole('heading', { name: /Turn what you study/ })).toBeVisible()
  await expectNoSeriousAxeViolations(page)

  await page.getByRole('button', { name: 'Create' }).click()
  await expect(page.getByRole('heading', { name: 'Create a local workspace' })).toBeVisible()
  await page.getByLabel('New vault directory').fill(vault)
  await page.getByRole('button', { name: 'Create demo workspace' }).click()
  await expect(page.getByRole('heading', { name: /Find what you already know/ })).toBeVisible({
    timeout: 180_000,
  })

  await page.getByLabel('Search your knowledge').fill('GD')
  await page.getByRole('button', { name: 'Search', exact: true }).click()
  await expect(page.getByRole('button', { name: /Gradient Descent/ })).toBeVisible()

  await page.getByLabel('Search your knowledge').fill('Steepest Descent')
  await page.getByRole('button', { name: 'Search', exact: true }).click()
  await expect(page.getByRole('button', { name: /Gradient Descent/ })).toBeVisible()

  await page.getByRole('link', { name: 'Settings' }).click()
  await expect(page.getByRole('heading', { name: /Your data, models, and recovery/ })).toBeVisible()
  await expect(page.getByRole('navigation', { name: 'Settings sections' })).toBeVisible()
  await expectNoSeriousAxeViolations(page)

  await page.setViewportSize({ width: 390, height: 844 })
  await page.getByRole('button', { name: 'Open navigation' }).click()
  await expect(page.getByRole('link', { name: 'Search' })).toBeVisible()
  await page.getByRole('link', { name: 'Search' }).click()
  await expect(page.getByRole('heading', { name: /Find what you already know/ })).toBeVisible()
  await expectNoSeriousAxeViolations(page)
})
