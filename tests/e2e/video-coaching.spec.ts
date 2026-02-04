import { test, expect } from '@playwright/test';

// Configure test to use fake camera/microphone streams for headless environments
test.use({
    permissions: ['camera', 'microphone'],
    launchOptions: {
        args: [
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
        ],
    },
});

test.describe('Video Coaching Feature', () => {
    test('should load exercise card and activate camera form check', async ({ page, context }) => {
        const apiKey = process.env.ELITE_API_KEY;
        if (!apiKey) {
            throw new Error('ELITE_API_KEY environment variable is not set');
        }

        // Set E2E Auth Mock in local storage AND Cookies for robust bypass
        const domain = new URL(process.env.BASE_URL || 'https://blackcard-concierge.netlify.app').hostname;
        await context.addCookies([{
            name: 'E2E_AUTH_MOCK',
            value: apiKey || 'true',
            domain: domain,
            path: '/'
        }]);

        await context.addInitScript((key) => {
            window.localStorage.setItem('E2E_AUTH_MOCK', key || 'true');
        }, apiKey);

        // 1. Navigate to a specific workout session (mock/demo ID) with bypass
        await page.goto(`/workout/demo_session_1?e2e-key=${apiKey}`);

        // 2. Locate the exercise card and "Check Form" button
        console.log('Locating Check Form button...');
        const checkFormBtn = page.getByText('Check Form', { exact: false }).first();
        await expect(checkFormBtn).toBeVisible({ timeout: 10000 });
        console.log('Button found, attempting click...');
        await checkFormBtn.click({ force: true });
        console.log('Click action completed.');

        // 3. Verify Camera Interface Overlay
        const cameraOverlay = page.locator('.fixed.inset-0.bg-black');
        await expect(cameraOverlay).toBeVisible();

        // 4. Verify "Form Check Mode" header exists
        await expect(page.getByText(/Form Check Mode/i)).toBeVisible();

        // 5. Verify Video Element is active (indicating camera stream started)
        const videoElement = cameraOverlay.locator('video');
        await expect(videoElement).toBeVisible();

        // Ensure web-cam didn't crash
        await expect(page.getByText(/Error accessing camera/i)).not.toBeVisible();

        // 6. Verify "Recording" indicator is NOT initially present
        await expect(page.getByText(/^Recording$/i)).not.toBeVisible();

        // 7. Test Recording Trigger (Optional, confirms interactivity)
        // Find the record button (large rounded full button)
        // Using a specific class or structure based on ExerciseCard.tsx
        // Button in the footer area
        const recordBtn = cameraOverlay.locator('button').filter({ has: page.locator('.rounded-full') }).last();
        await expect(recordBtn).toBeVisible();

        // Start Recording
        await recordBtn.click();

        // Verify "Recording" indicator appears (it has a bullet point so exact: false is safer)
        await expect(page.getByText('RECORDING', { exact: false }).first()).toBeVisible({ timeout: 10000 });

        // Stop Recording (via same button or verify auto-stop logic, but manual stop is faster)
        await page.waitForTimeout(1000); // Record for 1s
        await recordBtn.evaluate(el => el.dispatchEvent(new MouseEvent('click', { bubbles: true })));

        // Verify "Analyzing Mechanics..." loader appears
        await expect(page.getByText(/Analyzing Mechanics.../i)).toBeVisible();

        // Note: We are NOT asserting the backend response here fully to avoid flake on long AI calls,
        // but verifying we reached the "Analyzing" state confirms the frontend <-> camera integration worked.
    });
});
