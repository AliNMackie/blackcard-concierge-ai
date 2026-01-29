# E2E Testing Guide

This project uses [Playwright](https://playwright.dev/) for End-to-End testing.
The tests are located in `tests/e2e/`.

## Prerequisites
- Node.js installed.
- Deployed frontend URL (default: `https://blackcard-concierge.netlify.app`).

## Setup
1. Navigate to the test directory:
   ```bash
   cd tests/e2e
   ```
2. Install dependencies:
   ```bash
   npm install
   npx playwright install --with-deps chromium
   ```

## Running Tests Locally
Run all tests against the default production URL:
```bash
npx playwright test
```

Target a specific environment (e.g., localhost or preview):
```bash
BASE_URL=http://localhost:3000 npx playwright test
```

Debug mode (opens inspector):
```bash
npx playwright test --debug
```

UI Mode (interactive runner):
```bash
npx playwright test --ui
```

## CI/CD Integration
The E2E suite runs via GitHub Actions in `.github/workflows/e2e-nightly.yml`.
- **Triggers**: Manual dispatch or Nightly Schedule.
- **Environment**: Targets the live Production URL.
- **Failures**: Check the "Artifacts" section of the GitHub Action run for HTML reports and traces.
