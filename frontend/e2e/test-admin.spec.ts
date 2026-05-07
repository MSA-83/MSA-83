import { test, expect } from '@playwright/test'

test.describe('Admin Dashboard', () => {
  test('admin page loads with title', async ({ page }) => {
    await page.goto('/admin')

    await expect(page.getByRole('heading', { name: /admin dashboard/i })).toBeVisible()
  })

  test('shows all navigation tabs', async ({ page }) => {
    await page.goto('/admin')

    await expect(page.getByRole('button', { name: 'Overview' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Analytics' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Top Users' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Feature Flags' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'System' })).toBeVisible()
  })

  test('overview tab shows system health section', async ({ page }) => {
    await page.goto('/admin')
    await page.getByRole('button', { name: 'Overview' }).click()

    await expect(page.getByText(/system health/i)).toBeVisible()
  })

  test('analytics tab loads content', async ({ page }) => {
    await page.goto('/admin')
    await page.getByRole('button', { name: 'Analytics' }).click()

    await expect(page.getByText(/events by type/i)).toBeVisible()
  })

  test('feature flags tab loads content', async ({ page }) => {
    await page.goto('/admin')
    await page.getByRole('button', { name: 'Feature Flags' }).click()

    await expect(page.getByText(/feature flags/i)).toBeVisible()
  })

  test('system tab shows memory and agent sections', async ({ page }) => {
    await page.goto('/admin')
    await page.getByRole('button', { name: 'System' }).click()

    await expect(page.getByText(/memory stats/i)).toBeVisible()
    await expect(page.getByText(/agent pool/i)).toBeVisible()
  })

  test('tab switching works', async ({ page }) => {
    await page.goto('/admin')

    await page.getByRole('button', { name: 'Analytics' }).click()
    await expect(page.getByText(/events by type/i)).toBeVisible()

    await page.getByRole('button', { name: 'System' }).click()
    await expect(page.getByText(/memory stats/i)).toBeVisible()

    await page.getByRole('button', { name: 'Overview' }).click()
    await expect(page.getByText(/system health/i)).toBeVisible()
  })
})
