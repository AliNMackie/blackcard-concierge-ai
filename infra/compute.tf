# Artifact Registry Repo
# Storing here as it is the source for the compute service
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "${var.service_name}-repo"
  description   = "Docker repository for Elite Concierge services"
  format        = "DOCKER"
  project       = var.project_id
  
  depends_on = [google_project_service.apis]
}

# Cloud Run v2 Service
resource "google_cloud_run_v2_service" "api" {
  name     = "${var.service_name}-api"
  location = var.region
  project  = var.project_id
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.backend_sa.email

    containers {
      # Placeholder image for infra initialization
      image = "us-docker.pkg.dev/cloudrun/container/hello" 
      
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "DB_INSTANCE_CONNECTION_NAME"
        value = google_sql_database_instance.postgres.connection_name
      }
      
      # In a real app we'd mount the secret as volume or env var from secret ref
      env {
        name = "DB_PASS"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_pass_secret.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name  = "ENV"
        value = "production"
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version
    ]
  }

  depends_on = [google_project_service.apis]
}

# Allow unauthenticated invocations for the MVP API (Publicly accessible PWA/Webhook)
# resource "google_cloud_run_service_iam_member" "public_access" {
#   location = google_cloud_run_v2_service.api.location
#   project  = google_cloud_run_v2_service.api.project
#   service  = google_cloud_run_v2_service.api.name
#   role     = "roles/run.invoker"
#   member   = "allUsers"
# }
