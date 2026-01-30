terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable Required Services
resource "google_project_service" "aiplatform" {
  service = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "run" {
  service = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "sqladmin" {
  service = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

# 2. Service Account for the "Brain"
resource "google_service_account" "elite_sa" {
  account_id   = "elite-concierge-sa"
  display_name = "Elite Concierge Service Account"
}

resource "google_project_iam_member" "ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.elite_sa.email}"
}

resource "google_project_iam_member" "sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.elite_sa.email}"
}

# 3. Database (Free Tier Compatible)
resource "google_sql_database_instance" "main" {
  name             = "elite-concierge-db-${random_id.db_suffix.hex}"
  database_version = "POSTGRES_15"
  region           = "europe-west2"

  settings {
    tier = "db-f1-micro"
    availability_type = "ZONAL" # Free tier often requires zonal, not HA
    
    # Enable public IP for now (easier for MVP), restrict in prod
    ip_configuration {
      ipv4_enabled = true 
    }
  }
  deletion_protection = false # For dev/demo ease
  depends_on = [google_project_service.sqladmin]
}

resource "random_id" "db_suffix" {
  byte_length = 4
}

# 4. Cloud Run Service (The App)
resource "google_cloud_run_service" "api" {
  name     = "elite-concierge-api"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.elite_sa.email
      containers {
        image = "gcr.io/${var.project_id}/elite-concierge-api:latest" # Placeholder
        env {
          name  = "DB_INSTANCE_CONNECTION_NAME"
          value = google_sql_database_instance.main.connection_name
        }
        # Add other env vars (TERRA_API_SECRET, etc) here
      }
    }
  }

  traffic {
    percent = 100
    latest_revision = true
  }

  depends_on = [google_project_service.run]
}

# Variables (Minimal)
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "europe-west2"
}
