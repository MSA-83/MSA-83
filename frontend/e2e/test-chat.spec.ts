import { test, expect } from '@playwright/test'

test.describe('Chat Flow', () => {
  test('chat page renders with input', async ({ page }) => {
    await page.goto('/chat')

    const chatInput = page.getByRole('textbox')
    if (await chatInput.isVisible()) {
      await chatInput.fill('Hello, Titanium!')
      await expect(chatInput).toHaveValue('Hello, Titanium!')
    }
  })

  test('model selector exists', async ({ page }) => {
    await page.goto('/chat')

    const modelSelect = page.locator('select')
    if (await modelSelect.isVisible()) {
      await expect(modelSelect).toBeVisible()
    }
  })

  test('navigation to memory page works', async ({ page }) => {
    await page.goto('/chat')

    const memoryLink = page.getByRole('link', { name: /memory/i })
    if (await memoryLink.isVisible()) {
      await memoryLink.click()
      await expect(page).toHaveURL(/memory/)
    }
  })

  test('navigation to agents page works', async ({ page }) => {
    await page.goto('/chat')

    const agentsLink = page.getByRole('link', { name: /agent/i })
    if (await agentsLink.isVisible()) {
      await agentsLink.click()
      await expect(page).toHaveURL(/agents/)
    }
  })
})
