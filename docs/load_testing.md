# Load Testing Guide

We use [k6](https://k6.io/) for load testing the Cloud Run backend.

## Load Model & SLOs
- **Target RPS**: ~50 RPS peak.
- **Latency SLO**: 95% of requests < 500ms.
- **Error Rate**: < 1%.

## Running Locally
1. **Install k6**:
   - Windows: `winget install k6` or download from website.
   - Mac: `brew install k6`.

2. **Run Script**:
   ```bash
   # Run against Production (CAREFUL)
   k6 run -e BASE_URL=https://YOUR_CLOUD_RUN_URL load/script.js

   # Run against Localhost
   k6 run -e BASE_URL=http://localhost:8080 load/script.js
   ```

## CI/CD Workflow
The `load-test.yml` workflow allows on-demand load testing.
1. Go to **actions** tab in GitHub.
2. Select **Load Test**.
3. Click **Run workflow**.
4. (Optional) Provide a target URL, defaults to the production URL.

## Best Practices for Cloud Run
- **Start Small**: Don't accidentally DDoS the service. The current script caps at 50 VUs.
- **Concurrency**: Cloud Run handles concurrency well, but cold starts may cause initial latency spikes.
- **Cost**: Remember that load tests generate real billable requests.
