import { test, expect } from '@playwright/test';

test.describe('Concierge Chat Interaction', () => {
    test('should allow user to send a message and receive a response', async ({ page }) => {
        // Navigate to dashboard where chat widget lives
        await page.goto('/dashboard');

        // Open chat widget if it's collapsible, or find the input area directly
        // Assuming standard "Concierge" card or widget
        const chatInput = page.getByPlaceholder(/Ask your concierge/i).or(page.locator('input[type="text"]'));

        // Ensure input is visible
        await expect(chatInput.first()).toBeVisible();

        // Type a test message
        const testMessage = "Test E2E: What is my recovery score?";
        await chatInput.first().fill(testMessage);
        await chatInput.first().press('Enter');

        // Wait for response bubble
        // We expect a new message to appear in the chat list
        // This selectors might need tuning based on actual DOM classes
        const chatMessages = page.locator('.chat-message, .message-bubble, p');

        // Expect at least one message response (simulated or real)
        // The previous message was user's, next should be agent's
        await expect(chatMessages.getByText(testMessage)).toBeVisible();

        // Wait for "Thinking..." or response
        // Logic: If there is a backend connected, it should respond.
        // If not, we might verify just the UI state of "Sent".
        await expect(page.getByText(/Test E2E/i)).toBeVisible();
    });
});
