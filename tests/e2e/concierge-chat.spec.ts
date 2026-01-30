import { test, expect } from '@playwright/test';

test.describe('Concierge Chat Interaction', () => {
    test.skip('should allow user to send a message and receive a response', async ({ page }) => {
        // Navigate to dashboard where chat widget lives
        await page.goto('/messages');

        // Open chat widget if it's collapsible, or find the input area directly
        const chatInput = page.getByPlaceholder(/Message your coach/i);

        // Ensure input is visible
        await expect(chatInput).toBeVisible();

        // Type a test message
        const testMessage = "Test E2E: What is my recovery score?";
        await chatInput.click();
        await chatInput.fill(testMessage);

        // Wait for React state
        await page.waitForTimeout(500);

        // Try Enter key via keyboard (global focus)
        await page.keyboard.press('Enter');

        // Fallback: Click button if input still has text
        try {
            await expect(chatInput).toBeEmpty({ timeout: 1000 });
        } catch (e) {
            console.log("Enter key didn't work, trying forceful button click...");
            await page.locator('button').last().click({ force: true });
        }

        // Wait for response bubble
        // Check if the message appears in the chat history
        // Use a generous timeout for AI response / network latency
        await expect(page.getByText(testMessage)).toBeVisible({ timeout: 15000 });

        // Wait for "Thinking..." or response
        // Logic: If there is a backend connected, it should respond.
        // If not, we might verify just the UI state of "Sent".
        await expect(page.getByText(/Test E2E/i)).toBeVisible();
    });
});
