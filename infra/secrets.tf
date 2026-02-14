resource "google_secret_manager_secret" "db_pass" {
  secret_id = "elite-concierge-db-pass"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_pass_val" {
  secret      = google_secret_manager_secret.db_pass.id
  secret_data = var.db_password
}

resource "google_secret_manager_secret" "api_key" {
  secret_id = "ELITE_API_KEY"
  replication {
    auto {}
  }
}

# Grant Access to Backend SA
resource "google_secret_manager_secret_iam_member" "db_pass_access" {
  secret_id = google_secret_manager_secret.db_pass.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "api_key_access" {
  secret_id = google_secret_manager_secret.api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}
