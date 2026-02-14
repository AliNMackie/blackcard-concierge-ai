output "cloud_run_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.api.uri
}

output "db_instance_connection_name" {
  description = "The connection name of the Cloud SQL instance to be used in connection strings"
  value       = google_sql_database_instance.master.connection_name
}

output "backend_sa_email" {
  description = "The email of the backend service account"
  value       = google_service_account.backend_sa.email
}

output "artifact_registry_repo" {
  description = "The location of the Artifact Registry repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.name}"
}
