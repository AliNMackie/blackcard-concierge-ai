# Enable required APIs
# We keep this in main.tf as the entry point for enabling services
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com",
    "sqladmin.googleapis.com",
    "artifactregistry.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "orgpolicy.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  disable_on_destroy = false
}

