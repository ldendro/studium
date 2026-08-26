import { defineConfig, devices } from '@playwright/test'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const webDir = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(webDir, '..')
const frontendDir = path.join(webDir, 'dist')
const studiumBin = path.join(repoRoot, '.venv', 'bin', 'studium')
const appData = mkdtempSync(path.join(tmpdir(), 'studium-e2e-app-'))
const port = Number(process.env.STUDIUM_E2E_PORT ?? 8766)
const baseURL = `http://127.0.0.1:${port}`

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 240_000,
  expect: { timeout: 20_000 },
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL,
    ...devices['Desktop Chrome'],
    viewport: { width: 1280, height: 720 },
    trace: 'retain-on-failure',
  },
  webServer: {
    command: [
      studiumBin,
      'serve',
      '--frontend',
      frontendDir,
      '--no-open-browser',
      '--host',
      '127.0.0.1',
      '--port',
      String(port),
      '--app-data',
      appData,
    ]
      .map((part) => JSON.stringify(part))
      .join(' '),
    cwd: repoRoot,
    url: `${baseURL}/api/health`,
    reuseExistingServer: false,
    timeout: 120_000,
  },
})
