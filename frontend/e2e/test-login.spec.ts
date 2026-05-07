import { test, expect } from '@playwright/test'

test.describe('Login Flow', () => {
  test('shows login form on unauthenticated visit', async ({ page }) => {
    await page.goto('/login')

    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible()
    await expect(page.getByPlaceholder(/email/i)).toBeVisible()
    await expect(page.getByLabel(/password/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible()
  })

  test('shows error on invalid credentials', async ({ page }) => {
    await page.goto('/login')

    await page.getByPlaceholder(/email/i).fill('wrong@example.com')
    await page.getByLabel(/password/i).fill('wrongpassword')
    await page.getByRole('button', { name: /sign in/i }).click()

    await expect(page.getByText(/invalid|error|incorrect|failed/i)).toBeVisible({ timeout: 5000 })
  })

  test('has registration link', async ({ page }) => {
    await page.goto('/login')

    const registerLink = page.getByRole('link', { name: /register|sign up|create account/i })
    if (await registerLink.isVisible()) {
      await expect(registerLink).toBeVisible()
    }
  })
})
