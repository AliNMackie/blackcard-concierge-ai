# Project Setup: Black Card Concierge AI

This guide contains the exact commands to align the Terraform infrastructure with the GCP Project `blackcard-concierge-ai`.

## 1. Prerequisites
*   You are authenticated with `gcloud auth application-default login`.
*   Billing is enabled on `blackcard-concierge-ai`.
*   **Org Policy 1**: Ensure `constraints/sql.restrictPublicIp` is **NOT Enforced**.
    *   *Command*: `gcloud resource-manager org-policies disable-enforce constraints/sql.restrictPublicIp --project=blackcard-concierge-ai`
*   **Org Policy 2**: Ensure `constraints/iam.allowedPolicyMembers` (Domain Restricted Sharing) is **Allowed All**.
    *   *Step 1*: Create a file `allow_policy.yaml` with:
        ```yaml
        constraint: constraints/iam.allowedPolicyMembers
        listPolicy:
          allValues: ALLOW
        ```
    *   *Step 2*: Apply it: `gcloud resource-manager org-policies set-policy allow_policy.yaml --project=blackcard-concierge-ai`

## 2. Infrastructure Initialization
Navigate to the infrastructure directory:
```bash
cd infra
```

Initialize Terraform (downloads providers):
```bash
terraform init
```

## 3. Review Plan
Run a plan to verify what will be created in `europe-west2` for project `blackcard-concierge-ai`:
```bash
terraform plan -var="project_id=blackcard-concierge-ai" -var="region=europe-west2"
```

## 4. Apply Infrastructure
Provision the resources (Cloud Run, SQL, Artifact Registry, etc.):
```bash
terraform apply -var="project_id=blackcard-concierge-ai" -var="region=europe-west2"
```

## 5. Post-Apply Verification
*   Check the Cloud Run URL output.
*   Verify the Service Account email output for CI/CD setup.
